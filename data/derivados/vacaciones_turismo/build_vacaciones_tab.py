from __future__ import annotations

import csv
import json
import re
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[3]
SOURCE_HTML = ROOT / "data" / "dashboard_kawaii_139_rutas_publico_privado.html"
OUTPUT_HTML = ROOT / "data" / "dashboard_kawaii_140_vacaciones_turismo.html"
OUT_DIR = Path(__file__).resolve().parent
SOURCE_DIR = ROOT / "data" / "fuentes" / "turismo"


SOURCES = {
    "indec_page": "https://www.indec.gob.ar/indec/web/Nivel4-Tema-3-13-55",
    "indec_jun_2026": "https://www.indec.gob.ar/uploads/informesdeprensa/eti_07_2611F2D28020.pdf",
    "indec_annual_2025": "https://www.indec.gob.ar/uploads/informesdeprensa/eti_01_26212234D387.pdf",
    "eoh_page": "https://www.indec.gob.ar/indec/web/Nivel4-Tema-3-13-56",
    "eoh_method": "https://www.indec.gob.ar/uploads/informesdeprensa/eoh_12_25ED486DC3BD.pdf",
    "bcra_itcrm": "https://www.bcra.gob.ar/indices-de-tipo-de-cambio-multilateral/",
    "bcra_fx": "https://www.bcra.gob.ar/informe-de-la-evolucion-del-mercado-de-cambios-y-balance-cambiario/",
    "bcra_mar_2026": "https://www.bcra.gob.ar/archivos/Pdfs/PublicacionesEstadisticas/informes/informe-mercado-cambios-balance-cambiario-2026-03.pdf",
    "bcra_jun_2026": "https://www.bcra.gob.ar/archivos/Pdfs/PublicacionesEstadisticas/informes/informe-monetario-mensual-jun-26.pdf",
    "came_summer_2026": "https://www.redcame.org.ar/prensa/14480/temporada-2026",
    "came_summer_2025": "https://www.redcame.org.ar/novedades/14132/temporada-2025-viajaron-281-millones-de-turistas-y-gastaron-87-billones-de-pesos",
    "came_summer_2024": "https://www.redcame.org.ar/novedades/13608/temporada-2024-viajaron-292-millones-de-turistas-y-gastaron-casi-5-billones-de-pesos",
    "came_winter_2026": "https://www.argentina.gob.ar/noticias/vacaciones-de-invierno-212-billones-de-impacto-economico-un-25-mas-que-en-2025",
}


MONTHS = {
    "enero": 1,
    "febrero": 2,
    "marzo": 3,
    "abril": 4,
    "mayo": 5,
    "junio": 6,
    "julio": 7,
    "agosto": 8,
    "septiembre": 9,
    "octubre": 10,
    "noviembre": 11,
    "diciembre": 12,
}


def parse_flow(path: Path, total_col: int) -> tuple[list[dict], list[dict]]:
    frame = pd.read_excel(path, header=None)
    monthly: list[dict] = []
    annual: list[dict] = []
    year: int | None = None
    for _, row in frame.iterrows():
        raw = row.iloc[0]
        if pd.isna(raw):
            continue
        label = str(raw).strip().lower()
        found = re.search(r"a.o\s+(20\d{2})", label)
        if found:
            year = int(found.group(1))
            value = pd.to_numeric(row.iloc[total_col], errors="coerce")
            annual.append({"year": year, "value": None if pd.isna(value) else float(value)})
            continue
        if label in MONTHS and year is not None:
            value = pd.to_numeric(row.iloc[total_col], errors="coerce")
            if not pd.isna(value):
                monthly.append({"date": f"{year}-{MONTHS[label]:02d}-01", "value": float(value)})
    return monthly, annual


def build_data() -> dict:
    receptivo_monthly, receptivo_annual = parse_flow(
        SOURCE_DIR / "INDEC_serie_turismo_receptivo_total_vias.xlsx", 11
    )
    emisivo_monthly, emisivo_annual = parse_flow(
        SOURCE_DIR / "INDEC_serie_turismo_emisivo_total_vias.xlsx", 10
    )
    by_date: dict[str, dict] = {}
    for row in receptivo_monthly:
        by_date.setdefault(row["date"], {"date": row["date"]})["receptivo"] = row["value"]
    for row in emisivo_monthly:
        by_date.setdefault(row["date"], {"date": row["date"]})["emisivo"] = row["value"]
    monthly = []
    for row in sorted(by_date.values(), key=lambda item: item["date"]):
        if "receptivo" not in row or "emisivo" not in row:
            continue
        row["saldo"] = row["receptivo"] - row["emisivo"]
        row["ratio"] = row["emisivo"] / row["receptivo"] if row["receptivo"] else None
        monthly.append(row)

    annual_r = {row["year"]: row["value"] for row in receptivo_annual}
    annual_e = {row["year"]: row["value"] for row in emisivo_annual}
    annual = []
    for year in sorted(set(annual_r) & set(annual_e)):
        r, e = annual_r[year], annual_e[year]
        if r is None or e is None:
            year_rows = [row for row in monthly if row["date"].startswith(str(year))]
            if not year_rows:
                continue
            r = sum(row["receptivo"] for row in year_rows)
            e = sum(row["emisivo"] for row in year_rows)
            label = f"{year} · {len(year_rows)}m"
        else:
            label = str(year)
        annual.append({
            "year": year,
            "label": label,
            "receptivo": r,
            "emisivo": e,
            "saldo": r - e,
            "ratio": e / r if r else None,
            "partial": label != str(year),
        })

    spending = [
        {"year": 2024, "receptivo_usd_m": 3020.5, "emisivo_usd_m": 5146.3, "coverage": "ETI · pasos relevados"},
        {"year": 2025, "receptivo_usd_m": 3110.0, "emisivo_usd_m": 7164.2, "coverage": "ETI · pasos relevados"},
    ]
    for row in spending:
        row["saldo_usd_m"] = row["receptivo_usd_m"] - row["emisivo_usd_m"]

    itcrm_values = [
        ("2024-12-01", 79.79),
        ("2025-01-01", 79.70), ("2025-02-01", 81.21), ("2025-03-01", 80.52),
        ("2025-04-01", 82.62), ("2025-05-01", 83.90), ("2025-06-01", 86.12),
        ("2025-07-01", 91.77), ("2025-08-01", 95.10), ("2025-09-01", 99.10),
        ("2025-10-01", 98.89), ("2025-11-01", 96.02), ("2025-12-01", 94.70),
        ("2026-01-01", 93.50), ("2026-02-01", 90.10), ("2026-03-01", 86.20),
        ("2026-04-01", 84.70), ("2026-05-01", 84.30), ("2026-06-01", 85.00),
    ]

    summer = [
        {"year": 2023, "tourists_m": 33.8, "stay_nights": 4.15, "real_spend_yoy": None, "daily_real_yoy": None},
        {"year": 2024, "tourists_m": 29.2, "stay_nights": 3.9, "real_spend_yoy": 3.5, "daily_real_yoy": None},
        {"year": 2025, "tourists_m": 28.1, "stay_nights": None, "real_spend_yoy": -19.4, "daily_real_yoy": 1.9},
        {"year": 2026, "tourists_m": 30.7, "stay_nights": 3.65, "real_spend_yoy": 4.5, "daily_real_yoy": -3.3},
    ]
    base_2023 = summer[0]["tourists_m"]
    for index, row in enumerate(summer):
        row["tourists_vs_2023"] = (row["tourists_m"] / base_2023 - 1) * 100
        row["tourists_yoy_derived"] = None if index == 0 else (row["tourists_m"] / summer[index - 1]["tourists_m"] - 1) * 100

    origins = [
        ("Bolivia", 11.2, 19.9, True), ("Brasil", 101.4, 84.4, True),
        ("Chile", 42.3, 69.3, True), ("Paraguay", 26.2, 60.2, True),
        ("Uruguay", 46.9, 43.5, True), ("EE.UU. + Canadá", 25.2, 44.2, False),
        ("Resto de América", 38.2, 85.2, False), ("Europa", 28.7, 87.2, False),
        ("Resto del mundo", 9.2, 8.1, False),
    ]

    return {
        "cutoff": "2026-08-21",
        "flow_coverage": "INDEC · registros migratorios · total de vías · turistas (sin excursionistas)",
        "monthly": monthly,
        "annual": annual,
        "spending": spending,
        "itcrm": [{"date": date, "value": value} for date, value in itcrm_values],
        "eoh": {
            "last_period": "noviembre de 2025",
            "total_nights_m": 4.0,
            "total_nights_yoy": 5.3,
            "resident_nights_yoy": 4.8,
            "nonresident_nights_yoy": 6.8,
            "regions": ["Total país", "Buenos Aires", "CABA", "Córdoba", "Cuyo", "Litoral", "Norte", "Patagonia"],
        },
        "summer": summer,
        "winter_2026": {"tourists_m": 4.6, "domestic_m": 4.2, "foreign_m": 0.4, "tourists_yoy": 5.9, "real_spend_yoy": 2.5, "stay_nights": 4.0, "vs_2023": None},
        "origins_june_2026": [
            {"market": market, "receptivo_k": receptivo, "emisivo_k": emisivo, "bordering": bordering}
            for market, receptivo, emisivo, bordering in origins
        ],
        "bcra": {
            "period": "marzo de 2026",
            "travel_net_usd_m": -393,
            "travel_outflows_usd_m": 780,
            "travel_inflows_usd_m": 387,
            "own_fx_settlement_share": 70,
            "warning": "La cuenta Viajes y Pasajes incluye consumos con tarjeta que no son necesariamente turismo presencial.",
        },
        "sources": SOURCES,
    }


CSS = r"""
<style id="vacaciones-turismo-style-v140">
#tab-tourism{padding-top:4px}.tour-shell{display:grid;gap:16px;color:#5b4167}.tour-card{min-width:0;padding:20px;border:1px solid #e2d4ea;border-radius:24px;background:rgba(255,255,255,.93);box-shadow:0 10px 24px rgba(90,57,112,.06);box-sizing:border-box}.tour-hero{background:linear-gradient(135deg,rgba(255,249,253,.98),rgba(244,253,255,.98));border-color:#d8c4e8}.tour-head{display:flex;align-items:flex-start;justify-content:space-between;gap:15px}.tour-head h2,.tour-head h3,.tour-head h4{margin:0;color:#583766;line-height:1.2}.tour-head h2{font-size:27px}.tour-head h3{font-size:20px}.tour-sub{margin:7px 0 0;font-size:11px;line-height:1.55;color:#75617a}.tour-kicker,.tour-pill{display:inline-flex;align-items:center;gap:5px;padding:6px 9px;border:1px solid #dac8e5;border-radius:999px;background:#fff;font-size:8.5px;font-weight:950;letter-spacing:.035em;text-transform:uppercase;color:#765284}.tour-pill.good{border-color:#b8dccb;background:#f5fff9;color:#2c8062}.tour-pill.bad{border-color:#e6b9ca;background:#fff6fa;color:#a23e64}.tour-pill.warn{border-color:#ead49a;background:#fffbed;color:#7d6325}.tour-question{margin:14px 0;padding:14px 16px;border-left:5px solid #9a6bb2;border-radius:15px;background:#fbf7ff;font-size:17px;font-weight:950;color:#553563}.tour-question small{display:block;margin-top:5px;font-size:10px;font-weight:700;line-height:1.5;color:#746078}.tour-dimensions{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:8px}.tour-dimensions div{padding:11px 9px;border:1px solid #ded2e5;border-radius:14px;background:#fff;text-align:center}.tour-dimensions span{display:block;font-size:20px}.tour-dimensions b{font-size:9.5px;color:#5d3e6a}.tour-kpis{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:10px;margin-top:12px}.tour-kpi{padding:14px;border:1px solid #ded2e5;border-radius:16px;background:#fff}.tour-kpi small{display:block;font-size:7.8px;font-weight:950;letter-spacing:.04em;text-transform:uppercase;color:#836f89}.tour-kpi strong{display:block;margin:5px 0 3px;font-size:22px;line-height:1.05;color:#5b3c68}.tour-kpi span{font-size:9px;line-height:1.45;color:#76627b}.tour-kpi.green{background:#f5fff9;border-color:#b9ddcc}.tour-kpi.green strong{color:#2f8566}.tour-kpi.pink{background:#fff7fa;border-color:#e4bccd}.tour-kpi.pink strong{color:#ad416b}.tour-kpi.gold{background:#fffdf5;border-color:#ead8a9}.tour-kpi.gold strong{color:#9b721d}.tour-plain{margin-top:11px;padding:12px 14px;border:1px dashed #d8c8e1;border-radius:14px;background:#fdfbff;font-size:10.5px;line-height:1.55;color:#6e5974}.tour-plain b{color:#51315f}.tour-grid-2{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:14px}.tour-grid-3{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:11px}.tour-mini{padding:14px;border:1px solid #dfd3e7;border-radius:17px;background:#fff;font-size:10px;line-height:1.55;color:#6e5a73}.tour-mini h4{margin:0 0 7px;font-size:13px;color:#5b3b68}.tour-mini strong{color:#53345f}.tour-chart-scroll{max-width:100%;overflow-x:auto;overflow-y:hidden;padding-bottom:4px;-webkit-overflow-scrolling:touch}.tour-chart{width:100%;min-width:760px;height:430px}.tour-chart.small{height:345px;min-width:620px}.tour-controls{display:flex;flex-wrap:wrap;gap:7px;margin-top:11px}.tour-controls button,.tour-link{appearance:none;border:1px solid #d8c8e2;border-radius:999px;background:#fff;padding:8px 10px;color:#674a73;font:inherit;font-size:9px;font-weight:900;cursor:pointer;text-decoration:none}.tour-controls button.active{border-color:#9a64b2;background:#f4eafa}.tour-check{display:inline-flex;align-items:center;gap:7px;padding:7px 10px;border:1px solid #d8c8e2;border-radius:999px;background:#fff;font-size:9px;font-weight:900;color:#674a73}.tour-check input{accent-color:#8c62aa}.tour-callout{margin-top:11px;padding:13px 15px;border-left:5px solid #dc7e9e;border-radius:14px;background:#fff7fa;font-size:10.5px;line-height:1.58;color:#684e5b}.tour-callout.green{border-color:#57a987;background:#f5fff9}.tour-callout.gold{border-color:#d2a249;background:#fffdf4}.tour-flow{display:grid;grid-template-columns:1fr 42px 1fr;gap:10px;align-items:stretch;margin-top:12px}.tour-flow-card{padding:15px;border:1px solid #dfd2e7;border-radius:17px;background:#fff}.tour-flow-card h4{margin:0 0 9px;font-size:13px;color:#5b3c68}.tour-step{padding:9px;border-radius:11px;background:#f8f4fb;text-align:center;font-size:9.5px;font-weight:900;color:#63486f}.tour-arrow{text-align:center;color:#9b6daf;font-size:17px}.tour-vs{display:flex;align-items:center;justify-content:center;font-size:16px;font-weight:950;color:#a071b4}.tour-source-tag{display:inline-flex;margin-top:8px;padding:5px 8px;border-radius:999px;background:#fff7e9;border:1px solid #ead2a5;color:#8a672b;font-size:8px;font-weight:950;text-transform:uppercase}.tour-region-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:9px;margin-top:12px}.tour-region{padding:13px;border:1px solid #dfd3e7;border-radius:15px;background:#fff}.tour-region small{display:block;font-size:7.5px;font-weight:950;text-transform:uppercase;color:#856f8a}.tour-region strong{display:block;margin-top:4px;font-size:19px;color:#5c3e69}.tour-season{display:grid;grid-template-columns:minmax(0,1.15fr) minmax(0,.85fr);gap:14px}.tour-bars{display:grid;gap:8px;margin-top:11px}.tour-bar{display:grid;grid-template-columns:150px 1fr 66px;gap:8px;align-items:center;font-size:9px}.tour-bar-track{height:21px;border-radius:999px;background:#f0e8f4;overflow:hidden}.tour-bar-fill{height:100%;border-radius:999px;background:linear-gradient(90deg,#9d70b6,#6f55ad)}.tour-bar-fill.good{background:linear-gradient(90deg,#4b9d7d,#75c49e)}.tour-bar-fill.bad{background:linear-gradient(90deg,#d47b9b,#ef9bb4)}.tour-badge-row{display:flex;flex-wrap:wrap;gap:7px;margin-top:9px}.tour-sticker{display:inline-flex;align-items:center;gap:5px;padding:7px 9px;border:1px solid #decfe6;border-radius:12px;background:#fff;font-size:9px;font-weight:900;color:#654a71}.tour-formula{padding:15px;border:2px dashed #d8c4e4;border-radius:18px;background:#fbf8ff;text-align:center}.tour-formula code{display:block;margin:8px auto;padding:11px;border-radius:12px;background:#fff;color:#684b75;font-size:10px}.tour-sd{font-weight:950;color:#a1456a}.tour-links{display:flex;flex-wrap:wrap;gap:8px;margin-top:12px}.tour-faq{display:grid;gap:8px;margin-top:12px}.tour-faq details,.tour-method details{border:1px solid #dfd3e7;border-radius:14px;background:#fff}.tour-faq summary,.tour-method summary{cursor:pointer;padding:12px 14px;font-size:10.5px;font-weight:950;color:#5f416c}.tour-faq details div,.tour-method details div{padding:0 14px 13px;font-size:9.8px;line-height:1.58;color:#705d75}.tour-final{padding:19px;border:2px solid #cdbbe0;border-radius:20px;background:linear-gradient(135deg,#fbf7ff,#f4fff8)}.tour-final h3{margin:0;color:#593867;font-size:21px}.tour-final>p{font-size:12px;line-height:1.6;color:#654f6d}.tour-summary{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:9px;margin-top:12px}.tour-summary div{padding:12px;border:1px solid #ded2e5;border-radius:15px;background:#fff}.tour-summary b{display:block;font-size:10px;color:#5d3e69}.tour-summary span{display:block;margin-top:4px;font-size:9px;line-height:1.45;color:#746178}.tour-sources{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:8px;margin-top:12px}.tour-source{padding:11px;border:1px solid #e1d5e8;border-radius:13px;background:#fff;font-size:9px;line-height:1.45;color:#6e5b73}.tour-source a{color:#744c89;font-weight:900}.tour-table-wrap{max-width:100%;overflow:auto;margin-top:12px;border:1px solid #e0d4e7;border-radius:15px;background:#fff}.tour-table{width:100%;min-width:740px;border-collapse:collapse;font-size:9px}.tour-table th,.tour-table td{padding:9px 10px;border-bottom:1px solid #eee5f2;text-align:left}.tour-table th{background:#f7f1fb;color:#71527e;font-size:8px;text-transform:uppercase}.tour-table td.num{text-align:right;font-variant-numeric:tabular-nums}.tour-caveat{padding:13px;border:1px solid #ead5a5;border-radius:15px;background:#fffdf3;font-size:10px;line-height:1.55;color:#705b35}
@media(max-width:920px){.tour-kpis,.tour-dimensions{grid-template-columns:repeat(2,minmax(0,1fr))}.tour-grid-2,.tour-season{grid-template-columns:1fr}.tour-grid-3{grid-template-columns:repeat(2,minmax(0,1fr))}.tour-region-grid{grid-template-columns:repeat(2,minmax(0,1fr))}.tour-summary{grid-template-columns:repeat(2,minmax(0,1fr))}}
@media(max-width:560px){#tab-tourism{padding-left:2px;padding-right:2px}.tour-shell{gap:12px}.tour-card{padding:14px;border-radius:19px}.tour-head{flex-direction:column}.tour-head h2{font-size:22px}.tour-head h3{font-size:18px}.tour-kpis,.tour-dimensions,.tour-grid-3,.tour-region-grid,.tour-summary,.tour-sources{grid-template-columns:1fr}.tour-question{font-size:15px}.tour-chart{min-width:680px;height:390px}.tour-chart.small{min-width:600px;height:330px}.tour-flow{grid-template-columns:1fr}.tour-vs{min-height:25px}.tour-bar{grid-template-columns:110px 1fr 58px}.tour-controls button,.tour-link{font-size:8.5px}.tour-kicker{white-space:normal}.tour-region strong{font-size:17px}}
</style>
"""


SECTION = r"""
  <section id="tab-tourism" class="tab-panel">
    <div class="tour-shell">
      <section class="tour-card tour-hero">
        <div class="tour-head"><div><span class="tour-kicker">Acceso al descanso · corte 21/08/2026</span><h2>Vacaciones · Turismo ♡</h2><p class="tour-sub">Quién puede viajar, adónde se va la plata y qué pasa con el turismo argentino.</p></div><span class="tour-pill warn">personas ≠ viajes ≠ noches ≠ gasto</span></div>
        <div class="tour-question">¿Los argentinos pueden vacacionar más o menos que antes?<small>No alcanza con contar cruces de frontera: hay que mirar acceso, destino, duración, gasto y qué parte del ingreso familiar cuesta descansar.</small></div>
        <div class="tour-dimensions"><div><span>🧳</span><b>Quién viaja</b></div><div><span>🗺️</span><b>Adónde</b></div><div><span>🌙</span><b>Cuántas noches</b></div><div><span>💸</span><b>Cuánto gasta</b></div><div><span>🏠</span><b>Qué ingreso tiene</b></div></div>
        <div class="tour-kpis"><div class="tour-kpi pink"><small>H1 2026 · argentinos que salieron</small><strong id="tourHeroOut">—</strong><span>turistas · total de vías</span></div><div class="tour-kpi green"><small>H1 2026 · extranjeros que entraron</small><strong id="tourHeroIn">—</strong><span>turistas · total de vías</span></div><div class="tour-kpi gold"><small>salidas por cada entrada</small><strong id="tourHeroRatio">—</strong><span>no mide por sí solo bienestar</span></div><div class="tour-kpi"><small>acceso por nivel de ingreso</small><strong class="tour-sd">s/d reciente</strong><span>no hay serie oficial 2023–26 comparable</span></div></div>
        <div class="tour-controls" id="tourGlobalCompare"><span class="tour-pill">Comparar verano contra:</span><button data-base="2023" class="active">2023</button><button data-base="2024">2024</button><button data-base="2025">2025</button><button data-base="previous">año anterior</button><button data-base="prepandemic">prepandemia</button></div>
        <div class="tour-plain" id="tourGlobalCompareText"><b>Verano 2026 vs 2023:</b> calculando…</div>
      </section>

      <section class="tour-card">
        <div class="tour-head"><div><span class="tour-kicker">Flujo físico · INDEC</span><h3>¿Quién viaja más: nosotros o ellos?</h3><p class="tour-sub">Turistas —no excursionistas— registrados por todas las vías. La serie comparable disponible comienza en 2022.</p></div><span class="tour-pill bad">saldo = receptivo − emisivo</span></div>
        <div class="tour-controls" id="tourFlowMode"><button class="active" data-mode="monthly">Mensual</button><button data-mode="annual">Anual</button></div>
        <div class="tour-chart-scroll"><div id="tourFlowChart" class="tour-chart"></div></div>
        <div class="tour-grid-3"><div class="tour-mini"><h4>Actual · H1 2026</h4><strong id="tourRatioCurrent">—</strong><br>salidas por cada entrada.</div><div class="tour-mini"><h4>Mínimo mensual</h4><strong id="tourRatioMin">—</strong><br><span id="tourRatioMinDate">—</span></div><div class="tour-mini"><h4>Máximo mensual</h4><strong id="tourRatioMax">—</strong><br><span id="tourRatioMaxDate">—</span></div></div>
        <div class="tour-callout"><b>En criollo:</b> un saldo físico negativo dice que salieron más turistas residentes que los no residentes que entraron. No dice cuántos hogares pudieron vacacionar ni si esas salidas fueron vacaciones, trabajo o visita familiar.</div>
      </section>

      <div class="tour-grid-2">
        <section class="tour-card"><div class="tour-head"><div><span class="tour-kicker">Cobertura ETI · pasos relevados</span><h3>¿Cuántos dólares entran y salen?</h3></div></div><div class="tour-chart-scroll"><div id="tourSpendChart" class="tour-chart small"></div></div><div class="tour-callout gold"><b>No mezclar:</b> estos gastos ETI cubren los pasos relevados por la encuesta; los flujos del gráfico principal usan todos los registros migratorios. El saldo 2025 es <b>−USD 4.054,2 M</b>, derivado de la misma cobertura.</div></section>
        <section class="tour-card"><div class="tour-head"><div><span class="tour-kicker">BCRA · mecanismo financiero</span><h3>¿Cada dólar gastado afuera sale de las reservas?</h3></div><span class="tour-pill good">No necesariamente</span></div><div class="tour-flow"><div class="tour-flow-card"><h4>Gasto turístico externo</h4><div class="tour-step">tarjeta / transferencia / efectivo</div><div class="tour-arrow">↓</div><div class="tour-step">puede cancelarse con dólares propios</div></div><div class="tour-vs">≠</div><div class="tour-flow-card"><h4>Venta directa del BCRA</h4><div class="tour-step">mercado de cambios</div><div class="tour-arrow">↓</div><div class="tour-step">reservas y otras contrapartidas</div></div></div><div class="tour-kpis"><div class="tour-kpi"><small>mar-2026 · Viajes y Pasajes</small><strong>−USD 393 M</strong><span>saldo cambiario</span></div><div class="tour-kpi green"><small>cancelado con fondos propios</small><strong>≈70%</strong><span>de los egresos relevados</span></div></div><div class="tour-caveat"><b>Ojo:</b> la cuenta de tarjetas también contiene compras online. El turismo emisivo afecta servicios y demanda de divisas, pero <b>gasto afuera ≠ dólares vendidos directamente por el BCRA</b>.</div></section>
      </div>

      <section class="tour-card">
        <div class="tour-head"><div><span class="tour-kicker">EOH · estructura hotelera</span><h3>¿Los argentinos siguen vacacionando dentro del país?</h3><p class="tour-sub">La publicación nacional no llega a 2026. Mostramos el último dato sin extenderlo artificialmente.</p></div><span class="tour-pill warn">último: noviembre de 2025</span></div>
        <div class="tour-controls" id="tourRegionButtons"></div><div id="tourRegionMetrics" class="tour-region-grid"></div>
        <div class="tour-callout gold"><b>Por qué falta 2026:</b> INDEC informó una reformulación de ETI/EOH desde enero de 2026 tras no renovarse el convenio de financiamiento. Sin una actualización comparable, la dirección del turismo interno queda <b>s/d</b>.</div>
      </section>

      <div class="tour-grid-2">
        <section class="tour-card"><div class="tour-head"><div><span class="tour-kicker">Fuente sectorial · CAME</span><h3>Vacaciones de verano</h3></div><span class="tour-pill">2023–2026</span></div><div class="tour-chart-scroll"><div id="tourSummerChart" class="tour-chart small"></div></div><div class="tour-badge-row"><span class="tour-sticker">2026 vs 2025 · turistas <b>+9,5%</b></span><span class="tour-sticker">vs 2023 · turistas <b id="tourSummerVs23">—</b></span><span class="tour-sticker">estadía 2026 · <b>3,65 noches</b></span></div><div class="tour-caveat">La publicación 2025 informó 3,2 noches; la publicación 2026 reexpresó el comparador 2025 como 3,7. Para no reconciliar manualmente dos cifras sectoriales incompatibles, el gráfico deja 2025 como <b>s/d</b>.</div></section>
        <section class="tour-card"><div class="tour-head"><div><span class="tour-kicker">Fuente sectorial · CAME</span><h3>Vacaciones de invierno 2026</h3></div></div><div class="tour-kpis"><div class="tour-kpi green"><small>viajeros</small><strong>4,6 M</strong><span>+5,9% vs 2025</span></div><div class="tour-kpi green"><small>gasto total real</small><strong>+2,5%</strong><span>vs 2025</span></div><div class="tour-kpi"><small>estadía promedio</small><strong>4 días</strong><span>dato sectorial</span></div><div class="tour-kpi"><small>comparación vs 2023</small><strong class="tour-sd">s/d</strong><span>sin serie homogénea en la fuente</span></div></div><div class="tour-callout green"><b>¿Recuperación?</b> Sí contra 2025 en viajeros y gasto real. <b>¿Ya recuperó 2023?</b> No se puede responder con esta publicación.</div></section>
      </div>

      <section class="tour-card">
        <div class="tour-head"><div><span class="tour-kicker">Cantidad y actividad no son lo mismo</span><h3>La gente viaja, pero ¿gasta?</h3></div></div><div class="tour-season"><div id="tourSpendBars" class="tour-bars"></div><div class="tour-mini"><h4>Lectura 2026 vs 2025</h4><p><b>Más turistas:</b> +9,5%.</p><p><b>Más gasto total real:</b> +4,5%.</p><p><b>Menor gasto diario real:</b> −3,3%.</p><p><b>Estadía apenas menor:</b> 3,65 vs 3,7 noches según el comparador de la publicación 2026.</p></div></div><div class="tour-callout"><b>En criollo:</b> hubo más movimiento, pero cada día de viaje movió menos consumo real. Contar turistas no alcanza para medir la actividad económica turística.</div>
      </section>

      <section class="tour-card">
        <div class="tour-head"><div><span class="tour-kicker">Decisión individual vs efecto local</span><h3>¿Dónde gastan sus vacaciones los argentinos?</h3></div></div><div class="tour-flow"><div class="tour-flow-card"><h4>🏠 Turismo interno</h4><div class="tour-step">ingreso argentino</div><div class="tour-arrow">↓</div><div class="tour-step">hotel · restaurante · transporte argentino</div><div class="tour-arrow">↓</div><div class="tour-step">actividad y empleo local</div></div><div class="tour-vs">vs</div><div class="tour-flow-card"><h4>✈️ Turismo emisivo</h4><div class="tour-step">ingreso argentino</div><div class="tour-arrow">↓</div><div class="tour-step">hotel · restaurante · transporte extranjero</div><div class="tour-arrow">↓</div><div class="tour-step">actividad en otro país</div></div></div><div class="tour-callout green"><b>Sin juzgar la decisión personal:</b> viajar afuera puede mejorar el bienestar de quien viaja. Esta comparación sólo pregunta dónde queda el consumo turístico.</div>
      </section>

      <section class="tour-card">
        <div class="tour-head"><div><span class="tour-kicker">Gráfico estrella · BCRA + INDEC</span><h3>¿Qué pasa cuando Argentina se abarata o encarece en dólares?</h3><p class="tour-sub">ITCRM mensual promedio y turistas por todas las vías. El índice alto implica mayor competitividad cambiaria relativa.</p></div><label class="tour-check"><input id="tourNormalize" type="checkbox" checked> Base 100</label></div>
        <div class="tour-chart-scroll"><div id="tourFxChart" class="tour-chart"></div></div><div class="tour-callout gold"><b>No es una prueba causal.</b> También importan salarios, actividad, conectividad, precios de otros destinos, reglas cambiarias y expectativas. Los valores ITCRM son promedios mensuales tomados de informes BCRA y pueden revisarse.</div>
      </section>

      <div class="tour-grid-2">
        <section class="tour-card"><div class="tour-head"><div><span class="tour-kicker">Precio relativo</span><h3>¿Argentina está cara para quién?</h3></div></div><div class="tour-grid-2"><div class="tour-mini"><h4>Residente argentino</h4>Importan salario real, alojamiento, comida, transporte y el costo relativo de viajar afuera. Un ITCRM bajo puede volver relativamente atractivos destinos externos, pero no garantiza que un hogar pueda pagarlos.</div><div class="tour-mini"><h4>Turista extranjero</h4>Importan su moneda, precios argentinos, vuelos, conectividad y servicios. Un único dólar nominal no resume su costo efectivo.</div></div><div class="tour-callout"><b>No hay un “índice turístico” inventado:</b> mostramos ITCRM y las variables con fuente; los precios de destinos quedan pendientes hasta hallar una canasta homogénea.</div></section>
        <section class="tour-card"><div class="tour-head"><div><span class="tour-kicker">Accesibilidad familiar</span><h3>¿Cuántos ingresos cuesta una semana?</h3></div></div><div class="tour-formula"><b>Índice de vacaciones familiares</b><code>costo total del viaje familiar ÷ ingreso mensual familiar</code><strong class="tour-sd">Comparador en construcción · s/d</strong></div><div class="tour-plain">No completamos Mar del Plata, Córdoba, Bariloche, Brasil o Chile con precios sueltos: faltan una fecha común, el mismo hogar, noches, transporte, alojamiento, comidas y un ingreso comparable.</div></section>
      </div>

      <section class="tour-card">
        <div class="tour-head"><div><span class="tour-kicker">La pregunta social</span><h3>¿Quién puede vacacionar?</h3></div><span class="tour-pill bad">viajes totales ≠ acceso general</span></div><div class="tour-grid-2"><div class="tour-mini"><h4>Mejora generalizada</h4><b>Ingresos reales ↑</b><br>Más hogares viajan; crecen turismo interno y externo.</div><div class="tour-mini"><h4>Mejora concentrada</h4>Sectores altos viajan más afuera mientras hogares medios o bajos acortan o eliminan sus vacaciones.</div></div><div class="tour-callout"><b>Dato faltante clave:</b> no existe una serie oficial reciente 2023–2026 suficiente para medir por quintil qué porcentaje de hogares viajó, cuántas noches y por qué no viajó. No inferimos desigualdad sólo por las salidas internacionales.</div><div class="tour-links"><button class="tour-link" onclick="activateTab('tab-power')">→ Salarios</button><button class="tour-link" onclick="activateTab('tab-gini')">→ Gini</button><button class="tour-link" onclick="activateTab('tab-poverty')">→ Pobreza</button><button class="tour-link" onclick="activateTab('tab-consumption')">→ Consumo</button></div>
      </section>

      <section class="tour-card">
        <div class="tour-head"><div><span class="tour-kicker">Junio de 2026 · total país</span><h3>¿De dónde vienen y adónde van?</h3><p class="tour-sub">Mercado de residencia/destino declarado en registros migratorios. Miles de turistas.</p></div><span class="tour-pill">INDEC · misma cobertura</span></div><div class="tour-grid-2"><div><div class="tour-chart-scroll"><div id="tourOriginChart" class="tour-chart small"></div></div></div><div><div class="tour-chart-scroll"><div id="tourDestinationChart" class="tour-chart small"></div></div></div></div><div class="tour-callout"><b>Brasil domina el receptivo de junio, pero no es “siempre más barato”.</b> Para comparar destinos hacen falta fecha, ciudad, alojamiento, comida, transporte, tipo de cambio e ingreso del hogar.</div>
      </section>

      <div class="tour-grid-2">
        <section class="tour-card"><div class="tour-head"><div><span class="tour-kicker">Regiones argentinas</span><h3>¿Quién ganó y quién perdió turismo?</h3></div></div><div class="tour-plain"><b>Detalle regional reciente: s/d comparable.</b> La estructura EOH permite Buenos Aires, CABA, Córdoba, Cuyo, Litoral, Norte y Patagonia, pero el último reporte nacional llega a noviembre de 2025. No rellenamos 2026 con una fuente sectorial distinta.</div><div class="tour-flow"><div class="tour-flow-card"><h4>Menor demanda interna puede</h4><div class="tour-step">bajar ocupación</div><div class="tour-arrow">↓</div><div class="tour-step">reducir gastronomía y comercio</div><div class="tour-arrow">↓</div><div class="tour-step">afectar empleo estacional</div></div><div class="tour-vs">≠</div><div class="tour-flow-card"><h4>Relación automática</h4><div class="tour-step">cada destino tiene precios</div><div class="tour-arrow">+</div><div class="tour-step">conectividad y eventos</div><div class="tour-arrow">+</div><div class="tour-step">oferta y clima propios</div></div></div><div class="tour-links"><button class="tour-link" onclick="activateTab('tab-employment')">→ Trabajo</button><button class="tour-link" onclick="activateTab('tab-growth')">→ Actividad</button><button class="tour-link" onclick="activateTab('tab-consumption')">→ Consumo</button></div></section>
        <section class="tour-card"><div class="tour-head"><div><span class="tour-kicker">Cuentas externas</span><h3>¿El turismo aporta o demanda divisas?</h3></div></div><div class="tour-kpis"><div class="tour-kpi green"><small>ETI 2025 · gasto receptivo</small><strong>USD 3.110 M</strong><span>ingreso en la cobertura</span></div><div class="tour-kpi pink"><small>ETI 2025 · gasto emisivo</small><strong>USD 7.164 M</strong><span>egreso en la cobertura</span></div><div class="tour-kpi pink"><small>saldo turístico ETI</small><strong>−USD 4.054 M</strong><span>derivado</span></div><div class="tour-kpi"><small>reservas</small><strong>no equivalen</strong><span>mecanismo financiero distinto</span></div></div><div class="tour-callout gold">Turismo es un componente de servicios. <b>No es</b> balanza comercial de bienes, energía ni intereses; tampoco se suma sin más a esas cuentas.</div></section>
      </div>

      <section class="tour-card tour-method"><div class="tour-head"><div><span class="tour-kicker">FAQ</span><h3>Preguntas rápidas</h3></div></div><div class="tour-faq"><details open><summary>¿Los argentinos viajan más?</summary><div>En H1 2026 salieron 6,384 millones: 13,2% menos que en H1 2025. Pero sigue habiendo 2,20 salidas por cada entrada. La respuesta cambia según el período.</div></details><details><summary>¿Argentina recibe menos turistas?</summary><div>En H1 2026 ingresaron 2,898 millones: 7,4% más que en H1 2025. Junio de 2026 también creció 3,3% interanual. Eso describe una recuperación reciente, no un récord histórico.</div></details><details><summary>¿Viajan más afuera que dentro?</summary><div>No puede responderse comparando cruces internacionales con noches hoteleras: son unidades y universos distintos, y EOH no tiene actualización nacional 2026.</div></details><details><summary>¿El dólar relativamente barato ayuda a viajar?</summary><div>Puede abaratar destinos externos en términos relativos, pero el acceso depende además de salario real, precios, transporte y ahorro.</div></details><details><summary>¿Más viajes al exterior significa vivir mejor?</summary><div>No necesariamente. Puede ser una mejora generalizada o concentrada. Para distinguirlas hacen falta salarios, distribución del ingreso y acceso efectivo a vacaciones.</div></details><details><summary>¿La recuperación 2026 borró la caída previa?</summary><div>El verano mejoró contra 2025, pero sus 30,7 millones de turistas quedaron alrededor de 9,2% debajo de 2023. En invierno no hay comparador 2023 homogéneo en la publicación usada.</div></details></div></section>

      <section class="tour-final"><span class="tour-kicker">Resumen dinámico</span><h3>Entonces… ¿vacacionamos más?</h3><div class="tour-summary"><div><b id="tourSummaryOut">Turismo emisivo</b><span id="tourSummaryOutText">—</span></div><div><b id="tourSummaryIn">Turismo receptivo</b><span id="tourSummaryInText">—</span></div><div><b>Turismo interno</b><span>s/d 2026 · EOH corta en nov-2025</span></div><div><b>Verano interno</b><span>más turistas y gasto total real; menor gasto diario real</span></div><div><b>Estadía</b><span>3,65 noches en verano 2026 · sectorial</span></div><div><b>Costo / ingreso</b><span>s/d · falta canasta homogénea</span></div></div><p id="tourFinalText">Cargando lectura…</p><div class="tour-question">¿Quién puede irse de vacaciones?<small>La cantidad total de turistas no alcanza. Importa cuántos hogares pueden descansar, durante cuántos días y qué proporción de su ingreso necesitan.</small></div><div class="tour-links"><button class="tour-link" onclick="activateTab('tab-rates')">→ Inflación y tipo de cambio</button><button class="tour-link" onclick="activateTab('tab-power')">→ Salarios</button><button class="tour-link" onclick="activateTab('tab-gini')">→ Gini</button><button class="tour-link" onclick="activateTab('tab-poverty')">→ Pobreza</button><button class="tour-link" onclick="activateTab('tab-growth')">→ Actividad</button></div></section>

      <section class="tour-card tour-method"><div class="tour-head"><div><h3>Fuentes y cómo leer este tab</h3><p class="tour-sub">Coberturas separadas; datos faltantes visibles; resultados derivados desde los archivos fuente.</p></div></div><details open><summary>▸ Diferencias que no conviene mezclar</summary><div><b>Turismo interno:</b> residentes viajando dentro del país. <b>Receptivo:</b> no residentes que ingresan. <b>Emisivo:</b> residentes que salen. Turista pernocta; excursionista no. Los registros migratorios cubren todas las vías; ETI estima gasto en pasos relevados; EOH mide hotelería; CAME es una fuente sectorial. Ninguna de estas series se corrige manualmente con otra.</div></details><details><summary>▸ Tipo de cambio, bienestar y causalidad</summary><div>El ITCRM mide competitividad real multilateral y es más informativo que un dólar nominal aislado. Una asociación visual con turismo no prueba causalidad ni permite atribuir el movimiento automáticamente a un gobierno.</div></details><details><summary>▸ Qué falta para responder por acceso</summary><div>Una serie reciente comparable por nivel de ingreso, hogares que no viajan por razones económicas, noches y costo de una canasta homogénea de vacaciones. Hasta entonces esos campos quedan s/d.</div></details><div class="tour-sources"><div class="tour-source"><a href="https://www.indec.gob.ar/indec/web/Nivel4-Tema-3-13-55" target="_blank" rel="noopener">INDEC · turismo internacional</a><br>registros migratorios y ETI.</div><div class="tour-source"><a href="https://www.indec.gob.ar/indec/web/Nivel4-Tema-3-13-56" target="_blank" rel="noopener">INDEC · EOH</a><br>ocupación hotelera y corte disponible.</div><div class="tour-source"><a href="https://www.bcra.gob.ar/indices-de-tipo-de-cambio-multilateral/" target="_blank" rel="noopener">BCRA · ITCRM</a><br>competitividad real multilateral.</div><div class="tour-source"><a href="https://www.bcra.gob.ar/informe-de-la-evolucion-del-mercado-de-cambios-y-balance-cambiario/" target="_blank" rel="noopener">BCRA · Balance Cambiario</a><br>Viajes y Pasajes.</div><div class="tour-source"><a href="https://www.redcame.org.ar/prensa/14480/temporada-2026" target="_blank" rel="noopener">CAME · verano 2026</a><br>fuente sectorial.</div><div class="tour-source"><a href="https://www.argentina.gob.ar/noticias/vacaciones-de-invierno-212-billones-de-impacto-economico-un-25-mas-que-en-2025" target="_blank" rel="noopener">CAME · invierno 2026</a><br>fuente sectorial reproducida oficialmente.</div></div><div class="tour-links"><button class="tour-link" onclick="downloadTourData('json')">Descargar datos JSON</button><button class="tour-link" onclick="downloadTourData('csv')">Descargar flujos CSV</button><a class="tour-link" id="tourAuditLink" href="#" target="_blank">Abrir auditoría</a></div></section>
    </div>
  </section>
"""


SCRIPT_TEMPLATE = r"""
<script id="vacaciones-turismo-script-v140">
const TOUR_DATA=__TOUR_DATA__;
const TOUR_DOWNLOADS=__TOUR_DOWNLOADS__;
let tourRendered=false,tourFlowMode='monthly',tourCompareBase='2023';
const TOUR_CONFIG={responsive:true,displaylogo:false,scrollZoom:false,modeBarButtonsToRemove:['lasso2d','select2d']};
function tourFmt(v,d=1){return v==null||!Number.isFinite(Number(v))?'s/d':Number(v).toLocaleString('es-AR',{minimumFractionDigits:d,maximumFractionDigits:d})}
function tourSigned(v,d=1){return v==null?'s/d':`${v>=0?'+':'−'}${tourFmt(Math.abs(v),d)}%`}
function tourDate(date){return new Date(`${date}T00:00:00`).toLocaleDateString('es-AR',{month:'short',year:'numeric'})}
function tourLayout(title){return{title:{text:title,font:{size:13,color:'#5d4169'}},paper_bgcolor:'rgba(0,0,0,0)',plot_bgcolor:'rgba(255,255,255,.72)',font:{family:'Nunito,Arial,sans-serif',color:'#654f6c',size:10},margin:{l:62,r:38,t:62,b:68},hovermode:'x unified',hoverlabel:{bgcolor:'#fff8fc',bordercolor:'#d8b7ca',font:{size:10}},legend:{orientation:'h',y:1.13,x:0},xaxis:{gridcolor:'#eee5f2',automargin:true},yaxis:{gridcolor:'#eadff0',automargin:true}}
}
function tourH1(year){const rows=TOUR_DATA.monthly.filter(r=>r.date.startsWith(`${year}-`)&&+r.date.slice(5,7)<=6);return{receptivo:rows.reduce((a,r)=>a+r.receptivo,0),emisivo:rows.reduce((a,r)=>a+r.emisivo,0)}}
function renderTourHero(){const current=tourH1(2026),previous=tourH1(2025),ratio=current.emisivo/current.receptivo,dyOut=(current.emisivo/previous.emisivo-1)*100,dyIn=(current.receptivo/previous.receptivo-1)*100;document.getElementById('tourHeroOut').textContent=`${tourFmt(current.emisivo/1000,3)} M`;document.getElementById('tourHeroIn').textContent=`${tourFmt(current.receptivo/1000,3)} M`;document.getElementById('tourHeroRatio').textContent=tourFmt(ratio,2);document.getElementById('tourRatioCurrent').textContent=tourFmt(ratio,2);document.getElementById('tourSummaryOut').textContent=`Turismo emisivo ${dyOut>=0?'↑':'↓'}`;document.getElementById('tourSummaryOutText').textContent=`${tourSigned(dyOut)} vs H1 2025 · ${tourFmt(current.emisivo/1000,3)} M`;document.getElementById('tourSummaryIn').textContent=`Turismo receptivo ${dyIn>=0?'↑':'↓'}`;document.getElementById('tourSummaryInText').textContent=`${tourSigned(dyIn)} vs H1 2025 · ${tourFmt(current.receptivo/1000,3)} M`;document.getElementById('tourFinalText').innerHTML=`En el primer semestre de 2026, el turismo emisivo <b>bajó ${tourFmt(Math.abs(dyOut),1)}%</b> y el receptivo <b>subió ${tourFmt(dyIn,1)}%</b> frente al mismo período de 2025. El verano sectorial también rebotó contra 2025, aunque siguió debajo de 2023 y con menor gasto diario real. <b>No podemos decir que el acceso general mejoró:</b> faltan turismo interno 2026 y datos recientes por ingreso.`;const valid=TOUR_DATA.monthly.filter(r=>r.ratio!=null);const min=valid.reduce((a,r)=>r.ratio<a.ratio?r:a),max=valid.reduce((a,r)=>r.ratio>a.ratio?r:a);document.getElementById('tourRatioMin').textContent=tourFmt(min.ratio,2);document.getElementById('tourRatioMinDate').textContent=tourDate(min.date);document.getElementById('tourRatioMax').textContent=tourFmt(max.ratio,2);document.getElementById('tourRatioMaxDate').textContent=tourDate(max.date)}
function renderTourFlow(){const monthly=tourFlowMode==='monthly';const rows=monthly?TOUR_DATA.monthly:TOUR_DATA.annual;const x=rows.map(r=>monthly?r.date:r.label);const layout=tourLayout('Turistas receptivos, emisivos y saldo · miles');layout.yaxis.title='miles de turistas';layout.barmode='overlay';if(monthly){layout.shapes=[{type:'line',x0:'2023-12-10',x1:'2023-12-10',yref:'paper',y0:0,y1:1,line:{color:'#dc6c91',width:2,dash:'dot'}}];layout.annotations=[{x:'2023-12-10',y:1.03,yref:'paper',text:'10/12/2023 · Milei',showarrow:false,font:{size:9,color:'#9d4667'},bgcolor:'#fff7fa'}]}const custom=rows.map(r=>[r.receptivo,r.emisivo,r.saldo,r.ratio]);Plotly.react('tourFlowChart',[{type:'bar',name:'Saldo receptivo − emisivo',x,y:rows.map(r=>r.saldo),marker:{color:'rgba(217,104,143,.22)',line:{color:'rgba(190,76,117,.45)',width:1}},customdata:custom,hovertemplate:'<b>%{x}</b><br>saldo: %{y:,.1f} mil<br>receptivo: %{customdata[0]:,.1f} mil<br>emisivo: %{customdata[1]:,.1f} mil<br>salidas/entrada: %{customdata[3]:.2f}<extra></extra>'},{type:'scatter',mode:'lines+markers',name:'Extranjeros que entran',x,y:rows.map(r=>r.receptivo),line:{color:'#49a381',width:3},marker:{size:monthly?4:7},customdata:custom,hovertemplate:'<b>%{x}</b><br>receptivo: %{y:,.1f} mil<br>emisivo: %{customdata[1]:,.1f} mil<br>saldo: %{customdata[2]:,.1f} mil<br>salidas/entrada: %{customdata[3]:.2f}<extra></extra>'},{type:'scatter',mode:'lines+markers',name:'Argentinos que salen',x,y:rows.map(r=>r.emisivo),line:{color:'#825ab2',width:3},marker:{size:monthly?4:7},customdata:custom,hovertemplate:'<b>%{x}</b><br>emisivo: %{y:,.1f} mil<br>receptivo: %{customdata[0]:,.1f} mil<br>saldo: %{customdata[2]:,.1f} mil<br>salidas/entrada: %{customdata[3]:.2f}<extra></extra>'}],layout,TOUR_CONFIG)}
function renderTourSpend(){const rows=TOUR_DATA.spending,x=rows.map(r=>String(r.year)),layout=tourLayout('Gasto turístico · USD millones corrientes');layout.barmode='group';layout.yaxis.title='USD millones';Plotly.react('tourSpendChart',[{type:'bar',name:'Gasto receptivo',x,y:rows.map(r=>r.receptivo_usd_m),marker:{color:'#53a886'},hovertemplate:'%{x}<br>receptivo: USD %{y:,.1f} M<extra></extra>'},{type:'bar',name:'Gasto emisivo',x,y:rows.map(r=>r.emisivo_usd_m),marker:{color:'#d36d96'},hovertemplate:'%{x}<br>emisivo: USD %{y:,.1f} M<extra></extra>'},{type:'scatter',mode:'lines+markers+text',name:'Saldo',x,y:rows.map(r=>r.saldo_usd_m),line:{color:'#6d4ea0',width:2},marker:{size:8},text:rows.map(r=>`−USD ${tourFmt(Math.abs(r.saldo_usd_m),1)} M`),textposition:'bottom center',hovertemplate:'%{x}<br>saldo: USD %{y:,.1f} M<extra></extra>'}],layout,TOUR_CONFIG)}
function renderTourRegions(selected='Total país'){const root=document.getElementById('tourRegionButtons');if(!root.children.length){root.innerHTML=TOUR_DATA.eoh.regions.map((name,i)=>`<button data-region="${name}" class="${i===0?'active':''}">${name}</button>`).join('')}const total=selected==='Total país';document.getElementById('tourRegionMetrics').innerHTML=total?`<div class="tour-region"><small>Pernoctaciones totales</small><strong>${tourFmt(TOUR_DATA.eoh.total_nights_m,1)} M</strong></div><div class="tour-region"><small>Variación total a/a</small><strong>${tourSigned(TOUR_DATA.eoh.total_nights_yoy)}</strong></div><div class="tour-region"><small>Noches residentes a/a</small><strong>${tourSigned(TOUR_DATA.eoh.resident_nights_yoy)}</strong></div><div class="tour-region"><small>Noches no residentes a/a</small><strong>${tourSigned(TOUR_DATA.eoh.nonresident_nights_yoy)}</strong></div>`:`<div class="tour-region"><small>${selected}</small><strong class="tour-sd">s/d</strong></div><div class="tour-region"><small>Viajeros residentes</small><strong class="tour-sd">s/d</strong></div><div class="tour-region"><small>Pernoctaciones</small><strong class="tour-sd">s/d</strong></div><div class="tour-region"><small>Ocupación / estadía</small><strong class="tour-sd">s/d</strong></div>`}
function renderTourSummer(){const rows=TOUR_DATA.summer,layout=tourLayout('Turistas de verano · millones');layout.yaxis.title='millones de turistas';Plotly.react('tourSummerChart',[{type:'bar',x:rows.map(r=>String(r.year)),y:rows.map(r=>r.tourists_m),marker:{color:['#9b7abc','#b08ac2','#d3859f','#58aa89']},text:rows.map(r=>tourFmt(r.tourists_m,1)),textposition:'outside',customdata:rows.map(r=>[r.tourists_yoy_derived,r.tourists_vs_2023,r.stay_nights]),hovertemplate:'<b>%{x}</b><br>turistas: %{y:.1f} M<br>vs previo: %{customdata[0]:.1f}%<br>vs 2023: %{customdata[1]:.1f}%<br>estadía: %{customdata[2]} noches<extra></extra>'}],layout,TOUR_CONFIG);document.getElementById('tourSummerVs23').textContent=tourSigned(rows.at(-1).tourists_vs_2023);renderTourSpendBars()}
function renderTourSpendBars(){const rows=[['Turistas',9.5,'good'],['Gasto total real',4.5,'good'],['Gasto diario real',-3.3,'bad'],['Estadía aprox.',(3.65/3.7-1)*100,'bad']];document.getElementById('tourSpendBars').innerHTML=rows.map(([name,value,cls])=>`<div class="tour-bar"><b>${name}</b><div class="tour-bar-track"><div class="tour-bar-fill ${cls}" style="width:${Math.max(6,Math.min(100,Math.abs(value)*8))}%"></div></div><strong>${tourSigned(value)}</strong></div>`).join('')}
function renderTourFx(){const normalized=document.getElementById('tourNormalize').checked,byDate=new Map(TOUR_DATA.monthly.map(r=>[r.date,r])),rows=TOUR_DATA.itcrm.map(r=>({...r,...(byDate.get(r.date)||{})})).filter(r=>r.receptivo!=null);const base=rows[0];const val=(v,b)=>normalized?v/b*100:v;const layout=tourLayout(normalized?'ITCRM y turismo · base dic-2024=100':'ITCRM y turismo · niveles');layout.yaxis.title=normalized?'índice base 100':'ITCRM';if(!normalized)layout.yaxis2={title:'miles de turistas',overlaying:'y',side:'right',gridcolor:'rgba(0,0,0,0)'};const yaxis=normalized?'y':'y2';Plotly.react('tourFxChart',[{type:'scatter',mode:'lines+markers',name:'ITCRM',x:rows.map(r=>r.date),y:rows.map(r=>val(r.value,base.value)),line:{color:'#d39435',width:3},hovertemplate:'%{x|%b %Y}<br>ITCRM: %{customdata:.2f}<extra></extra>',customdata:rows.map(r=>r.value)},{type:'scatter',mode:'lines+markers',name:'Argentinos que salen',x:rows.map(r=>r.date),y:rows.map(r=>val(r.emisivo,base.emisivo)),yaxis,line:{color:'#825ab2',width:3},hovertemplate:'%{x|%b %Y}<br>emisivo: %{customdata:,.1f} mil<extra></extra>',customdata:rows.map(r=>r.emisivo)},{type:'scatter',mode:'lines+markers',name:'Extranjeros que entran',x:rows.map(r=>r.date),y:rows.map(r=>val(r.receptivo,base.receptivo)),yaxis,line:{color:'#4ca482',width:3},hovertemplate:'%{x|%b %Y}<br>receptivo: %{customdata:,.1f} mil<extra></extra>',customdata:rows.map(r=>r.receptivo)}],layout,TOUR_CONFIG)}
function renderTourMarkets(){const rows=TOUR_DATA.origins_june_2026,colors=rows.map(r=>r.bordering?'#56a98a':'#9c75b7');const common={type:'bar',orientation:'h',y:rows.map(r=>r.market),marker:{color:colors},textposition:'outside',cliponaxis:false};let layout=tourLayout('Turistas que entraron · origen');layout.margin={l:125,r:35,t:58,b:45};layout.yaxis={automargin:true,categoryorder:'total ascending'};layout.xaxis={title:'miles de turistas',gridcolor:'#eee5f2'};Plotly.react('tourOriginChart',[{...common,x:rows.map(r=>r.receptivo_k),text:rows.map(r=>tourFmt(r.receptivo_k,1)),hovertemplate:'%{y}<br>%{x:.1f} mil<extra></extra>'}],layout,TOUR_CONFIG);layout=tourLayout('Argentinos que salieron · destino');layout.margin={l:125,r:35,t:58,b:45};layout.yaxis={automargin:true,categoryorder:'total ascending'};layout.xaxis={title:'miles de turistas',gridcolor:'#eee5f2'};Plotly.react('tourDestinationChart',[{...common,x:rows.map(r=>r.emisivo_k),text:rows.map(r=>tourFmt(r.emisivo_k,1)),hovertemplate:'%{y}<br>%{x:.1f} mil<extra></extra>'}],layout,TOUR_CONFIG)}
function renderTourCompare(){const current=TOUR_DATA.summer.find(r=>r.year===2026),root=document.getElementById('tourGlobalCompareText');if(tourCompareBase==='prepandemic'){root.innerHTML='<b>Verano 2026 vs prepandemia:</b> s/d en una serie CAME homogénea dentro de las publicaciones usadas. No se fuerza la comparación.';return}if(tourCompareBase==='previous')tourCompareBase='2025';const base=TOUR_DATA.summer.find(r=>String(r.year)===tourCompareBase);const change=(current.tourists_m/base.tourists_m-1)*100;root.innerHTML=`<b>Verano 2026 vs ${base.year}:</b> ${tourSigned(change)} en turistas (${tourFmt(current.tourists_m,1)} M frente a ${tourFmt(base.tourists_m,1)} M). ${base.year===2025?'Mejoró contra el año previo, pero eso no alcanza para decir que recuperó 2023.':base.year===2023?'La recuperación parcial deja el nivel todavía por debajo de 2023.':'Comparación de cantidad; gasto y estadía requieren sus propias series.'}`}
function renderTour(){renderTourHero();renderTourFlow();renderTourSpend();renderTourRegions();renderTourSummer();renderTourFx();renderTourMarkets();renderTourCompare();tourRendered=true}
document.getElementById('tourFlowMode')?.addEventListener('click',e=>{const b=e.target.closest('button[data-mode]');if(!b)return;tourFlowMode=b.dataset.mode;document.querySelectorAll('#tourFlowMode button').forEach(x=>x.classList.toggle('active',x===b));renderTourFlow()});
document.getElementById('tourRegionButtons')?.addEventListener('click',e=>{const b=e.target.closest('button[data-region]');if(!b)return;document.querySelectorAll('#tourRegionButtons button').forEach(x=>x.classList.toggle('active',x===b));renderTourRegions(b.dataset.region)});
document.getElementById('tourGlobalCompare')?.addEventListener('click',e=>{const b=e.target.closest('button[data-base]');if(!b)return;tourCompareBase=b.dataset.base;document.querySelectorAll('#tourGlobalCompare button').forEach(x=>x.classList.toggle('active',x===b));renderTourCompare()});
document.getElementById('tourNormalize')?.addEventListener('change',renderTourFx);
function downloadTourData(kind){const item=TOUR_DOWNLOADS[kind];if(!item)return;const blob=new Blob(['\ufeff'+item.content],{type:item.type}),a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download=item.filename;document.body.appendChild(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(a.href),800)}
function tourProjectAsset(name){const inVersion=/\/data\/dashboard_/i.test(location.pathname);return new URL((inVersion?'derivados/vacaciones_turismo/':'data/derivados/vacaciones_turismo/')+name,location.href).href}
document.getElementById('tourAuditLink')?.setAttribute('href',tourProjectAsset('AUDITORIA_VACACIONES_TURISMO.md'));
document.querySelector('[data-tab="tab-tourism"]')?.addEventListener('click',()=>requestAnimationFrame(renderTour));
window.addEventListener('resize',()=>{if(!tourRendered)return;['tourFlowChart','tourSpendChart','tourSummerChart','tourFxChart','tourOriginChart','tourDestinationChart'].forEach(id=>{const el=document.getElementById(id);if(el&&window.Plotly)Plotly.Plots.resize(el)})});
</script>
"""


def derive_and_write(data: dict) -> dict:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    json_path = OUT_DIR / "vacaciones_turismo_data.json"
    json_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    csv_path = OUT_DIR / "vacaciones_turismo_flujos.csv"
    with csv_path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["date", "receptivo", "emisivo", "saldo", "ratio"])
        writer.writeheader()
        writer.writerows(data["monthly"])

    h1_2025 = [row for row in data["monthly"] if row["date"].startswith("2025-") and int(row["date"][5:7]) <= 6]
    h1_2026 = [row for row in data["monthly"] if row["date"].startswith("2026-") and int(row["date"][5:7]) <= 6]
    sum_field = lambda rows, field: sum(row[field] for row in rows)
    r25, e25 = sum_field(h1_2025, "receptivo"), sum_field(h1_2025, "emisivo")
    r26, e26 = sum_field(h1_2026, "receptivo"), sum_field(h1_2026, "emisivo")
    tests = {
        "monthly_rows": len(data["monthly"]),
        "annual_rows": len(data["annual"]),
        "h1_2026_receptivo_k": r26,
        "h1_2026_emisivo_k": e26,
        "h1_2026_ratio": e26 / r26,
        "h1_receptivo_yoy_pct": (r26 / r25 - 1) * 100,
        "h1_emisivo_yoy_pct": (e26 / e25 - 1) * 100,
        "spending_2025_balance_usd_m": data["spending"][1]["saldo_usd_m"],
        "summer_2026_vs_2023_pct": data["summer"][-1]["tourists_vs_2023"],
        "months_complete_through_june_2026": len(data["monthly"]) == 54,
    }
    tests["all_passed"] = all([
        abs(r26 - 2897.913) < 0.001,
        abs(e26 - 6383.576) < 0.001,
        abs(data["spending"][1]["saldo_usd_m"] + 4054.2) < 0.001,
        tests["months_complete_through_june_2026"],
    ])
    tests_path = OUT_DIR / "TESTS_VACACIONES_TURISMO.json"
    tests_path.write_text(json.dumps(tests, ensure_ascii=False, indent=2), encoding="utf-8")
    audit = f"""# Auditoría — Vacaciones · Turismo

**Corte editorial:** 21/08/2026

## Controles numéricos

- Flujos físicos: INDEC, turistas (no excursionistas), registros migratorios y total de vías; {len(data['monthly'])} meses entre enero de 2022 y junio de 2026.
- H1 2026 receptivo: **{r26 / 1000:.3f} M**; emisivo: **{e26 / 1000:.3f} M**; ratio: **{e26 / r26:.3f}**.
- Variación H1 2026/H1 2025: receptivo **{(r26 / r25 - 1) * 100:.2f}%**; emisivo **{(e26 / e25 - 1) * 100:.2f}%**.
- Gasto ETI 2025, pasos relevados: USD 3.110,0 M receptivo − USD 7.164,2 M emisivo = **−USD {abs(data['spending'][1]['saldo_usd_m']):.1f} M**.
- Verano CAME: 30,7 M en 2026; **{data['summer'][-1]['tourists_vs_2023']:.2f}%** contra 2023. El comparador 2025 de estadía queda `s/d` por discrepancia entre publicaciones.
- EOH: último reporte nacional usado, noviembre de 2025. No se extrapola 2026.
- BCRA marzo de 2026: Viajes y Pasajes, saldo −USD 393 M; ≈70% de egresos cancelado con fondos propios según el informe.

## Reglas semánticas

1. Flujos nacionales de registros migratorios y gasto ETI no se mezclan: tienen coberturas distintas.
2. Turista, excursionista, viaje, noche y gasto no se tratan como sinónimos.
3. CAME se rotula siempre como fuente sectorial.
4. Gasto turístico externo no equivale a una venta directa de reservas del BCRA.
5. ITCRM y turismo se superponen sólo descriptivamente; no se afirma causalidad.
6. No se inventan precios de destinos ni distribución por ingreso: permanecen `s/d`.
7. Comparar 2026 con 2025 y con 2023 evita llamar recuperación completa a un rebote parcial.

## Fuentes

""" + "\n".join(f"- {name}: {url}" for name, url in SOURCES.items()) + "\n"
    audit_path = OUT_DIR / "AUDITORIA_VACACIONES_TURISMO.md"
    audit_path.write_text(audit, encoding="utf-8")
    return {"json": json_path, "csv": csv_path, "tests": tests_path}


def build() -> None:
    data = build_data()
    derived = derive_and_write(data)
    html = SOURCE_HTML.read_text(encoding="utf-8")
    nav_anchor = '    <button class="tab-btn" data-tab="tab-debt-public">Deuda pública</button>'
    section_anchor = '  <section id="tab-debt-public" class="tab-panel">'
    if nav_anchor not in html or section_anchor not in html:
        raise RuntimeError("No se encontraron los anclajes de la versión 139")
    html = html.replace(nav_anchor, '    <button class="tab-btn" data-tab="tab-tourism">Vacaciones · Turismo</button>\n' + nav_anchor, 1)
    html = html.replace(section_anchor, SECTION + "\n" + section_anchor, 1)
    html = html.replace("</head>", CSS + "\n</head>", 1)
    downloads = {
        "json": {"filename": derived["json"].name, "type": "application/json;charset=utf-8", "content": derived["json"].read_text(encoding="utf-8")},
        "csv": {"filename": derived["csv"].name, "type": "text/csv;charset=utf-8", "content": derived["csv"].read_text(encoding="utf-8-sig")},
    }
    script = SCRIPT_TEMPLATE.replace("__TOUR_DATA__", json.dumps(data, ensure_ascii=False, separators=(",", ":"))).replace("__TOUR_DOWNLOADS__", json.dumps(downloads, ensure_ascii=False, separators=(",", ":")))
    html = html.replace("</body>", script + "\n</body>", 1)
    OUTPUT_HTML.write_text(html, encoding="utf-8")
    print(f"Built {OUTPUT_HTML.relative_to(ROOT)}")
    print(f"Months: {len(data['monthly'])} · tests passed: {json.loads(derived['tests'].read_text(encoding='utf-8'))['all_passed']}")


if __name__ == "__main__":
    build()
