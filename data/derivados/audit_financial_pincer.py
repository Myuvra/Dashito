#!/usr/bin/env python3
"""Audita la semántica de signos de la pinza financiera y genera el v128.

Convención universal para impacto sobre hogares:
    positivo = favorable
    negativo = desfavorable

Todos los insumos se leen desde data/ y las fuentes originales no se modifican.
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable

import build_rates_volume as base


DATA_DIR = Path(__file__).resolve().parents[1]
DERIVED_DIR = DATA_DIR / "derivados"
SOURCE_DIR = DATA_DIR / "fuentes"
INPUT_HTML = DATA_DIR / "dashboard_kawaii_127_cuenta_unificada_18_43.html"
OUTPUT_HTML = DATA_DIR / "dashboard_kawaii_128_pinza_financiera_auditada.html"
AUDIT_CSV = DERIVED_DIR / "tasas_pinza_hogar_auditada.csv"
AUDIT_MD = DERIVED_DIR / "AUDITORIA_PINZA_FINANCIERA.md"

POST_START = "2023-12"
POST_END = "2026-07"
MIRROR_START = "2021-04"
MIRROR_END = "2023-11"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def finite(value: Any) -> bool:
    return isinstance(value, (int, float)) and math.isfinite(value)


def close(a: float, b: float, tolerance: float = 0.05) -> bool:
    return abs(a - b) <= tolerance


def write_csv(path: Path, rows: Iterable[dict[str, Any]], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def replace_once(text: str, old: str, new: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"Se esperaba 1 coincidencia y hubo {count}: {old[:160]!r}")
    return text.replace(old, new, 1)


def replace_regex_once(text: str, pattern: str, replacement: str) -> str:
    result, count = re.subn(pattern, lambda _: replacement, text, count=1, flags=re.S)
    if count != 1:
        raise RuntimeError(f"No se pudo reemplazar patrón único: {pattern[:150]!r}")
    return result


def signed_billions(value: float) -> str:
    sign = "+" if value > 0 else "−" if value < 0 else "≈"
    return f"{sign}$ {abs(value) / 1e12:,.2f} B".replace(",", "X").replace(".", ",").replace("X", ".")


def month_number(month: str) -> int:
    year, number = map(int, month.split("-"))
    return year * 12 + number - 1


def read_fintech_series() -> tuple[dict[str, float], dict[str, float]]:
    """Lee TNA mensual y cortes de stock Fintech de la planilla PNFC oficial.

    Los stocks de la hoja 3 están publicados en miles de millones de pesos
    constantes de febrero de 2026. Las TNA de la hoja 5 están ponderadas por
    saldos de préstamos personales del grupo Fintech.
    """

    path = (
        SOURCE_DIR
        / "tasas"
        / "pnfc"
        / "series-informe-proveedores-no-financieros-credito-junio-2026.xlsx"
    )
    workbook = base.load_workbook(path, read_only=True, data_only=True)

    rates_sheet = workbook["5"]
    fintech_tna: dict[str, float] = {}
    for raw_date, raw_rate in zip(
        (rates_sheet.cell(11, col).value for col in range(3, 86)),
        (rates_sheet.cell(13, col).value for col in range(3, 86)),
    ):
        if isinstance(raw_date, datetime) and finite(raw_rate):
            fintech_tna[raw_date.strftime("%Y-%m")] = float(raw_rate)

    stock_sheet = workbook["3"]
    stock_points: dict[str, float] = {}
    for raw_date, raw_stock in zip(
        (stock_sheet.cell(5, col).value for col in range(3, 13)),
        (stock_sheet.cell(8, col).value for col in range(3, 13)),
    ):
        if not finite(raw_stock):
            continue
        if isinstance(raw_date, datetime):
            month = raw_date.strftime("%Y-%m")
        elif str(raw_date).lower() == "dic-23":
            month = "2023-12"
        else:
            continue
        stock_points[month] = float(raw_stock) * 1_000_000_000

    workbook.close()
    if "2021-04" not in fintech_tna or "2026-02" not in fintech_tna:
        raise RuntimeError("La serie TNA Fintech no cubre la ventana esperada")
    if "2020-12" not in stock_points or "2026-02" not in stock_points:
        raise RuntimeError("Faltan cortes de stock Fintech para interpolar las ventanas")
    return fintech_tna, stock_points


def interpolate_fintech_stock(
    month: str, stock_points: dict[str, float]
) -> tuple[float, str]:
    """Interpola linealmente stocks reales; luego del último corte conserva nivel."""

    if month in stock_points:
        return stock_points[month], "corte oficial"
    target = month_number(month)
    ordered = sorted((month_number(key), key, value) for key, value in stock_points.items())
    lower = [point for point in ordered if point[0] < target]
    upper = [point for point in ordered if point[0] > target]
    if lower and upper:
        left, right = lower[-1], upper[0]
        weight = (target - left[0]) / (right[0] - left[0])
        return left[2] + (right[2] - left[2]) * weight, "interpolado entre cortes oficiales"
    if lower:
        return lower[-1][2], "último corte conservado"
    raise RuntimeError(f"No hay stock Fintech suficiente para {month}")


def build_records(
    modern: list[dict[str, Any]],
    baselines: dict[str, float | int],
    personal: dict[str, float],
    pf: dict[str, float],
    ipc: dict[str, float],
    fintech_tna: dict[str, float],
    fintech_stock_points: dict[str, float],
) -> list[dict[str, Any]]:
    ipc_ref = ipc[POST_END]
    fintech_stock_to_ref = ipc_ref / ipc["2026-02"]
    last_fintech_month = max(fintech_tna)
    last_fintech_tna = fintech_tna[last_fintech_month]
    records: list[dict[str, Any]] = []
    for source in modern:
        month = source["date"][:7]
        if not (MIRROR_START <= month <= POST_END):
            continue
        banco_real = source.get("bancoReal")
        pf_real = source.get("pfReal")
        if not finite(banco_real) or not finite(pf_real):
            raise RuntimeError(f"Falta tasa real comparable en {month}")
        if month not in personal or month not in pf or month not in ipc:
            raise RuntimeError(f"Falta volumen o IPC en {month}")

        banco_brecha = float(banco_real) - float(baselines["bancoReal"])
        pf_brecha = float(pf_real) - float(baselines["pfReal"])
        monto_personales = personal[month]
        monto_pf = pf[month]
        factor = ipc_ref / ipc[month]

        impacto_costo_banco_nominal = monto_personales * banco_brecha / 100
        impacto_hogar_banco_nominal = -impacto_costo_banco_nominal
        impacto_hogar_banco_constante = impacto_hogar_banco_nominal * factor
        impacto_hogar_pf_nominal = monto_pf * pf_brecha / 100
        impacto_hogar_pf_constante = impacto_hogar_pf_nominal * factor
        impacto_hogar_total_nominal = (
            impacto_hogar_banco_nominal + impacto_hogar_pf_nominal
        )
        impacto_hogar_total = (
            impacto_hogar_banco_constante + impacto_hogar_pf_constante
        )

        fintech_tna_month = fintech_tna.get(month, last_fintech_tna)
        fintech_rate_method = (
            "TNA oficial mensual"
            if month in fintech_tna
            else f"TNA {last_fintech_month} conservada"
        )
        previous_year = int(month[:4]) - (1 if month[5:] == "01" else 0)
        previous_month_number = 12 if month[5:] == "01" else int(month[5:]) - 1
        previous_month = f"{previous_year:04d}-{previous_month_number:02d}"
        if previous_month not in ipc:
            raise RuntimeError(f"Falta IPC previo para calcular Fintech en {month}")
        inflation_monthly = (ipc[month] / ipc[previous_month] - 1) * 100
        fintech_real = (
            (1 + (fintech_tna_month / 12) / 100)
            / (1 + inflation_monthly / 100)
            - 1
        ) * 100
        fintech_gap = fintech_real - float(baselines["fintechReal"])
        fintech_stock_feb26, fintech_stock_method = interpolate_fintech_stock(
            month, fintech_stock_points
        )
        fintech_stock_ref = fintech_stock_feb26 * fintech_stock_to_ref
        fintech_cost_extra = fintech_stock_ref * fintech_gap / 100
        impacto_hogar_fintech = -fintech_cost_extra
        impacto_hogar_total_ampliado = impacto_hogar_total + impacto_hogar_fintech

        records.append(
            {
                "fecha": month,
                "banco_real": float(banco_real),
                "banco_promedio_historico": float(baselines["bancoReal"]),
                "banco_brecha_tecnica_pp": banco_brecha,
                "monto_personales": monto_personales,
                "impacto_banco_nominal": impacto_costo_banco_nominal,
                "impacto_hogar_banco_nominal": impacto_hogar_banco_nominal,
                "impacto_hogar_banco_constante": impacto_hogar_banco_constante,
                "pf_real": float(pf_real),
                "pf_promedio_historico": float(baselines["pfReal"]),
                "pf_brecha_pp": pf_brecha,
                "monto_pf": monto_pf,
                "impacto_hogar_pf_nominal": impacto_hogar_pf_nominal,
                "impacto_hogar_pf_constante": impacto_hogar_pf_constante,
                "impacto_hogar_total_nominal": impacto_hogar_total_nominal,
                "impacto_hogar_total": impacto_hogar_total,
                "fintech_tna": fintech_tna_month,
                "fintech_real": fintech_real,
                "fintech_promedio_historico": float(baselines["fintechReal"]),
                "fintech_brecha_tecnica_pp": fintech_gap,
                "stock_fintech_constante_feb_2026": fintech_stock_feb26,
                "stock_fintech_constante_jul_2026": fintech_stock_ref,
                "impacto_costo_fintech_constante": fintech_cost_extra,
                "impacto_hogar_fintech_constante": impacto_hogar_fintech,
                "impacto_hogar_total_ampliado": impacto_hogar_total_ampliado,
                "fintech_tasa_metodo": fintech_rate_method,
                "fintech_stock_metodo": fintech_stock_method,
                "fintech_tasa_observada": month in fintech_tna,
                "ipc": ipc[month],
                "ipc_ref": ipc_ref,
                "factor_ipc": factor,
                "periodo_referencia": POST_END,
                "ventana": "post_shock" if POST_START <= month else "espejo",
            }
        )
    return records


def window_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    def total(key: str) -> float:
        return sum(float(row[key]) for row in rows)

    bank_values = [float(row["impacto_hogar_banco_constante"]) for row in rows]
    pf_values = [float(row["impacto_hogar_pf_constante"]) for row in rows]
    total_values = [float(row["impacto_hogar_total"]) for row in rows]
    fintech_values = [float(row["impacto_hogar_fintech_constante"]) for row in rows]
    expanded_values = [float(row["impacto_hogar_total_ampliado"]) for row in rows]
    return {
        "inicio": rows[0]["fecha"],
        "fin": rows[-1]["fecha"],
        "meses": len(rows),
        "impacto_hogar_banco": sum(bank_values),
        "impacto_hogar_pf": sum(pf_values),
        "impacto_hogar_total": sum(total_values),
        "impacto_hogar_fintech": sum(fintech_values),
        "impacto_hogar_total_ampliado": sum(expanded_values),
        "banco_desfavorable_bruto": sum(value for value in bank_values if value < 0),
        "banco_favorable_compensacion": sum(value for value in bank_values if value > 0),
        "pf_desfavorable_bruto": sum(value for value in pf_values if value < 0),
        "pf_favorable_compensacion": sum(value for value in pf_values if value > 0),
        "fintech_desfavorable_bruto": sum(value for value in fintech_values if value < 0),
        "fintech_favorable_compensacion": sum(value for value in fintech_values if value > 0),
        "fintech_meses_tna_observada": sum(bool(row["fintech_tasa_observada"]) for row in rows),
        "fintech_meses_tna_conservada": sum(not bool(row["fintech_tasa_observada"]) for row in rows),
        "banco_brecha_tecnica_pp_mes": total("banco_brecha_tecnica_pp"),
        "pf_brecha_pp_mes": total("pf_brecha_pp"),
        "monto_personales_constante": sum(
            float(row["monto_personales"]) * float(row["factor_ipc"]) for row in rows
        ),
        "monto_pf_constante": sum(
            float(row["monto_pf"]) * float(row["factor_ipc"]) for row in rows
        ),
    }


def audit_tests(records: list[dict[str, Any]], summary: dict[str, Any]) -> dict[str, str]:
    post = [row for row in records if row["ventana"] == "post_shock"]
    mirror = [row for row in records if row["ventana"] == "espejo"]

    assert all(
        close(
            float(row["impacto_hogar_banco_nominal"]),
            -float(row["impacto_banco_nominal"]),
        )
        for row in records
    ), "Test 1: el signo banco no se invirtió correctamente"

    assert all(
        close(
            float(row["impacto_hogar_total"]),
            float(row["impacto_hogar_banco_constante"])
            + float(row["impacto_hogar_pf_constante"]),
        )
        for row in records
    ), "Test 2: el total mensual no coincide con banco + PF"

    assert all(
        close(
            float(row["impacto_hogar_total_ampliado"]),
            float(row["impacto_hogar_banco_constante"])
            + float(row["impacto_hogar_pf_constante"])
            + float(row["impacto_hogar_fintech_constante"]),
        )
        for row in records
    ), "Test 2b: el balance ampliado no coincide con banco + PF + Fintech"

    post_sum = sum(float(row["impacto_hogar_total"]) for row in post)
    mirror_sum = sum(float(row["impacto_hogar_total"]) for row in mirror)
    assert close(post_sum, summary["post"]["impacto_hogar_total"]), "Test 3 falló"
    assert close(mirror_sum, summary["mirror"]["impacto_hogar_total"]), "Test 4 falló"
    assert close(
        summary["diferencial"]["impacto_hogar_total"], post_sum - mirror_sum
    ), "Test 5 falló"
    assert close(
        summary["diferencial"]["impacto_hogar_total_ampliado"],
        summary["post"]["impacto_hogar_total_ampliado"]
        - summary["mirror"]["impacto_hogar_total_ampliado"],
    ), "Test 5b falló"

    for window in ("post", "mirror"):
        s = summary[window]
        assert close(
            s["impacto_hogar_total"],
            s["impacto_hogar_banco"] + s["impacto_hogar_pf"],
        ), f"Test 6 falló en {window}"

    for window in ("post", "mirror"):
        s = summary[window]
        assert close(
            s["impacto_hogar_pf"],
            s["pf_desfavorable_bruto"] + s["pf_favorable_compensacion"],
        ), f"Test 7 falló en {window}"

    return {
        "test_1_signo_banco": "OK · 64/64 meses",
        "test_2_total_mensual": "OK · 64/64 meses",
        "test_2b_total_ampliado_mensual": "OK · 64/64 meses",
        "test_3_suma_post_kpi": "OK",
        "test_4_suma_espejo_kpi": "OK",
        "test_5_diferencial": "OK",
        "test_5b_diferencial_ampliado": "OK",
        "test_6_componentes_grafico": "OK",
        "test_7_bruto_compensacion_saldo_pf": "OK",
    }


def build_summary(
    records: list[dict[str, Any]],
    baselines: dict[str, float | int],
) -> dict[str, Any]:
    post_rows = [row for row in records if row["ventana"] == "post_shock"]
    mirror_rows = [row for row in records if row["ventana"] == "espejo"]
    post = window_summary(post_rows)
    mirror = window_summary(mirror_rows)
    differential = {
        "impacto_hogar_banco": post["impacto_hogar_banco"]
        - mirror["impacto_hogar_banco"],
        "impacto_hogar_pf": post["impacto_hogar_pf"] - mirror["impacto_hogar_pf"],
        "impacto_hogar_total": post["impacto_hogar_total"]
        - mirror["impacto_hogar_total"],
        "impacto_hogar_fintech": post["impacto_hogar_fintech"]
        - mirror["impacto_hogar_fintech"],
        "impacto_hogar_total_ampliado": post["impacto_hogar_total_ampliado"]
        - mirror["impacto_hogar_total_ampliado"],
    }
    fintech_source = next(row for row in records if row["fecha"] == "2026-02")
    summary = {
        "referencia": POST_END,
        "convencion": "+ favorable para el hogar; − desfavorable para el hogar",
        "baselines": baselines,
        "post": post,
        "mirror": mirror,
        "diferencial": differential,
        "fintech": {
            "fecha": "2026-02",
            "saldo_constante_feb_2026": fintech_source["stock_fintech_constante_feb_2026"],
            "saldo_constante_jul_2026": fintech_source["stock_fintech_constante_jul_2026"],
            "brecha_pp": fintech_source["fintech_brecha_tecnica_pp"],
            "impacto_hogar_mes_constante": fintech_source["impacto_hogar_fintech_constante"],
            "exposicion_costo_mes_constante": fintech_source["impacto_costo_fintech_constante"],
            "clasificacion": "CARGA MENSUAL ESTIMADA SOBRE STOCK",
            "metodo": "TNA mensual ponderada por saldos × stock real interpolado; marzo-julio 2026 conserva la última TNA y stock oficiales",
        },
    }
    summary["tests"] = audit_tests(records, summary)
    return summary


def rounded_records(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    cleaned: list[dict[str, Any]] = []
    for row in records:
        out: dict[str, Any] = {}
        for key, value in row.items():
            out[key] = round(value, 6) if isinstance(value, float) else value
        cleaned.append(out)
    return cleaned


def build_audit_markdown(summary: dict[str, Any]) -> str:
    m, p, d = summary["mirror"], summary["post"], summary["diferencial"]
    tests = "\n".join(f"- **{name}:** {value}" for name, value in summary["tests"].items())
    return f"""# Auditoría de la pinza financiera

## 1. Convención anterior encontrada

El dashboard calculaba correctamente la desviación técnica de cada tasa, pero combinaba dos orientaciones: el costo bancario se mostraba positivo y el plazo fijo se invertía en algunos gráficos para mostrar la magnitud de la pérdida como barra positiva.

## 2. Problema de signos

La expresión anterior `banco_neto - pf_neto` no tenía una semántica universal desde el hogar. En particular, el **+$8,71 B** del plazo fijo espejo era `−pf_neto`: una magnitud de costo con el signo visual invertido, no un rendimiento favorable.

## 3. Convención nueva

En todo agregado de impacto hogar:

```text
+ = favorable para el hogar
− = desfavorable para el hogar
```

## 4. Fórmula banco

```text
brecha_técnica_banco = tasa_real_banco − promedio_histórico_banco
impacto_costo_banco = monto_personales × brecha_técnica_banco / 100
impacto_hogar_banco = −impacto_costo_banco
```

## 5. Fórmula plazo fijo

```text
brecha_pf = tasa_real_pf − promedio_histórico_pf
impacto_hogar_pf = monto_pf × brecha_pf / 100
```

## 6. Fórmula Fintech y balances

```text
balance_conjunto = impacto_hogar_banco + impacto_hogar_pf
impacto_hogar_fintech = −(stock_real_fintech × brecha_real_fintech / 100)
balance_ampliado = balance_conjunto + impacto_hogar_fintech
diferencial = saldo_post − saldo_espejo
```

El balance conjunto reúne crédito bancario y ahorro minorista. El balance ampliado suma Fintech como carga mensual estimada sobre stock. No representa a un “hogar promedio”: deudores y ahorristas son universos distintos.

La TNA Fintech es mensual y está ponderada por saldos. El stock real se interpola linealmente entre cortes oficiales; para marzo–julio de 2026 se conservan la última TNA y el último stock publicados en febrero. Esos cinco meses se muestran como estimación, no como observación.

Cada flujo mensual se llevó a pesos de **julio de 2026** con `IPC_ref / IPC_t` antes de acumular.

## 7. Resultados espejo

- Banco: **{signed_billions(m['impacto_hogar_banco'])}**.
- Fintech: **{signed_billions(m['impacto_hogar_fintech'])}**.
- Plazo fijo: **{signed_billions(m['impacto_hogar_pf'])}**.
- Balance conjunto: **{signed_billions(m['impacto_hogar_total'])}**.
- Balance ampliado: **{signed_billions(m['impacto_hogar_total_ampliado'])}**.

## 8. Resultados post-shock

- Banco: **{signed_billions(p['impacto_hogar_banco'])}**.
- Fintech: **{signed_billions(p['impacto_hogar_fintech'])}** ({p['fintech_meses_tna_observada']} meses con TNA observada y {p['fintech_meses_tna_conservada']} estimados).
- Plazo fijo: **{signed_billions(p['impacto_hogar_pf'])}**.
- Balance conjunto: **{signed_billions(p['impacto_hogar_total'])}**.
- Balance ampliado: **{signed_billions(p['impacto_hogar_total_ampliado'])}**.

En plazo fijo post-shock, la pérdida bruta de meses desfavorables fue **{signed_billions(p['pf_desfavorable_bruto'])}** y la compensación de meses favorables fue **{signed_billions(p['pf_favorable_compensacion'])}**; su suma da el saldo neto **{signed_billions(p['impacto_hogar_pf'])}**.

## 9. Diferencial

El **diferencial post-shock vs espejo** es **{signed_billions(d['impacto_hogar_total'])}**. Ambos saldos fueron negativos contra sus normas históricas, pero el balance conjunto post-shock fue menos desfavorable en **{signed_billions(d['impacto_hogar_total'])}**.

Por componente: el crédito bancario cambió **{signed_billions(d['impacto_hogar_banco'])}**, Fintech cambió **{signed_billions(d['impacto_hogar_fintech'])}**, el plazo fijo cambió **{signed_billions(d['impacto_hogar_pf'])}**, el balance conjunto cambió **{signed_billions(d['impacto_hogar_total'])}** y el balance ampliado cambió **{signed_billions(d['impacto_hogar_total_ampliado'])}**.

Hay dos preguntas distintas: en un saldo, positivo significa favorable y negativo desfavorable contra la norma histórica; en un diferencial entre ventanas, positivo significa mejora y negativo empeoramiento. Por eso “sigue siendo negativo” no equivale a “empeoró”.

La pista preliminar cercana a −$13,5 B no se reprodujo. La diferencia se explica porque trataba el **+$8,71 B** del PF espejo mostrado en pantalla como beneficio, cuando el dato subyacente era un impacto hogar de **−$8,71 B** y la interfaz lo había invertido para expresar “costo”.

## 10. Tests de consistencia

{tests}

## Tabla final

| Concepto | Espejo | Post-shock | Diferencial |
|---|---:|---:|---:|
| Banco | {signed_billions(m['impacto_hogar_banco'])} | {signed_billions(p['impacto_hogar_banco'])} | {signed_billions(d['impacto_hogar_banco'])} |
| Fintech · estimación sobre stock | {signed_billions(m['impacto_hogar_fintech'])} | {signed_billions(p['impacto_hogar_fintech'])} | {signed_billions(d['impacto_hogar_fintech'])} |
| PF | {signed_billions(m['impacto_hogar_pf'])} | {signed_billions(p['impacto_hogar_pf'])} | {signed_billions(d['impacto_hogar_pf'])} |
| Balance conjunto de crédito y ahorro minorista | {signed_billions(m['impacto_hogar_total'])} | {signed_billions(p['impacto_hogar_total'])} | {signed_billions(d['impacto_hogar_total'])} |
| Balance ampliado banco + Fintech + PF | {signed_billions(m['impacto_hogar_total_ampliado'])} | {signed_billions(p['impacto_hogar_total_ampliado'])} | {signed_billions(d['impacto_hogar_total_ampliado'])} |

## Fuentes archivadas

- `data/fuentes/tasas/bcra/tas2_ser.txt`
- `data/fuentes/tasas/bcra/tas1_ser.txt`
- `data/fuentes/tasas/indec/serie_ipc_divisiones.csv`
- `data/fuentes/tasas/pnfc/series-informe-proveedores-no-financieros-credito-junio-2026.xlsx`

No se descargaron fuentes nuevas ni se modificaron originales.
"""


AUDIT_CSS = r"""
<style id="rates-sign-audit-v128">
.rates-sign-audit{margin:12px 20px;padding:14px 15px;border:2px solid #d8c9e7;border-radius:17px;background:linear-gradient(135deg,#fff9fb,#f8fffb);box-sizing:border-box;color:#66536f}
.rates-sign-audit.compact{margin-top:4px}
.rates-sign-audit h3{margin:0 0 8px;font-size:16px;color:#654574}
.rates-sign-audit-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px}
.rates-sign-audit-grid>div{min-width:0;padding:11px 12px;border:1px solid #e5dbe9;border-radius:13px;background:#fff;font-size:11px;line-height:1.5;box-sizing:border-box}
.rates-sign-audit .bad{color:#b0476d;font-weight:900}.rates-sign-audit .good{color:#3f876b;font-weight:900}
#ratesMoneySection .rates-money-kpi-grid{grid-template-columns:repeat(6,minmax(0,1fr))}
#ratesMoneySection .rates-money-kpi{border-color:#ded5e4;background:#fff}
#ratesMoneySection .rates-money-kpi.primary{grid-column:1/-1;border-width:2px;padding:18px 20px;box-shadow:0 8px 24px rgba(76,116,92,.12)}
#ratesMoneySection .rates-money-kpi.primary .big{font-size:34px}
#ratesMoneySection .rates-money-kpi:nth-child(2),#ratesMoneySection .rates-money-kpi:nth-child(3),#ratesMoneySection .rates-money-kpi:nth-child(4){grid-column:span 2}
#ratesMoneySection .rates-money-kpi:nth-child(5),#ratesMoneySection .rates-money-kpi:nth-child(6){grid-column:span 3}
#ratesMoneySection .rates-money-kpi.fintech{border-color:#e7c5d5;background:#fff9fc}
#ratesMoneySection .rates-money-kpi.favorable{border-color:#b9dfcf;background:#f7fffb}
#ratesMoneySection .rates-money-kpi.favorable .big{color:#3f876b}
#ratesMoneySection .rates-money-kpi.desfavorable{border-color:#ecc0d1;background:#fff8fb}
#ratesMoneySection .rates-money-kpi.desfavorable .big{color:#b0476d}
#ratesMoneySection .rates-money-kpi.neutral .big{color:#75687c}
#ratesMoneyChart{height:470px;min-height:470px}
#ratesMoneySection .rates-money-table{min-width:1400px}
#ratesMoneySection .rates-money-normalized .full{grid-column:1/-1;border-style:solid;background:#f8fff9}
.rates-usury-callout-values{grid-template-columns:repeat(2,minmax(0,1fr))!important}
.rates-usury-stat.effect{grid-column:1/-1;grid-row:1;order:-1;border-width:2px!important;box-shadow:0 7px 20px rgba(91,63,163,.11)}
.rates-usury-stat.effect .amount{font-size:29px!important}
.rates-money-table .pos{color:#3f876b!important;font-weight:900}.rates-money-table .neg{color:#b0476d!important;font-weight:900}
.rates-money-table .technical-pos{color:#a85d2e;font-weight:850}.rates-money-table .technical-neg{color:#4f73a9;font-weight:850}
.rates-sign-method{margin:12px 20px;padding:13px 14px;border-left:5px solid #8a70b0;border-radius:13px;background:#faf8ff;color:#685771;font-size:11px;line-height:1.55}
.rates-sign-method b{color:#5e4270}
@media(max-width:900px){#ratesMoneySection .rates-money-kpi-grid{grid-template-columns:repeat(2,minmax(0,1fr))}#ratesMoneySection .rates-money-kpi{grid-column:auto!important}#ratesMoneySection .rates-money-kpi.primary,#ratesMoneySection .rates-money-kpi:nth-child(4){grid-column:1/-1!important}.rates-sign-audit-grid{grid-template-columns:1fr}}
@media(max-width:640px){#ratesMoneySection .rates-money-kpi-grid{grid-template-columns:1fr}#ratesMoneySection .rates-money-kpi.primary,#ratesMoneySection .rates-money-kpi:nth-child(4){grid-column:auto!important}#ratesMoneySection>.card-head{flex-direction:column;align-items:flex-start;gap:8px}#ratesMoneySection>.card-head .card-title{max-width:100%}#ratesMoneySection>.card-head .kicker{align-self:flex-start;max-width:100%;text-align:left}#ratesMoneyChart{height:530px;min-height:530px}}
@media(max-width:720px){.rates-sign-audit,.rates-sign-method{margin-left:14px;margin-right:14px}}
@media(max-width:430px){.rates-sign-audit,.rates-sign-method{margin-left:11px;margin-right:11px;padding:12px}}
@media(max-width:390px){.rates-sign-audit,.rates-sign-method{margin-left:9px;margin-right:9px}}
</style>
"""


def build_html(
    source: str,
    records: list[dict[str, Any]],
    summary: dict[str, Any],
    csv_content: str,
) -> str:
    html = source
    m, p, d = summary["mirror"], summary["post"], summary["diferencial"]

    html = replace_once(html, "</head>", AUDIT_CSS + "\n</head>")
    html = replace_once(
        html,
        "inflación + TNA + diferencial + efecto monetario antes/después · 2002–2026 · 2026 parcial",
        "inflación + TNA + balance conjunto · diferencial post-shock vs espejo jerarquizado · 2002–2026",
    )
    html = replace_once(
        html,
        "Fisher contra IPC mensual · 2019–2026 · líneas punteadas = promedio histórico pre-shock",
        "tasas reales técnicas contra IPC · 2019–2026 · el signo económico depende de cada producto",
    )
    html = replace_once(
        html,
        '<div id="realChart"></div>',
        '''<div id="realChart"></div>
          <div class="rates-sign-audit compact">
            <h3>Cómo leer el signo en este gráfico técnico</h3>
            <div class="rates-sign-audit-grid">
              <div><b>Préstamo:</b> una tasa real por encima de su promedio significa crédito más caro. La desviación técnica es positiva, pero el <span class="bad">impacto hogar es negativo</span>.</div>
              <div><b>Plazo fijo:</b> una tasa real por encima de su promedio significa mejor rendimiento. Acá la desviación y el <span class="good">impacto hogar son positivos</span>.</div>
            </div>
          </div>''',
    )
    html = replace_once(
        html,
        '<div id="ratesDiffGrid" class="rates-diff-grid"></div>',
        f'''<div id="ratesDiffGrid" class="rates-diff-grid"></div>
      <div class="rates-sign-audit">
        <h3>Desviación técnica ≠ impacto hogar</h3>
        <div class="rates-sign-audit-grid">
          <div><b>Banco pos-shock:</b> +{p['banco_brecha_tecnica_pp_mes']:.2f} pp-mes de costo real acumulado. Es <span class="bad">desfavorable para deudores</span>; al pasar a impacto hogar se invierte el signo.</div>
          <div><b>Plazo fijo pos-shock:</b> {p['pf_brecha_pp_mes']:.2f} pp-mes frente a su promedio. Es <span class="bad">desfavorable para ahorristas</span>; en PF el signo técnico ya coincide con el del hogar.</div>
          <div><b>Fintech:</b> la serie técnica observada llega a feb-2026. En el panel en pesos se incorporan 27 meses con TNA oficial y 5 meses estimados, conservando la última TNA y el último stock publicados.</div>
        </div>
      </div>''',
    )
    html = replace_once(
        html,
        '''        Para PNFC/Fintech publica series de <b>saldos de financiamiento</b>, pero con una frecuencia/concepto diferente.
        Por eso no multiplicamos tasa × stock a ciegas: eso podría contar el mismo capital varias veces.''',
        '''        Para PNFC/Fintech publica TNA mensual ponderada por saldos y cortes de <b>stock real de financiamiento</b>.
        En el panel en pesos usamos esa combinación como proxy mensual: interpolamos sólo entre cortes oficiales y marcamos aparte la prolongación feb→jul-2026. No equivale a ganancia neta ni a intereses efectivamente cobrados.''',
    )
    html = replace_once(
        html,
        "costo del crédito y rendimiento del ahorro frente a su propia norma histórica · pesos de jul-2026",
        "Balance ampliado de crédito bancario, Fintech y ahorro minorista · diferencial post-shock vs espejo · pesos de jul-2026",
    )
    html = replace_once(
        html,
        '<span class="method-badge partial">Fintech = stock / exposición</span>',
        '<span class="method-badge partial">Fintech = proxy mensual sobre stock · integrada</span>',
    )
    html = replace_once(
        html,
        '<div class="tag">Fintech · exposición de cartera al diferencial real</div>',
        '<div class="tag">Fintech · diferencial estimado e integrado al balance ampliado</div>',
    )
    html = replace_once(
        html,
        "<thead><tr><th>Mes</th><th>Personales operados</th><th>Brecha banco</th><th>Impacto banco constante</th><th>PF constituidos 30–59</th><th>Brecha PF</th><th>Impacto PF constante</th></tr></thead>",
        "<thead><tr><th>Mes</th><th>Personales operados</th><th>Desviación banco</th><th>Impacto deudor</th><th>PF constituidos 30–59</th><th>Desviación PF</th><th>Impacto ahorrista</th><th>Desviación Fintech</th><th>Impacto Fintech</th><th>Balance ampliado</th></tr></thead>",
    )

    old_audit_cards = '''  <div class="rates-money-audit-grid">
    <div class="rates-money-audit-card">
      <h3>Qué significa el número</h3>
      <p>Si en un mes se operaron $100.000 millones en préstamos personales y la tasa real quedó 2 puntos porcentuales sobre su norma histórica, el indicador asigna $2.000 millones de costo financiero real adicional a ese flujo, antes de llevarlo a pesos de julio de 2026.</p>
      <p><b>Personales:</b> 1936 + 1938, monto operado mensual a tasa fija o repactable. <b>Plazo fijo:</b> ocho series diarias que cubren cuatro estratos de monto para 30–44 y 45–59 días, agregadas por mes.</p>
    </div>
    <div class="rates-money-audit-card warn">
      <h3>Qué NO significa</h3>
      <ul><li>No es CFT ni incluye todas las comisiones.</li><li>No prueba causalidad individual ni ganancia bancaria.</li><li>No equivale a stock de deuda ni repite un mismo préstamo.</li><li>Los montos operados incluyen refinanciaciones y no son flujo neto.</li><li>Fintech no se suma: es exposición sobre stock, no interés cobrado.</li></ul>
    </div>
  </div>'''
    new_audit_cards = '''  <div class="rates-money-audit-grid">
    <div class="rates-money-audit-card">
      <h3>Dos preguntas, dos lecturas del signo</h3>
      <p><b>Saldo contra la norma:</b> positivo = favorable; negativo = desfavorable. <b>Cambio entre ventanas:</b> positivo = mejora; negativo = empeoramiento. Por eso un saldo que sigue negativo puede haber mejorado.</p>
      <p>En crédito se invierte la desviación técnica porque una tasa más alta perjudica al deudor. En plazo fijo el signo se conserva porque una tasa más alta favorece al ahorrista.</p>
      <p><b>Personales:</b> series 1936 + 1938. <b>Plazo fijo:</b> ocho series 30–59 días. Cada impacto mensual se lleva a pesos de julio de 2026 antes de acumular.</p>
    </div>
    <div class="rates-money-audit-card warn">
      <h3>Alcance del indicador</h3>
      <p>El <b>balance ampliado de crédito y ahorro minorista</b> combina las patas deudoras y la ahorrista para comparar ventanas; no describe a un hogar promedio porque corresponden a universos distintos. <b>Tampoco demuestra que todo el diferencial se transforme en ganancia financiera.</b></p>
      <p>Fintech se incorpora como estimación mensual sobre stock real: se interpola entre cortes oficiales y se identifica la prolongación de febrero a julio de 2026.</p>
    </div>
  </div>'''
    html = replace_once(html, old_audit_cards, new_audit_cards)

    html = replace_once(html, "Antes · espejo abr-2021→nov-2023", "Saldo ampliado · espejo abr-2021→nov-2023")
    html = replace_once(html, "Después · dic-2023→jul-2026", "Saldo ampliado · pos-shock dic-2023→jul-2026")
    html = replace_once(html, "Efecto neto · después − antes", "Diferencial post-shock vs espejo")
    html = replace_once(
        html,
        '''              <b>Efecto mostrado:</b> a cada mes pos-shock le restamos el mes equivalente de la ventana espejo previa y acumulamos la diferencia.
              Las tres curvas usan <code>costo bancario adicional − rendimiento neto del plazo fijo</code> y pesos constantes de julio de 2026.''',
        '''              <b>Dato principal:</b> <code>diferencial = saldo post-shock − saldo espejo</code>. Positivo significa mejora entre ventanas; negativo, empeoramiento.
              El saldo ampliado suma banco + Fintech + plazo fijo. Los últimos cinco meses Fintech prolongan la TNA y el stock oficiales de feb-2026.''',
    )

    public_reading = '''<div class="rates-public-reading" id="ratesPublicReading">
            <div class="rates-public-head">
              <div>
                <div class="rates-public-kicker">En criollo · signos ya auditados</div>
                <h3>¿El balance ampliado de crédito y ahorro mejoró o empeoró?</h3>
                <p class="rates-public-lead"><b>En los saldos:</b> + favorable y − desfavorable contra la norma. <b>En el diferencial:</b> + mejora y − empeoramiento frente a la ventana espejo.</p>
              </div>
              <div class="rates-public-formula">saldo post − saldo espejo = diferencial</div>
            </div>
            <div class="rates-public-steps">
              <div class="rates-public-step before">
                <div class="rates-public-step-label"><span class="rates-public-step-no">1</span> Ventana espejo</div>
                <div class="rates-public-step-amount" id="ratesPublicBefore">—</div>
                <p>Saldo ampliado de banco + Fintech + plazo fijo durante los 32 meses anteriores.</p>
              </div>
              <div class="rates-public-step after">
                <div class="rates-public-step-label"><span class="rates-public-step-no">2</span> Período pos-shock</div>
                <div class="rates-public-step-amount" id="ratesPublicAfter">—</div>
                <p>Saldo ampliado durante los 32 meses posteriores al shock.</p>
              </div>
              <div class="rates-public-step effect">
                <div class="rates-public-step-label"><span class="rates-public-step-no">3</span> Diferencial post-shock vs espejo</div>
                <div class="rates-public-step-amount" id="ratesPublicEffect">—</div>
                <p>Un resultado positivo indica que el período posterior fue menos desfavorable.</p>
                <div class="rates-public-delta" id="ratesPublicEffectPct">—</div>
              </div>
            </div>
            <div class="rates-public-conclusion" id="ratesPublicConclusion">Calculando la lectura…</div>
          </div>'''
    html = replace_regex_once(
        html,
        r'<div class="rates-public-reading" id="ratesPublicReading">.*?</div>\s*<div class="family-mini-note"',
        public_reading + '\n          <div class="family-mini-note"',
    )

    compact = lambda rows: [
        {
            "fecha": row["fecha"],
            "impacto_hogar_banco_constante": row["impacto_hogar_banco_constante"],
            "impacto_hogar_pf_constante": row["impacto_hogar_pf_constante"],
            "impacto_hogar_total": row["impacto_hogar_total"],
            "impacto_hogar_fintech_constante": row["impacto_hogar_fintech_constante"],
            "impacto_hogar_total_ampliado": row["impacto_hogar_total_ampliado"],
            "fintech_tasa_observada": row["fintech_tasa_observada"],
        }
        for row in rows
    ]
    post_rows = [row for row in records if row["ventana"] == "post_shock"]
    mirror_rows = [row for row in records if row["ventana"] == "espejo"]
    rows_js = (
        "const ratesUsuryPostRows = "
        + json.dumps(compact(post_rows), ensure_ascii=False, separators=(",", ":"))
        + ";\nconst ratesUsuryMirrorRows = "
        + json.dumps(compact(mirror_rows), ensure_ascii=False, separators=(",", ":"))
        + ";"
    )
    html = replace_regex_once(
        html,
        r"const ratesUsuryPostRows = \[.*?\];\s*const ratesUsuryMirrorRows = \[.*?\];",
        rows_js,
    )
    html = replace_once(
        html,
        '''function ratesUsuryMonthlyValue(r){
  return Number(r.impacto_banco_pesos_constantes) - Number(r.impacto_pf_pesos_constantes);
}''',
        '''function ratesUsuryMonthlyValue(r){
  return Number(r.impacto_hogar_total_ampliado);
}''',
    )
    replacements = {
        "Antes · acumulado espejo ($)": "Saldo ampliado · ventana espejo ($)",
        "Después · acumulado pos-shock ($)": "Saldo ampliado · pos-shock ($)",
        "Efecto · después − antes ($)": "Diferencial post-shock vs espejo ($)",
        "<b>Antes · acumulado espejo</b>": "<b>Saldo ampliado · espejo</b>",
        "<b>Después · acumulado pos-shock</b>": "<b>Saldo ampliado · pos-shock</b>",
        "<b>Efecto acumulado vs antes</b>": "<b>Diferencial post-shock vs espejo</b>",
        "line:{color:'#3f8a6c',width:2.7,dash:'dash'}": "line:{color:'#c16a88',width:2.7,dash:'dash'}",
        "marker:{size:3.5,color:'#3f8a6c'}": "marker:{size:3.5,color:'#c16a88'}",
        "line:{color:'#5b3fa3',width:3.4}": "line:{color:'#3f876b',width:3.4}",
        "marker:{size:4.5,color:'#5b3fa3'}": "marker:{size:4.5,color:'#3f876b'}",
    }
    for old, new in replacements.items():
        html = replace_once(html, old, new)

    summary_js = json.dumps(summary, ensure_ascii=False, separators=(",", ":"))
    records_js = json.dumps(
        [row for row in records if row["ventana"] == "post_shock"],
        ensure_ascii=False,
        separators=(",", ":"),
    )
    audit_data_block = (
        f"const ratesMoneySummary = {summary_js};\n"
        f"const ratesMoneyRows = {records_js};\n"
        f"const ratesImpactCsv = {json.dumps(csv_content, ensure_ascii=False)};"
    )
    html = replace_regex_once(
        html,
        r"const ratesMoneySummary = \{.*?\};\s*const ratesMoneyRows = \[.*?\];\s*const ratesImpactCsv = .*?;\s*\n",
        audit_data_block + "\n",
    )

    rates_js = r'''function ratesMoneyArs(value,digits=2,showPlus=false){
  const v=Number(value),abs=Math.abs(v);
  const sign=v<0?'−':(showPlus&&v>0?'+':'');
  if(abs>=1e12)return `${sign}$ ${(abs/1e12).toLocaleString('es-AR',{minimumFractionDigits:digits,maximumFractionDigits:digits})} billones`;
  if(abs>=1e9)return `${sign}$ ${(abs/1e9).toLocaleString('es-AR',{minimumFractionDigits:1,maximumFractionDigits:1})} mil M`;
  return `${sign}$ ${abs.toLocaleString('es-AR',{maximumFractionDigits:0})}`;
}
function ratesMoneyCompact(value,showPlus=true){const v=Number(value),sign=v<0?'−':(showPlus&&v>0?'+':'');return `${sign}$ ${(Math.abs(v)/1e12).toLocaleString('es-AR',{minimumFractionDigits:2,maximumFractionDigits:2})} B`;}
function ratesMoneySignedClass(value){const v=Number(value);return v>0?'pos':v<0?'neg':'neutral';}
function ratesMoneyKpiClass(value){const v=Number(value);return v>0?'favorable':v<0?'desfavorable':'neutral';}
function ratesMoneyWord(value){const v=Number(value);return v>0?'favorable para el hogar':v<0?'desfavorable para el hogar':'prácticamente neutro';}
function ratesMoneyChangeWord(value){const v=Number(value);return v>0?'mejoró':v<0?'empeoró':'no cambió';}
function renderRatesMoney(){
  const s=ratesMoneySummary,p=s.post,m=s.mirror,d=s.diferencial;
  const el=document.getElementById('ratesMoneyGrid');
  if(!el)return;
  el.innerHTML=`
    <div class="rates-money-kpi primary ${ratesMoneyKpiClass(d.impacto_hogar_total_ampliado)}"><div class="tag">Diferencial post-shock vs espejo · balance ampliado</div><div class="big">${ratesMoneyArs(d.impacto_hogar_total_ampliado,2,true)}</div><div class="mini"><b>${ratesMoneyChangeWord(d.impacto_hogar_total_ampliado)}</b>. Fórmula: saldo post-shock − saldo espejo. Incluye banco + Fintech + plazo fijo.</div></div>
    <div class="rates-money-kpi ${ratesMoneyKpiClass(d.impacto_hogar_banco)}"><div class="tag">Cambio en crédito bancario</div><div class="big">${ratesMoneyArs(d.impacto_hogar_banco,2,true)}</div><div class="mini"><b>${ratesMoneyChangeWord(d.impacto_hogar_banco)}</b> respecto de la ventana espejo.</div></div>
    <div class="rates-money-kpi fintech ${ratesMoneyKpiClass(d.impacto_hogar_fintech)}"><div class="tag">Cambio en Fintech</div><div class="big">${ratesMoneyArs(d.impacto_hogar_fintech,2,true)}</div><div class="mini"><b>${ratesMoneyChangeWord(d.impacto_hogar_fintech)}</b>. Estimación mensual sobre stock real; ${p.fintech_meses_tna_conservada} meses prolongan el último dato oficial.</div></div>
    <div class="rates-money-kpi ${ratesMoneyKpiClass(d.impacto_hogar_pf)}"><div class="tag">Cambio en plazo fijo</div><div class="big">${ratesMoneyArs(d.impacto_hogar_pf,2,true)}</div><div class="mini"><b>${ratesMoneyChangeWord(d.impacto_hogar_pf)}</b> respecto de la ventana espejo.</div></div>
    <div class="rates-money-kpi ${ratesMoneyKpiClass(p.impacto_hogar_total_ampliado)}"><div class="tag">Saldo ampliado · post-shock</div><div class="big">${ratesMoneyArs(p.impacto_hogar_total_ampliado,2,true)}</div><div class="mini"><b>${ratesMoneyWord(p.impacto_hogar_total_ampliado)}</b> contra las normas históricas.</div></div>
    <div class="rates-money-kpi ${ratesMoneyKpiClass(m.impacto_hogar_total_ampliado)}"><div class="tag">Saldo ampliado · espejo</div><div class="big">${ratesMoneyArs(m.impacto_hogar_total_ampliado,2,true)}</div><div class="mini"><b>${ratesMoneyWord(m.impacto_hogar_total_ampliado)}</b> contra las normas históricas.</div></div>`;
  const beforeTotal=document.getElementById('ratesUsuryBeforeTotal');
  const afterTotal=document.getElementById('ratesUsuryAfterTotal');
  const effectTotal=document.getElementById('ratesUsuryEffectTotal');
  const effectPct=document.getElementById('ratesUsuryEffectPct');
  if(beforeTotal)beforeTotal.textContent=ratesMoneyCompact(m.impacto_hogar_total_ampliado);
  if(afterTotal)afterTotal.textContent=ratesMoneyCompact(p.impacto_hogar_total_ampliado);
  if(effectTotal)effectTotal.textContent=ratesMoneyCompact(d.impacto_hogar_total_ampliado);
  const improvementPct=d.impacto_hogar_total_ampliado/Math.abs(m.impacto_hogar_total_ampliado)*100;
  if(effectPct)effectPct.textContent=`${Math.abs(improvementPct).toLocaleString('es-AR',{minimumFractionDigits:1,maximumFractionDigits:1})}% · ${ratesMoneyChangeWord(d.impacto_hogar_total_ampliado)} vs espejo`;
  const publicAfter=document.getElementById('ratesPublicAfter');
  const publicBefore=document.getElementById('ratesPublicBefore');
  const publicEffect=document.getElementById('ratesPublicEffect');
  const publicEffectPct=document.getElementById('ratesPublicEffectPct');
  const publicConclusion=document.getElementById('ratesPublicConclusion');
  if(publicAfter)publicAfter.textContent=ratesMoneyArs(p.impacto_hogar_total_ampliado,2,true);
  if(publicBefore)publicBefore.textContent=ratesMoneyArs(m.impacto_hogar_total_ampliado,2,true);
  if(publicEffect)publicEffect.textContent=ratesMoneyArs(d.impacto_hogar_total_ampliado,2,true);
  if(publicEffectPct)publicEffectPct.textContent=`${Math.abs(improvementPct).toLocaleString('es-AR',{minimumFractionDigits:1,maximumFractionDigits:1})}% · ${ratesMoneyChangeWord(d.impacto_hogar_total_ampliado)} frente a la ventana anterior`;
  if(publicConclusion)publicConclusion.innerHTML=`<b>Lectura rápida:</b> crédito bancario <b>${ratesMoneyChangeWord(d.impacto_hogar_banco)} ${ratesMoneyArs(d.impacto_hogar_banco,2,true)}</b>; Fintech <b>${ratesMoneyChangeWord(d.impacto_hogar_fintech)} ${ratesMoneyArs(d.impacto_hogar_fintech,2,true)}</b>; plazo fijo <b>${ratesMoneyChangeWord(d.impacto_hogar_pf)} ${ratesMoneyArs(d.impacto_hogar_pf,2,true)}</b>. El balance ampliado <b>${ratesMoneyChangeWord(d.impacto_hogar_total_ampliado)} ${ratesMoneyArs(d.impacto_hogar_total_ampliado,2,true)}</b>, aunque el saldo post-shock siguió ${ratesMoneyWord(p.impacto_hogar_total_ampliado)}.`;
  document.getElementById('ratesMoneyNormalized').innerHTML=`<div class="full"><b>Diferencial por patas:</b> banco ${ratesMoneyChangeWord(d.impacto_hogar_banco)} ${ratesMoneyArs(d.impacto_hogar_banco,2,true)} · Fintech ${ratesMoneyChangeWord(d.impacto_hogar_fintech)} ${ratesMoneyArs(d.impacto_hogar_fintech,2,true)} · PF ${ratesMoneyChangeWord(d.impacto_hogar_pf)} ${ratesMoneyArs(d.impacto_hogar_pf,2,true)} · balance ampliado ${ratesMoneyChangeWord(d.impacto_hogar_total_ampliado)} ${ratesMoneyArs(d.impacto_hogar_total_ampliado,2,true)}.</div><div><b>Sin Fintech:</b> el balance banco + PF mejoró ${ratesMoneyArs(d.impacto_hogar_total,2,true)}.</div><div><b>Fintech:</b> ${p.fintech_meses_tna_observada} meses con TNA oficial y ${p.fintech_meses_tna_conservada} meses estimados hasta jul-2026.</div>`;
  const table=document.getElementById('ratesMoneyTableBody');
  table.innerHTML=ratesMoneyRows.map(r=>`<tr><td>${r.fecha}${r.fintech_tasa_observada?'':' *'}</td><td>${ratesMoneyArs(r.monto_personales)}</td><td class="${Number(r.banco_brecha_tecnica_pp)>=0?'technical-pos':'technical-neg'}">${Number(r.banco_brecha_tecnica_pp).toLocaleString('es-AR',{minimumFractionDigits:2,maximumFractionDigits:2})} pp</td><td class="${ratesMoneySignedClass(r.impacto_hogar_banco_constante)}">${ratesMoneyArs(r.impacto_hogar_banco_constante,2,true)}</td><td>${ratesMoneyArs(r.monto_pf)}</td><td class="${Number(r.pf_brecha_pp)>=0?'pos':'neg'}">${Number(r.pf_brecha_pp).toLocaleString('es-AR',{minimumFractionDigits:2,maximumFractionDigits:2})} pp</td><td class="${ratesMoneySignedClass(r.impacto_hogar_pf_constante)}">${ratesMoneyArs(r.impacto_hogar_pf_constante,2,true)}</td><td class="${Number(r.fintech_brecha_tecnica_pp)>=0?'technical-pos':'technical-neg'}">${Number(r.fintech_brecha_tecnica_pp).toLocaleString('es-AR',{minimumFractionDigits:2,maximumFractionDigits:2})} pp</td><td class="${ratesMoneySignedClass(r.impacto_hogar_fintech_constante)}">${ratesMoneyArs(r.impacto_hogar_fintech_constante,2,true)}</td><td class="${ratesMoneySignedClass(r.impacto_hogar_total_ampliado)}">${ratesMoneyArs(r.impacto_hogar_total_ampliado,2,true)}</td></tr>`).join('');
  const fintech=s.fintech;
  document.getElementById('ratesFintechAmount').textContent=ratesMoneyArs(d.impacto_hogar_fintech,2,true);
  document.getElementById('ratesFintechNote').innerHTML=`<b>Diferencial Fintech post-shock vs espejo</b>. Saldo espejo ${ratesMoneyArs(m.impacto_hogar_fintech,2,true)} · post-shock ${ratesMoneyArs(p.impacto_hogar_fintech,2,true)}. La estimación usa TNA ponderada por saldos y stock real interpolado; marzo–julio 2026 conserva el último dato oficial. Es una proxy de carga financiera extraordinaria, <b>no de ganancia neta efectivamente cobrada</b>.`;
  const financialRelief=Math.max(0,-p.impacto_hogar_total_ampliado);
  const milei=document.getElementById('mileiFinancialAuditContent');
  if(milei)milei.innerHTML=`
    <div class="milei-financial-grid">
      <div class="milei-financial-item">
        <div class="audit-tag">Balance ampliado banco + Fintech + PF · pos-shock</div>
        <div class="audit-amount">${ratesMoneyArs(p.impacto_hogar_total_ampliado,2,true)}</div>
        <p>Ventana espejo: <b>${ratesMoneyArs(m.impacto_hogar_total_ampliado,2,true)}</b> · diferencial post − espejo: <b>${ratesMoneyArs(d.impacto_hogar_total_ampliado,2,true)}</b>.</p>
      </div>
      <div class="milei-financial-item fintech">
        <div class="audit-tag">Fintech · ya incorporado al balance ampliado</div>
        <div class="audit-amount">${ratesMoneyArs(d.impacto_hogar_fintech,2,true)}</div>
        <p>Diferencial Fintech entre ventanas. Saldo pos-shock: <b>${ratesMoneyArs(p.impacto_hogar_fintech,2,true)}</b>. Incluye ${p.fintech_meses_tna_observada} meses con TNA oficial y ${p.fintech_meses_tna_conservada} meses estimados.</p>
      </div>
    </div>
    <p class="milei-financial-summary"><b>Cómo entra en la cuenta de $18,43 billones:</b> si se eliminara por completo el saldo financiero negativo pos-shock del balance ampliado, el alivio potencial sería <b>${ratesMoneyArs(financialRelief)}</b>. Para responder si mejoró o empeoró, el dato correcto es el diferencial post − espejo: <b>${ratesMoneyArs(d.impacto_hogar_total_ampliado,2,true)}</b>. Sin Fintech, banco + PF da <b>${ratesMoneyArs(d.impacto_hogar_total,2,true)}</b>.</p>`;
  renderRatesMoneyCharts();
}
function renderRatesMoneyCharts(){
  if(typeof Plotly==='undefined')return;
  const s=ratesMoneySummary,d=s.diferencial,mobile=window.innerWidth<=720;
  const labels=['Cambio · crédito bancario','Cambio · Fintech','Cambio · plazo fijo','Cambio · banco + PF','Diferencial · balance ampliado'];
  const values=[d.impacto_hogar_banco,d.impacto_hogar_fintech,d.impacto_hogar_pf,d.impacto_hogar_total,d.impacto_hogar_total_ampliado];
  const axisMax=Math.max(...values.map(v=>Math.abs(v)))*1.18;
  Plotly.react('ratesMoneyChart',[{type:'bar',orientation:'h',x:values,y:labels,marker:{color:values.map(v=>v>0?'#59ad8a':v<0?'#d56589':'#aaa0ad'),line:{color:'#ffffff',width:1}},text:values.map(v=>ratesMoneyCompact(v)),textposition:'outside',cliponaxis:false,customdata:values.map(v=>ratesMoneyChangeWord(v)),hovertemplate:'<b>%{y}</b><br>Diferencial: <b>%{text}</b><br>%{customdata}<extra></extra>'}],{paper_bgcolor:'rgba(255,255,255,0)',plot_bgcolor:'#fffdfd',font:{color:'#5e4670',family:'Inter,system-ui,sans-serif'},height:mobile?520:450,margin:{l:mobile?155:205,r:mobile?38:70,t:48,b:68},xaxis:{title:'Cambio entre ventanas · izquierda = empeoró / derecha = mejoró',range:[-axisMax,axisMax],gridcolor:'#efe4f4',zeroline:true,zerolinecolor:'#695d70',zerolinewidth:2,fixedrange:true},yaxis:{automargin:true,fixedrange:true,autorange:'reversed'},showlegend:false,annotations:[{xref:'paper',yref:'paper',x:.02,y:1.08,text:'← empeoró',showarrow:false,font:{size:mobile?9:11,color:'#b0476d'}},{xref:'paper',yref:'paper',x:.98,y:1.08,text:'mejoró →',showarrow:false,xanchor:'right',font:{size:mobile?9:11,color:'#3f876b'}}]},{responsive:true,displaylogo:false,displayModeBar:false,scrollZoom:false,doubleClick:false});
  const fintechEl=document.getElementById('ratesFintechChart');
  if(fintechEl)fintechEl.innerHTML=`<div class="rates-fintech-snapshot">
    <div class="rates-fintech-metric"><div class="metric-tag">STOCK REAL DE CARTERA</div><div class="metric-value">${ratesMoneyArs(s.fintech.saldo_constante_jul_2026)}</div><div class="metric-note">Corte ${s.fintech.fecha}, reexpresado a jul-2026</div></div>
    <div class="rates-fintech-metric"><div class="metric-tag">BRECHA REAL</div><div class="metric-value">+${Number(s.fintech.brecha_pp).toLocaleString('es-AR',{minimumFractionDigits:2,maximumFractionDigits:2})} pp</div><div class="metric-note">contra promedio histórico Fintech</div></div>
    <div class="rates-fintech-metric exposure"><div class="metric-tag">IMPACTO HOGAR DEL MES</div><div class="metric-value">${ratesMoneyArs(s.fintech.impacto_hogar_mes_constante,2,true)}</div><div class="metric-note">proxy de carga; no ganancia neta</div></div>
  </div>`;
}
function downloadRatesImpactCsv(){
  const blob=new Blob(['\ufeff'+ratesImpactCsv],{type:'text/csv;charset=utf-8'});
  const url=URL.createObjectURL(blob),a=document.createElement('a');
  a.href=url;a.download='tasas_pinza_hogar_auditada.csv';document.body.appendChild(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),500);
}
renderRatesMoney();'''
    html = replace_regex_once(
        html,
        r"function ratesMoneyArs\(value, digits=2\)\{.*?\nrenderRatesMoney\(\);",
        rates_js,
    )

    html = replace_once(
        html,
        "const financialRelief=Math.max(0,ratesMoneySummary.post.pinza_neta_hogar);",
        "const financialRelief=Math.max(0,-ratesMoneySummary.post.impacto_hogar_total_ampliado);",
    )
    html = replace_once(
        html,
        "const fintechExposure=Math.max(0,ratesMoneySummary.fintech.exposicion_constante);",
        "const fintechExposure=Math.abs(ratesMoneySummary.diferencial.impacto_hogar_fintech);",
    )
    html = html.replace("Pinza banco/PF si se soluciona", "Balance financiero ampliado si se soluciona")
    html = html.replace("pinza banco/PF descontaría", "pinza ampliada descontaría")
    html = html.replace("Fintech · exposición visible", "Fintech · diferencial incluido")
    html = html.replace(
        "La capa Fintech de <b>${mileiCostMoney(fintechExposure)}</b> queda visible dentro de la auditoría financiera y representa ≈ <b>${mileiCostPct(fintechExposure,grossShock).toLocaleString('es-AR',{minimumFractionDigits:2,maximumFractionDigits:2})}%</b> de la cuenta madre.",
        "La pata Fintech de <b>${mileiCostMoney(fintechExposure)}</b> ya está incluida en la pinza ampliada y representa ≈ <b>${mileiCostPct(fintechExposure,grossShock).toLocaleString('es-AR',{minimumFractionDigits:2,maximumFractionDigits:2})}%</b> de la cuenta madre.",
    )
    html = html.replace(
        "Queda dentro de la misma escala financiera para mostrar su tamaño frente a la cuenta madre.",
        "Está incluida en el balance financiero ampliado; se muestra aquí sólo para transparentar su aporte.",
    )
    html = replace_once(
        html,
        "hoja 3 / Fintech / feb-2026.",
        "hoja 3 / stock real Fintech por cortes; hoja 5 / TNA Fintech mensual ponderada por saldos. Interpolación entre cortes y prolongación feb→jul-2026 identificada.",
    )

    html = replace_once(
        html,
        "['bank','Préstamo bancario',ratesAccumData.bancoReal,'costo']",
        "['bank','Desviación técnica banco (+ = crédito más caro)',ratesAccumData.bancoReal,'costo']",
    )
    html = replace_once(
        html,
        "['pf','Plazo fijo 30 días',ratesAccumData.pfReal,'rendimiento']",
        "['pf','PF · desviación e impacto hogar (+ = mejor)',ratesAccumData.pfReal,'rendimiento']",
    )
    html = replace_once(
        html,
        "['bancoReal','Préstamo bancario','#4d83ff']",
        "['bancoReal','Banco · desviación técnica (+ = más caro)','#4d83ff']",
    )
    html = replace_once(
        html,
        "['pfReal','Plazo fijo 30 días','#ff8d52']",
        "['pfReal','PF · desviación / impacto hogar (+ = mejor)','#ff8d52']",
    )
    html = replace_once(
        html,
        "title:'Saldo acumulado vs promedio · pp-mes'",
        "title:'Desviación técnica acumulada · pp-mes'",
    )

    return html


def main() -> None:
    if not INPUT_HTML.exists():
        raise RuntimeError(f"No existe la última versión esperada: {INPUT_HTML}")
    if OUTPUT_HTML.exists():
        raise RuntimeError(f"El archivo de salida ya existe y no se sobrescribirá: {OUTPUT_HTML}")

    source_hash = sha256(INPUT_HTML)
    source_html = INPUT_HTML.read_text(encoding="utf-8")
    annual = base.js_json_array(source_html, "annual")
    modern = base.js_json_array(source_html, "modern")
    baselines = base.historical_baselines(annual, modern)
    personal = base.read_bcra_txt(
        SOURCE_DIR / "tasas" / "bcra" / "tas2_ser.txt",
        base.PERSONAL_CODES,
        daily=False,
    )
    pf = base.read_bcra_txt(
        SOURCE_DIR / "tasas" / "bcra" / "tas1_ser.txt",
        base.PF_CODES,
        daily=True,
    )
    ipc = base.read_ipc()
    fintech_tna, fintech_stock_points = read_fintech_series()

    records = build_records(
        modern,
        baselines,
        personal,
        pf,
        ipc,
        fintech_tna,
        fintech_stock_points,
    )
    if len(records) != 64:
        raise RuntimeError(f"Se esperaban 64 meses y se obtuvieron {len(records)}")
    summary = build_summary(records, baselines)
    cleaned = rounded_records(records)
    fields = list(cleaned[0])
    write_csv(AUDIT_CSV, cleaned, fields)
    csv_content = AUDIT_CSV.read_text(encoding="utf-8-sig")
    AUDIT_MD.write_text(build_audit_markdown(summary), encoding="utf-8", newline="\n")
    html = build_html(source_html, cleaned, summary, csv_content)
    OUTPUT_HTML.write_text(html, encoding="utf-8", newline="\n")

    if sha256(INPUT_HTML) != source_hash:
        raise RuntimeError("El HTML de entrada cambió durante la auditoría")
    if not all(value.startswith("OK") for value in summary["tests"].values()):
        raise RuntimeError("Algún test obligatorio no terminó en OK")
    if "tasas_pinza_hogar_auditada.csv" not in html:
        raise RuntimeError("El HTML no enlaza el CSV auditado")

    print(
        json.dumps(
            {
                "input": str(INPUT_HTML),
                "input_sha256": source_hash,
                "output": str(OUTPUT_HTML),
                "csv": str(AUDIT_CSV),
                "audit_md": str(AUDIT_MD),
                "summary": summary,
            },
            ensure_ascii=True,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
