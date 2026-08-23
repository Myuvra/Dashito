#!/usr/bin/env python3
"""Construye la simulación auditable de un aporte progresivo de grandes fortunas.

Base primaria: ARCA, Anuario de Estadísticas Tributarias 2023, cuadro
2.5.1.2.1.1 (Bienes Personales, período fiscal 2022). Los importes oficiales
están en millones de pesos corrientes y se reexpresan a junio de 2026 con IPC
nacional de INDEC. La cola abierta superior se reparte con una Pareto calibrada
para conservar exactamente casos y patrimonio oficial del tramo.
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
import re
import shutil
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
DATA = ROOT / "data"
SOURCES = DATA / "fuentes" / "grandes_fortunas"
OUTPUT_HTML = DATA / "dashboard_kawaii_133_aporte_grandes_fortunas.html"
TARGET = 4.98e12
FX_JUN_2026 = 1450.2728  # BCRA A3500, promedio mensual ya embebido en el dashboard.
ANNUAL_WAGE_JUN_2026 = 11_987_664.340695  # Misma masa salarial urbana del primer tab.


# limite inferior, superior, casos con bienes, bienes totales, bienes país, exterior.
# Importes patrimoniales: millones de pesos corrientes del período fiscal 2022.
AFIP_ROWS = [
    (0, 11, 477_962, 2_425_396, 2_379_315, 46_081),
    (11, 15, 100_288, 1_283_288, 1_235_956, 47_332),
    (15, 30, 159_308, 3_337_401, 3_115_394, 222_007),
    (30, 45, 55_052, 2_009_418, 1_751_164, 258_254),
    (45, 60, 27_438, 1_419_775, 1_152_057, 267_718),
    (60, 75, 16_096, 1_077_775, 823_813, 253_962),
    (75, 90, 10_640, 873_543, 626_818, 246_725),
    (90, 105, 7_561, 734_168, 502_136, 232_032),
    (105, 120, 5_678, 637_145, 408_211, 228_933),
    (120, 135, 4_456, 566_721, 348_600, 218_122),
    (135, 150, 3_547, 504_350, 298_584, 205_766),
    (150, 165, 2_970, 467_238, 257_734, 209_504),
    (165, 180, 2_537, 437_235, 235_273, 201_962),
    (180, 195, 2_097, 392_930, 202_103, 190_827),
    (195, 210, 1_773, 358_487, 177_988, 180_500),
    (210, 225, 1_500, 325_879, 157_186, 168_694),
    (225, 240, 1_299, 301_666, 142_550, 159_115),
    (240, 255, 1_205, 298_275, 140_796, 157_480),
    (255, 270, 1_067, 280_032, 125_565, 154_466),
    (270, 285, 997, 276_988, 114_300, 162_689),
    (285, 300, 784, 229_418, 93_659, 135_759),
    (300, 350, 2_171, 701_843, 282_565, 419_278),
    (350, 400, 1_528, 569_326, 231_272, 338_054),
    (400, 450, 1_091, 462_242, 184_825, 277_416),
    (450, 500, 739, 350_570, 143_718, 206_851),
    (500, 550, 622, 325_569, 123_565, 202_004),
    (550, 600, 547, 314_695, 109_630, 205_065),
    (600, 650, 422, 263_389, 95_825, 167_564),
    (650, 700, 353, 238_203, 78_278, 159_924),
    (700, 750, 293, 212_246, 72_422, 139_823),
    (750, 800, 257, 199_031, 67_355, 131_676),
    (800, 850, 221, 182_231, 55_840, 126_391),
    (850, 900, 226, 197_925, 63_417, 134_508),
    (900, 950, 171, 158_042, 51_954, 106_087),
    (950, 1_000, 175, 170_747, 51_288, 119_459),
    (1_000, 1_200, 504, 552_938, 167_746, 385_192),
    (1_200, 1_300, 166, 206_928, 59_842, 147_086),
    (1_300, 1_400, 153, 206_134, 58_508, 147_626),
    (1_400, 1_600, 217, 322_864, 88_981, 233_882),
    (1_600, 1_800, 149, 251_778, 67_866, 183_912),
    (1_800, 2_000, 119, 225_091, 51_641, 173_450),
    (2_000, 3_000, 329, 802_951, 184_671, 618_280),
    (3_000, 4_000, 130, 443_547, 110_697, 332_851),
    (4_000, 5_000, 92, 408_112, 68_961, 339_151),
    (5_000, None, 181, 1_919_100, 461_308, 1_457_792),
]


def read_cpi() -> dict[str, float]:
    path = DATA / "fuentes" / "tasas" / "indec" / "serie_ipc_divisiones.csv"
    out: dict[str, float] = {}
    with path.open(encoding="utf-8-sig", errors="replace", newline="") as fh:
        for row in csv.DictReader(fh, delimiter=";"):
            if row["Codigo"] == "0" and row["Region"] == "Nacional":
                out[row["Periodo"]] = float(row["Indice_IPC"].replace(",", "."))
    return out


def calibrated_closed_nodes(lo: float, hi: float, mean: float, cases: float, pieces: int = 9):
    """Curva monótona dentro del intervalo cuya media coincide con la oficial."""
    qs = [(i + 0.5) / pieces for i in range(pieces)]
    ratio = min(0.999999, max(0.000001, (mean - lo) / (hi - lo)))
    low, high = 0.02, 60.0
    for _ in range(90):
        gamma = (low + high) / 2
        got = sum(q**gamma for q in qs) / pieces
        if got > ratio:
            low = gamma
        else:
            high = gamma
    gamma = (low + high) / 2
    vals = [lo + (hi - lo) * q**gamma for q in qs]
    return [{"w": value, "n": cases / pieces} for value in vals]


def pareto_open_nodes(lo: float, mean: float, cases: float, pieces: int = 64):
    """Cola Pareto calibrada por el mínimo y la media oficial del tramo abierto."""
    ratio = mean / lo
    alpha = ratio / (ratio - 1)
    qs = [(i + 0.5) / pieces for i in range(pieces)]
    vals = [lo / (1 - q) ** (1 / alpha) for q in qs]
    scale = mean / (sum(vals) / pieces)
    vals = [value * scale for value in vals]
    return [{"w": value, "n": cases / pieces} for value in vals], alpha


def make_nodes(inflation_factor: float, method: str = "curva_pareto"):
    nodes = []
    alpha = None
    for idx, (lo_m, hi_m, cases, assets_m, _domestic_m, _foreign_m) in enumerate(AFIP_ROWS):
        lo = lo_m * 1e6 * inflation_factor
        hi = hi_m * 1e6 * inflation_factor if hi_m is not None else None
        mean = assets_m * 1e6 * inflation_factor / cases
        if method == "promedio_oficial" or hi is None and method == "curva_sin_cola":
            row_nodes = [{"w": mean, "n": cases}]
        elif hi is None:
            row_nodes, alpha = pareto_open_nodes(lo, mean, cases)
        else:
            row_nodes = calibrated_closed_nodes(lo, hi, mean, cases)
        for node in row_nodes:
            node["row"] = idx
            nodes.append(node)
    return nodes, alpha


def wealth_weight(wealth: float) -> float:
    if wealth < 3e9:
        return 1.0
    if wealth < 10e9:
        return 1.5
    if wealth < 50e9:
        return 2.0
    if wealth < 250e9:
        return 3.0
    return 4.0


def weighted_quantile(pairs, quantile=0.5):
    values = sorted((v, n) for v, n in pairs if n > 0)
    total = sum(n for _, n in values)
    if not values or total <= 0:
        return 0.0
    cursor = 0.0
    for value, count in values:
        cursor += count
        if cursor >= total * quantile:
            return value
    return values[-1][0]


def band_label(wealth: float) -> str:
    if wealth < 1e9:
        return "< $1 B"
    if wealth < 3e9:
        return "$1–3 B"
    if wealth < 10e9:
        return "$3–10 B"
    if wealth < 50e9:
        return "$10–50 B"
    if wealth < 250e9:
        return "$50–250 B"
    return "> $250 B"


BAND_ORDER = ["< $1 B", "$1–3 B", "$3–10 B", "$10–50 B", "$50–250 B", "> $250 B"]


def solve(nodes, threshold: float, participation: float, cap: float, target: float = TARGET):
    eligible = [node for node in nodes if node["w"] > threshold]

    def contribution(node, lam):
        raw = lam * wealth_weight(node["w"]) * max(node["w"] - threshold, 0)
        return min(raw, cap * node["w"])

    maximum = participation * sum(cap * node["w"] * node["n"] for node in eligible)
    feasible = maximum + 1 >= target
    if feasible:
        low, high = 0.0, 1.0
        while participation * sum(contribution(n, high) * n["n"] for n in eligible) < target:
            high *= 2
        for _ in range(100):
            mid = (low + high) / 2
            revenue = participation * sum(contribution(n, mid) * n["n"] for n in eligible)
            if revenue < target:
                low = mid
            else:
                high = mid
        lam = high
    else:
        lam = 1e6

    rows = []
    for node in eligible:
        amount = contribution(node, lam)
        rows.append({**node, "aporte": amount, "tasa": amount / node["w"]})
    revenue = participation * sum(r["aporte"] * r["n"] for r in rows)
    contributors = participation * sum(r["n"] for r in rows)
    avg = revenue / contributors if contributors else 0
    median = weighted_quantile([(r["aporte"], r["n"]) for r in rows])
    median_rate = weighted_quantile([(r["tasa"], r["n"]) for r in rows])
    rates = [r["tasa"] for r in rows]

    bands = []
    for label in BAND_ORDER:
        selected = [r for r in rows if band_label(r["w"]) == label]
        count = participation * sum(r["n"] for r in selected)
        patrimonio = participation * sum(r["w"] * r["n"] for r in selected)
        aporte = participation * sum(r["aporte"] * r["n"] for r in selected)
        base = participation * sum(max(r["w"] - threshold, 0) * r["n"] for r in selected)
        if count:
            bands.append({
                "tramo": label,
                "aportantes_estimados": count,
                "patrimonio_total": patrimonio,
                "base_excedente": base,
                "aporte_total": aporte,
                "aporte_promedio": aporte / count,
                "tasa_efectiva_promedio": aporte / patrimonio if patrimonio else 0,
            })
    return {
        "threshold": threshold,
        "participation": participation,
        "cap": cap,
        "lambda": lam,
        "feasible": feasible,
        "revenue": min(revenue, maximum),
        "maximum": maximum,
        "gap": max(0, target - revenue),
        "contributors": contributors,
        "average": avg,
        "median": median,
        "min_rate": min(rates) if rates else 0,
        "median_rate": median_rate,
        "max_rate": max(rates) if rates else 0,
        "median_retained": 1 - median_rate,
        "bands": bands,
    }


def write_csv(path: Path, rows, fieldnames):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def stable_sources():
    arca_dir = SOURCES / "arca"
    used = next(arca_dir.rglob("2.5.1.2.1.1.xls"), None)
    stable = arca_dir / "bienes_personales_tramos_2022.xls"
    if used and not stable.exists():
        shutil.copy2(used, stable)
    wid_note = SOURCES / "wid" / "wid_contexto_argentina_2026.txt"
    wid_note.write_text(
        "World Inequality Report 2026 · Country sheets · Argentina\n"
        "URL: https://wir2026.wid.world/www-site/uploads/2025/11/WIR26_Country_Sheets.pdf\n"
        "Contexto, no base imponible: top 10% = 58,7% de la riqueza; top 1% = 24,2%; riqueza neta media = EUR PPP 51.922 (2024).\n"
        "La descarga directa fue rechazada por el host remoto el 2026-08-20; se conserva esta nota de extracción y el enlace original.\n",
        encoding="utf-8",
    )
    method_note = SOURCES / "metodologia" / "metodo_distribucion_y_cola.txt"
    method_note.write_text(
        "Los tramos cerrados se desagregan en nueve nodos monótonos dentro de cada intervalo. "
        "El exponente se calibra para reproducir la media oficial. El tramo abierto >$5.000 M "
        "se modela con Pareto calibrada por mínimo y media, preservando casos y patrimonio. "
        "No se usan rankings de personas ni se infiere evasión en el escenario base.\n",
        encoding="utf-8",
    )
    return stable, wid_note, method_note, arca_dir / "bienes_personales_declaracion_2026-08-20.html"


def update_manifest(files):
    manifest = DATA / "fuentes" / "FUENTES.csv"
    with manifest.open(encoding="utf-8-sig", newline="") as fh:
        existing_rows = list(csv.DictReader(fh))
    ids = {row["id"] for row in existing_rows}
    additions = [
        {
            "id": "arca_bp_tramos_2022", "tema": "grandes_fortunas", "institucion": "ARCA",
            "titulo": "Bienes Personales 2022: presentaciones y bienes por tramo",
            "url_original": "https://contenidos.afip.gob.ar/institucional/estudios/archivos/estadisticasTributarias/Estadisticas-Tributarias-2023.zip",
            "archivo_local": "/data/fuentes/grandes_fortunas/arca/bienes_personales_tramos_2022.xls",
            "fecha_descarga": "2026-08-20", "fecha_publicacion": "2024", "codigo_serie": "Cuadro 2.5.1.2.1.1",
            "periodo_utilizado": "fiscal 2022", "tipo": "XLS oficial", "sha256": sha256(files[0]),
            "nota": "Base patrimonial declarada; importes originales en millones de pesos corrientes",
        },
        {
            "id": "arca_estadisticas_tributarias_2023_zip", "tema": "grandes_fortunas", "institucion": "ARCA",
            "titulo": "Anuario de Estadísticas Tributarias 2023 · paquete completo",
            "url_original": "https://contenidos.afip.gob.ar/institucional/estudios/archivos/estadisticasTributarias/Estadisticas-Tributarias-2023.zip",
            "archivo_local": "/data/fuentes/grandes_fortunas/arca/Estadisticas-Tributarias-2023.zip",
            "fecha_descarga": "2026-08-20", "fecha_publicacion": "2024", "codigo_serie": "",
            "periodo_utilizado": "fiscal 2022", "tipo": "ZIP oficial", "sha256": sha256(SOURCES / "arca" / "Estadisticas-Tributarias-2023.zip"),
            "nota": "El checksum cubre el paquete original completo",
        },
        {
            "id": "aporte_solidario_informe_final", "tema": "aporte_solidario", "institucion": "Ministerio de Economía",
            "titulo": "Aporte Solidario y Extraordinario · informe final al 17/12/2021",
            "url_original": "https://www.argentina.gob.ar/sites/default/files/2021/12/aporte_solidario_final_2021.12.20.pdf",
            "archivo_local": "/data/fuentes/grandes_fortunas/aporte_solidario/aporte_solidario_final_2021-12-20.pdf",
            "fecha_descarga": "2026-08-20", "fecha_publicacion": "2021-12-20", "codigo_serie": "",
            "periodo_utilizado": "2021", "tipo": "PDF oficial", "sha256": sha256(SOURCES / "aporte_solidario" / "aporte_solidario_final_2021-12-20.pdf"),
            "nota": "$247.503 M al 17/12/2021; alrededor de 10.000 contribuyentes",
        },
        {
            "id": "afip_recaudacion_aporte_2021", "tema": "aporte_solidario", "institucion": "AFIP",
            "titulo": "Informe de recaudación · 4° trimestre 2021",
            "url_original": "https://contenidos.afip.gob.ar/institucional/estudios/archivos/informe-4-trimestre-2021.pdf",
            "archivo_local": "/data/fuentes/grandes_fortunas/aporte_solidario/afip_informe_recaudacion_4t_2021.pdf",
            "fecha_descarga": "2026-08-20", "fecha_publicacion": "2022", "codigo_serie": "Aporte Solidario",
            "periodo_utilizado": "2021", "tipo": "PDF oficial", "sha256": sha256(SOURCES / "aporte_solidario" / "afip_informe_recaudacion_4t_2021.pdf"),
            "nota": "$248.006 M recaudados en el año 2021",
        },
        {
            "id": "wid_argentina_wealth_2026", "tema": "concentracion_patrimonial", "institucion": "World Inequality Lab",
            "titulo": "World Inequality Report 2026 · Argentina country sheet",
            "url_original": "https://wir2026.wid.world/www-site/uploads/2025/11/WIR26_Country_Sheets.pdf",
            "archivo_local": "/data/fuentes/grandes_fortunas/wid/wid_contexto_argentina_2026.txt",
            "fecha_descarga": "2026-08-20", "fecha_publicacion": "2025-11", "codigo_serie": "wealth shares",
            "periodo_utilizado": "2024", "tipo": "nota de extracción", "sha256": sha256(files[1]),
            "nota": "Sólo contexto de concentración; no se mezcla con la base declarada de ARCA",
        },
        {
            "id": "gf_metodo_cola", "tema": "metodologia", "institucion": "Elaboración propia",
            "titulo": "Desagregación por tramos y cola abierta",
            "url_original": "", "archivo_local": "/data/fuentes/grandes_fortunas/metodologia/metodo_distribucion_y_cola.txt",
            "fecha_descarga": "2026-08-20", "fecha_publicacion": "2026-08-20", "codigo_serie": "",
            "periodo_utilizado": "2022 reexpresado a 2026-06", "tipo": "metodología", "sha256": sha256(files[2]),
            "nota": "Curva calibrada por tramo; Pareto sólo en el tramo superior abierto",
        },
        {
            "id": "arca_bienes_personales_pagina", "tema": "grandes_fortunas", "institucion": "ARCA",
            "titulo": "Bienes Personales · declaración jurada",
            "url_original": "https://www.arca.gob.ar/gananciasYBienes/bienes-personales/declaracion-jurada/",
            "archivo_local": "/data/fuentes/grandes_fortunas/arca/bienes_personales_declaracion_2026-08-20.html",
            "fecha_descarga": "2026-08-20", "fecha_publicacion": "", "codigo_serie": "",
            "periodo_utilizado": "consulta 2026-08-20", "tipo": "HTML oficial", "sha256": sha256(files[3]),
            "nota": "Copia local del redireccionamiento oficial de ARCA",
        },
    ]
    existing_rows.extend(row for row in additions if row["id"] not in ids)
    with manifest.open("w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=[
            "id", "tema", "institucion", "titulo", "url_original", "archivo_local", "fecha_descarga",
            "fecha_publicacion", "codigo_serie", "periodo_utilizado", "tipo", "sha256", "nota",
        ])
        writer.writeheader()
        writer.writerows(existing_rows)


def audit_markdown(factor, alpha, default, hist_real, threshold_real):
    return f"""# Auditoría · aporte voluntario progresivo de grandes fortunas

Fecha de construcción: 2026-08-20. Unidad común: pesos de junio de 2026.

1. **Pregunta.** Se prueba si un aporte patrimonial voluntario y progresivo puede compensar una meta de $4,98 billones sin superar un tope individual elegido.
2. **Base oficial.** ARCA, Anuario de Estadísticas Tributarias 2023, cuadro 2.5.1.2.1.1: 895.111 declaraciones con bienes y $27.922.627 millones declarados para el período fiscal 2022.
3. **Actualización.** IPC nacional INDEC dic-2022={read_cpi()['202212']:.4f}, jun-2026={read_cpi()['202606']:.4f}; factor={factor:.8f}. No se mezclan pesos nominales de años distintos.
4. **Universo.** Declarantes de Bienes Personales, no toda la población rica ni una lista de personas. Patrimonio declarado no equivale a ingreso anual ni a riqueza nacional WID.
5. **Distribución.** Los tramos cerrados se desagregan en nueve nodos dentro de sus límites y se calibran para preservar la media oficial.
6. **Cola abierta.** El tramo oficial >$5.000 millones de 2022 tiene 181 casos. Se usa Pareto α={alpha:.4f}, calibrada por mínimo y media, preservando casos y patrimonio. Es una estimación, no microdato.
7. **Fórmula.** aporteᵢ = min[λ × peso(patrimonioᵢ) × max(patrimonioᵢ−umbral,0), tope × patrimonioᵢ]. λ se resuelve por bisección para alcanzar la meta dada la participación.
8. **Participación.** 25/50/75/100% es participación esperada homogénea dentro de cada nodo. No modela selección estratégica; se muestra como escenario, no pronóstico conductual.
9. **Escenario inicial (tope 3%).** Umbral $1 B, 100% de participación, tope 3%: recaudación {default['revenue']/1e12:.6f} billones; {default['contributors']:.1f} aportantes esperados; tasa efectiva mediana {default['median_rate']*100:.4f}%.
10. **Comparación histórica.** El Aporte Solidario fue obligatorio, extraordinario y por única vez. AFIP informó $248.006 M en 2021; a precios de jun-2026 (aproximación dic-2021) son ${hist_real/1e12:.3f} billones. El mínimo legal de $200 M de dic-2020 equivale a ${threshold_real/1e9:.3f} B. No se lo llama antecedente legal del esquema voluntario.
11. **Subdeclaración.** El escenario base no corrige evasión, valuaciones ni activos omitidos. La sensibilidad +20% es mecánica y visible; WID se usa sólo para recordar que la riqueza neta nacional y la base fiscal declarada son universos diferentes.
12. **No doble conteo.** La contribución es una compensación hipotética separada. No aumenta el daño del tab “Lo que te robó Milei” ni se suma a pérdidas, privilegios, SIDE, Mercado Libre o la pinza financiera.

## Resultado histórico comparable

- Recaudación oficial 2021: $248.006 millones.
- Reexpresión aproximada a junio de 2026: ${hist_real:,.0f}.
- Aportantes informados: alrededor de 10.000.
- Pago medio real aproximado: ${hist_real/10_000:,.0f} por aportante.
- Tasas legales: 2%–3,5% sobre los bienes, con incremento para activos del exterior según la Ley 27.605.
- Tasa efectiva histórica promedio: **no publicada en los agregados oficiales revisados**; se evita inventarla.

## Archivos reproducibles

- `distribucion_patrimonial.csv`
- `simulacion_aporte_voluntario.csv`
- `sensibilidad_aporte.csv`
- `../lo_que_te_robo_reconciliacion.csv`
"""


def main():
    cpi = read_cpi()
    factor = cpi["202606"] / cpi["202212"]
    nodes, alpha = make_nodes(factor, "curva_pareto")
    default = solve(nodes, 1e9, 1.0, 0.03)

    distribution_rows = []
    for idx, (lo, hi, cases, total, domestic, foreign) in enumerate(AFIP_ROWS, 1):
        distribution_rows.append({
            "fila_oficial": idx,
            "tramo_original_millones_ars_2022": f"> {lo:,}" if hi is None else f"{lo:,}–{hi:,}",
            "limite_inferior_ars_jun_2026": round(lo * 1e6 * factor, 2),
            "limite_superior_ars_jun_2026": "" if hi is None else round(hi * 1e6 * factor, 2),
            "personas_con_bienes": cases,
            "patrimonio_total_ars_jun_2026": round(total * 1e6 * factor, 2),
            "patrimonio_promedio_ars_jun_2026": round(total * 1e6 * factor / cases, 2),
            "bienes_pais_ars_jun_2026": round(domestic * 1e6 * factor, 2),
            "bienes_exterior_ars_jun_2026": round(foreign * 1e6 * factor, 2),
            "fuente_primaria": "ARCA Anuario 2023, cuadro 2.5.1.2.1.1, fiscal 2022",
            "metodo_estimacion": "dato oficial agregado; IPC INDEC a jun-2026; curva calibrada / Pareto sólo cola abierta",
        })
    write_csv(HERE / "distribucion_patrimonial.csv", distribution_rows, list(distribution_rows[0]))

    simulation_rows = []
    for band in default["bands"]:
        simulation_rows.append({
            "escenario": "Amplio · tope 3%",
            "umbral_ars_jun_2026": 1e9,
            "participacion": 1.0,
            "tope_patrimonio": 0.03,
            "lambda": default["lambda"],
            **band,
            "recaudacion_total_escenario": default["revenue"],
            "meta": TARGET,
            "brecha": default["gap"],
            "factibilidad": "alcanza" if default["feasible"] else "no alcanza",
        })
    write_csv(HERE / "simulacion_aporte_voluntario.csv", simulation_rows, list(simulation_rows[0]))

    sensitivity_rows = []
    methods = {
        "promedio_oficial": make_nodes(factor, "promedio_oficial")[0],
        "curva_sin_cola": make_nodes(factor, "curva_sin_cola")[0],
        "curva_pareto": nodes,
        "curva_pareto_subdeclaracion_20pct": [{**n, "w": n["w"] * 1.2} for n in nodes],
    }
    for method, method_nodes in methods.items():
        for threshold_b in (1, 2, 3, 5, 10):
            for participation in (0.25, 0.5, 0.75, 1.0):
                for cap in (0.01, 0.02, 0.03, 0.05):
                    result = solve(method_nodes, threshold_b * 1e9, participation, cap)
                    sensitivity_rows.append({
                        "metodo_distribucion": method,
                        "umbral_billones": threshold_b,
                        "participacion": participation,
                        "tope_patrimonio": cap,
                        "lambda": result["lambda"],
                        "recaudacion": result["revenue"],
                        "recaudacion_maxima": result["maximum"],
                        "brecha": result["gap"],
                        "factibilidad": "alcanza" if result["feasible"] else "no alcanza",
                        "aportantes_estimados": result["contributors"],
                        "aporte_promedio": result["average"],
                        "aporte_mediano": result["median"],
                        "tasa_efectiva_minima": result["min_rate"],
                        "tasa_efectiva_mediana": result["median_rate"],
                        "tasa_efectiva_maxima": result["max_rate"],
                        "patrimonio_retenido_mediano": result["median_retained"],
                    })
    write_csv(HERE / "sensibilidad_aporte.csv", sensitivity_rows, list(sensitivity_rows[0]))

    reconciliation = [
        ("Agujero salarial bruto", "pérdida", 18.43e12, "dic-2023–jun-2026", "sí", "no", "Base madre; incluye sólo caídas mensuales", "medio"),
        ("Recuperación salarial observada", "contrafactual observado", -6.08e12, "dic-2023–jun-2026", "sí", "no", "Se descuenta del agujero bruto", "medio"),
        ("Brecha salarial neta", "subtotal", 12.35e12, "dic-2023–jun-2026", "no", "no", "No sumar: ya surge de las dos filas anteriores", "alto"),
        ("Pinza financiera", "compensación hipotética", 5.85e12, "32 meses post-shock", "no", "sí", "No es pérdida salarial ni obligación judicial", "alto"),
        ("Privilegios fiscales prudentes", "reasignación hipotética", 1.23e12, "anual", "no", "sí", "Período distinto; mostrar separado", "alto"),
        ("Mercado Libre", "beneficio documentado", 223.08e9, "2024–1T2026 reexpresado", "no", "sí", "Régimen previo; no sumar como daño salarial", "alto"),
        ("SIDE", "crédito presupuestario", 49.30e9, "2026", "no", "sí", "Crédito no equivale a ejecución", "alto"),
        ("Aporte grandes fortunas", "compensación hipotética", TARGET, "una vez; pesos jun-2026", "no", "sí", "Recaudación objetivo, no daño ni ingreso observado", "alto"),
    ]
    write_csv(
        HERE.parent / "lo_que_te_robo_reconciliacion.csv",
        [dict(zip(("componente", "naturaleza", "monto", "periodo", "incluido_total_robo", "incluido_compensacion", "riesgo_doble_conteo", "calidad"), row)) for row in reconciliation],
        ["componente", "naturaleza", "monto", "periodo", "incluido_total_robo", "incluido_compensacion", "riesgo_doble_conteo", "calidad"],
    )

    historical_real = 248_006e6 * cpi["202606"] / cpi["202112"]
    historical_threshold = 200e6 * cpi["202606"] / cpi["202012"]
    (HERE / "AUDITORIA_APORTE.md").write_text(
        audit_markdown(factor, alpha, default, historical_real, historical_threshold), encoding="utf-8"
    )

    source_files = stable_sources()
    update_manifest(source_files)
    build_html(nodes, factor, alpha, historical_real, historical_threshold)
    print(json.dumps({
        "output_html": str(OUTPUT_HTML),
        "factor_ipc": factor,
        "pareto_alpha": alpha,
        "default": default,
        "historical_real_jun_2026": historical_real,
        "historical_threshold_jun_2026": historical_threshold,
    }, ensure_ascii=False, indent=2))


def build_html(nodes, factor, alpha, historical_real, historical_threshold):
    source = (ROOT / "index.html").read_text(encoding="utf-8")
    js_data = {
        "nodes": [{"w": round(n["w"], 2), "n": round(n["n"], 8)} for n in nodes],
        "target": TARGET,
        "factor": factor,
        "alpha": alpha,
        "fxJun2026": FX_JUN_2026,
        "annualWageJun2026": ANNUAL_WAGE_JUN_2026,
        "historicalNominal": 248_006e6,
        "historicalReal": historical_real,
        "historicalContributors": 10_000,
        "historicalThresholdReal": historical_threshold,
    }
    data_assignment = "const wealthContributionData=" + json.dumps(js_data, ensure_ascii=False, separators=(",", ":")) + ";"
    if "tab-wealth-contribution" in source:
        # Después de promover la versión al root, una nueva corrida mantiene el
        # dashboard y sólo refresca la base numérica embebida.
        source, replacements = re.subn(
            r"const wealthContributionData=\{.*?\};\n",
            lambda _match: data_assignment + "\n",
            source,
            count=1,
            flags=re.DOTALL,
        )
        if replacements != 1:
            raise RuntimeError("No se encontró la base wealthContributionData para actualizar.")
        output_source = source.replace(
            'href="data/fuentes/grandes_fortunas/', 'href="fuentes/grandes_fortunas/'
        ).replace(
            'href="data/derivados/grandes_fortunas/', 'href="derivados/grandes_fortunas/'
        )
        OUTPUT_HTML.write_text(output_source, encoding="utf-8")
        return

    source = source.replace("</style>", WEALTH_CSS + "\n</style>", 1)
    source = source.replace(
        '    <button class="tab-btn" data-tab="tab-milei-cost">Lo que te robó Milei</button>',
        '    <button class="tab-btn" data-tab="tab-wealth-contribution">Grandes fortunas</button>\n'
        '    <button class="tab-btn" data-tab="tab-milei-cost">Lo que te robó Milei</button>',
        1,
    )
    source = source.replace(
        '  <section id="tab-milei-cost" class="tab-panel">',
        WEALTH_HTML.replace("__HISTORICAL_THRESHOLD__", f"{historical_threshold:.6f}") + '\n\n  <section id="tab-milei-cost" class="tab-panel">',
        1,
    )
    source = source.replace(
        '    <div class="milei-cost-grid" id="mileiCostCards"></div>',
        '    <section id="mileiWealthCompensation" class="milei-wealth-compensation"></section>\n\n'
        '    <div class="milei-cost-grid" id="mileiCostCards"></div>',
        1,
    )
    wealth_js = data_assignment + "\n" + WEALTH_JS
    source = source.replace("function mileiCostPct(v,total)", wealth_js + "\nfunction mileiCostPct(v,total)", 1)
    source = source.replace(
        "      } else if (target === 'tab-milei-cost') {",
        "      } else if (target === 'tab-wealth-contribution') {\n"
        "        renderWealthContribution();\n"
        "      } else if (target === 'tab-milei-cost') {",
        1,
    )
    source = source.replace(
        "  const latestRealLevel=powerTotalAllOfficial.yNov.at(-1);",
        "  const wealthScenarioForTable=wealthScenarioState.result||gfSolve(wealthScenarioState.threshold,wealthScenarioState.participation,wealthScenarioState.cap,wealthScenarioState.underdeclared,wealthContributionData.target/(wealthScenarioState.horizonYears||1));\n"
        "  const wealthScenarioYears=wealthScenarioForTable.horizonYears||wealthScenarioState.horizonYears||1;\n"
        "  const wealthScenarioTotal=wealthScenarioForTable.revenue*wealthScenarioYears;\n"
        "  const wealthScenarioCoverage=Math.min(1,wealthScenarioTotal/wealthContributionData.target);\n"
        "  const wealthScenarioRemaining=Math.max(0,wealthContributionData.target-wealthScenarioTotal);\n"
        "  renderWealthCompensationInMilei();\n  const latestRealLevel=powerTotalAllOfficial.yNov.at(-1);",
        1,
    )
    source = source.replace(
        "    <tr><td>Fintech · cambio vs espejo</td>",
        "    <tr><td>Aporte voluntario de grandes fortunas</td><td class=\"household-plus\">+${gfMoney(wealthScenarioTotal)} para compensar</td><td class=\"attr-no\">No integra los ${powerMoneyBillions(grossShock)} de daño: es una vía hipotética y separada para financiar una meta específica de ${gfMoney(wealthContributionData.target)}.</td><td><b>${gfPct(wealthScenarioCoverage,1)} cubierto</b> · resta ${gfMoney(wealthScenarioRemaining)}</td></tr>\n"
        "    <tr><td>Fintech · cambio vs espejo</td>",
        1,
    )
    OUTPUT_HTML.write_text(source, encoding="utf-8")


WEALTH_CSS = r"""
/* v133 · Grandes fortunas y aporte voluntario progresivo */
#tab-wealth-contribution{--gf-plum:#60346f;--gf-pink:#cf5f8a;--gf-green:#3f8a70;--gf-gold:#b27b29}
.wealth-hero,.wealth-controls,.wealth-card,.wealth-history,.wealth-audit,.milei-wealth-compensation{box-sizing:border-box;border:1px solid #e6cfea;border-radius:22px;background:rgba(255,255,255,.92);box-shadow:0 9px 22px rgba(99,53,112,.06)}
.wealth-hero{margin-top:14px;padding:24px;background:linear-gradient(135deg,#fff7fb,#f7f4ff 55%,#f3fff9)}
.wealth-eyebrow{font-size:9px;font-weight:950;letter-spacing:.055em;text-transform:uppercase;color:#9a6c9f}
.wealth-hero h1{margin:7px 0 5px;color:var(--gf-plum);font-size:32px;line-height:1.1}
.wealth-hero .lead{max-width:1000px;margin:0;color:#715c78;font-size:13px;line-height:1.6}
.wealth-target{display:flex;align-items:flex-end;gap:12px;flex-wrap:wrap;margin-top:18px}.wealth-target strong{font-size:42px;line-height:1;color:#a43f68}.wealth-target span{padding-bottom:4px;font-size:11px;color:#78617d}
.wealth-controls{margin-top:14px;padding:18px}.wealth-preset-row{display:flex;gap:7px;flex-wrap:wrap;margin-bottom:14px}.wealth-preset{border:1px solid #dec8e5;background:#fff;color:#704b7c;border-radius:999px;padding:8px 12px;font:800 10px/1.2 inherit;cursor:pointer}.wealth-preset.active{background:#f3ddf7;border-color:#bb83ca;color:#5c296c}
.wealth-control-grid{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:11px}.wealth-control{min-width:0;padding:11px 12px;border:1px solid #eee2f1;border-radius:14px;background:#fffafd}.wealth-control label{display:block;font-size:9px;font-weight:950;text-transform:uppercase;color:#876b90}.wealth-control select,.wealth-control input[type=range]{width:100%;margin-top:8px}.wealth-control select{border:1px solid #dbc9e1;border-radius:10px;padding:8px;background:#fff;color:#654d70;font:800 11px inherit}.wealth-control output{display:block;margin-top:6px;font-size:17px;font-weight:950;color:#774287}.wealth-toggle{display:flex!important;align-items:center;gap:8px;text-transform:none!important;line-height:1.35}.wealth-toggle input{accent-color:#a8527a}
.wealth-kpis{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:10px;margin-top:14px}.wealth-kpi{min-width:0;padding:15px;border:1px solid #e8dbea;border-radius:17px;background:#fff}.wealth-kpi .tag{font-size:8px;font-weight:950;text-transform:uppercase;color:#917895}.wealth-kpi .val{margin-top:6px;font-size:22px;font-weight:950;color:#68407a;overflow-wrap:anywhere}.wealth-kpi.good{background:#f4fff9;border-color:#bee2d3}.wealth-kpi.good .val{color:#347e63}.wealth-kpi.hot{background:#fff8fb;border-color:#eabed0}.wealth-kpi.hot .val{color:#aa426b}.wealth-kpi .mini{margin-top:5px;font-size:9.5px;line-height:1.45;color:#7d6b82}
.wealth-feasibility{margin-top:11px;padding:13px 15px;border-left:5px solid #4ca17e;border-radius:13px;background:#f0fff7;color:#47695e;font-size:12px;line-height:1.5}.wealth-feasibility.bad{border-color:#d15b7e;background:#fff3f7;color:#8b4660}.wealth-feasibility strong{color:inherit}
.wealth-chart-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:13px;margin-top:14px}.wealth-card{min-width:0;padding:16px}.wealth-card.full{grid-column:1/-1}.wealth-card h2,.wealth-history h2,.wealth-audit h2{margin:0;color:#654074;font-size:18px}.wealth-card .chart-note,.wealth-history .chart-note{margin-top:4px;font-size:10px;line-height:1.5;color:#806d85}.wealth-plot{width:100%;height:355px}.wealth-card.full .wealth-plot{height:385px}
.wealth-table-wrap{overflow-x:auto;margin-top:13px;border:1px solid #eadfec;border-radius:15px}.wealth-table{width:100%;min-width:860px;border-collapse:collapse;font-size:10px}.wealth-table th{padding:10px;background:#f7eff9;color:#775681;text-align:left;text-transform:uppercase;font-size:8px}.wealth-table td{padding:10px;border-top:1px solid #f0e7f2;color:#725f78}.wealth-table td:first-child{font-weight:900;color:#62446e}.wealth-table .num{text-align:right;font-variant-numeric:tabular-nums}
.wealth-history{margin-top:14px;padding:18px}.wealth-history-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:10px;margin-top:12px}.wealth-history-grid>div{padding:13px;border:1px solid #eadfec;border-radius:14px;background:#fffafd}.wealth-history-grid span{display:block;font-size:8px;font-weight:950;text-transform:uppercase;color:#957b99}.wealth-history-grid b{display:block;margin-top:5px;font-size:18px;color:#684176}.wealth-history-callout{margin-top:12px;padding:12px 14px;border-radius:13px;background:#fff8e9;color:#7e6438;font-size:11px;line-height:1.55}
.wealth-audit{margin-top:14px;padding:18px}.wealth-audit-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:10px;margin-top:12px}.wealth-audit-grid>div{padding:13px;border:1px solid #e9ddea;border-radius:14px;background:#fff}.wealth-audit-grid b{display:block;color:#684176;font-size:11px}.wealth-audit-grid p{margin:5px 0 0;color:#78677e;font-size:10px;line-height:1.55}.wealth-sources{margin-top:12px;font-size:9.5px;line-height:1.6;color:#826d87}.wealth-sources a{color:#86569a;font-weight:850}.wealth-jump{display:flex;justify-content:flex-end;margin-top:12px}
.milei-wealth-compensation{margin:14px 0;padding:18px;background:linear-gradient(135deg,#f4fff9,#fff 52%,#fff7e9);border-color:#bedfce}.milei-wealth-compensation .eyebrow{font-size:8.5px;font-weight:950;text-transform:uppercase;color:#548a75}.milei-wealth-compensation h2{margin:5px 0;color:#5f426b;font-size:20px}.milei-wealth-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:9px;margin-top:11px}.milei-wealth-grid>div{padding:12px;border:1px solid #d7e9df;border-radius:14px;background:rgba(255,255,255,.87)}.milei-wealth-grid span{display:block;font-size:8px;font-weight:950;text-transform:uppercase;color:#70877b}.milei-wealth-grid b{display:block;margin-top:5px;font-size:18px;color:#347c62}.milei-wealth-compensation p{font-size:10.5px;line-height:1.55;color:#6c706d}.milei-wealth-track{height:10px;border-radius:99px;background:#e8efe9;overflow:hidden}.milei-wealth-track span{display:block;height:100%;background:linear-gradient(90deg,#63b493,#b5d66f);border-radius:99px}
@media(min-width:1728px){.wealth-hero,.wealth-controls,.wealth-history,.wealth-audit{padding-left:26px;padding-right:26px}.wealth-plot{height:385px}.wealth-card.full .wealth-plot{height:420px}}
@media(max-width:1366px){.wealth-kpis{grid-template-columns:repeat(3,minmax(0,1fr))}.wealth-control-grid{grid-template-columns:repeat(3,minmax(0,1fr))}}
@media(max-width:1024px){.wealth-chart-grid{grid-template-columns:1fr}.wealth-card.full{grid-column:auto}.wealth-history-grid,.milei-wealth-grid{grid-template-columns:repeat(2,minmax(0,1fr))}.wealth-audit-grid{grid-template-columns:1fr}}
@media(max-width:768px){.wealth-hero{padding:18px 15px}.wealth-hero h1{font-size:25px}.wealth-target strong{font-size:34px}.wealth-controls,.wealth-card,.wealth-history,.wealth-audit{padding:14px}.wealth-control-grid,.wealth-kpis{grid-template-columns:1fr}.wealth-plot,.wealth-card.full .wealth-plot{height:330px}}
@media(max-width:430px){.wealth-history-grid,.milei-wealth-grid{grid-template-columns:1fr}.wealth-preset{flex:1 1 46%}.wealth-hero h1{font-size:23px}.wealth-target strong{font-size:31px}.wealth-plot,.wealth-card.full .wealth-plot{height:310px}}
@media(max-width:390px){.wealth-hero,.wealth-controls,.wealth-card,.wealth-history,.wealth-audit{padding-left:11px;padding-right:11px}.wealth-preset{flex-basis:100%}.wealth-plot,.wealth-card.full .wealth-plot{height:295px}.wealth-kpi .val{font-size:20px}}
"""


WEALTH_HTML = r"""
  <section id="tab-wealth-contribution" class="tab-panel">
    <div class="method-shield">
      <span class="label">Grandes fortunas · simulador patrimonial auditable</span>
      <strong>¿Cuánto tendría que aportar voluntariamente la parte más rica para reunir $4,98 billones sin perder una porción material de su patrimonio?</strong>
      <span class="method-badge official">ARCA · Bienes Personales 2022</span>
      <span class="method-badge official">INDEC · IPC nacional</span>
      <span class="method-badge derived">estimación por tramos</span>
    </div>

    <section class="wealth-hero" id="wealthHero">
      <div class="wealth-eyebrow">Una compensación hipotética · no agranda la cuenta del daño</div>
      <h1>Grandes fortunas y aporte voluntario progresivo</h1>
      <p class="lead">La base son 895.111 declaraciones con bienes de ARCA. El aporte se calcula sólo sobre el excedente del umbral elegido, aumenta con el patrimonio y nunca supera el tope individual. Patrimonio no es ingreso: acá medimos stock de riqueza declarada.</p>
      <div class="wealth-target"><strong>$ 4,98 billones</strong><span>meta única, expresada en pesos de junio de 2026</span></div>
    </section>

    <section class="wealth-controls" id="wealthControls">
      <div class="wealth-preset-row" aria-label="Escenarios prearmados">
        <button class="wealth-preset" data-preset="concentrated" type="button">Muy concentrado</button>
        <button class="wealth-preset" data-preset="prudent" type="button">Prudente</button>
        <button class="wealth-preset active" data-preset="broad" type="button">Amplio</button>
        <button class="wealth-preset" data-preset="historical" type="button">Aporte Solidario comparable</button>
        <button class="wealth-preset" data-preset="custom" type="button">Personalizado</button>
      </div>
      <div class="wealth-control-grid">
        <div class="wealth-control"><label for="wealthThreshold">Umbral patrimonial</label><select id="wealthThreshold"><option value="1000000000" selected>$1 B</option><option value="2000000000">$2 B</option><option value="3000000000">$3 B</option><option value="5000000000">$5 B</option><option value="__HISTORICAL_THRESHOLD__">$6,13 B · mínimo histórico real</option><option value="10000000000">$10 B</option></select><output id="wealthThresholdContext"></output></div>
        <div class="wealth-control"><label for="wealthParticipation">Participación voluntaria</label><input id="wealthParticipation" type="range" min="25" max="100" step="25" value="100"><output id="wealthParticipationOut">100%</output></div>
        <div class="wealth-control"><label for="wealthCap">Tope máximo por persona</label><select id="wealthCap"><option value="0.01">1% del patrimonio</option><option value="0.02">2% del patrimonio</option><option value="0.03" selected>3% del patrimonio</option><option value="0.05">5% del patrimonio</option></select><output id="wealthCapOut">3%</output></div>
        <div class="wealth-control"><label for="wealthHorizon">Horizonte del aporte</label><select id="wealthHorizon"><option value="1" selected>Una sola vez</option><option value="3">Anual · durante 3 años</option></select><output id="wealthHorizonOut">Una vez</output></div>
        <div class="wealth-control"><label class="wealth-toggle"><input id="wealthUnderdeclared" type="checkbox"> Sensibilidad: patrimonio captado +20%</label><output id="wealthMethodOut">Base declarada</output></div>
      </div>
    </section>

    <div id="wealthKpis" class="wealth-kpis"></div>
    <div id="wealthFeasibility" class="wealth-feasibility"></div>

    <div class="wealth-chart-grid">
      <section class="wealth-card full"><h2>1 · Carga individual por nivel de patrimonio</h2><div class="chart-note">Barras: tasa efectiva media sobre todo el patrimonio. Línea: aporte medio de cada tramo. El aporte se aplica al excedente del umbral, no al patrimonio completo.</div><div id="wealthBurdenChart" class="wealth-plot"></div></section>
      <section class="wealth-card"><h2>2 · ¿Quién financia cuánto?</h2><div class="chart-note">Aporte total por tramo y acumulado de la recaudación.</div><div id="wealthFinanceChart" class="wealth-plot"></div></section>
      <section class="wealth-card"><h2>3 · Participación vs tasa requerida</h2><div class="chart-note">Tasa efectiva mediana necesaria para la meta; cada línea respeta un tope patrimonial distinto. Los huecos indican que ni agotando el tope alcanza.</div><div id="wealthParticipationChart" class="wealth-plot"></div></section>
    </div>

    <section class="wealth-card" style="margin-top:14px"><h2>Distribución del esfuerzo</h2><div class="chart-note">Aportantes esperados: participación × casos elegibles. No son adhesiones observadas.</div><div id="wealthTable" class="wealth-table-wrap"></div></section>

    <section class="wealth-history" id="wealthHistory"><h2>Comparación histórica · Aporte Solidario 2020/21</h2><div class="chart-note">Referencia de escala, no antecedente legal equivalente del mecanismo voluntario.</div><div id="wealthHistoryContent"></div></section>

    <section class="wealth-audit"><h2>Qué es oficial y qué estimamos</h2><div class="wealth-audit-grid">
      <div><b>Oficial</b><p>Casos, patrimonio total, bienes en el país y en el exterior por tramo: ARCA. IPC para llevar todo a junio de 2026: INDEC. Recaudación histórica: AFIP.</p></div>
      <div><b>Estimado</b><p>La forma dentro de cada tramo y la cola abierta superior. Conservamos exactamente los casos y el patrimonio oficial; la cola usa Pareto calibrada α≈1,89.</p></div>
      <div><b>No medido</b><p>Probabilidad real de adhesión, evasión, liquidez disponible y conducta frente al aporte. El +20% es sólo sensibilidad mecánica y nunca se mezcla silenciosamente con la base.</p></div>
    </div>
    <div class="wealth-sources"><b>Fuentes:</b> <a href="fuentes/grandes_fortunas/arca/bienes_personales_tramos_2022.xls">ARCA · cuadro 2.5.1.2.1.1</a> · <a href="fuentes/grandes_fortunas/aporte_solidario/aporte_solidario_final_2021-12-20.pdf">Informe oficial del Aporte Solidario</a> · <a href="fuentes/grandes_fortunas/aporte_solidario/afip_informe_recaudacion_4t_2021.pdf">AFIP · recaudación 2021</a> · <a href="derivados/grandes_fortunas/AUDITORIA_APORTE.md">auditoría reproducible</a>. WID se usa sólo como contexto: top 10% concentra 58,7% de la riqueza neta estimada en 2024; no se suma a la base fiscal declarada.</div>
    <div class="wealth-jump"><button class="subbtn" type="button" onclick="activateTabAndScroll('tab-milei-cost','mileiWealthCompensation')">Ver cómo compensaría en “Lo que te robó Milei” →</button></div></section>

    <footer><b>Lectura responsable:</b> “voluntario” describe el escenario solicitado, no una estimación de cumplimiento. Un patrimonio de $3 billones no equivale a $3 billones disponibles en efectivo. La factibilidad contable no demuestra factibilidad política, jurídica ni de liquidez.</footer>
  </section>
"""


WEALTH_JS = r"""
const wealthScenarioState={threshold:1e9,participation:1,cap:.03,horizonYears:1,underdeclared:false,preset:'broad'};
const wealthPresets={
  concentrated:{threshold:10e9,participation:1,cap:.05},
  prudent:{threshold:2e9,participation:1,cap:.05},
  broad:{threshold:1e9,participation:1,cap:.03},
  historical:{threshold:wealthContributionData.historicalThresholdReal,participation:1,cap:.05}
};
function gfWeight(w){return w<3e9?1:w<10e9?1.5:w<50e9?2:w<250e9?3:4}
function gfBand(w){return w<1e9?'< $1 B':w<3e9?'$1–3 B':w<10e9?'$3–10 B':w<50e9?'$10–50 B':w<250e9?'$50–250 B':'> $250 B'}
const gfBandOrder=['< $1 B','$1–3 B','$3–10 B','$10–50 B','$50–250 B','> $250 B'];
function gfWeightedMedian(rows,key){const a=rows.filter(r=>r.n>0).slice().sort((x,y)=>x[key]-y[key]);const total=a.reduce((s,r)=>s+r.n,0);let c=0;for(const r of a){c+=r.n;if(c>=total/2)return r[key]}return a.length?a.at(-1)[key]:0}
function gfSolve(threshold,participation,cap,underdeclared=false,target=wealthContributionData.target){
  const factor=underdeclared?1.2:1;
  const eligible=wealthContributionData.nodes.map(n=>({w:n.w*factor,n:n.n})).filter(n=>n.w>threshold);
  const contribution=(n,lambda)=>Math.min(lambda*gfWeight(n.w)*Math.max(0,n.w-threshold),cap*n.w);
  const maximum=participation*eligible.reduce((s,n)=>s+cap*n.w*n.n,0);
  const feasible=maximum+1>=target;let lambda;
  if(feasible){let lo=0,hi=1;while(participation*eligible.reduce((s,n)=>s+contribution(n,hi)*n.n,0)<target)hi*=2;for(let i=0;i<100;i++){const mid=(lo+hi)/2;const rev=participation*eligible.reduce((s,n)=>s+contribution(n,mid)*n.n,0);if(rev<target)lo=mid;else hi=mid}lambda=hi}else lambda=1e6;
  const rows=eligible.map(n=>({...n,aporte:contribution(n,lambda),tasa:contribution(n,lambda)/n.w,band:gfBand(n.w)}));
  const revenue=Math.min(maximum,participation*rows.reduce((s,r)=>s+r.aporte*r.n,0));
  const contributors=participation*rows.reduce((s,r)=>s+r.n,0);
  const bands=gfBandOrder.map(label=>{const a=rows.filter(r=>r.band===label);const count=participation*a.reduce((s,r)=>s+r.n,0);const wealth=participation*a.reduce((s,r)=>s+r.w*r.n,0);const contributionTotal=participation*a.reduce((s,r)=>s+r.aporte*r.n,0);return {label,count,wealth,contribution:contributionTotal,average:count?contributionTotal/count:0,rate:wealth?contributionTotal/wealth:0}}).filter(x=>x.count>0);
  return {threshold,participation,cap,underdeclared,target,lambda,feasible,maximum,revenue,gap:Math.max(0,target-revenue),contributors,average:contributors?revenue/contributors:0,median:gfWeightedMedian(rows,'aporte'),minRate:rows.length?Math.min(...rows.map(r=>r.tasa)):0,medianRate:gfWeightedMedian(rows,'tasa'),maxRate:rows.length?Math.max(...rows.map(r=>r.tasa)):0,bands,rows};
}
function gfMoney(v){const a=Math.abs(v);if(a>=1e12)return '$ '+(v/1e12).toLocaleString('es-AR',{minimumFractionDigits:2,maximumFractionDigits:2})+' billones';if(a>=1e9)return '$ '+(v/1e9).toLocaleString('es-AR',{minimumFractionDigits:1,maximumFractionDigits:1})+' mil M';return '$ '+(v/1e6).toLocaleString('es-AR',{minimumFractionDigits:1,maximumFractionDigits:1})+' M'}
function gfPct(v,digits=2){return (v*100).toLocaleString('es-AR',{minimumFractionDigits:digits,maximumFractionDigits:digits})+'%'}
function gfCount(v){return Math.round(v).toLocaleString('es-AR')}
function gfPlotLayout(mobile){return {paper_bgcolor:'rgba(255,255,255,0)',plot_bgcolor:'#fffdfd',font:{color:'#654d70',family:'Inter,system-ui,sans-serif',size:mobile?9:11},margin:{l:mobile?48:68,r:mobile?42:64,t:20,b:mobile?80:68},hoverlabel:{bgcolor:'#fff7fb',bordercolor:'#e6bed1',font:{color:'#50375d'}},legend:{orientation:'h',y:1.16,x:0}}}
function renderWealthContribution(){
  const root=document.getElementById('tab-wealth-contribution');if(!root)return;
  const threshold=document.getElementById('wealthThreshold'),participation=document.getElementById('wealthParticipation'),cap=document.getElementById('wealthCap'),horizon=document.getElementById('wealthHorizon'),under=document.getElementById('wealthUnderdeclared');
  if(!root.dataset.bound){
    root.dataset.bound='1';
    [threshold,participation,cap,horizon,under].forEach(el=>el.addEventListener('input',()=>{wealthScenarioState.preset='custom';document.querySelectorAll('.wealth-preset').forEach(b=>b.classList.toggle('active',b.dataset.preset==='custom'));renderWealthContribution()}));
    root.querySelectorAll('.wealth-preset').forEach(btn=>btn.addEventListener('click',()=>{const p=wealthPresets[btn.dataset.preset];if(p){threshold.value=String(p.threshold);participation.value=String(p.participation*100);cap.value=String(p.cap);horizon.value='1';under.checked=false;wealthScenarioState.preset=btn.dataset.preset}root.querySelectorAll('.wealth-preset').forEach(b=>b.classList.toggle('active',b===btn));renderWealthContribution()}));
  }
  wealthScenarioState.threshold=+threshold.value;wealthScenarioState.participation=+participation.value/100;wealthScenarioState.cap=+cap.value;wealthScenarioState.horizonYears=+horizon.value;wealthScenarioState.underdeclared=under.checked;
  const annualTarget=wealthContributionData.target/wealthScenarioState.horizonYears;const s=gfSolve(wealthScenarioState.threshold,wealthScenarioState.participation,wealthScenarioState.cap,wealthScenarioState.underdeclared,annualTarget);s.horizonYears=wealthScenarioState.horizonYears;wealthScenarioState.result=s;
  const horizonRevenue=s.revenue*s.horizonYears,horizonGap=Math.max(0,wealthContributionData.target-horizonRevenue),horizonRate=s.medianRate*s.horizonYears;
  document.getElementById('wealthParticipationOut').textContent=Math.round(s.participation*100)+'%';document.getElementById('wealthCapOut').textContent=gfPct(s.cap,0);document.getElementById('wealthHorizonOut').textContent=s.horizonYears===1?'Una vez':'3 aportes anuales';document.getElementById('wealthMethodOut').textContent=s.underdeclared?'Sensibilidad +20%':'Base declarada';
  const usd=s.threshold/wealthContributionData.fxJun2026;const incomes=s.threshold/wealthContributionData.annualWageJun2026;document.getElementById('wealthThresholdContext').textContent='≈ USD '+(usd/1e6).toLocaleString('es-AR',{maximumFractionDigits:2})+' M · '+Math.round(incomes).toLocaleString('es-AR')+' ingresos anuales';
  document.getElementById('wealthKpis').innerHTML=`
    <div class="wealth-kpi ${s.feasible?'good':'hot'}"><div class="tag">Recaudación del horizonte</div><div class="val">${gfMoney(horizonRevenue)}</div><div class="mini">${s.horizonYears===1?'Aporte único':gfMoney(s.revenue)+' por año × 3'} · ${gfPct(horizonRevenue/wealthContributionData.target,1)} de la meta.</div></div>
    <div class="wealth-kpi"><div class="tag">Aportantes esperados</div><div class="val">${gfCount(s.contributors)}</div><div class="mini">Casos elegibles × participación.</div></div>
    <div class="wealth-kpi"><div class="tag">Aporte medio / mediano</div><div class="val">${gfMoney(s.average*s.horizonYears)}</div><div class="mini">Mediana del horizonte: ${gfMoney(s.median*s.horizonYears)}.</div></div>
    <div class="wealth-kpi"><div class="tag">Tasa efectiva mediana</div><div class="val">${gfPct(horizonRate)}</div><div class="mini">Rango del horizonte: ${gfPct(s.minRate*s.horizonYears)}–${gfPct(s.maxRate*s.horizonYears)}.</div></div>
    <div class="wealth-kpi"><div class="tag">Patrimonio retenido</div><div class="val">${gfPct(Math.max(0,1-horizonRate),1)}</div><div class="mini">Mediana tras todo el horizonte, sin rendimientos.</div></div>`;
  const feasible=document.getElementById('wealthFeasibility');feasible.classList.toggle('bad',!s.feasible);feasible.innerHTML=s.feasible?`<strong>Alcanza.</strong> Con este diseño se cubren ${gfMoney(wealthContributionData.target)} ${s.horizonYears===1?'en un aporte':'en tres aportes de '+gfMoney(s.revenue)+' por año'}. El calibrador λ anual es ${s.lambda.toLocaleString('es-AR',{maximumFractionDigits:5})}.`:`<strong>No alcanza con este tope, horizonte y participación.</strong> El máximo del horizonte sería ${gfMoney(s.maximum*s.horizonYears)} y faltarían ${gfMoney(horizonGap)}. Subir λ no resuelve el faltante porque las personas elegibles ya chocan con el tope.`;
  renderWealthCharts(s);renderWealthTable(s);renderWealthHistory(s);
}
function renderWealthCharts(s){
  const mobile=window.innerWidth<=720,labels=s.bands.map(b=>b.label),layout=gfPlotLayout(mobile),years=s.horizonYears||1;
  Plotly.react('wealthBurdenChart',[{type:'bar',x:labels,y:s.bands.map(b=>b.rate*100*years),name:'Tasa efectiva del horizonte',marker:{color:['#c9a2d6','#bd8fce','#ad79c2','#9767b0','#80559c','#684185']},hovertemplate:'<b>%{x}</b><br>Tasa: %{y:.2f}%<extra></extra>'},{type:'scatter',mode:'lines+markers',x:labels,y:s.bands.map(b=>b.average*years/1e9),name:'Aporte medio · $ mil M',yaxis:'y2',line:{color:'#d45b83',width:3},marker:{size:7},hovertemplate:'<b>%{x}</b><br>Aporte medio: $ %{y:.2f} mil M<extra></extra>'}],{...layout,yaxis:{title:'% del patrimonio · horizonte',gridcolor:'#eee4f1',rangemode:'tozero'},yaxis2:{title:'$ mil M por aportante',overlaying:'y',side:'right',rangemode:'tozero'},xaxis:{tickangle:mobile?-38:0}},{responsive:true,displaylogo:false,displayModeBar:false});
  let cumulative=0;const totals=s.bands.map(b=>b.contribution*years);const cumulativePct=totals.map(v=>(cumulative+=v)/Math.max(1,s.revenue*years)*100);
  Plotly.react('wealthFinanceChart',[{type:'bar',x:labels,y:totals.map(v=>v/1e12),name:'Aporte del tramo',marker:{color:'#c8668b'},hovertemplate:'<b>%{x}</b><br>$ %{y:.3f} billones<extra></extra>'},{type:'scatter',mode:'lines+markers',x:labels,y:cumulativePct,name:'Acumulado',yaxis:'y2',line:{color:'#3f9274',width:3},hovertemplate:'Acumulado: %{y:.1f}%<extra></extra>'}],{...layout,yaxis:{title:'$ billones',gridcolor:'#eee4f1',rangemode:'tozero'},yaxis2:{title:'% acumulado',overlaying:'y',side:'right',range:[0,105]},xaxis:{tickangle:mobile?-38:0}},{responsive:true,displaylogo:false,displayModeBar:false});
  const participations=[.25,.5,.75,1],caps=[.01,.02,.03,.05],colors=['#e088a8','#bc78c5','#7866bd','#3f9274'];
  const traces=caps.map((c,i)=>{const points=participations.map(p=>gfSolve(s.threshold,p,c,s.underdeclared,s.target));return {type:'scatter',mode:'lines+markers',x:participations.map(p=>p*100),y:points.map(r=>r.feasible?r.medianRate*100*years:null),name:'Tope '+gfPct(c,0)+(years>1?'/año':''),connectgaps:false,line:{color:colors[i],width:c===s.cap?4:2},marker:{size:c===s.cap?8:6},customdata:points.map(r=>[r.feasible,r.maximum*years/1e12]),hovertemplate:'Participación %{x:.0f}%<br>Tasa mediana del horizonte %{y:.2f}%<br>Máximo $ %{customdata[1]:.2f} B<extra></extra>'}});
  Plotly.react('wealthParticipationChart',traces,{...layout,xaxis:{title:'Participación voluntaria (%)',tickvals:[25,50,75,100],range:[20,105]},yaxis:{title:'Tasa efectiva mediana requerida (%)',gridcolor:'#eee4f1',rangemode:'tozero'}},{responsive:true,displaylogo:false,displayModeBar:false});
}
function renderWealthTable(s){const y=s.horizonYears||1;document.getElementById('wealthTable').innerHTML=`<table class="wealth-table"><thead><tr><th>Tramo patrimonial</th><th class="num">Aportantes</th><th class="num">Patrimonio del tramo</th><th class="num">Aporte total</th><th class="num">Aporte medio</th><th class="num">Tasa efectiva</th><th>En criollo</th></tr></thead><tbody>${s.bands.map(b=>`<tr><td>${b.label}</td><td class="num">${gfCount(b.count)}</td><td class="num">${gfMoney(b.wealth)}</td><td class="num">${gfMoney(b.contribution*y)}</td><td class="num">${gfMoney(b.average*y)}</td><td class="num">${gfPct(b.rate*y)}</td><td>Conserva en promedio ${gfPct(Math.max(0,1-b.rate*y),1)} de su patrimonio tras el horizonte.</td></tr>`).join('')}</tbody></table>`}
function renderWealthHistory(s){const d=wealthContributionData;document.getElementById('wealthHistoryContent').innerHTML=`<div class="wealth-history-grid"><div><span>Recaudación 2021</span><b>$ 248.006 M</b></div><div><span>A pesos jun-2026</span><b>${gfMoney(d.historicalReal)}</b></div><div><span>Aportantes</span><b>≈ ${gfCount(d.historicalContributors)}</b></div><div><span>Pago medio real</span><b>${gfMoney(d.historicalReal/d.historicalContributors)}</b></div></div><div class="wealth-history-callout"><b>La escala histórica casi coincide con la meta:</b> equivale a ${gfPct(d.historicalReal/d.target,1)} de los ${gfMoney(d.target)}. Pero el Aporte Solidario fue obligatorio, extraordinario y por única vez; tuvo mínimo legal de $200 M de dic-2020 (≈ ${gfMoney(d.historicalThresholdReal)} de jun-2026) y alícuotas nominales de 2%–3,5%, con incremento para bienes del exterior. La tasa efectiva promedio observada no está publicada en los agregados oficiales revisados, así que no la inventamos.</div>`}
function renderWealthCompensationInMilei(){
  const box=document.getElementById('mileiWealthCompensation');if(!box)return;const fallbackYears=wealthScenarioState.horizonYears||1;const s=wealthScenarioState.result||gfSolve(wealthScenarioState.threshold,wealthScenarioState.participation,wealthScenarioState.cap,wealthScenarioState.underdeclared,wealthContributionData.target/fallbackYears);const years=s.horizonYears||fallbackYears,totalContribution=s.revenue*years,coverage=Math.min(1,totalContribution/wealthContributionData.target),remaining=Math.max(0,wealthContributionData.target-totalContribution),surplus=Math.max(0,totalContribution-wealthContributionData.target);
  box.innerHTML=`<div class="eyebrow">Compensación hipotética separada · no se suma al daño</div><h2>Si las grandes fortunas aportaran voluntariamente</h2><p>Este bloque responde otra pregunta: cuánto de la meta específica de ${gfMoney(wealthContributionData.target)} podría financiarse. No agranda los $18,43 billones ni duplica salarios, bancos, Fintech, SIDE o Mercado Libre.</p><div class="milei-wealth-grid"><div><span>Costo / meta a compensar</span><b>${gfMoney(wealthContributionData.target)}</b></div><div><span>Aporte del escenario</span><b>+ ${gfMoney(totalContribution)}</b></div><div><span>Cobertura</span><b>${gfPct(coverage,1)}</b></div><div><span>Resta por cubrir</span><b>${gfMoney(remaining)}</b></div></div><div class="milei-wealth-track" aria-label="Cobertura de la meta"><span style="width:${coverage*100}%"></span></div>${surplus>0?`<p><b>Excedente separado:</b> ${gfMoney(surplus)}. No se muestra como cobertura superior al 100%.</p>`:''}<p><b>Escenario:</b> umbral ${gfMoney(s.threshold)}, participación ${gfPct(s.participation,0)}, tope ${gfPct(s.cap,0)} ${years===1?'una vez':'por año durante 3 años'}${s.underdeclared?' y sensibilidad patrimonial +20%':''}. ${s.feasible?'La meta es contablemente alcanzable.':'Con estos límites no alcanza.'}</p><div class="wealth-jump"><button class="subbtn" type="button" onclick="activateTabAndScroll('tab-wealth-contribution','wealthControls')">Abrir simulador y auditoría →</button></div>`;
}
"""


if __name__ == "__main__":
    main()
