(() => {
  'use strict';
  if (document.getElementById('reclamo-credito-tab-v1')) return;



  const tabs = document.getElementById('dash-main-tabs');
  const anchorBtn = tabs?.querySelector('[data-tab="tab-mora-ley"]') || tabs?.querySelector('[data-tab="tab-youth-credit"]');
  if (!tabs || !anchorBtn) return;
  anchorBtn

  const anchorPanel = document.getElementById('tab-mora-ley') || document.getElementById('tab-youth-credit');
  if (!anchorPanel) return;
  anchorPanel

  const plotConfig = { responsive:true, displaylogo:false, displayModeBar:false };
  function plotBase(mobile) {
    return {paper_bgcolor:'rgba(0,0,0,0)',plot_bgcolor:'#fff',font:{family:'Inter,system-ui,sans-serif',size:mobile?9:10,color:'#65516d'},margin:{l:mobile?48:60,r:18,t:24,b:mobile?70:56},hoverlabel:{bgcolor:'#fff',bordercolor:'#d9cde0',font:{color:'#5d4867'}}};
  }

  const CFT = {"eeff":321,"pnfc":588,"gap":267,"ratio":1.83};
  const ROA = [{"g":"Sistema financiero","v12":1.07,"v12prev":1.74},{"g":"Bancos privados nacionales","v12":0.22,"v12prev":1.89},{"g":"Bancos privados extranjeros","v12":1.54,"v12prev":1.59},{"g":"Bancos públicos","v12":1.36,"v12prev":1.65},{"g":"EFNB","v12":3.94,"v12prev":3.48}];
  const PESO = [{"d":"2023-09","v":3.01},{"d":"2023-12","v":2.61},{"d":"2024-06","v":2.53},{"d":"2024-12","v":4.31},{"d":"2025-06","v":13.64},{"d":"2025-12","v":13.65},{"d":"2026-05","v":13.57}];

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

