from __future__ import annotations

import csv
import hashlib
import json
import re
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
SOURCE_HTML = ROOT / "data" / "dashboard_kawaii_144_pendulo_fiscal_observado.html"
OUTPUT_HTML = ROOT / "data" / "dashboard_kawaii_145_pendulo_activos_ampliado.html"
INDEX_HTML = ROOT / "index.html"
DERIVED_DIR = ROOT / "data" / "derivados" / "pendulo_poder_economico"
CER_SOURCE = ROOT / "data" / "fuentes" / "tasas" / "bcra" / "tas5_ser.txt"
ASSET_CSV = DERIVED_DIR / "asset_returns_dec2023.csv"
ASSET_EXPANDED_CSV = DERIVED_DIR / "asset_returns_with_cer_dec2023.csv"
CER_MONTHLY_CSV = DERIVED_DIR / "cer_month_end_2023_2026.csv"
METRIC_REGISTRY = DERIVED_DIR / "metric_registry.json"
OVERLAP_CSV = DERIVED_DIR / "double_count_matrix.csv"
AUDIT_MD = DERIVED_DIR / "AUDITORIA_CAPA_ACTIVOS_V145.md"
TESTS_JSON = DERIVED_DIR / "TESTS_CAPA_ACTIVOS_V145.json"


NEW_METRIC = {
    "id": "asset_cer_reference",
    "layer": "Activos",
    "title": "Capital indexado por CER · referencia",
    "measure_type": "RENDIMIENTO HIPOTÉTICO",
    "unit": "índice real rebaseable; 100 en la fecha de entrada elegida",
    "frequency": "mensual desde serie diaria",
    "period": "dic-2023–jul-2026",
    "source_grade": "B",
    "transformation": "CER fin de mes deflactado por IPC mensual",
    "actors": "persona con acceso a un contrato o instrumento ajustable por CER",
    "economic_flow_id": "conditional_cer_linked_principal_return",
    "status": "integrado como referencia, no como activo autónomo",
    "do_not_sum_with": ["cer_linked_bond_total_return", "household_net_worth_change"],
    "note": "El CER no se compra por sí solo. No incorpora cupón, precio de mercado, comisiones ni plazo de un instrumento concreto; el rezago del CER vuelve sensible el resultado a la fecha de entrada.",
}

NEW_OVERLAPS = [
    {
        "metric_a": "asset_cer_reference",
        "metric_b": "cer_linked_bond_total_return",
        "risk": "alto",
        "relationship": "coeficiente de ajuste vs retorno total de un título con precio y cupón",
        "rule": "no presentar CER como si fuera la cotización o el retorno de un bono",
    },
    {
        "metric_a": "asset_cer_reference",
        "metric_b": "household_net_worth_change",
        "risk": "alto",
        "relationship": "rendimiento condicional vs patrimonio efectivamente poseído",
        "rule": "no inferir riqueza sin cantidades, deuda, propiedad y acceso",
    },
    {
        "metric_a": "asset_usd_a3500_real",
        "metric_b": "retail_dollar_total_return",
        "risk": "alto",
        "relationship": "referencia mayorista A3500 vs precio y costos de acceso minorista",
        "rule": "no tratar A3500 como una operación minorista efectivamente realizable",
    },
]


ASSET_CSS = r'''
<style id="pendulo-poder-assets-v145-style">
.pend-asset-controls{display:flex;align-items:flex-end;justify-content:space-between;gap:12px;flex-wrap:wrap;margin:13px 0 4px;padding:12px 14px;border:1px solid #ded0e8;border-radius:16px;background:linear-gradient(135deg,#fbf7ff,#fffdf6)}
.pend-asset-controls label{display:grid;gap:5px;color:#62456f;font-size:8px;font-weight:950;text-transform:uppercase;letter-spacing:.04em}.pend-asset-controls select{min-width:210px;padding:9px 12px;border:1px solid #d4c1e0;border-radius:12px;background:#fff;color:#563b63;font:800 10px Nunito,Arial,sans-serif}.pend-asset-controls p{max-width:570px;margin:0;color:#79667f;font-size:9px;line-height:1.5}
.pend-asset-summary.v145{grid-template-columns:repeat(5,minmax(0,1fr))}.pend-asset-kpi.reference{border-style:dashed;background:#fbf9ff}.pend-asset-kpi .asset-access{display:block;margin-top:7px;padding-top:7px;border-top:1px solid #eee5f2;color:#8a748f;font-size:7.7px;line-height:1.35}
.pend-asset-plain{margin-top:12px;padding:13px 15px;border-left:4px solid #7f61b7;border-radius:13px;background:#f8f4ff;color:#654f6e;font-size:9.6px;line-height:1.55}.pend-asset-plain b{color:#51335f}
.pend-asset-access-grid{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:9px;margin-top:12px}.pend-asset-access-card{padding:12px;border:1px solid #ded2e6;border-radius:15px;background:#fff}.pend-asset-access-card small{display:block;color:#8c7691;font-size:7.2px;font-weight:950;text-transform:uppercase}.pend-asset-access-card b{display:block;margin:5px 0;color:#5c3e69;font-size:10px}.pend-asset-access-card p{margin:0;color:#77627d;font-size:8.2px;line-height:1.45}.pend-asset-access-card .access-verdict{display:inline-block;margin-top:7px;padding:3px 7px;border-radius:999px;background:#f3edf7;color:#6e527a;font-size:7px;font-weight:950;text-transform:uppercase}.pend-asset-access-card .access-verdict.warn{background:#fff2e4;color:#8b6227}.pend-asset-access-card .access-verdict.no{background:#fff0f5;color:#984b6b}
.pend-asset-sensitivity{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:9px;margin-top:12px}.pend-asset-sens-card{padding:11px;border:1px solid #ded2e6;border-radius:15px;background:#fff}.pend-asset-sens-card b{display:block;color:#5c3d69;font-size:10px}.pend-asset-sens-card small{display:block;margin:2px 0 7px;color:#88738e;font-size:7.4px}.pend-asset-sens-card span{display:block;color:#705a77;font-size:8px;line-height:1.45}.pend-asset-sens-card strong{color:#5f45a0}.pend-asset-warning{margin-top:11px;padding:12px 14px;border:1px solid #f0c6a2;border-radius:15px;background:#fff8ef;color:#765a3b;font-size:9px;line-height:1.55}
@media(max-width:1150px){.pend-asset-summary.v145,.pend-asset-access-grid{grid-template-columns:repeat(3,minmax(0,1fr))}}
@media(max-width:760px){.pend-asset-summary.v145,.pend-asset-access-grid,.pend-asset-sensitivity{grid-template-columns:1fr 1fr}.pend-asset-controls{align-items:stretch}.pend-asset-controls label,.pend-asset-controls select{width:100%}.pend-asset-chart{min-width:760px}}
@media(max-width:430px){.pend-asset-summary.v145,.pend-asset-access-grid,.pend-asset-sensitivity{grid-template-columns:1fr}.pend-asset-controls select{min-width:0}.pend-asset-chart{min-width:720px}}
</style>
'''


ASSET_PANEL = r'''
      <div class="pend-layer-panel" data-pend-layer-panel="assets" role="tabpanel" hidden>
        <div class="pend-layer-stack">
          <section class="pend-card pend-hero pend-assets-v145">
            <div class="pend-head"><div><span class="pend-kicker">E · La ventaja de ya tener capital</span><h2>Si ya tenías $100 disponibles, ¿qué alternativas defendieron su poder de compra?</h2><p class="pend-sub">Comparación condicional a poder entrar y sostener cada alternativa. No describe el patrimonio observado de los hogares ni supone que todos podían operar al mismo precio.</p></div></div>
            <div class="pend-layer-question">Tener ingreso ↔ poder ahorrar ↔ poder acceder a un activo<small>Son tres escalones distintos. Un rendimiento alto sólo beneficia a quien podía inmovilizar dinero, abrir una cuenta u operar el instrumento correspondiente.</small></div>
            <div class="pend-meta-line"><span class="pend-meta scenario">RENDIMIENTO HIPOTÉTICO</span><span class="pend-meta evidence-b">fuente A/B · cálculo reproducible</span><span class="pend-meta">base de entrada seleccionable</span><span class="pend-meta">sin patrimonio inferido</span></div>
            <div class="pend-asset-controls"><label>Fecha hipotética de entrada<select id="pendPowerAssetBase"><option value="2023-12-01">Diciembre de 2023</option><option value="2024-03-01">Marzo de 2024</option><option value="2024-12-01">Diciembre de 2024</option><option value="2025-12-01">Diciembre de 2025</option></select></label><p><b>Mové la base:</b> cada curva vuelve a 100 en el mes elegido. Así se ve que el resultado depende también de cuándo se podía entrar, especialmente en CER por su rezago frente al IPC.</p></div>
            <div class="pend-chart-stickers"><span class="pend-chart-sticker warn">CER = coeficiente, no bono</span><span class="pend-chart-sticker">A3500 = referencia mayorista</span><span class="pend-chart-sticker">PF = renovación promedio hipotética</span><span class="pend-chart-sticker warn">salario = ingreso, no activo</span></div>
            <div class="pend-chart-scroll"><div id="pendPowerAssetChart" class="pend-asset-chart"></div></div>
            <div id="pendPowerAssetSummary" class="pend-asset-summary v145"></div>
            <div id="pendPowerAssetReading" class="pend-asset-plain"></div>
          </section>
          <section class="pend-card">
            <div class="pend-head"><div><span class="pend-kicker">La parte que una curva sola no cuenta</span><h3>Antes del rendimiento estaba la barrera de acceso</h3><p class="pend-note">Precio observado y posibilidad efectiva de invertir son preguntas diferentes.</p></div></div>
            <div class="pend-asset-access-grid"><article class="pend-asset-access-card"><small>EFECTIVO · ACTIVO LÍQUIDO</small><b>Pesos sin remunerar</b><p>Acceso inmediato, pero queda totalmente expuesto a la inflación.</p><span class="access-verdict">acceso amplio</span></article><article class="pend-asset-access-card"><small>DEPÓSITO · ESCENARIO B</small><b>Plazo fijo tradicional</b><p>Requiere cuenta bancaria, saldo inmovilizable y renovación mensual. Usa una tasa promedio, no la oferta individual.</p><span class="access-verdict warn">acceso condicionado</span></article><article class="pend-asset-access-card"><small>REFERENCIA CAMBIARIA · A</small><b>Dólar A3500</b><p>Es un precio mayorista de referencia. No incorpora spread, impuestos, límites ni precio minorista.</p><span class="access-verdict no">no operable así por el hogar</span></article><article class="pend-asset-access-card"><small>COEFICIENTE · B</small><b>Principal ajustado por CER</b><p>El CER no se compra solo: sirve para contratos e instrumentos indexados. Acá no hay cupón, cotización ni comisión.</p><span class="access-verdict warn">acceso vía otro instrumento</span></article><article class="pend-asset-access-card"><small>REFERENCIA DE INGRESO · A</small><b>Salario real</b><p>No es capital invertido. Aparece para comparar la película de quien dependía del ingreso corriente.</p><span class="access-verdict no">no es activo</span></article></div>
          </section>
          <section class="pend-card">
            <div class="pend-head"><div><span class="pend-kicker">Sensibilidad</span><h3>El punto de entrada cambia la película</h3><p class="pend-note">Índice final de cada alternativa si 100 se fija en meses distintos. Es una prueba de robustez, no cuatro carteras reales.</p></div></div>
            <div id="pendPowerAssetSensitivity" class="pend-asset-sensitivity"></div>
            <div class="pend-asset-warning"><b>Por qué CER puede aparecer muy arriba desde diciembre de 2023:</b> el IPC incorporó el shock de diciembre en ese mismo mes, mientras el CER lo trasladó con rezago. Entrar antes de ese ajuste genera una ventaja de fecha. No debe leerse como “CER paga 29% real asegurado” ni extrapolarse a cualquier momento.</div>
          </section>
          <section class="pend-card">
            <div class="pend-head"><div><h3>Qué sigue afuera —a propósito</h3><p class="pend-note">No agregamos una línea sólo porque exista una cotización.</p></div></div>
            <div class="pend-asset-pending"><div><b>Acciones / Merval</b>Falta una serie de retorno total reproducible, con dividendos y costos; un índice de precios solo no responde la misma pregunta.</div><div><b>Bonos</b>Precio, cupón, reinversión, duración y default cambian el resultado. CER solo no reemplaza el retorno total de un título.</div><div><b>Inmuebles</b>Faltan renta, gastos, vacancia, costos de entrada/salida y cobertura geográfica homogénea.</div><div><b>Patrimonio de hogares</b>No se infiere desde precios: requiere cantidades, deuda y propiedad efectiva por grupo social.</div></div>
            <div class="pend-links"><button class="pend-link" onclick="activateTab('tab-power')">Abrir Salarios reales →</button><button class="pend-link" onclick="activateTab('tab-bcra')">Abrir Dólar y tasas →</button><button class="pend-link" onclick="activateTab('tab-housing')">Abrir Vivienda →</button></div>
          </section>
        </div>
      </div>
'''


ASSET_JS = r'''
let pendPowerAssetRendered=false;
let pendPowerAssetBase='2023-12-01';
const PEND_POWER_ASSET_BASE_LABELS={'2023-12-01':'dic-2023','2024-03-01':'mar-2024','2024-12-01':'dic-2024','2025-12-01':'dic-2025'};
function pendPowerFmt(value,digits=2){return Number(value).toLocaleString('es-AR',{minimumFractionDigits:digits,maximumFractionDigits:digits})}
function pendPowerMoney(value){const sign=value>0?'+':value<0?'−':'';return `${sign}$ ${pendPowerFmt(Math.abs(value)/1e12,2)} B`}
function pendPowerAssetChange(value){const delta=value-100,sign=delta>0?'+':delta<0?'−':'';return `${sign}${pendPowerFmt(Math.abs(delta),1)}% real`}
function pendPowerLast(rows,key){for(let i=rows.length-1;i>=0;i--)if(rows[i][key]!=null)return rows[i];return null}
function renderPendPowerFinance(){
 const root=document.getElementById('pendPowerFinanceKpis');if(!root||typeof ratesMoneySummary==='undefined')return;
 const d=ratesMoneySummary.diferencial;
 const cards=[
  ['Crédito bancario',d.impacto_hogar_banco,'Deudores','Empeoró respecto de la ventana espejo.','financial_bank_window_delta'],
  ['Fintech / PNFC',d.impacto_hogar_fintech,'Deudores fintech','Empeoró; incluye cinco meses estimados.','financial_fintech_window_delta'],
  ['Plazo fijo',d.impacto_hogar_pf,'Ahorristas','Mejoró y compensó las dos patas de crédito.','financial_pf_window_delta'],
  ['Balance ampliado',d.impacto_hogar_total_ampliado,'Universos distintos','Mejoró en conjunto; no todos ganaron.','financial_expanded_balance_delta']
 ];
 root.innerHTML=cards.map(([title,value,who,reading,id])=>`<article class="pend-power-metric ${value>0?'good':value<0?'bad':'neutral'}" data-metric-id="${id}"><small>CONTRAFACTUAL · diferencial</small><strong>${pendPowerMoney(value)}</strong><p><b>${title}:</b> ${reading}</p><span class="perspective">Perspectiva: ${who} · + mejora / − empeora</span></article>`).join('');
}
function pendPowerAssetRebased(baseDate){
 const start=Math.max(0,PEND_POWER_ASSETS.findIndex(r=>r.date===baseDate));
 const raw=PEND_POWER_ASSETS.slice(start),base=PEND_POWER_ASSETS[start];
 const keys=['cash_real','pf_real','usd_a3500_real','cer_real_reference','salary_real_reference'];
 return raw.map(row=>{const copy={...row};keys.forEach(key=>{copy[key]=row[key]==null||base[key]==null?null:100*row[key]/base[key]});return copy});
}
function pendPowerAssetFinal(rows,key){const row=pendPowerLast(rows,key);return row?{row,value:row[key]}:null}
function pendPowerAssetSensitivity(){
 const root=document.getElementById('pendPowerAssetSensitivity');if(!root)return;
 root.innerHTML=Object.keys(PEND_POWER_ASSET_BASE_LABELS).map(base=>{const rows=pendPowerAssetRebased(base),cer=pendPowerAssetFinal(rows,'cer_real_reference'),pf=pendPowerAssetFinal(rows,'pf_real'),usd=pendPowerAssetFinal(rows,'usd_a3500_real');return `<article class="pend-asset-sens-card"><b>Entrada: ${PEND_POWER_ASSET_BASE_LABELS[base]}</b><small>índice final · base 100</small><span>CER referencia: <strong>${pendPowerFmt(cer.value,1)}</strong></span><span>Plazo fijo: <strong>${pendPowerFmt(pf.value,1)}</strong></span><span>Dólar A3500: <strong>${pendPowerFmt(usd.value,1)}</strong></span></article>`}).join('');
}
function renderPendPowerAssets(){
 const chart=document.getElementById('pendPowerAssetChart');if(!chart||!window.Plotly)return;
 const rows=pendPowerAssetRebased(pendPowerAssetBase),x=rows.map(r=>r.date),baseLabel=PEND_POWER_ASSET_BASE_LABELS[pendPowerAssetBase];
 const traces=[
  {x,y:rows.map(r=>r.cash_real),name:'Efectivo sin remunerar',mode:'lines',line:{color:'#d05d83',width:3,dash:'dot'},hovertemplate:'<b>%{x|%b %Y}</b><br>Efectivo real: %{y:.1f}<br>Acceso amplio; sin rendimiento<extra></extra>'},
  {x,y:rows.map(r=>r.pf_real),name:'Plazo fijo renovado',mode:'lines+markers',line:{color:'#49a17e',width:3},marker:{size:4},hovertemplate:'<b>%{x|%b %Y}</b><br>PF real acumulado: %{y:.1f}<br>Renovación mensual hipotética<extra></extra>'},
  {x,y:rows.map(r=>r.usd_a3500_real),name:'Dólar mayorista A3500',mode:'lines+markers',line:{color:'#d09335',width:3},marker:{size:4},hovertemplate:'<b>%{x|%b %Y}</b><br>A3500 real: %{y:.1f}<br>Referencia mayorista, no precio minorista<extra></extra>'},
  {x,y:rows.map(r=>r.cer_real_reference),name:'Principal ajustado por CER · referencia',mode:'lines+markers',line:{color:'#3f8eae',width:3},marker:{size:4},hovertemplate:'<b>%{x|%b %Y}</b><br>CER real: %{y:.1f}<br>Coeficiente; no bono ni depósito concreto<extra></extra>'},
  {x,y:rows.map(r=>r.salary_real_reference),name:'Salario real · referencia',mode:'lines',line:{color:'#7357b5',width:3,dash:'dash'},hovertemplate:'<b>%{x|%b %Y}</b><br>Salario real: %{y:.1f}<br>Ingreso, no activo<extra></extra>'}
 ];
 const layout={title:{text:`Poder de compra real · entrada ${baseLabel} = 100`,font:{size:13,color:'#5d4169'}},paper_bgcolor:'rgba(0,0,0,0)',plot_bgcolor:'rgba(255,255,255,.72)',font:{family:'Nunito, Arial, sans-serif',color:'#654f6c',size:10},margin:{l:58,r:22,t:76,b:55},hovermode:'x unified',xaxis:{type:'date',gridcolor:'#eee5f2',tickformat:'%b<br>%Y',dtick:'M3',automargin:true},yaxis:{title:'índice real',gridcolor:'#eadff0',zeroline:false,automargin:true},legend:{orientation:'h',y:1.19,x:0,font:{size:8.6}},shapes:[{type:'line',xref:'paper',x0:0,x1:1,y0:100,y1:100,line:{color:'#8c7994',dash:'dot',width:1.4}}],annotations:[{xref:'paper',yref:'y',x:1,y:100,text:'100 = conserva poder de compra desde la entrada',showarrow:false,xanchor:'right',yshift:10,font:{size:8,color:'#806b87'}}]};
 Plotly.react(chart,traces,layout,{responsive:true,displaylogo:false,scrollZoom:false,modeBarButtonsToRemove:['lasso2d','select2d']});pendPowerAssetRendered=true;
 const summary=document.getElementById('pendPowerAssetSummary');
 const defs=[['cash_real','Efectivo','Pesos sin remunerar','acceso amplio'],['pf_real','Plazo fijo','Renovación promedio','cuenta + inmovilización'],['usd_a3500_real','Dólar A3500','Referencia mayorista','no operable así por hogar'],['cer_real_reference','CER referencia','Principal indexado, sin cupón','acceso vía instrumento'],['salary_real_reference','Salario real','Ingreso; no activo','sin capital inicial']];
 if(summary)summary.innerHTML=defs.map(([key,title,note,access])=>{const item=pendPowerAssetFinal(rows,key);return `<article class="pend-asset-kpi ${key==='salary_real_reference'||key==='cer_real_reference'?'reference':''}"><small>${title}</small><strong>${pendPowerFmt(item.value,1)}</strong><span>${pendPowerAssetChange(item.value)} desde ${baseLabel} · ${note} · ${item.row.date.slice(0,7)}</span><em class="asset-access">Acceso: ${access}</em></article>`}).join('');
 const investable=['cash_real','pf_real','usd_a3500_real','cer_real_reference'].map(key=>({key,...pendPowerAssetFinal(rows,key)})).sort((a,b)=>b.value-a.value),best=investable[0],worst=investable[investable.length-1],names={cash_real:'efectivo',pf_real:'plazo fijo',usd_a3500_real:'A3500 mayorista',cer_real_reference:'referencia CER'};
 const reading=document.getElementById('pendPowerAssetReading');if(reading)reading.innerHTML=`<b>En criollo:</b> para quien podía entrar en ${baseLabel}, la alternativa que termina más arriba es <b>${names[best.key]} (${pendPowerFmt(best.value,1)})</b> y la que queda más abajo es <b>${names[worst.key]} (${pendPowerFmt(worst.value,1)})</b>. Esto compara rendimientos condicionales, no cuántas personas accedieron ni cuánto patrimonio tenían. Cambiá la fecha de entrada para comprobar cuánto depende la conclusión del momento elegido.`;
 pendPowerAssetSensitivity();
}
document.getElementById('pendPowerAssetBase')?.addEventListener('change',event=>{pendPowerAssetBase=event.target.value;renderPendPowerAssets()});
window.addEventListener('resize',()=>{if(pendPowerAssetRendered){const el=document.getElementById('pendPowerAssetChart');if(el&&window.Plotly)Plotly.Plots.resize(el)}});
'''


def extract_json_line(text: str, name: str) -> list | dict:
    match = re.search(rf"^const {re.escape(name)}=(.+);$", text, re.MULTILINE)
    if not match:
        raise RuntimeError(f"No se encontró {name}")
    return json.loads(match.group(1))


def replace_json_line(text: str, name: str, value: list | dict) -> str:
    payload = json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    text, count = re.subn(rf"^const {re.escape(name)}=.+;$", f"const {name}={payload};", text, count=1, flags=re.MULTILINE)
    if count != 1:
        raise RuntimeError(f"No se pudo reemplazar {name}")
    return text


def read_cer_month_end() -> dict[str, dict]:
    result: dict[str, dict] = {}
    with CER_SOURCE.open(encoding="latin-1", newline="") as handle:
        for source_row in csv.reader(handle, delimiter=";"):
            if len(source_row) != 3:
                continue
            code, date_text, value_text = source_row
            if code != "3540":
                continue
            date = datetime.strptime(date_text, "%d/%m/%Y")
            month = date.strftime("%Y-%m")
            if not "2023-12" <= month <= "2026-07":
                continue
            previous = result.get(month)
            if previous is None or date > previous["date"]:
                result[month] = {"date": date, "value": float(value_text)}
    return result


def build_asset_rows() -> tuple[list[dict], list[dict]]:
    with ASSET_CSV.open(encoding="utf-8-sig", newline="") as handle:
        original = list(csv.DictReader(handle))
    cer = read_cer_month_end()
    if set(row["date"][:7] for row in original) - set(cer):
        raise RuntimeError("Faltan meses CER para la ventana de activos")
    base_cer = cer["2023-12"]["value"]
    base_ipc = float(original[0]["ipc_level"])
    rows: list[dict] = []
    monthly: list[dict] = []
    for row in original:
        month = row["date"][:7]
        cer_item = cer[month]
        ipc = float(row["ipc_level"])
        converted: dict = {}
        for key, value in row.items():
            if key == "date":
                converted[key] = value
            elif value == "":
                converted[key] = None
            else:
                converted[key] = float(value)
        converted["cer_level"] = cer_item["value"]
        converted["cer_observation_date"] = cer_item["date"].strftime("%Y-%m-%d")
        converted["cer_real_reference"] = 100 * (cer_item["value"] / base_cer) * (base_ipc / ipc)
        rows.append(converted)
        monthly.append({"month": month, "observation_date": converted["cer_observation_date"], "cer_level": cer_item["value"]})
    return rows, monthly


def write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def read_overlap_csv() -> list[dict]:
    with OVERLAP_CSV.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def main() -> None:
    DERIVED_DIR.mkdir(parents=True, exist_ok=True)
    text = SOURCE_HTML.read_text(encoding="utf-8")
    asset_rows, cer_monthly = build_asset_rows()

    text = text.replace("</head>", ASSET_CSS + "\n</head>", 1)
    text, panel_count = re.subn(
        r'      <div class="pend-layer-panel" data-pend-layer-panel="assets" role="tabpanel" hidden>.*?(?=      <div class="pend-layer-panel" data-pend-layer-panel="lab")',
        ASSET_PANEL,
        text,
        count=1,
        flags=re.DOTALL,
    )
    if panel_count != 1:
        raise RuntimeError("No se pudo reemplazar la capa Activos")

    metrics = extract_json_line(text, "PEND_POWER_METRICS")
    asset_ids = {"asset_cash_real", "asset_pf_real", "asset_usd_a3500_real", "income_real_salary_reference"}
    for metric in metrics:
        if metric["id"] in asset_ids:
            metric["unit"] = "índice real rebaseable; 100 en la fecha de entrada elegida"
            metric["note"] += " La interfaz permite cambiar la fecha de entrada sin alterar la serie fuente."
        if metric["id"] == "income_real_salary_reference" and "asset_cer_reference" not in metric["do_not_sum_with"]:
            metric["do_not_sum_with"].append("asset_cer_reference")
    if any(metric["id"] == NEW_METRIC["id"] for metric in metrics):
        raise RuntimeError("La métrica CER ya existe")
    metrics.append(NEW_METRIC)
    text = replace_json_line(text, "PEND_POWER_METRICS", metrics)

    overlaps = extract_json_line(text, "PEND_POWER_OVERLAPS")
    existing_pairs = {(row["metric_a"], row["metric_b"]) for row in overlaps}
    overlaps.extend(row for row in NEW_OVERLAPS if (row["metric_a"], row["metric_b"]) not in existing_pairs)
    text = replace_json_line(text, "PEND_POWER_OVERLAPS", overlaps)
    text = replace_json_line(text, "PEND_POWER_ASSETS", asset_rows)

    start = text.index("let pendPowerAssetRendered=false;")
    end = text.index("function renderPendPowerRegistry(){", start)
    text = text[:start] + ASSET_JS + "\n" + text[end:]
    old_nav_sync = "document.querySelectorAll('#pendPowerLayerNav .pend-layer-btn').forEach(btn=>{const active=btn.dataset.layer===layer;btn.classList.toggle('active',active);btn.setAttribute('aria-selected',String(active))});"
    new_nav_sync = "document.querySelectorAll('#pendPowerLayerNav .pend-layer-btn').forEach(btn=>{const active=btn.dataset.layer===layer;btn.classList.toggle('active',active);btn.setAttribute('aria-selected',String(active));if(active&&window.innerWidth<=760)requestAnimationFrame(()=>btn.scrollIntoView({behavior:'smooth',block:'nearest',inline:'center'}))});"
    if old_nav_sync not in text:
        raise RuntimeError("No se encontró la sincronización del navegador de capas")
    text = text.replace(old_nav_sync, new_nav_sync, 1)
    text = text.replace("<script id=\"pendulo-poder-script-v141\">", "<script id=\"pendulo-poder-script-v145\">", 1)
    text = text.replace("<span>escenario condicional</span></div>", "<span>escenario + acceso auditado</span></div>", 1)
    text = text.replace("</body>", "<!-- PENDULO_POWER_ASSETS_VERSION:145 -->\n</body>", 1)

    html_ids = re.findall(r'\bid="([^"]+)"', text)
    tests = {
        "cer_months_complete": len(cer_monthly) == len(asset_rows) == 32,
        "cer_base_is_100": abs(asset_rows[0]["cer_real_reference"] - 100) < 1e-9,
        "cer_last_is_finite": 50 < asset_rows[-1]["cer_real_reference"] < 200,
        "cer_is_labeled_reference": "CER = coeficiente, no bono" in text,
        "entry_date_selector_present": text.count('id="pendPowerAssetBase"') == 1,
        "active_layer_tab_scrolls_into_mobile_view": "inline:'center'" in text,
        "five_asset_traces_present": "Principal ajustado por CER · referencia" in text,
        "access_layer_present": "Antes del rendimiento estaba la barrera de acceso" in text,
        "assets_not_called_observed_wealth": "No describe el patrimonio observado" in text,
        "market_assets_keep_visible_gaps": all(label in text for label in ("Acciones / Merval", "Bonos", "Inmuebles", "Patrimonio de hogares")),
        "salary_bug_stays_fixed": "function pendPowerAssetChange(value)" in text and "function pendPowerChange(value)" not in ASSET_JS,
        "finance_preserved": "pendPowerFinanceRealChart" in text,
        "housing_preserved": "pendPowerHousingChart" in text,
        "fiscal_preserved": "pendPowerFiscalChart" in text,
        "six_layers_preserved": text.count('class="pend-layer-btn') == 6,
        "tab_count_preserved": text.count('class="tab-btn') == SOURCE_HTML.read_text(encoding="utf-8").count('class="tab-btn'),
        "metric_ids_unique": len({row["id"] for row in metrics}) == len(metrics),
        "html_ids_unique": len(html_ids) == len(set(html_ids)),
    }
    if not all(tests.values()):
        failed = [name for name, passed in tests.items() if not passed]
        raise RuntimeError(f"Fallaron tests v145: {failed}")

    OUTPUT_HTML.write_text(text, encoding="utf-8")
    INDEX_HTML.write_text(text, encoding="utf-8")

    fields = ["date", "cash_real", "pf_real", "usd_a3500_real", "cer_real_reference", "salary_real_reference", "ipc_level", "fx_a3500", "pf_real_monthly_pct", "cer_level", "cer_observation_date"]
    write_csv(ASSET_EXPANDED_CSV, asset_rows, fields)
    write_csv(CER_MONTHLY_CSV, cer_monthly, ["month", "observation_date", "cer_level"])

    registry = json.loads(METRIC_REGISTRY.read_text(encoding="utf-8-sig"))
    registry_by_id = {row["id"]: row for row in registry}
    for metric in metrics:
        if metric["id"] in asset_ids or metric["id"] == NEW_METRIC["id"]:
            registry_by_id[metric["id"]] = metric
    registry = list(registry_by_id.values())
    METRIC_REGISTRY.write_text(json.dumps(registry, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    overlap_all = read_overlap_csv()
    overlap_pairs = {(row["metric_a"], row["metric_b"]) for row in overlap_all}
    overlap_all.extend(row for row in NEW_OVERLAPS if (row["metric_a"], row["metric_b"]) not in overlap_pairs)
    write_csv(OVERLAP_CSV, overlap_all, ["metric_a", "metric_b", "risk", "relationship", "rule"])

    last = asset_rows[-1]
    sensitivity_lines = []
    for base_month in ("2023-12", "2024-03", "2024-12", "2025-12"):
        base = next(row for row in asset_rows if row["date"].startswith(base_month))
        sensitivity_lines.append(
            f"- {base_month}: CER {100 * last['cer_real_reference'] / base['cer_real_reference']:.2f}; "
            f"PF {100 * last['pf_real'] / base['pf_real']:.2f}; A3500 {100 * last['usd_a3500_real'] / base['usd_a3500_real']:.2f}."
        )
    digest = hashlib.sha256(OUTPUT_HTML.read_bytes()).hexdigest()
    audit = f"""# Auditoría · Capa Activos ampliada v145

Fecha de corte editorial: 2026-08-21  
Archivo: `data/dashboard_kawaii_145_pendulo_activos_ampliado.html`  
SHA-256: `{digest}`

## Cambio principal

Se agrega el CER oficial del BCRA como **referencia de principal indexado**, no como bono, depósito ni activo autónomo. La capa permite cambiar la fecha hipotética de entrada y vuelve a base 100 todas las curvas visibles.

Fuente CER: código 3540 de `tas5_ser.txt`, observación de fin de cada mes.  
Catálogo: https://www.bcra.gob.ar/archivos/Pdfs/PublicacionesEstadisticas/es_series.txt  
Serie: https://www.bcra.gob.ar/archivos/Pdfs/PublicacionesEstadisticas/tas5_ser.txt

## Fórmula

```text
CER_real_t = 100 × (CER_fin_mes_t / CER_fin_mes_base) × (IPC_base / IPC_t)
```

La interfaz puede volver a rebasar esta trayectoria y las demás en marzo de 2024, diciembre de 2024 o diciembre de 2025. El resultado de diciembre de 2023 es especialmente sensible al rezago del CER frente al IPC después del shock.

## Resultado por fecha de entrada

{chr(10).join(sensitivity_lines)}

## Contrato de lectura

- Efectivo y plazo fijo son escenarios de tenencia/renovación.
- A3500 es una referencia mayorista, no una operación minorista.
- CER es un coeficiente: no incluye cupón, cotización, duración, comisión ni default de un instrumento.
- Salario real es ingreso de referencia, no activo.
- Ninguna línea informa cuántas personas accedieron, cuánto poseían ni cómo cambió el patrimonio de los hogares.
- Acciones, bonos, inmuebles y patrimonio siguen como huecos visibles hasta disponer de retornos totales y coberturas compatibles.

## Controles automáticos

""" + "\n".join(f"- {name}: {'PASS' if value else 'FAIL'}" for name, value in tests.items()) + "\n"
    AUDIT_MD.write_text(audit, encoding="utf-8")
    TESTS_JSON.write_text(json.dumps(tests, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(json.dumps({"output": str(OUTPUT_HTML), "sha256": digest, "cer_last_default": last["cer_real_reference"], "tests": tests}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
