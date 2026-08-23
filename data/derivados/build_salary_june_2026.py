#!/usr/bin/env python3
"""Actualiza el tab de poder adquisitivo con salarios INDEC de junio de 2026.

El script parte del dashboard v122, lee las dos descargas oficiales de salarios y
el IPC nacional ya auditado en ``data/fuentes``, recalcula todas las series reales
y genera una nueva versión sin sobrescribir las anteriores.
"""

from __future__ import annotations

import csv
import json
import re
from pathlib import Path
from typing import Any


DATA_DIR = Path(__file__).resolve().parents[1]
ROOT_DIR = DATA_DIR.parent
INPUT_HTML = DATA_DIR / "dashboard_kawaii_122_efecto_tasas_antes_despues.html"
OUTPUT_NAME = "dashboard_kawaii_123_salarios_junio_2026.html"
OUTPUT_HTML = DATA_DIR / OUTPUT_NAME
ROOT_OUTPUT_HTML = ROOT_DIR / OUTPUT_NAME

WAGE_INDEX_CSV = (
    DATA_DIR
    / "fuentes"
    / "salarios"
    / "indec"
    / "indice_salarios_2026-08-20.csv"
)
WAGE_VARIATION_CSV = (
    DATA_DIR
    / "fuentes"
    / "salarios"
    / "indec"
    / "variacion_indice_salarios_2026-08-20.csv"
)
IPC_CSV = DATA_DIR / "fuentes" / "tasas" / "indec" / "serie_ipc_divisiones.csv"

JAN_2017 = "1/1/2017"
NOV_2023 = "1/11/2023"
MAY_2026 = "1/5/2026"
JUN_2026 = "1/6/2026"
JUN_ISO = "2026-06-01"


def number(value: str) -> float:
    text = value.strip()
    if not text or text.upper() == "NA":
        raise ValueError(f"Valor numérico ausente: {value!r}")
    return float(text.replace(".", "").replace(",", "."))


def rows_by(path: Path, key: str) -> dict[str, dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return {row[key]: row for row in csv.DictReader(handle, delimiter=";")}


def read_ipc() -> dict[str, float]:
    for encoding in ("utf-8-sig", "cp1252", "latin-1"):
        try:
            with IPC_CSV.open("r", encoding=encoding, newline="") as handle:
                rows = list(csv.DictReader(handle, delimiter=";"))
            break
        except UnicodeDecodeError:
            continue
    else:
        raise RuntimeError("No se pudo decodificar el CSV de IPC")
    return {
        f"{row['Periodo'][:4]}-{row['Periodo'][4:]}-01": number(row["Indice_IPC"])
        for row in rows
        if row["Codigo"] == "0"
        and row["Region"] == "Nacional"
        and len(row["Periodo"]) == 6
    }


def replace_once(text: str, old: str, new: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"Se esperaba 1 coincidencia y hubo {count}: {old[:100]!r}")
    return text.replace(old, new, 1)


def replace_const_json(text: str, name: str, value: Any) -> str:
    pattern = rf"const\s+{re.escape(name)}\s*=\s*(\{{.*?\}});"
    match = re.search(pattern, text, re.S)
    if not match:
        raise RuntimeError(f"No se encontró const {name}")
    payload = json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    return text[: match.start(1)] + payload + text[match.end(1) :]


def read_const_json(text: str, name: str) -> Any:
    match = re.search(rf"const\s+{re.escape(name)}\s*=\s*(\{{.*?\}});", text, re.S)
    if not match:
        raise RuntimeError(f"No se encontró const {name}")
    return json.loads(match.group(1))


def real_index(
    nominal_now: float,
    nominal_base: float,
    ipc_now: float,
    ipc_base: float,
) -> float:
    return (nominal_now / nominal_base) / (ipc_now / ipc_base) * 100


def es(value: float, digits: int = 2) -> str:
    return f"{value:.{digits}f}".replace(".", ",")


def accumulated_metrics(total: dict[str, list[float]]) -> dict[str, float | int | str]:
    dates = total["dates"]
    values = total["yNov"]
    base_index = dates.index("2023-11-01")
    post = values[base_index + 1 :]
    gross = sum(max(0.0, 1 - value / 100) for value in post)
    recovered = sum(max(0.0, value / 100 - 1) for value in post)
    net = sum(value / 100 - 1 for value in post)
    months = len(post)
    left_index = base_index - months
    mirror = sum(values[i] / 100 - 1 for i in range(left_index, base_index))
    return {
        "gross": gross,
        "recovered": recovered,
        "net": net,
        "months": months,
        "left": dates[left_index],
        "mirror": mirror,
    }


def main() -> None:
    wage_rows = rows_by(WAGE_INDEX_CSV, "periodo")
    variation_rows = rows_by(WAGE_VARIATION_CSV, "periodo")
    ipc = read_ipc()
    january = wage_rows[JAN_2017]
    november = wage_rows[NOV_2023]
    may = wage_rows[MAY_2026]
    june = wage_rows[JUN_2026]
    variation = variation_rows[JUN_2026]

    ipc_jan = ipc["2017-01-01"]
    ipc_nov = ipc["2023-11-01"]
    ipc_may = ipc["2026-05-01"]
    ipc_jun = ipc[JUN_ISO]
    cpi_ratio = ipc_jun / ipc_nov

    # Controles contra el comunicado oficial, antes de tocar el HTML.
    assert abs(number(variation["v_m_indice_total"]) - 2.89) < 0.001
    assert abs(number(variation["v_acum_indice_total"]) - 18.48) < 0.001
    assert abs(ipc_jun / ipc_may * 100 - 101.886871) < 0.001

    column_by_series = {
        "Total registrado (INDEC)": "IS_total_registrado",
        "Privado registrado": "IS_sector_privado_registrado",
        "Público registrado": "IS_sector_publico",
        "Privado no registrado (EPH, rezago ~5 meses)": "IS_sector_no_registrado",
    }

    html = INPUT_HTML.read_text(encoding="utf-8")
    power_data = read_const_json(html, "powerData")
    june_index = power_data["dates"].index(JUN_ISO)
    results: dict[str, dict[str, float]] = {}

    for series in power_data["series"]:
        column = column_by_series.get(series["name"])
        if not column:
            continue
        y_nov = real_index(number(june[column]), number(november[column]), ipc_jun, ipc_nov)
        y_jan = real_index(number(june[column]), number(january[column]), ipc_jun, ipc_jan)
        series["yNov"][june_index] = round(y_nov, 6)
        series["yJan"][june_index] = round(y_jan, 6)
        results[series["name"]] = {"yNov": y_nov, "yJan": y_jan}

    total_all = read_const_json(html, "powerTotalAllOfficial")
    total_column = "IS_indice_total"
    total_y_nov = real_index(
        number(june[total_column]), number(november[total_column]), ipc_jun, ipc_nov
    )
    total_y_jan = real_index(
        number(june[total_column]), number(january[total_column]), ipc_jun, ipc_jan
    )
    if JUN_ISO in total_all["dates"]:
        total_index = total_all["dates"].index(JUN_ISO)
        total_all["yNov"][total_index] = round(total_y_nov, 6)
        total_all["yJan"][total_index] = round(total_y_jan, 6)
    else:
        total_all["dates"].append(JUN_ISO)
        total_all["yNov"].append(round(total_y_nov, 6))
        total_all["yJan"].append(round(total_y_jan, 6))

    metrics = accumulated_metrics(total_all)
    nominal_monthly = number(variation["v_m_indice_total"])
    nominal_h1 = number(variation["v_acum_indice_total"])
    inflation_monthly = (ipc_jun / ipc_may - 1) * 100
    inflation_h1 = (ipc_jun / ipc["2025-12-01"] - 1) * 100
    real_monthly = (
        (number(june[total_column]) / number(may[total_column]))
        / (ipc_jun / ipc_may)
        - 1
    ) * 100

    registered = results["Total registrado (INDEC)"]["yNov"]
    private = results["Privado registrado"]["yNov"]
    public = results["Público registrado"]["yNov"]
    unregistered = results["Privado no registrado (EPH, rezago ~5 meses)"]["yNov"]

    # Masa salarial contrafactual, idéntica a la metodología previa pero cerrada a junio.
    salaried_registered = 8_700_000
    salaried_unregistered = 5_100_000
    salaried = salaried_registered + salaried_unregistered
    avg_q3 = (
        salaried_registered * 229_521 + salaried_unregistered * 103_755
    ) / salaried
    avg_wage_index_q3 = (1519.50 + 1635.33 + 1826.29) / 3
    wage_base_nov = avg_q3 * (2157.73 / avg_wage_index_q3)
    base_monthly_mass = wage_base_nov * salaried
    net_nov = -float(metrics["net"]) * base_monthly_mass
    net_current = net_nov * cpi_ratio

    # JSON embebido: fuente del gráfico y del CSV descargable.
    html = replace_const_json(html, "powerData", power_data)
    html = replace_const_json(html, "powerTotalAllOfficial", total_all)

    # Cierre editorial y tabla principal del primer tab.
    html = replace_once(html, "📌 cierre editorial · 19 ago 2026", "📌 cierre editorial · 20 ago 2026")
    html = replace_once(html, "cerrada al <b>19/08/2026</b>", "cerrada al <b>20/08/2026</b>")
    html = replace_once(html, "const DASHBOARD_SNAPSHOT_CUTOFF = '2026-08-19';", "const DASHBOARD_SNAPSHOT_CUTOFF = '2026-08-20';")

    old_rows = """            <tr><td>Total salarios <span class=\"power-method-pill\">incluye no registrado EPH</span></td><td>May-2026</td><td>103,19</td></tr>
            <tr><td>Total registrado (INDEC)</td><td>May-2026</td><td>91,30</td></tr>
            <tr><td>Privado registrado</td><td>May-2026</td><td>96,40</td></tr>
            <tr><td>Público registrado</td><td>May-2026</td><td>82,24</td></tr>
            <tr><td>Privado no registrado <span class=\"power-method-pill\">estimación EPH · rezago ~5m</span></td><td>May-2026</td><td>180,34</td></tr>"""
    new_rows = f"""            <tr><td>Total salarios <span class=\"power-method-pill\">incluye no registrado EPH</span></td><td>Jun-2026</td><td>{es(total_y_nov)}</td></tr>
            <tr><td>Total registrado (INDEC)</td><td>Jun-2026</td><td>{es(registered)}</td></tr>
            <tr><td>Privado registrado</td><td>Jun-2026</td><td>{es(private)}</td></tr>
            <tr><td>Público registrado</td><td>Jun-2026</td><td>{es(public)}</td></tr>
            <tr><td>Privado no registrado <span class=\"power-method-pill\">estimación EPH · rezago ~5m</span></td><td>Jun-2026</td><td>{es(unregistered)}</td></tr>"""
    html = replace_once(html, old_rows, new_rows)

    recovery_note = f"""        <div class=\"note good\" style=\"margin-top:12px\"><b>Junio 2026 · recuperación real:</b> el Total índice de salarios subió <b>{es(nominal_monthly, 1)}%</b> y el IPC <b>{es(inflation_monthly, 1)}%</b>. Eso equivale a <b>+{es(real_monthly)}% real mensual</b> y completa <b>4 meses consecutivos</b> de mejora. En el primer semestre: salarios <b>+{es(nominal_h1, 1)}%</b> frente a inflación <b>+{es(inflation_h1, 1)}%</b>.</div>
"""
    html = replace_once(
        html,
        "        </table>\n        <div class=\"note warn\" style=\"margin-top:12px\"><b>Extensión histórica:</b>",
        "        </table>\n" + recovery_note + "        <div class=\"note warn\" style=\"margin-top:12px\"><b>Extensión histórica:</b>",
    )

    old_total_note = """<div class=\"note good\"><b>Total salarios · incluye registrado + no registrado:</b> es el <b>“Total índice de salarios” oficial de INDEC</b>. Pondera masas salariales del período base: <b>50,16% privado registrado + 29,91% público + 19,93% privado no registrado</b>. En mayo de 2026 da <b>103,19</b> con nov-2023=100: ≈ <b>+3,19% real</b> respecto de la base. Como incorpora al no registrado, también hereda la cautela metodológica de la estimación EPH con rezago.</div>"""
    new_total_note = f"""<div class=\"note good\"><b>Total salarios · incluye registrado + no registrado:</b> es el <b>“Total índice de salarios” oficial de INDEC</b>. Pondera masas salariales del período base: <b>50,16% privado registrado + 29,91% público + 19,93% privado no registrado</b>. En junio de 2026 da <b>{es(total_y_nov)}</b> con nov-2023=100: ≈ <b>+{es(total_y_nov - 100)}% real</b> respecto de la base. Como incorpora al no registrado, también hereda la cautela metodológica de la estimación EPH con rezago.</div>"""
    html = replace_once(html, old_total_note, new_total_note)
    html = replace_once(
        html,
        "https://www.indec.gob.ar/uploads/informesdeprensa/salarios_07_2651AD962B45.pdf\">📄 INDEC · salarios may-2026",
        "https://www.indec.gob.ar/uploads/informesdeprensa/salarios_08_26D1A1A01CB7.pdf\">📄 INDEC · salarios jun-2026",
    )

    # Fórmulas visibles: junio y todos los saldos dependientes.
    old_total_formula = """        <div class=\"formula-card favorable\">
          <div class=\"formula-title\">Total salarios · incluye no registrado · mayo 2026</div>
          <div class=\"formula\">[(9.177,39 / 2.157,73) / 4,12183] × 100 = 103,19</div>
          <div class=\"formula-result\">≈ +3,19% real frente a nov-2023</div>
          <div class=\"formula-caveat\"><b>9.177,39</b> y <b>2.157,73</b> son el “Total índice de salarios” nominal oficial de INDEC en may-2026 y nov-2023. <b>4,12183</b> es IPC may-2026 / IPC nov-2023 usando el mismo IPC nivel general del gráfico. El dashboard <b>no promedia a mano</b> 91,30 y 180,34: toma el total oficial de INDEC y sólo lo deflacta/rebasea.</div>
        </div>"""
    new_total_formula = f"""        <div class=\"formula-card favorable\">
          <div class=\"formula-title\">Total salarios · incluye no registrado · junio 2026</div>
          <div class=\"formula\">[(9.442,50 / 2.157,73) / {es(cpi_ratio, 5)}] × 100 = {es(total_y_nov)}</div>
          <div class=\"formula-result\">≈ +{es(total_y_nov - 100)}% real frente a nov-2023</div>
          <div class=\"formula-caveat\"><b>9.442,50</b> y <b>2.157,73</b> son el “Total índice de salarios” nominal oficial de INDEC en jun-2026 y nov-2023. <b>{es(cpi_ratio, 5)}</b> es IPC jun-2026 / IPC nov-2023 usando el mismo IPC nivel general del gráfico. El dashboard <b>no promedia a mano</b> {es(registered)} y {es(unregistered)}: toma el total oficial de INDEC y sólo lo deflacta/rebasea.</div>
        </div>
        <div class=\"formula-card favorable\">
          <div class=\"formula-title\">Recuperación real · junio 2026</div>
          <div class=\"formula\">[(1 + {es(nominal_monthly, 2)}%) / (1 + {es(inflation_monthly, 2)}%)] − 1 = +{es(real_monthly)}%</div>
          <div class=\"formula-result\">Cuarto mes consecutivo con salarios por encima del IPC</div>
          <div class=\"formula-caveat\">En el primer semestre el índice salarial acumuló <b>+{es(nominal_h1, 2)}%</b> y el IPC <b>+{es(inflation_h1, 2)}%</b>. La comparación mensual real usa los niveles oficiales, no sólo las variaciones redondeadas del comunicado.</div>
        </div>"""
    html = replace_once(html, old_total_formula, new_total_formula)

    html = replace_once(
        html,
        "0,9377 × $237.872 × 13,8 M = ≈ $3,08 billones de nov-2023",
        f"{es(-float(metrics['net']), 4)} × $237.872 × 13,8 M = ≈ ${es(net_nov / 1e12)} billones de nov-2023",
    )
    html = replace_once(
        html,
        "× 4,12183 de IPC = ≈ $12,69 billones a precios de may-2026",
        f"× {es(cpi_ratio, 5)} de IPC = ≈ ${es(net_current / 1e12)} billones a precios de jun-2026",
    )
    html = replace_once(
        html,
        "Dic-2023 → may-2026: pérdida bruta ≈ 1,34 · recuperación ≈ 0,40 · saldo neto ≈ −0,94 sueldos-base",
        f"Dic-2023 → jun-2026: pérdida bruta ≈ {es(float(metrics['gross']))} · recuperación ≈ {es(float(metrics['recovered']))} · saldo neto ≈ −{es(-float(metrics['net']))} sueldos-base",
    )
    html = replace_once(
        html,
        "Σ [(índiceₜ − 100) / 100] durante los 30 meses previos",
        f"Σ [(índiceₜ − 100) / 100] durante los {metrics['months']} meses previos",
    )
    html = replace_once(
        html,
        "May-2021 → oct-2023: ≈ +2,03 sueldos-base por encima del nivel de nov-2023",
        f"Abr-2021 → oct-2023: ≈ +{es(float(metrics['mirror']))} sueldos-base por encima del nivel de nov-2023",
    )

    sector_cards = {
        """<div class=\"formula-title\">Total registrado · mayo 2026</div>
          <div class=\"formula\">(91,30 / 100 − 1) × 100 = −8,70%</div>
          <div class=\"formula-result\">≈ 8,70% menos poder adquisitivo que en nov-2023</div>""":
        f"""<div class=\"formula-title\">Total registrado · junio 2026</div>
          <div class=\"formula\">({es(registered)} / 100 − 1) × 100 = −{es(100 - registered)}%</div>
          <div class=\"formula-result\">≈ {es(100 - registered)}% menos poder adquisitivo que en nov-2023</div>""",
        """<div class=\"formula-title\">Sector público · mayo 2026</div>
          <div class=\"formula\">(82,24 / 100 − 1) × 100 = −17,76%</div>
          <div class=\"formula-result\">≈ 17,76% menos que la base</div>""":
        f"""<div class=\"formula-title\">Sector público · junio 2026</div>
          <div class=\"formula\">({es(public)} / 100 − 1) × 100 = −{es(100 - public)}%</div>
          <div class=\"formula-result\">≈ {es(100 - public)}% menos que la base</div>""",
        """<div class=\"formula-title\">Privado registrado · mayo 2026</div>
          <div class=\"formula\">(96,40 / 100 − 1) × 100 = −3,60%</div>""":
        f"""<div class=\"formula-title\">Privado registrado · junio 2026</div>
          <div class=\"formula\">({es(private)} / 100 − 1) × 100 = −{es(100 - private)}%</div>""",
    }
    for old, new in sector_cards.items():
        html = replace_once(html, old, new)

    # Parámetros de la cuenta agregada y redacción dinámica del tab principal.
    old_params = """  wageIndexNov2023:2157.73,
  wageIndexMay2026:9177.39,

  // Mismo deflactor del gráfico:
  cpiMay2026VsNov2023:4.12183"""
    new_params = f"""  wageIndexNov2023:2157.73,
  wageIndexJun2026:9442.50,

  // Mismo deflactor del gráfico:
  cpiJun2026VsNov2023:{cpi_ratio:.8f}"""
    html = replace_once(html, old_params, new_params)
    html = html.replace("p.cpiMay2026VsNov2023", "p.cpiJun2026VsNov2023")
    html = html.replace("powerAggregateLossParams.cpiMay2026VsNov2023", "powerAggregateLossParams.cpiJun2026VsNov2023")
    html = replace_once(html, "pesos de may-2026 · hasta el último dato salarial comparable", "pesos de jun-2026 · hasta el último dato salarial comparable")

    # Homogeneiza también Mercado Libre a junio para mantener comparables las escalas.
    html = html.replace("meli.may26Bn", "meli.jun26Bn")
    html = html.replace("meliRecent?.may26Bn", "meliRecent?.jun26Bn")
    html = html.replace("meliArsMay26", "meliArsJun26")
    html = html.replace("massMay26", "massJun26")
    html = replace_once(
        html,
        "const mayRatio=meliCpiRatioFromPension('2026-05-01');",
        "const junRatio=meliCpiRatioFromPension('2026-06-01');",
    )
    html = html.replace("may26Bn", "jun26Bn")
    html = html.replace("mayRatio", "junRatio")
    html = html.replace("mayo-2026", "junio-2026")
    html = html.replace("pesos de may-2026", "pesos de jun-2026")
    html = html.replace("equivalente may-26", "equivalente jun-26")
    html = html.replace("homogéneo may-26", "homogéneo jun-26")
    html = html.replace("homogeneizados a may-26", "homogeneizados a jun-26")
    html = html.replace("2024–1T26 a may-26", "2024–1T26 a jun-26")
    html = html.replace("ARS a may-26", "ARS a jun-26")
    html = html.replace("IPC a may-26", "IPC a jun-26")
    html = html.replace("may26", "jun26")
    html = replace_once(html, "≈ $ 218,95 mil M", "≈ $ 223,08 mil M")

    OUTPUT_HTML.write_text(html, encoding="utf-8", newline="\n")
    ROOT_OUTPUT_HTML.write_text(html, encoding="utf-8", newline="\n")

    print(f"Generado: {OUTPUT_HTML}")
    print(f"Generado: {ROOT_OUTPUT_HTML}")
    print(
        "Junio 2026:",
        {
            "total_real_nov2023_100": round(total_y_nov, 6),
            "total_registrado": round(registered, 6),
            "privado_registrado": round(private, 6),
            "publico": round(public, 6),
            "no_registrado": round(unregistered, 6),
            "recuperacion_real_mensual_pct": round(real_monthly, 6),
            "saldo_neto_sueldos_base": round(float(metrics["net"]), 6),
            "brecha_pesos_jun2026": round(net_current),
        },
    )


if __name__ == "__main__":
    main()
