import { readFileSync, writeFileSync } from 'node:fs'
const DATOS = 'C:/Github/Tuneando inflacion/Legacy/inflacion/Mora/05_ANALISIS_Y_CALCULOS/datos/'
const OUT = 'C:/Github/Tuneando inflacion/Legacy/inflacion/assets/mora-ley-tab.js'

const num = (s) => { if (s == null) return null; const v = String(s).replace(/^"|"$/g, '').replace(/\uFEFF/g, '').replace(/\./g, s.includes(',') ? '' : '.').replace(',', '.'); const n = parseFloat(v); return Number.isFinite(n) ? n : null }
// robust CSV parse (handles quoted commas)
function parseCsv(text) {
  const lines = text.replace(/\uFEFF/g, '').split(/\r?\n/).filter((l) => l.length)
  const rows = lines.map((l) => {
    const out = []; let cur = ''; let q = false
    for (const ch of l) { if (ch === '"') q = !q; else if (ch === ',' && !q) { out.push(cur); cur = '' } else cur += ch }
    out.push(cur); return out.map((c) => c.replace(/^"|"$/g, ''))
  })
  const head = rows[0]
  return rows.slice(1).map((r) => Object.fromEntries(head.map((h, i) => [h.replace(/\uFEFF/g, ''), r[i]])))
}
// number with European decimals ("28,96239") or dot decimals
const eu = (s) => { if (s == null || s === '') return null; const n = parseFloat(String(s).replace(/\./g, '').replace(',', '.')); return Number.isFinite(n) ? n : null }
const dot = (s) => { if (s == null || s === '') return null; const n = parseFloat(s); return Number.isFinite(n) ? n : null }
const r2 = (n) => n == null ? null : Math.round(n * 100) / 100
const r3 = (n) => n == null ? null : Math.round(n * 1000) / 1000

// ── Mora bancaria de hogares (mensual, dot decimals) ──
const bankAll = parseCsv(readFileSync(DATOS + 'morosidad_hogares.csv', 'utf8'))
const bank = bankAll.filter((r) => r.date >= '2021-01-01').map((r) => ({
  d: r.date.slice(0, 7),
  h: r3(dot(r.households_pct)),
  pc: r3(dot(r.households_personal_cards_pct)),
  cum: r3(dot(r.cumulative_excess_pp_month)),
}))
const preShockMean = r3(dot(bankAll[0].historical_mean_pre_shock_pct))

// ── Mora PNFC (mensual, dot decimals) ──
const pnfcAll = parseCsv(readFileSync(DATOS + 'morosidad_pnfc.csv', 'utf8'))
const pnfc = pnfcAll.filter((r) => r.date >= '2022-01-01').map((r) => ({
  d: r.date.slice(0, 7),
  total: r2(dot(r.pnfc_total_pct)),
  personal: r2(dot(r.pnfc_personal_pct)),
  cards: r2(dot(r.pnfc_cards_pct)),
  fintech: r2(dot(r.fintech_pct)),
}))

// ── Costo real del crédito (anual) ──
const costAll = parseCsv(readFileSync(DATOS + 'costo_credito_personal_resumen_anual_2023_2026.csv', 'utf8'))
const cost = costAll.map((r) => ({
  year: r.year,
  infl: r2(dot(r.promedio_inflacion_12m_pct)),
  teaReal: r2(dot(r.promedio_tasa_real_tea_pct)),
  cfteaReal: r2(dot(r.promedio_tasa_real_cftea_proxy_pct)),
}))

// ── Cobertura de personales (mensual, EU decimals, dos tramos) ──
const covAll = parseCsv(readFileSync(DATOS + 'bcra_inclusion_prestamos_personales_2023_2025.csv', 'utf8'))
const cov = covAll.map((r) => ({ d: r.periodo, v: r2(eu(r.cobertura_personales_pct_poblacion_adulta)), tramo: r.tramo_metodologico?.[0] || 'A' }))

// KPIs (últimos datos verificados)
const lastBank = bank[bank.length - 1]
const lastPnfc = pnfc[pnfc.length - 1]
const lastCov = cov[cov.length - 1]

const DATA = { bank, preShockMean, pnfc, cost, cov, lastBank, lastPnfc, lastCov }
console.log('bank rows:', bank.length, 'último:', lastBank)
console.log('pnfc rows:', pnfc.length, 'último:', lastPnfc)
console.log('cost:', cost)
console.log('cov rows:', cov.length, 'último:', lastCov, '· tramos:', [...new Set(cov.map(c => c.tramo))])

// ─────────────────────────────────────────────────────────────────────────────
// Asset IIFE (estilo EPICA; parseEpicaAsset lo pre-materializa en Dashito).
// Reusa primitivas .epica-* (ya tematizadas 3 skins) + .mora-ley-* mínimas.
// ─────────────────────────────────────────────────────────────────────────────
const J = (x) => JSON.stringify(x)

const asset = `(() => {
  'use strict';
  if (document.getElementById('mora-ley-tab-v1')) return;

  const style = document.createElement('style');
  style.id = 'mora-ley-tab-v1';
  style.textContent = \`
.mora-ley-calc{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);gap:14px}
.mora-ley-calc .epica-amount-control{margin:6px 0}
.mora-ley-out{display:grid;gap:8px}
.mora-ley-out .row{display:flex;justify-content:space-between;gap:12px;padding:8px 11px;border:1px solid #e7e1ed;border-radius:12px;background:#fdfcfe;font-size:11px}
.mora-ley-out .row b{color:#573f63}
.mora-ley-out .row.cmp{border-color:#b8ddcd;background:#f4fff9}
.mora-ley-out .row.cmp strong{font-size:16px;color:#2f8263}
.mora-ley-presets{display:flex;flex-wrap:wrap;gap:7px;margin:4px 0 2px}
@media(max-width:820px){.mora-ley-calc{grid-template-columns:1fr}}
\`;
  document.head.appendChild(style);

  const tabs = document.getElementById('dash-main-tabs');
  const anchorBtn = tabs?.querySelector('[data-tab="tab-youth-credit"]');
  if (!tabs || !anchorBtn) return;
  anchorBtn.insertAdjacentHTML('afterend', \`<button class="tab-btn" type="button" data-tab="tab-mora-ley">Hogares en mora · propuesta</button>\`);

  const anchorPanel = document.getElementById('tab-youth-credit');
  if (!anchorPanel) return;
  anchorPanel.insertAdjacentHTML('afterend', \`
  <section id="tab-mora-ley" class="tab-panel">
    <div class="epica-shell">
      <header class="epica-hero">
        <div>
          <span class="epica-eyebrow">⚖ Dossier · proyecto de ley</span>
          <h2>Hogares en mora: del diagnóstico a la propuesta</h2>
          <p>La mora de los hogares se multiplicó desde fines de 2023 mientras el sistema financiero conservó capacidad de absorción. El deterioro justifica un régimen preventivo y de reestructuración; no prueba por sí solo que toda tasa sea abusiva ni que el costo del crédito sea la única causa.</p>
        </div>
        <aside class="epica-status-card">
          <div><strong>Evidencia oficial auditada</strong><small>BCRA (informes may/jun 2026), Central de Deudores CENDEU y régimen PNFC. 11/11 controles automáticos en PASS.</small></div>
          <div class="epica-status-row"><span class="epica-chip observed">observado</span><span class="epica-chip proxy">CFTEA aproximado</span><span class="epica-chip open">causalidad no probada</span></div>
        </aside>
      </header>

      <div class="epica-kpis" aria-live="polite">
        <article class="epica-kpi"><small>Mora bancaria de hogares</small><b>${lastBank.h.toString().replace('.', ',')}%</b><span>may-2026 · ×4,75 vs nov-2023</span></article>
        <article class="epica-kpi"><small>Personales + tarjetas</small><b>${lastBank.pc.toString().replace('.', ',')}%</b><span>may-2026 · ×6,07 vs nov-2023</span></article>
        <article class="epica-kpi"><small>Mora PNFC total &gt;90 días</small><b>${lastPnfc.total.toString().replace('.', ',')}%</b><span>feb-2026</span></article>
        <article class="epica-kpi"><small>PNFC en préstamos personales</small><b>${lastPnfc.personal.toString().replace('.', ',')}%</b><span>feb-2026</span></article>
        <article class="epica-kpi"><small>Cobertura de personales</small><b>${lastCov.v.toString().replace('.', ',')}%</b><span>dic-2025 · tramo $25.000</span></article>
      </div>

      <div class="epica-grid">
        <section class="epica-panel">
          <div class="epica-panel-head"><div><h3>Trayectoria de la mora bancaria de hogares</h3><p>% del saldo financiado. La línea punteada es el promedio pre-shock (${preShockMean.toString().replace('.', ',')}%).</p></div><span class="epica-chip observed">BCRA · mensual</span></div>
          <div id="moraLeyBancariaChart" class="epica-chart tall" role="img" aria-label="Mora bancaria de hogares y de personales más tarjetas, 2021-2026"></div>
        </section>
        <aside class="epica-panel">
          <div class="epica-panel-head"><div><h3>Cómo leerlo</h3></div></div>
          <div class="epica-answer-grid">
            <div class="epica-answer good"><b>Qué muestran los datos</b><p>El saldo irregular como porcentaje de las financiaciones a familias. Mide saldo, no cantidad de personas.</p></div>
            <div class="epica-answer caution"><b>Qué no muestran</b><p>Nuevos morosos: el stock cambia por pagos, originaciones, refinanciaciones, castigos, ventas y reclasificaciones.</p></div>
            <div class="epica-answer open"><b>Dato faltante para causalidad</b><p>Serie por hogar que enlace ingreso, gastos esenciales, servicio de deuda y atrasos por tramo a 3/6/12 meses.</p></div>
          </div>
        </aside>
      </div>

      <div class="epica-grid equal">
        <section class="epica-panel">
          <div class="epica-panel-head"><div><h3>Proveedores no financieros y fintech</h3><p>Mora &gt;90 días, % del saldo. Otro universo: no es comparable 1:1 con el bancario.</p></div><span class="epica-chip observed">PNFC · mensual</span></div>
          <div id="moraLeyPnfcChart" class="epica-chart" role="img" aria-label="Mora PNFC total, personales, tarjetas y fintech"></div>
        </section>
        <section class="epica-panel">
          <div class="epica-panel-head"><div><h3>Costo real del crédito personal</h3><p>Tasa real anual promedio. 2024 fue licuado por la inflación; al desacelerar, tasas altas se volvieron costo real fuertemente positivo.</p></div><span class="epica-chip proxy">CFTEA aproximado</span></div>
          <div id="moraLeyCostoChart" class="epica-chart" role="img" aria-label="Tasa real TEA y CFTEA aproximada por año"></div>
          <div class="epica-formula"><b>Tasa real:</b> <code>r_real = ((1 + tasa_nominal_efectiva) / (1 + inflación_12m)) − 1</code>. Correlación máxima tasa real–mora: <b>r = 0,488</b> con 6 meses de rezago (83 obs.); asociación moderada, no prueba causal.</div>
        </section>
      </div>

      <section class="epica-panel">
        <div class="epica-panel-head"><div><h3>Capacidad Máxima de Pago (CMP) — simulador del método</h3><p>Dos límites simultáneos protegen el ingreso y el mínimo vital del hogar. Cargá ingreso y mínimo vital; probá los ejemplos del articulado.</p></div><span class="epica-chip open">presunción revisable</span></div>
        <div class="mora-ley-presets" role="group" aria-label="Ejemplos del método">
          <button class="epica-toggle" type="button" data-mora-preset="A" onclick="moraApplyPreset('A')">Ej. A · sin excedente</button>
          <button class="epica-toggle" type="button" data-mora-preset="B" onclick="moraApplyPreset('B')">Ej. B · excedente limita</button>
          <button class="epica-toggle" type="button" data-mora-preset="C" onclick="moraApplyPreset('C')">Ej. C · límite nominal</button>
          <button class="epica-toggle" type="button" data-mora-preset="D" onclick="moraApplyPreset('D')">Ej. D · vulnerable</button>
        </div>
        <div class="mora-ley-calc">
          <div>
            <div class="epica-amount-control"><label for="moraInch">Ingreso neto del hogar (INCH)<input id="moraInch" type="range" min="0" max="6000000" step="50000" value="2000000" oninput="moraCmpCalc()"></label><output id="moraInchOut">$2.000.000</output></div>
            <div class="epica-amount-control"><label for="moraMvh">Mínimo Vital del Hogar (MVH)<input id="moraMvh" type="range" min="0" max="6000000" step="50000" value="1600000" oninput="moraCmpCalc()"></label><output id="moraMvhOut">$1.600.000</output></div>
            <label class="epica-chip" style="cursor:pointer;user-select:none"><input id="moraVuln" type="checkbox" style="margin-right:6px" onchange="moraCmpCalc()">Hogar vulnerable (15% / 60%)</label>
            <div class="epica-formula" style="margin-top:10px"><code>ED = máx(0; INCH − MVH)</code><br><code>CMP = mín(20%·INCH; 70%·ED)</code> · vulnerable <code>mín(15%; 60%)</code></div>
          </div>
          <div class="mora-ley-out">
            <div class="row"><span>Excedente distribuible (ED)</span><b id="moraEd">—</b></div>
            <div class="row"><span id="moraLimIncLabel">20% del ingreso</span><b id="moraLimInc">—</b></div>
            <div class="row"><span id="moraLimExcLabel">70% del excedente</span><b id="moraLimExc">—</b></div>
            <div class="row cmp"><span>Capacidad Máxima de Pago</span><strong id="moraCmp">—</strong></div>
            <p id="moraCmpNote" class="epica-path-note"></p>
          </div>
        </div>
      </section>

      <section class="epica-panel">
        <div class="epica-panel-head"><div><h3>De la evidencia al diseño legal</h3></div></div>
        <div class="epica-answer-grid">
          <div class="epica-answer good"><b>Hipótesis que sobrevive</b><p>Los proveedores profesionales fijan precio, evalúan riesgo, provisionan y controlan la originación: por eso deben internalizar las consecuencias de una evaluación irresponsable o de cargos ilegales.</p></div>
          <div class="epica-answer good"><b>Solvencia agregada preservada</b><p>ROA 1,1% y previsiones del 86,3% de la cartera irregular (may-2026): el Estado no necesita comprar cartera privada para crear reestructuración y segunda oportunidad.</p></div>
          <div class="epica-answer caution"><b>Quiebre estadístico jul-2024</b><p>El umbral reportable de la Central de Deudores pasó de $1.000 a $25.000: las series de cobertura antes y después no se empalman mecánicamente.</p></div>
          <div class="epica-answer open"><b>Cobertura universal necesaria</b><p>Los deudores PNFC equivalen al 85% de las personas deudoras del sistema: una ley limitada a bancos dejaría fuera el centro del problema.</p></div>
        </div>
      </section>

      <section class="sources-box"><h3>Fuentes y descarga</h3>
        <div class="source-links">
          <a class="source-link" target="_blank" rel="noopener" href="https://www.bcra.gob.ar/publicaciones/informe-sobre-bancos-mayo-de-2026/">🏦 Fuente · BCRA Informe sobre bancos (may-2026)</a>
          <a class="source-link" target="_blank" rel="noopener" href="https://www.bcra.gob.ar/archivos/Pdfs/PublicacionesEstadisticas/informes/InfBanc0526.xlsx">⬇ Fuente · planilla BCRA bancos (xlsx)</a>
          <a class="source-link" target="_blank" rel="noopener" href="https://www.bcra.gob.ar/publicaciones/informe-de-proveedores-no-financieros-de-credito-junio-de-2026/">🏦 Fuente · BCRA Informe PNFC (jun-2026)</a>
          <a class="source-link" target="_blank" rel="noopener" href="https://www.bcra.gob.ar/archivos/Pdfs/PublicacionesEstadisticas/informes/series-informe-proveedores-no-financieros-credito-junio-2026.xlsx">⬇ Fuente · series PNFC (xlsx)</a>
          <a class="source-link" target="_blank" rel="noopener" href="https://www.bcra.gob.ar/archivos/Catalogo/Content/files/pdf/regimen-transparencia-v1.pdf">📄 Fuente · Régimen de Transparencia (costo)</a>
        </div>
        <div class="source-links" style="margin-top:7px">
          <span class="epica-chip">Copias archivadas · fallback</span>
          <a class="download-link" download href="Mora/05_ANALISIS_Y_CALCULOS/datos/morosidad_hogares.csv">⬇ mora bancaria (CSV)</a>
          <a class="download-link" download href="Mora/05_ANALISIS_Y_CALCULOS/datos/morosidad_pnfc.csv">⬇ mora PNFC (CSV)</a>
          <a class="download-link" download href="Mora/05_ANALISIS_Y_CALCULOS/datos/costo_credito_personal_resumen_anual_2023_2026.csv">⬇ costo real (CSV)</a>
          <button class="epica-toggle" type="button" onclick="downloadMoraLeyCsv()">⬇ serie en pantalla (CSV)</button>
        </div>
        <div class="sources-note"><b>Resolución de datos:</b> los enlaces "Fuente" apuntan a los archivos publicados por el BCRA; las copias archivadas (SHA-256 en el dossier) son el fallback reproducible cuando la fuente cambia de ruta. Las series de los gráficos son <b>derivadas</b> de esas planillas oficiales. <b>Corte:</b> bancario may-2026 · PNFC feb-2026 · cobertura dic-2025. <b>Comparador:</b> promedio pre-shock ${preShockMean.toString().replace('.', ',')}% y ventana espejo de 30 meses. <b>Nota:</b> los datos públicos acreditan el deterioro agregado, no la ganancia neta por línea ni el CFT de cada contrato individual.</div>
      </section>
    </div>
  </section>\`);

  const plotConfig = { responsive:true, displaylogo:false, displayModeBar:false };
  function plotBase(mobile) {
    return {paper_bgcolor:'rgba(0,0,0,0)',plot_bgcolor:'#fff',font:{family:'Inter,system-ui,sans-serif',size:mobile?9:10,color:'#65516d'},margin:{l:mobile?48:60,r:18,t:24,b:mobile?92:68},hoverlabel:{bgcolor:'#fff',bordercolor:'#d9cde0',font:{color:'#5d4867'}}};
  }

  const BANK = ${J(bank)};
  const PRE_SHOCK_MEAN = ${preShockMean};
  const PNFC = ${J(pnfc)};
  const COST = ${J(cost)};

  function renderMoraBancaria() {
    const t = document.getElementById('moraLeyBancariaChart'); if (!t || !window.Plotly) return;
    const mobile = innerWidth <= 720, x = BANK.map(r => r.d);
    const traces = [
      {type:'scatter',mode:'lines',name:'Hogares',x,y:BANK.map(r=>r.h),line:{width:2.4},hovertemplate:'%{x}<br><b>Hogares</b> %{y:.2f}%<extra></extra>'},
      {type:'scatter',mode:'lines',name:'Personales + tarjetas',x,y:BANK.map(r=>r.pc),line:{width:2.4},hovertemplate:'%{x}<br><b>Pers.+tarjetas</b> %{y:.2f}%<extra></extra>'},
    ];
    const layout = {...plotBase(mobile),hovermode:'x unified',legend:{orientation:'h',y:1.12},yaxis:{title:'% del saldo',gridcolor:'#e9e2ee',fixedrange:true,zeroline:false},xaxis:{fixedrange:true},shapes:[{type:'line',xref:'paper',x0:0,x1:1,y0:PRE_SHOCK_MEAN,y1:PRE_SHOCK_MEAN,line:{color:'#8ba1af',dash:'dot',width:1.4}}],annotations:[{xref:'paper',x:0.01,y:PRE_SHOCK_MEAN,yanchor:'bottom',text:'promedio pre-shock '+String(PRE_SHOCK_MEAN).replace('.',',')+'%',showarrow:false,font:{size:9,color:'#8ba1af'}}]};
    Plotly.react(t,traces,layout,plotConfig);
  }
  function renderMoraPnfc() {
    const t = document.getElementById('moraLeyPnfcChart'); if (!t || !window.Plotly) return;
    const mobile = innerWidth <= 720, x = PNFC.map(r => r.d);
    const traces = [
      {type:'scatter',mode:'lines',name:'Total >90d',x,y:PNFC.map(r=>r.total),line:{width:2.4}},
      {type:'scatter',mode:'lines',name:'Personales',x,y:PNFC.map(r=>r.personal),line:{width:2}},
      {type:'scatter',mode:'lines',name:'Tarjetas',x,y:PNFC.map(r=>r.cards),line:{width:2}},
      {type:'scatter',mode:'lines',name:'Fintech',x,y:PNFC.map(r=>r.fintech),line:{width:2}},
    ];
    const layout = {...plotBase(mobile),hovermode:'x unified',legend:{orientation:'h',y:1.14},yaxis:{title:'% del saldo',gridcolor:'#e9e2ee',fixedrange:true,zeroline:false},xaxis:{fixedrange:true}};
    Plotly.react(t,traces,layout,plotConfig);
  }
  function renderMoraCosto() {
    const t = document.getElementById('moraLeyCostoChart'); if (!t || !window.Plotly) return;
    const mobile = innerWidth <= 720, x = COST.map(r => r.year);
    const traces = [
      {type:'bar',name:'Tasa real TEA',x,y:COST.map(r=>r.teaReal),hovertemplate:'%{x}<br><b>TEA real</b> %{y:.1f}%<extra></extra>'},
      {type:'bar',name:'Tasa real CFTEA aprox.',x,y:COST.map(r=>r.cfteaReal),hovertemplate:'%{x}<br><b>CFTEA real</b> %{y:.1f}%<extra></extra>'},
    ];
    const layout = {...plotBase(mobile),barmode:'group',hovermode:'x unified',legend:{orientation:'h',y:1.16},yaxis:{title:'tasa real anual %',gridcolor:'#e9e2ee',fixedrange:true,zeroline:true,zerolinecolor:'#b9a9c2'},xaxis:{fixedrange:true}};
    Plotly.react(t,traces,layout,plotConfig);
  }

  // ── Simulador CMP ──
  const money = (n) => '$' + Math.round(n).toLocaleString('es-AR');
  function moraCmpCalc() {
    const inch = +document.getElementById('moraInch').value;
    const mvh = +document.getElementById('moraMvh').value;
    const vuln = document.getElementById('moraVuln').checked;
    const ed = Math.max(0, inch - mvh);
    const pInc = vuln ? 0.15 : 0.20, pExc = vuln ? 0.60 : 0.70;
    const limInc = pInc * inch, limExc = pExc * ed, cmp = Math.min(limInc, limExc);
    document.getElementById('moraInchOut').textContent = money(inch);
    document.getElementById('moraMvhOut').textContent = money(mvh);
    document.getElementById('moraEd').textContent = money(ed);
    document.getElementById('moraLimIncLabel').textContent = (vuln?'15':'20') + '% del ingreso';
    document.getElementById('moraLimExcLabel').textContent = (vuln?'60':'70') + '% del excedente';
    document.getElementById('moraLimInc').textContent = money(limInc);
    document.getElementById('moraLimExc').textContent = money(limExc);
    document.getElementById('moraCmp').textContent = money(cmp);
    const note = document.getElementById('moraCmpNote');
    if (cmp <= 0) note.textContent = 'Sin excedente sobre el mínimo vital: no corresponde imponer cuota. Debe evaluarse espera, procedimiento sin activos y eventual exoneración.';
    else if (limInc < limExc) note.textContent = 'El límite nominal (una quinta/séptima parte del ingreso) manda: la ley evita afectar de más aunque el excedente sea amplio.';
    else note.textContent = 'El excedente sobre el mínimo vital manda: si el pasivo no se amortiza en 60 meses se necesita quita acordada o judicial, no una cuota globo.';
  }
  const PRESETS = { A:[1200000,1250000,false], B:[2000000,1600000,false], C:[3000000,1500000,false], D:[1800000,1500000,true] };
  function applyPreset(k){ const p = PRESETS[k]; if(!p) return; document.getElementById('moraInch').value=p[0]; document.getElementById('moraMvh').value=p[1]; document.getElementById('moraVuln').checked=p[2]; moraCmpCalc(); }

  window.moraCmpCalc = moraCmpCalc;
  window.moraApplyPreset = applyPreset;
  window.renderMoraLey = () => { renderMoraBancaria(); renderMoraPnfc(); renderMoraCosto(); moraCmpCalc(); };
  window.downloadMoraLeyCsv = () => {
    const head = 'periodo,mora_hogares_pct,mora_personales_tarjetas_pct';
    const rows = BANK.map(r => r.d + ',' + r.h + ',' + r.pc);
    const blob = new Blob([head + '\\n' + rows.join('\\n')], {type:'text/csv'});
    const a = document.createElement('a'); a.href = URL.createObjectURL(blob); a.download = 'mora_ley_bancaria_hogares.csv'; a.click();
  };

  // Interactividad vía handlers inline (oninput/onclick/onchange) en el markup:
  // LegacyMarkup los convierte a handlers React, robustos frente al ciclo de montaje.

  tabs.querySelector('[data-tab="tab-mora-ley"]')?.addEventListener('click', () => window.setTimeout(window.renderMoraLey, 160));
  window.addEventListener('resize', () => ['moraLeyBancariaChart','moraLeyPnfcChart','moraLeyCostoChart'].forEach(id => { const el = document.getElementById(id); if (el?.data) Plotly.Plots.resize(el); }));
})();
`

writeFileSync(OUT, asset, 'utf8')
console.log('\\nWrote', OUT, '(' + asset.length + ' chars)')
