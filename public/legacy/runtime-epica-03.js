(() => {
  'use strict';

  if (document.getElementById('political-wealth-v2')) return;

  const scriptUrl = document.currentScript?.src;
  const publicBaseUrl = scriptUrl ? new URL('../',scriptUrl) : new URL('./',document.baseURI);
  const DATA_URL = new URL('research/political_wealth_2026-09-01/derived/dashboard_data_2017_2025.json',publicBaseUrl).href;
  const ROSTER_URL = new URL('research/political_wealth_2026-09-01/derived/active_politicians_coverage_2026-09-01.json',publicBaseUrl).href;
  const RESEARCH_URL = new URL('research/political_wealth_2026-09-01/derived/active_politician_research_summary_2026-09-01.json',publicBaseUrl).href;
  const KARINA_AUDIT_URL = new URL('research/political_wealth_2026-09-01/derived/karina_milei_revaluation_audit_2023_2025.json',publicBaseUrl).href;
  const JAVIER_AUDIT_URL = new URL('research/political_wealth_2026-09-01/derived/javier_milei_revaluation_audit_2023_2025.json',publicBaseUrl).href;
  const ROMINA_AUDIT_URL = new URL('research/political_wealth_2026-09-01/derived/romina_del_pla_patrimonial_audit_2023_2024.json',publicBaseUrl).href;
  const GABRIELA_AUDIT_URL = new URL('research/political_wealth_2026-09-01/derived/gabriela_estevez_patrimonial_audit_2022_2024.json',publicBaseUrl).href;
  const NATALIA_AUDIT_URL = new URL('research/political_wealth_2026-09-01/derived/natalia_gadano_patrimonial_audit_2023_2024.json',publicBaseUrl).href;
  const YOLANDA_AUDIT_URL = new URL('research/political_wealth_2026-09-01/derived/yolanda_vega_patrimonial_audit_2023_2024.json',publicBaseUrl).href;
  const ALEJANDRO_AUDIT_URL = new URL('research/political_wealth_2026-09-01/derived/alejandro_bongiovanni_patrimonial_audit_2023_2024.json',publicBaseUrl).href;
  const FACUNDO_AUDIT_URL = new URL('research/political_wealth_2026-09-01/derived/facundo_correa_llano_patrimonial_audit_2023_2024.json',publicBaseUrl).href;
  const PATRICIA_AUDIT_URL = new URL('research/political_wealth_2026-09-01/derived/patricia_vasquez_patrimonial_audit_2023_2024.json',publicBaseUrl).href;
  const SOURCE_CONSISTENCY_URL = new URL('research/political_wealth_2026-09-01/derived/active_series_source_consistency_summary_2022_2024.json',publicBaseUrl).href;

  async function fetchJson(url,label){
    let lastError;
    for(const delay of [0,180,650]){
      if(delay) await new Promise(resolve=>window.setTimeout(resolve,delay));
      try{
        const response = await fetch(url,{cache:'no-store',credentials:'same-origin'});
        if(!response.ok) throw new Error(`HTTP ${response.status}`);
        return await response.json();
      }catch(error){
        lastError = error;
      }
    }
    throw new Error(`${label}: ${lastError?.message||'falló la carga'}`);
  }


  const tabs = document.getElementById('dash-main-tabs');
  const castaButton = tabs?.querySelector('[data-tab="tab-casta"]');
  const castaPanel = document.getElementById('tab-casta');
  if (!tabs || !castaButton || !castaPanel) return;

  castaButton
  castaPanel

  let payload = null;
  let rosterPayload = null;
  let researchSummary = null;
  let researchQueueById = new Map();
  let sourceConsistencyByPerson = new Map();
  let personSearchEntries = [];
  let selectedPerson = 'maximo';
  const plotConfig = {displayModeBar:false,responsive:true,scrollZoom:false,doubleClick:false};
  const byId = id => document.getElementById(id);
  const num = value => value === '' || value == null ? null : Number(value);
  const pct = value => {
    const number = num(value);
    if (number == null) return 'N/D';
    return `${number > 0 ? '+' : ''}${number.toLocaleString('es-AR',{minimumFractionDigits:1,maximumFractionDigits:1})}%`;
  };
  const money = value => {
    const number = num(value);
    if (number == null) return 'N/D';
    const millions = number / 1e6;
    return `$ ${millions.toLocaleString('es-AR',{minimumFractionDigits:millions < 100 ? 1 : 0,maximumFractionDigits:1})} M`;
  };
  const sourceLabel = state => state === 'oficial_consolidado_oa' ? 'oficial consolidado' : state === 'publicado_pdf_oa_pendiente' ? 'provisional · PDF OA pendiente' : 'N/D';
  const esc = value => String(value ?? '').replace(/[&<>"']/g,char=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[char]));
  const searchText = value => String(value ?? '').normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase();

  function personRows(id){ return payload.series.filter(row => row.persona_id === id); }
  function coverageRow(id){ return payload.coverage.find(row => row.persona_id === id); }
  function sourceConsistencyIssue(id){
    const rows = sourceConsistencyByPerson.get(id) || [];
    const valid = state => state === 'concilia' || state === 'concilia_cero';
    const assetIssues = rows.filter(row=>!valid(row.bienes_estado));
    const debtIssues = rows.filter(row=>!valid(row.deudas_estado));
    const years = values => [...new Set(values.map(row=>row.anio))].sort().join(', ');
    const parts = [];
    if(assetIssues.length) parts.push(`${assetIssues.length} control${assetIssues.length===1?'':'es'} de bienes no concilia${assetIssues.length===1?'':'n'} (${years(assetIssues)})`);
    if(debtIssues.length) parts.push(`${debtIssues.length} control${debtIssues.length===1?'':'es'} de deuda requiere${debtIssues.length===1?'':'n'} revisión (${years(debtIssues)})`);
    return {rows,assetIssues,debtIssues,anyIssues:assetIssues.length+debtIssues.length>0,alert:parts.join('; ')};
  }

  function syncPersonSelection(id){
    selectedPerson = id;
    document.querySelectorAll('[data-pw-person]').forEach(item=>{
      const active = item.dataset.pwPerson === id;
      item.classList.toggle('active',active);
      item.setAttribute('aria-pressed',String(active));
    });
    const select = byId('pwPersonSelect');
    if (select?.querySelector(`option[value="${CSS.escape(id)}"]`)) select.value = id;
  }

  function choosePerson(id,{showView=false}={}){
    if (!payload?.people.some(person=>person.persona_id===id)) return;
    syncPersonSelection(id);
    if (showView) setView('person');
    renderPerson();
  }

  function renderPersonDirectory(){
    const input = byId('pwPersonSearch');
    const select = byId('pwPersonSelect');
    const query = searchText(input?.value).trim();
    const matches = personSearchEntries.filter(entry=>!query || entry.haystack.includes(query));
    const currentVisible = matches.some(entry=>entry.person.persona_id===selectedPerson);
    select.innerHTML = matches.length
      ? `${currentVisible?'':`<option value="">Elegí entre ${matches.length.toLocaleString('es-AR')} coincidencias…</option>`}${matches.map(entry=>`<option value="${esc(entry.person.persona_id)}">${esc(entry.optionLabel)}</option>`).join('')}`
      : '<option value="">Sin coincidencias</option>';
    select.disabled = !matches.length;
    select.value = currentVisible ? selectedPerson : '';
    document.querySelectorAll('[data-pw-person]').forEach(button=>{
      button.hidden = !matches.some(entry=>entry.person.persona_id===button.dataset.pwPerson);
    });
    byId('pwPersonSearchStatus').textContent = query
      ? `${matches.length.toLocaleString('es-AR')} ${matches.length===1?'coincidencia':'coincidencias'}. Podés abrir la primera con Enter.`
      : `${matches.length.toLocaleString('es-AR')} trayectorias disponibles. Buscá o usá el selector.`;
    byId('pwPersonDirectoryCount').textContent = `${matches.length.toLocaleString('es-AR')} visibles`;
    return matches;
  }

  function analyzeSeriesQuality(rows){
    const observed = rows.filter(row=>num(row.total_bienes_real_ars_2025)!=null).sort((a,b)=>Number(a.anio)-Number(b.anio));
    const comparisons = [];
    let zeroBase = null;
    for(let index=1;index<observed.length;index+=1){
      const start = observed[index-1];
      const end = observed[index];
      if(Number(end.anio)-Number(start.anio)!==1) continue;
      const startValue = num(start.total_bienes_real_ars_2025);
      const endValue = num(end.total_bienes_real_ars_2025);
      if(startValue===0 && endValue>0){zeroBase={start,end};continue;}
      if(!(startValue>0) || endValue==null) continue;
      comparisons.push({start,end,change:(endValue/startValue-1)*100});
    }
    if(zeroBase) return {kind:'review',short:`${zeroBase.start.anio}→${zeroBase.end.anio} · base cero`,label:'Base cero',detail:'El porcentaje no es calculable: pasar de cero a un valor positivo no equivale a crecimiento infinito.'};
    if(!comparisons.length) return {kind:'open',short:'sin par interanual',label:'Comparación interanual',detail:'No hay dos cierres consecutivos positivos para calcular una variación real.'};
    const peak = comparisons.sort((a,b)=>Math.abs(b.change)-Math.abs(a.change))[0];
    const magnitude = Math.abs(peak.change);
    const kind = magnitude>=200?'review':magnitude>=50?'caution':'good';
    const typeChange = peak.start.tipo_ddjj===peak.end.tipo_ddjj ? peak.end.tipo_ddjj : `${peak.start.tipo_ddjj}→${peak.end.tipo_ddjj}`;
    return {kind,short:`${peak.start.anio}→${peak.end.anio} · ${pct(peak.change)} real`,label:'Mayor cambio real interanual',detail:`${pct(peak.change)} entre ${peak.start.anio} y ${peak.end.anio} (${typeChange}). Es una señal para revisar composición y perímetro, no una conclusión sobre su causa.`};
  }

  function renderPerson(){
    if (!payload) return;
    const rows = personRows(selectedPerson);
    const observed = rows.filter(row => num(row.total_bienes_ars) != null);
    const first = observed[0];
    const last = observed[observed.length - 1];
    const coverage = coverageRow(selectedPerson);
    const person = payload.people.find(item => item.persona_id === selectedPerson);
    const caseAudit = payload?.case_audits?.[selectedPerson];
    const sourceCheck = sourceConsistencyIssue(selectedPerson);
    const sourceIntegritySuspended = caseAudit?.metadata?.serie_estado?.startsWith('suspendida') || sourceCheck.assetIssues.length>0;
    const sourceIntegrityOpen = sourceIntegritySuspended || sourceCheck.debtIssues.length>0;
    const sourceIntegrityAlert = caseAudit?.alerta_fuente || sourceCheck.alert;
    const quality = analyzeSeriesQuality(rows);
    const historicFederal = person?.alcance_serie === 'historial_federal_previo_no_ddjj_provincial_actual';
    const historicPublic = person?.alcance_serie === 'historial_publico_oa_previo_no_equivale_ddjj_mandato_actual';
    const historicScopeLabel = historicFederal ? 'historial federal previo' : historicPublic ? 'historial OA previo' : '';
    const historicScopeWarning = historicFederal
      ? 'estos valores corresponden a un cargo público nacional previo; no representan una DDJJ del mandato provincial actual ni permiten inferir el patrimonio presente.'
      : historicPublic
        ? 'estos valores forman un historial público OA previo al corte; pueden incluir la Legislatura CABA o cargos nacionales anteriores y no equivalen por sí solos a la DDJJ del mandato actual.'
        : '';
    const metricFirst = observed.find(row => Number(row.anio) === Number(coverage.anio_base_metricas)) || first;
    const provisional = last.estado_fuente === 'publicado_pdf_oa_pendiente';

    byId('pwPersonScopeBadge').textContent = `${coverage.anios_oficiales_2017_2024}/8 años oficiales${historicScopeLabel ? ` · ${historicScopeLabel}` : ''}`;
    byId('pwStartLabel').textContent = `Base comparable · ${metricFirst.anio}`;
    byId('pwStartValue').textContent = money(metricFirst.total_bienes_ars);
    byId('pwStartNote').textContent = sourceLabel(metricFirst.estado_fuente);
    byId('pwEndLabel').textContent = `Último dato · ${last.anio}`;
    byId('pwEndValue').textContent = money(last.total_bienes_ars);
    const latestAssetIssue = sourceCheck.assetIssues.some(row=>Number(row.anio)===Number(last.anio));
    byId('pwEndNote').textContent = latestAssetIssue ? 'dato crudo · control resumen↔detalle' : sourceLabel(last.estado_fuente);
    byId('pwEndKpi').className = `pw-kpi ${provisional || latestAssetIssue ? 'review' : 'expected'}`;
    byId('pwNominalChange').textContent = pct(coverage.cambio_nominal_primero_ultimo_pct);
    byId('pwNominalNote').textContent = `${metricFirst.anio}→${last.anio}`;
    byId('pwRealChange').textContent = pct(coverage.cambio_real_primero_ultimo_pct);
    byId('pwUsdChange').textContent = pct(coverage.cambio_usd_primero_ultimo_pct);
    byId('pwRealNote').textContent = `CAGR ${pct(coverage.cagr_real_anual_pct)} anual · pesos de 2025`;
    byId('pwUsdNote').textContent = `CAGR ${pct(coverage.cagr_usd_anual_pct)} anual · A3500`;
    byId('pwTrendTitle').textContent = `${person.persona}: bienes declarados bajo tres lentes`;
    byId('pwTrendSubtitle').textContent = `Base ${metricFirst.anio}=100 · huecos sin interpolar${provisional ? ' · 2025 provisional' : ''}${historicScopeLabel ? ' · no equivale a DDJJ actual' : ''}${sourceIntegritySuspended ? ' · serie con control de bienes abierto' : ''}.`;
    const missing = coverage.anios_faltantes_2017_2024 === 'ninguno' ? 'Ninguno entre 2017 y 2024.' : coverage.anios_faltantes_2017_2024.replaceAll('|', ', ');
    byId('pwPersonReading').innerHTML = `
      <div class="epica-answer good"><b>Ventana observada</b><p>${first.anio}→${last.anio}; métricas comparables desde ${metricFirst.anio}; ${coverage.anios_oficiales_2017_2024} registros oficiales en 2017–2024.</p></div>
      <div class="epica-answer caution"><b>Huecos oficiales</b><p>${missing}</p></div>
      <div class="epica-answer ${provisional || latestAssetIssue ? 'open' : 'good'}"><b>Último estado</b><p>${latestAssetIssue?'Dato oficial crudo con inconsistencia interna; ver control resumen↔detalle':sourceLabel(last.estado_fuente)}.</p></div>
      <div class="epica-answer ${quality.kind}"><b>${quality.label}</b><p>${quality.detail}</p></div>
      <div class="epica-answer ${sourceCheck.assetIssues.length?'open':sourceCheck.debtIssues.length?'caution':sourceCheck.rows.length?'good':'partial'}"><b>Resumen ↔ detalle · 2022–2024</b><p>${sourceCheck.anyIssues?esc(sourceCheck.alert):sourceCheck.rows.length?`${sourceCheck.rows.length} declaraciones controladas sin brecha en bienes ni deudas.`:'Sin declaración controlable en los años con detalle público.'}</p></div>`;
    byId('pwPersonCallout').innerHTML = `${sourceIntegrityOpen?`<strong>Control de fuente abierto:</strong> ${esc(sourceIntegrityAlert)}<br><br>`:''}${historicScopeWarning ? `<strong>Alcance:</strong> ${historicScopeWarning}<br><br>` : ''}<strong>Lectura neutral:</strong> el cambio nominal fue ${pct(coverage.cambio_nominal_primero_ultimo_pct)}, pero pasa a ${pct(coverage.cambio_real_primero_ultimo_pct)} al descontar IPC y a ${pct(coverage.cambio_usd_primero_ultimo_pct)} como equivalente A3500. Son lentes contables; ninguno prueba por sí solo el origen del cambio.`;

    if (window.Plotly) {
      const x = rows.map(row => String(row.anio));
      const traces = [
        {name:'Nominal',field:'indice_nominal_base',color:'#a35e7b'},
        {name:'Real IPC',field:'indice_real_base',color:'#4f9980'},
        {name:'USD A3500',field:'indice_usd_base',color:'#c29336'}
      ].map(spec => ({type:'scatter',mode:'lines+markers',name:spec.name,x,y:rows.map(row=>num(row[spec.field])),connectgaps:false,line:{color:spec.color,width:3},marker:{size:7},hovertemplate:`<b>%{x}</b><br>${spec.name} %{y:.1f}<extra></extra>`}));
      const provisionalRows = rows.filter(row => row.estado_fuente === 'publicado_pdf_oa_pendiente');
      if (provisionalRows.length) traces.push({type:'scatter',mode:'markers',name:'2025 provisional',x:provisionalRows.map(row=>String(row.anio)),y:provisionalRows.map(row=>num(row.indice_nominal_base)),marker:{size:13,symbol:'diamond-open',color:'#a54768',line:{width:2}},hovertemplate:'<b>%{x}</b><br>valor publicado · PDF OA pendiente<extra></extra>'});
      const mobile = window.innerWidth <= 720;
      Plotly.react('politicalWealthTrendChart',traces,{paper_bgcolor:'rgba(0,0,0,0)',plot_bgcolor:'#fff',font:{family:'Inter,system-ui,sans-serif',size:mobile?9:10,color:'#715e69'},margin:{l:mobile?48:60,r:18,t:45,b:48},legend:{orientation:'h',y:1.17},yaxis:{title:'Índice base=100',rangemode:'tozero',gridcolor:'#eee5ea',fixedrange:true},xaxis:{fixedrange:true,type:'category',categoryorder:'array',categoryarray:rows.map(row=>String(row.anio))},hovermode:'x unified'},plotConfig);
    }
    renderBenchmarks();
    renderComposition();
    renderReconciliation();
    renderCaseAudit();
  }

  function renderBenchmarks(){
    const rows = payload.benchmark_comparisons.filter(row => row.persona_id === selectedPerson);
    const audit = payload?.case_audits?.[selectedPerson];
    const sourceCheck = sourceConsistencyIssue(selectedPerson);
    if(audit?.metadata?.benchmark_estado?.startsWith('suspendido') || sourceCheck.assetIssues.length){
      const suspensionNote = audit?.metadata?.benchmark_suspension_note || 'El total de la serie no concilia con el detalle del mismo archivo oficial.';
      byId('pwBenchmarkSubtitle').textContent = `Comparación suspendida: ${suspensionNote}`;
      byId('pwBenchmarkCards').innerHTML = '<div class="pw-chart-empty" style="grid-column:1/-1;min-height:120px">N/D hasta resolver la inconsistencia de fuente.</div>';
      byId('pwBenchmarkReading').innerHTML = '<div class="epica-answer open"><b>No comparable</b><p>Calcular rendimiento sobre un total cuestionado produciría una precisión ficticia.</p></div>';
      byId('pwBenchmarkCallout').innerHTML = `<strong>Dato preservado, inferencia suspendida.</strong> ${esc(suspensionNote)} El resumen y el detalle se muestran en la lectura profunda; ninguno se elige por intuición.`;
      if(window.Plotly) Plotly.purge('politicalWealthBenchmarkChart');
      byId('politicalWealthBenchmarkChart').innerHTML = '<div class="pw-chart-empty">Benchmark suspendido por control de fuente.</div>';
      return;
    }
    if (!rows.length) {
      byId('pwBenchmarkSubtitle').textContent = 'Se necesitan al menos dos años con patrimonio positivo para calcular un CAGR comparable.';
      byId('pwBenchmarkCards').innerHTML = '<div class="pw-chart-empty" style="grid-column:1/-1;min-height:120px">Un solo año observado: el contrafactual queda N/D hasta sumar otro ejercicio.</div>';
      byId('pwBenchmarkReading').innerHTML = '<div class="epica-answer open"><b>Ventana insuficiente</b><p>No se anualiza un cambio de un único punto.</p></div>';
      byId('pwBenchmarkCallout').innerHTML = '<strong>N/D no es cero.</strong> El benchmark se habilitará cuando exista un segundo año comparable.';
      if (window.Plotly) Plotly.purge('politicalWealthBenchmarkChart');
      byId('politicalWealthBenchmarkChart').innerHTML = '<div class="pw-chart-empty">Sin ventana temporal comparable.</div>';
      return;
    }
    const riskMeta = {
      poco:{label:'Poco riesgo',kind:'low',description:'T-bills 3 meses · rollover proxy'},
      medio:{label:'Riesgo medio',kind:'medium',description:'Vanguard Balanced Index · 60/40'},
      mucho:{label:'Mucho riesgo',kind:'high',description:'MSCI ACWI · acciones globales'}
    };
    const observedUsd = num(rows[0].patrimonio_cagr_usd_a3500_pct);
    const observedReal = num(rows[0].patrimonio_cagr_real_pct);
    byId('pwBenchmarkSubtitle').textContent = `${rows[0].anio_inicio}→${rows[0].anio_fin} · retorno total USD · CAGR patrimonio USD A3500 ${pct(observedUsd)}.`;
    byId('pwBenchmarkCards').innerHTML = rows.map(row=>{const meta=riskMeta[row.riesgo];return `<article class="pw-benchmark-card ${meta.kind}"><small>${meta.label}</small><b>${pct(row.benchmark_cagr_usd_pct)} anual</b><p>${meta.description}<br>Acumulado: ${pct(row.benchmark_retorno_acumulado_usd_pct)} · brecha patrimonio−benchmark: ${pct(row.brecha_cagr_vs_patrimonio_usd_pp)} pp/año.</p></article>`;}).join('');
    byId('pwBenchmarkReading').innerHTML = `<div class="epica-answer good"><b>Patrimonio real IPC</b><p>CAGR ${pct(observedReal)} anual.</p></div><div class="epica-answer caution"><b>Patrimonio en USD</b><p>CAGR ${pct(observedUsd)} anual al A3500.</p></div><div class="epica-answer open"><b>Capital contrafactual</b><p>${money(rows[0].capital_final_contrafactual_ars_a3500)} a ${money(rows[2].capital_final_contrafactual_ars_a3500)}, según riesgo.</p></div>`;
    const caseWarning = audit?.metadata?.benchmark_nota
      ? `<br><br><strong>Lectura del caso.</strong> ${esc(audit.metadata.benchmark_nota)}`
      : selectedPerson === 'karina'
        ? '<br><br><strong>En este caso no debe leerse como rendimiento.</strong> El extremo 2025 es provisional y el salto está dominado por una diferencia de valuación del inmueble, no por una cartera que haya ganado esa tasa.'
        : selectedPerson === 'javier'
          ? '<br><br><strong>En este caso no debe leerse como rendimiento.</strong> El extremo 2025 es provisional y el puente profundo separa valuación, ingresos, gastos y variación real; superar un benchmark no prueba que una cartera haya ganado esa tasa.'
          : '';
    byId('pwBenchmarkCallout').innerHTML = `<strong>No describe la cartera real.</strong> Supone que todo el patrimonio inicial se convirtió al A3500, se invirtió sin aportes ni retiros, reinvirtió cupones/dividendos y volvió a pesos al cierre. Es antes de impuestos, sin apalancamiento y sin costos de acceso desde Argentina.${caseWarning}`;
    if (!window.Plotly) return;
    const labels = ['Patrimonio DDJJ',...rows.map(row=>riskMeta[row.riesgo].label)];
    const values = [observedUsd,...rows.map(row=>num(row.benchmark_cagr_usd_pct))];
    const colors = ['#715e69','#6eb092','#d2aa58','#a35e7b'];
    Plotly.react('politicalWealthBenchmarkChart',[{type:'bar',orientation:'h',y:labels,x:values,marker:{color:colors},text:values.map(value=>pct(value)),textposition:'auto',hovertemplate:'<b>%{y}</b><br>CAGR %{x:.2f}%<extra></extra>'}],{paper_bgcolor:'rgba(0,0,0,0)',plot_bgcolor:'#fff',font:{family:'Inter,system-ui,sans-serif',size:9,color:'#715e69'},margin:{l:105,r:18,t:18,b:45},xaxis:{title:'CAGR anual en USD (%)',zeroline:true,zerolinecolor:'#bbaeb6',gridcolor:'#eee5ea',fixedrange:true},yaxis:{fixedrange:true,autorange:'reversed'},showlegend:false},plotConfig);
  }

  function renderComposition(){
    const target = byId('politicalWealthCompositionChart');
    const rows = payload.composition.filter(row => row.persona_id === selectedPerson);
    if (!rows.length) {
      if (window.Plotly) Plotly.purge(target);
      target.innerHTML = '<div class="pw-chart-empty">No hay detalle abierto de bienes para esta trayectoria en 2022–2024. El total histórico se conserva, pero no se inventa su composición.</div>';
      byId('pwCompositionBadge').textContent = 'detalle N/D';
      return;
    }
    const year = Math.max(...rows.map(row => Number(row.anio)));
    const current = rows.filter(row => Number(row.anio) === year);
    byId('pwCompositionBadge').textContent = sourceConsistencyIssue(selectedPerson).assetIssues.length || payload?.case_audits?.[selectedPerson]?.metadata?.serie_estado?.startsWith('suspendida') ? `${year} · detalle control` : String(year);
    byId('pwCompositionTitle').textContent = `Composición ${year}`;
    if (!window.Plotly) return;
    Plotly.react(target,[{type:'pie',hole:.56,labels:current.map(row=>row.categoria),values:current.map(row=>num(row.importe_ars)),textinfo:'percent',hovertemplate:'<b>%{label}</b><br>$ %{value:,.0f}<br>%{percent}<extra></extra>',marker:{colors:['#7d536d','#4f9980','#d2aa58','#9c7eb4','#6d92ad','#cc7b79','#97a278']}}],{paper_bgcolor:'rgba(0,0,0,0)',font:{family:'Inter,system-ui,sans-serif',size:9,color:'#715e69'},margin:{l:10,r:10,t:16,b:30},legend:{orientation:'h',y:-.08}},plotConfig);
  }

  function renderCaseAudit(){
    const section = byId('pwCaseAudit');
    const audit = payload?.case_audits?.[selectedPerson];
    const visible = Boolean(audit);
    section.hidden = !visible;
    if (!visible) return;
    const latest = audit.periodos.find(row=>row.periodo === '2024-2025') || audit.periodos[audit.periodos.length-1];
    const reading = audit.lectura_epistemica;
    const shortList = values => values.map(value=>`• ${esc(value)}`).join('<br>');
    const endYear = String(latest.periodo).split('-').at(-1);
    byId('pwCaseTitle').textContent = `Lectura profunda · ${audit.metadata.persona}`;
    byId('pwCaseQuestion').textContent = audit.metadata.pregunta;
    byId('pwCaseChip').textContent = audit.metadata.etiqueta || 'anomalía documental · no conclusión penal';
    byId('pwCaseSource').textContent = audit.metadata.alcance;
    byId('pwCaseVerdict').textContent = reading.conclusion;
    const defaultMetrics = [
      {label:`Aumento bienes · ${endYear}`,valor:pct(latest.aumento_bienes_pct),nota:'stock bruto, no rendimiento de cartera'},
      {label:'Valuación / aumento',valor:pct(latest.valuacion_sobre_aumento_bienes_pct),nota:'puede superar 100% si otros bienes bajan'},
      {label:'Inmueble vs. IPC',valor:`${pct(latest.aumento_inmueble_pct)} / ${pct(latest.ipc_periodo_pct)}`,nota:'variación del último período'},
      {label:'Brecha vs. IPC simple',valor:money(latest.brecha_inmueble_vs_ipc_simple_ars),nota:'requiere base fiscal y cálculo'},
      {label:'IPC simple explica',valor:pct(latest.aumento_inmueble_explicado_por_ipc_simple_pct),nota:'del salto del inmueble'}
    ];
    const metrics = audit.metricas_destacadas?.length === 5 ? audit.metricas_destacadas : defaultMetrics;
    metrics.forEach((metric,index)=>{
      byId(`pwCaseMetricLabel${index}`).textContent = metric.label;
      byId(`pwCaseMetricValue${index}`).textContent = metric.valor;
      byId(`pwCaseMetricNote${index}`).textContent = metric.nota;
    });
    const defaultBridgeColumns = [
      {label:'Δ bienes',field:'aumento_bienes_ars',format:'money'},
      {label:'Diferencia valuación',field:'diferencia_valuacion_total_ars',format:'money'},
      {label:'% del aumento',field:'valuacion_sobre_aumento_bienes_pct',format:'pct'},
      {label:'Δ inmueble',field:'aumento_inmueble_pct',format:'pct'},
      {label:'IPC',field:'ipc_periodo_pct',format:'pct'}
    ];
    const bridgeColumns = audit.columnas_puente?.length === 5 ? audit.columnas_puente : defaultBridgeColumns;
    bridgeColumns.forEach((column,index)=>{byId(`pwCaseBridgeHeader${index}`).textContent=column.label;});
    const formatBridgeValue = (value,format) => format === 'money' ? money(value) : format === 'pct' ? pct(value) : String(value ?? '—');
    byId('pwCaseBridgeBody').innerHTML = audit.periodos.map(row=>{
      const sourceState = row.estado_fuente || '';
      const primary = sourceState.startsWith('oficial');
      const reconciled = sourceState === 'oficial_consolidado_oa';
      const statusLabel = reconciled ? 'oficial' : primary ? 'oficial · control' : 'provisional';
      const interpretation = row.lectura || (row.periodo === '2023-2024'
        ? 'El inmueble acompaña el IPC; la valuación explica sólo una parte del aumento bruto.'
        : 'La valuación supera el aumento bruto y el IPC anual sólo explica una fracción del salto del inmueble.');
      const cells = bridgeColumns.map(column=>`<td class="num">${esc(formatBridgeValue(row[column.field],column.format))}</td>`).join('');
      return `<tr><td><b>${esc(row.periodo)}</b></td><td><span class="pw-status ${reconciled?'expected':'review'}">${statusLabel}</span></td>${cells}<td>${esc(interpretation)}</td></tr>`;
    }).join('');
    byId('pwCaseReading').innerHTML = `
      <div class="epica-answer good"><b>Qué sí está documentado</b><p>${shortList(reading.documentado)}</p></div>
      <div class="epica-answer caution"><b>Qué podría explicarlo</b><p>${shortList(reading.compatible_pero_no_probado)}</p></div>
      <div class="epica-answer open"><b>Qué todavía no está probado</b><p>${shortList(reading.no_documentado)}</p></div>
      <div class="epica-answer caution"><b>Qué cerraría la pregunta</b><p>${shortList(reading.evidencia_para_cerrar)}</p></div>`;
    const fallbackAlert = selectedPerson === 'karina'
      ? 'El consolidado tiene una inconsistencia independiente en deudas: en 2023 el total resumen ($10,91 M) es diez veces la suma de sus cinco filas de detalle ($1,09 M), y el cierre 2024 tampoco coincide con la apertura 2025 publicada. El dato crudo se preserva, pero el residual automático queda suspendido.'
      : 'El dato crudo se preserva, pero no se interpreta como una pericia ni se atribuye a la persona.';
    byId('pwCaseSourceAlert').innerHTML = `<strong>Control de calidad de fuente.</strong> ${esc(audit.alerta_fuente || fallbackAlert)}`;
  }

  function renderReconciliation(){
    const rows = payload.reconciliation.filter(row => row.persona_id === selectedPerson);
    const target = byId('pwReconciliation');
    const suspended = payload?.case_audits?.[selectedPerson]?.reconciliation_suspended;
    if(suspended){
      byId('pwReconciliationSubtitle').textContent = `${suspended.periodo} · control suspendido por inconsistencia entre resumen y detalle`;
      target.innerHTML = `<div class="epica-answer caution"><b>No calculable de forma robusta</b><p>${esc(suspended.lectura)}</p></div><div class="epica-answer good"><b>Qué se conserva</b><p>Los valores de ambas capas, sus brechas y el identificador de la declaración quedan disponibles para auditoría.</p></div>`;
      return;
    }
    const sourceCheck = sourceConsistencyIssue(selectedPerson);
    const override = payload?.case_audits?.[selectedPerson]?.reconciliation_override;
    if (override) {
      byId('pwReconciliationSubtitle').textContent = `${override.periodo} · ${override.subtitulo || 'puente corregido contra el formulario individual'}`;
      target.innerHTML = `<div class="epica-answer good"><b>Δ patrimonio neto</b><p>${money(override.delta_patrimonio_neto_ars)}</p></div><div class="epica-answer caution"><b>Componentes disponibles</b><p>${money(override.componentes_disponibles_ars)}</p></div><div class="epica-answer good"><b>Residual ajustado</b><p>${money(override.residual_ajustado_ars)}</p></div><div class="epica-answer open"><b>Lectura</b><p>${esc(override.lectura)}</p></div>`;
      return;
    }
    if (selectedPerson === 'karina' && payload?.case_audits?.karina) {
      byId('pwReconciliationSubtitle').textContent = 'Control suspendido: los campos de deuda del consolidado no concilian entre resumen, detalle y apertura siguiente.';
      target.innerHTML = '<div class="epica-answer caution"><b>No calculable de forma robusta</b><p>Se conserva el dato crudo, pero no se presenta un residual automático hasta resolver la inconsistencia de origen.</p></div><div class="epica-answer good"><b>Puente alternativo</b><p>La auditoría profunda separa bienes brutos, valuación, inmueble e IPC sin usar ese total de deuda defectuoso.</p></div>';
      return;
    }
    if(sourceCheck.anyIssues){
      byId('pwReconciliationSubtitle').textContent = 'Control suspendido: resumen y detalle no concilian en bienes o deudas dentro de 2022–2024.';
      target.innerHTML = `<div class="epica-answer caution"><b>No calculable de forma robusta</b><p>${esc(sourceCheck.alert)}. Un residual mezclaría capas incompatibles.</p></div><div class="epica-answer good"><b>Qué se conserva</b><p>El barrido sistemático publica resumen, suma del detalle, ratio y estado por declaración.</p></div>`;
      return;
    }
    if (!rows.length) {
      byId('pwReconciliationSubtitle').textContent = 'Sin DJPI anual o de baja calculable en la ventana.';
      target.innerHTML = '<div class="epica-answer open"><b>N/D</b><p>No se fuerza una identidad con datos insuficientes.</p></div>';
      return;
    }
    const row = rows[rows.length - 1];
    byId('pwReconciliationSubtitle').textContent = `${row.anio} · ${row.tipo_ddjj} · dj_id ${row.dj_id}`;
    if (row.estado_calculo !== 'calculable') {
      target.innerHTML = '<div class="epica-answer open"><b>Dato de origen malformado</b><p>La fila se conserva y queda fuera del cálculo; no se corrige por inferencia.</p></div>';
      return;
    }
    target.innerHTML = `<div class="epica-answer good"><b>Δ patrimonio neto</b><p>${money(row.delta_patrimonio_neto_ars)}</p></div><div class="epica-answer caution"><b>Componentes disponibles</b><p>${money(row.suma_componentes_ars)}</p></div><div class="epica-answer open"><b>Residual</b><p>${money(row.residual_ars)}</p></div>`;
  }

  function renderCoverage(){
    if (!payload || !rosterPayload) return;
    const summary = rosterPayload.summary;
    byId('pwActiveCount').textContent = Number(summary.cargos_activos).toLocaleString('es-AR');
    byId('pwCurrentFilingCount').textContent = Number(summary.presentaciones_camara_localizadas).toLocaleString('es-AR');
    byId('pwOaUniqueCount').textContent = Number(summary.personas_con_nombre_compatible_unico_oa_2017_2024).toLocaleString('es-AR');
    byId('pwCuratedActiveCount').textContent = Number(researchSummary?.trayectorias_auditadas_activas ?? summary.personas_con_serie_curada_tab).toLocaleString('es-AR');
    byId('pwProvincialIndexed').textContent = `${Number(summary.legisladores_provinciales_nominales).toLocaleString('es-AR')} / ${Number(summary.bancas_provinciales_suma_fichas_dne).toLocaleString('es-AR')}`;
    byId('pwUniverseHeroCount').textContent = Number(summary.cargos_activos).toLocaleString('es-AR');
    byId('pwRosterScope').innerHTML = `<strong>${esc(rosterPayload.scope.title)}.</strong> ${esc(rosterPayload.scope.included)}<br><b>Todavía fuera:</b> ${esc(rosterPayload.scope.not_yet_included)} ${esc(rosterPayload.scope.next_layer_reference)}`;
    byId('pwCoverageBody').innerHTML = payload.coverage.map(row => {
      const gaps = row.anios_faltantes_2017_2024 === 'ninguno' ? 'ninguno' : row.anios_faltantes_2017_2024.replaceAll('|', ', ');
      const state2025 = row.dato_2025 === 'provisional_publicado' ? '<span class="pw-status review">provisional</span>' : '<span class="pw-status missing">N/D</span>';
      return `<tr><td><b>${row.persona}</b></td><td>${row.primer_anio_con_dato}–${row.ultimo_anio_con_dato}</td><td class="num">${row.anios_oficiales_2017_2024}/8</td><td>${gaps}</td><td>${state2025}</td><td class="num">${pct(row.cambio_real_primero_ultimo_pct)}</td></tr>`;
    }).join('');
    byId('pwProvincialCoverageBody').innerHTML = (rosterPayload.provincial_coverage || []).map(row => {
      const indexed = Number(row.legisladores_nominales_incorporados);
      const total = Number(row.bancas_total_ficha_dne);
      const complete = indexed === total;
      const status = complete
        ? '<span class="pw-status expected">nómina incorporada</span>'
        : '<span class="pw-status review">pendiente nominal</span>';
      const municipalities = Number(row.intendencias_ficha_dne) || '—';
      return `<tr><td><b>${esc(row.jurisdiccion_corta)}</b></td><td>${esc(row.tipo_legislatura)}</td><td class="num">${total.toLocaleString('es-AR')}</td><td class="num">${indexed.toLocaleString('es-AR')} / ${total.toLocaleString('es-AR')}</td><td class="num">${typeof municipalities === 'number' ? municipalities.toLocaleString('es-AR') : municipalities}</td><td>${status}</td></tr>`;
    }).join('');
    renderActiveRoster();
  }

  function currentStatus(row){
    const state = row.estado_ddjj_cargo_actual;
    if (state.startsWith('presentacion_')) return ['expected','presentación localizada'];
    if (state.startsWith('sin_presentacion_')) return ['missing','sin localizar en el listado'];
    if (state === 'listado_ddjj_2025_publicado_sin_cruce_nominal') return ['partial','listado 2025 · cruce pendiente'];
    if (state === 'ruta_provincial_localizada_sin_cruce_nominal') return ['partial','ruta oficial · cruce pendiente'];
    if (state === 'ruta_provincial_por_relevar') return ['review','ruta provincial pendiente'];
    return ['partial','verificación 2025/2026 pendiente'];
  }

  function oaStatus(row){
    const state = row.oa_historial_2017_2024_estado;
    if (state === 'nombre_compatible_unico_en_oa') return ['expected',`${row.oa_cantidad_anios_2017_2024} año${Number(row.oa_cantidad_anios_2017_2024)===1?'':'s'} · candidato único`];
    if (state === 'coincidencia_multiple_revisar_homonimia') return ['review','homonimia por revisar'];
    return ['missing','sin nombre compatible'];
  }

  function researchStatus(row){
    const item = researchQueueById.get(row.persona_id);
    if (!item) return ['missing','estado pendiente',''];
    if (item.estado_investigacion === 'freezado') return ['frozen','freezado',item.motivo_estado_investigacion||'Expansión pausada; la evidencia reunida se conserva.'];
    const labels = {
      serie_curada:['expected','serie curada'],
      identidad_confirmada_cruce_oficial:['expected','identidad + serie auditadas'],
      preclasificacion_fuerte_misma_institucion:['partial','evidencia institucional'],
      preclasificacion_nombre_y_cuit_unicos:['partial','identidad a cotejar'],
      historial_oa_posible_cargo_nacional_previo:['review','posible antecedente nacional'],
      revision_manual_identidad:['review','identidad a revisar'],
      homonimia_oa_por_resolver:['review','homonimia'],
      sin_registro_oa_2017_2024:['missing','buscar otra fuente'],
      sin_registro_oa_2017_2024_identidad_desambiguada:['missing','OA descartada · buscar régimen actual']
    };
    const [kind,label] = labels[item.estado_busqueda_patrimonial] || ['missing','estado pendiente'];
    return [kind,label,item.siguiente_accion||''];
  }

  function renderActiveRoster(){
    if (!rosterPayload) return;
    const query = searchText(byId('pwRosterSearch')?.value);
    const level = byId('pwRosterLevel')?.value || 'all';
    const status = byId('pwRosterStatus')?.value || 'all';
    const rows = rosterPayload.rows.filter(row => {
      const haystack = searchText([row.persona,row.cargo,row.jurisdiccion,row.partido_o_alianza].join(' '));
      if (query && !haystack.includes(query)) return false;
      if (level !== 'all' && row.nivel_cargo !== level) return false;
      if (status === 'filing' && !row.estado_ddjj_cargo_actual.startsWith('presentacion_')) return false;
      if (status === 'pending' && row.estado_ddjj_cargo_actual.startsWith('presentacion_')) return false;
      if (status === 'oa' && row.oa_historial_2017_2024_estado !== 'nombre_compatible_unico_en_oa') return false;
      if (status === 'series' && !payload.people.some(person=>person.persona_id===row.persona_id || person.persona_id===row.serie_tab_id)) return false;
      if (status === 'frozen' && researchQueueById.get(row.persona_id)?.estado_investigacion !== 'freezado') return false;
      return true;
    });
    byId('pwRosterVisibleCount').textContent = `Mostrando ${rows.length.toLocaleString('es-AR')} de ${rosterPayload.rows.length.toLocaleString('es-AR')} cargos`;
    byId('pwActiveRosterBody').innerHTML = rows.map(row => {
      const [currentKind,currentLabel] = currentStatus(row);
      const [oaKind,oaLabel] = oaStatus(row);
      const [researchKind,researchLabel,researchDetail] = researchStatus(row);
      const deepSeriesId = row.serie_tab_id || (payload.people.some(person=>person.persona_id===row.persona_id) ? row.persona_id : '');
      const frozen = researchQueueById.get(row.persona_id)?.estado_investigacion === 'freezado';
      const action = deepSeriesId ? `<button class="pw-open-series" type="button" data-pw-open-series="${esc(deepSeriesId)}">Abrir análisis</button>` : frozen ? '<span class="pw-status frozen">freezado</span>' : '<span class="pw-status missing">en cola</span>';
      const detail = row.detalle_ddjj_cargo_actual ? ` title="${esc(row.detalle_ddjj_cargo_actual)}"` : '';
      const researchTitle = researchDetail ? ` title="${esc(researchDetail)}"` : '';
      return `<tr><td><b>${esc(row.persona)}</b></td><td>${esc(row.cargo)}</td><td>${esc(row.jurisdiccion)}</td><td>${esc(row.partido_o_alianza)}</td><td><span class="pw-status ${currentKind}"${detail}>${currentLabel}</span></td><td><span class="pw-status ${oaKind}">${oaLabel}</span></td><td><span class="pw-status ${researchKind}"${researchTitle}>${researchLabel}</span></td><td>${action}</td></tr>`;
    }).join('') || '<tr><td colspan="8">No hay coincidencias con estos filtros.</td></tr>';
  }

  function openSeries(id){
    if (!payload.people.some(person=>person.persona_id===id)) return;
    const search = byId('pwPersonSearch');
    if (search) search.value = '';
    renderPersonDirectory();
    syncPersonSelection(id);
    setView('person');
    renderPerson();
    document.getElementById('tab-political-wealth')?.scrollIntoView({behavior:'smooth',block:'start'});
  }

  function setView(view){
    document.querySelectorAll('[data-pw-surface]').forEach(surface => {surface.hidden = surface.dataset.pwSurface !== view;});
    document.querySelectorAll('[data-pw-view]').forEach(button => {const active=button.dataset.pwView===view;button.classList.toggle('active',active);button.setAttribute('aria-pressed',String(active));});
    if (view === 'person') window.setTimeout(renderPerson,40);
    if (view === 'coverage') renderCoverage();
  }

  function initialize(data, roster, research, queue=[], caseAudits=[], sourceConsistency=null){
    if(sourceConsistency?.filas){
      data.source_consistency = sourceConsistency.filas;
      data.source_consistency_summary = sourceConsistency.resumen;
    }
    for (const audit of caseAudits || []) {
      const id = audit?.metadata?.persona_id;
      if (id) {
        data.case_audits = {...(data.case_audits||{}),[id]:audit};
        const existing = new Set((data.composition||[]).map(row=>`${row.persona_id}|${row.anio}|${row.categoria}`));
        data.composition.push(...(audit.composition||[]).filter(row=>!existing.has(`${row.persona_id}|${row.anio}|${row.categoria}`)));
      }
    }
    payload = data;
    rosterPayload = roster;
    researchSummary = research;
    researchQueueById = new Map(queue.map(item=>[item.persona_id,item]));
    sourceConsistencyByPerson = new Map();
    for(const row of data.source_consistency || []){
      const current = sourceConsistencyByPerson.get(row.persona_id) || [];
      current.push(row);
      sourceConsistencyByPerson.set(row.persona_id,current);
    }
    const rosterHeader = document.querySelector('#pwActiveRosterBody')?.closest('table')?.querySelector('thead tr');
    if (rosterHeader && rosterHeader.children.length === 7) rosterHeader.children[6].insertAdjacentHTML('beforebegin','<th>Investigación</th>');
    const sourceLinks = document.querySelector('#tab-political-wealth .source-links');
    if (sourceLinks && !sourceLinks.querySelector('[href*="active_series_source_consistency_audit_2022_2024.csv"]')) {
      sourceLinks.insertAdjacentHTML('afterbegin','<a class="download-link" download href="research/political_wealth_2026-09-01/derived/active_series_source_consistency_audit_2022_2024.csv">CSV · resumen vs. detalle · 545 DDJJ</a><a class="download-link" download href="research/political_wealth_2026-09-01/derived/active_series_source_consistency_summary_2022_2024.json">JSON · consistencia global 2022–2024</a>');
    }
    if (sourceLinks && !sourceLinks.querySelector('[href*="karina_milei_revaluation_bridge_2024_2025.csv"]')) {
      sourceLinks.insertAdjacentHTML('afterbegin','<a class="download-link" download href="research/political_wealth_2026-09-01/derived/karina_milei_revaluation_bridge_2024_2025.csv">CSV · puente de revaluación · Karina</a><a class="download-link" download href="research/political_wealth_2026-09-01/derived/karina_milei_source_consistency_audit_2023_2025.csv">CSV · consistencia de fuente · Karina</a><a class="download-link" download href="research/political_wealth_2026-09-01/derived/karina_milei_revaluation_audit_2023_2025.json">JSON · lectura profunda · Karina</a>');
    }
    if (sourceLinks && !sourceLinks.querySelector('[href*="javier_milei_patrimonial_bridge_2023_2025.csv"]')) {
      sourceLinks.insertAdjacentHTML('afterbegin','<a class="download-link" download href="research/political_wealth_2026-09-01/derived/javier_milei_patrimonial_bridge_2023_2025.csv">CSV · puente patrimonial · Javier</a><a class="download-link" download href="research/political_wealth_2026-09-01/derived/javier_milei_revaluation_components_2025.csv">CSV · componentes de valuación · Javier</a><a class="download-link" download href="research/political_wealth_2026-09-01/derived/javier_milei_source_consistency_audit_2023_2025.csv">CSV · consistencia de fuente · Javier</a><a class="download-link" download href="research/political_wealth_2026-09-01/derived/javier_milei_revaluation_audit_2023_2025.json">JSON · lectura profunda · Javier</a>');
    }
    if (sourceLinks && !sourceLinks.querySelector('[href*="romina_del_pla_source_consistency_audit_2023_2024.csv"]')) {
      sourceLinks.insertAdjacentHTML('afterbegin','<a class="download-link" download href="research/political_wealth_2026-09-01/derived/romina_del_pla_source_consistency_audit_2023_2024.csv">CSV · consistencia de fuente · Romina Del Plá</a><a class="download-link" download href="research/political_wealth_2026-09-01/derived/romina_del_pla_patrimonial_audit_2023_2024.json">JSON · lectura profunda · Romina Del Plá</a><a class="source-link" target="_blank" rel="noopener" href="https://www.hcdn.gob.ar/institucional/transparencia/declaraciones_juradas/listado/4407dd25-ea1a-11ef-b33c-00505689ffd4">Diputados · presentaciones 2024</a>');
    }
    if (sourceLinks && !sourceLinks.querySelector('[href*="gabriela_estevez_source_consistency_audit_2022_2024.csv"]')) {
      sourceLinks.insertAdjacentHTML('afterbegin','<a class="download-link" download href="research/political_wealth_2026-09-01/derived/gabriela_estevez_source_consistency_audit_2022_2024.csv">CSV · consistencia de fuente · Gabriela Estévez</a><a class="download-link" download href="research/political_wealth_2026-09-01/derived/gabriela_estevez_patrimonial_audit_2022_2024.json">JSON · lectura profunda · Gabriela Estévez</a>');
    }
    if (sourceLinks && !sourceLinks.querySelector('[href*="natalia_gadano_source_consistency_audit_2023_2024.csv"]')) {
      sourceLinks.insertAdjacentHTML('afterbegin','<a class="download-link" download href="research/political_wealth_2026-09-01/derived/natalia_gadano_source_consistency_audit_2023_2024.csv">CSV · consistencia de fuente · Natalia Gadano</a><a class="download-link" download href="research/political_wealth_2026-09-01/derived/natalia_gadano_patrimonial_audit_2023_2024.json">JSON · lectura profunda · Natalia Gadano</a>');
    }
    if (sourceLinks && !sourceLinks.querySelector('[href*="yolanda_vega_source_consistency_audit_2023_2024.csv"]')) {
      sourceLinks.insertAdjacentHTML('afterbegin','<a class="download-link" download href="research/political_wealth_2026-09-01/derived/yolanda_vega_source_consistency_audit_2023_2024.csv">CSV · consistencia de fuente · Yolanda Vega</a><a class="download-link" download href="research/political_wealth_2026-09-01/derived/yolanda_vega_patrimonial_audit_2023_2024.json">JSON · lectura profunda · Yolanda Vega</a>');
    }
    if (sourceLinks && !sourceLinks.querySelector('[href*="alejandro_bongiovanni_source_consistency_audit_2023_2024.csv"]')) {
      sourceLinks.insertAdjacentHTML('afterbegin','<a class="download-link" download href="research/political_wealth_2026-09-01/derived/alejandro_bongiovanni_source_consistency_audit_2023_2024.csv">CSV · consistencia de fuente · Alejandro Bongiovanni</a><a class="download-link" download href="research/political_wealth_2026-09-01/derived/alejandro_bongiovanni_patrimonial_audit_2023_2024.json">JSON · lectura profunda · Alejandro Bongiovanni</a>');
    }
    if (sourceLinks && !sourceLinks.querySelector('[href*="facundo_correa_llano_source_consistency_audit_2023_2024.csv"]')) {
      sourceLinks.insertAdjacentHTML('afterbegin','<a class="download-link" download href="research/political_wealth_2026-09-01/derived/facundo_correa_llano_source_consistency_audit_2023_2024.csv">CSV · consistencia de fuente · Facundo Correa Llano</a><a class="download-link" download href="research/political_wealth_2026-09-01/derived/facundo_correa_llano_patrimonial_audit_2023_2024.json">JSON · lectura profunda · Facundo Correa Llano</a>');
    }
    if (sourceLinks && !sourceLinks.querySelector('[href*="patricia_vasquez_source_consistency_audit_2023_2024.csv"]')) {
      sourceLinks.insertAdjacentHTML('afterbegin','<a class="download-link" download href="research/political_wealth_2026-09-01/derived/patricia_vasquez_source_consistency_audit_2023_2024.csv">CSV · consistencia de fuente · Patricia Vásquez</a><a class="download-link" download href="research/political_wealth_2026-09-01/derived/patricia_vasquez_patrimonial_audit_2023_2024.json">JSON · lectura profunda · Patricia Vásquez</a>');
    }
    if (sourceLinks && !sourceLinks.querySelector('[href*="active_politician_research_queue_2026-09-01.csv"]')) {
      const verifiedBatchFiles = [
        {batch:1,audit:'research/political_wealth_2026-09-01/derived/active_politician_identity_audit_iteration_1_2026-09-01.csv',series:'research/political_wealth_2026-09-01/derived/active_politician_verified_series_iteration_1_2017_2024.csv',benchmarks:'research/political_wealth_2026-09-01/derived/active_politician_verified_benchmarks_iteration_1_2017_2024.csv'},
        {batch:2,audit:'research/political_wealth_2026-09-01/derived/active_politician_identity_audit_iteration_2_2026-09-01.csv',series:'research/political_wealth_2026-09-01/derived/active_politician_verified_series_iteration_2_2017_2024.csv',benchmarks:'research/political_wealth_2026-09-01/derived/active_politician_verified_benchmarks_iteration_2_2017_2024.csv'},
        {batch:3,audit:'research/political_wealth_2026-09-01/derived/active_politician_identity_audit_iteration_3_2026-09-01.csv',series:'research/political_wealth_2026-09-01/derived/active_politician_verified_series_iteration_3_2017_2024.csv',benchmarks:'research/political_wealth_2026-09-01/derived/active_politician_verified_benchmarks_iteration_3_2017_2024.csv'},
        {batch:4,audit:'research/political_wealth_2026-09-01/derived/active_politician_identity_audit_iteration_4_2026-09-01.csv',series:'research/political_wealth_2026-09-01/derived/active_politician_verified_series_iteration_4_2017_2024.csv',benchmarks:'research/political_wealth_2026-09-01/derived/active_politician_verified_benchmarks_iteration_4_2017_2024.csv'},
        {batch:5,audit:'research/political_wealth_2026-09-01/derived/active_politician_identity_audit_iteration_5_2026-09-01.csv',series:'research/political_wealth_2026-09-01/derived/active_politician_verified_series_iteration_5_2017_2024.csv',benchmarks:'research/political_wealth_2026-09-01/derived/active_politician_verified_benchmarks_iteration_5_2017_2024.csv'},
        {batch:6,audit:'research/political_wealth_2026-09-01/derived/active_politician_identity_audit_iteration_6_2026-09-01.csv',series:'research/political_wealth_2026-09-01/derived/active_politician_verified_series_iteration_6_2017_2024.csv',benchmarks:'research/political_wealth_2026-09-01/derived/active_politician_verified_benchmarks_iteration_6_2017_2024.csv'},
        {batch:7,audit:'research/political_wealth_2026-09-01/derived/active_politician_identity_audit_iteration_7_2026-09-01.csv',series:'research/political_wealth_2026-09-01/derived/active_politician_verified_series_iteration_7_2017_2024.csv',benchmarks:'research/political_wealth_2026-09-01/derived/active_politician_verified_benchmarks_iteration_7_2017_2024.csv'},
        {batch:8,audit:'research/political_wealth_2026-09-01/derived/active_politician_identity_audit_iteration_8_2026-09-01.csv',series:'research/political_wealth_2026-09-01/derived/active_politician_verified_series_iteration_8_2017_2024.csv',benchmarks:'research/political_wealth_2026-09-01/derived/active_politician_verified_benchmarks_iteration_8_2017_2024.csv'},
        {batch:9,audit:'research/political_wealth_2026-09-01/derived/active_politician_identity_audit_iteration_9_2026-09-01.csv',series:'research/political_wealth_2026-09-01/derived/active_politician_verified_series_iteration_9_2017_2024.csv',benchmarks:'research/political_wealth_2026-09-01/derived/active_politician_verified_benchmarks_iteration_9_2017_2024.csv'},
        {batch:10,audit:'research/political_wealth_2026-09-01/derived/active_politician_identity_audit_iteration_10_2026-09-01.csv',series:'research/political_wealth_2026-09-01/derived/active_politician_verified_series_iteration_10_2017_2024.csv',benchmarks:'research/political_wealth_2026-09-01/derived/active_politician_verified_benchmarks_iteration_10_2017_2024.csv'},
        {batch:11,audit:'research/political_wealth_2026-09-01/derived/active_politician_identity_audit_iteration_11_2026-09-01.csv',series:'research/political_wealth_2026-09-01/derived/active_politician_verified_series_iteration_11_2017_2024.csv',benchmarks:'research/political_wealth_2026-09-01/derived/active_politician_verified_benchmarks_iteration_11_2017_2024.csv'},
        {batch:12,audit:'research/political_wealth_2026-09-01/derived/active_politician_identity_audit_iteration_12_2026-09-01.csv',series:'research/political_wealth_2026-09-01/derived/active_politician_verified_series_iteration_12_2017_2024.csv',benchmarks:'research/political_wealth_2026-09-01/derived/active_politician_verified_benchmarks_iteration_12_2017_2024.csv'},
        {batch:13,audit:'research/political_wealth_2026-09-01/derived/active_politician_identity_audit_iteration_13_2026-09-01.csv',series:'research/political_wealth_2026-09-01/derived/active_politician_verified_series_iteration_13_2017_2024.csv',benchmarks:'research/political_wealth_2026-09-01/derived/active_politician_verified_benchmarks_iteration_13_2017_2024.csv'},
        {batch:14,audit:'research/political_wealth_2026-09-01/derived/active_politician_identity_audit_iteration_14_2026-09-01.csv',series:'research/political_wealth_2026-09-01/derived/active_politician_verified_series_iteration_14_2017_2024.csv',benchmarks:'research/political_wealth_2026-09-01/derived/active_politician_verified_benchmarks_iteration_14_2017_2024.csv'},
        {batch:15,audit:'research/political_wealth_2026-09-01/derived/active_politician_identity_audit_iteration_15_2026-09-01.csv',series:'research/political_wealth_2026-09-01/derived/active_politician_verified_series_iteration_15_2017_2024.csv',benchmarks:'research/political_wealth_2026-09-01/derived/active_politician_verified_benchmarks_iteration_15_2017_2024.csv'},
        {batch:17,audit:'research/political_wealth_2026-09-01/derived/active_politician_identity_audit_iteration_17_2026-09-01.csv',series:'research/political_wealth_2026-09-01/derived/active_politician_verified_series_iteration_17_2017_2024.csv',benchmarks:'research/political_wealth_2026-09-01/derived/active_politician_verified_benchmarks_iteration_17_2017_2024.csv'},
        {batch:18,audit:'research/political_wealth_2026-09-01/derived/active_politician_identity_audit_iteration_18_2026-09-01.csv',series:'research/political_wealth_2026-09-01/derived/active_politician_verified_series_iteration_18_2017_2024.csv',benchmarks:'research/political_wealth_2026-09-01/derived/active_politician_verified_benchmarks_iteration_18_2017_2024.csv'},
        {batch:19,audit:'research/political_wealth_2026-09-01/derived/active_politician_identity_audit_iteration_19_2026-09-01.csv',series:'research/political_wealth_2026-09-01/derived/active_politician_verified_series_iteration_19_2017_2024.csv',benchmarks:'research/political_wealth_2026-09-01/derived/active_politician_verified_benchmarks_iteration_19_2017_2024.csv'}
      ];
      const confirmedBatches = researchSummary?.identidades_confirmadas_por_iteracion || {};
      const batchDownloads = verifiedBatchFiles.filter(item=>Number(confirmedBatches[item.batch] || 0)>0).map(item=>`<a class="download-link" download href="${item.audit}">CSV · auditoría de identidad · tanda ${item.batch}</a><a class="download-link" download href="${item.series}">CSV · series verificadas · tanda ${item.batch}</a><a class="download-link" download href="${item.benchmarks}">CSV · contrafactuales · tanda ${item.batch}</a>`).join('');
      sourceLinks.insertAdjacentHTML('afterbegin',`${batchDownloads}<a class="download-link" download href="research/political_wealth_2026-09-01/derived/active_politician_homonymy_candidate_audit_2026-09-01.csv">CSV · candidatos de homonimia</a><a class="download-link" download href="research/political_wealth_2026-09-01/derived/active_politician_homonymy_resolutions_iteration_13_2026-09-01.csv">CSV · homonimias · tanda 13</a><a class="download-link" download href="research/political_wealth_2026-09-01/derived/active_politician_homonymy_resolutions_iteration_14_2026-09-01.csv">CSV · homonimias · tanda 14</a><a class="download-link" download href="research/political_wealth_2026-09-01/derived/active_politician_homonymy_resolutions_iteration_15_2026-09-01.csv">CSV · homonimia resuelta · tanda 15</a><a class="download-link" download href="research/political_wealth_2026-09-01/derived/active_politician_homonymy_exclusions_iteration_15_2026-09-01.csv">CSV · homónimos descartados · tanda 15</a><a class="download-link" download href="research/political_wealth_2026-09-01/derived/active_politician_homonymy_exclusions_iteration_16_2026-09-01.csv">CSV · cotejos reservados · tanda 16</a><a class="download-link" download href="research/political_wealth_2026-09-01/derived/active_politician_homonymy_exclusions_iteration_17_2026-09-01.csv">CSV · identidades cerradas · tanda 17</a><a class="download-link" download href="research/political_wealth_2026-09-01/derived/active_politician_research_queue_2026-09-01.csv">CSV · cola de los 789</a><a class="download-link" download href="research/political_wealth_2026-09-01/derived/active_politician_oa_identity_review_2026-09-01.csv">CSV · revisión de identidad OA</a><a class="download-link" download href="research/political_wealth_2026-09-01/derived/active_politician_oa_candidate_series_2017_2024.csv">CSV · series OA candidatas</a><a class="download-link" download href="research/political_wealth_2026-09-01/derived/active_politician_research_summary_2026-09-01.json">JSON · avance de investigación</a>`);
      sourceLinks.insertAdjacentHTML('afterbegin','<a class="download-link" download href="research/political_wealth_2026-09-01/derived/active_politician_homonymy_resolutions_iteration_17_2026-09-01.csv">CSV · homonimia resuelta · tanda 17</a>');
      sourceLinks.insertAdjacentHTML('afterbegin','<a class="download-link" download href="research/political_wealth_2026-09-01/derived/active_politician_pen_identity_resolutions_iteration_18_2026-09-01.csv">CSV · autoridades PEN · tanda 18</a>');
      sourceLinks.insertAdjacentHTML('afterbegin','<a class="download-link" download href="research/political_wealth_2026-09-01/derived/active_politician_cross_institution_resolutions_iteration_19_2026-09-01.csv">CSV · puentes institucionales · tanda 19</a>');
    }
    if (sourceLinks && !sourceLinks.querySelector('[href="https://web.legisrn.gov.ar/institucional/legisladores"]')) {
      sourceLinks.insertAdjacentHTML('beforeend','<a class="source-link" target="_blank" rel="noopener" href="https://web.legisrn.gov.ar/institucional/legisladores">Río Negro · Legisladores</a>');
    }
    if (sourceLinks && !sourceLinks.querySelector('[href="https://www.diputadosmisiones.gov.ar/nuevo/diputados"]')) {
      sourceLinks.insertAdjacentHTML('beforeend','<a class="source-link" target="_blank" rel="noopener" href="https://www.diputadosmisiones.gov.ar/nuevo/diputados">Misiones · Representantes</a>');
    }
    if (sourceLinks && !sourceLinks.querySelector('[href="https://www.electoral.gob.ar/nuevo/paginas/pdf/BEP%204-2023.pdf"]')) {
      sourceLinks.insertAdjacentHTML('beforeend','<a class="source-link" target="_blank" rel="noopener" href="https://www.electoral.gob.ar/nuevo/paginas/pdf/BEP%204-2023.pdf">Río Negro · acta de proclamación 2023</a>');
    }
    if (sourceLinks && !sourceLinks.querySelector('[href="https://www3.hcdn.gob.ar/archivos/transparencia/Opciones2025.pdf"]')) {
      sourceLinks.insertAdjacentHTML('beforeend','<a class="source-link" target="_blank" rel="noopener" href="https://www3.hcdn.gob.ar/archivos/transparencia/Opciones2025.pdf">Diputados · nombres completos 2025</a>');
    }
    if (sourceLinks && !sourceLinks.querySelector('[href="https://www.argentina.gob.ar/normativa/nacional/decreto-127-1996-33500/actualizacion"]')) {
      sourceLinks.insertAdjacentHTML('beforeend','<a class="source-link" target="_blank" rel="noopener" href="https://www.argentina.gob.ar/normativa/nacional/decreto-127-1996-33500/actualizacion">Bienes Personales · nuda propiedad y usufructo</a>');
    }
    const consistencySummary = payload.source_consistency_summary || {};
    byId('pwSourceControlled').textContent = `${Number(consistencySummary.declaraciones_controladas || 0).toLocaleString('es-AR')} DDJJ · ${Number(consistencySummary.personas_controladas || 0).toLocaleString('es-AR')} personas`;
    byId('pwSourceReconciled').textContent = `${Number(consistencySummary.declaraciones_que_concilian || 0).toLocaleString('es-AR')} / ${Number(consistencySummary.declaraciones_controladas || 0).toLocaleString('es-AR')}`;
    byId('pwSourceAssetScale').textContent = `${Number(consistencySummary.personas_bienes_con_quiebre_escala || 0).toLocaleString('es-AR')} personas · ${Number(consistencySummary.declaraciones_bienes_con_quiebre_escala || 0).toLocaleString('es-AR')} DDJJ`;
    byId('pwSourceDebtReview').textContent = `${Number(consistencySummary.personas_deudas_con_observacion || 0).toLocaleString('es-AR')} personas · ${Number(consistencySummary.declaraciones_deudas_con_observacion || 0).toLocaleString('es-AR')} DDJJ`;
    byId('pwSourceQualityCallout').innerHTML = `<strong>La primera pregunta ya no es “¿por qué creció tanto?”, sino “¿el total publicado usa la misma escala que su detalle?”.</strong> ${Number(consistencySummary.declaraciones_con_observacion || 0).toLocaleString('es-AR')} de las ${Number(consistencySummary.declaraciones_controladas || 0).toLocaleString('es-AR')} declaraciones controladas tienen alguna observación. Una discrepancia suspende el cálculo afectado; no se corrige silenciosamente ni se atribuye a la persona.`;
    const sourcesNote = document.querySelector('#tab-political-wealth .sources-note');
    if (sourcesNote) sourcesNote.innerHTML = `<b>Corte analítico:</b> 03/09/2026. <b>Padrón:</b> 789 cargos; 298 trayectorias activas publicables y 491 casos freezados sin perder su estado ni sus fuentes. Las copias usadas en los casos profundos de Karina, Javier, Romina Del Plá, Gabriela Estévez, Natalia Gadano, Yolanda Vega, Alejandro Bongiovanni, Facundo Correa Llano y Patricia Vásquez están respaldadas en el repo; las pesadas se excluyen del bundle liviano de Railway. <b>Control sistemático:</b> ${Number(consistencySummary.declaraciones_controladas || 0).toLocaleString('es-AR')} DDJJ de 2022–2024; ${Number(consistencySummary.personas_bienes_con_quiebre_escala || 0).toLocaleString('es-AR')} personas presentan al menos un total de bienes con quiebre decimal. Es una observación sobre la exportación, no sobre la persona. <b>2025:</b> los tres valores publicados —Máximo, Javier y Karina— se conservan provisionales hasta respaldar sus PDF OA; ninguna anomalía aritmética se presenta como conclusión penal.`;
    if (researchSummary) byId('pwResearchQueueStatus').innerHTML = `<strong>Expansión freezada al ${esc(researchSummary.expansion_universo_fecha || '02/09/2026')}: ${Number(researchSummary.cargos_freezados || 0).toLocaleString('es-AR')} cargos pendientes quedan preservados y ${Number(researchSummary.cargos_publicables || researchSummary.trayectorias_auditadas_activas).toLocaleString('es-AR')} tienen trayectoria publicable.</strong> El freeze cambia la prioridad hacia análisis más profundos; no borra fuentes, no cierra preguntas y no convierte una ausencia en incumplimiento o patrimonio cero. Las ${researchSummary.identidades_confirmadas_total.toLocaleString('es-AR')} identidades verificadas y sus ${researchSummary.filas_persona_anio_oa_preseleccionadas.toLocaleString('es-AR')} filas persona-año permanecen reproducibles.`;
    const deepCount = payload.people.length;
    byId('pwPersonViewButton').textContent = `Trayectorias auditadas (${deepCount.toLocaleString('es-AR')})`;
    byId('pwDeepHeroCount').textContent = deepCount.toLocaleString('es-AR');
    byId('pwDeepCoverageBadge').textContent = `${deepCount.toLocaleString('es-AR')} casos auditados`;
    byId('pwDeepScopeCopy').textContent = `Estas ${deepCount.toLocaleString('es-AR')} trayectorias tienen identidad auditada e importes persona-año normalizados. Los ${Number(researchSummary?.cargos_freezados || 0).toLocaleString('es-AR')} cargos restantes preservan su estado en “Todos los cargos”; el freeze no inventa una serie ni convierte N/D en cero.`;
    byId('pwPartyCohortNote').textContent = `${deepCount.toLocaleString('es-AR')} trayectorias con huecos, entradas y afiliaciones temporales distintas todavía no permiten atribuir diferencias a una agrupación.`;
    byId('pwQualityPositions').textContent = `${payload.series.length.toLocaleString('es-AR')} posiciones`;
    byId('pwQualityReconciliations').textContent = `${payload.reconciliation.length.toLocaleString('es-AR')} conciliaciones`;
    byId('pwQualityComposition').textContent = `${payload.composition.length.toLocaleString('es-AR')} agregados`;
    byId('pwQualityBenchmarks').textContent = `${payload.benchmark_comparisons.length.toLocaleString('es-AR')} contrafactuales`;
    byId('pwQualitySourceConsistency').textContent = `${Number(consistencySummary.declaraciones_controladas || 0).toLocaleString('es-AR')} controles · ${Number(consistencySummary.personas_bienes_con_quiebre_escala || 0).toLocaleString('es-AR')} personas con escala de bienes`;
    byId('pwLoading').hidden = true;
    setView('coverage');
    const rosterBySeries = new Map();
    for (const row of rosterPayload?.rows || []) {
      if (row.serie_tab_id) rosterBySeries.set(row.serie_tab_id,row);
      rosterBySeries.set(row.persona_id,row);
    }
    personSearchEntries = payload.people.map(person=>{
      const rosterRow = rosterBySeries.get(person.persona_id) || {};
      const context = [rosterRow.cargo,rosterRow.jurisdiccion,rosterRow.partido_o_alianza].filter(Boolean);
      const quality = analyzeSeriesQuality(personRows(person.persona_id));
      const deep = Boolean(payload?.case_audits?.[person.persona_id]);
      const sourceIssue = sourceConsistencyIssue(person.persona_id);
      const sourceFlag = sourceIssue.assetIssues.length ? 'escala de bienes a conciliar' : sourceIssue.debtIssues.length ? 'deuda a conciliar' : '';
      return {
        person,
        quality,
        deep,
        contextLabel:[rosterRow.jurisdiccion,deep?'caso profundo':sourceFlag||quality.short].filter(Boolean).join(' · '),
        haystack:searchText([person.persona,...context,quality.short,sourceFlag,deep?'caso profundo':''].join(' ')),
        optionLabel:`${person.persona}${rosterRow.jurisdiccion?` · ${rosterRow.jurisdiccion}`:''}${deep?' · caso profundo':sourceFlag?` · ${sourceFlag}`:quality.kind==='review'?' · revisar serie':''}`
      };
    }).sort((a,b)=>a.person.persona.localeCompare(b.person.persona,'es',{sensitivity:'base'}));
    byId('pwPersonControls').innerHTML = personSearchEntries.map(entry=>`<button class="pw-person-button" type="button" data-pw-person="${esc(entry.person.persona_id)}" aria-pressed="false"><span>${esc(entry.person.persona)}${entry.deep?' · caso profundo':''}</span><small>${esc(entry.contextLabel)}</small></button>`).join('');
    syncPersonSelection(selectedPerson);
    renderPersonDirectory();
    document.querySelectorAll('[data-pw-person]').forEach(button=>button.addEventListener('click',()=>choosePerson(button.dataset.pwPerson)));
    byId('pwPersonSearch')?.addEventListener('input',renderPersonDirectory);
    byId('pwPersonSearch')?.addEventListener('keydown',event=>{
      if (event.key !== 'Enter') return;
      const first = renderPersonDirectory()[0];
      if (!first) return;
      event.preventDefault();
      choosePerson(first.person.persona_id);
    });
    byId('pwPersonSelect')?.addEventListener('change',event=>choosePerson(event.target.value));
    byId('pwRosterSearch')?.addEventListener('input',renderActiveRoster);
    byId('pwRosterLevel')?.addEventListener('change',renderActiveRoster);
    byId('pwRosterStatus')?.addEventListener('change',renderActiveRoster);
    byId('pwActiveRosterBody')?.addEventListener('click',event=>{
      const button = event.target.closest('[data-pw-open-series]');
      if (button) openSeries(button.dataset.pwOpenSeries);
    });
    renderCoverage();
    renderPerson();
  }

  document.querySelectorAll('[data-pw-view]').forEach(button=>button.addEventListener('click',()=>setView(button.dataset.pwView)));
  tabs.querySelector('[data-tab="tab-political-wealth"]')?.addEventListener('click',()=>window.setTimeout(renderPerson,180));
  window.renderPoliticalWealth = ()=>{
    if(payload&&!document.querySelector('[data-pw-surface="person"]')?.hidden) renderPerson();
  };

  const bootstrap = window.__POLITICAL_WEALTH_BOOTSTRAP__;
  const hasBootstrap = Boolean(bootstrap?.data&&bootstrap?.roster);
  const wealthPanel = document.getElementById('tab-political-wealth');
  if(wealthPanel) wealthPanel.dataset.pwDataSource = hasBootstrap?'bootstrap':'fetch';
  const loadPromise = hasBootstrap
    ? Promise.resolve([bootstrap.data,bootstrap.roster,bootstrap.research||null,bootstrap.queue||[]])
    : Promise.all([
        fetchJson(DATA_URL,'serie patrimonial'),
        fetchJson(ROSTER_URL,'padrón activo'),
        fetchJson(RESEARCH_URL,'avance de investigación'),
        Promise.resolve([]),
        Promise.all([fetchJson(KARINA_AUDIT_URL,'auditoría Karina'),fetchJson(JAVIER_AUDIT_URL,'auditoría Javier'),fetchJson(ROMINA_AUDIT_URL,'auditoría Romina Del Plá'),fetchJson(GABRIELA_AUDIT_URL,'auditoría Gabriela Estévez'),fetchJson(NATALIA_AUDIT_URL,'auditoría Natalia Gadano'),fetchJson(YOLANDA_AUDIT_URL,'auditoría Yolanda Vega'),fetchJson(ALEJANDRO_AUDIT_URL,'auditoría Alejandro Bongiovanni'),fetchJson(FACUNDO_AUDIT_URL,'auditoría Facundo Correa Llano'),fetchJson(PATRICIA_AUDIT_URL,'auditoría Patricia Vásquez')]),
        fetchJson(SOURCE_CONSISTENCY_URL,'consistencia resumen-detalle')
      ]);
  loadPromise.then(([data,roster,research,queue,caseAudits,sourceConsistency])=>initialize(data,roster,research,queue,caseAudits,sourceConsistency)).catch(error=>{byId('pwLoading').innerHTML=`No se pudo cargar el universo patrimonial (${error.message}). Los CSV siguen disponibles en la sección de fuentes.`;});
})();

