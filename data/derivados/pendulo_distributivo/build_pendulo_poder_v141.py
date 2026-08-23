from __future__ import annotations

import csv
import hashlib
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
SOURCE_HTML = ROOT / "data" / "dashboard_kawaii_140_vacaciones_turismo.html"
INDEX_HTML = ROOT / "index.html"
OUTPUT_HTML = ROOT / "data" / "dashboard_kawaii_141_pendulo_poder_economico.html"
DERIVED_DIR = ROOT / "data" / "derivados" / "pendulo_poder_economico"
REGISTRY_JSON = DERIVED_DIR / "metric_registry.json"
OVERLAPS_CSV = DERIVED_DIR / "double_count_matrix.csv"
ASSETS_CSV = DERIVED_DIR / "asset_returns_dec2023.csv"
AUDIT_MD = DERIVED_DIR / "AUDITORIA_PENDULO_PODER_ECONOMICO.md"
TESTS_JSON = DERIVED_DIR / "TESTS_PENDULO_PODER_ECONOMICO.json"


METRICS = [
    {
        "id": "production_cgi_pendulum",
        "layer": "Producción",
        "title": "Péndulo CGI",
        "measure_type": "RATIO",
        "unit": "puntos del índice",
        "frequency": "anual histórica / trimestral moderna",
        "period": "1993–2007 y 2016–2026-T1",
        "source_grade": "A",
        "transformation": "derivado",
        "actors": "trabajo asalariado + ingreso mixto ↔ excedente bruto",
        "economic_flow_id": "cgi_primary_income_distribution",
        "status": "disponible",
        "do_not_sum_with": ["financial_bank_window_delta", "financial_fintech_window_delta", "financial_pf_window_delta"],
        "note": "Cuenta primaria; no incorpora intereses, alquileres, impuestos ni activos.",
    },
    {
        "id": "financial_bank_window_delta",
        "layer": "Finanzas",
        "title": "Crédito bancario · diferencial post-shock vs espejo",
        "measure_type": "CONTRAFACTUAL",
        "unit": "pesos constantes de julio de 2026",
        "frequency": "acumulado de dos ventanas de 32 meses",
        "period": "abr-2021–nov-2023 / dic-2023–jul-2026",
        "source_grade": "B",
        "transformation": "derivado sólido",
        "actors": "hogares deudores ↔ bancos",
        "economic_flow_id": "household_bank_credit_rate_gap",
        "status": "disponible",
        "do_not_sum_with": ["bank_financial_margin", "bank_profitability"],
        "note": "Impacto estimado contra una norma histórica; no son intereses efectivamente cobrados ni ganancia bancaria.",
    },
    {
        "id": "financial_fintech_window_delta",
        "layer": "Finanzas",
        "title": "Fintech · diferencial post-shock vs espejo",
        "measure_type": "CONTRAFACTUAL",
        "unit": "pesos constantes de julio de 2026",
        "frequency": "acumulado de dos ventanas de 32 meses",
        "period": "abr-2021–nov-2023 / dic-2023–jul-2026",
        "source_grade": "B",
        "transformation": "reconstrucción",
        "actors": "hogares deudores ↔ PNFC/fintech",
        "economic_flow_id": "household_fintech_credit_rate_gap",
        "status": "disponible con estimación",
        "do_not_sum_with": ["fintech_interest_income", "fintech_profitability"],
        "note": "Cinco meses prolongan último stock y TNA oficiales; no es CFT ni ganancia de las fintech.",
    },
    {
        "id": "financial_pf_window_delta",
        "layer": "Finanzas",
        "title": "Plazo fijo · diferencial post-shock vs espejo",
        "measure_type": "CONTRAFACTUAL",
        "unit": "pesos constantes de julio de 2026",
        "frequency": "acumulado de dos ventanas de 32 meses",
        "period": "abr-2021–nov-2023 / dic-2023–jul-2026",
        "source_grade": "B",
        "transformation": "derivado sólido",
        "actors": "bancos ↔ hogares ahorristas",
        "economic_flow_id": "household_deposit_rate_gap",
        "status": "disponible",
        "do_not_sum_with": ["bank_funding_cost", "bank_financial_margin"],
        "note": "Rendimiento estimado contra la norma histórica; no representa a un hogar promedio.",
    },
    {
        "id": "financial_expanded_balance_delta",
        "layer": "Finanzas",
        "title": "Balance ampliado · banco + fintech + plazo fijo",
        "measure_type": "CONTRAFACTUAL",
        "unit": "pesos constantes de julio de 2026",
        "frequency": "diferencial entre ventanas",
        "period": "32 meses por ventana",
        "source_grade": "B",
        "transformation": "agregado derivado",
        "actors": "universos distintos de deudores y ahorristas",
        "economic_flow_id": "retail_credit_saving_balance",
        "status": "disponible",
        "do_not_sum_with": ["financial_bank_window_delta", "financial_fintech_window_delta", "financial_pf_window_delta"],
        "note": "Ya contiene sus tres componentes. No es el impacto de un hogar promedio.",
    },
    {
        "id": "housing_tenure_status",
        "layer": "Vivienda",
        "title": "Condición de tenencia",
        "measure_type": "RATIO",
        "unit": "% de hogares",
        "frequency": "onda EPH",
        "period": "según último dato del tab Vivienda",
        "source_grade": "A",
        "transformation": "observado",
        "actors": "hogares propietarios / inquilinos / otras tenencias",
        "economic_flow_id": "housing_tenure_structure",
        "status": "disponible en tab vinculado",
        "do_not_sum_with": [],
        "note": "Describe tenencia; no mide cuánto se paga de alquiler.",
    },
    {
        "id": "housing_rent_income_burden",
        "layer": "Vivienda",
        "title": "Alquiler / ingreso familiar",
        "measure_type": "RATIO",
        "unit": "% del ingreso familiar",
        "frequency": "pendiente",
        "period": "sin serie contemporánea homogénea",
        "source_grade": "C",
        "transformation": "pendiente",
        "actors": "hogar inquilino ↔ propietario",
        "economic_flow_id": "household_rent_payment",
        "status": "no calculado",
        "do_not_sum_with": ["landlord_rent_income", "engho_housing_spend"],
        "note": "Se deja el hueco visible antes que fabricar una serie.",
    },
    {
        "id": "fiscal_tax_structure",
        "layer": "Fiscal",
        "title": "Estructura de recaudación y gasto",
        "measure_type": "FLUJO",
        "unit": "% del PIB / pesos por período",
        "frequency": "anual o presupuestaria",
        "period": "según cada fuente",
        "source_grade": "A",
        "transformation": "observado agregado",
        "actors": "hogares, empresas y Estado sin incidencia individual",
        "economic_flow_id": "general_government_revenue_spending",
        "status": "disponible en tabs vinculados",
        "do_not_sum_with": ["fiscal_net_household_position"],
        "note": "La recaudación agregada no identifica quién soporta finalmente cada impuesto.",
    },
    {
        "id": "fiscal_tax_expenditure",
        "layer": "Fiscal",
        "title": "Gasto tributario / beneficios fiscales",
        "measure_type": "CONTRAFACTUAL",
        "unit": "pesos o % del PIB estimado",
        "frequency": "anual",
        "period": "según estimación oficial",
        "source_grade": "B",
        "transformation": "contrafactual",
        "actors": "Estado ↔ beneficiarios de tratamientos tributarios",
        "economic_flow_id": "tax_expenditure_counterfactual",
        "status": "disponible en tab vinculado",
        "do_not_sum_with": ["foregone_revenue_scenario", "fiscal_net_household_position"],
        "note": "No equivale automáticamente a dinero cobrable ni a una transferencia ejecutada.",
    },
    {
        "id": "asset_cash_real",
        "layer": "Activos",
        "title": "Efectivo sin remunerar",
        "measure_type": "RENDIMIENTO HIPOTÉTICO",
        "unit": "índice real base dic-2023=100",
        "frequency": "mensual",
        "period": "dic-2023–jul-2026",
        "source_grade": "A",
        "transformation": "escenario",
        "actors": "persona con pesos líquidos",
        "economic_flow_id": "conditional_asset_return_cash",
        "status": "disponible",
        "do_not_sum_with": ["household_net_worth_change"],
        "note": "Mide poder de compra de pesos no invertidos; no riqueza observada.",
    },
    {
        "id": "asset_pf_real",
        "layer": "Activos",
        "title": "Plazo fijo renovado",
        "measure_type": "RENDIMIENTO HIPOTÉTICO",
        "unit": "índice real base dic-2023=100",
        "frequency": "mensual",
        "period": "dic-2023–jul-2026",
        "source_grade": "B",
        "transformation": "escenario compuesto",
        "actors": "persona con capacidad de constituir y renovar depósitos",
        "economic_flow_id": "conditional_asset_return_pf",
        "status": "disponible",
        "do_not_sum_with": ["financial_pf_window_delta", "household_net_worth_change"],
        "note": "Supone renovación mensual al promedio publicado; no es una cuenta observada ni incluye decisiones individuales.",
    },
    {
        "id": "asset_usd_a3500_real",
        "layer": "Activos",
        "title": "Dólar mayorista A3500",
        "measure_type": "RENDIMIENTO HIPOTÉTICO",
        "unit": "índice real base dic-2023=100",
        "frequency": "mensual",
        "period": "dic-2023–jul-2026",
        "source_grade": "A",
        "transformation": "escenario",
        "actors": "persona hipotética expuesta al tipo de cambio de referencia",
        "economic_flow_id": "conditional_asset_return_a3500",
        "status": "disponible",
        "do_not_sum_with": ["household_net_worth_change"],
        "note": "Referencia mayorista; no implica acceso minorista a ese precio.",
    },
    {
        "id": "income_real_salary_reference",
        "layer": "Activos",
        "title": "Salario real · línea de referencia",
        "measure_type": "RATIO",
        "unit": "índice real base dic-2023=100",
        "frequency": "mensual",
        "period": "dic-2023–jun-2026",
        "source_grade": "A",
        "transformation": "derivado",
        "actors": "personas asalariadas",
        "economic_flow_id": "real_salary_reference",
        "status": "disponible",
        "do_not_sum_with": ["asset_cash_real", "asset_pf_real", "asset_usd_a3500_real"],
        "note": "Es ingreso, no activo invertible; aparece sólo como referencia separada.",
    },
]


OVERLAPS = [
    {
        "metric_a": "financial_bank_window_delta",
        "metric_b": "bank_financial_margin",
        "risk": "alto",
        "relationship": "mismo circuito visto desde deudor e intermediario",
        "rule": "no sumar; además las cifras no son contablemente idénticas",
    },
    {
        "metric_a": "financial_pf_window_delta",
        "metric_b": "bank_funding_cost",
        "risk": "alto",
        "relationship": "interés recibido por ahorrista / costo de fondeo",
        "rule": "mostrar como contrapartes, no como beneficios independientes",
    },
    {
        "metric_a": "housing_rent_income_burden",
        "metric_b": "landlord_rent_income",
        "risk": "alto",
        "relationship": "pago del inquilino / ingreso del propietario",
        "rule": "un mismo flujo cambia de perspectiva",
    },
    {
        "metric_a": "engho_consumption_with_tax",
        "metric_b": "household_indirect_taxes",
        "risk": "alto",
        "relationship": "IVA y otros impuestos ya incluidos en el precio de consumo",
        "rule": "no volver a restarlos en el waterfall salvo apertura neta compatible",
    },
    {
        "metric_a": "fiscal_tax_expenditure",
        "metric_b": "foregone_revenue_scenario",
        "risk": "alto",
        "relationship": "dos nombres para el mismo contrafactual tributario",
        "rule": "usar una sola medición por escenario",
    },
    {
        "metric_a": "asset_pf_real",
        "metric_b": "financial_pf_window_delta",
        "risk": "medio",
        "relationship": "rendimiento acumulado vs desviación contra norma histórica",
        "rule": "pueden convivir como preguntas distintas, nunca sumarse",
    },
    {
        "metric_a": "asset_usd_a3500_real",
        "metric_b": "household_net_worth_change",
        "risk": "alto",
        "relationship": "retorno del activo vs patrimonio efectivamente poseído",
        "rule": "no inferir riqueza sin cantidades y propiedad",
    },
]


POWER_CSS = r'''
<style id="pendulo-poder-v141">
/* v141 · Péndulo del poder económico · capas auditables */
#tab-pendulo .pend-power-hero{position:relative;overflow:hidden;background:linear-gradient(135deg,rgba(255,249,253,.98),rgba(246,253,255,.98) 52%,rgba(250,247,255,.98));border-color:#ceb9df}
#tab-pendulo .pend-power-hero::after{content:'capas';position:absolute;right:-12px;bottom:-34px;font-size:96px;font-weight:950;color:rgba(108,72,126,.045);transform:rotate(-6deg);pointer-events:none}
.pend-power-title{margin:7px 0 5px;color:#563366;font-size:30px;line-height:1.08}.pend-power-lede{max-width:940px;margin:0;color:#6f5875;font-size:12px;line-height:1.6}
.pend-circuit{position:relative;z-index:1;display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:24px;margin-top:17px}.pend-circuit-step{position:relative;padding:14px;border:1px solid #dfd1e7;border-radius:17px;background:rgba(255,255,255,.93)}.pend-circuit-step:not(:last-child)::after{content:'➜';position:absolute;right:-22px;top:50%;transform:translateY(-50%);color:#9d70b0;font-size:18px}.pend-circuit-step small{display:block;font-size:7.7px;font-weight:950;letter-spacing:.05em;text-transform:uppercase;color:#876d8d}.pend-circuit-step b{display:block;margin:5px 0 3px;color:#583966;font-size:12px}.pend-circuit-step span{font-size:9px;line-height:1.45;color:#77647c}
.pend-contract{margin-top:13px;padding:12px 14px;border-left:5px solid #48a07f;border-radius:14px;background:#f5fff9;font-size:10.5px;line-height:1.55;color:#5d6d65}.pend-contract b{color:#286c55}
.pend-layer-nav-wrap{position:sticky;top:6px;z-index:20;padding:8px;border:1px solid #d9c9e3;border-radius:20px;background:rgba(255,252,255,.95);box-shadow:0 8px 20px rgba(74,43,91,.1);backdrop-filter:blur(12px)}
.pend-layer-nav{display:flex;gap:7px;max-width:100%;overflow-x:auto;scrollbar-width:thin;-webkit-overflow-scrolling:touch}.pend-layer-btn{flex:0 0 auto;appearance:none;min-height:38px;border:1px solid #d9cbe2;border-radius:999px;background:#fff;padding:9px 13px;color:#6a4a75;font:inherit;font-size:9.5px;font-weight:950;cursor:pointer;white-space:nowrap}.pend-layer-btn.active{border-color:#805497;background:#f4eafa;color:#52305f;box-shadow:0 4px 10px rgba(94,55,111,.13)}.pend-layer-btn:focus-visible{outline:3px solid rgba(128,84,151,.25);outline-offset:2px}
.pend-layer-panel{display:none}.pend-layer-panel.active{display:block}.pend-layer-stack{display:grid;gap:16px}
.pend-layer-question{margin:13px 0 0;padding:13px 15px;border-left:5px solid #9d6db3;border-radius:14px;background:#fbf7ff;color:#563963;font-size:15px;font-weight:950}.pend-layer-question small{display:block;margin-top:5px;color:#75617a;font-size:9.5px;font-weight:700;line-height:1.5}
.pend-meta-line,.pend-meta-badges{display:flex;flex-wrap:wrap;gap:6px;margin-top:10px}.pend-meta{display:inline-flex;align-items:center;gap:4px;padding:5px 8px;border:1px solid #dbcee4;border-radius:999px;background:#fff;color:#6f5579;font-size:7.8px;font-weight:950;letter-spacing:.035em;text-transform:uppercase}.pend-meta.flow{border-color:#b8dccb;background:#f5fff9;color:#2d795f}.pend-meta.stock{border-color:#bed4e8;background:#f5fbff;color:#366c91}.pend-meta.ratio{border-color:#cfc1e6;background:#faf7ff;color:#65468a}.pend-meta.counter{border-color:#e7c4d2;background:#fff7fa;color:#9b4163}.pend-meta.scenario{border-color:#ead69e;background:#fffdf2;color:#7d641f}.pend-meta.evidence-a{background:#f2fff8;border-color:#a9d5c0;color:#26765b}.pend-meta.evidence-b{background:#f4f9ff;border-color:#b7d2e8;color:#326b90}.pend-meta.evidence-c{background:#fffaf0;border-color:#e6cf9b;color:#80631c}.pend-meta.evidence-d{background:#fff5fa;border-color:#e4b9ca;color:#9c3d63}
.pend-power-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:10px;margin-top:14px}.pend-power-metric{min-width:0;padding:14px;border:1px solid #dfd2e7;border-radius:17px;background:#fff}.pend-power-metric.good{border-color:#b7dccb;background:#f5fff9}.pend-power-metric.bad{border-color:#e6bdcd;background:#fff7fa}.pend-power-metric.neutral{border-color:#d1c1e6;background:#faf8ff}.pend-power-metric small{display:block;color:#836e89;font-size:7.6px;font-weight:950;letter-spacing:.04em;text-transform:uppercase}.pend-power-metric strong{display:block;margin:5px 0 4px;color:#5a3b68;font-size:22px;line-height:1.05}.pend-power-metric.good strong{color:#2d8263}.pend-power-metric.bad strong{color:#aa416a}.pend-power-metric p{margin:0;color:#736078;font-size:9px;line-height:1.45}.pend-power-metric .perspective{display:block;margin-top:8px;padding-top:7px;border-top:1px dashed #dfd3e6;color:#654c6e;font-size:8.5px;line-height:1.4}
.pend-actor-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:10px;margin-top:13px}.pend-actor{padding:14px;border:1px solid #e0d4e7;border-radius:17px;background:#fff}.pend-actor .emoji{font-size:24px}.pend-actor h4{margin:5px 0;color:#5a3b68;font-size:12px}.pend-actor p{margin:0;color:#75627a;font-size:9.5px;line-height:1.5}.pend-actor b{color:#52325f}
.pend-gate{display:grid;grid-template-columns:auto 1fr;gap:12px;align-items:start;margin-top:13px;padding:14px;border:1px solid #e5cf98;border-radius:17px;background:#fffdf2}.pend-gate .icon{font-size:28px}.pend-gate h4{margin:0 0 5px;color:#70591e;font-size:12px}.pend-gate p{margin:0;color:#756842;font-size:9.5px;line-height:1.55}
.pend-asset-chart{width:100%;min-width:720px;height:460px}.pend-asset-summary{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:9px;margin-top:12px}.pend-asset-kpi{padding:12px;border:1px solid #dfd3e7;border-radius:15px;background:#fff}.pend-asset-kpi small{display:block;color:#826e88;font-size:7.5px;font-weight:950;text-transform:uppercase}.pend-asset-kpi strong{display:block;margin:4px 0;color:#5a3b67;font-size:18px}.pend-asset-kpi span{color:#75627a;font-size:8.6px;line-height:1.4}.pend-asset-pending{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:9px;margin-top:12px}.pend-asset-pending div{padding:11px;border:1px dashed #d9cbe2;border-radius:14px;background:#fdfbff;color:#78657d;font-size:9px;line-height:1.45}.pend-asset-pending b{display:block;color:#5f436b;margin-bottom:3px}
.pend-risk-table{max-width:100%;overflow:auto;margin-top:12px;border:1px solid #e1d5e8;border-radius:16px;background:#fff}.pend-risk-table table{width:100%;min-width:780px;border-collapse:collapse;font-size:8.8px}.pend-risk-table th,.pend-risk-table td{padding:9px 10px;border-bottom:1px solid #eee5f2;text-align:left;vertical-align:top}.pend-risk-table th{background:#f7f1fb;color:#70517d;font-size:7.8px;text-transform:uppercase}.pend-risk-table tr:last-child td{border-bottom:0}.pend-risk-high{color:#a23f65;font-weight:950}.pend-risk-medium{color:#8a6a23;font-weight:950}
.pend-evidence-legend{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:9px;margin-top:12px}.pend-evidence{padding:12px;border:1px solid #ded2e6;border-radius:15px;background:#fff}.pend-evidence b{display:block;margin-bottom:4px;color:#5c3d69;font-size:11px}.pend-evidence span{color:#756179;font-size:8.8px;line-height:1.45}
.pend-disabled-lab{margin-top:13px;padding:16px;border:2px solid #d6c5e2;border-radius:18px;background:linear-gradient(135deg,#fbf8ff,#fffdf4)}.pend-disabled-lab h4{margin:0 0 7px;color:#5c3c69;font-size:14px}.pend-disabled-lab p{margin:0;color:#725d78;font-size:10px;line-height:1.55}.pend-lab-status{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:8px;margin-top:11px}.pend-lab-status div{padding:10px;border:1px solid #e0d4e7;border-radius:13px;background:#fff;text-align:center}.pend-lab-status b{display:block;color:#5c3d68;font-size:9px}.pend-lab-status span{display:block;margin-top:3px;font-size:8px;color:#86728b}.pend-lab-status .blocked{border-color:#e6c4d2;background:#fff7fa}.pend-lab-status .ready{border-color:#b9dccb;background:#f5fff9}
@media(max-width:1050px){.pend-circuit,.pend-power-grid,.pend-asset-summary{grid-template-columns:repeat(2,minmax(0,1fr))}.pend-actor-grid,.pend-asset-pending{grid-template-columns:1fr}.pend-evidence-legend{grid-template-columns:repeat(2,minmax(0,1fr))}.pend-lab-status{grid-template-columns:repeat(3,minmax(0,1fr))}}
@media(max-width:760px){.pend-power-title{font-size:25px}.pend-circuit{grid-template-columns:1fr;gap:22px}.pend-circuit-step:not(:last-child)::after{content:'⬇';right:auto;left:50%;top:auto;bottom:-20px;transform:translateX(-50%)}.pend-layer-nav-wrap{top:4px;border-radius:16px}.pend-layer-btn{min-height:42px;padding:10px 13px}.pend-power-grid,.pend-asset-summary{grid-template-columns:1fr 1fr}.pend-asset-chart{min-width:680px;height:420px}.pend-evidence-legend{grid-template-columns:1fr 1fr}.pend-lab-status{grid-template-columns:1fr 1fr}}
@media(max-width:430px){.pend-power-grid,.pend-asset-summary,.pend-evidence-legend,.pend-lab-status{grid-template-columns:1fr}.pend-power-title{font-size:23px}.pend-power-lede{font-size:10.5px}.pend-asset-chart{min-width:640px}.pend-gate{grid-template-columns:1fr}.pend-layer-nav-wrap{margin-left:-2px;margin-right:-2px}}
</style>
'''


def extract_json_const(text: str, name: str) -> dict:
    pattern = re.compile(rf"^const {re.escape(name)}\s*=\s*(\{{.*\}});\s*$", re.MULTILINE)
    match = pattern.search(text)
    if not match:
        raise RuntimeError(f"No se encontró el objeto JS {name}")
    return json.loads(match.group(1))


def build_asset_rows(text: str) -> list[dict]:
    bcra = extract_json_const(text, "bcraData")
    salaries = extract_json_const(text, "powerTotalAllOfficial")
    with (ROOT / "data" / "derivados" / "tasas_pinza_hogar_auditada.csv").open(encoding="utf-8-sig", newline="") as handle:
        rate_rows = list(csv.DictReader(handle))
    rate_rows = [row for row in rate_rows if "2023-12" <= row["fecha"] <= "2026-07"]
    rate_rows.sort(key=lambda row: row["fecha"])
    if not rate_rows or rate_rows[0]["fecha"] != "2023-12":
        raise RuntimeError("La serie patrimonial no puede fijar la base dic-2023")

    fx_map = {date[:7]: value for date, value in zip(bcra["fx"]["dates"], bcra["fx"]["level"])}
    salary_map = {date[:7]: value for date, value in zip(salaries["dates"], salaries["yNov"])}
    base_ipc = float(rate_rows[0]["ipc"])
    base_fx = float(fx_map["2023-12"])
    base_salary = float(salary_map["2023-12"])
    pf_index = 100.0
    rows: list[dict] = []
    for index, row in enumerate(rate_rows):
        month = row["fecha"]
        ipc = float(row["ipc"])
        if index > 0:
            pf_index *= 1 + float(row["pf_real"]) / 100
        fx = fx_map.get(month)
        salary = salary_map.get(month)
        rows.append(
            {
                "date": f"{month}-01",
                "cash_real": 100 * base_ipc / ipc,
                "pf_real": pf_index,
                "usd_a3500_real": None if fx is None else 100 * (float(fx) / base_fx) * (base_ipc / ipc),
                "salary_real_reference": None if salary is None else 100 * float(salary) / base_salary,
                "ipc_level": ipc,
                "fx_a3500": fx,
                "pf_real_monthly_pct": float(row["pf_real"]),
            }
        )
    return rows


def measure_badges(*items: tuple[str, str]) -> str:
    return '<div class="pend-meta-line">' + "".join(f'<span class="pend-meta {kind}">{label}</span>' for kind, label in items) + "</div>"


def build_outer_section(production_inner: str) -> str:
    finance_badges = measure_badges(
        ("counter", "contrafactual"),
        ("", "pesos constantes"),
        ("evidence-b", "fuente/derivación B"),
        ("", "actores: deudor · ahorrista · intermediario"),
    )
    housing_badges = measure_badges(("ratio", "ratios"), ("", "EPH / ENGHo"), ("evidence-c", "cobertura desigual"))
    fiscal_badges = measure_badges(("flow", "flujos"), ("counter", "+ contrafactuales"), ("", "macro ≠ incidencia del hogar"))
    asset_badges = measure_badges(("scenario", "rendimiento hipotético"), ("", "base real dic-2023=100"), ("evidence-c", "escenario C"))

    return f'''  <section id="tab-pendulo" class="tab-panel">
    <div class="pend-shell">
      <section class="pend-card pend-power-hero">
        <span class="pend-kicker">Ingreso · finanzas · vivienda · Estado · activos</span>
        <h2 class="pend-power-title">Péndulo del poder económico ♡</h2>
        <p class="pend-power-lede">Una tomografía en capas de cómo se distribuye, se transfiere y se reproduce el poder económico. <b>No es una gran cuenta sumable:</b> cada capa conserva sus actores, unidad, período y nivel de evidencia.</p>
        <div class="pend-circuit" aria-label="Circuito económico conceptual">
          <div class="pend-circuit-step"><small>1 · producción</small><b>Se genera y reparte ingreso</b><span>Trabajo asalariado, ingreso mixto y excedente bruto.</span></div>
          <div class="pend-circuit-step"><small>2 · compromisos</small><b>Se pagan crédito y vivienda</b><span>La posición deudora, ahorrista o inquilina cambia la experiencia.</span></div>
          <div class="pend-circuit-step"><small>3 · Estado</small><b>Recauda y redistribuye</b><span>Impuestos, transferencias, servicios y beneficios no son lo mismo.</span></div>
          <div class="pend-circuit-step"><small>4 · acumulación</small><b>Activos, ahorro y deuda</b><span>Poseer un activo permite capturar su rendimiento; no prueba quién lo poseía.</span></div>
        </div>
        <div class="pend-contract"><b>Contrato de lectura:</b> stocks, flujos, ratios, contrafactuales y rendimientos hipotéticos se rotulan de forma distinta. Si dos métricas miran el mismo flujo desde lados opuestos, no se suman.</div>
      </section>

      <nav class="pend-layer-nav-wrap" aria-label="Capas del Péndulo del poder económico">
        <div class="pend-layer-nav" id="pendPowerLayerNav" role="tablist">
          <button class="pend-layer-btn active" role="tab" aria-selected="true" data-layer="production">A · Producción</button>
          <button class="pend-layer-btn" role="tab" aria-selected="false" data-layer="finance">B · Finanzas</button>
          <button class="pend-layer-btn" role="tab" aria-selected="false" data-layer="housing">C · Vivienda</button>
          <button class="pend-layer-btn" role="tab" aria-selected="false" data-layer="fiscal">D · Fiscal</button>
          <button class="pend-layer-btn" role="tab" aria-selected="false" data-layer="assets">E · Activos</button>
          <button class="pend-layer-btn" role="tab" aria-selected="false" data-layer="lab">F · Laboratorio</button>
        </div>
      </nav>

      <div class="pend-layer-panel active" data-pend-layer-panel="production" role="tabpanel">
        <div class="pend-layer-stack">
{production_inner}
        </div>
      </div>

      <div class="pend-layer-panel" data-pend-layer-panel="finance" role="tabpanel" hidden>
        <div class="pend-layer-stack">
          <section class="pend-card pend-hero">
            <div class="pend-head"><div><span class="pend-kicker">B · Crédito, ahorro e intermediación</span><h2>¿Cuánto te pagan por tener plata y cuánto te cobran por necesitarla?</h2><p class="pend-sub">Resumen vinculado al tab de Tasas e inflación. Conserva la convención auditada: en los saldos, + favorece al hogar y − lo perjudica; en el diferencial, + significa mejora respecto de la ventana espejo.</p></div></div>
            <div class="pend-layer-question">Deudor ↔ ahorrista ↔ intermediario<small>No existe un único eje “hogares vs capital”: cada posición recibe o paga flujos distintos.</small></div>
            {finance_badges}
            <div id="pendPowerFinanceKpis" class="pend-power-grid"></div>
            <div class="pend-reading"><b>Qué significa:</b> el balance ampliado puede mejorar aunque el crédito bancario o fintech empeoren, porque plazo fijo pertenece a otro universo y puede moverse en sentido contrario. <b>No es el resultado de un hogar promedio.</b></div>
            <div class="pend-links"><button class="pend-link" onclick="activateTab('tab-rates')">Abrir Tasas e inflación →</button><button class="pend-link" onclick="activateTab('tab-morosidad')">Abrir Morosidad →</button><button class="pend-link" onclick="activateTab('tab-bcra')">Abrir sistema bancario/BCRA →</button></div>
          </section>
          <section class="pend-card">
            <div class="pend-head"><div><h3>La misma tasa no afecta igual a todos</h3><p class="pend-note">El spread es una diferencia bruta entre tasas. No es ganancia bancaria ni resultado contable.</p></div></div>
            <div class="pend-actor-grid"><article class="pend-actor"><span class="emoji">🧾</span><h4>Deudor</h4><p>Necesita liquidez y <b>paga</b> una tasa. Para medir su costo efectivo hace falta CFT cuando esté disponible.</p></article><article class="pend-actor"><span class="emoji">🐷</span><h4>Ahorrista</h4><p>Puede inmovilizar pesos y <b>cobra</b> rendimiento. El plazo fijo promedio no representa todas las alternativas.</p></article><article class="pend-actor"><span class="emoji">🏦</span><h4>Intermediario</h4><p>El spread bruto también cubre riesgo, incobrabilidad, fondeo, encajes, costos, impuestos y capital regulatorio.</p></article></div>
            <div class="pend-gate"><span class="icon">🚧</span><div><h4>Rentabilidad bancaria: carril separado</h4><p>ROA, ROE, margen y resultado real no se derivan del spread ni de esta ventana contrafactual. Se incorporarán cuando exista una serie archivada y comparable; no se rellena el hueco con una tasa activa.</p></div></div>
          </section>
        </div>
      </div>

      <div class="pend-layer-panel" data-pend-layer-panel="housing" role="tabpanel" hidden>
        <div class="pend-layer-stack">
          <section class="pend-card pend-hero">
            <div class="pend-head"><div><span class="pend-kicker">C · Vivienda y presupuesto esencial</span><h2>Después de cobrar, ¿cuánto queda?</h2><p class="pend-sub">Propietario e inquilino pueden tener el mismo ingreso y márgenes disponibles muy distintos. La capa separa condición de tenencia, gastos observados y escenarios.</p></div></div>
            <div class="pend-layer-question">Inquilino ↔ propietario · costo habitacional<small>El alquiler pagado y la renta recibida son dos perspectivas del mismo flujo: jamás se cuentan dos veces.</small></div>
            {housing_badges}
            <div class="pend-power-grid"><article class="pend-power-metric neutral"><small>RATIO · fuente A</small><strong>Tenencia</strong><p>Propietario, inquilino y otras formas según EPH.</p><span class="perspective">Disponible en el tab Vivienda; no mide monto de alquiler.</span></article><article class="pend-power-metric"><small>RATIO · pendiente</small><strong>Alquiler / ingreso</strong><p>No hay todavía una serie contemporánea homogénea incorporada.</p><span class="perspective">Hueco visible: no se infiere desde precios publicados.</span></article><article class="pend-power-metric"><small>SNAPSHOT · fuente oficial</small><strong>ENGHo 2017–18</strong><p>Puede servir como estructura histórica del presupuesto por quintil.</p><span class="perspective">No se rotulará como presupuesto 2026.</span></article><article class="pend-power-metric"><small>ESCENARIO · pendiente</small><strong>Hogar tipo</strong><p>Calculadora futura separada de los datos observados.</p><span class="perspective">No descontará IVA dos veces dentro del consumo.</span></article></div>
            <div class="pend-links"><button class="pend-link" onclick="activateTab('tab-housing')">Abrir Vivienda →</button><button class="pend-link" onclick="activateTab('tab-family')">Abrir Canastas familiares →</button><button class="pend-link" onclick="activateTab('tab-consumption')">Abrir Consumo →</button></div>
          </section>
          <section class="pend-card"><div class="pend-head"><div><h3>Waterfall de $100 · todavía no cuantificado</h3><p class="pend-note">Se habilitará con dos modos explícitos: radiografía ENGHo 2017–18 o calculadora de hogar tipo. Nunca se presentará como una observación contemporánea si mezcla fechas.</p></div></div><div class="pend-gate"><span class="icon">🧮</span><div><h4>Control antidoble conteo activo</h4><p>Los impuestos indirectos ya contenidos en alimentos, alquiler formal, servicios y otros consumos no vuelven a restarse. Deuda principal, intereses, gasto y ahorro también deben separarse antes de cerrar una cuenta.</p></div></div></section>
        </div>
      </div>

      <div class="pend-layer-panel" data-pend-layer-panel="fiscal" role="tabpanel" hidden>
        <div class="pend-layer-stack">
          <section class="pend-card pend-hero">
            <div class="pend-head"><div><span class="pend-kicker">D · Estado, aportes y beneficios</span><h2>¿Quién pone la plata y hacia quién vuelve?</h2><p class="pend-sub">Esta capa reúne accesos a recaudación, transferencias, servicios y beneficios fiscales, pero no inventa una posición fiscal neta por hogar.</p></div></div>
            <div class="pend-layer-question">Contribuyentes ↔ Estado ↔ receptores / beneficiarios<small>Quién ingresa formalmente un impuesto no siempre es quien soporta económicamente su carga.</small></div>
            {fiscal_badges}
            <div class="pend-power-grid"><article class="pend-power-metric"><small>FLUJO · macro</small><strong>Recaudación</strong><p>IVA, Ganancias, contribuciones y otros recursos agregados.</p><span class="perspective">No asigna incidencia final a cada quintil.</span></article><article class="pend-power-metric"><small>FLUJO · macro</small><strong>Transferencias</strong><p>Jubilaciones, AUH y programas con unidades propias.</p><span class="perspective">Presupuesto no equivale siempre a recepción efectiva.</span></article><article class="pend-power-metric"><small>CONTRAFACTUAL</small><strong>Gasto tributario</strong><p>Tratamientos diferenciales y beneficios estimados.</p><span class="perspective">No equivale automáticamente a caja recuperable.</span></article><article class="pend-power-metric neutral"><small>RATIO · no calculado</small><strong>Posición fiscal neta</strong><p>Exigiría una microsimulación de incidencia compatible.</p><span class="perspective">No se reparte el IVA total a ojo.</span></article></div>
            <div class="pend-links"><button class="pend-link" onclick="activateTab('tab-fiscal')">Abrir Resultado fiscal →</button><button class="pend-link" onclick="activateTab('tab-social')">Abrir Transferencias →</button><button class="pend-link" onclick="activateTab('tab-meli-benefits')">Abrir Privilegios fiscales →</button><button class="pend-link" onclick="activateTab('tab-casta')">Abrir La casta →</button><button class="pend-link" onclick="activateTab('tab-wealth-contribution')">Abrir Grandes fortunas →</button></div>
          </section>
          <section class="pend-card"><div class="pend-head"><div><h3>Regla fiscal de lectura</h3><p class="pend-note">Transferencia, servicio en especie, subsidio económico, beneficio tributario y crédito presupuestario son clases distintas.</p></div></div><div class="pend-plain-grid"><div class="pend-plain-card up"><span class="icon">💸</span><b>Ejecutado</b>Flujo efectivamente registrado en un período.</div><div class="pend-plain-card warn"><span class="icon">🧾</span><b>Autorizado / presupuestado</b>Puede no haberse ejecutado todavía.</div><div class="pend-plain-card down"><span class="icon">🪞</span><b>Contrafactual</b>Estima qué ocurriría bajo otra regla; no es una transferencia observada.</div></div></section>
        </div>
      </div>

      <div class="pend-layer-panel" data-pend-layer-panel="assets" role="tabpanel" hidden>
        <div class="pend-layer-stack">
          <section class="pend-card pend-hero">
            <div class="pend-head"><div><span class="pend-kicker">E · La ventaja de ya tener capital</span><h2>Si tenías $100 invertibles, ¿qué pasó con su poder de compra?</h2><p class="pend-sub">Comparación condicional a poder poseer y mantener cada alternativa. No describe el patrimonio observado de los hogares ni quién tuvo acceso efectivo a cada precio.</p></div></div>
            {asset_badges}
            <div class="pend-chart-stickers"><span class="pend-chart-sticker warn">salario = referencia de ingreso, no activo</span><span class="pend-chart-sticker">A3500 = referencia mayorista</span><span class="pend-chart-sticker">PF = renovación mensual hipotética</span></div>
            <div class="pend-chart-scroll"><div id="pendPowerAssetChart" class="pend-asset-chart"></div></div>
            <div id="pendPowerAssetSummary" class="pend-asset-summary"></div>
            <div class="pend-reading"><b>Lectura correcta:</b> la curva responde “qué habría ocurrido si ya podías tener ese activo”. No demuestra cómo cambió la riqueza de la población, porque no incorpora cantidades poseídas ni distribución de la propiedad.</div>
          </section>
          <section class="pend-card">
            <div class="pend-head"><div><h3>Qué falta antes de ampliar la cartera</h3><p class="pend-note">Se prefieren huecos visibles a usar precios sin propiedad, renta, costos o cobertura comparables.</p></div></div>
            <div class="pend-asset-pending"><div><b>Acciones / bonos</b>Pendiente de elegir índices reproducibles, tratamiento de cupones/dividendos y acceso realista.</div><div><b>Inmuebles</b>Pendiente de serie homogénea, renta potencial, costos y cobertura geográfica.</div><div><b>Patrimonio de hogares</b>No se inferirá desde precios: requiere cantidades, deuda y propiedad efectiva.</div></div>
            <div class="pend-links"><button class="pend-link" onclick="activateTab('tab-power')">Abrir Salarios reales →</button><button class="pend-link" onclick="activateTab('tab-bcra')">Abrir Dólar y tasas →</button><button class="pend-link" onclick="activateTab('tab-housing')">Abrir Vivienda →</button></div>
          </section>
        </div>
      </div>

      <div class="pend-layer-panel" data-pend-layer-panel="lab" role="tabpanel" hidden>
        <div class="pend-layer-stack">
          <section class="pend-card pend-hero">
            <div class="pend-head"><div><span class="pend-kicker">F · Laboratorio de supuestos</span><h2>Las capas primero; el compuesto después</h2><p class="pend-sub">El laboratorio queda subordinado y sin un gran número factual. Antes de habilitar pesos, cada variable debe superar compatibilidad de unidad, período, signo, actores y solapamientos.</p></div></div>
            <div class="pend-disabled-lab"><h4>🔒 Índice compuesto todavía apagado</h4><p>No hay suficientes componentes contemporáneos compatibles para que un promedio ponderado sea informativo. Activarlo ahora produciría una cifra dominada por decisiones de diseño y datos faltantes.</p><div class="pend-lab-status"><div class="ready"><b>Producción</b><span>serie lista</span></div><div class="ready"><b>Finanzas</b><span>contrafactual listo</span></div><div class="blocked"><b>Vivienda</b><span>ratios pendientes</span></div><div class="blocked"><b>Fiscal</b><span>sin incidencia neta</span></div><div class="ready"><b>Activos</b><span>escenario condicional</span></div></div></div>
          </section>
          <section class="pend-card">
            <div class="pend-head"><div><h3>Matriz de riesgo de doble conteo</h3><p class="pend-note">Dos variables pueden ser válidas por separado y aun así no poder sumarse.</p></div></div>
            <div id="pendPowerOverlapTable" class="pend-risk-table"></div>
          </section>
          <section class="pend-card">
            <div class="pend-head"><div><h3>Registro autoauditable de métricas</h3><p class="pend-note">Tipo de medida, unidad, período, actores, fuente y transformación permanecen visibles.</p></div></div>
            <div class="pend-evidence-legend"><div class="pend-evidence"><b>A · fuente comparable</b><span>Cuenta o serie oficial con cobertura adecuada.</span></div><div class="pend-evidence"><b>B · derivado sólido</b><span>Transformación directa y reproducible.</span></div><div class="pend-evidence"><b>C · escenario</b><span>Reconstrucción, snapshot o rendimiento condicional.</span></div><div class="pend-evidence"><b>D · experimental</b><span>Normalización y pesos normativos.</span></div></div>
            <div id="pendPowerRegistryTable" class="pend-risk-table"></div>
          </section>
          <section class="pend-card pend-method"><details open><summary>▸ ¿Por qué no sumamos todo en un único índice?</summary><div><p>Cada capa responde una pregunta distinta y puede usar flujos, stocks, ratios o contrafactuales. Una suma directa puede duplicar el mismo flujo, mezclar fechas o convertir una elección normativa en un supuesto “dato”.</p><p>Cuando el laboratorio se habilite, los pesos serán visibles y editables, el resultado se llamará escenario y deberá mostrar sensibilidad. Nunca reemplazará las capas.</p></div></details></section>
        </div>
      </div>
    </div>
  </section>

'''


def power_script(asset_rows: list[dict]) -> str:
    metrics_json = json.dumps(METRICS, ensure_ascii=False, separators=(",", ":"))
    overlaps_json = json.dumps(OVERLAPS, ensure_ascii=False, separators=(",", ":"))
    assets_json = json.dumps(asset_rows, ensure_ascii=False, separators=(",", ":"), allow_nan=False)
    return f'''<script id="pendulo-poder-script-v141">
const PEND_POWER_METRICS={metrics_json};
const PEND_POWER_OVERLAPS={overlaps_json};
const PEND_POWER_ASSETS={assets_json};
let pendPowerAssetRendered=false;
function pendPowerFmt(value,digits=2){{return Number(value).toLocaleString('es-AR',{{minimumFractionDigits:digits,maximumFractionDigits:digits}})}}
function pendPowerMoney(value){{const sign=value>0?'+':value<0?'−':'';return `${{sign}}$ ${{pendPowerFmt(Math.abs(value)/1e12,2)}} B`}}
function pendPowerChange(value){{const delta=value-100,sign=delta>0?'+':delta<0?'−':'';return `${{sign}}${{pendPowerFmt(Math.abs(delta),1)}}% real`}}
function pendPowerLast(rows,key){{for(let i=rows.length-1;i>=0;i--)if(rows[i][key]!=null)return rows[i];return null}}
function renderPendPowerFinance(){{
 const root=document.getElementById('pendPowerFinanceKpis');if(!root||typeof ratesMoneySummary==='undefined')return;
 const d=ratesMoneySummary.diferencial;
 const cards=[
  ['Crédito bancario',d.impacto_hogar_banco,'Deudores','Empeoró respecto de la ventana espejo.','financial_bank_window_delta'],
  ['Fintech / PNFC',d.impacto_hogar_fintech,'Deudores fintech','Empeoró; incluye cinco meses estimados.','financial_fintech_window_delta'],
  ['Plazo fijo',d.impacto_hogar_pf,'Ahorristas','Mejoró y compensó las dos patas de crédito.','financial_pf_window_delta'],
  ['Balance ampliado',d.impacto_hogar_total_ampliado,'Universos distintos','Mejoró en conjunto; no todos ganaron.','financial_expanded_balance_delta']
 ];
 root.innerHTML=cards.map(([title,value,who,reading,id])=>`<article class="pend-power-metric ${{value>0?'good':value<0?'bad':'neutral'}}" data-metric-id="${{id}}"><small>CONTRAFACTUAL · diferencial</small><strong>${{pendPowerMoney(value)}}</strong><p><b>${{title}}:</b> ${{reading}}</p><span class="perspective">Perspectiva: ${{who}} · + mejora / − empeora</span></article>`).join('');
}}
function renderPendPowerAssets(){{
 const chart=document.getElementById('pendPowerAssetChart');if(!chart||!window.Plotly)return;
 const rows=PEND_POWER_ASSETS,x=rows.map(r=>r.date);
 const traces=[
  {{x,y:rows.map(r=>r.cash_real),name:'Efectivo sin remunerar',mode:'lines',line:{{color:'#d05d83',width:3,dash:'dot'}},hovertemplate:'<b>%{{x|%b %Y}}</b><br>Efectivo real: %{{y:.1f}}<br>Rendimiento condicional<extra></extra>'}},
  {{x,y:rows.map(r=>r.pf_real),name:'Plazo fijo renovado',mode:'lines+markers',line:{{color:'#49a17e',width:3}},marker:{{size:4}},hovertemplate:'<b>%{{x|%b %Y}}</b><br>PF real acumulado: %{{y:.1f}}<br>Supone renovación mensual<extra></extra>'}},
  {{x,y:rows.map(r=>r.usd_a3500_real),name:'Dólar mayorista A3500',mode:'lines+markers',line:{{color:'#d09335',width:3}},marker:{{size:4}},hovertemplate:'<b>%{{x|%b %Y}}</b><br>A3500 real: %{{y:.1f}}<br>Referencia mayorista<extra></extra>'}},
  {{x,y:rows.map(r=>r.salary_real_reference),name:'Salario real · referencia',mode:'lines',line:{{color:'#7357b5',width:3,dash:'dash'}},hovertemplate:'<b>%{{x|%b %Y}}</b><br>Salario real: %{{y:.1f}}<br>Ingreso, no activo<extra></extra>'}}
 ];
 const layout={{title:{{text:'Poder de compra real · base diciembre de 2023 = 100',font:{{size:13,color:'#5d4169'}}}},paper_bgcolor:'rgba(0,0,0,0)',plot_bgcolor:'rgba(255,255,255,.72)',font:{{family:'Nunito, Arial, sans-serif',color:'#654f6c',size:10}},margin:{{l:58,r:22,t:68,b:55}},hovermode:'x unified',xaxis:{{type:'date',gridcolor:'#eee5f2',tickformat:'%b<br>%Y',dtick:'M3',automargin:true}},yaxis:{{title:'índice real',gridcolor:'#eadff0',zeroline:false,automargin:true}},legend:{{orientation:'h',y:1.14,x:0,font:{{size:9}}}},shapes:[{{type:'line',xref:'paper',x0:0,x1:1,y0:100,y1:100,line:{{color:'#90759a',width:1,dash:'dash'}}}}],annotations:[{{xref:'paper',x:1,y:100,xanchor:'right',text:'base = 100',showarrow:false,yshift:10,font:{{size:9,color:'#806a87'}}}}]}};
 Plotly.react(chart,traces,layout,{{responsive:true,displaylogo:false,scrollZoom:false,modeBarButtonsToRemove:['lasso2d','select2d']}});pendPowerAssetRendered=true;
 const summary=document.getElementById('pendPowerAssetSummary');
 const defs=[['cash_real','Efectivo','Pesos líquidos sin remuneración'],['pf_real','Plazo fijo','Renovación mensual hipotética'],['usd_a3500_real','Dólar A3500','Referencia mayorista'],['salary_real_reference','Salario real','Referencia de ingreso · último dato anterior']];
 summary.innerHTML=defs.map(([key,title,note])=>{{const last=pendPowerLast(rows,key);return `<article class="pend-asset-kpi"><small>${{title}}</small><strong>${{pendPowerFmt(last[key],1)}}</strong><span>${{pendPowerChange(last[key])}} desde dic-2023 · ${{note}} · ${{last.date.slice(0,7)}}</span></article>`}}).join('');
}}
function renderPendPowerRegistry(){{
 const overlap=document.getElementById('pendPowerOverlapTable');if(overlap)overlap.innerHTML='<table><thead><tr><th>Métrica A</th><th>Métrica B</th><th>Riesgo</th><th>Relación</th><th>Regla</th></tr></thead><tbody>'+PEND_POWER_OVERLAPS.map(r=>`<tr><td>${{r.metric_a}}</td><td>${{r.metric_b}}</td><td class="${{r.risk==='alto'?'pend-risk-high':'pend-risk-medium'}}">${{r.risk}}</td><td>${{r.relationship}}</td><td>${{r.rule}}</td></tr>`).join('')+'</tbody></table>';
 const registry=document.getElementById('pendPowerRegistryTable');if(registry)registry.innerHTML='<table><thead><tr><th>Capa / métrica</th><th>Clase</th><th>Unidad / frecuencia</th><th>Evidencia</th><th>Actores</th><th>Estado</th></tr></thead><tbody>'+PEND_POWER_METRICS.map(r=>`<tr><td><b>${{r.layer}}</b><br>${{r.title}}<br><small>${{r.economic_flow_id}}</small></td><td>${{r.measure_type}}<br><small>${{r.transformation}}</small></td><td>${{r.unit}}<br><small>${{r.frequency}} · ${{r.period}}</small></td><td><b>${{r.source_grade}}</b></td><td>${{r.actors}}</td><td>${{r.status}}<br><small>${{r.note}}</small></td></tr>`).join('')+'</tbody></table>';
}}
function pendActivatePowerLayer(layer){{
 document.querySelectorAll('#pendPowerLayerNav .pend-layer-btn').forEach(btn=>{{const active=btn.dataset.layer===layer;btn.classList.toggle('active',active);btn.setAttribute('aria-selected',String(active))}});
 document.querySelectorAll('#tab-pendulo [data-pend-layer-panel]').forEach(panel=>{{const active=panel.dataset.pendLayerPanel===layer;panel.classList.toggle('active',active);panel.hidden=!active}});
 if(layer==='finance')renderPendPowerFinance();
 if(layer==='assets')requestAnimationFrame(renderPendPowerAssets);
 if(layer==='lab')renderPendPowerRegistry();
 if(layer==='production'&&window.Plotly)requestAnimationFrame(()=>['pendMainChart','pendSharesChart','pendMandateChart'].forEach(id=>{{const el=document.getElementById(id);if(el)Plotly.Plots.resize(el)}}));
}}
document.getElementById('pendPowerLayerNav')?.addEventListener('click',event=>{{const button=event.target.closest('button[data-layer]');if(button)pendActivatePowerLayer(button.dataset.layer)}});
window.addEventListener('resize',()=>{{if(pendPowerAssetRendered){{const el=document.getElementById('pendPowerAssetChart');if(el&&window.Plotly)Plotly.Plots.resize(el)}}}});
</script>

'''


def make_audit(asset_rows: list[dict], output_hash: str, tests: dict[str, bool]) -> str:
    last = asset_rows[-1]
    salary_last = next(row for row in reversed(asset_rows) if row["salary_real_reference"] is not None)
    results = "\n".join(f"- {name}: {'PASS' if ok else 'FAIL'}" for name, ok in tests.items())
    return f"""# Auditoría · Péndulo del poder económico v141

Fecha de corte editorial: 2026-08-21  
Archivo: `data/dashboard_kawaii_141_pendulo_poder_economico.html`  
SHA-256: `{output_hash}`

## Alcance de esta primera etapa

- El Péndulo CGI original se conserva sin alterar fórmulas, datos ni asignación por gobierno.
- Se incorporan seis capas navegables: Producción, Finanzas, Vivienda, Fiscal, Activos y Laboratorio.
- Finanzas resume los cálculos ya auditados del tab Tasas e inflación; no los recalcula con otra semántica.
- Vivienda y Fiscal muestran cobertura y huecos antes que fabricar incidencia contemporánea.
- El índice compuesto permanece deshabilitado hasta que existan componentes compatibles.
- Se crea un registro de métricas y una matriz de riesgo de doble conteo.

## La ventaja de ya tener capital

Base común real: diciembre de 2023 = 100.

- Efectivo sin remunerar, julio de 2026: {last['cash_real']:.6f}.
- Plazo fijo renovado mensualmente, julio de 2026: {last['pf_real']:.6f}.
- Dólar A3500 real, julio de 2026: {last['usd_a3500_real']:.6f}.
- Salario real como referencia, último dato {salary_last['date'][:7]}: {salary_last['salary_real_reference']:.6f}.

Fórmulas:

```text
efectivo_real_t = 100 × IPC_base / IPC_t
dólar_real_t = 100 × (A3500_t / A3500_base) × (IPC_base / IPC_t)
PF_real_t = PF_real_t-1 × (1 + rendimiento_real_mensual_t)
salario_real_t = 100 × índice_salario_real_t / índice_salario_real_base
```

El salario es una referencia de ingreso, no un activo. A3500 es referencia mayorista. El plazo fijo supone renovación mensual al promedio de 30–59 días. Ninguna curva informa quién poseía el activo.

## Clasificación de evidencia

Se separan dos ejes:

1. calidad/cobertura de fuente: A–D;
2. transformación: observado, derivado, contrafactual, reconstrucción o escenario.

El registro completo está en `metric_registry.json`. La matriz de solapamientos está en `double_count_matrix.csv`.

## Controles automáticos

{results}
"""


def write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    text = SOURCE_HTML.read_text(encoding="utf-8")
    if 'id="pendulo-poder-v141"' in text:
        raise RuntimeError("La fuente v140 ya contiene v141; no es una base limpia")
    asset_rows = build_asset_rows(text)

    css_marker = '<style id="rutas-publico-privado-v139">'
    if css_marker not in text:
        raise RuntimeError("No se encontró el marcador CSS de Rutas")
    text = text.replace(css_marker, POWER_CSS + "\n" + css_marker, 1)
    text = text.replace(
        '<button class="tab-btn" data-tab="tab-pendulo">Péndulo distributivo</button>',
        '<button class="tab-btn" data-tab="tab-pendulo">Péndulo del poder económico</button>',
        1,
    )

    section_start = text.index('  <section id="tab-pendulo" class="tab-panel">')
    section_end = text.index('  <section id="tab-fiscal" class="tab-panel">', section_start)
    old_section = text[section_start:section_end]
    shell_marker = '<div class="pend-shell">'
    shell_start = old_section.index(shell_marker) + len(shell_marker)
    shell_end = old_section.rfind('</div>')
    production_inner = old_section[shell_start:shell_end].strip()
    production_inner = production_inner.replace(
        '<h2>Péndulo distributivo ♡</h2><p class="pend-sub">Un instrumento para contrastar —no para dar por cierta— una hipótesis sobre cómo se reparte el ingreso generado entre trabajo/hogares y excedente societario.</p>',
        '<h2>A · Péndulo de producción / distribución primaria ♡</h2><p class="pend-sub"><b>Pregunta:</b> ¿quién capturó el ingreso cuando se produjo? La Cuenta de Generación del Ingreso se conserva exactamente como estaba auditada; esta capa no incorpora intereses, alquileres, impuestos ni activos.</p><div class="pend-meta-line"><span class="pend-meta ratio">RATIO · trimestral</span><span class="pend-meta evidence-a">fuente A · CGI oficial</span><span class="pend-meta">transformación: derivado</span><span class="pend-meta">actores: trabajo + IMB ↔ EEB</span></div>',
        1,
    )
    new_section = build_outer_section(production_inner)
    text = text[:section_start] + new_section + text[section_end:]

    js_marker = '<script id="rutas-publico-privado-script-v139">'
    if js_marker not in text:
        raise RuntimeError("No se encontró el marcador JS de Rutas")
    text = text.replace(js_marker, power_script(asset_rows) + js_marker, 1)

    tests = {
        "original_cgi_formula_preserved": "pendulo = ((RTA + IMB) − EEB) / (RTA + IMB + EEB) × 100" in text,
        "six_layer_buttons": text.count('class="pend-layer-btn') == 6,
        "financial_summary_uses_audited_global": "ratesMoneySummary.diferencial" in text,
        "asset_base_is_100": all(abs(asset_rows[0][field] - 100) < 1e-9 for field in ("cash_real", "pf_real", "usd_a3500_real", "salary_real_reference")),
        "asset_salary_has_visible_gap": asset_rows[-1]["salary_real_reference"] is None,
        "composite_is_disabled": "Índice compuesto todavía apagado" in text,
        "tab_count_preserved": text.count('class="tab-btn') == SOURCE_HTML.read_text(encoding="utf-8").count('class="tab-btn'),
    }
    ids = re.findall(r'\bid="([^"]+)"', text)
    tests["html_ids_unique"] = len(ids) == len(set(ids))
    tests["metric_ids_unique"] = len({row["id"] for row in METRICS}) == len(METRICS)
    if not all(tests.values()):
        failed = ", ".join(name for name, ok in tests.items() if not ok)
        raise RuntimeError(f"Fallaron controles: {failed}")

    DERIVED_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_HTML.write_text(text, encoding="utf-8")
    INDEX_HTML.write_text(text, encoding="utf-8")
    REGISTRY_JSON.write_text(json.dumps(METRICS, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_csv(OVERLAPS_CSV, OVERLAPS, ["metric_a", "metric_b", "risk", "relationship", "rule"])
    write_csv(
        ASSETS_CSV,
        asset_rows,
        ["date", "cash_real", "pf_real", "usd_a3500_real", "salary_real_reference", "ipc_level", "fx_a3500", "pf_real_monthly_pct"],
    )
    output_hash = hashlib.sha256(OUTPUT_HTML.read_bytes()).hexdigest()
    AUDIT_MD.write_text(make_audit(asset_rows, output_hash, tests), encoding="utf-8")
    TESTS_JSON.write_text(json.dumps(tests, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(OUTPUT_HTML), "sha256": output_hash, "tests": tests}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
