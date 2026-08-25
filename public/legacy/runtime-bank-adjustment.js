
const BANK_ADJUSTMENT_2024={
  fiscal:{primary2023:-2.9,primary2024:1.8,imfConsolidation:5.0},
  money:{gdp2024Ars:583909615e6,ipcAvg2024:6317.7413166667,ipcJul2026:12076.3937,priceLabel:'jul-2026'},
  indec:{
    years:[2016,2017,2018,2019,2020,2021,2022,2023,2024],
    operatingSurplus:[1.1,.8,.8,.4,.9,.4,0,-.9,1.0],
    propertyIncome:[.3,.3,.6,1.2,1.2,1.3,2.5,4.9,3.7],
    primaryIncome:[1.4,1.1,1.4,1.6,2.1,1.7,2.5,4.0,4.7],
    currentTaxes:[.4,.4,.4,.2,.4,.4,.5,1.6,.6],
    grossSaving:[.9,.5,.8,1.2,1.6,1.2,1.9,2.2,4.0],
    netLending:[.7,.4,.7,1.0,1.4,1.1,1.7,2.2,4.0]
  },
  profitability:{labels:['2023','2024','2025','jun-2026 · 12m'],roa:[5.3,4.1,1.0,1.2],roe:[26.9,15.8,4.4,null]},
  capital:{labels:['dic-2023','dic-2024','jun-2026'],excessRequirement:[302.7,279,269],excessCredit:[60.2,45.1,35.4],tenYearCreditAvg:[21.4,26.7,null]}
};
let bankAdjustmentRendered=false;
function bankAdjustMean(a){return a.reduce((s,v)=>s+v,0)/a.length}
function bankAdjustPct(v,d=1){return v.toLocaleString('es-AR',{minimumFractionDigits:d,maximumFractionDigits:d})+'%'}
function bankAdjustPp(v,d=1){return v.toLocaleString('es-AR',{minimumFractionDigits:d,maximumFractionDigits:d})+' pp'}
function bankAdjustMoney(v){
  if(typeof powerMoneyBillions==='function')return powerMoneyBillions(v);
  return '$ '+(v/1e12).toLocaleString('es-AR',{minimumFractionDigits:2,maximumFractionDigits:2})+' billones';
}
function bankAdjustModel(){
  const d=BANK_ADJUSTMENT_2024, fiscalSwing=d.fiscal.primary2024-d.fiscal.primary2023;
  const histAvg=bankAdjustMean(d.indec.grossSaving.slice(0,7));
  const taxPp=d.indec.currentTaxes[7]-d.indec.currentTaxes[8];
  const savingPp=d.indec.grossSaving[8]-d.indec.grossSaving[7];
  const historicalPp=d.indec.grossSaving[8]-histAvg;
  let grossShock=18.43e12,recovered=6.08e12,pinch=2.886133051e12,postBalance=5.852938441375309e12,bankPinch=1.0410172449149282e12,fintechPinch=1.845115806067871e12;
  try{const loss=typeof powerAggregateLossEstimate==='function'?powerAggregateLossEstimate():null;if(loss){grossShock=loss.grossCurrent;recovered=loss.recoveredCurrent}}catch(e){}
  try{if(typeof ratesMoneySummary!=='undefined'){const p=ratesMoneySummary.post,m=ratesMoneySummary.mirror,d=ratesMoneySummary.diferencial;pinch=Math.max(0,-(d.impacto_hogar_banco+d.impacto_hogar_fintech));postBalance=Math.max(0,-p.impacto_hogar_total_ampliado);bankPinch=Math.max(0,-d.impacto_hogar_banco);fintechPinch=Math.max(0,-d.impacto_hogar_fintech)}}catch(e){}
  const remaining=Math.max(0,grossShock-recovered);
  const priceFactor=d.money.ipcJul2026/d.money.ipcAvg2024;
  const ppToJul2026=pp=>d.money.gdp2024Ars*(pp/100)*priceFactor;
  return {fiscalSwing,histAvg,taxPp,savingPp,historicalPp,grossShock,recovered,remaining,pinch,postBalance,bankPinch,fintechPinch,priceFactor,
    taxMoney2024:d.money.gdp2024Ars*(taxPp/100),savingMoney2024:d.money.gdp2024Ars*(savingPp/100),historicalMoney2024:d.money.gdp2024Ars*(historicalPp/100),
    taxMoneyCurrent:ppToJul2026(taxPp),savingMoneyCurrent:ppToJul2026(savingPp),historicalMoneyCurrent:ppToJul2026(historicalPp),
    taxPct:taxPp/fiscalSwing*100,savingPct:savingPp/fiscalSwing*100,historicalPct:historicalPp/fiscalSwing*100,
    taxImf:taxPp/d.fiscal.imfConsolidation*100,savingImf:savingPp/d.fiscal.imfConsolidation*100,historicalImf:historicalPp/d.fiscal.imfConsolidation*100,
    pinchGross:pinch/grossShock*100,pinchRemaining:remaining?pinch/remaining*100:0};
}
function bankAdjustLayout(titleY,mobile=false){return {paper_bgcolor:'rgba(0,0,0,0)',plot_bgcolor:'rgba(255,255,255,.72)',font:{family:'Nunito,Inter,Arial,sans-serif',size:mobile?9:10,color:'#66506d'},margin:{l:mobile?52:66,r:mobile?20:36,t:mobile?38:42,b:mobile?58:50},hoverlabel:{bgcolor:'#fff7fb',bordercolor:'#e6bfd0',font:{color:'#51385e'}},xaxis:{gridcolor:'#eee5f1',zeroline:false},yaxis:{title:titleY,gridcolor:'#eee5f1',zeroline:true,zerolinecolor:'#b9a8c1'},legend:{orientation:'h',y:1.12,x:0}}}
function renderBankAdjustment2024(){
  const root=document.getElementById('ratesBankCapacitySection');if(!root||!window.Plotly)return;
  const d=BANK_ADJUSTMENT_2024,m=bankAdjustModel(),mobile=window.innerWidth<=720;
  const set=(id,text)=>{const el=document.getElementById(id);if(el)el.textContent=text};
  set('bankAdjustFiscalSwing',bankAdjustPp(m.fiscalSwing,1)+' PBI');
  set('bankAdjustPinchMoney',bankAdjustMoney(m.pinch));set('bankAdjustPinchGross',bankAdjustPct(m.pinchGross,1));set('bankAdjustPinchRemaining',bankAdjustPct(m.pinchRemaining,1));
  set('bankAdjustTaxMoney','≈ '+bankAdjustMoney(m.taxMoneyCurrent));set('bankAdjustTaxPct','≈ '+bankAdjustPct(m.taxPct,1));set('bankAdjustTaxImf','FMI: ≈ '+bankAdjustPct(m.taxImf,0));
  set('bankAdjustSavingMoney','≈ '+bankAdjustMoney(m.savingMoneyCurrent));set('bankAdjustSavingPct','≈ '+bankAdjustPct(m.savingPct,1));set('bankAdjustSavingImf','FMI: ≈ '+bankAdjustPct(m.savingImf,0));
  set('bankAdjustHistoricalMoney','≈ '+bankAdjustMoney(m.historicalMoneyCurrent));set('bankAdjustHistoricalPct','≈ '+bankAdjustPct(m.historicalPct,1));set('bankAdjustHistoricalImf','FMI: ≈ '+bankAdjustPct(m.historicalImf,1));
  set('bankAdjustFintechPinch',bankAdjustMoney(m.fintechPinch));
  const reading=document.getElementById('bankAdjustReading');if(reading)reading.innerHTML=`<strong>En pesos de ${d.money.priceLabel}, el rango bancario central es ≈ ${bankAdjustMoney(m.taxMoneyCurrent)}–${bankAdjustMoney(m.savingMoneyCurrent)}.</strong> Eso equivale a <span class="range">≈ ${bankAdjustPct(m.taxPct,0)}–${bankAdjustPct(m.savingPct,0)}</span> del giro primario observado de 2024. El escenario histórico agresivo sube a <b>≈ ${bankAdjustMoney(m.historicalMoneyCurrent)}</b>. El deterioro deudor usado como contexto es ${bankAdjustMoney(m.pinch)} frente al espejo; el saldo ampliado post-shock contra normas fue ${bankAdjustMoney(m.postBalance)}. Fintech: capacidad N/D. Esto describe <b>capacidad contrafactual de reparto</b>, no una ganancia ni una transferencia probada.`;

  const scenarioNames=['Mantener carga tributaria 2023','Mantener ahorro/PBI 2023','Volver al promedio 2016–22'];
  const scenarioVals=[m.taxPct,m.savingPct,m.historicalPct],imfVals=[m.taxImf,m.savingImf,m.historicalImf],moneyVals=[m.taxMoneyCurrent,m.savingMoneyCurrent,m.historicalMoneyCurrent];
  Plotly.react('bankAdjustScenarioChart',[{type:'bar',orientation:'h',y:scenarioNames,x:scenarioVals,marker:{color:['#6c86bd','#4c9a78','#c59645'],line:{color:'#fff',width:1}},text:scenarioVals.map((v,i)=>bankAdjustMoney(moneyVals[i])+' · '+bankAdjustPct(v,1)),textposition:'outside',cliponaxis:false,customdata:scenarioVals.map((v,i)=>[imfVals[i],moneyVals[i]/1e12]),hovertemplate:'<b>%{y}</b><br>Pesos jul-2026: $ %{customdata[1]:.2f} billones<br>Sobre giro observado 4,7 pp: %{x:.1f}%<br>Sobre FMI 5 pp: %{customdata[0]:.1f}%<extra></extra>'}],{...bankAdjustLayout('% del giro fiscal',mobile),margin:{l:mobile?145:210,r:mobile?50:65,t:28,b:45},xaxis:{title:'% del giro primario 2023→2024',range:[0,Math.max(68,Math.ceil(m.historicalPct+7))],gridcolor:'#eee5f1'},yaxis:{autorange:'reversed',automargin:true},showlegend:false},{responsive:true,displaylogo:false,displayModeBar:false});

  const avgLine=d.indec.years.map(()=>m.histAvg);
  Plotly.react('bankAdjustSavingChart',[{x:d.indec.years,y:d.indec.grossSaving,type:'scatter',mode:'lines+markers',name:'Ahorro bruto / PBI',line:{color:'#5e4ca8',width:3},marker:{size:7},hovertemplate:'<b>%{x}</b><br>Ahorro bruto: %{y:.1f}% del PBI<extra></extra>'},{x:d.indec.years,y:avgLine,type:'scatter',mode:'lines',name:'Promedio 2016–22 · '+bankAdjustPct(m.histAvg,2),line:{color:'#c08c39',dash:'dash',width:2},hoverinfo:'skip'}],{...bankAdjustLayout('% del PBI',mobile),margin:{l:55,r:20,t:38,b:45},xaxis:{dtick:1,fixedrange:true},yaxis:{title:'% del PBI',gridcolor:'#eee5f1',zeroline:true,zerolinecolor:'#b9a8c1'},shapes:[{type:'line',x0:2023.5,x1:2023.5,y0:0,y1:1,yref:'paper',line:{color:'#dc7395',width:1.5,dash:'dot'}}],annotations:[{x:2024,y:4.0,text:'4,0% · máximo de la serie',showarrow:true,ax:mobile?-54:-72,ay:34,bgcolor:'#fff7fb',bordercolor:'#e4bfd0',font:{size:9,color:'#6b4b76'}}]},{responsive:true,displaylogo:false,displayModeBar:false});

  const prof=d.profitability;
  Plotly.react('bankAdjustProfitChart',[{x:prof.labels,y:prof.roa,type:'bar',name:'ROA · % activo',marker:{color:'#657fc0'},text:prof.roa.map(v=>bankAdjustPct(v,1)),textposition:'outside',hovertemplate:'<b>%{x}</b><br>ROA: %{y:.1f}%<extra></extra>'},{x:prof.labels,y:prof.roe,type:'scatter',mode:'lines+markers+text',name:'ROE · % patrimonio',yaxis:'y2',line:{color:'#d45d87',width:3},marker:{size:7},text:prof.roe.map(v=>v==null?'':bankAdjustPct(v,1)),textposition:'top center',hovertemplate:'<b>%{x}</b><br>ROE: %{y:.1f}%<extra></extra>'}],{...bankAdjustLayout('ROA · % activo',mobile),margin:{l:55,r:mobile?42:58,t:46,b:62},xaxis:{type:'category',tickangle:mobile?-25:0},yaxis:{title:'ROA · % del activo',rangemode:'tozero',gridcolor:'#eee5f1'},yaxis2:{title:'ROE · % patrimonio',overlaying:'y',side:'right',rangemode:'tozero',showgrid:false},legend:{orientation:'h',y:1.14,x:0}},{responsive:true,displaylogo:false,displayModeBar:false});

  const cap=d.capital;
  Plotly.react('bankAdjustCapitalChart',[{x:cap.labels,y:cap.excessRequirement,type:'bar',name:'Exceso / exigencia regulatoria',marker:{color:'#6f59ad'},text:cap.excessRequirement.map(v=>bankAdjustPct(v,0)),textposition:'outside',hovertemplate:'<b>%{x}</b><br>Exceso / exigencia: %{y:.1f}%<extra></extra>'},{x:cap.labels,y:cap.excessCredit,type:'scatter',mode:'lines+markers+text',name:'Exceso / crédito privado neto',yaxis:'y2',line:{color:'#4e9b79',width:3},marker:{size:8},text:cap.excessCredit.map(v=>bankAdjustPct(v,1)),textposition:'top center',hovertemplate:'<b>%{x}</b><br>Exceso / crédito neto: %{y:.1f}%<extra></extra>'}],{...bankAdjustLayout('% exigencia',mobile),margin:{l:55,r:mobile?44:60,t:48,b:58},yaxis:{title:'% de la exigencia',rangemode:'tozero',gridcolor:'#eee5f1'},yaxis2:{title:'% del crédito neto',overlaying:'y',side:'right',range:[0,75],showgrid:false},legend:{orientation:'h',y:1.14,x:0}},{responsive:true,displaylogo:false,displayModeBar:false});

  const rows=[
    ['Excedente de explotación bruto',-.9,1.0,'pp PBI'],['Rentas de la propiedad netas',4.9,3.7,'pp PBI'],['Saldo de ingresos primarios bruto',4.0,4.7,'pp PBI'],['Impuestos corrientes sobre ingreso y riqueza',1.6,.6,'pp PBI'],['Ahorro bruto / ingreso disponible',2.2,4.0,'pp PBI'],['Préstamo neto / capacidad de financiamiento',2.2,4.0,'pp PBI']
  ];
  const readings={
    'Excedente de explotación bruto':'revirtió de negativo a positivo','Rentas de la propiedad netas':'bajaron, aunque siguieron altas','Saldo de ingresos primarios bruto':'aumentó 0,7 pp','Impuestos corrientes sobre ingreso y riqueza':'bajaron 1,0 pp; no implica por sí solo rebaja discrecional','Ahorro bruto / ingreso disponible':'subió 1,8 pp','Préstamo neto / capacidad de financiamiento':'subió 1,8 pp'
  };
  const tbody=document.getElementById('bankAdjustTableBody');if(tbody)tbody.innerHTML=rows.map(([name,a,b])=>{const ch=b-a,cls=ch>0?'up':ch<0?'down':'';return `<tr><td><strong>${name}</strong></td><td>${bankAdjustPct(a,1)}</td><td>${bankAdjustPct(b,1)}</td><td class="${cls}">${ch>=0?'+':''}${bankAdjustPp(ch,1)}</td><td style="text-align:left">${readings[name]}</td></tr>`}).join('');
  bankAdjustmentRendered=true;
}
function downloadBankAdjustmentCsv(){
  const d=BANK_ADJUSTMENT_2024,m=bankAdjustModel(),lines=['tipo,periodo,indicador,valor,unidad,nota'];
  d.indec.years.forEach((y,i)=>{[['ahorro_bruto_pbi',d.indec.grossSaving[i]],['ingreso_primario_bruto_pbi',d.indec.primaryIncome[i]],['impuestos_corrientes_pbi',d.indec.currentTaxes[i]],['excedente_explotacion_bruto_pbi',d.indec.operatingSurplus[i]],['rentas_propiedad_netas_pbi',d.indec.propertyIncome[i]],['prestamo_neto_pbi',d.indec.netLending[i]]].forEach(([k,v])=>lines.push(`INDEC,${y},${k},${v},% PBI,"Sociedades de depósito excepto BCRA"`))});
  [['tributario',m.taxPct,m.taxImf,m.taxMoney2024,m.taxMoneyCurrent],['ahorro_2023',m.savingPct,m.savingImf,m.savingMoney2024,m.savingMoneyCurrent],['historico_2016_2022',m.historicalPct,m.historicalImf,m.historicalMoney2024,m.historicalMoneyCurrent]].forEach(([k,v,imf,ars2024,arsCurrent])=>{lines.push(`contrafactual,2024,${k},${v.toFixed(4)},% giro primario 4.7 pp,"escenario alternativo; no sumar"`);lines.push(`contrafactual_FMI,2024,${k},${imf.toFixed(4)},% consolidación 5 pp,"denominador alternativo FMI"`);lines.push(`contrafactual_monto,2024,${k},${ars2024.toFixed(0)},ARS 2024,"PIB nominal 2024 × pp del PBI"`);lines.push(`contrafactual_monto,2026-07,${k},${arsCurrent.toFixed(0)},ARS jul-2026,"actualizado por IPC promedio 2024 → jul-2026; factor ${m.priceFactor.toFixed(6)}"`)});
  lines.push(`base,2024,pib_nominal,${d.money.gdp2024Ars.toFixed(0)},ARS,"INDEC"`);lines.push(`base,2024,ipc_promedio,${d.money.ipcAvg2024.toFixed(6)},indice,"promedio mensual IPC nacional"`);lines.push(`base,2026-07,ipc,${d.money.ipcJul2026.toFixed(6)},indice,"último IPC oficial disponible al 23-08-2026"`);
  lines.push(`hogares,2023-12_2026-07,deterioro_deudor_vs_espejo,${m.pinch.toFixed(0)},ARS jul-2026,"costo del lado hogar; no ganancia bancaria"`);
  lines.push(`hogares,2023-12_2026-07,deterioro_deudor_sobre_agujero_bruto,${m.pinchGross.toFixed(4)},%,"derivado del dashboard"`);lines.push(`hogares,2023-12_2026-07,deterioro_deudor_sobre_saldo_no_recuperado,${m.pinchRemaining.toFixed(4)},%,"derivado del dashboard"`);
  const blob=new Blob(['\ufeff'+lines.join('\n')],{type:'text/csv;charset=utf-8'}),a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download='bancos_vs_ajuste_2024.csv';document.body.appendChild(a);a.click();setTimeout(()=>{URL.revokeObjectURL(a.href);a.remove()},0);
}
document.querySelector('.tab-btn[data-tab="tab-rates"]')?.addEventListener('click',()=>requestAnimationFrame(renderBankAdjustment2024));
if(document.getElementById('tab-rates')?.classList.contains('active'))requestAnimationFrame(renderBankAdjustment2024);
window.addEventListener('resize',()=>{if(!bankAdjustmentRendered||!window.Plotly)return;['bankAdjustScenarioChart','bankAdjustSavingChart','bankAdjustProfitChart','bankAdjustCapitalChart'].forEach(id=>{const el=document.getElementById(id);if(el)Plotly.Plots.resize(el)})});

