(() => {
  'use strict';

  if (document.getElementById('epica-super-tabs-v1')) return;



  const tabs = document.getElementById('dash-main-tabs');
  const storyButton = tabs?.querySelector('[data-tab="tab-story"]');
  if (!tabs || !storyButton) return;

  storyButton

  const storyPanel = document.getElementById('tab-story');
  storyPanel

  const householdData = {
    '2025-S1': { any:70.690, none:29.310, current:25.811, mixed:36.246, installments:50.874, profiles:[29.310,8.768,3.500,21.169,1.007,36.246] },
    '2025-S2': { any:70.533, none:29.467, current:25.386, mixed:36.750, installments:51.563, profiles:[29.467,7.546,3.964,21.155,1.119,36.750] },
    '2026-Q1': { any:71.778, none:28.222, current:24.534, mixed:36.599, installments:50.660, profiles:[28.222,9.190,3.542,21.510,0.937,36.599] }
  };
  const householdProfileLabels = ['Ninguna V13–V17','Sólo ahorro','Sólo préstamos','Sólo cuotas/fiado','Sólo venta','Combinación 2+'];
  let householdPeriod = '2026-Q1';
  let dollarView = 'liquidity';
  let caputoChannel = 'bank';
  const pct = value => `${value.toLocaleString('es-AR',{minimumFractionDigits:1,maximumFractionDigits:1})}%`;
  const usd = value => `USD ${Math.round(value).toLocaleString('es-AR')}`;
  const plotConfig = { responsive:true, displaylogo:false, displayModeBar:false };

  function plotBase(mobile) {
    return {paper_bgcolor:'rgba(0,0,0,0)',plot_bgcolor:'#fff',font:{family:'Inter,system-ui,sans-serif',size:mobile?9:10,color:'#65516d'},margin:{l:mobile?48:60,r:18,t:24,b:mobile?92:68},hoverlabel:{bgcolor:'#fff',bordercolor:'#d9cde0',font:{color:'#5d4867'}}};
  }

  function renderHouseholdProfiles() {
    const target = document.getElementById('epicaHouseholdProfileChart');
    if (!target || !window.Plotly) return;
    const row = householdData[householdPeriod];
    const mobile = window.innerWidth <= 720;
    ['Any','None','Current','Mixed','Installments'].forEach(key => {
      const map = {Any:'any',None:'none',Current:'current',Mixed:'mixed',Installments:'installments'};
      const element = document.getElementById(`epicaHousehold${key}`);
      if (element) element.textContent = pct(row[map[key]]);
    });
    const layout = {...plotBase(mobile),showlegend:false,bargap:.27,yaxis:{title:'% de hogares',range:[0,44],gridcolor:'#eee7f0',ticksuffix:'%',fixedrange:true},xaxis:{tickangle:mobile?-35:-15,fixedrange:true,automargin:true}};
    Plotly.react(target,[{type:'bar',x:householdProfileLabels,y:row.profiles,text:row.profiles.map(pct),textposition:'outside',cliponaxis:false,marker:{color:['#b7a8bd','#e5a8bd','#d3b0df','#d9bd71','#d88e84','#9c5e83'],line:{color:'#fff',width:1}},hovertemplate:'<b>%{x}</b><br>%{y:.3f}% de hogares<extra></extra>'}],layout,plotConfig);
  }

  function renderHouseholdStrata() {
    const target = document.getElementById('epicaHouseholdStrataChart');
    if (!target || !window.Plotly) return;
    const mobile = window.innerWidth <= 720;
    const x = ['Ahorros','Cuotas/fiado','Préstamos','Venta','Alguna V13–17','Proxy corriente'];
    const z = [[39.847,39.752,32.941,14.979,69.745,23.926],[39.093,54.037,24.316,9.011,71.507,25.849],[36.858,66.040,16.747,5.199,76.442,23.141]];
    const layout = {...plotBase(mobile),margin:{l:mobile?58:70,r:15,t:18,b:mobile?100:72},xaxis:{tickangle:mobile?-38:-20,fixedrange:true},yaxis:{fixedrange:true,autorange:'reversed'},coloraxis:{cmin:0,cmax:80,colorscale:[[0,'#fff8fb'],[.35,'#efd3df'],[.7,'#c382a2'],[1,'#744b78']],colorbar:{title:'%',thickness:10,len:.8}}};
    Plotly.react(target,[{type:'heatmap',x,y:['Bajo','Medio','Alto'],z,coloraxis:'coloraxis',text:z.map(row=>row.map(pct)),texttemplate:'%{text}',hovertemplate:'<b>%{y}</b><br>%{x}: %{z:.3f}%<extra></extra>'}],layout,plotConfig);
  }

  function setDollarMeta(title, subtitle, badge, kind) {
    const titleEl = document.getElementById('epicaDollarChartTitle');
    const subtitleEl = document.getElementById('epicaDollarChartSubtitle');
    const badgeEl = document.getElementById('epicaDollarChartBadge');
    if (titleEl) titleEl.textContent = title;
    if (subtitleEl) subtitleEl.textContent = subtitle;
    if (badgeEl) { badgeEl.textContent = badge; badgeEl.className = `epica-chip ${kind}`; }
  }

  function renderDollarChart() {
    const target = document.getElementById('epicaDollarMainChart');
    if (!target || !window.Plotly) return;
    const mobile = window.innerWidth <= 720;
    let traces;
    let layout;
    if (dollarView === 'composition') {
      setDollarMeta('Composición de los activos de reserva','Planilla SDDS · 31/07/2026 · USD millones.','medida oficial','observed');
      traces = [{type:'pie',labels:['Moneda extranjera','Oro','DEG','Otros activos'],values:[38433.62,8046.37,908.14,211.06],hole:.58,sort:false,textinfo:'label+percent',textposition:mobile?'inside':'outside',marker:{colors:['#4b9a8f','#d9b65c','#8e77b8','#cf91a8'],line:{color:'#fff',width:2}},hovertemplate:'<b>%{label}</b><br>USD %{value:,.2f} M<br>%{percent}<extra></extra>'}];
      layout = {...plotBase(mobile),margin:{l:20,r:20,t:18,b:20},showlegend:mobile,legend:{orientation:'h',y:-.08},annotations:[{text:'USD 47.599 M<br><span style="font-size:9px">total oficial</span>',x:.5,y:.5,showarrow:false,font:{size:16,color:'#315d5b'}}]};
    } else if (dollarView === 'debt') {
      setDollarMeta('Muro de servicios 2027–2031','Administración Central · perfil estático al 31/03/2026.','perímetro acotado','proxy');
      const years=[2027,2028,2029,2030,2031],capital=[72570.254,40028.613,26234.018,22527.077,38448.478],interest=[10141.386,9761.577,8982.286,7901.508,6592.491];
      traces=[{type:'bar',name:'Capital',x:years,y:capital,marker:{color:'#4f8f88'},hovertemplate:'<b>%{x}</b><br>Capital USD %{y:,.0f} M<extra></extra>'},{type:'bar',name:'Intereses',x:years,y:interest,marker:{color:'#d5ad59'},hovertemplate:'<b>%{x}</b><br>Intereses USD %{y:,.0f} M<extra></extra>'}];
      layout={...plotBase(mobile),barmode:'stack',legend:{orientation:'h',y:1.12},yaxis:{title:'USD millones',gridcolor:'#e8efed',fixedrange:true},xaxis:{dtick:1,fixedrange:true},hovermode:'x unified'};
    } else {
      setDollarMeta('Stock bruto y residual por horizonte','Estrés estático: no supone nuevas entradas, rollover ni valuación.','escenario mecánico','proxy');
      const labels=['Activos oficiales','Después de ≤1 mes','Después de ≤3 meses','Después de ≤1 año'],values=[47599.19,10471.37,10227.88,5819.75];
      traces=[{type:'bar',x:labels,y:values,text:values.map(v=>`USD ${Math.round(v).toLocaleString('es-AR')} M`),textposition:'outside',cliponaxis:false,marker:{color:['#4b9a8f','#d8bd70','#cfa967','#c78478'],line:{color:'#fff',width:1}},hovertemplate:'<b>%{x}</b><br>USD %{y:,.2f} M<extra></extra>'}];
      layout={...plotBase(mobile),showlegend:false,yaxis:{title:'USD millones',range:[0,53000],gridcolor:'#e8efed',fixedrange:true},xaxis:{tickangle:mobile?-30:-12,fixedrange:true,automargin:true},annotations:[{xref:'paper',yref:'paper',x:.99,y:.98,xanchor:'right',text:'Flujos acumulados a 1 año: −USD 41.779 M',showarrow:false,font:{size:9,color:'#8b6a40'},bgcolor:'#fff8e7',bordercolor:'#e3c97e',borderpad:5}]};
    }
    Plotly.react(target,traces,layout,plotConfig);
  }

  function renderCaputoIncome() {
    const target = document.getElementById('epicaCaputoIncomeChart');
    if (!target || !window.Plotly) return;
    const mobile = window.innerWidth <= 720;
    const shares = [1.8,3.2,4.2,5.3,6.3,7.6,9.3,12.1,16.6,33.5];
    const labels = shares.map((_,index) => `D${index + 1}`);
    const layout = {...plotBase(mobile),showlegend:false,bargap:.22,yaxis:{title:'% del ingreso corriente',range:[0,39],gridcolor:'#eeeaf4',ticksuffix:'%',fixedrange:true},xaxis:{title:'Decil de ingreso individual',fixedrange:true},annotations:[{x:'D10',y:36.5,text:'El decil 10 concentra 33,5%',showarrow:false,font:{size:9,color:'#67559a'},bgcolor:'#f6f3ff',bordercolor:'#d7ceed',borderpad:4}]};
    Plotly.react(target,[{type:'bar',x:labels,y:shares,text:shares.map(pct),textposition:'outside',cliponaxis:false,marker:{color:shares.map((_,index)=>index>=8?'#67559a':'#c8bee1'),line:{color:'#fff',width:1}},hovertemplate:'<b>Decil %{x}</b><br>%{y:.1f}% del ingreso<extra></extra>'}],layout,plotConfig);
  }

  function renderCaputoReturns() {
    const target = document.getElementById('epicaCaputoReturnChart');
    const input = document.getElementById('epicaCaputoAmount');
    const costInput = document.getElementById('epicaCaputoBrokerCost');
    if (!target || !input || !costInput || !window.Plotly) return;
    const mobile = window.innerWidth <= 720;
    const amount = Number(input.value);
    const incrementalCost = Number(costInput.value);
    const rates = [0,0.22,2.05,Math.max(0,4.14-incrementalCost)];
    const gains = rates.map(rate => amount * rate / 100);
    const output = document.getElementById('epicaCaputoAmountOutput');
    if (output) output.textContent = usd(amount);
    const costOutput = document.getElementById('epicaCaputoBrokerCostOutput');
    if (costOutput) costOutput.textContent = `${incrementalCost.toLocaleString('es-AR',{minimumFractionDigits:1,maximumFractionDigits:1})}%`;
    const breakEvenRead = document.getElementById('epicaCaputoBreakEvenRead');
    const rateGap = 2.09 - incrementalCost;
    if (breakEvenRead) breakEvenRead.textContent = Math.abs(rateGap) < 0.005 ? 'El escenario coincide con el punto de equilibrio.' : rateGap > 0 ? `Con el escenario elegido queda una brecha de +${rateGap.toLocaleString('es-AR',{minimumFractionDigits:2,maximumFractionDigits:2})} p.p.` : `Con el escenario elegido el PF queda ${Math.abs(rateGap).toLocaleString('es-AR',{minimumFractionDigits:2,maximumFractionDigits:2})} p.p. arriba.`;
    [['Cash',0],['Savings',1],['Fixed',2],['Treasury',3]].forEach(([key,index]) => {
      const element = document.getElementById(`epicaCaputoGain${key}`);
      if (element) element.textContent = `${Number(index) === 0 ? '' : '+'}${usd(gains[Number(index)])}`;
    });
    const labels = ['Efectivo','Caja ahorro USD','PF USD 60+','T-Bill neta de costo escenario'];
    const layout = {...plotBase(mobile),showlegend:false,margin:{l:mobile?52:64,r:18,t:28,b:mobile?105:78},yaxis:{title:'Ganancia bruta estimada · USD',range:[0,Math.max(50,Math.max(...gains)*1.22)],gridcolor:'#eeeaf4',fixedrange:true},xaxis:{tickangle:mobile?-32:-16,fixedrange:true,automargin:true}};
    Plotly.react(target,[{type:'bar',x:labels,y:gains,text:gains.map(value=>value===0?'USD 0':`+${usd(value)}`),textposition:'outside',cliponaxis:false,marker:{color:['#c7bfce','#b9aecf','#9383bb','#67559a'],line:{color:'#fff',width:1}},customdata:rates,hovertemplate:'<b>%{x}</b><br>Tasa de referencia: %{customdata:.2f}%<br>Ganancia bruta: USD %{y:,.2f}<extra></extra>'}],layout,plotConfig);
  }

  function renderCaputoPath() {
    const target = document.getElementById('epicaCaputoPath');
    const note = document.getElementById('epicaCaputoPathNote');
    if (!target || !note) return;
    const paths = {
      bank: {
        steps:[['Dueño','Ahorro USD'],['Intermediario','Banco local'],['Decisión ajena','Crédito empresa'],['Mecánica','Liquida USD'],['Resultado buscado','Actividad y empleo']],
        note:'El beneficio macro es posible, no automático: hacen falta banco dispuesto, empresa elegible, demanda solvente y un uso que efectivamente aumente producción o empleo.'
      },
      broker: {
        steps:[['Dueño','Ahorro USD'],['Intermediario','Cuenta comitente'],['Decisión propia','Compra T-Bill'],['Beneficio privado','Renta y liquidez'],['Efecto local directo','Sin fondeo bancario']],
        note:'El ahorrista elige el activo y captura su renta, descontados costos e impuestos. Ese dinero no amplía directamente la capacidad de crédito de un banco argentino.'
      },
      spend: {
        steps:[['Dueño','Ahorro USD'],['Uso','Vende o paga'],['Destino','Consumo / proyecto'],['Transmisión','Demanda y empleo'],['Resultado posible','Actividad e impuestos']],
        note:'También puede movilizar actividad sin depósito previo. El resultado depende de cuánto sea producción local, importación, ahorro de terceros o inversión efectiva.'
      }
    };
    const selected = paths[caputoChannel];
    target.innerHTML = selected.steps.map(([label,value],index)=>`<div class="${index===selected.steps.length-1?'result':''}"><small>${label}</small><b>${value}</b></div>`).join('');
    note.textContent = selected.note;
  }

  window.renderEpicaHouseholds = () => { renderHouseholdProfiles(); renderHouseholdStrata(); };
  window.renderEpicaDollars = renderDollarChart;
  window.renderEpicaCaputo = () => { renderCaputoIncome(); renderCaputoReturns(); renderCaputoPath(); };

  document.querySelectorAll('[data-epica-household-period]').forEach(button => button.addEventListener('click', () => {
    householdPeriod = button.dataset.epicaHouseholdPeriod;
    document.querySelectorAll('[data-epica-household-period]').forEach(item => { const active=item===button; item.classList.toggle('active',active); item.setAttribute('aria-pressed',String(active)); });
    renderHouseholdProfiles();
  }));
  document.querySelectorAll('[data-epica-dollar-view]').forEach(button => button.addEventListener('click', () => {
    dollarView = button.dataset.epicaDollarView;
    document.querySelectorAll('[data-epica-dollar-view]').forEach(item => { const active=item===button; item.classList.toggle('active',active); item.setAttribute('aria-pressed',String(active)); });
    renderDollarChart();
  }));
  document.getElementById('epicaCaputoAmount')?.addEventListener('input', renderCaputoReturns);
  document.getElementById('epicaCaputoBrokerCost')?.addEventListener('input', renderCaputoReturns);
  document.querySelectorAll('[data-epica-caputo-channel]').forEach(button => button.addEventListener('click', () => {
    caputoChannel = button.dataset.epicaCaputoChannel;
    document.querySelectorAll('[data-epica-caputo-channel]').forEach(item => { const active=item===button; item.classList.toggle('active',active); item.setAttribute('aria-pressed',String(active)); });
    renderCaputoPath();
  }));

  tabs.querySelector('[data-tab="tab-epica-households"]')?.addEventListener('click', () => window.setTimeout(window.renderEpicaHouseholds, 190));
  tabs.querySelector('[data-tab="tab-epica-dollars"]')?.addEventListener('click', () => window.setTimeout(window.renderEpicaDollars, 190));
  tabs.querySelector('[data-tab="tab-epica-caputo-colchon"]')?.addEventListener('click', () => window.setTimeout(window.renderEpicaCaputo, 190));
  const epicaResponsiveRenderers = {
    'tab-epica-households':'renderEpicaHouseholds',
    'tab-epica-dollars':'renderEpicaDollars',
    'tab-epica-development':'renderEpicaDevelopment',
    'tab-epica-narratives':'renderEpicaNarratives',
    'tab-epica-caputo-colchon':'renderEpicaCaputo',
    'tab-political-wealth':'renderPoliticalWealth'
  };
  let epicaViewportMode = window.innerWidth <= 720 ? 'mobile' : 'desktop';
  let epicaResponsiveTimer = null;

  function resizeVisibleEpicaCharts() {
    if (!window.Plotly?.Plots?.resize) return;
    document.querySelectorAll('.tab-panel.active .epica-shell .js-plotly-plot').forEach(chart => {
      if (chart.data) Plotly.Plots.resize(chart);
    });
  }

  function refreshEpicaResponsive(forceRerender = false) {
    const nextMode = window.innerWidth <= 720 ? 'mobile' : 'desktop';
    const activeTab = document.querySelector('.tab-panel.active[id]');
    const renderer = window[epicaResponsiveRenderers[activeTab?.id]];
    if ((forceRerender || nextMode !== epicaViewportMode) && typeof renderer === 'function') renderer();
    epicaViewportMode = nextMode;
    window.requestAnimationFrame(resizeVisibleEpicaCharts);
  }

  function scheduleEpicaResponsiveRefresh(forceRerender = false) {
    window.clearTimeout(epicaResponsiveTimer);
    epicaResponsiveTimer = window.setTimeout(() => refreshEpicaResponsive(forceRerender), 120);
  }

  function keepEpicaControlInView(control) {
    if (window.innerWidth > 720) return;
    const rail = control.closest('.epica-toolbar,.pw-controls');
    if (!rail || rail.scrollWidth <= rail.clientWidth + 2) return;
    window.requestAnimationFrame(() => control.scrollIntoView({behavior:'smooth',block:'nearest',inline:'center'}));
  }

  window.refreshEpicaResponsive = refreshEpicaResponsive;
  window.scheduleEpicaResponsiveRefresh = scheduleEpicaResponsiveRefresh;
  document.addEventListener('click', event => {
    const control = event.target.closest?.('.epica-toolbar .epica-toggle,.pw-controls .pw-person-button');
    if (control) keepEpicaControlInView(control);
  });
  window.addEventListener('resize', () => scheduleEpicaResponsiveRefresh(false));
  window.addEventListener('orientationchange', () => window.setTimeout(() => refreshEpicaResponsive(true), 250));
})();

