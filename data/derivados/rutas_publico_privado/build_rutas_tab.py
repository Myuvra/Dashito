from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
SOURCE_HTML = ROOT / "data" / "dashboard_kawaii_138_pendulo_promedios_politicos.html"
OUTPUT_HTML = ROOT / "data" / "dashboard_kawaii_139_rutas_publico_privado.html"
OUT_DIR = Path(__file__).resolve().parent


SOURCES = {
    "rfc": "https://www.argentina.gob.ar/transporte/vialidad-nacional/red-federal-de-concesiones",
    "stage3_status": "https://www.argentina.gob.ar/noticias/avance-de-la-red-federal-de-concesiones-apertura-de-ofertas-economicas-para-la-etapa-iii",
    "law": "https://www.argentina.gob.ar/normativa/nacional/ley-17520-16942/actualizacion",
    "bice_stage3": "https://www.bice.com.ar/institucional/mas-informacion/fideicomiso-financiero-red-federal-de-concesiones-etapa-iii/",
    "bice_cuyo": "https://www.bice.com.ar/wp-content/uploads/2026/05/RedFederaldeConcesiones-EtapaIII-TramoCUYO.pdf",
    "opc_2024": "https://opc.gob.ar/ejecucion-presupuestaria/ejecucion-mensual-base-devengado/analisis-de-la-ejecucion-presupuestaria-de-la-inversion-publica-2024/",
    "opc_2025": "https://opc.gob.ar/ejecucion-presupuestaria/ejecucion-mensual-base-devengado/analisis-de-la-ejecucion-presupuestaria-de-la-inversion-publica-2025/",
    "opc_2026": "https://opc.gob.ar/download/50855/?tmstv=1781210735",
    "agn_ppp": "https://www.agn.gob.ar/informes/Informe-109-2026",
    "world_bank": "https://ppp.worldbank.org/library/toll-roads-ppps-identifying-mitigating-and-managing-traffic-risk",
    "pavement": "https://www.argentina.gob.ar/noticias/vialidad-nacional-pone-disposicion-los-primeros-informes-de-transito-y-estados-de-calzada",
    "stage1_award": "https://www.argentina.gob.ar/node/485451",
    "stage1_start": "https://www.argentina.gob.ar/noticias/red-federal-de-concesiones-etapa-i-toma-de-posesion-de-los-tramos-oriental-y-conexion",
    "stage2a_award": "https://www.argentina.gob.ar/noticias/avance-de-la-red-federal-de-concesiones-se-adjudicaron-los-tramos-de-la-etapa-ii",
    "stage2b_status": "https://www.argentina.gob.ar/noticias/avance-de-la-red-federal-de-concesiones-apertura-de-ofertas-economicas-para-la-etapa-ii-b",
}


CORRIDORS = [
    {"id": "I-ORIENTAL", "stage": "I", "corridor": "Oriental", "routes": "RN 12, 14, 117, 135, A-015", "km": 682.28, "status": "En operación", "company": "Autovía Construcciones y Servicios S.A.", "award_date": "2025-11-19", "start_date": "2026-01-07", "duration_years": None, "tariff": None, "investment_committed": None, "investment_certified": None, "new_road_km": None, "rehab_km": None, "financing_bice": "Instrumento opcional anunciado para Etapa I", "subsidy": "El Gobierno informa sin subsidio presupuestario; auditar contrato", "source": SOURCES["stage1_start"]},
    {"id": "I-CONEXION", "stage": "I", "corridor": "Conexión", "routes": "RN 174 · Puente Rosario–Victoria", "km": 59.43, "status": "En operación", "company": "UTE Obring, Rovial, Edeca, Pitón y Pietroboni", "award_date": "2025-11-19", "start_date": "2026-01-07", "duration_years": None, "tariff": None, "investment_committed": None, "investment_certified": None, "new_road_km": None, "rehab_km": None, "financing_bice": "Instrumento opcional anunciado para Etapa I", "subsidy": "El Gobierno informa sin subsidio presupuestario; auditar contrato", "source": SOURCES["stage1_start"]},
    {"id": "IIA-SUR", "stage": "II-A", "corridor": "Sur Atlántico · Acceso Sur", "routes": "Au. Ezeiza–Cañuelas, Riccheri, Newbery; RN 3, 205, 226", "km": 1325.17, "status": "Adjudicado", "company": "Concret Nor, Marcalba, Pose y Coarco", "award_date": "2026-05-15", "start_date": None, "duration_years": 20, "tariff": None, "investment_committed": None, "investment_certified": None, "new_road_km": None, "rehab_km": None, "financing_bice": None, "subsidy": "El Gobierno informa sin erogaciones; auditar contrato", "source": SOURCES["stage2a_award"]},
    {"id": "IIA-PAMPA", "stage": "II-A", "corridor": "Pampa", "routes": "RN 5", "km": 546.65, "status": "Adjudicado", "company": "Construcciones Electromecánicas del Oeste S.A.", "award_date": "2026-05-15", "start_date": None, "duration_years": 20, "tariff": None, "investment_committed": None, "investment_certified": None, "new_road_km": None, "rehab_km": None, "financing_bice": None, "subsidy": "El Gobierno informa sin erogaciones; auditar contrato", "source": SOURCES["stage2a_award"]},
    {"id": "IIB-MEDITERRANEO", "stage": "II-B", "corridor": "Mediterráneo", "routes": "RN 7, 35", "km": 672.32, "status": "Ofertas económicas abiertas 06/07/2026", "company": None, "award_date": None, "start_date": None, "duration_years": None, "tariff": None, "investment_committed": None, "investment_certified": None, "new_road_km": None, "rehab_km": None, "financing_bice": None, "subsidy": None, "source": SOURCES["stage2b_status"]},
    {"id": "IIB-PUNTANO", "stage": "II-B", "corridor": "Puntano", "routes": "RN 8, 36, 193, A-005", "km": 720.00, "status": "Ofertas económicas abiertas 06/07/2026", "company": None, "award_date": None, "start_date": None, "duration_years": None, "tariff": None, "investment_committed": None, "investment_certified": None, "new_road_km": None, "rehab_km": None, "financing_bice": None, "subsidy": None, "source": SOURCES["stage2b_status"]},
    {"id": "IIB-PORTUARIO-S", "stage": "II-B", "corridor": "Portuario Sur", "routes": "RN 9, 188", "km": 636.75, "status": "Ofertas económicas abiertas 06/07/2026", "company": None, "award_date": None, "start_date": None, "duration_years": None, "tariff": None, "investment_committed": None, "investment_certified": None, "new_road_km": None, "rehab_km": None, "financing_bice": None, "subsidy": None, "source": SOURCES["stage2b_status"]},
    {"id": "IIB-PORTUARIO-N", "stage": "II-B", "corridor": "Portuario Norte", "routes": "RN 9, 33, A-008", "km": 528.04, "status": "Ofertas económicas abiertas 06/07/2026", "company": None, "award_date": None, "start_date": None, "duration_years": None, "tariff": None, "investment_committed": None, "investment_certified": None, "new_road_km": None, "rehab_km": None, "financing_bice": None, "subsidy": None, "source": SOURCES["stage2b_status"]},
]

STAGE3 = [
    ("Centro", "RN 9, 19, 34", 681.92),
    ("Mesopotámico", "RN 12, 18", 276.11),
    ("Centro–Norte", "RN 34", 536.43),
    ("Noroeste", "RN 9, 34, 66, 1V66, A-016", 596.52),
    ("Litoral", "RN 12, 16", 546.74),
    ("Noreste", "RN 12, 105", 456.22),
    ("Chaco–Santa Fe", "RN 11", 497.18),
    ("Cuyo", "RN 7", 329.09),
]

for corridor, routes, km in STAGE3:
    CORRIDORS.append({
        "id": "III-" + corridor.upper().replace("Á", "A").replace("–", "-").replace(" ", "-"),
        "stage": "III", "corridor": corridor, "routes": routes, "km": km,
        "status": "Ofertas económicas abiertas 22/07/2026 · adjudicación pendiente en la última fuente oficial",
        "company": None, "award_date": None, "start_date": None, "duration_years": None,
        "tariff": None, "investment_committed": None, "investment_certified": None,
        "new_road_km": None, "rehab_km": None,
        "financing_bice": "Términos indicativos disponibles; instrumento por corredor",
        "subsidy": None, "source": SOURCES["stage3_status"],
    })


DATA = {
    "cutoff": "2026-08-21",
    "stage3": {
        "procurement": "504-0001-LPU26",
        "bid_open_date": "2026-07-22",
        "bidders": 21,
        "offers": 48,
        "corridors": [{"corridor": a, "routes": b, "km": c} for a, b, c in STAGE3],
        "source": SOURCES["rfc"],
        "status_source": SOURCES["stage3_status"],
    },
    "network_concentration": {"network_km_share": 20, "traffic_share": 80, "scope": "Red Federal de Concesiones completa", "source": "https://www.argentina.gob.ar/node/471981"},
    "public_investment": [
        {"year": "2023", "real_change": None, "index": 100.0, "coverage": "Inversión pública nacional total", "source": "https://opc.gob.ar/ejecucion-presupuestaria/proyectos-de-inversion/analisis-de-la-ejecucion-presupuestaria-de-la-inversion-publica-2023/"},
        {"year": "2024", "real_change": -75.1, "index": None, "coverage": "Inversión pública nacional total", "source": SOURCES["opc_2024"]},
        {"year": "2025", "real_change": -27.0, "index": None, "coverage": "Inversión pública nacional total", "source": SOURCES["opc_2025"]},
    ],
    "investment_ytd": {"period": "ene–may 2026", "dnv_road_works_real_change": -30.9, "ird_real_change": -34.2, "coverage": "comparación interanual; no se empalma con años completos", "source": SOURCES["opc_2026"]},
    "bice_cuyo": {"date": "2026-05", "stage": "III", "corridor": "Cuyo", "estimated_first_year_investment_ars": 30307503022.27, "max_issue_ars": 21215000000, "max_share": 70, "sponsor_min_share": 15, "unit": "UVA", "rate": "UVA + 2%", "term_years": 6, "grace_years": 1, "max_assigned_collection_share": 70, "status": "Indicativo, preliminar, no vinculante", "source": SOURCES["bice_cuyo"]},
    "ppp_2018": {"contracts": 6, "award_year": 2018, "last_extinction": "2020-12-15", "required_tpi_usd": 9969428469, "contingent_contribution_estimate_usd": 8837327324, "audit_period": "2018-07-31 → 2020-12-31; fideicomiso hasta 2022", "source": SOURCES["agn_ppp"]},
    "corridors": CORRIDORS,
    "sources": SOURCES,
}


CSS = r"""
<style id="rutas-publico-privado-v139">
/* v139 · Rutas: público o privado */
#tab-roads{padding-top:4px}.road-shell{display:grid;gap:16px;color:#5b4167}.road-card{min-width:0;padding:20px;border:1px solid #e2d4ea;border-radius:24px;background:rgba(255,255,255,.92);box-shadow:0 10px 24px rgba(90,57,112,.06);box-sizing:border-box}.road-hero{background:linear-gradient(135deg,rgba(255,250,253,.98),rgba(246,253,255,.98));border-color:#d8c4e8}.road-head{display:flex;align-items:flex-start;justify-content:space-between;gap:16px}.road-head h2,.road-head h3,.road-head h4{margin:0;color:#583766;line-height:1.2}.road-head h2{font-size:27px}.road-head h3{font-size:20px}.road-sub{margin:7px 0 0;font-size:11px;line-height:1.55;color:#75617a}.road-kicker,.road-pill{display:inline-flex;align-items:center;gap:5px;padding:6px 9px;border:1px solid #dac8e5;border-radius:999px;background:#fff;font-size:8.5px;font-weight:950;letter-spacing:.035em;text-transform:uppercase;color:#765284}.road-pill.good{border-color:#b8dccb;background:#f5fff9;color:#2c8062}.road-pill.warn{border-color:#ead49a;background:#fffbed;color:#7d6325}.road-pill.bad{border-color:#e6b9ca;background:#fff6fa;color:#a23e64}.road-question{margin:14px 0;padding:14px 16px;border-left:5px solid #9a6bb2;border-radius:15px;background:#fbf7ff;font-size:16px;font-weight:950;color:#553563}.road-question small{display:block;margin-top:5px;font-size:10px;font-weight:700;line-height:1.5;color:#746078}.road-five{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:9px;margin-top:13px}.road-five div{padding:12px;border:1px solid #dfd2e7;border-radius:15px;background:#fff;text-align:center}.road-five b{display:block;margin-top:4px;font-size:11px;color:#5d3e6a}.road-five span{font-size:23px}.road-kpis{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:10px;margin-top:14px}.road-kpi{padding:14px;border:1px solid #ded2e5;border-radius:16px;background:#fff}.road-kpi small{display:block;font-size:7.8px;font-weight:950;letter-spacing:.04em;text-transform:uppercase;color:#836f89}.road-kpi strong{display:block;margin:5px 0 3px;font-size:23px;line-height:1.05;color:#5b3c68}.road-kpi span{font-size:9px;line-height:1.45;color:#76627b}.road-kpi.green{background:#f5fff9;border-color:#b9ddcc}.road-kpi.green strong{color:#2f8566}.road-kpi.pink{background:#fff7fa;border-color:#e4bccd}.road-kpi.pink strong{color:#ad416b}.road-kpi.gold{background:#fffdf5;border-color:#ead8a9}.road-kpi.gold strong{color:#9b721d}.road-plain{margin-top:11px;padding:12px 14px;border:1px dashed #d8c8e1;border-radius:14px;background:#fdfbff;font-size:10.5px;line-height:1.55;color:#6e5974}.road-plain b{color:#51315f}.road-grid-2{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:14px}.road-grid-3{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:11px}.road-mini{padding:14px;border:1px solid #dfd3e7;border-radius:17px;background:#fff;font-size:10px;line-height:1.55;color:#6e5a73}.road-mini h4{margin:0 0 7px;font-size:13px;color:#5b3b68}.road-mini strong{color:#53345f}.road-legal{display:grid;grid-template-columns:auto 1fr;gap:14px;align-items:start;margin-top:13px;padding:16px;border:2px solid #bcdaca;border-radius:18px;background:#f5fff9}.road-legal .icon{font-size:38px}.road-legal h4{margin:0 0 6px;color:#2d775e}.road-legal p{margin:0;font-size:11px;line-height:1.6;color:#5e6d66}.road-chart-scroll{max-width:100%;overflow-x:auto;overflow-y:hidden;padding-bottom:4px;-webkit-overflow-scrolling:touch}.road-chart{width:100%;min-width:780px;height:430px}.road-chart.small{height:340px;min-width:620px}.road-type-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:9px;margin-top:12px}.road-type{padding:12px;border-radius:14px;border:1px solid #dfd2e7;background:#fff}.road-type b{display:block;margin-bottom:4px;font-size:10px;color:#5c3d69}.road-type span{font-size:9px;line-height:1.45;color:#746178}.road-flow{display:grid;grid-template-columns:1fr 46px 1fr;gap:10px;align-items:stretch;margin-top:13px}.road-flow-model{padding:15px;border:1px solid #dfd2e7;border-radius:17px;background:#fff}.road-flow-model h4{margin:0 0 10px;font-size:13px;color:#5b3c68}.road-flow-steps{display:grid;gap:5px}.road-step{padding:9px;border-radius:11px;background:#f8f4fb;text-align:center;font-size:9.5px;font-weight:900;color:#63486f}.road-down{text-align:center;color:#9b6daf;font-size:17px}.road-vs{display:flex;align-items:center;justify-content:center;font-size:16px;font-weight:950;color:#a071b4}.road-logistics{margin-top:11px;padding:12px;border:1px solid #ead6a4;border-radius:14px;background:#fffdf3;text-align:center;font-size:10px;line-height:1.5;color:#705d39}.road-logistics b{color:#6a4e14}.road-funding{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:10px;margin-top:13px}.road-funding article{padding:14px;border:1px solid #dfd2e7;border-radius:16px;background:#fff}.road-funding h4{margin:0 0 7px;font-size:12px;color:#5a3b68}.road-funding ul{margin:0;padding-left:17px;font-size:9.5px;line-height:1.55;color:#715e75}.road-bice{margin-top:12px;padding:15px;border:2px solid #cdbce1;border-radius:18px;background:linear-gradient(135deg,#fbf8ff,#f6fff9)}.road-bice-grid{display:grid;grid-template-columns:repeat(6,minmax(0,1fr));gap:8px;margin-top:10px}.road-bice-grid div{padding:10px;border-radius:12px;background:#fff;border:1px solid #dfd4e6}.road-bice-grid small{display:block;font-size:7px;text-transform:uppercase;font-weight:950;color:#88758d}.road-bice-grid strong{display:block;margin-top:3px;font-size:13px;color:#5b3c68}.road-bars{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-top:13px}.road-bar-card{padding:15px;border:1px solid #dfd2e7;border-radius:17px;background:#fff}.road-bar-card h4{margin:0 0 10px;font-size:12px;color:#5b3b68}.road-bar-track{height:24px;border-radius:999px;background:#f2ebf5;overflow:hidden}.road-bar-fill{height:100%;display:flex;align-items:center;padding-left:10px;box-sizing:border-box;border-radius:999px;background:linear-gradient(90deg,#aa78c0,#6e51aa);color:#fff;font-size:9px;font-weight:950}.road-bar-fill.traffic{background:linear-gradient(90deg,#3d9b78,#61bd92)}.road-sim{display:grid;grid-template-columns:minmax(0,.95fr) minmax(0,1.05fr);gap:14px;margin-top:13px}.road-sim-controls{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:9px}.road-field{padding:10px;border:1px solid #dfd3e7;border-radius:13px;background:#fff}.road-field label{display:block;font-size:8px;font-weight:950;text-transform:uppercase;color:#7d6883}.road-field input{width:100%;box-sizing:border-box;margin-top:5px;border:1px solid #d8c9e2;border-radius:9px;padding:8px;color:#5a4165;font:inherit}.road-field output{display:block;margin-top:4px;font-size:9px;color:#7c687f}.road-sim-result{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:9px}.road-result{padding:14px;border-radius:15px;background:#fff;border:1px solid #ddd0e5}.road-result small{display:block;font-size:7.5px;font-weight:950;text-transform:uppercase;color:#846f89}.road-result strong{display:block;margin-top:5px;font-size:19px;color:#593b66}.road-sim-verdict{grid-column:1/-1;padding:14px;border-radius:15px;border:2px solid #d7c7e2;background:#fbf8ff;font-size:11px;line-height:1.55;color:#66506e}.road-sim-verdict.good{border-color:#abd8c3;background:#f3fff8}.road-sim-verdict.bad{border-color:#e2b4c7;background:#fff6fa}.road-definitions{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:10px;margin-top:12px}.road-def{padding:14px;border-radius:16px;background:#fff;border:1px solid #dfd2e7}.road-def b{display:block;margin-bottom:5px;color:#5a3b67;font-size:11px}.road-def span{font-size:9.5px;line-height:1.5;color:#725f76}.road-cost{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-top:13px}.road-formula{padding:15px;border:1px solid #dfd2e7;border-radius:17px;background:#fff}.road-formula h4{margin:0 0 8px;font-size:13px;color:#5b3b68}.road-formula code{display:block;white-space:pre-wrap;padding:11px;border-radius:12px;background:#f8f4fb;color:#5e4668;font-size:9px;line-height:1.55}.road-table-wrap{max-width:100%;overflow:auto;margin-top:12px;border:1px solid #e0d4e7;border-radius:15px;background:#fff}.road-table{width:100%;min-width:1120px;border-collapse:collapse;font-size:8.8px}.road-table th,.road-table td{padding:9px 10px;border-bottom:1px solid #eee5f2;text-align:left;vertical-align:top}.road-table th{position:sticky;top:0;background:#f7f1fb;color:#71527e;font-size:7.5px;text-transform:uppercase}.road-table tr:last-child td{border-bottom:0}.road-table .num{text-align:right;font-variant-numeric:tabular-nums}.road-filter{display:flex;flex-wrap:wrap;gap:8px;margin-top:11px}.road-filter button{border:1px solid #d8c8e2;border-radius:999px;background:#fff;padding:8px 10px;color:#674a73;font:inherit;font-size:9px;font-weight:900;cursor:pointer}.road-filter button.active{border-color:#9a64b2;background:#f4eafa}.road-timeline{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:9px;margin-top:13px}.road-time{position:relative;padding:14px 12px;border:1px solid #dfd2e7;border-radius:16px;background:#fff}.road-time b{display:block;font-size:15px;color:#5b3b68}.road-time span{display:block;margin-top:5px;font-size:9px;line-height:1.45;color:#735f77}.road-time:not(:last-child)::after{content:'→';position:absolute;right:-14px;top:18px;z-index:2;color:#a173b4;font-size:17px}.road-faq{display:grid;gap:8px;margin-top:12px}.road-faq details,.road-method details{border:1px solid #dfd3e7;border-radius:14px;background:#fff}.road-faq summary,.road-method summary{cursor:pointer;padding:12px 14px;font-size:10.5px;font-weight:950;color:#5f416c}.road-faq details div,.road-method details div{padding:0 14px 13px;font-size:9.8px;line-height:1.58;color:#705d75}.road-final{padding:18px;border:2px solid #cdbbe0;border-radius:20px;background:linear-gradient(135deg,#fbf7ff,#f4fff8)}.road-final h3{margin:0;color:#593867;font-size:20px}.road-final>p{font-size:12px;line-height:1.6;color:#654f6d}.road-links{display:flex;flex-wrap:wrap;gap:8px;margin-top:12px}.road-link{appearance:none;border:1px solid #d8cae3;border-radius:999px;background:#fff;padding:8px 11px;color:#654770;font:inherit;font-size:9.5px;font-weight:900;cursor:pointer;text-decoration:none}.road-sources{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:8px;margin-top:12px}.road-source{padding:11px;border:1px solid #e1d5e8;border-radius:13px;background:#fff;font-size:9px;line-height:1.45;color:#6e5b73}.road-source a{color:#744c89;font-weight:900}.road-muted{color:#8b7a90}.road-sd{font-weight:950;color:#9b4a6a}.road-note{margin-top:9px;font-size:9px;line-height:1.5;color:#806d84}.road-note b{color:#5b3d68}
@media(max-width:1100px){.road-five{grid-template-columns:repeat(3,minmax(0,1fr))}.road-kpis{grid-template-columns:repeat(2,minmax(0,1fr))}.road-grid-3,.road-funding,.road-definitions{grid-template-columns:1fr}.road-bice-grid{grid-template-columns:repeat(3,minmax(0,1fr))}.road-sim,.road-cost{grid-template-columns:1fr}.road-timeline{grid-template-columns:repeat(3,minmax(0,1fr))}.road-time::after{display:none}}
@media(max-width:760px){.road-card{padding:15px;border-radius:20px}.road-head{display:block}.road-head h2{font-size:23px}.road-five,.road-kpis,.road-grid-2,.road-bars,.road-sources{grid-template-columns:1fr}.road-flow{grid-template-columns:1fr}.road-vs{padding:2px}.road-bice-grid{grid-template-columns:repeat(2,minmax(0,1fr))}.road-chart{min-width:760px;height:410px}.road-chart.small{min-width:650px}.road-sim-controls{grid-template-columns:1fr 1fr}.road-sim-result{grid-template-columns:1fr}.road-timeline{grid-template-columns:1fr}.road-type-grid{grid-template-columns:1fr 1fr}.road-legal{grid-template-columns:1fr}.road-five div{text-align:left;display:flex;align-items:center;gap:8px}.road-five b{margin:0}}
@media(max-width:430px){.road-card{padding:12px}.road-bice-grid,.road-sim-controls,.road-type-grid{grid-template-columns:1fr}.road-chart{min-width:720px}.road-sub{font-size:10.5px}.road-question{font-size:14px;padding:12px}.road-kpi strong{font-size:21px}}
@media(max-width:390px){.road-card{padding:10px}.road-chart{min-width:700px}.road-kicker{white-space:normal}}
</style>
"""


SECTION = r"""
  <!-- RUTAS_PUBLICO_PRIVADO_TAB_VERSION:1 -->
  <section id="tab-roads" class="tab-panel">
    <div class="road-shell">
      <section class="road-card road-hero">
        <div class="road-head"><div><span class="road-kicker">Vialidad · concesiones · inversión pública · corte 21/08/2026</span><h2>Rutas · ¿Público o privado? ♡</h2><p class="road-sub">Quién es dueño, quién ejecuta, quién financia, quién paga y quién asume el riesgo.</p></div><span class="road-pill warn">tab en seguimiento</span></div>
        <div class="road-question">¿La inversión privada reemplazó realmente a la obra pública?<small>No alcanza con mirar quién firma el contrato: hay que separar propiedad, ejecución, capital inicial, repago y riesgo.</small></div>
        <div class="road-five"><div><span>🛣️</span><b>¿Quién es dueño?</b></div><div><span>👷</span><b>¿Quién construye?</b></div><div><span>🏦</span><b>¿Quién financia?</b></div><div><span>🚙</span><b>¿Quién paga?</b></div><div><span>⚠️</span><b>¿Quién arriesga?</b></div></div>
        <div class="road-kpis"><div class="road-kpi"><small>Etapa III</small><strong id="roadStage3Km">—</strong><span>km de corredores existentes incluidos</span></div><div class="road-kpi pink"><small>Ruta nueva demostrada</small><strong class="road-sd">s/d</strong><span>los pliegos no publican una suma homogénea de km nuevos</span></div><div class="road-kpi gold"><small>Estado licitatorio</small><strong>48 ofertas</strong><span>21 oferentes · sobres económicos 22/07/2026</span></div><div class="road-kpi green"><small>Concentración RFC</small><strong>20% → 80%</strong><span>de km de red → tránsito aproximado</span></div></div>
        <div class="road-plain"><b>Respuesta corta:</b> no se vendieron 3.900 km ni se construyeron 3.900 km nuevos. Se licita la concesión temporal de corredores públicos existentes para explotación, mantenimiento y obras. El costo deja de concentrarse en el presupuesto y pasa en mayor medida a peajes, financiamiento y usuarios.</div>
      </section>

      <section class="road-card">
        <div class="road-head"><div><span class="road-kicker">Panel 1 · la cifra bajo la lupa</span><h3>3.900 km ≠ 3.900 km de rutas nuevas</h3><p class="road-sub">La tabla oficial de Etapa III suma 3.920,21 km en ocho corredores. La última fuente oficial encontrada estaba todavía en apertura de ofertas económicas.</p></div><span class="road-pill bad">no confundir stock con obra nueva</span></div>
        <div class="road-chart-scroll"><div id="roadCorridorChart" class="road-chart"></div></div>
        <div class="road-type-grid"><div class="road-type"><b>Corredor concesionado</b><span>Longitud de ruta existente entregada temporalmente para operación.</span></div><div class="road-type"><b>Mantenimiento</b><span>Bacheo, señalización, limpieza y conservación cotidiana.</span></div><div class="road-type"><b>Rehabilitación</b><span>Recuperación estructural o funcional de una calzada ya existente.</span></div><div class="road-type"><b>Obra nueva</b><span>Infraestructura inexistente o ampliación estructural relevante. Total Etapa III: <span class="road-sd">s/d</span>.</span></div></div>
      </section>

      <section class="road-card">
        <div class="road-head"><div><span class="road-kicker">Definición jurídica</span><h3>¿La ruta se privatiza?</h3></div></div>
        <div class="road-legal"><span class="icon">🔑</span><div><h4>Se concesiona el uso y la explotación; no se documentó una venta de la ruta.</h4><p>La Ley 17.520 permite otorgar por un plazo la construcción, conservación o explotación de obras e infraestructuras públicas mediante tarifas o peajes. La concesión no transforma por sí sola el corredor en propiedad privada.</p></div></div>
        <div class="road-plain"><b>En criollo:</b> la empresa recibe temporalmente las llaves para operar y hacer las obras exigidas. La ruta sigue siendo infraestructura pública y el contrato debe decir qué hace, cuánto cobra, qué riesgos asume y cómo vuelve al Estado.</div>
      </section>

      <section class="road-card">
        <div class="road-head"><div><span class="road-kicker">Panel 2 · quién paga</span><h3>Si el Estado deja de pagar una ruta, ¿la ruta se volvió gratis?</h3><p class="road-sub"><b>No.</b> Cambió la forma de financiamiento y la distribución del costo.</p></div></div>
        <div class="road-flow"><div class="road-flow-model"><h4>🏛️ Obra pública presupuestaria</h4><div class="road-flow-steps"><div class="road-step">Contribuyentes / deuda</div><div class="road-down">↓</div><div class="road-step">Estado</div><div class="road-down">↓</div><div class="road-step">Obra y mantenimiento</div></div></div><div class="road-vs">VS</div><div class="road-flow-model"><h4>🎫 Concesión por peaje</h4><div class="road-flow-steps"><div class="road-step">Capital propio + deuda</div><div class="road-down">↓</div><div class="road-step">Concesionario</div><div class="road-down">↓</div><div class="road-step">Obra / operación</div><div class="road-down">↓</div><div class="road-step">Usuarios → peajes → repago</div></div></div></div>
        <div class="road-logistics"><b>Camión → peaje → costo logístico → precio final.</b><br>Parte del costo puede trasladarse según competencia, elasticidad y peso de la logística; no se supone traslado automático del 100%.</div>
      </section>

      <section class="road-card">
        <div class="road-head"><div><span class="road-kicker">Panel 3 · “100% privado”</span><h3>Separar presupuesto, capital y arquitectura financiera</h3></div><span class="road-pill warn">no es una respuesta sí/no</span></div>
        <div class="road-funding"><article><h4>A · Tesoro</h4><ul><li>subsidios directos;</li><li>pagos por disponibilidad;</li><li>garantías o compensaciones;</li><li>ingreso mínimo garantizado.</li></ul></article><article><h4>B · Capital privado</h4><ul><li>aporte del concesionario;</li><li>deuda y valores fiduciarios;</li><li>repago con derechos de cobro;</li><li>riesgo de tránsito contractual.</li></ul></article><article><h4>C · Finanzas públicas</h4><ul><li>BICE organiza;</li><li>BICE Fideicomisos administra;</li><li>puede haber estructura pública sin subsidio;</li><li>cada instrumento debe auditarse.</li></ul></article></div>
        <div class="road-bice"><div class="road-head"><div><h4>Caso verificable · BICE Etapa III, Tramo Cuyo</h4><p class="road-sub">Términos indicativos, preliminares y no vinculantes. No son una regla universal para todos los corredores.</p></div><span class="road-pill">crédito/estructura ≠ subsidio</span></div><div class="road-bice-grid"><div><small>Inversión año 1</small><strong>$30,31 mil M</strong></div><div><small>Emisión máxima</small><strong>$21,22 mil M</strong></div><div><small>Tope financiable</small><strong>70%</strong></div><div><small>Aporte inicial mínimo</small><strong>15%</strong></div><div><small>Condición</small><strong>UVA + 2%</strong></div><div><small>Plazo / gracia</small><strong>6 / 1 años</strong></div></div><div class="road-note"><b>Repago:</b> puede afectarse hasta 70% del flujo de derechos de cobro. Que BICE estructure y BICE Fideicomisos sea fiduciario muestra participación institucional pública; no prueba por sí solo un aporte presupuestario ni una bonificación.</div></div>
      </section>

      <section class="road-card">
        <div class="road-head"><div><span class="road-kicker">Panel 4 · geografía económica</span><h3>Una parte pequeña de la red concentra la mayor parte del tránsito</h3></div></div>
        <div class="road-bars"><div class="road-bar-card"><h4>Kilómetros de la Red Vial Nacional</h4><div class="road-bar-track"><div class="road-bar-fill" style="width:20%">≈20%</div></div></div><div class="road-bar-card"><h4>Tránsito que pasa por la RFC</h4><div class="road-bar-track"><div class="road-bar-fill traffic" style="width:80%">≈80%</div></div></div></div>
        <div class="road-grid-2" style="margin-top:11px"><div class="road-mini"><h4>💰 ¿Por qué ahí?</h4>Más tránsito crea una base mayor de peajes y vuelve más financiables operación, mantenimiento y deuda.</div><div class="road-mini"><h4>🗺️ ¿Y el resto?</h4>Una ruta socialmente necesaria pero con poco tránsito puede no cubrir todos los costos sólo con tarifas. Eso no demuestra que todas sean inviables: obliga a analizar corredor por corredor.</div></div>
      </section>

      <section class="road-card">
        <div class="road-head"><div><span class="road-kicker">Mini simulador conceptual</span><h3>¿Puede una ruta financiarse sólo con peajes?</h3><p class="road-sub">Mové el tránsito o la tarifa y mirá cómo cambia la brecha anual.</p></div></div>
        <div class="road-sim"><div class="road-sim-controls"><div class="road-field"><label>Tránsito diario</label><input id="roadTraffic" type="range" min="500" max="50000" step="500" value="12000"><output id="roadTrafficOut">—</output></div><div class="road-field"><label>Tarifa promedio · $</label><input id="roadToll" type="number" min="0" step="100" value="2500"></div><div class="road-field"><label>Longitud · km</label><input id="roadKm" type="number" min="1" step="1" value="330"></div><div class="road-field"><label>Inversión inicial · $ mil M</label><input id="roadCapex" type="number" min="0" step="1" value="30"></div><div class="road-field"><label>Mantenimiento anual · $ mil M</label><input id="roadMaintenance" type="number" min="0" step="0.5" value="8"></div><div class="road-field"><label>Costo financiero anual · %</label><input id="roadFinance" type="number" min="0" max="100" step="0.5" value="12"></div><div class="road-field"><label>Concesión · años</label><input id="roadYears" type="number" min="1" max="40" step="1" value="20"></div><div class="road-field"><label>Margen requerido · %</label><input id="roadMargin" type="number" min="0" max="100" step="1" value="15"></div></div><div class="road-sim-result"><div class="road-result"><small>Ingresos por peaje</small><strong id="roadRevenue">—</strong></div><div class="road-result"><small>Costo anual requerido</small><strong id="roadRequired">—</strong></div><div class="road-result"><small>Brecha</small><strong id="roadGap">—</strong></div><div id="roadVerdict" class="road-sim-verdict">—</div></div></div>
        <div class="road-note"><b>Simulación conceptual:</b> anualiza la inversión con una cuota financiera simple y suma mantenimiento y margen. No incorpora inflación, crecimiento del tránsito, evasión, impuestos, reinversiones, obras escalonadas ni reglas contractuales.</div>
      </section>

      <section class="road-card">
        <div class="road-head"><div><span class="road-kicker">Panel 5 · presupuesto</span><h3>¿Qué pasó con la inversión pública desde 2023?</h3><p class="road-sub">Índice real encadenado de inversión pública nacional total. No se presenta como inversión vial.</p></div><span class="road-pill bad">cobertura nacional total ≠ rutas</span></div>
        <div class="road-chart-scroll"><div id="roadInvestmentChart" class="road-chart small"></div></div>
        <div class="road-plain"><b>2026 no se empalma:</b> OPC informó para enero–mayo una caída real interanual de 34,2% en inversión real directa y de 30,9% en asignaciones para obras viales de DNV. Es otra ventana y otra cobertura, por eso se muestra como nota, no como una cuarta barra.</div>
      </section>

      <section class="road-card">
        <div class="road-head"><div><span class="road-kicker">Paneles 6 y 7 · obra y resultado</span><h3>Mantener no es rehabilitar; concesionar tampoco demuestra calidad</h3></div></div>
        <div class="road-definitions"><div class="road-def"><b>🧹 Mantenimiento rutinario</b><span>Bacheo, señalización, limpieza y conservación básica para sostener transitabilidad.</span></div><div class="road-def"><b>🧱 Rehabilitación</b><span>Intervención mayor para recuperar estructura, rugosidad y capacidad de la calzada existente.</span></div><div class="road-def"><b>🆕 Obra nueva</b><span>Nueva infraestructura o ampliación estructural relevante. No se imputa por la mera longitud concesionada.</span></div></div>
        <div class="road-grid-3" style="margin-top:11px"><div class="road-mini"><h4>Km evaluados hoy</h4><strong class="road-sd">s/d nacional homogéneo</strong><br>Vialidad publicó evaluaciones de base por corredor, no una medición nacional actual comparable hallada.</div><div class="road-mini"><h4>Bueno / regular / malo</h4><strong class="road-sd">s/d comparable</strong><br>No se mezclan informes parciales ni estimaciones externas con una medición oficial nacional.</div><div class="road-mini"><h4>Qué deberá actualizarse</h4>IRI/Índice de Estado, baches, señalización, accidentes, tiempo de viaje y cumplimiento de niveles de servicio.</div></div>
      </section>

      <section class="road-card">
        <div class="road-head"><div><span class="road-kicker">Paneles 8 y 9 · eficiencia</span><h3>Más privado no es automáticamente más eficiente; más público tampoco</h3></div></div>
        <div class="road-grid-3" style="margin-top:12px"><div class="road-mini"><h4>📏 Resultado físico</h4>calidad, seguridad, km rehabilitados, obras terminadas y tiempo de viaje.</div><div class="road-mini"><h4>💸 Costo</h4>costo/km, peaje, financiamiento, mantenimiento, renegociaciones y rescates.</div><div class="road-mini"><h4>📋 Contrato</h4>competencia, sanciones, actualizaciones, riesgo de tránsito y control estatal.</div></div>
        <div class="road-cost"><div class="road-formula"><h4>Costo fiscal</h4><code>gasto presupuestario
+ subsidios
+ garantías ejecutadas
+ aportes públicos</code></div><div class="road-formula"><h4>Costo social aproximado</h4><code>impuestos destinados
+ peajes pagados
+ subsidios y financiamiento
+ costos logísticos
+ rescates / renegociaciones</code></div></div>
        <div class="road-plain"><b>Regla:</b> que el Tesoro gaste menos no prueba que el país gaste menos. Tampoco se suman estas piezas automáticamente: primero hay que hacerlas comparables y evitar doble conteo.</div>
      </section>

      <section class="road-card">
        <div class="road-head"><div><span class="road-kicker">Panel 10 · monitor vivo</span><h3>Seguimiento corredor por corredor</h3><p class="road-sub">Los campos no publicados quedan como <b>s/d</b>. Elegí una etapa para filtrar.</p></div></div>
        <div class="road-filter" id="roadStageFilter"><button class="active" data-stage="all">Todos</button><button data-stage="I">Etapa I</button><button data-stage="II-A">II-A</button><button data-stage="II-B">II-B</button><button data-stage="III">III</button></div>
        <div id="roadTracker" class="road-table-wrap"></div>
      </section>

      <section class="road-card">
        <div class="road-head"><div><span class="road-kicker">Antecedente y riesgos</span><h3>Argentina ya intentó algo parecido</h3></div></div>
        <div class="road-kpis"><div class="road-kpi"><small>PPP viales 2018</small><strong>6 contratos</strong><span>corredores A, B, C, E, F y Sur</span></div><div class="road-kpi pink"><small>TPI requeridos al adjudicar</small><strong>USD 9,97 B</strong><span>total auditado por AGN</span></div><div class="road-kpi gold"><small>Última extinción</small><strong>15/12/2020</strong><span>todos cerrados dentro del período auditado</span></div><div class="road-kpi"><small>Aporte contingente estimado</small><strong>USD 8,84 B</strong><span>escenario citado por AGN</span></div></div>
        <div class="road-timeline"><div class="road-time"><b>2018</b><span>Se adjudican seis PPP viales.</span></div><div class="road-time"><b>2020</b><span>Se extinguen los contratos.</span></div><div class="road-time"><b>2024–25</b><span>Cae fuerte la inversión pública nacional.</span></div><div class="road-time"><b>2026</b><span>Etapas I y II-A avanzan; II-B y III siguen licitándose.</span></div><div class="road-time"><b>Futuro</b><span>Controlar calidad, costo total y cumplimiento.</span></div></div>
        <div class="road-method" style="margin-top:11px"><details><summary>▸ Riesgos típicos de una concesión vial</summary><div>El Banco Mundial destaca riesgo de tránsito e ingresos, construcción, costos de operación, financiamiento, actualización tarifaria, cambios regulatorios y renegociaciones. La AGN señaló en las PPP argentinas descalce entre ingresos en pesos y compromisos en dólares, dificultad de financiamiento y atrasos de obra. El antecedente no demuestra que el modelo actual vaya a fracasar: muestra qué variables vigilar.</div></details></div>
      </section>

      <section class="road-card road-method">
        <div class="road-head"><div><span class="road-kicker">FAQ</span><h3>Preguntas rápidas</h3></div></div>
        <div class="road-faq"><details open><summary>¿Milei privatizó las rutas?</summary><div>No en el sentido de vender la propiedad de cada corredor. El esquema concede temporalmente explotación, mantenimiento y obras de infraestructura pública. Sí forma parte del proceso de privatización de Corredores Viales S.A., que es una empresa, no la propiedad física de toda la red.</div></details><details><summary>¿Se construyeron 3.900 km nuevos?</summary><div>No. Son 3.920,21 km de corredores existentes incluidos en Etapa III. La suma homogénea de obra nueva estricta no está publicada: figura <b>s/d</b>.</div></details><details><summary>¿La inversión es 100% privada?</summary><div>La ausencia declarada de subsidio directo no resuelve todo. Deben separarse capital del concesionario, deuda colocada a inversores, arquitectura pública de BICE/BICE Fideicomisos, garantías y repago con peajes.</div></details><details><summary>¿Entonces la ruta no la paga el Estado?</summary><div>Puede no haber un pago presupuestario directo, pero la ruta se financia con peajes y esos costos pueden incidir parcialmente en logística y precios. Además, el Estado regula, controla y puede retener riesgos definidos por contrato.</div></details><details><summary>¿El privado corre todo el riesgo?</summary><div>Depende del contrato. Hay que revisar tráfico, actualización tarifaria, fuerza mayor, garantías, equilibrio económico-financiero y mecanismos de renegociación.</div></details><details><summary>¿Una concesión privada siempre es más barata?</summary><div>No puede afirmarse antes de comparar costo total, calidad, tarifa, financiamiento, sanciones, renegociaciones y resultados.</div></details><details><summary>¿Puede toda la red financiarse con peajes?</summary><div>No necesariamente. Las rutas de baja demanda pueden necesitar otras fuentes si el flujo de usuarios no cubre inversión, mantenimiento y financiamiento.</div></details><details><summary>¿La obra pública era gratis?</summary><div>No. Se pagaba con impuestos, deuda y otros recursos. La pregunta útil es quién paga, cuánto y qué infraestructura recibe.</div></details></div>
      </section>

      <section class="road-final">
        <span class="road-kicker">Pregunta síntesis</span><h3>¿Obra pública o concesión privada?</h3><p><b>No existe una respuesta universal.</b> Una concesión puede funcionar cuando hay tránsito, competencia, tarifas razonables, riesgo bien asignado y control efectivo. La obra pública puede ser necesaria cuando el valor social es alto pero la rentabilidad comercial o el tránsito son bajos.</p><div class="road-plain"><b>La pregunta que queda:</b> para cada corredor, ¿qué esquema produjo mejor infraestructura, a qué costo total y quién terminó pagando ese costo?</div>
        <div class="road-links"><button class="road-link" onclick="activateTab('tab-investment')">→ Ver Inversión</button><button class="road-link" onclick="activateTab('tab-debt-public')">→ Ver Deuda</button><button class="road-link" onclick="activateTab('tab-growth')">→ Ver Crecimiento</button><button class="road-link" onclick="activateTab('tab-rates')">→ Ver Inflación</button><button class="road-link" onclick="activateTab('tab-consumption')">→ Ver Consumo</button><button class="road-link" onclick="activateTab('tab-casta')">→ Ver La casta</button></div>
      </section>

      <section class="road-card road-method">
        <div class="road-head"><div><h3>Fuentes y metodología</h3><p class="road-sub">Cada cifra central enlaza a una fuente oficial o institucional.</p></div></div>
        <details><summary>▸ Cómo construimos este tab</summary><div>Se separan propiedad, gestión y financiamiento; km concesionados, mantenimiento, rehabilitación y obra nueva; gasto fiscal y costo social; subsidio, crédito y garantía. No se comparan series presupuestarias con coberturas distintas ni se atribuye causalidad automática a una presidencia. La eficiencia sólo podrá evaluarse con resultados posteriores.</div></details>
        <div class="road-sources"><div class="road-source"><a href="https://www.argentina.gob.ar/transporte/vialidad-nacional/red-federal-de-concesiones" target="_blank" rel="noopener">Vialidad · Red Federal de Concesiones</a><br>tramos, rutas y km.</div><div class="road-source"><a href="https://www.argentina.gob.ar/normativa/nacional/ley-17520-16942/actualizacion" target="_blank" rel="noopener">Ley 17.520 actualizada</a><br>marco de concesión por peaje.</div><div class="road-source"><a href="https://www.bice.com.ar/institucional/mas-informacion/fideicomiso-financiero-red-federal-de-concesiones-etapa-iii/" target="_blank" rel="noopener">BICE · Fideicomiso Etapa III</a><br>términos indicativos por corredor.</div><div class="road-source"><a href="https://opc.gob.ar/ejecucion-presupuestaria/ejecucion-mensual-base-devengado/analisis-de-la-ejecucion-presupuestaria-de-la-inversion-publica-2025/" target="_blank" rel="noopener">OPC · inversión pública 2025</a><br>ejecución real nacional.</div><div class="road-source"><a href="https://www.agn.gob.ar/informes/Informe-109-2026" target="_blank" rel="noopener">AGN · PPP viales 2018–2020</a><br>auditoría aprobada en 2026.</div><div class="road-source"><a href="https://ppp.worldbank.org/library/toll-roads-ppps-identifying-mitigating-and-managing-traffic-risk" target="_blank" rel="noopener">Banco Mundial · riesgo de tránsito</a><br>marco comparado.</div></div>
        <div class="road-links"><button class="road-link" onclick="downloadRoadData('json')">Descargar datos JSON</button><button class="road-link" onclick="downloadRoadData('csv')">Descargar corredores CSV</button><a class="road-link" id="roadAuditLink" href="#" target="_blank">Abrir auditoría</a></div>
      </section>
    </div>
  </section>
"""


SCRIPT_TEMPLATE = r"""
<script id="rutas-publico-privado-script-v139">
const ROAD_DATA=__ROAD_DATA__;
const ROAD_DOWNLOADS=__ROAD_DOWNLOADS__;
let roadRendered=false,roadStage='all';
const ROAD_CONFIG={responsive:true,displaylogo:false,scrollZoom:false,modeBarButtonsToRemove:['lasso2d','select2d']};
function roadFmt(v,d=1){return v==null||!Number.isFinite(Number(v))?'s/d':Number(v).toLocaleString('es-AR',{minimumFractionDigits:d,maximumFractionDigits:d})}
function roadSigned(v,d=1){return v==null?'s/d':`${v>=0?'+':'−'}${roadFmt(Math.abs(v),d)}`}
function roadBillions(v){return `$ ${roadFmt(v,2)} mil M`}
function roadBaseLayout(title){return{title:{text:title,font:{size:13,color:'#5d4169'}},paper_bgcolor:'rgba(0,0,0,0)',plot_bgcolor:'rgba(255,255,255,.72)',font:{family:'Nunito,Arial,sans-serif',color:'#654f6c',size:10},margin:{l:60,r:24,t:62,b:72},hoverlabel:{bgcolor:'#fff8fc',bordercolor:'#d8b7ca',font:{size:10}},xaxis:{gridcolor:'#eee5f2',automargin:true},yaxis:{gridcolor:'#eadff0',automargin:true}}
}
function renderRoadCorridors(){const rows=ROAD_DATA.stage3.corridors,layout=roadBaseLayout('Etapa III · kilómetros de corredores existentes');layout.xaxis={title:'kilómetros concesionados',gridcolor:'#eee5f2'};layout.yaxis={automargin:true,categoryorder:'total ascending'};layout.margin={l:120,r:25,t:60,b:55};Plotly.react('roadCorridorChart',[{type:'bar',orientation:'h',y:rows.map(r=>r.corridor),x:rows.map(r=>r.km),customdata:rows.map(r=>[r.routes]),marker:{color:rows.map((_,i)=>['#8765ad','#a676bd','#c27daa','#d4839f','#df927b','#d9aa66','#8fbf9e','#66a98d'][i])},text:rows.map(r=>`${roadFmt(r.km,2)} km`),textposition:'outside',cliponaxis:false,hovertemplate:'<b>%{y}</b><br>%{x:.2f} km<br>%{customdata[0]}<br><b>No equivale a km de obra nueva.</b><extra></extra>'}],layout,ROAD_CONFIG)}
function roadInvestmentSeries(){let prev=100;return ROAD_DATA.public_investment.map((r,i)=>{if(i===0)return{...r,index:100};prev=prev*(1+r.real_change/100);return{...r,index:prev}})}
function renderRoadInvestment(){const rows=roadInvestmentSeries(),layout=roadBaseLayout('Inversión pública nacional total · índice real 2023=100');layout.yaxis={title:'índice real',range:[0,110],gridcolor:'#eadff0'};layout.xaxis={type:'category'};layout.annotations=[{xref:'paper',yref:'paper',x:.98,y:.95,xanchor:'right',text:'2024: −75,1% real<br>2025: −27,0% real',showarrow:false,align:'right',bgcolor:'rgba(255,255,255,.9)',bordercolor:'#d7c8e0',borderpad:5,font:{size:9,color:'#654f6c'}}];Plotly.react('roadInvestmentChart',[{type:'bar',x:rows.map(r=>r.year),y:rows.map(r=>r.index),marker:{color:['#9e7abb','#cf6f91','#dc9875']},text:rows.map(r=>roadFmt(r.index)),textposition:'outside',hovertemplate:'<b>%{x}</b><br>índice real: %{y:.1f}<br>Cobertura: inversión pública nacional total<extra></extra>'}],layout,ROAD_CONFIG)}
function roadCell(v){return v==null||v===''?'<span class="road-sd">s/d</span>':v}
function renderRoadTracker(){const rows=ROAD_DATA.corridors.filter(r=>roadStage==='all'||r.stage===roadStage);document.getElementById('roadTracker').innerHTML=`<table class="road-table"><thead><tr><th>Etapa</th><th>Corredor / rutas</th><th>Km concesionados</th><th>Estado</th><th>Adjudicataria</th><th>Inicio</th><th>Duración</th><th>Tarifa inicial</th><th>Inversión comprometida</th><th>Km obra nueva</th><th>Financiamiento público</th><th>Fuente</th></tr></thead><tbody>${rows.map(r=>`<tr><td><b>${r.stage}</b></td><td><b>${r.corridor}</b><br><small>${r.routes}</small></td><td class="num">${roadFmt(r.km,2)}</td><td>${r.status}</td><td>${roadCell(r.company)}</td><td>${roadCell(r.start_date)}</td><td>${r.duration_years?`${r.duration_years} años`:roadCell(null)}</td><td>${roadCell(r.tariff)}</td><td>${roadCell(r.investment_committed)}</td><td>${roadCell(r.new_road_km)}</td><td>${roadCell(r.financing_bice)}</td><td><a href="${r.source}" target="_blank" rel="noopener">abrir</a></td></tr>`).join('')}</tbody></table>`}
function calcRoadSimulator(){const traffic=+document.getElementById('roadTraffic').value,toll=+document.getElementById('roadToll').value,capex=+document.getElementById('roadCapex').value,maintenance=+document.getElementById('roadMaintenance').value,rate=+document.getElementById('roadFinance').value/100,years=Math.max(1,+document.getElementById('roadYears').value),margin=+document.getElementById('roadMargin').value/100;const revenue=traffic*365*toll/1e9,factor=rate===0?1/years:(rate*Math.pow(1+rate,years))/(Math.pow(1+rate,years)-1),annualized=capex*factor,required=(annualized+maintenance)*(1+margin),gap=revenue-required;document.getElementById('roadTrafficOut').textContent=`${roadFmt(traffic,0)} vehículos/día`;document.getElementById('roadRevenue').textContent=roadBillions(revenue);document.getElementById('roadRequired').textContent=roadBillions(required);document.getElementById('roadGap').textContent=`${gap>=0?'+':'−'} ${roadBillions(Math.abs(gap))}`;const verdict=document.getElementById('roadVerdict');verdict.className=`road-sim-verdict ${gap>=0?'good':'bad'}`;verdict.innerHTML=gap>=0?`<b>Con estos supuestos, los peajes cubrirían la anualización simplificada.</b><br>Quedaría un margen estimado de ${roadBillions(gap)} por año antes de otros costos.`:`<b>Con estos supuestos, los peajes no alcanzarían.</b><br>Faltarían ${roadBillions(Math.abs(gap))} por año: habría que cambiar tarifa, tránsito, obras, plazo, financiamiento o fuente de fondos.`}
function renderRoad(){document.getElementById('roadStage3Km').textContent=`${roadFmt(ROAD_DATA.stage3.corridors.reduce((a,r)=>a+r.km,0),2)} km`;renderRoadCorridors();renderRoadInvestment();renderRoadTracker();calcRoadSimulator();roadRendered=true}
document.getElementById('roadStageFilter')?.addEventListener('click',e=>{const b=e.target.closest('button[data-stage]');if(!b)return;roadStage=b.dataset.stage;document.querySelectorAll('#roadStageFilter button').forEach(x=>x.classList.toggle('active',x===b));renderRoadTracker()});
['roadTraffic','roadToll','roadKm','roadCapex','roadMaintenance','roadFinance','roadYears','roadMargin'].forEach(id=>document.getElementById(id)?.addEventListener('input',calcRoadSimulator));
function downloadRoadData(kind){const item=ROAD_DOWNLOADS[kind];if(!item)return;const blob=new Blob(['\ufeff'+item.content],{type:item.type}),a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download=item.filename;document.body.appendChild(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(a.href),800)}
function roadProjectAsset(name){const inVersion=/\/data\/dashboard_/i.test(location.pathname);return new URL((inVersion?'derivados/rutas_publico_privado/':'data/derivados/rutas_publico_privado/')+name,location.href).href}
document.getElementById('roadAuditLink')?.setAttribute('href',roadProjectAsset('AUDITORIA_RUTAS_PUBLICO_PRIVADO.md'));
document.querySelector('[data-tab="tab-roads"]')?.addEventListener('click',()=>requestAnimationFrame(renderRoad));
window.addEventListener('resize',()=>{if(!roadRendered)return;['roadCorridorChart','roadInvestmentChart'].forEach(id=>{const el=document.getElementById(id);if(el&&window.Plotly)Plotly.Plots.resize(el)})});
</script>
"""


def derive_and_write() -> dict:
    stage3_total = sum(row["km"] for row in DATA["stage3"]["corridors"])
    investment = []
    previous = 100.0
    for index, row in enumerate(DATA["public_investment"]):
        current = dict(row)
        if index:
            previous *= 1 + row["real_change"] / 100
            current["index"] = previous
        investment.append(current)
    export = dict(DATA)
    export["stage3"]["total_km_derived"] = stage3_total
    export["public_investment"] = investment
    data_path = OUT_DIR / "rutas_publico_privado_data.json"
    data_path.write_text(json.dumps(export, ensure_ascii=False, indent=2), encoding="utf-8")
    csv_path = OUT_DIR / "rutas_publico_privado_corredores.csv"
    fields = list(CORRIDORS[0].keys())
    with csv_path.open("w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        writer.writerows(CORRIDORS)
    tests = {
        "stage3_total_km": stage3_total,
        "stage3_total_expected": 3920.21,
        "stage3_total_ok": abs(stage3_total - 3920.21) < 0.001,
        "stage3_corridors": len(DATA["stage3"]["corridors"]),
        "stage3_status_is_not_awarded": all(row["company"] is None for row in CORRIDORS if row["stage"] == "III"),
        "new_road_km_is_missing_not_zero": all(row["new_road_km"] is None for row in CORRIDORS),
        "investment_index_2024": investment[1]["index"],
        "investment_index_2025": investment[2]["index"],
        "bice_cuyo_max_share_ok": DATA["bice_cuyo"]["max_share"] == 70,
        "all_passed": True,
    }
    tests["all_passed"] = all([tests["stage3_total_ok"], tests["stage3_corridors"] == 8, tests["stage3_status_is_not_awarded"], tests["new_road_km_is_missing_not_zero"], tests["bice_cuyo_max_share_ok"]])
    (OUT_DIR / "TESTS_RUTAS_PUBLICO_PRIVADO.json").write_text(json.dumps(tests, ensure_ascii=False, indent=2), encoding="utf-8")
    audit = f"""# Auditoría — Rutas · ¿Público o privado?

**Corte editorial:** 21/08/2026

## Controles numéricos

- Etapa III: 8 tramos; suma derivada de tabla oficial: **{stage3_total:.2f} km**.
- La longitud se etiqueta como `km concesionados`, nunca como `km construidos`.
- `km de obra nueva` permanece `s/d`; no se imputa cero.
- Último estado oficial hallado para Etapa III: apertura de ofertas económicas del 22/07/2026; 21 oferentes y 48 ofertas. La adjudicación final figuraba pendiente.
- Inversión pública total, índice real 2023=100: 2024 **{investment[1]['index']:.2f}**; 2025 **{investment[2]['index']:.2f}**. Son encadenamientos de variaciones OPC y no se presentan como inversión vial.
- Ene–may 2026 se mantiene como nota separada: IRD −34,2% real a/a y obras viales DNV −30,9% real a/a.
- BICE Cuyo se rotula como ejemplo indicativo, preliminar y no vinculante.

## Reglas semánticas

1. Concesión no equivale a venta de la ruta.
2. Ausencia de subsidio directo no equivale a ausencia del Estado en la arquitectura financiera.
3. Crédito, garantía, fideicomiso y subsidio no son sinónimos.
4. Gasto fiscal y costo social no se suman sin homogeneizar y evitar doble conteo.
5. No se compara una medición parcial de calzada con una serie nacional inexistente.
6. El simulador es conceptual y no reproduce un contrato real.

## Fuentes

""" + "\n".join(f"- {name}: {url}" for name, url in SOURCES.items()) + "\n"
    (OUT_DIR / "AUDITORIA_RUTAS_PUBLICO_PRIVADO.md").write_text(audit, encoding="utf-8")
    return {"json": data_path, "csv": csv_path, "tests": tests}


def build() -> None:
    derived = derive_and_write()
    html = SOURCE_HTML.read_text(encoding="utf-8")
    nav_anchor = '    <button class="tab-btn" data-tab="tab-debt-public">Deuda pública</button>'
    section_anchor = '  <section id="tab-debt-public" class="tab-panel">'
    if nav_anchor not in html or section_anchor not in html:
        raise RuntimeError("No se encontraron los anclajes esperados en la versión fuente")
    html = html.replace(nav_anchor, '    <button class="tab-btn" data-tab="tab-roads">Rutas · ¿Público o privado?</button>\n' + nav_anchor, 1)
    html = html.replace(section_anchor, SECTION + "\n" + section_anchor, 1)
    html = html.replace("</head>", CSS + "\n</head>", 1)
    downloads = {
        "json": {"filename": derived["json"].name, "type": "application/json;charset=utf-8", "content": derived["json"].read_text(encoding="utf-8")},
        "csv": {"filename": derived["csv"].name, "type": "text/csv;charset=utf-8", "content": derived["csv"].read_text(encoding="utf-8-sig")},
    }
    script = SCRIPT_TEMPLATE.replace("__ROAD_DATA__", json.dumps(DATA, ensure_ascii=False, separators=(",", ":"))).replace("__ROAD_DOWNLOADS__", json.dumps(downloads, ensure_ascii=False, separators=(",", ":")))
    html = html.replace("</body>", script + "\n</body>", 1)
    OUTPUT_HTML.write_text(html, encoding="utf-8")
    print(f"Built {OUTPUT_HTML.relative_to(ROOT)}")
    print(f"Corridors: {len(CORRIDORS)} · Stage III km: {derived['tests']['stage3_total_km']:.2f} · tests passed: {derived['tests']['all_passed']}")


if __name__ == "__main__":
    build()
