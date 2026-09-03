(() => {
  'use strict';
  if (document.getElementById('mora-ley-tab-v1')) return;



  const tabs = document.getElementById('dash-main-tabs');
  const anchorBtn = tabs?.querySelector('[data-tab="tab-youth-credit"]');
  if (!tabs || !anchorBtn) return;
  anchorBtn

  const anchorPanel = document.getElementById('tab-youth-credit');
  if (!anchorPanel) return;
  anchorPanel

  const plotConfig = { responsive:true, displaylogo:false, displayModeBar:false };
  function plotBase(mobile) {
    return {paper_bgcolor:'rgba(0,0,0,0)',plot_bgcolor:'#fff',font:{family:'Inter,system-ui,sans-serif',size:mobile?9:10,color:'#65516d'},margin:{l:mobile?48:60,r:18,t:24,b:mobile?92:68},hoverlabel:{bgcolor:'#fff',bordercolor:'#d9cde0',font:{color:'#5d4867'}}};
  }

  const BANK = [{"d":"2021-01","h":1.809,"pc":1.761,"cum":-1.035},{"d":"2021-02","h":1.702,"pc":1.705,"cum":-2.708},{"d":"2021-03","h":1.992,"pc":2.161,"cum":-4.092},{"d":"2021-04","h":2.567,"pc":2.929,"cum":-4.901},{"d":"2021-05","h":2.943,"pc":3.458,"cum":-5.333},{"d":"2021-06","h":4.12,"pc":4.901,"cum":-4.589},{"d":"2021-07","h":5.058,"pc":5.787,"cum":-2.907},{"d":"2021-08","h":5.055,"pc":5.702,"cum":-1.228},{"d":"2021-09","h":4.761,"pc":5.221,"cum":0.157},{"d":"2021-10","h":4.657,"pc":5.036,"cum":1.439},{"d":"2021-11","h":4.299,"pc":4.525,"cum":2.363},{"d":"2021-12","h":4.177,"pc":4.296,"cum":3.164},{"d":"2022-01","h":4.069,"pc":4.135,"cum":3.858},{"d":"2022-02","h":3.917,"pc":3.973,"cum":4.399},{"d":"2022-03","h":3.729,"pc":3.635,"cum":4.753},{"d":"2022-04","h":3.52,"pc":3.453,"cum":4.897},{"d":"2022-05","h":3.333,"pc":3.201,"cum":4.855},{"d":"2022-06","h":3.229,"pc":3.063,"cum":4.708},{"d":"2022-07","h":3.221,"pc":3.075,"cum":4.554},{"d":"2022-08","h":3.12,"pc":2.958,"cum":4.298},{"d":"2022-09","h":3.016,"pc":2.821,"cum":3.939},{"d":"2022-10","h":3.016,"pc":2.843,"cum":3.579},{"d":"2022-11","h":2.862,"pc":2.688,"cum":3.066},{"d":"2022-12","h":3.036,"pc":2.828,"cum":2.726},{"d":"2023-01","h":3.125,"pc":2.911,"cum":2.476},{"d":"2023-02","h":3.145,"pc":2.953,"cum":2.245},{"d":"2023-03","h":3.275,"pc":3.126,"cum":2.145},{"d":"2023-04","h":3.262,"pc":3.099,"cum":2.031},{"d":"2023-05","h":3.199,"pc":3.025,"cum":1.855},{"d":"2023-06","h":3.313,"pc":3.115,"cum":1.792},{"d":"2023-07","h":3.32,"pc":3.086,"cum":1.736},{"d":"2023-08","h":3.141,"pc":2.856,"cum":1.501},{"d":"2023-09","h":3.084,"pc":2.833,"cum":1.209},{"d":"2023-10","h":2.847,"pc":2.588,"cum":0.681},{"d":"2023-11","h":2.695,"pc":2.393,"cum":0},{"d":"2023-12","h":2.785,"pc":2.502,"cum":-0.591},{"d":"2024-01","h":2.7,"pc":2.496,"cum":-1.267},{"d":"2024-02","h":2.605,"pc":2.424,"cum":-2.037},{"d":"2024-03","h":2.652,"pc":2.585,"cum":-2.761},{"d":"2024-04","h":2.589,"pc":2.578,"cum":-3.547},{"d":"2024-05","h":2.759,"pc":2.775,"cum":-4.164},{"d":"2024-06","h":2.786,"pc":2.753,"cum":-4.753},{"d":"2024-07","h":2.672,"pc":2.604,"cum":-5.457},{"d":"2024-08","h":2.662,"pc":2.589,"cum":-6.17},{"d":"2024-09","h":2.635,"pc":2.558,"cum":-6.91},{"d":"2024-10","h":2.489,"pc":2.4,"cum":-7.796},{"d":"2024-11","h":2.525,"pc":2.484,"cum":-8.647},{"d":"2024-12","h":2.553,"pc":2.505,"cum":-9.47},{"d":"2025-01","h":2.664,"pc":2.644,"cum":-10.181},{"d":"2025-02","h":2.939,"pc":2.989,"cum":-10.617},{"d":"2025-03","h":3.256,"pc":3.375,"cum":-10.737},{"d":"2025-04","h":3.665,"pc":3.884,"cum":-10.447},{"d":"2025-05","h":4.459,"pc":4.843,"cum":-9.364},{"d":"2025-06","h":5.128,"pc":5.635,"cum":-7.612},{"d":"2025-07","h":5.649,"pc":6.231,"cum":-5.339},{"d":"2025-08","h":6.601,"pc":7.412,"cum":-2.114},{"d":"2025-09","h":7.277,"pc":8.215,"cum":1.788},{"d":"2025-10","h":7.757,"pc":8.76,"cum":6.169},{"d":"2025-11","h":8.822,"pc":10.057,"cum":11.616},{"d":"2025-12","h":9.333,"pc":10.569,"cum":17.573},{"d":"2026-01","h":10.606,"pc":12.073,"cum":24.804},{"d":"2026-02","h":11.221,"pc":12.688,"cum":32.649},{"d":"2026-03","h":11.636,"pc":13.087,"cum":40.909},{"d":"2026-04","h":12.09,"pc":13.651,"cum":49.623},{"d":"2026-05","h":12.795,"pc":14.52,"cum":59.043}];
  const PRE_SHOCK_MEAN = 3.376;
  const PNFC = [{"d":"2022-01","total":13,"personal":22.4,"cards":6.5,"fintech":22.7},{"d":"2022-02","total":12.8,"personal":21.5,"cards":6.5,"fintech":21.4},{"d":"2022-03","total":12.8,"personal":21.1,"cards":6.4,"fintech":20.7},{"d":"2022-04","total":12.9,"personal":21.2,"cards":6.4,"fintech":20.2},{"d":"2022-05","total":13,"personal":21.3,"cards":6.3,"fintech":20.3},{"d":"2022-06","total":12.5,"personal":21.1,"cards":5.8,"fintech":20},{"d":"2022-07","total":13,"personal":21.8,"cards":6.3,"fintech":20.6},{"d":"2022-08","total":12.6,"personal":21.5,"cards":6,"fintech":20},{"d":"2022-09","total":12.2,"personal":21.2,"cards":5.3,"fintech":19.8},{"d":"2022-10","total":12,"personal":21.1,"cards":5.2,"fintech":19.6},{"d":"2022-11","total":11.7,"personal":20.6,"cards":5,"fintech":19.1},{"d":"2022-12","total":11.9,"personal":21.1,"cards":5.2,"fintech":20.7},{"d":"2023-01","total":12.2,"personal":20.9,"cards":5.4,"fintech":20.8},{"d":"2023-02","total":12.3,"personal":20.8,"cards":5.6,"fintech":20.9},{"d":"2023-03","total":12.1,"personal":20.6,"cards":5.4,"fintech":20.4},{"d":"2023-04","total":12.2,"personal":20.9,"cards":5.6,"fintech":21.3},{"d":"2023-05","total":12.3,"personal":21.5,"cards":5.5,"fintech":22.5},{"d":"2023-06","total":12.4,"personal":21.7,"cards":5.6,"fintech":22.6},{"d":"2023-07","total":12.3,"personal":21.9,"cards":5.4,"fintech":23.1},{"d":"2023-08","total":11.8,"personal":21.3,"cards":5.1,"fintech":22.6},{"d":"2023-09","total":11.9,"personal":21.8,"cards":5,"fintech":23},{"d":"2023-10","total":11.3,"personal":21.7,"cards":4.6,"fintech":22.1},{"d":"2023-11","total":10.8,"personal":21.8,"cards":4.2,"fintech":22},{"d":"2023-12","total":9.8,"personal":21.4,"cards":3.6,"fintech":21.8},{"d":"2024-01","total":9.4,"personal":20.3,"cards":3.6,"fintech":20.1},{"d":"2024-02","total":8.5,"personal":18.4,"cards":3.3,"fintech":16.6},{"d":"2024-03","total":8.4,"personal":17.9,"cards":3.4,"fintech":16},{"d":"2024-04","total":8.4,"personal":17,"cards":3.7,"fintech":14.9},{"d":"2024-05","total":8.3,"personal":16.8,"cards":3.8,"fintech":14.7},{"d":"2024-06","total":8.4,"personal":16.5,"cards":4.1,"fintech":14.3},{"d":"2024-07","total":8.1,"personal":14.2,"cards":4.1,"fintech":12},{"d":"2024-08","total":7.9,"personal":13.6,"cards":4.1,"fintech":11.9},{"d":"2024-09","total":7.7,"personal":12.9,"cards":4.1,"fintech":11.3},{"d":"2024-10","total":7.5,"personal":11.6,"cards":4.2,"fintech":10},{"d":"2024-11","total":7.3,"personal":10.6,"cards":4.2,"fintech":8.9},{"d":"2024-12","total":7.7,"personal":11.2,"cards":4.6,"fintech":9.9},{"d":"2025-01","total":8.6,"personal":12.1,"cards":5.6,"fintech":10.4},{"d":"2025-02","total":9.5,"personal":12.4,"cards":6.4,"fintech":10.4},{"d":"2025-03","total":10.4,"personal":13.3,"cards":7,"fintech":11.2},{"d":"2025-04","total":11.4,"personal":14.5,"cards":7.9,"fintech":12.3},{"d":"2025-05","total":12.9,"personal":16.9,"cards":8.5,"fintech":15},{"d":"2025-06","total":14.3,"personal":18.2,"cards":9.6,"fintech":16.5},{"d":"2025-07","total":16.4,"personal":20.3,"cards":10.8,"fintech":18.4},{"d":"2025-08","total":17.2,"personal":21.4,"cards":12,"fintech":19.6},{"d":"2025-09","total":18.8,"personal":23,"cards":13.7,"fintech":21.1},{"d":"2025-10","total":20.3,"personal":25.1,"cards":15,"fintech":22.1},{"d":"2025-11","total":21.7,"personal":26.6,"cards":16,"fintech":22.9},{"d":"2025-12","total":23.1,"personal":29,"cards":16.7,"fintech":24.7},{"d":"2026-01","total":24.7,"personal":30.9,"cards":18.2,"fintech":25.9},{"d":"2026-02","total":26.9,"personal":34.1,"cards":19.4,"fintech":26.2}];
  const COST = [{"year":"2023","infl":127.95,"teaReal":18.33,"cfteaReal":44.33},{"year":"2024","infl":236.8,"teaReal":-29.22,"cfteaReal":-15.6},{"year":"2025","infl":44.47,"teaReal":43.27,"cfteaReal":65.69},{"year":"2026","infl":33,"teaReal":45.56,"cfteaReal":66.47}];

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
    const blob = new Blob([head + '\n' + rows.join('\n')], {type:'text/csv'});
    const a = document.createElement('a'); a.href = URL.createObjectURL(blob); a.download = 'mora_ley_bancaria_hogares.csv'; a.click();
  };

  // Interactividad vía handlers inline (oninput/onclick/onchange) en el markup:
  // LegacyMarkup los convierte a handlers React, robustos frente al ciclo de montaje.

  tabs.querySelector('[data-tab="tab-mora-ley"]')?.addEventListener('click', () => window.setTimeout(window.renderMoraLey, 160));
  window.addEventListener('resize', () => ['moraLeyBancariaChart','moraLeyPnfcChart','moraLeyCostoChart'].forEach(id => { const el = document.getElementById(id); if (el?.data) Plotly.Plots.resize(el); }));
})();

