(() => {
  'use strict';

  if (document.getElementById('epica-stage2-v1')) return;



  const tabs = document.getElementById('dash-main-tabs');
  const caputoButton = tabs?.querySelector('[data-tab="tab-epica-caputo-colchon"]');
  const caputoPanel = document.getElementById('tab-epica-caputo-colchon');
  if (!tabs || !caputoButton || !caputoPanel) return;

  caputoButton

  caputoPanel

  let developmentView = 'activity';
  let narrativeCategory = 'all';
  const plotConfig = {responsive:true,displaylogo:false,displayModeBar:false};
  const narrativeRows = [
    {category:'macro',origin:'“Superávit comercial = superávit de cuenta corriente”',question:'¿Qué componentes conectan el saldo de bienes con la cuenta corriente?',status:'evidencia lista',kind:'observed',reading:'Bienes aportó USD 6.339 M en 2026-Q1, pero servicios e ingreso primario llevaron la cuenta corriente a −USD 1.651 M.',limit:'El dato posterior a 2026-Q1 aún no estaba publicado al corte.',tab:'tab-epica-dollars'},
    {category:'macro',origin:'“Reservas brutas = dólares libres”',question:'¿Qué parte del stock tiene disponibilidad observable y bajo qué condiciones?',status:'en exploración',kind:'open',reading:'La planilla SDDS permite separar composición y flujos predeterminados; el residual de estrés no es una cifra oficial de reservas netas.',limit:'Falta una plantilla sincronizada para netas, líquidas y propias.',tab:'tab-epica-dollars'},
    {category:'households',origin:'“Bajar pobreza = recuperación completa del bienestar”',question:'¿Qué dimensiones faltan para describir la recuperación de los hogares?',status:'en exploración',kind:'open',reading:'Pobreza, uso de ahorro, deuda y mora pueden moverse de forma diferente porque miden personas, hogares y saldos distintos.',limit:'No existe un panel público que siga al mismo hogar.',tab:'tab-epica-households'},
    {category:'households',origin:'“Acceso al crédito = inclusión financiera”',question:'¿Cuándo el crédito amplía oportunidades y cuándo agrega fragilidad?',status:'en exploración',kind:'open',reading:'La cobertura de préstamos personales aumentó y luego creció la irregularidad; la secuencia no identifica causalidad individual.',limit:'Faltan cohortes con tasa, ingreso, destino y resultado.',tab:'tab-morosidad'},
    {category:'development',origin:'“Más inversión = más empleo”',question:'¿Cómo se pasa de una inversión aprobada a empleo ejecutado y permanente?',status:'en exploración',kind:'open',reading:'El portal RIGI informa compromisos y empleos proyectados, pero no una serie homogénea de ejecución ni permanencia.',limit:'Se necesitan avances por proyecto, proveedores y puestos observados.',tab:'tab-epica-development'},
    {category:'development',origin:'“Bajar impuestos siempre aumenta la recaudación”',question:'¿Qué expansión de base compensa cada reducción de alícuota?',status:'escenario',kind:'proxy',reading:'Con recaudación R=t·B, una baja de 10%, 25% o 50% requiere una base 11,11%, 33,33% o 100% mayor para neutralidad.',limit:'La identidad no pronostica formalización ni actividad.',tab:'tab-fiscal'},
    {category:'development',origin:'“Cerrar, desregular o privatizar es un logro por definición”',question:'¿Qué output y qué resultado aparecen después de cada medida?',status:'evidencia lista',kind:'observed',reading:'La acción administrativa es un input. Capacidad, cobertura, precio, calidad y distribución requieren indicadores posteriores.',limit:'Cada política necesita objetivo, línea de base y ventana propios.',tab:'tab-program'}
  ];

  function plotBase(mobile) {
    return {paper_bgcolor:'rgba(0,0,0,0)',plot_bgcolor:'#fff',font:{family:'Inter,system-ui,sans-serif',size:mobile?9:10,color:'#506b7c'},margin:{l:mobile?52:64,r:18,t:28,b:mobile?92:68},hoverlabel:{bgcolor:'#fff',bordercolor:'#cbd9e2',font:{color:'#35576d'}}};
  }

  function setDevelopmentMeta(title,subtitle,badge,kind) {
    document.getElementById('epicaDevelopmentTitle').textContent=title;
    document.getElementById('epicaDevelopmentSubtitle').textContent=subtitle;
    const badgeEl=document.getElementById('epicaDevelopmentBadge');
    badgeEl.textContent=badge; badgeEl.className=`epica-chip ${kind}`;
  }

  function renderDevelopment() {
    const target=document.getElementById('epicaDevelopmentChart');
    if (!target || !window.Plotly) return;
    const mobile=window.innerWidth<=720;
    let traces,layout;
    if (developmentView==='rigi') {
      setDevelopmentMeta('Cronograma de inversión declarado por sector','Portal RIGI · USD millones · no es ejecución ni empleo.','plan de inversión','proxy');
      const years=[2024,2025,2026,2027,2028,2029,2030,2031];
      traces=[
        {type:'bar',name:'Energía',x:years,y:[37,252,162,36,0,0,0,0],marker:{color:'#e7b65e'}},
        {type:'bar',name:'Petróleo y gas',x:years,y:[48,1802,2724,1632,1309,953,1033,915],marker:{color:'#477b9c'}},
        {type:'bar',name:'Minería',x:years,y:[527,1473,2579,3875,4128,3278,2450,1503],marker:{color:'#7c6aa6'}},
        {type:'bar',name:'Otros',x:years,y:[0,174,204,130,40,21,2,0],marker:{color:'#a9bbc7'}}
      ];
      layout={...plotBase(mobile),barmode:'stack',legend:{orientation:'h',y:1.14},yaxis:{title:'USD millones programados',gridcolor:'#e5eef4',fixedrange:true},xaxis:{dtick:1,fixedrange:true},hovermode:'x unified'};
    } else if (developmentView==='capital') {
      setDevelopmentMeta('Flujo real de inversión pública','Índice 2023=100 · ejecución presupuestaria, no condición física.','flujo observado','observed');
      traces=[{type:'bar',x:['2023','2024','2025'],y:[100,24.90,18.18],text:['100','24,90','18,18'],textposition:'outside',cliponaxis:false,marker:{color:['#7ca6bf','#d2a95f','#bd765f']},hovertemplate:'<b>%{x}</b><br>Índice real %{y:.2f}<extra></extra>'}];
      layout={...plotBase(mobile),showlegend:false,yaxis:{title:'Índice real 2023=100',range:[0,112],gridcolor:'#e5eef4',fixedrange:true},xaxis:{fixedrange:true}};
    } else {
      setDevelopmentMeta('Actividad y empleo registrado desde noviembre de 2023','Índices comparables con base 100 en noviembre de 2023.','coexistencia observada','observed');
      traces=[{type:'bar',x:['EMAE desestacionalizado','Empleo privado registrado'],y:[105.154,96.06],text:['105,15','96,06'],textposition:'outside',cliponaxis:false,marker:{color:['#4d8aaa','#c47768']},hovertemplate:'<b>%{x}</b><br>Índice %{y:.2f}<extra></extra>'}];
      layout={...plotBase(mobile),showlegend:false,yaxis:{title:'Índice nov-2023=100',range:[90,108],gridcolor:'#e5eef4',fixedrange:true},xaxis:{tickangle:mobile?-22:0,fixedrange:true},shapes:[{type:'line',x0:-.5,x1:1.5,y0:100,y1:100,line:{color:'#8ba1af',dash:'dot'}}]};
    }
    Plotly.react(target,traces,layout,plotConfig);
  }

  function renderNarratives() {
    const target=document.getElementById('epicaNarrativeGrid');
    if (!target) return;
    target.innerHTML=narrativeRows.filter(row=>narrativeCategory==='all'||row.category===narrativeCategory).map(row=>`<article class="epica-narrative-card"><small>Frase de origen · ${row.category==='macro'?'macro y dólares':row.category==='households'?'hogares y crédito':'Estado y desarrollo'}</small><p class="epica-narrative-origin">${row.origin}</p><h3>${row.question}</h3><p><b>Lectura actual:</b> ${row.reading}</p><p><b>Límite:</b> ${row.limit}</p><div class="epica-narrative-status"><span class="epica-chip ${row.kind}">${row.status}</span><button type="button" onclick="activateTab('${row.tab}')">Abrir evidencia →</button></div></article>`).join('');
  }

  window.renderEpicaDevelopment=renderDevelopment;
  window.renderEpicaNarratives=renderNarratives;

  document.querySelectorAll('[data-epica-development-view]').forEach(button=>button.addEventListener('click',()=>{
    developmentView=button.dataset.epicaDevelopmentView;
    document.querySelectorAll('[data-epica-development-view]').forEach(item=>{const active=item===button;item.classList.toggle('active',active);item.setAttribute('aria-pressed',String(active));});
    renderDevelopment();
  }));
  document.querySelectorAll('[data-epica-narrative-category]').forEach(button=>button.addEventListener('click',()=>{
    narrativeCategory=button.dataset.epicaNarrativeCategory;
    document.querySelectorAll('[data-epica-narrative-category]').forEach(item=>{const active=item===button;item.classList.toggle('active',active);item.setAttribute('aria-pressed',String(active));});
    renderNarratives();
  }));

  tabs.querySelector('[data-tab="tab-epica-development"]')?.addEventListener('click',()=>window.setTimeout(renderDevelopment,190));
  tabs.querySelector('[data-tab="tab-epica-narratives"]')?.addEventListener('click',()=>window.setTimeout(renderNarratives,190));
  renderNarratives();
})();

