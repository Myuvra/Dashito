from __future__ import annotations

import csv
import hashlib
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
SOURCE_HTML = ROOT / "data" / "dashboard_kawaii_143_pendulo_vivienda_observada.html"
OUTPUT_HTML = ROOT / "data" / "dashboard_kawaii_144_pendulo_fiscal_observado.html"
INDEX_HTML = ROOT / "index.html"
DERIVED_DIR = ROOT / "data" / "derivados" / "pendulo_poder_economico"
FISCAL_CSV = DERIVED_DIR / "fiscal_result_2002_2026.csv"
COMPONENTS_CSV = DERIVED_DIR / "fiscal_components_audit_v144.csv"
REGISTRY_JSON = DERIVED_DIR / "metric_registry.json"
OVERLAPS_CSV = DERIVED_DIR / "double_count_matrix.csv"
AUDIT_MD = DERIVED_DIR / "AUDITORIA_CAPA_FISCAL_V144.md"
TESTS_JSON = DERIVED_DIR / "TESTS_CAPA_FISCAL_V144.json"


FISCAL_COMPONENTS = [
    {
        "id": "fiscal_tax_expenditure_prudent",
        "title": "Privilegios fiscales · recorte prudente",
        "amount_ars": 1.232e12,
        "display": "$ 1,23 billones/año",
        "measure_type": "CONTRAFACTUAL TRIBUTARIO",
        "period": "2026 anual",
        "evidence": "B",
        "actor": "beneficiarios de tratamientos tributarios ↔ Estado",
        "status": "estimación auditada",
        "reading": "Recaudación potencial bajo otra regla; no es caja cobrada ni transferencia ejecutada.",
    },
    {
        "id": "fiscal_meli_documented_benefit",
        "title": "Mercado Libre · beneficios documentados",
        "amount_ars": 223.08e9,
        "display": "$ 223,08 mil M",
        "measure_type": "BENEFICIO OBSERVADO + CONVERSIÓN",
        "period": "2024–1T26 · pesos jun-2026",
        "evidence": "B/C",
        "actor": "empresa beneficiaria ↔ régimen tributario",
        "status": "piso documentado",
        "reading": "El régimen es previo al mandato; el monto documenta beneficios durante el período, no recaudación recuperable uno-a-uno.",
    },
    {
        "id": "fiscal_side_extra_credit",
        "title": "SIDE · refuerzo de crédito",
        "amount_ars": 49.3e9,
        "display": "+ $ 49,30 mil M",
        "measure_type": "CRÉDITO PRESUPUESTARIO",
        "period": "julio de 2026",
        "evidence": "A/B",
        "actor": "PEN / SIDE ↔ presupuesto",
        "status": "autorizado; ejecución no demostrada",
        "reading": "Aumento de crédito disponible: no equivale automáticamente a gasto ejecutado.",
    },
    {
        "id": "fiscal_pen_salary_catchup",
        "title": "Cúpula PEN · extra nominal anualizado",
        "amount_ars": 9.78e9,
        "display": "≈ $ 9,78 mil M/año",
        "measure_type": "ESCENARIO SALARIAL",
        "period": "escala 2026 vs congelar dic-2023",
        "evidence": "C",
        "actor": "autoridades superiores del PEN",
        "status": "anualización; no costo ejecutado observado",
        "reading": "La remuneración real todavía queda bajo dic-2023; esta diferencia nominal no prueba enriquecimiento real.",
    },
    {
        "id": "fiscal_senate_allowance_floor",
        "title": "Senado · piso del salto de dietas",
        "amount_ars": 2.2752e9,
        "display": "≥ $ 2,28 mil M/año netos",
        "measure_type": "PISO DERIVADO",
        "period": "salto aprobado en 2024",
        "evidence": "C",
        "actor": "Senado · Poder Legislativo",
        "status": "piso neto; no costo fiscal bruto",
        "reading": "Decisión del Senado, no del PEN; la base usa 72 bancas y 13 dietas.",
    },
]


NEW_METRICS = [
    {
        "id": "fiscal_meli_documented_benefit",
        "layer": "Fiscal",
        "title": "Mercado Libre · beneficios documentados",
        "measure_type": "BENEFICIO OBSERVADO + CONVERSIÓN",
        "unit": "pesos constantes de junio de 2026",
        "frequency": "acumulado documental",
        "period": "2024–1T26",
        "source_grade": "B/C",
        "transformation": "USD documentados × A3500 por período + IPC",
        "actors": "empresa beneficiaria ↔ régimen tributario",
        "economic_flow_id": "meli_tax_benefit_documented",
        "status": "integrado como piso documentado",
        "do_not_sum_with": ["fiscal_tax_expenditure", "foregone_revenue_scenario"],
        "note": "Régimen previo al mandato; no implica recaudación recuperable uno-a-uno.",
    },
    {
        "id": "fiscal_side_extra_credit",
        "layer": "Fiscal",
        "title": "SIDE · refuerzo de crédito presupuestario",
        "measure_type": "CRÉDITO PRESUPUESTARIO",
        "unit": "pesos nominales autorizados",
        "frequency": "DNU puntual",
        "period": "julio de 2026",
        "source_grade": "A/B",
        "transformation": "observado presupuestario",
        "actors": "PEN / SIDE ↔ presupuesto",
        "economic_flow_id": "side_budget_credit_authorization",
        "status": "autorizado; ejecución no demostrada",
        "do_not_sum_with": ["fiscal_tax_structure", "side_executed_spending"],
        "note": "Crédito vigente no equivale a gasto devengado o pagado.",
    },
    {
        "id": "fiscal_pen_salary_catchup",
        "layer": "Fiscal",
        "title": "Cúpula PEN · extra nominal anualizado",
        "measure_type": "ESCENARIO SALARIAL",
        "unit": "pesos nominales anualizados",
        "frequency": "escenario",
        "period": "2026 vs escala dic-2023 congelada",
        "source_grade": "C",
        "transformation": "diferencia salarial anualizada",
        "actors": "autoridades superiores del PEN",
        "economic_flow_id": "pen_salary_scale_counterfactual",
        "status": "escenario; no ejecución fiscal observada",
        "do_not_sum_with": ["fiscal_tax_structure", "public_wage_bill"],
        "note": "El salario real permanece bajo dic-2023; no prueba enriquecimiento real.",
    },
    {
        "id": "fiscal_senate_allowance_floor",
        "layer": "Fiscal",
        "title": "Senado · piso del salto de dietas",
        "measure_type": "PISO DERIVADO",
        "unit": "pesos netos anualizados",
        "frequency": "anualización",
        "period": "salto aprobado en 2024",
        "source_grade": "C",
        "transformation": "72 bancas × diferencia de dietas",
        "actors": "Senado · Poder Legislativo",
        "economic_flow_id": "senate_allowance_floor",
        "status": "piso neto; no costo fiscal bruto",
        "do_not_sum_with": ["fiscal_tax_structure", "senate_gross_payroll"],
        "note": "No se atribuye al Poder Ejecutivo.",
    },
]


NEW_OVERLAPS = [
    {
        "metric_a": "fiscal_tax_structure",
        "metric_b": "fiscal_side_extra_credit",
        "risk": "alto",
        "relationship": "resultado ejecutado neto vs autorización presupuestaria",
        "rule": "no restar un crédito autorizado del resultado sin verificar ejecución y base contable",
    },
    {
        "metric_a": "fiscal_tax_expenditure",
        "metric_b": "fiscal_meli_documented_benefit",
        "risk": "alto",
        "relationship": "contrafactual tributario anual vs beneficio empresarial documentado en otro período",
        "rule": "no sumar sin demostrar alcance no solapado, período común y misma moneda real",
    },
    {
        "metric_a": "fiscal_tax_structure",
        "metric_b": "fiscal_pen_salary_catchup",
        "risk": "alto",
        "relationship": "saldo fiscal agregado vs escenario salarial parcial",
        "rule": "el escenario no se agrega al resultado observado",
    },
    {
        "metric_a": "fiscal_pen_salary_catchup",
        "metric_b": "fiscal_senate_allowance_floor",
        "risk": "medio",
        "relationship": "actores y poderes distintos; bases nominales/netas diferentes",
        "rule": "mostrar por separado y no presentarlos como una única masa salarial pública",
    },
]


FISCAL_CSS = r'''
<style id="pendulo-fiscal-observado-v144">
#tab-pendulo .pend-fiscal-observed{border-color:#e5cd91;background:linear-gradient(145deg,rgba(255,254,248,.98),rgba(252,249,255,.98))}
.pend-fiscal-kpis{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:9px;margin-top:12px}.pend-fiscal-kpi{padding:13px;border:1px solid #ddd1e4;border-radius:16px;background:#fff}.pend-fiscal-kpi.surplus{border-color:#afd9c7;background:#f5fff9}.pend-fiscal-kpi.deficit{border-color:#e8bdce;background:#fff7fa}.pend-fiscal-kpi.partial{border-color:#e5cf98;background:#fffdf2}.pend-fiscal-kpi small{display:block;color:#806b87;font-size:7.3px;font-weight:950;letter-spacing:.035em;text-transform:uppercase}.pend-fiscal-kpi strong{display:block;margin:5px 0 4px;color:#593a66;font-size:21px;line-height:1}.pend-fiscal-kpi.surplus strong{color:#2f8063}.pend-fiscal-kpi.deficit strong{color:#a74368}.pend-fiscal-kpi.partial strong{color:#8a6822}.pend-fiscal-kpi p{margin:0;color:#725f78;font-size:8.7px;line-height:1.45}
.pend-fiscal-chart{width:100%;min-width:760px;height:445px}.pend-fiscal-plain{margin-top:12px;padding:13px 15px;border-left:5px solid #d5a03f;border-radius:14px;background:#fffdf2;color:#6f613c;font-size:10px;line-height:1.55}.pend-fiscal-plain b{color:#745817}
.pend-fiscal-components{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:9px;margin-top:12px}.pend-fiscal-component{min-width:0;padding:13px;border:1px solid #ddd1e5;border-radius:16px;background:#fff}.pend-fiscal-component.counter{border-color:#e8c3d1;background:#fff8fa}.pend-fiscal-component.budget{border-color:#e5d09b;background:#fffdf3}.pend-fiscal-component.observed{border-color:#bad5e7;background:#f7fbff}.pend-fiscal-component.scenario{border-style:dashed;background:#faf8ff}.pend-fiscal-component small{display:block;min-height:24px;color:#856f8b;font-size:7.1px;font-weight:950;line-height:1.35;text-transform:uppercase}.pend-fiscal-component strong{display:block;margin:5px 0;color:#593a67;font-size:16px;line-height:1.1}.pend-fiscal-component h4{margin:0 0 5px;color:#5c3e69;font-size:10.5px;line-height:1.3}.pend-fiscal-component p{margin:0;color:#746179;font-size:8.3px;line-height:1.45}.pend-fiscal-component .status{display:block;margin-top:7px;padding-top:6px;border-top:1px dashed #ded3e5;color:#7d6983;font-size:7.6px;font-weight:900;line-height:1.35}
.pend-fiscal-types{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:9px;margin-top:12px}.pend-fiscal-type{padding:12px;border:1px solid #ded2e6;border-radius:15px;background:#fff}.pend-fiscal-type b{display:block;color:#5a3b67;font-size:10px}.pend-fiscal-type span{display:block;margin-top:4px;color:#75627a;font-size:8.5px;line-height:1.45}
@media(max-width:1120px){.pend-fiscal-components{grid-template-columns:repeat(3,minmax(0,1fr))}.pend-fiscal-kpis{grid-template-columns:repeat(2,minmax(0,1fr))}}
@media(max-width:760px){.pend-fiscal-chart{min-width:680px;height:415px}.pend-fiscal-components{grid-template-columns:1fr 1fr}.pend-fiscal-kpis,.pend-fiscal-types{grid-template-columns:1fr 1fr}}
@media(max-width:430px){.pend-fiscal-components,.pend-fiscal-kpis,.pend-fiscal-types{grid-template-columns:1fr}.pend-fiscal-chart{min-width:640px}}
</style>
'''


FISCAL_PANEL = r'''      <div class="pend-layer-panel" data-pend-layer-panel="fiscal" role="tabpanel" hidden>
        <div class="pend-layer-stack">
          <section class="pend-card pend-hero pend-fiscal-observed">
            <div class="pend-head"><div><span class="pend-kicker">D · Estado, resultado y tratamientos diferenciales</span><h2>¿Al Estado le sobró o le faltó plata?</h2><p class="pend-sub">Resultado financiero anual del Sector Público Nacional. El gráfico usa % del PIB para comparar años; 2025 es aproximado y 2026 es parcial enero–julio.</p></div></div>
            <div class="pend-layer-question">Contribuyentes ↔ Estado ↔ receptores / beneficiarios<small>Superávit favorece el balance del Estado. No significa automáticamente que mejoró el bolsillo del hogar: puede cambiar por recursos, gastos, intereses o combinaciones distintas.</small></div>
            <div class="pend-meta-line"><span class="pend-meta flow">FLUJO · resultado financiero</span><span class="pend-meta evidence-a">fuente A · Hacienda/ONP</span><span class="pend-meta">% PIB · anual</span><span class="pend-meta">2026 parcial ene–jul</span></div>
            <div id="pendPowerFiscalKpis" class="pend-fiscal-kpis"></div>
            <div class="pend-chart-stickers"><span class="pend-chart-sticker">+ = superávit del Estado</span><span class="pend-chart-sticker warn">no equivale a “ganó el hogar”</span><span class="pend-chart-sticker">2023 = año de transición</span></div>
            <div class="pend-chart-scroll"><div id="pendPowerFiscalChart" class="pend-fiscal-chart"></div></div>
            <div class="pend-fiscal-plain"><b>En criollo:</b> en 2023 el SPN cerró con déficit de 4,4% del PIB; desde 2024 los datos muestran superávit financiero. Eso dice que el Estado recaudó más de lo que gastó —incluidos intereses— dentro de cada período. <b>No dice por sí solo quién pagó el ajuste ni quién recibió menos o más.</b></div>
            <div class="pend-links"><button class="pend-link" onclick="activateTab('tab-fiscal')">Abrir Resultado fiscal completo →</button><button class="pend-link" onclick="activateTab('tab-social')">Abrir Transferencias →</button><button class="pend-link" onclick="activateTab('tab-debt-public')">Abrir Deuda pública →</button></div>
          </section>
          <section class="pend-card">
            <div class="pend-head"><div><span class="pend-kicker">No sumar estas tarjetas</span><h3>Partidas auditadas: cada una es una clase de número distinta</h3><p class="pend-note">Sirven para identificar actores y escala. No forman una cuenta fiscal homogénea ni se agregan al resultado del gráfico.</p></div></div>
            <div id="pendPowerFiscalComponents" class="pend-fiscal-components"></div>
            <div class="pend-fiscal-types"><article class="pend-fiscal-type"><b>✓ Ejecutado / observado</b><span>Un flujo o beneficio efectivamente registrado en el período y con la cobertura indicada.</span></article><article class="pend-fiscal-type"><b>⏳ Autorizado / presupuestado</b><span>Habilita gasto, pero puede no haberse devengado ni pagado todavía.</span></article><article class="pend-fiscal-type"><b>🪞 Contrafactual / escenario</b><span>Pregunta qué ocurriría bajo otra regla; no es dinero ya disponible para repartir.</span></article></div>
            <div class="pend-gate"><span class="icon">🚧</span><div><h4>Posición fiscal neta por hogar todavía deshabilitada</h4><p>Para responder quién aporta y quién recibe en cada quintil hace falta una microsimulación compatible de impuestos, transferencias y servicios. No se reparte IVA, gasto social ni beneficios “a ojo”.</p></div></div>
            <div class="pend-links"><button class="pend-link" onclick="activateTab('tab-meli-benefits')">Abrir Privilegios fiscales →</button><button class="pend-link" onclick="activateTab('tab-casta')">Abrir La casta →</button><button class="pend-link" onclick="activateTab('tab-milei-cost')">Abrir Lo que te robó Milei →</button><button class="pend-link" onclick="activateTab('tab-wealth-contribution')">Abrir Grandes fortunas →</button></div>
          </section>
        </div>
      </div>

'''


FISCAL_SCRIPT_TEMPLATE = r'''
<script id="pendulo-fiscal-observado-script-v144">
const PEND_POWER_FISCAL_ROWS=__FISCAL_ROWS__;
const PEND_POWER_FISCAL_COMPONENTS=__FISCAL_COMPONENTS__;
const PEND_POWER_FISCAL_METRICS=__FISCAL_METRICS__;
const PEND_POWER_FISCAL_OVERLAPS=__FISCAL_OVERLAPS__;
PEND_POWER_METRICS.push(...PEND_POWER_FISCAL_METRICS);
PEND_POWER_OVERLAPS.push(...PEND_POWER_FISCAL_OVERLAPS);
const pendFiscalStructureMetric=PEND_POWER_METRICS.find(row=>row.id==='fiscal_tax_structure');
if(pendFiscalStructureMetric)Object.assign(pendFiscalStructureMetric,{title:'Resultado financiero del SPN',measure_type:'FLUJO',unit:'% del PIB y ARS nominales',frequency:'anual',period:'2002–2026 parcial',status:'integrado en la capa Fiscal',note:'Resultado agregado del Estado; no informa incidencia distributiva por hogar.'});
const pendFiscalTaxMetric=PEND_POWER_METRICS.find(row=>row.id==='fiscal_tax_expenditure');
if(pendFiscalTaxMetric)Object.assign(pendFiscalTaxMetric,{period:'recorte prudente 2026',status:'integrado como contrafactual separado',note:'No equivale a caja cobrada ni se suma a créditos presupuestarios o beneficios de otros períodos.'});
let pendPowerFiscalRendered=false;
function pendFiscalSigned(value,digits=1){const sign=value>0?'+':value<0?'−':'';return `${sign}${pendPowerFmt(Math.abs(value),digits)}%`;}
function pendFiscalComponentClass(type){if(type.includes('TRIBUTARIO'))return 'counter';if(type.includes('CRÉDITO'))return 'budget';if(type.includes('OBSERVADO'))return 'observed';return 'scenario';}
function renderPendPowerFiscal(){
 const chart=document.getElementById('pendPowerFiscalChart'),kpis=document.getElementById('pendPowerFiscalKpis'),components=document.getElementById('pendPowerFiscalComponents');
 if(!chart||!kpis||!components||!window.Plotly)return;
 const rows=PEND_POWER_FISCAL_ROWS,byYear=new Map(rows.map(r=>[r.year,r]));
 kpis.innerHTML=[2023,2024,2025,2026].map(year=>{const r=byYear.get(year),cls=r.financial_pct_gdp<0?'deficit':r.partial?'partial':'surplus',label=r.financial_pct_gdp<0?'Déficit financiero':'Superávit financiero',qualifier=r.gdp_approx?'≈ ':'';return `<article class="pend-fiscal-kpi ${cls}"><small>${year}${r.partial?' · parcial':''}</small><strong>${qualifier}${pendFiscalSigned(r.financial_pct_gdp)}</strong><p>${label}. ${r.partial?'Acumulado ene–jul; no es un año completo.':year===2023?'Año de transición: no se asigna entero a un gobierno.':'Resultado anual del SPN.'}</p></article>`}).join('');
 const visible=rows.filter(r=>r.financial_pct_gdp!=null),colors=visible.map(r=>r.partial?'#d5a03f':r.financial_pct_gdp>=0?'#48a07f':'#d45f83');
 const trace={type:'bar',x:visible.map(r=>r.date),y:visible.map(r=>r.financial_pct_gdp),customdata:visible.map(r=>[r.year,r.financial_ars_m,r.gdp_approx,r.partial||'']),marker:{color:colors,line:{color:'rgba(84,58,96,.25)',width:.6}},hovertemplate:'<b>%{customdata[0]}</b><br>Resultado financiero: <b>%{y:.2f}% del PIB</b><br>ARS nominales: %{customdata[1]:,.1f} M<br>%{customdata[3]}<extra></extra>'};
 const separators=['2007-12-10','2015-12-10','2019-12-10','2023-12-10'];
 const shapes=[{type:'line',xref:'paper',x0:0,x1:1,y0:0,y1:0,line:{color:'#6f5d76',width:1.2}},...separators.map(x=>({type:'line',x0:x,x1:x,yref:'paper',y0:0,y1:1,line:{color:'rgba(132,102,145,.42)',width:1,dash:'dot'}}))];
 const annotations=[{x:'2026-07-31',y:byYear.get(2026).financial_pct_gdp,text:'2026 parcial<br>ene–jul',showarrow:true,arrowhead:2,ax:-28,ay:-45,font:{size:8,color:'#7d601d'},bgcolor:'rgba(255,253,242,.94)'},{xref:'paper',x:1,y:0,text:'0 = equilibrio financiero',showarrow:false,xanchor:'right',yshift:10,font:{size:8,color:'#806a87'}}];
 const layout={title:{text:'Resultado financiero del SPN · porcentaje del PIB',font:{size:13,color:'#5d4169'}},paper_bgcolor:'rgba(0,0,0,0)',plot_bgcolor:'rgba(255,255,255,.74)',font:{family:'Nunito, Arial, sans-serif',color:'#654f6c',size:10},margin:{l:62,r:26,t:70,b:58},hovermode:'closest',xaxis:{type:'date',range:['2003-06-01','2027-01-01'],gridcolor:'#eee5f2',tickformat:'%Y',dtick:'M24',automargin:true},yaxis:{title:'% del PIB',ticksuffix:'%',gridcolor:'#eadff0',zeroline:false,automargin:true},showlegend:false,shapes,annotations};
 Plotly.react(chart,[trace],layout,{responsive:true,displaylogo:false,scrollZoom:false,modeBarButtonsToRemove:['lasso2d','select2d']});
 components.innerHTML=PEND_POWER_FISCAL_COMPONENTS.map(r=>`<article class="pend-fiscal-component ${pendFiscalComponentClass(r.measure_type)}"><small>${r.measure_type} · evidencia ${r.evidence}</small><h4>${r.title}</h4><strong>${r.display}</strong><p>${r.reading}</p><span class="status">${r.period}<br>${r.status}<br>Actor: ${r.actor}</span></article>`).join('');
 pendPowerFiscalRendered=true;
}
window.addEventListener('resize',()=>{if(pendPowerFiscalRendered){const el=document.getElementById('pendPowerFiscalChart');if(el&&window.Plotly)Plotly.Plots.resize(el);}});
</script>

'''


def extract_json_const(text: str, name: str) -> list[dict] | dict:
    match = re.search(rf"^const {re.escape(name)}\s*=\s*(\[.*?\]|\{{.*?\}});\s*$", text, re.MULTILINE)
    if not match:
        raise RuntimeError(f"No se encontró {name}")
    return json.loads(match.group(1))


def parse_fiscal_rows(text: str) -> list[dict]:
    match = re.search(r"const fiscalAnnualData=\{\s*(.*?)\n\};", text, re.DOTALL)
    if not match:
        raise RuntimeError("No se encontró fiscalAnnualData")
    rows: list[dict] = []
    for year_text, body in re.findall(r"^\s*(\d{4}):\{([^}]*)\},?\s*$", match.group(1), re.MULTILINE):
        financial_match = re.search(r"financial:([-\d.]+)", body)
        gdp_match = re.search(r"gdp:(null|[-\d.]+)", body)
        if not financial_match or not gdp_match:
            raise RuntimeError(f"Fila fiscal incompleta: {year_text}")
        partial_match = re.search(r"partial:'([^']+)'", body)
        source_match = re.search(r"source:'([^']+)'", body)
        year = int(year_text)
        gdp = None if gdp_match.group(1) == "null" else float(gdp_match.group(1))
        rows.append(
            {
                "year": year,
                "date": f"{year}-07-31" if partial_match else f"{year}-12-31",
                "financial_ars_m": float(financial_match.group(1)),
                "financial_pct_gdp": gdp,
                "gdp_approx": "gdpApprox:true" in body,
                "partial": None if not partial_match else partial_match.group(1),
                "source": source_match.group(1) if source_match else "serie oficial",
                "transition_year": year in {2003, 2007, 2015, 2019, 2023},
            }
        )
    rows.sort(key=lambda row: row["year"])
    return rows


def read_csv(path: Path) -> list[dict]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def make_audit(rows: list[dict], digest: str, tests: dict[str, bool]) -> str:
    by_year = {row["year"]: row for row in rows}
    results = "\n".join(f"- {name}: {'PASS' if ok else 'FAIL'}" for name, ok in tests.items())
    component_lines = "\n".join(
        f"- {row['title']}: {row['display']} · {row['measure_type']} · {row['period']} · evidencia {row['evidence']}."
        for row in FISCAL_COMPONENTS
    )
    return f"""# Auditoría · Péndulo fiscal observado v144

Fecha editorial: 2026-08-21  
Archivo: `data/dashboard_kawaii_144_pendulo_fiscal_observado.html`  
SHA-256: `{digest}`

## Resultado financiero del SPN

La visualización principal reutiliza la serie fiscal ya archivada en el dashboard. Para comparar años se privilegia el resultado financiero como porcentaje del PIB.

- 2023: {by_year[2023]['financial_pct_gdp']:.6f}% del PIB; año de transición.
- 2024: {by_year[2024]['financial_pct_gdp']:.6f}% del PIB.
- 2025: ≈ {by_year[2025]['financial_pct_gdp']:.6f}% del PIB.
- 2026: ≈ {by_year[2026]['financial_pct_gdp']:.6f}% del PIB; acumulado enero–julio.

Superávit indica un saldo favorable para el balance estatal, no una mejora automática del bienestar de los hogares. La serie agregada no identifica incidencia por quintil.

## Partidas vinculadas

{component_lines}

Estas tarjetas no se suman entre sí ni al resultado fiscal. Mezclan un contrafactual tributario, un beneficio documentado con conversión, una autorización presupuestaria y dos escenarios/pisos salariales de poderes distintos.

## Antidoble conteo

- Crédito presupuestario no equivale a ejecución.
- Gasto tributario no equivale a recaudación recuperable uno-a-uno.
- Resultado fiscal neto ya agrega recursos y gastos del universo cubierto.
- Períodos, monedas y actores deben homogeneizarse antes de cualquier escenario conjunto.

## Controles

{results}
"""


def main() -> None:
    source = SOURCE_HTML.read_text(encoding="utf-8")
    if 'id="pendulo-fiscal-observado-v144"' in source:
        raise RuntimeError("La fuente v143 ya contiene v144")
    rows = parse_fiscal_rows(source)
    metrics = extract_json_const(source, "PEND_POWER_METRICS")
    overlaps = read_csv(OVERLAPS_CSV)

    structure_metric = next(metric for metric in metrics if metric["id"] == "fiscal_tax_structure")
    structure_metric.update(
        {
            "title": "Resultado financiero del SPN",
            "measure_type": "FLUJO",
            "unit": "% del PIB y ARS nominales",
            "frequency": "anual",
            "period": "2002–2026 parcial",
            "status": "integrado en la capa Fiscal",
            "note": "Resultado agregado del Estado; no informa incidencia distributiva por hogar.",
        }
    )
    tax_metric = next(metric for metric in metrics if metric["id"] == "fiscal_tax_expenditure")
    tax_metric.update(
        {
            "period": "recorte prudente 2026",
            "status": "integrado como contrafactual separado",
            "note": "No equivale a caja cobrada ni se suma a créditos presupuestarios o beneficios de otros períodos.",
        }
    )
    all_metrics = metrics + NEW_METRICS
    all_overlaps = overlaps + NEW_OVERLAPS

    text = source
    css_marker = '<style id="rutas-publico-privado-v139">'
    if css_marker not in text:
        raise RuntimeError("No se encontró marcador CSS")
    text = text.replace(css_marker, FISCAL_CSS + "\n" + css_marker, 1)

    fiscal_start = text.index('      <div class="pend-layer-panel" data-pend-layer-panel="fiscal"')
    fiscal_end = text.index('      <div class="pend-layer-panel" data-pend-layer-panel="assets"', fiscal_start)
    text = text[:fiscal_start] + FISCAL_PANEL + text[fiscal_end:]

    script = (
        FISCAL_SCRIPT_TEMPLATE.replace("__FISCAL_ROWS__", json.dumps(rows, ensure_ascii=False, separators=(",", ":")))
        .replace("__FISCAL_COMPONENTS__", json.dumps(FISCAL_COMPONENTS, ensure_ascii=False, separators=(",", ":")))
        .replace("__FISCAL_METRICS__", json.dumps(NEW_METRICS, ensure_ascii=False, separators=(",", ":")))
        .replace("__FISCAL_OVERLAPS__", json.dumps(NEW_OVERLAPS, ensure_ascii=False, separators=(",", ":")))
    )
    script_marker = '<script id="rutas-publico-privado-script-v139">'
    if script_marker not in text:
        raise RuntimeError("No se encontró marcador JS")
    text = text.replace(script_marker, script + script_marker, 1)
    activation = "if(layer==='housing')requestAnimationFrame(renderPendPowerHousing);"
    if activation not in text:
        raise RuntimeError("No se encontró activación de Vivienda")
    text = text.replace(activation, activation + "\n if(layer==='fiscal')requestAnimationFrame(renderPendPowerFiscal);", 1)

    by_year = {row["year"]: row for row in rows}
    tests = {
        "fiscal_coverage_2002_2026": len(rows) == 25 and rows[0]["year"] == 2002 and rows[-1]["year"] == 2026,
        "fiscal_2023_value": abs(by_year[2023]["financial_pct_gdp"] - (-4.3982489198)) < 1e-10,
        "fiscal_2024_value": abs(by_year[2024]["financial_pct_gdp"] - 0.3022360912) < 1e-10,
        "fiscal_2025_is_approx": by_year[2025]["gdp_approx"] and by_year[2025]["financial_pct_gdp"] == 0.2,
        "fiscal_2026_is_partial": by_year[2026]["partial"] == "ene–jul" and by_year[2026]["financial_pct_gdp"] == 0.1,
        "component_measure_types_distinct": len({row["measure_type"] for row in FISCAL_COMPONENTS}) == len(FISCAL_COMPONENTS),
        "components_not_summed": "No sumar estas tarjetas" in text and "No forman una cuenta fiscal homogénea" in text,
        "household_incidence_not_inferred": "Posición fiscal neta por hogar todavía deshabilitada" in text,
        "fiscal_renderer_connected": "renderPendPowerFiscal" in text and "if(layer==='fiscal')" in text,
        "salary_bug_stays_fixed": text.count("function pendPowerChange(") == 1 and "function pendPowerAssetChange(value)" in text,
        "finance_preserved": 'id="pendPowerFinanceRealChart"' in text,
        "housing_preserved": 'id="pendPowerHousingChart"' in text,
        "assets_preserved": 'id="pendPowerAssetChart"' in text,
        "six_layers_preserved": text.count('class="pend-layer-btn') == 6,
        "tab_count_preserved": text.count('class="tab-btn') == source.count('class="tab-btn'),
        "metric_ids_unique": len({row["id"] for row in all_metrics}) == len(all_metrics),
    }
    ids = re.findall(r'\bid="([^"]+)"', text)
    tests["html_ids_unique"] = len(ids) == len(set(ids))
    if not all(tests.values()):
        failed = ", ".join(name for name, ok in tests.items() if not ok)
        raise RuntimeError(f"Fallaron controles: {failed}")

    DERIVED_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_HTML.write_text(text, encoding="utf-8")
    INDEX_HTML.write_text(text, encoding="utf-8")
    REGISTRY_JSON.write_text(json.dumps(all_metrics, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_csv(FISCAL_CSV, rows, ["year", "date", "financial_ars_m", "financial_pct_gdp", "gdp_approx", "partial", "source", "transition_year"])
    write_csv(COMPONENTS_CSV, FISCAL_COMPONENTS, ["id", "title", "amount_ars", "display", "measure_type", "period", "evidence", "actor", "status", "reading"])
    write_csv(OVERLAPS_CSV, all_overlaps, ["metric_a", "metric_b", "risk", "relationship", "rule"])
    digest = hashlib.sha256(OUTPUT_HTML.read_bytes()).hexdigest()
    AUDIT_MD.write_text(make_audit(rows, digest, tests), encoding="utf-8")
    TESTS_JSON.write_text(json.dumps(tests, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(OUTPUT_HTML), "sha256": digest, "tests": tests}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
