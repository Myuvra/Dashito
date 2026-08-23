from __future__ import annotations

import csv
import hashlib
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
SOURCE_HTML = ROOT / "data" / "dashboard_kawaii_141_pendulo_poder_economico.html"
OUTPUT_HTML = ROOT / "data" / "dashboard_kawaii_142_pendulo_financiero_observado.html"
INDEX_HTML = ROOT / "index.html"
RATES_CSV = ROOT / "data" / "derivados" / "tasas_pinza_hogar_auditada.csv"
DERIVED_DIR = ROOT / "data" / "derivados" / "pendulo_poder_economico"
FINANCIAL_CSV = DERIVED_DIR / "financial_real_monthly_2019_2026.csv"
REGISTRY_JSON = DERIVED_DIR / "metric_registry.json"
OVERLAPS_CSV = DERIVED_DIR / "double_count_matrix.csv"
AUDIT_MD = DERIVED_DIR / "AUDITORIA_CAPA_FINANCIERA_V142.md"
TESTS_JSON = DERIVED_DIR / "TESTS_CAPA_FINANCIERA_V142.json"


NEW_METRICS = [
    {
        "id": "financial_bank_real_monthly",
        "layer": "Finanzas",
        "title": "Crédito bancario · costo real mensual",
        "measure_type": "RATIO",
        "unit": "% real mensual",
        "frequency": "mensual",
        "period": "ene-2019–jul-2026",
        "source_grade": "B",
        "transformation": "Fisher desde TNA promedio e IPC",
        "actors": "hogar deudor ↔ banco",
        "economic_flow_id": "bank_credit_price_real",
        "status": "disponible",
        "do_not_sum_with": ["financial_bank_window_delta", "bank_interest_income", "bank_profitability"],
        "note": "Precio real promedio del crédito; no es CFT, interés cobrado ni ganancia bancaria.",
    },
    {
        "id": "financial_fintech_real_monthly",
        "layer": "Finanzas",
        "title": "Fintech/PNFC · costo real mensual",
        "measure_type": "RATIO",
        "unit": "% real mensual",
        "frequency": "mensual",
        "period": "abr-2021–feb-2026 observado; mar–jul-2026 prolongado",
        "source_grade": "B/C",
        "transformation": "Fisher + extensión visible",
        "actors": "hogar deudor ↔ PNFC/fintech",
        "economic_flow_id": "fintech_credit_price_real",
        "status": "observado hasta feb-2026; extensión separada",
        "do_not_sum_with": ["financial_fintech_window_delta", "fintech_interest_income", "fintech_profitability"],
        "note": "La extensión conserva la última TNA oficial; no es CFT ni ganancia de la fintech.",
    },
    {
        "id": "financial_pf_real_monthly",
        "layer": "Finanzas",
        "title": "Plazo fijo · rendimiento real mensual",
        "measure_type": "RATIO",
        "unit": "% real a 30 días",
        "frequency": "mensual",
        "period": "ene-2019–jul-2026",
        "source_grade": "B",
        "transformation": "Fisher desde tasa 30–59 días e IPC",
        "actors": "ahorrista ↔ banco",
        "economic_flow_id": "bank_saving_price_real",
        "status": "disponible",
        "do_not_sum_with": ["financial_pf_window_delta", "asset_pf_real"],
        "note": "Rendimiento promedio real; no representa todas las alternativas ni un hogar promedio.",
    },
    {
        "id": "financial_bank_pf_real_gap",
        "layer": "Finanzas",
        "title": "Diferencia real crédito bancario − plazo fijo",
        "measure_type": "RATIO",
        "unit": "puntos porcentuales reales mensuales",
        "frequency": "mensual",
        "period": "ene-2019–jul-2026",
        "source_grade": "B",
        "transformation": "resta de tasas reales comparables",
        "actors": "deudor ↔ ahorrista; intermediario como nexo",
        "economic_flow_id": "bank_credit_saving_price_gap",
        "status": "disponible",
        "do_not_sum_with": ["bank_financial_margin", "bank_profitability", "financial_bank_window_delta"],
        "note": "Brecha bruta de precios financieros; no es margen contable ni ganancia.",
    },
    {
        "id": "financial_consumer_cft",
        "layer": "Finanzas",
        "title": "Costo Financiero Total comparable",
        "measure_type": "RATIO",
        "unit": "% efectivo con cargos",
        "frequency": "mensual deseada",
        "period": "pendiente",
        "source_grade": "—",
        "transformation": "sin fabricar",
        "actors": "hogar deudor ↔ proveedor de crédito",
        "economic_flow_id": "consumer_credit_total_cost",
        "status": "no integrado: falta serie continua comparable",
        "do_not_sum_with": ["financial_bank_real_monthly", "financial_fintech_real_monthly"],
        "note": "La TNA no reemplaza al CFT. El hueco queda declarado.",
    },
    {
        "id": "bank_profitability",
        "layer": "Finanzas",
        "title": "Rentabilidad bancaria real",
        "measure_type": "RATIO / FLUJO CONTABLE",
        "unit": "ROA, ROE, margen y resultado real",
        "frequency": "mensual o trimestral deseada",
        "period": "pendiente",
        "source_grade": "A requerida",
        "transformation": "carril separado",
        "actors": "bancos y accionistas",
        "economic_flow_id": "bank_accounting_profitability",
        "status": "no integrado: requiere estados contables comparables",
        "do_not_sum_with": ["financial_bank_pf_real_gap", "financial_bank_window_delta"],
        "note": "No se deriva del spread de tasas ni del contrafactual del hogar.",
    },
]


NEW_OVERLAPS = [
    {
        "metric_a": "financial_bank_real_monthly",
        "metric_b": "financial_bank_window_delta",
        "risk": "alto",
        "relationship": "la tasa real es insumo del impacto contrafactual",
        "rule": "mostrar nivel e impacto por separado; nunca sumarlos",
    },
    {
        "metric_a": "financial_fintech_real_monthly",
        "metric_b": "financial_fintech_window_delta",
        "risk": "alto",
        "relationship": "la tasa real es insumo de la exposición contrafactual",
        "rule": "no sumar precio del crédito e impacto monetario",
    },
    {
        "metric_a": "financial_bank_pf_real_gap",
        "metric_b": "bank_profitability",
        "risk": "alto",
        "relationship": "brecha de precios vs resultado contable del intermediario",
        "rule": "la brecha no aproxima ROA, ROE ni ganancia",
    },
    {
        "metric_a": "financial_pf_real_monthly",
        "metric_b": "asset_pf_real",
        "risk": "medio",
        "relationship": "tasa de un mes vs cartera real acumulada",
        "rule": "pueden explicar el mismo escenario; no se agregan",
    },
    {
        "metric_a": "financial_consumer_cft",
        "metric_b": "financial_bank_real_monthly",
        "risk": "alto",
        "relationship": "costo total del producto vs tasa promedio sin todos los cargos",
        "rule": "no sustituir CFT faltante por TNA",
    },
]


FINANCE_CSS = r'''
<style id="pendulo-financiero-observado-v142">
#tab-pendulo .pend-shell{grid-template-columns:minmax(0,1fr);min-width:0}#tab-pendulo .pend-layer-panel,#tab-pendulo .pend-layer-stack,#tab-pendulo .pend-layer-stack>*{min-width:0;max-width:100%}#tab-pendulo .pend-layer-stack{grid-template-columns:minmax(0,1fr)}
#tab-pendulo .pend-finance-observed{border-color:#c9b8dc;background:linear-gradient(145deg,rgba(255,253,255,.98),rgba(247,252,255,.98))}
.pend-finance-glossary{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:9px;margin-top:12px}.pend-finance-term{padding:12px;border:1px solid #dfd3e7;border-radius:15px;background:#fff}.pend-finance-term small{display:block;color:#866e8d;font-size:7.4px;font-weight:950;letter-spacing:.04em;text-transform:uppercase}.pend-finance-term b{display:block;margin:5px 0 3px;color:#583865;font-size:11px}.pend-finance-term p{margin:0;color:#75617b;font-size:8.7px;line-height:1.45}.pend-finance-term.missing{border-style:dashed;background:#fffaf1}.pend-finance-term.separate{background:#f6fbff}
.pend-finance-chart{width:100%;min-width:780px;height:450px}.pend-finance-now{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:9px;margin-top:12px}.pend-fin-now-card{padding:13px;border:1px solid #dfd2e7;border-radius:16px;background:#fff}.pend-fin-now-card.cost{border-color:#e6bdcc;background:#fff7fa}.pend-fin-now-card.saving{border-color:#c5dccc;background:#f7fff9}.pend-fin-now-card.gap{border-color:#d5c5e6;background:#faf8ff}.pend-fin-now-card small{display:block;color:#846e8b;font-size:7.3px;font-weight:950;letter-spacing:.035em;text-transform:uppercase}.pend-fin-now-card strong{display:block;margin:5px 0 4px;color:#5b3b68;font-size:20px;line-height:1}.pend-fin-now-card.cost strong{color:#a74368}.pend-fin-now-card.saving strong{color:#2f7e64}.pend-fin-now-card p{margin:0;color:#725f78;font-size:8.8px;line-height:1.45}.pend-fin-now-card .date{display:block;margin-top:7px;padding-top:6px;border-top:1px dashed #ded3e4;color:#806b86;font-size:7.8px;font-weight:900}
.pend-finance-plain{margin-top:12px;padding:13px 15px;border-left:5px solid #d25980;border-radius:14px;background:#fff7fa;color:#694e5b;font-size:10px;line-height:1.55}.pend-finance-plain b{color:#8f3658}.pend-finance-source{margin-top:9px;color:#7b687f;font-size:8.5px;line-height:1.5}
@media(max-width:1050px){.pend-finance-glossary,.pend-finance-now{grid-template-columns:repeat(2,minmax(0,1fr))}}
@media(max-width:760px){.pend-finance-chart{min-width:680px;height:420px}.pend-finance-glossary,.pend-finance-now{grid-template-columns:1fr 1fr}}
@media(max-width:430px){.pend-finance-glossary,.pend-finance-now{grid-template-columns:1fr}.pend-finance-chart{min-width:640px}.pend-fin-now-card strong{font-size:19px}}
</style>
'''


FINANCE_SECTION = r'''
          <section class="pend-card pend-finance-observed">
            <div class="pend-head"><div><span class="pend-kicker">Película observada · precios financieros</span><h3>Crédito y ahorro, medidos en poder de compra</h3><p class="pend-note">Tasa real mensual: cuánto ganó o perdió cada tasa frente a la inflación del mismo mes. Banco y plazo fijo llegan a jul-2026; fintech está observada hasta feb-2026 y luego se prolonga en trazo punteado.</p></div></div>
            <div class="pend-finance-glossary" aria-label="Qué mide cada tasa">
              <article class="pend-finance-term"><small>TNA · nominal</small><b>Precio anunciado anual</b><p>Sirve como insumo y contexto. No descuenta inflación ni incluye necesariamente todos los cargos.</p></article>
              <article class="pend-finance-term"><small>REAL · mensual · B</small><b>La comparación del gráfico</b><p>Aplica Fisher contra el IPC mensual. Positivo en crédito significa mayor costo real para quien debe.</p></article>
              <article class="pend-finance-term missing"><small>CFT · faltante visible</small><b>No lo reemplazamos con TNA</b><p>Falta una serie continua y comparable con seguros, comisiones y demás cargos del producto.</p></article>
              <article class="pend-finance-term separate"><small>RENTABILIDAD · carril aparte</small><b>ROA/ROE no salen del spread</b><p>Requieren estados contables comparables; no se deducen de estas curvas.</p></article>
            </div>
            <div class="pend-chart-stickers"><span class="pend-chart-sticker warn">+ crédito real = peor para quien debe</span><span class="pend-chart-sticker">+ PF real = mejor para quien ahorra</span><span class="pend-chart-sticker">línea fintech punteada = extensión</span></div>
            <div class="pend-chart-scroll"><div id="pendPowerFinanceRealChart" class="pend-finance-chart"></div></div>
            <div id="pendPowerFinanceNow" class="pend-finance-now"></div>
            <div class="pend-finance-plain"><b>En criollo:</b> la cifra positiva no siempre “beneficia al hogar”. En un préstamo es costo para el deudor; en un plazo fijo es rendimiento para el ahorrista. La distancia banco − plazo fijo muestra cuánto se separan esos dos precios, pero <b>no dice cuánto ganó el banco</b>.</div>
            <p class="pend-finance-source">Fuente: promedios oficiales BCRA e INDEC; PNFC/fintech según serie archivada del tab Tasas e inflación. Transformación Fisher reproducible. Las tasas son promedios, no ofertas individuales ni CFT.</p>
          </section>

'''


FINANCE_SCRIPT_TEMPLATE = r'''
<script id="pendulo-financiero-observado-script-v142">
const PEND_POWER_FINANCE_ROWS=__FINANCE_ROWS__;
const PEND_POWER_FINANCE_METRICS=__FINANCE_METRICS__;
const PEND_POWER_FINANCE_OVERLAPS=__FINANCE_OVERLAPS__;
PEND_POWER_METRICS.push(...PEND_POWER_FINANCE_METRICS);
PEND_POWER_OVERLAPS.push(...PEND_POWER_FINANCE_OVERLAPS);
let pendPowerFinanceRealRendered=false;
function pendPowerFinancePct(value){const sign=value>0?'+':value<0?'−':'';return `${sign}${pendPowerFmt(Math.abs(value),2)}%`;}
function pendPowerFinancePp(value){const sign=value>0?'+':value<0?'−':'';return `${sign}${pendPowerFmt(Math.abs(value),2)} pp`;}
function renderPendPowerFinanceObserved(){
 const chart=document.getElementById('pendPowerFinanceRealChart');
 const cards=document.getElementById('pendPowerFinanceNow');
 if(!chart||!cards||!window.Plotly)return;
 const rows=PEND_POWER_FINANCE_ROWS,x=rows.map(r=>r.date);
 const firstExtended=rows.findIndex(r=>r.fintech_extended);
 const fintechObserved=rows.map(r=>r.fintech_observed?r.fintech_real_monthly_pct:null);
 const fintechExtended=rows.map((r,index)=>firstExtended>=1&&index>=firstExtended-1?r.fintech_real_monthly_pct:null);
 const traces=[
  {x,y:rows.map(r=>r.bank_real_monthly_pct),name:'Crédito bancario · costo real',mode:'lines',line:{color:'#ef6c91',width:2.8},hovertemplate:'<b>%{x|%b %Y}</b><br>Banco: %{y:.2f}% real mensual<br>+ = mayor costo real para el deudor<extra></extra>'},
  {x,y:rows.map(r=>r.pf_real_monthly_pct),name:'Plazo fijo · rendimiento real',mode:'lines',line:{color:'#47a07e',width:2.8},hovertemplate:'<b>%{x|%b %Y}</b><br>Plazo fijo: %{y:.2f}% real mensual<br>+ = ganó poder de compra<extra></extra>'},
  {x,y:fintechObserved,name:'Fintech · costo real observado',mode:'lines',line:{color:'#8c5bbc',width:3},hovertemplate:'<b>%{x|%b %Y}</b><br>Fintech: %{y:.2f}% real mensual<br>Dato de tasa observado<extra></extra>'},
  {x,y:fintechExtended,name:'Fintech · extensión',mode:'lines',line:{color:'#8c5bbc',width:3,dash:'dot'},hovertemplate:'<b>%{x|%b %Y}</b><br>Fintech: %{y:.2f}% real mensual<br>Extensión de última TNA oficial<extra></extra>'}
 ];
 const layout={title:{text:'Tasa real mensual · crédito cuesta / ahorro rinde',font:{size:13,color:'#5d4169'}},paper_bgcolor:'rgba(0,0,0,0)',plot_bgcolor:'rgba(255,255,255,.74)',font:{family:'Nunito, Arial, sans-serif',color:'#654f6c',size:10},margin:{l:58,r:24,t:76,b:58},hovermode:'x unified',xaxis:{type:'date',gridcolor:'#eee5f2',tickformat:'%b<br>%Y',dtick:'M12',automargin:true},yaxis:{title:'% real mensual',ticksuffix:'%',gridcolor:'#eadff0',zeroline:false,automargin:true},legend:{orientation:'h',y:1.17,x:0,font:{size:9}},shapes:[{type:'line',xref:'paper',x0:0,x1:1,y0:0,y1:0,line:{color:'#7d6884',width:1,dash:'dash'}},{type:'line',x0:'2023-12-01',x1:'2023-12-01',yref:'paper',y0:0,y1:1,line:{color:'#dc6f92',width:1.5,dash:'dot'}}],annotations:[{xref:'paper',x:1,y:0,xanchor:'right',text:'0% = empató a la inflación',showarrow:false,yshift:10,font:{size:8,color:'#806a87'}},{x:'2023-12-01',yref:'paper',y:1,text:'shock dic-2023',showarrow:false,yshift:10,font:{size:8,color:'#a33f62'}}]};
 Plotly.react(chart,traces,layout,{responsive:true,displaylogo:false,scrollZoom:false,modeBarButtonsToRemove:['lasso2d','select2d']});
 pendPowerFinanceRealRendered=true;
 const latest=rows[rows.length-1];
 const lastFintech=[...rows].reverse().find(r=>r.fintech_observed);
 cards.innerHTML=[
  ['cost','Crédito bancario · costo',pendPowerFinancePct(latest.bank_real_monthly_pct),'Una tasa real positiva encarece el préstamo frente al IPC.','jul-2026 · promedio observado'],
  ['cost','Fintech · costo',pendPowerFinancePct(lastFintech.fintech_real_monthly_pct),'Última comparación con tasa fintech observada.','feb-2026 · último observado'],
  ['saving','Plazo fijo · rendimiento',pendPowerFinancePct(latest.pf_real_monthly_pct),'Negativo: el ahorro perdió poder de compra ese mes.','jul-2026 · promedio observado'],
  ['gap','Banco − plazo fijo',pendPowerFinancePp(latest.bank_pf_real_gap_pp),'Brecha bruta de precios; no es margen contable.','jul-2026 · cálculo derivado B']
 ].map(([kind,title,value,note,date])=>`<article class="pend-fin-now-card ${kind}"><small>${title}</small><strong>${value}</strong><p>${note}</p><span class="date">${date}</span></article>`).join('');
}
window.addEventListener('resize',()=>{if(pendPowerFinanceRealRendered){const el=document.getElementById('pendPowerFinanceRealChart');if(el&&window.Plotly)Plotly.Plots.resize(el);}});
</script>

'''


def bool_value(value: str) -> bool:
    return value.strip().lower() in {"true", "1", "yes", "sí", "si"}


def build_financial_rows(text: str) -> list[dict]:
    modern = extract_embedded_array(text, "modern")
    with RATES_CSV.open(encoding="utf-8-sig", newline="") as handle:
        source_rows = list(csv.DictReader(handle))
    rate_map = {row["fecha"]: row for row in source_rows}
    rows: list[dict] = []
    for source in modern:
        month = source["date"][:7]
        audited = rate_map.get(month)
        bank = float(source["bancoReal"])
        pf = float(source["pfReal"])
        fintech_observed = source["fintechReal"] is not None
        fintech_extended = bool(audited) and not fintech_observed and month >= "2026-03"
        fintech = (
            float(source["fintechReal"])
            if fintech_observed
            else float(audited["fintech_real"])
            if fintech_extended
            else None
        )
        rows.append(
            {
                "date": source["date"],
                "bank_real_monthly_pct": bank,
                "pf_real_monthly_pct": pf,
                "fintech_real_monthly_pct": fintech,
                "bank_pf_real_gap_pp": bank - pf,
                "fintech_tna_pct": None if not audited else float(audited["fintech_tna"]),
                "fintech_observed": fintech_observed,
                "fintech_extended": fintech_extended,
                "fintech_status": "observado" if fintech_observed else "extensión última TNA oficial" if fintech_extended else "sin serie fintech comparable",
            }
        )
    if not rows or rows[0]["date"] != "2019-01-01" or rows[-1]["date"] != "2026-07-01":
        raise RuntimeError("Cobertura financiera inesperada")
    return rows


def extract_embedded_array(text: str, name: str) -> list[dict]:
    match = re.search(rf"^const {re.escape(name)}\s*=\s*(\[.*?\]);\s*$", text, re.MULTILINE)
    if not match:
        raise RuntimeError(f"No se encontró {name} en el HTML")
    return json.loads(match.group(1))


def read_csv(path: Path) -> list[dict]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def build_audit(rows: list[dict], tests: dict[str, bool], digest: str) -> str:
    latest = rows[-1]
    last_fintech = next(row for row in reversed(rows) if row["fintech_observed"])
    results = "\n".join(f"- {name}: {'PASS' if ok else 'FAIL'}" for name, ok in tests.items())
    return f"""# Auditoría · capa financiera observada v142

Fecha editorial: 2026-08-21  
Archivo: `data/dashboard_kawaii_142_pendulo_financiero_observado.html`  
SHA-256: `{digest}`

## Qué se agregó

- Película mensual desde enero de 2019 de costo real del crédito bancario, costo real fintech y rendimiento real del plazo fijo.
- Tramo fintech observado hasta febrero de 2026 y extensión marzo–julio separada visualmente.
- Cuatro lecturas actuales con perspectiva explícita: deudor, ahorrista y brecha bruta.
- Glosario visible que distingue TNA, tasa real mensual, CFT faltante y rentabilidad contable.
- El spread queda rotulado como diferencia de precios financieros, nunca como ganancia.

## Últimos valores visibles

- Crédito bancario, julio de 2026: {latest['bank_real_monthly_pct']:.6f}% real mensual.
- Plazo fijo, julio de 2026: {latest['pf_real_monthly_pct']:.6f}% real mensual.
- Banco − plazo fijo, julio de 2026: {latest['bank_pf_real_gap_pp']:.6f} pp.
- Fintech, último observado febrero de 2026: {last_fintech['fintech_real_monthly_pct']:.6f}% real mensual.

Fórmula de la brecha mostrada:

```text
brecha_real_banco_pf_t = tasa_real_banco_t − rendimiento_real_pf_t
3,292465 − (−0,374889) = 3,667354 pp en julio de 2026
```

Las tasas reales ya provienen de la transformación Fisher auditada del tab Tasas e inflación. CFT queda ausente porque no hay una serie continua comparable integrada. ROA/ROE y resultados reales permanecen en un carril separado.

## Controles

{results}
"""


def main() -> None:
    text = SOURCE_HTML.read_text(encoding="utf-8")
    if 'id="pendulo-financiero-observado-v142"' in text:
        raise RuntimeError("La fuente v141 ya contiene v142")
    rows = build_financial_rows(text)
    existing_metrics = extract_embedded_array(text, "PEND_POWER_METRICS")
    existing_overlaps = extract_embedded_array(text, "PEND_POWER_OVERLAPS")
    all_metrics = existing_metrics + NEW_METRICS
    all_overlaps = existing_overlaps + NEW_OVERLAPS

    css_marker = '<style id="rutas-publico-privado-v139">'
    if css_marker not in text:
        raise RuntimeError("No se encontró marcador CSS")
    text = text.replace(css_marker, FINANCE_CSS + "\n" + css_marker, 1)

    section_marker = '          <section class="pend-card">\n            <div class="pend-head"><div><h3>La misma tasa no afecta igual a todos</h3>'
    if section_marker not in text:
        raise RuntimeError("No se encontró la segunda tarjeta financiera")
    text = text.replace(section_marker, FINANCE_SECTION + section_marker, 1)

    script = (
        FINANCE_SCRIPT_TEMPLATE.replace("__FINANCE_ROWS__", json.dumps(rows, ensure_ascii=False, separators=(",", ":")))
        .replace("__FINANCE_METRICS__", json.dumps(NEW_METRICS, ensure_ascii=False, separators=(",", ":")))
        .replace("__FINANCE_OVERLAPS__", json.dumps(NEW_OVERLAPS, ensure_ascii=False, separators=(",", ":")))
    )
    script_marker = '<script id="rutas-publico-privado-script-v139">'
    if script_marker not in text:
        raise RuntimeError("No se encontró marcador JS")
    text = text.replace(script_marker, script + script_marker, 1)
    activation = "if(layer==='finance')renderPendPowerFinance();"
    if activation not in text:
        raise RuntimeError("No se encontró activación financiera")
    text = text.replace(activation, "if(layer==='finance'){renderPendPowerFinance();renderPendPowerFinanceObserved();}", 1)

    last_fintech = next(row for row in reversed(rows) if row["fintech_observed"])
    tests = {
        "coverage_2019_2026": rows[0]["date"] == "2019-01-01" and rows[-1]["date"] == "2026-07-01",
        "fintech_observed_ends_feb_2026": last_fintech["date"] == "2026-02-01",
        "fintech_extension_is_visible": "Fintech · extensión" in text and "trazo punteado" in text,
        "gap_formula_exact": all(abs(row["bank_pf_real_gap_pp"] - (row["bank_real_monthly_pct"] - row["pf_real_monthly_pct"])) < 1e-12 for row in rows),
        "cft_missing_declared": "CFT · faltante visible" in text and "No lo reemplazamos con TNA" in text,
        "profitability_separate": "ROA/ROE no salen del spread" in text,
        "finance_renderer_connected": "renderPendPowerFinanceObserved();" in text,
        "six_layers_preserved": text.count('class="pend-layer-btn') == 6,
        "asset_module_preserved": 'id="pendPowerAssetChart"' in text,
        "original_cgi_formula_preserved": "pendulo = ((RTA + IMB) − EEB) / (RTA + IMB + EEB) × 100" in text,
        "tab_count_preserved": text.count('class="tab-btn') == SOURCE_HTML.read_text(encoding="utf-8").count('class="tab-btn'),
    }
    ids = re.findall(r'\bid="([^"]+)"', text)
    tests["html_ids_unique"] = len(ids) == len(set(ids))
    tests["metric_ids_unique"] = len({metric["id"] for metric in all_metrics}) == len(all_metrics)
    if not all(tests.values()):
        failed = ", ".join(name for name, ok in tests.items() if not ok)
        raise RuntimeError(f"Fallaron controles: {failed}")

    DERIVED_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_HTML.write_text(text, encoding="utf-8")
    INDEX_HTML.write_text(text, encoding="utf-8")
    REGISTRY_JSON.write_text(json.dumps(all_metrics, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_csv(
        OVERLAPS_CSV,
        all_overlaps,
        ["metric_a", "metric_b", "risk", "relationship", "rule"],
    )
    write_csv(
        FINANCIAL_CSV,
        rows,
        ["date", "bank_real_monthly_pct", "pf_real_monthly_pct", "fintech_real_monthly_pct", "bank_pf_real_gap_pp", "fintech_tna_pct", "fintech_observed", "fintech_extended", "fintech_status"],
    )
    digest = hashlib.sha256(OUTPUT_HTML.read_bytes()).hexdigest()
    AUDIT_MD.write_text(build_audit(rows, tests, digest), encoding="utf-8")
    TESTS_JSON.write_text(json.dumps(tests, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(OUTPUT_HTML), "sha256": digest, "tests": tests}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
