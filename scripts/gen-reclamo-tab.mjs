import { readFileSync, writeFileSync } from 'node:fs'
const RC = 'C:/Github/Tuneando inflacion/Legacy/inflacion/Reclamo colectivo/02_CALCULOS_Y_METODOLOGIA/'
const OUT = 'C:/Github/Tuneando inflacion/Legacy/inflacion/assets/reclamo-credito-tab.js'

function parseCsv(text) {
  const lines = text.replace(/\uFEFF/g, '').split(/\r?\n/).filter((l) => l.length)
  const rows = lines.map((l) => { const o = []; let c = ''; let q = false; for (const ch of l) { if (ch === '"') q = !q; else if (ch === ',' && !q) { o.push(c); c = '' } else c += ch } o.push(c); return o.map((x) => x.replace(/^"|"$/g, '')) })
  const head = rows[0].map((h) => h.replace(/\uFEFF/g, ''))
  return rows.slice(1).map((r) => Object.fromEntries(head.map((h, i) => [h, r[i]])))
}
const eu = (s) => { if (s == null || s === '') return null; const n = parseFloat(String(s).replace(/\./g, '').replace(',', '.')); return Number.isFinite(n) ? n : null }
const dot = (s) => { const n = parseFloat(s); return Number.isFinite(n) ? n : null }
const r2 = (n) => n == null ? null : Math.round(n * 100) / 100

// ── ROA por grupo (E-4, dot decimals) ──
const roaRows = parseCsv(readFileSync(RC + 'E-4__bank_roa_snapshot_may2026.csv', 'utf8'))
const roa = roaRows.map((r) => ({ g: r.group, v12: r2(dot(r.roa_12m_may2026)), v12prev: r2(dot(r.roa_12m_may2025)) }))

// ── Peso del interés de personales en el ingreso financiero (B-11, EU decimals) ──
const panelRows = parseCsv(readFileSync(RC + 'B-11__bcra_panel_bancos_resumen_2023_2026.csv', 'utf8'))
const peso = panelRows.map((r) => ({ d: r.corte_publicacion, v: r2(eu(r.intereses_personales_sobre_ingresos_financieros_pct_no_consolidado)) }))

// ── CFT comparable jun-2023 (M-2, controles PASS: EEFF 321%, PNFC 588%, +267pp, 1.83x) ──
const cft = { eeff: 321, pnfc: 588, gap: 267, ratio: 1.83 }

console.log('roa:', roa)
console.log('peso:', peso)

const J = (x) => JSON.stringify(x)
const lastPeso = peso[peso.length - 1]
const sistemaRoa = roa.find((r) => r.g === 'Sistema financiero')

const asset = `(() => {
  'use strict';
  if (document.getElementById('reclamo-credito-tab-v1')) return;

  const style = document.createElement('style');
  style.id = 'reclamo-credito-tab-v1';
  style.textContent = \`
.reclamo-case{display:grid;grid-template-columns:auto 1fr;gap:12px;align-items:center;padding:12px 14px;border:1px solid #e4d9e7;border-radius:14px;background:#fbf9fc;margin-top:8px}
.reclamo-case .big{font-size:22px;font-weight:900;color:#573f63;white-space:nowrap}
.reclamo-case small{display:block;color:#78687d;font-size:9.5px;line-height:1.5}
\`;
  document.head.appendChild(style);

  const tabs = document.getElementById('dash-main-tabs');
  const anchorBtn = tabs?.querySelector('[data-tab="tab-mora-ley"]') || tabs?.querySelector('[data-tab="tab-youth-credit"]');
  if (!tabs || !anchorBtn) return;
  anchorBtn.insertAdjacentHTML('afterend', \`<button class="tab-btn" type="button" data-tab="tab-reclamo-credito">Costo del crédito · reclamo</button>\`);

  const anchorPanel = document.getElementById('tab-mora-ley') || document.getElementById('tab-youth-credit');
  if (!anchorPanel) return;
  anchorPanel.insertAdjacentHTML('afterend', \`
  <section id="tab-reclamo-credito" class="tab-panel">
    <div class="epica-shell">
      <header class="epica-hero">
        <div>
          <span class="epica-eyebrow">§ Dossier · reclamo colectivo</span>
          <h2>Costo del crédito: qué muestran los datos públicos</h2>
          <p>El costo del crédito al consumo fue muy alto y el no bancario, mucho más caro que el bancario. Pero costo para el hogar no es lo mismo que ganancia del proveedor: precio, contrafactual y resultado contable son tres preguntas distintas que no se suman.</p>
        </div>
        <aside class="epica-status-card">
          <div><strong>Expediente de investigación, no demanda</strong><small>BCRA: Régimen de Transparencia (IIF 1S-2023), Informe sobre Bancos y panel de balances. Las huellas SHA-256 prueban integridad de las copias, no autenticidad contractual.</small></div>
          <div class="epica-status-row"><span class="epica-chip observed">observado</span><span class="epica-chip proxy">CFT ofrecido, no pagado</span><span class="epica-chip open">ganancia neta N/D</span></div>
        </aside>
      </header>

      <div class="epica-kpis" aria-live="polite">
        <article class="epica-kpi"><small>CFT máx. no bancario (PNFC)</small><b>${cft.pnfc}%</b><span>jun-2023 · promedio ofrecido</span></article>
        <article class="epica-kpi"><small>CFT máx. bancario (EEFF)</small><b>${cft.eeff}%</b><span>jun-2023 · +${cft.gap} pp de brecha</span></article>
        <article class="epica-kpi"><small>ROA del sistema (12m)</small><b>${sistemaRoa.v12.toString().replace('.', ',')}%</b><span>may-2026 · resultado contable</span></article>
        <article class="epica-kpi"><small>Interés de personales / ingreso financiero</small><b>${lastPeso.v.toString().replace('.', ',')}%</b><span>${lastPeso.d} · control no consolidado</span></article>
      </div>

      <div class="epica-grid">
        <section class="epica-panel">
          <div class="epica-panel-head"><div><h3>Costo Financiero Total máximo ofrecido</h3><p>Promedio del CFT máximo, junio 2023. Muestra de las 15 entidades y 15 PNFC con más deudores en el Régimen de Transparencia.</p></div><span class="epica-chip observed">BCRA · IIF gráfico 18</span></div>
          <div id="reclamoCftChart" class="epica-chart" role="img" aria-label="CFT máximo ofrecido bancos vs no bancarios, junio 2023"></div>
          <div class="epica-formula"><b>Brecha:</b> PNFC − EEFF = +${cft.gap} pp · cociente ${cft.ratio.toString().replace('.', ',')}×. No es costo promedio pagado, ingreso del proveedor, saldo de cartera ni dato 2026.</div>
        </section>
        <aside class="epica-panel">
          <div class="epica-panel-head"><div><h3>Contrato de lectura · anti-doble conteo</h3></div></div>
          <div class="epica-answer-grid">
            <div class="epica-answer good"><b>Precio del crédito (CFT/TNA)</b><p>Perspectiva del deudor: cuánto cuesta tomar deuda. Es lo que muestran estos gráficos.</p></div>
            <div class="epica-answer caution"><b>Contrafactual monetario (la "pinza")</b><p>Se construye contra una norma histórica; vive en la pestaña de tasas. No se suma al costo.</p></div>
            <div class="epica-answer caution"><b>Resultado contable (ROA)</b><p>Lo que el intermediario gana sobre su activo. Ni el CFT ni la pinza se convierten en ganancia.</p></div>
            <div class="epica-answer open"><b>Regla</b><p>Ninguno de los tres sustituye a los otros ni se suma. La ganancia neta por cartera no está en los datos públicos.</p></div>
          </div>
        </aside>
      </div>

      <div class="epica-grid equal">
        <section class="epica-panel">
          <div class="epica-panel-head"><div><h3>Rentabilidad contable por grupo</h3><p>ROA anualizado a 12 meses, mayo 2026. Costo alto del crédito no implica ROA alto.</p></div><span class="epica-chip observed">BCRA · Informe de bancos</span></div>
          <div id="reclamoRoaChart" class="epica-chart" role="img" aria-label="ROA por grupo de entidades, mayo 2026"></div>
          <div class="epica-formula"><b>EFNB ≠ PNFC/fintech.</b> El ROA del sistema cayó −0,67 pp interanual. No se infiere rentabilidad fintech desde TNA, CFT ni EFNB.</div>
        </section>
        <section class="epica-panel">
          <div class="epica-panel-head"><div><h3>Peso del interés de préstamos personales</h3><p>Intereses de personales sobre el ingreso financiero de los bancos. Control no consolidado: usar como tendencia, no como total del sistema.</p></div><span class="epica-chip proxy">control</span></div>
          <div id="reclamoPesoChart" class="epica-chart" role="img" aria-label="Peso del interés de personales en el ingreso financiero, 2023-2026"></div>
          <div class="reclamo-case"><div class="big">Caso MasVentas</div><small>Formularios de solicitud, tarifario y constancias públicas preservados como caso concreto. Los datos públicos no acreditan por sí solos qué CFT se cobró en un contrato individual.</small></div>
        </section>
      </div>

      <section class="epica-panel">
        <div class="epica-panel-head"><div><h3>Alcance del reclamo</h3></div><button type="button" class="epica-toggle" onclick="activateTab('tab-rates')">Ver foto macro en Tasas →</button></div>
        <div class="epica-answer-grid">
          <div class="epica-answer good"><b>Qué muestran los datos</b><p>Un costo del crédito alto y una brecha grande del no bancario frente al bancario, con rentabilidad contable modesta y variable entre grupos.</p></div>
          <div class="epica-answer caution"><b>Qué no muestran</b><p>Una tasa legal o justa, el CFT contractual completo con cargos y seguros, ni la ganancia neta de una cartera.</p></div>
          <div class="epica-answer open"><b>Dato faltante para pasar de sobrecosto a beneficio</b><p>Costo de fondeo, mora por cohortes, previsiones, encajes, impuestos, costo de capital, gastos operativos asignables, recuperos, comisiones/seguros y estructura contractual.</p></div>
          <div class="epica-answer caution"><b>Quiebre metodológico jul-2024</b><p>El umbral reportable de la Central de Deudores pasó de $1.000 a $25.000: las series de cobertura antes y después no se empalman.</p></div>
        </div>
      </section>

      <section class="sources-box"><h3>Fuentes y descarga</h3>
        <div class="source-links">
          <a class="source-link" target="_blank" rel="noopener" href="https://www.bcra.gob.ar/publicaciones/informe-sobre-bancos-mayo-de-2026/">🏦 Fuente · BCRA Informe sobre bancos (may-2026)</a>
          <a class="source-link" target="_blank" rel="noopener" href="https://www.bcra.gob.ar/archivos/Pdfs/PublicacionesEstadisticas/informes/InfBanc0526.xlsx">⬇ Fuente · planilla BCRA bancos / ROA (xlsx)</a>
          <a class="source-link" target="_blank" rel="noopener" href="https://www.bcra.gob.ar/archivos/Catalogo/Content/files/pdf/regimen-transparencia-v1.pdf">📄 Fuente · Régimen de Transparencia (CFT)</a>
          <a class="source-link" target="_blank" rel="noopener" href="https://api.bcra.gob.ar/transparencia/v1.0/Prestamos/Personales">🔌 Fuente en vivo · API BCRA transparencia (CFT/TEA ofrecido hoy)</a>
        </div>
        <div class="source-links" style="margin-top:7px">
          <span class="epica-chip">Copias archivadas · fallback</span>
          <a class="download-link" download href="Reclamo colectivo/02_CALCULOS_Y_METODOLOGIA/E-4__bank_roa_snapshot_may2026.csv">⬇ ROA por grupo (CSV)</a>
          <a class="download-link" download href="Reclamo colectivo/02_CALCULOS_Y_METODOLOGIA/B-11__bcra_panel_bancos_resumen_2023_2026.csv">⬇ panel de bancos (CSV)</a>
        </div>
        <div class="sources-note"><b>Resolución de datos:</b> los enlaces "Fuente" apuntan a los archivos y la API publicados por el BCRA; las copias archivadas (SHA-256 en el dossier) son el fallback reproducible. La API de transparencia devuelve la foto <b>actual</b> del CFT/TEA ofrecido por entidad (dato distinto del CFT comparable de jun-2023). <b>Corte:</b> CFT jun-2023 · ROA may-2026 · panel may-2026. <b>Nota:</b> este es un expediente de investigación, no una demanda; antes de presentar deben completarse demandantes, demandados, contratos, clase, competencia y revisión por persona abogada matriculada.</div>
      </section>
    </div>
  </section>\`);

  const plotConfig = { responsive:true, displaylogo:false, displayModeBar:false };
  function plotBase(mobile) {
    return {paper_bgcolor:'rgba(0,0,0,0)',plot_bgcolor:'#fff',font:{family:'Inter,system-ui,sans-serif',size:mobile?9:10,color:'#65516d'},margin:{l:mobile?48:60,r:18,t:24,b:mobile?70:56},hoverlabel:{bgcolor:'#fff',bordercolor:'#d9cde0',font:{color:'#5d4867'}}};
  }

  const CFT = ${J(cft)};
  const ROA = ${J(roa)};
  const PESO = ${J(peso)};

  function renderReclamoCft() {
    const t = document.getElementById('reclamoCftChart'); if (!t || !window.Plotly) return;
    const mobile = innerWidth <= 720;
    const traces = [{type:'bar',x:['Bancos (EEFF)','No bancarios (PNFC)'],y:[CFT.eeff,CFT.pnfc],text:[CFT.eeff+'%',CFT.pnfc+'%'],textposition:'outside',cliponaxis:false,hovertemplate:'<b>%{x}</b><br>CFT máx. %{y}%<extra></extra>'}];
    const layout = {...plotBase(mobile),showlegend:false,yaxis:{title:'CFT máximo ofrecido %',range:[0,660],gridcolor:'#e9e2ee',fixedrange:true},xaxis:{fixedrange:true}};
    Plotly.react(t,traces,layout,plotConfig);
  }
  function renderReclamoRoa() {
    const t = document.getElementById('reclamoRoaChart'); if (!t || !window.Plotly) return;
    const mobile = innerWidth <= 720;
    const traces = [{type:'bar',x:ROA.map(r=>r.g),y:ROA.map(r=>r.v12),text:ROA.map(r=>String(r.v12).replace('.',',')+'%'),textposition:'outside',cliponaxis:false,hovertemplate:'<b>%{x}</b><br>ROA 12m %{y:.2f}%<extra></extra>'}];
    const layout = {...plotBase(mobile),showlegend:false,yaxis:{title:'ROA 12m % del activo',gridcolor:'#e9e2ee',fixedrange:true,zeroline:true,zerolinecolor:'#b9a9c2'},xaxis:{tickangle:mobile?-30:0,fixedrange:true}};
    Plotly.react(t,traces,layout,plotConfig);
  }
  function renderReclamoPeso() {
    const t = document.getElementById('reclamoPesoChart'); if (!t || !window.Plotly) return;
    const mobile = innerWidth <= 720;
    const traces = [{type:'scatter',mode:'lines+markers',x:PESO.map(r=>r.d),y:PESO.map(r=>r.v),line:{width:2.4},hovertemplate:'%{x}<br><b>%{y:.2f}%</b> del ingreso financiero<extra></extra>'}];
    const layout = {...plotBase(mobile),showlegend:false,yaxis:{title:'% del ingreso financiero',gridcolor:'#e9e2ee',fixedrange:true,zeroline:false},xaxis:{fixedrange:true}};
    Plotly.react(t,traces,layout,plotConfig);
  }

  window.renderReclamoCredito = () => { renderReclamoCft(); renderReclamoRoa(); renderReclamoPeso(); };

  tabs.querySelector('[data-tab="tab-reclamo-credito"]')?.addEventListener('click', () => window.setTimeout(window.renderReclamoCredito, 160));
  window.addEventListener('resize', () => ['reclamoCftChart','reclamoRoaChart','reclamoPesoChart'].forEach(id => { const el = document.getElementById(id); if (el?.data) Plotly.Plots.resize(el); }));
})();
`

writeFileSync(OUT, asset, 'utf8')
console.log('\\nWrote', OUT, '(' + asset.length + ' chars)')
