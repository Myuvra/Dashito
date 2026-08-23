from __future__ import annotations

import csv
import hashlib
import json
import re
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
SOURCE_HTML = ROOT / "data" / "dashboard_kawaii_145_pendulo_activos_ampliado.html"
OUTPUT_HTML = ROOT / "data" / "dashboard_kawaii_146_pendulo_cft_rentabilidad.html"
INDEX_HTML = ROOT / "index.html"
DERIVED_DIR = ROOT / "data" / "derivados" / "pendulo_poder_economico"
ROA_SOURCE = ROOT / "data" / "fuentes" / "pendulo_poder_economico" / "bcra" / "InfBanc0526.xlsx"
METRIC_REGISTRY = DERIVED_DIR / "metric_registry.json"
OVERLAP_CSV = DERIVED_DIR / "double_count_matrix.csv"
CFT_CSV = DERIVED_DIR / "cft_snapshot_jun2023.csv"
ROA_CSV = DERIVED_DIR / "bank_roa_snapshot_may2026.csv"
AUDIT_MD = DERIVED_DIR / "AUDITORIA_CFT_RENTABILIDAD_V146.md"
TESTS_JSON = DERIVED_DIR / "TESTS_CFT_RENTABILIDAD_V146.json"


CFT_ROWS = [
    {
        "period": "2023-06",
        "provider_group": "Entidades financieras",
        "provider_code": "EEFF",
        "sample_n": 15,
        "measure": "promedio del CFT máximo ofrecido",
        "cft_pct": 321.0,
        "source_grade": "A",
    },
    {
        "period": "2023-06",
        "provider_group": "Proveedores no financieros de crédito",
        "provider_code": "PNFC",
        "sample_n": 15,
        "measure": "promedio del CFT máximo ofrecido",
        "cft_pct": 588.0,
        "source_grade": "A",
    },
]


FINANCE_CSS = r'''
<style id="pendulo-poder-finance-evidence-v146-style">
#tab-pendulo .pend-finance-evidence{border-color:#d8cae5;background:linear-gradient(145deg,rgba(255,252,255,.98),rgba(250,253,255,.98))}
.pend-fin-evidence-grid{display:grid;grid-template-columns:minmax(0,1.12fr) minmax(310px,.88fr);gap:14px;align-items:stretch;margin-top:12px}.pend-fin-evidence-chart{width:100%;height:330px}.pend-fin-evidence-summary{display:grid;grid-template-columns:1fr 1fr;gap:9px}.pend-fin-evidence-kpi{padding:13px;border:1px solid #dfd2e7;border-radius:16px;background:#fff}.pend-fin-evidence-kpi.wide{grid-column:1/-1}.pend-fin-evidence-kpi small{display:block;color:#836d8a;font-size:7.4px;font-weight:950;letter-spacing:.04em;text-transform:uppercase}.pend-fin-evidence-kpi strong{display:block;margin:5px 0;color:#5c3d69;font-size:22px;line-height:1}.pend-fin-evidence-kpi.pink strong{color:#b03f68}.pend-fin-evidence-kpi.blue strong{color:#3d719b}.pend-fin-evidence-kpi.green strong{color:#2f8065}.pend-fin-evidence-kpi p{margin:0;color:#735f79;font-size:8.6px;line-height:1.45}.pend-fin-evidence-note{margin-top:12px;padding:13px 15px;border-left:5px solid #7d62b4;border-radius:14px;background:#faf7ff;color:#67516f;font-size:9.6px;line-height:1.55}.pend-fin-evidence-note b{color:#553661}.pend-fin-evidence-caveats{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:8px;margin-top:11px}.pend-fin-evidence-caveats span{padding:9px 10px;border:1px dashed #dbcde3;border-radius:12px;background:#fff;color:#75617c;font-size:8px;line-height:1.4}.pend-fin-evidence-caveats b{display:block;color:#5b3c67;font-size:8.3px}.pend-fin-evidence-caveats .warn{border-color:#ebc99f;background:#fffaf1}
.pend-roa-chart{width:100%;min-width:740px;height:390px}.pend-roa-summary{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:9px;margin-top:12px}.pend-roa-card{padding:13px;border:1px solid #dfd2e7;border-radius:16px;background:#fff}.pend-roa-card small{display:block;color:#826d89;font-size:7.3px;font-weight:950;text-transform:uppercase}.pend-roa-card strong{display:block;margin:5px 0;color:#5a3b67;font-size:21px}.pend-roa-card p{margin:0;color:#725f78;font-size:8.7px;line-height:1.45}.pend-roa-card.good{background:#f5fff9;border-color:#bddcc9}.pend-roa-card.good strong{color:#2f7e63}.pend-roa-card.warn{background:#fff9f0;border-color:#e5cca6}.pend-roa-card.warn strong{color:#9a6826}.pend-fin-separation{display:grid;grid-template-columns:auto 1fr;gap:12px;align-items:start;margin-top:12px;padding:14px;border:1px solid #bed7e7;border-radius:16px;background:#f5fbff}.pend-fin-separation .icon{font-size:27px}.pend-fin-separation h4{margin:0 0 5px;color:#3d6986;font-size:11.5px}.pend-fin-separation p{margin:0;color:#5f7481;font-size:9px;line-height:1.52}
@media(max-width:1050px){.pend-fin-evidence-grid{grid-template-columns:1fr}.pend-fin-evidence-caveats{grid-template-columns:1fr 1fr}}
@media(max-width:760px){.pend-fin-evidence-summary,.pend-roa-summary{grid-template-columns:1fr 1fr}.pend-roa-card:last-child{grid-column:1/-1}.pend-fin-evidence-chart{height:310px}.pend-roa-chart{min-width:680px;height:370px}}
@media(max-width:430px){.pend-fin-evidence-summary,.pend-roa-summary,.pend-fin-evidence-caveats{grid-template-columns:1fr}.pend-fin-evidence-kpi.wide,.pend-roa-card:last-child{grid-column:auto}.pend-fin-evidence-kpi strong,.pend-roa-card strong{font-size:19px}.pend-roa-chart{min-width:640px}.pend-fin-separation{grid-template-columns:1fr}}
</style>
'''


FINANCE_EVIDENCE_PANEL = r'''
          <section class="pend-card pend-finance-evidence">
            <div class="pend-head"><div><span class="pend-kicker">Costo total del crédito · foto oficial</span><h3>CFT: la comparación banco–PNFC que sí existe</h3><p class="pend-note">Junio de 2023, antes del shock. Promedio del <b>CFT máximo ofrecido</b> por los 15 proveedores con más deudores de cada grupo.</p></div></div>
            <div class="pend-meta-line"><span class="pend-meta ratio">SNAPSHOT · junio 2023</span><span class="pend-meta evidence-a">evidencia A · BCRA</span><span class="pend-meta">15 EEFF + 15 PNFC</span><span class="pend-meta">oferta máxima · no costo pagado</span></div>
            <div class="pend-fin-evidence-grid"><div class="pend-chart-scroll"><div id="pendPowerCftChart" class="pend-fin-evidence-chart"></div></div><div id="pendPowerCftSummary" class="pend-fin-evidence-summary"></div></div>
            <div class="pend-fin-evidence-note"><b>En criollo:</b> en esa muestra y en ese mes, el techo de costo publicado por las PNFC era mucho más alto. Eso muestra una diferencia relevante para quien necesitaba crédito, pero <b>no autoriza a decir cuánto pagó cada persona, cuánto recaudó el proveedor ni cuál es el CFT vigente en 2026</b>.</div>
            <div class="pend-fin-evidence-caveats"><span><b>Qué sí compara</b>Máximos ofrecidos bajo la misma metodología y mes.</span><span><b>Qué no compara</b>Contratos efectivamente tomados o costos promedio pagados.</span><span><b>Por qué no es una serie</b>Es una fotografía publicada para junio de 2023.</span><span class="warn"><b>No se suma a la pinza</b>Es un precio porcentual; la pinza es un contrafactual monetario.</span></div>
            <p class="pend-finance-source">Fuente: BCRA, Informe de Inclusión Financiera · primer semestre de 2023, gráfico 18. CFT incluye tasa, comisiones, seguros y otros cargos según el producto.</p>
          </section>

          <section class="pend-card pend-finance-evidence">
            <div class="pend-head"><div><span class="pend-kicker">Resultado del intermediario · carril contable</span><h3>¿La brecha de tasas se volvió ganancia bancaria?</h3><p class="pend-note"><b>No se puede deducir directamente.</b> Para ver rentabilidad usamos ROA contable oficial: resultado anualizado como porcentaje del activo.</p></div></div>
            <div class="pend-meta-line"><span class="pend-meta ratio">RATIO · ROA anualizado</span><span class="pend-meta evidence-a">evidencia A · BCRA</span><span class="pend-meta">acumulados 3 y 12 meses</span><span class="pend-meta">mayo 2026</span></div>
            <div class="pend-chart-stickers"><span class="pend-chart-sticker">3 meses = pulso reciente</span><span class="pend-chart-sticker warn">12 meses = película más estable</span><span class="pend-chart-sticker">ROA ≠ spread</span></div>
            <div class="pend-chart-scroll"><div id="pendPowerRoaChart" class="pend-roa-chart"></div></div>
            <div id="pendPowerRoaSummary" class="pend-roa-summary"></div>
            <div class="pend-fin-evidence-note"><b>Lectura apta para todo público:</b> el sistema financiero mostró una mejora reciente —2,2% anualizado en la ventana de tres meses—, pero su ROA de doce meses fue 1,1%, alrededor de 0,7 puntos menos que un año antes. El BCRA vincula el repunte corto a mayor margen financiero real, especialmente resultados por títulos y menores egresos por intereses, junto con una leve moderación de cargos por incobrabilidad. <b>Eso sigue sin convertir nuestra brecha de tasas en una cuenta de ganancias.</b></div>
            <div class="pend-fin-separation"><span class="icon">🧭</span><div><h4>EFNB no significa fintech/PNFC</h4><p>La categoría EFNB del informe bancario agrupa entidades financieras no bancarias dentro del sistema regulado. No es intercambiable con proveedores no financieros de crédito ni permite afirmar la rentabilidad de las fintech. Esa serie comparable sigue faltando.</p></div></div>
            <p class="pend-finance-source">Fuente: BCRA, Informe sobre Bancos · mayo de 2026, gráfico 13 y planilla oficial. Valores en moneda homogénea. El dato a tres meses es más sensible a cambios recientes que el acumulado de doce meses.</p>
          </section>

          <section class="pend-card">
            <div class="pend-head"><div><h3>La misma tasa no afecta igual a todos</h3><p class="pend-note">Ahora hay tres carriles visibles: costo del deudor, rendimiento del ahorrista y resultado contable del intermediario. Se relacionan, pero no son sumables ni equivalentes.</p></div></div>
            <div class="pend-actor-grid"><article class="pend-actor"><span class="emoji">🧾</span><h4>Deudor</h4><p>Necesita liquidez y <b>paga CFT</b>: interés más comisiones, seguros y cargos. El snapshot muestra ofertas máximas, no su contrato individual.</p></article><article class="pend-actor"><span class="emoji">🐷</span><h4>Ahorrista</h4><p>Puede inmovilizar pesos y <b>cobra</b> rendimiento. La tasa promedio de plazo fijo no representa todas las alternativas ni a todos los hogares.</p></article><article class="pend-actor"><span class="emoji">🏦</span><h4>Intermediario</h4><p>Su resultado se observa con contabilidad —acá ROA— después de riesgo, incobrabilidad, fondeo, encajes, costos, impuestos y otros negocios.</p></article></div>
            <div class="pend-gate"><span class="icon">🚧</span><div><h4>Rentabilidad fintech: hueco todavía visible</h4><p>No encontramos una serie oficial integrada y comparable de rentabilidad para PNFC/fintech. Por eso no usamos EFNB como sustituto ni convertimos el CFT de 2023 o la TNA fintech en “ganancia”.</p></div></div>
          </section>
'''


FINANCE_JS = r'''
let pendPowerFinanceEvidenceRendered=false;
function renderPendPowerFinanceEvidence(){
 const cftChart=document.getElementById('pendPowerCftChart'),roaChart=document.getElementById('pendPowerRoaChart');
 if(!cftChart||!roaChart||!window.Plotly)return;
 const cft=PEND_POWER_CFT_SNAPSHOT,eeff=cft.find(r=>r.provider_code==='EEFF'),pnfc=cft.find(r=>r.provider_code==='PNFC'),gap=pnfc.cft_pct-eeff.cft_pct,ratio=pnfc.cft_pct/eeff.cft_pct;
 Plotly.react(cftChart,[{x:[eeff.cft_pct,pnfc.cft_pct],y:['Entidades financieras','PNFC / fintech'],type:'bar',orientation:'h',marker:{color:['#4d87b5','#d8507d'],line:{color:'#fff',width:1}},text:[`${pendPowerFmt(eeff.cft_pct,0)}%`,`${pendPowerFmt(pnfc.cft_pct,0)}%`],textposition:'outside',cliponaxis:false,hovertemplate:'<b>%{y}</b><br>Promedio del CFT máximo: %{x:.0f}%<br>Junio de 2023 · muestra de 15<extra></extra>'}],{title:{text:'Promedio del CFT máximo ofrecido · junio 2023',font:{size:12,color:'#5c3e68'}},paper_bgcolor:'rgba(0,0,0,0)',plot_bgcolor:'rgba(255,255,255,.72)',font:{family:'Nunito, Arial, sans-serif',color:'#66506d',size:9},margin:{l:135,r:48,t:58,b:42},xaxis:{title:'% efectivo anual',range:[0,660],gridcolor:'#ebdfef',zeroline:false},yaxis:{autorange:'reversed'},showlegend:false},{responsive:true,displaylogo:false,modeBarButtonsToRemove:['lasso2d','select2d']});
 const cftSummary=document.getElementById('pendPowerCftSummary');if(cftSummary)cftSummary.innerHTML=`<article class="pend-fin-evidence-kpi blue"><small>EEFF · 15 proveedores</small><strong>${pendPowerFmt(eeff.cft_pct,0)}%</strong><p>Promedio del máximo ofrecido; no promedio pagado.</p></article><article class="pend-fin-evidence-kpi pink"><small>PNFC · 15 proveedores</small><strong>${pendPowerFmt(pnfc.cft_pct,0)}%</strong><p>Misma foto y criterio de selección.</p></article><article class="pend-fin-evidence-kpi wide"><small>Diferencia de la foto</small><strong>+${pendPowerFmt(gap,0)} pp · ${pendPowerFmt(ratio,2)}×</strong><p>El máximo promedio PNFC fue ${pendPowerFmt(ratio,2)} veces el de las entidades financieras en junio de 2023.</p></article>`;
 const groups=PEND_POWER_ROA_SNAPSHOT.map(r=>r.group),three=PEND_POWER_ROA_SNAPSHOT.map(r=>r.roa_3m_may2026),twelve=PEND_POWER_ROA_SNAPSHOT.map(r=>r.roa_12m_may2026);
 Plotly.react(roaChart,[{x:groups,y:three,name:'3 meses a may-2026',type:'bar',marker:{color:'#7559b4'},text:three.map(v=>pendPowerFmt(v,1)),textposition:'outside',hovertemplate:'<b>%{x}</b><br>ROA 3 meses anualizado: %{y:.2f}%<extra></extra>'},{x:groups,y:twelve,name:'12 meses a may-2026',type:'bar',marker:{color:'#51a182'},text:twelve.map(v=>pendPowerFmt(v,1)),textposition:'outside',hovertemplate:'<b>%{x}</b><br>ROA 12 meses: %{y:.2f}%<extra></extra>'}],{title:{text:'ROA por grupo de entidades · mayo 2026',x:.02,xanchor:'left',font:{size:12,color:'#5c3e68'}},barmode:'group',paper_bgcolor:'rgba(0,0,0,0)',plot_bgcolor:'rgba(255,255,255,.72)',font:{family:'Nunito, Arial, sans-serif',color:'#66506d',size:9},margin:{l:55,r:22,t:76,b:95},legend:{orientation:'h',y:1.14,x:0},xaxis:{tickangle:-18,automargin:true},yaxis:{title:'% del activo · anualizado',gridcolor:'#ebdfef',zeroline:true,zerolinecolor:'#b9a9c2',rangemode:'tozero'}},{responsive:true,displaylogo:false,modeBarButtonsToRemove:['lasso2d','select2d']});
 const system=PEND_POWER_ROA_SNAPSHOT[0],delta=system.roa_12m_may2026-system.roa_12m_may2025,summary=document.getElementById('pendPowerRoaSummary');if(summary)summary.innerHTML=`<article class="pend-roa-card good"><small>Sistema · pulso reciente</small><strong>${pendPowerFmt(system.roa_3m_may2026,1)}%</strong><p>ROA anualizado acumulado en tres meses a mayo de 2026.</p></article><article class="pend-roa-card"><small>Sistema · película anual</small><strong>${pendPowerFmt(system.roa_12m_may2026,1)}%</strong><p>ROA acumulado en doce meses a mayo de 2026.</p></article><article class="pend-roa-card warn"><small>Cambio interanual · 12 meses</small><strong>${delta<0?'−':'+'}${pendPowerFmt(Math.abs(delta),1)} pp</strong><p>Frente al ROA de doce meses a mayo de 2025 (${pendPowerFmt(system.roa_12m_may2025,1)}%).</p></article>`;
 pendPowerFinanceEvidenceRendered=true;
}
window.addEventListener('resize',()=>{if(!pendPowerFinanceEvidenceRendered||!window.Plotly)return;['pendPowerCftChart','pendPowerRoaChart'].forEach(id=>{const el=document.getElementById(id);if(el)Plotly.Plots.resize(el)})});
if(document.querySelector('[data-pend-layer-panel="finance"]:not([hidden])'))requestAnimationFrame(renderPendPowerFinanceEvidence);
'''


UPDATED_CFT_METRIC = {
    "id": "financial_consumer_cft",
    "layer": "Finanzas",
    "title": "Costo Financiero Total máximo ofrecido · snapshot",
    "measure_type": "RATIO · SNAPSHOT",
    "unit": "% efectivo anual máximo ofrecido",
    "frequency": "snapshot oficial",
    "period": "jun-2023",
    "source_grade": "A",
    "transformation": "promedio publicado de máximos ofrecidos; muestra de 15 proveedores por grupo",
    "actors": "deudores ↔ entidades financieras / PNFC",
    "economic_flow_id": "consumer_credit_total_cost_offer",
    "status": "integrado como snapshot; no es una serie ni un dato 2026",
    "do_not_sum_with": ["financial_bank_real_monthly", "financial_fintech_real_monthly", "financial_bank_window_delta", "financial_fintech_window_delta"],
    "note": "Máximo ofrecido promedio, no costo promedio pagado ni ingreso del proveedor. Muestra de 15 EEFF y 15 PNFC con más deudores.",
}


UPDATED_BANK_METRIC = {
    "id": "bank_profitability",
    "layer": "Finanzas",
    "title": "Rentabilidad contable del sistema financiero",
    "measure_type": "RATIO / FLUJO CONTABLE",
    "unit": "ROA anualizado, % del activo",
    "frequency": "acumulado 3 y 12 meses",
    "period": "may-2025 / may-2026",
    "source_grade": "A",
    "transformation": "observado en moneda homogénea",
    "actors": "bancos / EFNB / accionistas",
    "economic_flow_id": "bank_accounting_profitability",
    "status": "integrado",
    "do_not_sum_with": ["financial_bank_pf_real_gap", "financial_bank_window_delta", "financial_consumer_cft"],
    "note": "Resultado contable oficial; no se deriva del spread ni del contrafactual del hogar. EFNB no equivale a fintech/PNFC.",
}


FINTECH_METRIC = {
    "id": "fintech_profitability",
    "layer": "Finanzas",
    "title": "Rentabilidad contable PNFC/fintech",
    "measure_type": "RATIO / FLUJO CONTABLE",
    "unit": "serie comparable no disponible",
    "frequency": "pendiente",
    "period": "sin serie integrada",
    "source_grade": "—",
    "transformation": "sin fabricar",
    "actors": "PNFC / fintech / accionistas",
    "economic_flow_id": "fintech_accounting_profitability",
    "status": "no integrado: falta serie observada comparable",
    "do_not_sum_with": ["financial_fintech_real_monthly", "financial_fintech_window_delta", "financial_consumer_cft"],
    "note": "No se sustituye con TNA, CFT, exposición contrafactual ni con la categoría EFNB del sistema financiero.",
}


OVERLAP_UPDATES = [
    {"metric_a": "financial_consumer_cft", "metric_b": "financial_bank_real_monthly", "risk": "alto", "relationship": "máximo ofrecido del costo total vs TNA promedio transformada a tasa real", "rule": "mostrar como preguntas distintas; no sustituir ni sumar"},
    {"metric_a": "financial_consumer_cft", "metric_b": "financial_fintech_real_monthly", "risk": "alto", "relationship": "máximo ofrecido del costo total vs TNA PNFC promedio", "rule": "el snapshot CFT no completa ni reemplaza la serie TNA"},
    {"metric_a": "bank_profitability", "metric_b": "financial_bank_window_delta", "risk": "alto", "relationship": "resultado contable del sistema vs impacto contrafactual sobre deudores", "rule": "no convertir perjuicio estimado del hogar en ganancia bancaria"},
    {"metric_a": "fintech_profitability", "metric_b": "financial_fintech_real_monthly", "risk": "alto", "relationship": "rentabilidad contable faltante vs precio promedio del crédito", "rule": "no inferir beneficio empresario desde TNA"},
    {"metric_a": "fintech_profitability", "metric_b": "financial_fintech_window_delta", "risk": "alto", "relationship": "rentabilidad contable faltante vs exposición contrafactual del hogar", "rule": "no inferir beneficio empresario desde el diferencial monetario"},
]


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


def xlsx_values(path: Path, sheet_name: str) -> dict[str, object]:
    main_ns = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
    rel_ns = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
    pkg_ns = "http://schemas.openxmlformats.org/package/2006/relationships"
    with zipfile.ZipFile(path) as archive:
        workbook = ET.fromstring(archive.read("xl/workbook.xml"))
        sheet = next((node for node in workbook.findall(f".//{{{main_ns}}}sheet") if node.attrib.get("name") == sheet_name), None)
        if sheet is None:
            raise RuntimeError(f"No se encontró la hoja {sheet_name}")
        relation_id = sheet.attrib[f"{{{rel_ns}}}id"]
        relations = ET.fromstring(archive.read("xl/_rels/workbook.xml.rels"))
        relation = next(node for node in relations.findall(f"{{{pkg_ns}}}Relationship") if node.attrib.get("Id") == relation_id)
        target = relation.attrib["Target"].lstrip("/")
        sheet_path = target if target.startswith("xl/") else f"xl/{target}"
        shared: list[str] = []
        if "xl/sharedStrings.xml" in archive.namelist():
            shared_root = ET.fromstring(archive.read("xl/sharedStrings.xml"))
            for item in shared_root.findall(f"{{{main_ns}}}si"):
                shared.append("".join(node.text or "" for node in item.iter(f"{{{main_ns}}}t")))
        root = ET.fromstring(archive.read(sheet_path))
        result: dict[str, object] = {}
        for cell in root.findall(f".//{{{main_ns}}}c"):
            ref = cell.attrib.get("r")
            value_node = cell.find(f"{{{main_ns}}}v")
            if not ref or value_node is None or value_node.text is None:
                continue
            raw = value_node.text
            if cell.attrib.get("t") == "s":
                result[ref] = shared[int(raw)]
            else:
                try:
                    result[ref] = float(raw)
                except ValueError:
                    result[ref] = raw
        return result


def build_roa_rows() -> list[dict]:
    values = xlsx_values(ROA_SOURCE, "13")
    groups = [
        ("B", "Sistema financiero"),
        ("C", "Bancos privados nacionales"),
        ("D", "Bancos privados extranjeros"),
        ("E", "Bancos públicos"),
        ("F", "EFNB"),
    ]
    rows = []
    for column, group in groups:
        rows.append(
            {
                "group": group,
                "roa_3m_may2026": float(values[f"{column}11"]),
                "roa_12m_may2025": float(values[f"{column}13"]),
                "roa_12m_may2026": float(values[f"{column}14"]),
                "unit": "% del activo anualizado",
                "source_grade": "A",
            }
        )
    return rows


def upsert_metric(rows: list[dict], metric: dict) -> None:
    for index, row in enumerate(rows):
        if row["id"] == metric["id"]:
            rows[index] = metric
            return
    rows.append(metric)


def upsert_overlap(rows: list[dict], update: dict) -> None:
    pair = (update["metric_a"], update["metric_b"])
    reverse = (update["metric_b"], update["metric_a"])
    for index, row in enumerate(rows):
        current = (row["metric_a"], row["metric_b"])
        if current in (pair, reverse):
            rows[index] = update
            return
    rows.append(update)


def write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    DERIVED_DIR.mkdir(parents=True, exist_ok=True)
    source_text = SOURCE_HTML.read_text(encoding="utf-8")
    text = source_text
    roa_rows = build_roa_rows()

    text = text.replace("</head>", FINANCE_CSS + "\n</head>", 1)
    text, panel_count = re.subn(
        r'          <section class="pend-card">\s*<div class="pend-head"><div><h3>La misma tasa no afecta igual a todos</h3>.*?</section>\s*(?=        </div>\s*</div>\s*\n\s*<div class="pend-layer-panel" data-pend-layer-panel="housing")',
        FINANCE_EVIDENCE_PANEL,
        text,
        count=1,
        flags=re.DOTALL,
    )
    if panel_count != 1:
        raise RuntimeError("No se pudo reemplazar el cierre de la capa Finanzas")

    text = text.replace(
        '<article class="pend-finance-term missing"><small>CFT · faltante visible</small><b>No lo reemplazamos con TNA</b><p>Falta una serie continua y comparable con seguros, comisiones y demás cargos del producto.</p></article>',
        '<article class="pend-finance-term missing"><small>CFT · snapshot oficial</small><b>Foto comparable · jun-2023</b><p>Abajo se integra el máximo ofrecido promedio de EEFF y PNFC. No es una serie ni costo pagado.</p></article>',
        1,
    )
    text = text.replace(
        '<article class="pend-finance-term separate"><small>RENTABILIDAD · carril aparte</small><b>ROA/ROE no salen del spread</b><p>Requieren estados contables comparables; no se deducen de estas curvas.</p></article>',
        '<article class="pend-finance-term separate"><small>ROA · carril contable</small><b>Rentabilidad observada · may-2026</b><p>Se integra abajo desde estados contables. No sale del spread ni de la pinza.</p></article>',
        1,
    )

    finance_metrics = extract_json_line(text, "PEND_POWER_FINANCE_METRICS")
    upsert_metric(finance_metrics, UPDATED_CFT_METRIC)
    upsert_metric(finance_metrics, UPDATED_BANK_METRIC)
    upsert_metric(finance_metrics, FINTECH_METRIC)
    text = replace_json_line(text, "PEND_POWER_FINANCE_METRICS", finance_metrics)

    finance_overlaps = extract_json_line(text, "PEND_POWER_FINANCE_OVERLAPS")
    for overlap in OVERLAP_UPDATES:
        upsert_overlap(finance_overlaps, overlap)
    text = replace_json_line(text, "PEND_POWER_FINANCE_OVERLAPS", finance_overlaps)

    cft_payload = json.dumps(CFT_ROWS, ensure_ascii=False, separators=(",", ":"))
    roa_payload = json.dumps(roa_rows, ensure_ascii=False, separators=(",", ":"))
    extra_script = f'''<script id="pendulo-poder-finance-evidence-v146">\nconst PEND_POWER_CFT_SNAPSHOT={cft_payload};\nconst PEND_POWER_ROA_SNAPSHOT={roa_payload};\n{FINANCE_JS}\n</script>\n'''
    text = text.replace("</body>", extra_script + "</body>", 1)
    old_activation = "if(layer==='finance'){renderPendPowerFinance();renderPendPowerFinanceObserved();}"
    new_activation = "if(layer==='finance'){renderPendPowerFinance();renderPendPowerFinanceObserved();if(typeof renderPendPowerFinanceEvidence==='function')requestAnimationFrame(renderPendPowerFinanceEvidence);}"
    if old_activation not in text:
        raise RuntimeError("No se encontró la activación de Finanzas")
    text = text.replace(old_activation, new_activation, 1)
    text = text.replace('<script id="pendulo-poder-script-v145">', '<script id="pendulo-poder-script-v146">', 1)
    text = text.replace("<!-- PENDULO_POWER_ASSETS_VERSION:145 -->", "<!-- PENDULO_POWER_FINANCE_EVIDENCE_VERSION:146 -->", 1)

    html_ids = re.findall(r'\bid="([^"]+)"', text)
    cft_gap = CFT_ROWS[1]["cft_pct"] - CFT_ROWS[0]["cft_pct"]
    cft_ratio = CFT_ROWS[1]["cft_pct"] / CFT_ROWS[0]["cft_pct"]
    system = roa_rows[0]
    tests = {
        "cft_eeff_is_321": CFT_ROWS[0]["cft_pct"] == 321,
        "cft_pnfc_is_588": CFT_ROWS[1]["cft_pct"] == 588,
        "cft_gap_is_267pp": cft_gap == 267,
        "cft_ratio_is_1_83x": abs(cft_ratio - 1.8317757) < 1e-6,
        "roa_system_3m_matches_workbook": abs(system["roa_3m_may2026"] - 2.199157) < 1e-6,
        "roa_system_12m_matches_workbook": abs(system["roa_12m_may2026"] - 1.065898) < 1e-6,
        "roa_interannual_delta_matches": abs((system["roa_12m_may2026"] - system["roa_12m_may2025"]) - (-0.674661)) < 1e-6,
        "efnb_caveat_visible": "EFNB no significa fintech/PNFC" in text,
        "cft_not_labeled_2026": "no es una serie ni un dato 2026" in json.dumps(finance_metrics, ensure_ascii=False) and "cuál es el CFT vigente en 2026" in text,
        "fintech_profitability_gap_visible": "Rentabilidad fintech: hueco todavía visible" in text,
        "observed_finance_preserved": "pendPowerFinanceRealChart" in text,
        "assets_preserved": "pendPowerAssetChart" in text,
        "housing_preserved": "pendPowerHousingChart" in text,
        "fiscal_preserved": "pendPowerFiscalChart" in text,
        "six_layers_preserved": text.count('class="pend-layer-btn') == 6,
        "tab_count_preserved": text.count('class="tab-btn') == source_text.count('class="tab-btn'),
        "finance_metric_ids_unique": len({row["id"] for row in finance_metrics}) == len(finance_metrics),
        "html_ids_unique": len(html_ids) == len(set(html_ids)),
    }
    if not all(tests.values()):
        failed = [name for name, passed in tests.items() if not passed]
        raise RuntimeError(f"Fallaron tests v146: {failed}")

    OUTPUT_HTML.write_text(text, encoding="utf-8")
    INDEX_HTML.write_text(text, encoding="utf-8")
    write_csv(CFT_CSV, CFT_ROWS, ["period", "provider_group", "provider_code", "sample_n", "measure", "cft_pct", "source_grade"])
    write_csv(ROA_CSV, roa_rows, ["group", "roa_3m_may2026", "roa_12m_may2025", "roa_12m_may2026", "unit", "source_grade"])

    registry = json.loads(METRIC_REGISTRY.read_text(encoding="utf-8-sig"))
    for metric in (UPDATED_CFT_METRIC, UPDATED_BANK_METRIC, FINTECH_METRIC):
        upsert_metric(registry, metric)
    METRIC_REGISTRY.write_text(json.dumps(registry, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    with OVERLAP_CSV.open(encoding="utf-8-sig", newline="") as handle:
        overlaps = list(csv.DictReader(handle))
    for overlap in OVERLAP_UPDATES:
        upsert_overlap(overlaps, overlap)
    write_csv(OVERLAP_CSV, overlaps, ["metric_a", "metric_b", "risk", "relationship", "rule"])

    digest = hashlib.sha256(OUTPUT_HTML.read_bytes()).hexdigest()
    audit = f"""# Auditoría · CFT y rentabilidad financiera v146

Fecha de corte editorial: 2026-08-21  
Archivo: `data/dashboard_kawaii_146_pendulo_cft_rentabilidad.html`  
SHA-256: `{digest}`

## CFT · fotografía comparable

- Fuente: BCRA, Informe de Inclusión Financiera · primer semestre de 2023, gráfico 18.
- Período: junio de 2023.
- Muestra: 15 entidades financieras y 15 PNFC con mayor cantidad de deudores entre quienes informaban préstamos personales al Régimen de Transparencia.
- Medida: promedio del CFT máximo ofrecido; EEFF = 321%, PNFC = 588%.
- Diferencia: +267 pp; cociente PNFC/EEFF = {cft_ratio:.4f}.
- No es costo promedio pagado, ingreso del proveedor, saldo de cartera ni dato 2026.

## Rentabilidad bancaria · carril contable

- Fuente: BCRA, Informe sobre Bancos · mayo de 2026 y hoja 13 de su planilla oficial.
- Medida: ROA anualizado acumulado en tres y doce meses, en moneda homogénea.
- Sistema financiero: 3 meses a mayo de 2026 = {system['roa_3m_may2026']:.6f}%; 12 meses = {system['roa_12m_may2026']:.6f}%.
- Comparación interanual del ROA de doce meses: {system['roa_12m_may2026'] - system['roa_12m_may2025']:.6f} pp.
- La categoría EFNB no equivale a PNFC/fintech.

## Contrato de lectura y antidoble conteo

- CFT/TNA son precios del crédito desde la perspectiva del deudor.
- La pinza es un contrafactual monetario construido contra una norma histórica.
- ROA es resultado contable observado del intermediario como porcentaje del activo.
- Ninguno de estos indicadores se suma con los otros ni se usa como sustituto.
- No se infiere rentabilidad fintech desde TNA, CFT, EFNB o exposición contrafactual.

## Controles automáticos

""" + "\n".join(f"- {name}: {'PASS' if value else 'FAIL'}" for name, value in tests.items()) + "\n"
    AUDIT_MD.write_text(audit, encoding="utf-8")
    TESTS_JSON.write_text(json.dumps(tests, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(json.dumps({"output": str(OUTPUT_HTML), "sha256": digest, "cft_gap_pp": cft_gap, "cft_ratio": cft_ratio, "system_roa_3m": system["roa_3m_may2026"], "system_roa_12m": system["roa_12m_may2026"], "tests": tests}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
