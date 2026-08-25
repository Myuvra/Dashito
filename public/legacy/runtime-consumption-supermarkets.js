
// ---------------- Consumo · supermercados 2026 ----------------
const SUPERMARKET_PULSE_2026={
  months:['Ene','Feb','Mar','Abr','May','Jun'],
  nominal_millions:[2339233.3,2214141.6,2464000.0,2399923.1,2502789.7,2484975.5],
  nominal_yoy:[25.1,23.5,20.5,21.5,25.9,23.7],
  real_yoy:[-1.2,-3.1,-5.1,-3.7,-0.7,-3.1],
  real_accum:[-1.2,-2.1,-3.1,-3.3,-2.8,-2.8],
  june:{sa_mom:-1.0,operations:65548779,ticket:37910,companies:93,stores:3128,workers:95816,workers_yoy:-4.1,credit_share:42.8,credit_millions:1062498.318},
  historical:{national:-9.2,below:22,total:24,period:'1S-2026 vs promedio 1S 2017–2025'},
  district_refs:[
    ['Neuquén',12.8],['Río Negro',5.1],['Santa Fe',-0.4],['Córdoba',-3.2],['CABA',-3.8],['Tierra del Fuego',-4.2],['Resto PBA',-6.3],['La Pampa',-8.8],['San Luis',-12.9],['Chaco',-21.1],['Jujuy',-22.1],['San Juan',-22.1],['La Rioja',-25.0],['Santiago del Estero',-25.1],['Misiones',-29.0],['Corrientes',-32.8],['Tucumán',-33.0],['Formosa',-35.9]
  ]
};
SUPERMARKET_PULSE_2026.h1_nominal_millions=SUPERMARKET_PULSE_2026.nominal_millions.reduce((a,b)=>a+b,0);

function renderSupermarketPulse(){
  if(!window.Plotly)return;
  const mobile=window.innerWidth<=720,d=SUPERMARKET_PULSE_2026;
  const pulse=document.getElementById('supermarketPulseChart');
  if(pulse){
    const nominalB=d.nominal_millions.map(v=>v/1e6);
    Plotly.react(pulse,[
      {type:'bar',x:d.months,y:nominalB,name:'Facturación nominal',marker:{color:'#9c78c6'},text:nominalB.map(v=>'$ '+v.toLocaleString('es-AR',{minimumFractionDigits:2,maximumFractionDigits:2})+' B'),textposition:'outside',cliponaxis:false,customdata:d.months.map((m,i)=>[d.nominal_yoy[i],d.real_yoy[i],d.real_accum[i]]),hovertemplate:'<b>%{x} 2026</b><br>Facturación: <b>$ %{y:.3f} billones</b><br>Nominal ia: <b>+%{customdata[0]:.1f}%</b><br>Real ia: <b>%{customdata[1]:.1f}%</b><br>Real acumulado: <b>%{customdata[2]:.1f}%</b><extra></extra>'},
      {type:'scatter',mode:'lines+markers',x:d.months,y:d.real_yoy,name:'Ventas reales · ia',yaxis:'y2',line:{color:'#c45778',width:3},marker:{size:mobile?7:8,color:'#c45778'},hovertemplate:'<b>%{x} 2026</b><br>Ventas reales: <b>%{y:.1f}% ia</b><extra></extra>'}
    ],{
      ...common,
      margin:{l:mobile?48:62,r:mobile?48:62,t:mobile?72:58,b:44},
      barmode:'group',
      xaxis:{...common.xaxis,fixedrange:true},
      yaxis:{...common.yaxis,title:'$ billones corrientes',rangemode:'tozero',fixedrange:true},
      yaxis2:{title:'variación real ia',overlaying:'y',side:'right',ticksuffix:'%',range:[-7,2],showgrid:false,zeroline:true,zerolinecolor:'#bfaec8',fixedrange:true},
      legend:{...common.legend,orientation:'h',y:mobile?1.13:1.10,x:0,font:{size:mobile?8.5:10.5}},
      annotations:[{xref:'paper',yref:'paper',x:.01,y:-.16,text:'Barras y línea usan escalas distintas · nominal ≠ real',showarrow:false,xanchor:'left',font:{size:mobile?8:9,color:'#806c89'}}]
    },{responsive:true,displaylogo:false,displayModeBar:false,scrollZoom:false,doubleClick:false});
  }

  const district=document.getElementById('supermarketHistoryDistrictChart');
  if(district){
    const rows=[...d.district_refs].sort((a,b)=>a[1]-b[1]);
    Plotly.react(district,[{
      type:'bar',orientation:'h',y:rows.map(r=>r[0]),x:rows.map(r=>r[1]),
      marker:{color:rows.map(r=>r[1]>=0?'#5ba27e':'#ce6686')},
      text:rows.map(r=>(r[1]>=0?'+':'')+r[1].toLocaleString('es-AR',{minimumFractionDigits:1,maximumFractionDigits:1})+'%'),textposition:'outside',cliponaxis:false,
      customdata:rows.map(()=>[d.historical.period]),
      hovertemplate:'<b>%{y}</b><br>Vs promedio histórico: <b>%{x:.1f}%</b><br><span style="font-size:10px">%{customdata[0]}</span><extra></extra>'
    }],{
      ...common,
      margin:{l:mobile?125:135,r:mobile?34:42,t:32,b:44},
      xaxis:{title:'% vs promedio del mismo semestre 2017–2025',range:[-40,16],ticksuffix:'%',gridcolor:'#eee5f2',zeroline:true,zerolinecolor:'#9c879f',fixedrange:true},
      yaxis:{autorange:'reversed',automargin:true,fixedrange:true},
      showlegend:false,
      annotations:[{xref:'paper',yref:'paper',x:0,y:-.13,text:'Sólo referencias con valor explícito publicado · no es el ranking completo',showarrow:false,xanchor:'left',font:{size:mobile?7.5:9,color:'#806c89'}}]
    },{responsive:true,displaylogo:false,displayModeBar:false,scrollZoom:false,doubleClick:false});
  }
}

function downloadSupermarketPulseCsv(){
  const d=SUPERMARKET_PULSE_2026,lines=['tipo,periodo_o_jurisdiccion,ventas_nominales_millones_ars,variacion_nominal_ia_pct,variacion_real_ia_pct,variacion_real_acum_pct,vs_promedio_historico_pct,nota'];
  d.months.forEach((m,i)=>lines.push(`mensual,${m}-2026,${d.nominal_millions[i].toFixed(1)},${d.nominal_yoy[i].toFixed(1)},${d.real_yoy[i].toFixed(1)},${d.real_accum[i].toFixed(1)},,"INDEC · precios corrientes y constantes"`));
  lines.push(`semestre,1S-2026,${d.h1_nominal_millions.toFixed(1)},,,${d.real_accum[5].toFixed(1)},${d.historical.national.toFixed(1)},"Nominal = suma mensual; histórico = Politikon sobre INDEC"`);
  d.district_refs.forEach(([name,v])=>lines.push(`jurisdiccion,"${name}",,,,,${v.toFixed(1)},"Referencia explícitamente publicada; ranking parcial"`));
  const blob=new Blob(['\uFEFF'+lines.join('\n')],{type:'text/csv;charset=utf-8'}),url=URL.createObjectURL(blob),a=document.createElement('a');
  a.href=url;a.download='supermercados_2026_nominal_real_historico.csv';document.body.appendChild(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),800);
}

document.querySelector('.tab-btn[data-tab="tab-consumption"]')?.addEventListener('click',()=>setTimeout(renderSupermarketPulse,160));
if(document.getElementById('tab-consumption')?.classList.contains('active'))setTimeout(renderSupermarketPulse,120);
window.addEventListener('resize',()=>{
  ['supermarketPulseChart','supermarketHistoryDistrictChart'].forEach(id=>{const el=document.getElementById(id);if(el?.data)Plotly.Plots.resize(el)});
});

