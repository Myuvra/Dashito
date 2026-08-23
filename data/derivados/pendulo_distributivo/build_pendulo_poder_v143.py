from __future__ import annotations

import csv
import hashlib
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
SOURCE_HTML = ROOT / "data" / "dashboard_kawaii_142_pendulo_financiero_observado.html"
OUTPUT_HTML = ROOT / "data" / "dashboard_kawaii_143_pendulo_vivienda_observada.html"
INDEX_HTML = ROOT / "index.html"
DERIVED_DIR = ROOT / "data" / "derivados" / "pendulo_poder_economico"
HOUSING_CSV = DERIVED_DIR / "housing_tenure_2016_2025.csv"
REGISTRY_JSON = DERIVED_DIR / "metric_registry.json"
AUDIT_MD = DERIVED_DIR / "AUDITORIA_CAPA_VIVIENDA_V143.md"
TESTS_JSON = DERIVED_DIR / "TESTS_CAPA_VIVIENDA_V143.json"


HOUSING_CSS = r'''
<style id="pendulo-vivienda-observada-v143">
#tab-pendulo .pend-housing-observed{border-color:#b9d8cf;background:linear-gradient(145deg,rgba(252,255,254,.98),rgba(250,248,255,.98))}
.pend-housing-kpis{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:9px;margin-top:12px}.pend-housing-kpi{padding:13px;border:1px solid #d9d1e3;border-radius:16px;background:#fff}.pend-housing-kpi.owner{border-color:#abd8c6;background:#f5fff9}.pend-housing-kpi.renter{border-color:#e7c1d0;background:#fff7fa}.pend-housing-kpi.other{border-color:#d0c3e3;background:#faf8ff}.pend-housing-kpi small{display:block;color:#816c87;font-size:7.3px;font-weight:950;letter-spacing:.035em;text-transform:uppercase}.pend-housing-kpi strong{display:block;margin:5px 0 4px;color:#593a66;font-size:21px;line-height:1}.pend-housing-kpi.owner strong{color:#2d7f62}.pend-housing-kpi.renter strong{color:#a74368}.pend-housing-kpi p{margin:0;color:#725f78;font-size:8.7px;line-height:1.45}
.pend-housing-chart{width:100%;min-width:720px;height:440px}.pend-housing-changes{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px;margin-top:12px}.pend-housing-change{padding:14px;border:1px solid #ddd0e5;border-radius:16px;background:#fff}.pend-housing-change small{display:block;color:#846f8a;font-size:7.4px;font-weight:950;text-transform:uppercase}.pend-housing-change h4{margin:5px 0 7px;color:#5a3b67;font-size:12px}.pend-housing-change p{margin:0;color:#725f78;font-size:9px;line-height:1.5}.pend-housing-change b.owner{color:#2e8063}.pend-housing-change b.renter{color:#a44066}
.pend-housing-plain{margin-top:12px;padding:13px 15px;border-left:5px solid #4e9d80;border-radius:14px;background:#f5fff9;color:#586b63;font-size:10px;line-height:1.55}.pend-housing-plain b{color:#286b54}
@media(max-width:1050px){.pend-housing-kpis{grid-template-columns:repeat(2,minmax(0,1fr))}}
@media(max-width:760px){.pend-housing-chart{min-width:660px;height:410px}.pend-housing-kpis{grid-template-columns:1fr 1fr}.pend-housing-changes{grid-template-columns:1fr}}
@media(max-width:430px){.pend-housing-kpis{grid-template-columns:1fr}.pend-housing-chart{min-width:620px}}
</style>
'''


HOUSING_PANEL = r'''      <div class="pend-layer-panel" data-pend-layer-panel="housing" role="tabpanel" hidden>
        <div class="pend-layer-stack">
          <section class="pend-card pend-hero pend-housing-observed">
            <div class="pend-head"><div><span class="pend-kicker">C · Vivienda y seguridad habitacional</span><h2>¿La gente vive en una casa propia, alquilada o prestada?</h2><p class="pend-sub">Serie semestral EPH para hogares de 31 aglomerados. Mide condición de tenencia: no informa cuánto vale la vivienda, cuánto pesa el alquiler ni si existe deuda hipotecaria.</p></div></div>
            <div class="pend-layer-question">Propietario ↔ inquilino ↔ ocupante<small>Son posiciones habitacionales, no bloques morales. Ser propietario tampoco informa calidad, ubicación, deuda ni ingreso.</small></div>
            <div class="pend-meta-line"><span class="pend-meta ratio">RATIO · % de hogares</span><span class="pend-meta evidence-a">fuente A · EPH</span><span class="pend-meta">semestral · 31 aglomerados</span><span class="pend-meta">actores: propietario · inquilino · ocupante</span></div>
            <div id="pendPowerHousingKpis" class="pend-housing-kpis"></div>
            <div class="pend-chart-stickers"><span class="pend-chart-sticker">propietario total incluye “sólo vivienda”</span><span class="pend-chart-sticker warn">más inquilinos ≠ alquiler más caro</span><span class="pend-chart-sticker">composición ≠ bienestar completo</span></div>
            <div class="pend-chart-scroll"><div id="pendPowerHousingChart" class="pend-housing-chart"></div></div>
            <div id="pendPowerHousingChanges" class="pend-housing-changes"></div>
            <div class="pend-housing-plain"><b>En criollo:</b> frente a 2016 hay menos hogares propietarios y más inquilinos. Desde el cierre de 2023 la composición se movió parcialmente en sentido contrario. Eso describe <b>cómo se ocupa la vivienda</b>; no alcanza para decir si alquilar se volvió más llevadero o si comprar se volvió accesible.</div>
            <div class="pend-links"><button class="pend-link" onclick="activateTab('tab-housing')">Abrir Vivienda completa →</button><button class="pend-link" onclick="activateTab('tab-family')">Abrir Canastas familiares →</button><button class="pend-link" onclick="activateTab('tab-consumption')">Abrir Consumo →</button></div>
          </section>
          <section class="pend-card">
            <div class="pend-head"><div><h3>Lo que la tenencia no responde</h3><p class="pend-note">El nivel observado y la carga mensual son preguntas distintas.</p></div></div>
            <div class="pend-power-grid"><article class="pend-power-metric"><small>RATIO · faltante visible</small><strong>Alquiler / ingreso</strong><p>No hay todavía una serie contemporánea homogénea incorporada.</p><span class="perspective">No se infiere desde avisos ni desde un precio promedio.</span></article><article class="pend-power-metric"><small>STOCK · faltante</small><strong>Deuda hipotecaria</strong><p>Ser propietario no revela si la vivienda está pagada.</p><span class="perspective">Requiere cantidades y saldos compatibles.</span></article><article class="pend-power-metric"><small>SNAPSHOT · oficial</small><strong>ENGHo 2017–18</strong><p>Puede describir estructura histórica del presupuesto por quintil.</p><span class="perspective">No se presentará como presupuesto 2026.</span></article><article class="pend-power-metric"><small>ESCENARIO · pendiente</small><strong>Hogar tipo</strong><p>Calculadora futura separada de los datos observados.</p><span class="perspective">No duplicará IVA contenido en consumo.</span></article></div>
            <div class="pend-gate"><span class="icon">🧮</span><div><h4>Waterfall de $100 todavía deshabilitado</h4><p>Se habilitará sólo con alquiler/ingreso o una radiografía ENGHo explícitamente fechada. Alquiler pagado y renta recibida representan el mismo flujo desde dos actores: nunca se suman como dos fenómenos.</p></div></div>
          </section>
        </div>
      </div>

'''


HOUSING_SCRIPT_TEMPLATE = r'''
<script id="pendulo-vivienda-observada-script-v143">
const PEND_POWER_HOUSING_ROWS=__HOUSING_ROWS__;
let pendPowerHousingRendered=false;
const pendHousingMetric=PEND_POWER_METRICS.find(row=>row.id==='housing_tenure_status');
if(pendHousingMetric)Object.assign(pendHousingMetric,{period:'2S-2016–2S-2025',status:'integrado en la capa Vivienda',note:'Composición observada de tenencia EPH; no mide costo, valor ni deuda de la vivienda.'});
function pendHousingSigned(value){const sign=value>0?'+':value<0?'−':'';return `${sign}${pendPowerFmt(Math.abs(value),1)} pp`;}
function renderPendPowerHousing(){
 const chart=document.getElementById('pendPowerHousingChart'),kpis=document.getElementById('pendPowerHousingKpis'),changes=document.getElementById('pendPowerHousingChanges');
 if(!chart||!kpis||!changes||!window.Plotly)return;
 const rows=PEND_POWER_HOUSING_ROWS,first=rows[0],latest=rows[rows.length-1],shock=rows.find(r=>r.period==='2S-2023');
 const residual=latest.occupant+latest.other;
 kpis.innerHTML=[
  ['owner','Propietario · vivienda y terreno',latest.owner_land,'Parte claramente propietaria; no informa deuda ni calidad.'],
  ['owner','Propietarios totales',latest.owner_total,'Incluye vivienda+terreno y propietario sólo de la vivienda.'],
  ['renter','Inquilinos / arrendatarios',latest.renter,'Hogares expuestos al pago de alquiler; no mide su monto.'],
  ['other','Ocupantes y otras formas',residual,'Uso gratuito, relación de dependencia y otras tenencias.']
 ].map(([kind,title,value,note])=>`<article class="pend-housing-kpi ${kind}"><small>${title}</small><strong>${pendPowerFmt(value,1)}%</strong><p>${note}</p></article>`).join('');
 const x=rows.map(r=>r.date);
 const traces=[
  {x,y:rows.map(r=>r.owner_total),customdata:rows.map(r=>[r.period,r.owner_land,r.owner_only]),name:'Propietarios totales',mode:'lines+markers',line:{color:'#3f9a76',width:3},marker:{size:6},hovertemplate:'<b>%{customdata[0]}</b><br>Propietarios totales: %{y:.1f}%<br>Vivienda + terreno: %{customdata[1]:.1f}%<br>Sólo vivienda: %{customdata[2]:.1f}%<extra></extra>'},
  {x,y:rows.map(r=>r.renter),customdata:rows.map(r=>r.period),name:'Inquilinos',mode:'lines+markers',line:{color:'#df6489',width:3},marker:{size:6},hovertemplate:'<b>%{customdata}</b><br>Inquilinos: %{y:.1f}%<br>No mide alquiler / ingreso<extra></extra>'},
  {x,y:rows.map(r=>r.occupant+r.other),customdata:rows.map(r=>r.period),name:'Ocupantes y otras formas',mode:'lines',line:{color:'#8d6eb4',width:2,dash:'dot'},hovertemplate:'<b>%{customdata}</b><br>Ocupantes + otras: %{y:.1f}%<extra></extra>'}
 ];
 const layout={title:{text:'Condición de tenencia · hogares de 31 aglomerados EPH',font:{size:13,color:'#5d4169'}},paper_bgcolor:'rgba(0,0,0,0)',plot_bgcolor:'rgba(255,255,255,.74)',font:{family:'Nunito, Arial, sans-serif',color:'#654f6c',size:10},margin:{l:58,r:24,t:76,b:58},hovermode:'x unified',xaxis:{type:'date',gridcolor:'#eee5f2',tickformat:'%Y',dtick:'M12',automargin:true},yaxis:{title:'% de hogares',ticksuffix:'%',range:[0,78],gridcolor:'#eadff0',zeroline:false,automargin:true},legend:{orientation:'h',y:1.17,x:0,font:{size:9}},shapes:[{type:'line',x0:'2023-12-31',x1:'2023-12-31',yref:'paper',y0:0,y1:1,line:{color:'#db6c90',width:1.5,dash:'dot'}}],annotations:[{x:'2023-12-31',yref:'paper',y:1,text:'2S-2023',showarrow:false,yshift:10,font:{size:8,color:'#a33f62'}}]};
 Plotly.react(chart,traces,layout,{responsive:true,displaylogo:false,scrollZoom:false,modeBarButtonsToRemove:['lasso2d','select2d']});
 pendPowerHousingRendered=true;
 changes.innerHTML=`<article class="pend-housing-change"><small>Película larga · 2S-2016 → 2S-2025</small><h4>Cambio de composición en nueve años</h4><p>Propietarios totales: <b class="owner">${pendHousingSigned(latest.owner_total-first.owner_total)}</b>. Inquilinos: <b class="renter">${pendHousingSigned(latest.renter-first.renter)}</b>.</p></article><article class="pend-housing-change"><small>Desde la base heredada · 2S-2023 → 2S-2025</small><h4>Movimiento posterior, sin atribuir causalidad</h4><p>Propietarios totales: <b class="owner">${pendHousingSigned(latest.owner_total-shock.owner_total)}</b>. Inquilinos: <b class="renter">${pendHousingSigned(latest.renter-shock.renter)}</b>.</p></article>`;
}
window.addEventListener('resize',()=>{if(pendPowerHousingRendered){const el=document.getElementById('pendPowerHousingChart');if(el&&window.Plotly)Plotly.Plots.resize(el);}});
</script>

'''


def extract_json_const(text: str, name: str) -> list[dict] | dict:
    match = re.search(rf"^const {re.escape(name)}\s*=\s*(\[.*?\]|\{{.*?\}});\s*$", text, re.MULTILINE)
    if not match:
        raise RuntimeError(f"No se encontró {name}")
    return json.loads(match.group(1))


def write_csv(path: Path, rows: list[dict]) -> None:
    fields = ["period", "date", "owner_land", "owner_only", "renter", "occupant", "other", "owner_total"]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def salary_changes(text: str) -> dict[str, float]:
    series = extract_json_const(text, "powerTotalAllOfficial")
    dates = series["dates"]
    values = series["yNov"]
    windows = {
        "Macri": ("2017-01-01", "2019-12-01"),
        "Alberto": ("2020-01-01", "2023-11-01"),
        "Milei": ("2023-11-01", "2026-06-01"),
    }
    return {
        name: (values[dates.index(end)] / values[dates.index(start)] - 1) * 100
        for name, (start, end) in windows.items()
    }


def make_audit(rows: list[dict], salaries: dict[str, float], digest: str, tests: dict[str, bool]) -> str:
    first, latest = rows[0], rows[-1]
    shock = next(row for row in rows if row["period"] == "2S-2023")
    results = "\n".join(f"- {name}: {'PASS' if ok else 'FAIL'}" for name, ok in tests.items())
    salary_lines = "\n".join(f"- {name}: {value:.6f}%" for name, value in salaries.items())
    return f"""# Auditoría · Péndulo vivienda observada v143

Fecha editorial: 2026-08-21  
Archivo: `data/dashboard_kawaii_143_pendulo_vivienda_observada.html`  
SHA-256: `{digest}`

## Corrección de la tarjeta salarial

La función de Activos `pendPowerChange(value)` colisionaba con la función homónima que calculaba ventanas salariales por gobierno. Se renombró exclusivamente la función de Activos a `pendPowerAssetChange(value)`.

Resultados restaurados:

{salary_lines}

## Vivienda observada

Fuente reutilizada: serie EPH ya archivada en el tab Vivienda, 31 aglomerados, semestral.

- Propietarios totales: {first['owner_total']:.1f}% en 2S-2016 y {latest['owner_total']:.1f}% en 2S-2025; cambio {latest['owner_total']-first['owner_total']:+.1f} pp.
- Inquilinos: {first['renter']:.1f}% en 2S-2016 y {latest['renter']:.1f}% en 2S-2025; cambio {latest['renter']-first['renter']:+.1f} pp.
- Desde 2S-2023: propietarios {latest['owner_total']-shock['owner_total']:+.1f} pp; inquilinos {latest['renter']-shock['renter']:+.1f} pp.

La condición de tenencia no mide valor, calidad, deuda hipotecaria ni alquiler/ingreso. Las categorías no se convierten en una puntuación de bienestar y los cambios no se atribuyen causalmente a un gobierno.

## Controles

{results}
"""


def main() -> None:
    source = SOURCE_HTML.read_text(encoding="utf-8")
    if 'id="pendulo-vivienda-observada-v143"' in source:
        raise RuntimeError("La fuente v142 ya contiene v143")
    rows = extract_json_const(source, "housingTenure")
    metrics = extract_json_const(source, "PEND_POWER_METRICS")
    salaries = salary_changes(source)

    text = source
    asset_function = "function pendPowerChange(value){const delta=value-100,sign=delta>0?'+':delta<0?'−':'';return `${sign}${pendPowerFmt(Math.abs(delta),1)}% real`}"
    if text.count(asset_function) != 1:
        raise RuntimeError("No se encontró la colisión de nombre esperada")
    text = text.replace(asset_function, asset_function.replace("pendPowerChange", "pendPowerAssetChange"), 1)
    asset_call = "${pendPowerChange(last[key])} desde dic-2023"
    if text.count(asset_call) != 1:
        raise RuntimeError("No se encontró la llamada de Activos esperada")
    text = text.replace(asset_call, "${pendPowerAssetChange(last[key])} desde dic-2023", 1)

    css_marker = '<style id="rutas-publico-privado-v139">'
    if css_marker not in text:
        raise RuntimeError("No se encontró marcador CSS")
    text = text.replace(css_marker, HOUSING_CSS + "\n" + css_marker, 1)

    housing_start = text.index('      <div class="pend-layer-panel" data-pend-layer-panel="housing"')
    housing_end = text.index('      <div class="pend-layer-panel" data-pend-layer-panel="fiscal"', housing_start)
    text = text[:housing_start] + HOUSING_PANEL + text[housing_end:]

    script = HOUSING_SCRIPT_TEMPLATE.replace("__HOUSING_ROWS__", json.dumps(rows, ensure_ascii=False, separators=(",", ":")))
    script_marker = '<script id="rutas-publico-privado-script-v139">'
    if script_marker not in text:
        raise RuntimeError("No se encontró marcador JS")
    text = text.replace(script_marker, script + script_marker, 1)
    activation = "if(layer==='finance'){renderPendPowerFinance();renderPendPowerFinanceObserved();}"
    if activation not in text:
        raise RuntimeError("No se encontró activación de capas")
    text = text.replace(activation, activation + "\n if(layer==='housing')requestAnimationFrame(renderPendPowerHousing);", 1)

    tenure_metric = next(metric for metric in metrics if metric["id"] == "housing_tenure_status")
    tenure_metric.update(
        {
            "period": "2S-2016–2S-2025",
            "status": "integrado en la capa Vivienda",
            "note": "Composición observada de tenencia EPH; no mide costo, valor ni deuda de la vivienda.",
        }
    )

    first, latest = rows[0], rows[-1]
    shock = next(row for row in rows if row["period"] == "2S-2023")
    tests = {
        "asset_salary_function_collision_removed": text.count("function pendPowerChange(") == 1 and "function pendPowerAssetChange(value)" in text,
        "asset_summary_uses_renamed_function": "pendPowerAssetChange(last[key])" in text,
        "salary_macri_restored": abs(salaries["Macri"] - (-17.786096621644532)) < 1e-9,
        "salary_alberto_restored": abs(salaries["Alberto"] - (-12.493450900482205)) < 1e-9,
        "salary_milei_restored": abs(salaries["Milei"] - 4.202776000000008) < 1e-9,
        "housing_coverage": first["period"] == "2S-2016" and latest["period"] == "2S-2025" and len(rows) == 19,
        "housing_latest_values": latest["owner_total"] == 68.3 and latest["renter"] == 20.5,
        "housing_long_changes": abs((latest["owner_total"] - first["owner_total"]) - (-3.7)) < 1e-9 and abs((latest["renter"] - first["renter"]) - 2.8) < 1e-9,
        "housing_post_2023_changes": abs((latest["owner_total"] - shock["owner_total"]) - 1.7) < 1e-9 and abs((latest["renter"] - shock["renter"]) - (-1.5)) < 1e-9,
        "rent_income_gap_preserved": "Alquiler / ingreso" in HOUSING_PANEL and "faltante visible" in HOUSING_PANEL,
        "housing_renderer_connected": "renderPendPowerHousing" in text and "if(layer==='housing')" in text,
        "finance_preserved": 'id="pendPowerFinanceRealChart"' in text,
        "assets_preserved": 'id="pendPowerAssetChart"' in text,
        "six_layers_preserved": text.count('class="pend-layer-btn') == 6,
        "tab_count_preserved": text.count('class="tab-btn') == source.count('class="tab-btn'),
    }
    ids = re.findall(r'\bid="([^"]+)"', text)
    tests["html_ids_unique"] = len(ids) == len(set(ids))
    if not all(tests.values()):
        failed = ", ".join(name for name, ok in tests.items() if not ok)
        raise RuntimeError(f"Fallaron controles: {failed}")

    DERIVED_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_HTML.write_text(text, encoding="utf-8")
    INDEX_HTML.write_text(text, encoding="utf-8")
    REGISTRY_JSON.write_text(json.dumps(metrics, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_csv(HOUSING_CSV, rows)
    digest = hashlib.sha256(OUTPUT_HTML.read_bytes()).hexdigest()
    AUDIT_MD.write_text(make_audit(rows, salaries, digest, tests), encoding="utf-8")
    TESTS_JSON.write_text(json.dumps(tests, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(OUTPUT_HTML), "sha256": digest, "tests": tests, "salary_changes": salaries}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
