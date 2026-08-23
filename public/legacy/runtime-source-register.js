
function sourceProjectAsset(path){
  const clean=String(path||'').replace(/^\.\//,'');
  const inVersion=/\/data\/dashboard_/i.test(location.pathname);
  return new URL(inVersion?clean.replace(/^data\//,''):clean,location.href).href;
}
function sourceLinkKind(link){
  const raw=((link.getAttribute('data-source-path')||'')+' '+(link.getAttribute('href')||'')+' '+(link.textContent||'')).toLowerCase();
  if(/auditor|metodolog|cálculo|calculo|reproduc/.test(raw))return 'audit';
  if(/\.(csv|xls|xlsx|json|zip|txt)(?:$|[?#])|dataset|repositorio|serie oficial|archivo|manifiesto|anexo/.test(raw))return 'data';
  return 'primary';
}
function sourcePanelForTab(tab){
  const explicit=tab.querySelector('[data-source-panel]');
  if(explicit)return explicit;
  const standard=tab.querySelector('.sources-box');
  if(standard)return standard;
  const sourceChild=tab.querySelector('.emae-source-list,.pend-source-grid,.wealth-sources,.road-sources,.tour-sources');
  return sourceChild?.closest('section,div')||null;
}
function normalizeSourceRegisters(){
  const audit=[];
  document.querySelectorAll('.tab-panel').forEach(tab=>{
    let panel=sourcePanelForTab(tab);
    const tabLabel=document.querySelector(`.tab-btn[data-tab="${tab.id}"]`)?.textContent.trim()||tab.id;
    if(!panel){
      panel=document.createElement('section');
      panel.className='source-register source-register-missing';
      panel.dataset.sourcePanel='missing';
      tab.append(panel);
    }
    panel.classList.add('source-register');
    panel.querySelectorAll('[data-source-path]').forEach(link=>link.setAttribute('href',sourceProjectAsset(link.dataset.sourcePath)));
    const links=[...panel.querySelectorAll('a[href]')].filter(link=>link.getAttribute('href')!=='#');
    links.forEach(link=>{
      const kind=sourceLinkKind(link);
      link.classList.add('source-register-link',`source-kind-${kind}`);
      if(/^https?:/i.test(link.href)){link.target='_blank';link.rel='noopener noreferrer';}
    });
    const counts={primary:0,data:0,audit:0};
    links.forEach(link=>counts[sourceLinkKind(link)]++);
    if(!panel.querySelector(':scope > .source-register-standard')){
      const header=document.createElement('div');
      header.className='source-register-standard';
      const ok=links.length>0;
      header.innerHTML=`<div class="source-register-copy"><span class="source-register-kicker">Fuentes y trazabilidad</span><strong>Respaldo visible de esta pestaña</strong><small>Separamos publicación de origen, archivos de datos y auditorías/cálculos propios.</small></div><div class="source-register-status"><span class="${ok?'ok':'warn'}">${ok?'✓':'!'} ${links.length} referencia${links.length===1?'':'s'} visible${links.length===1?'':'s'}</span><span>corte · 22 ago 2026</span><a href="${sourceProjectAsset('data/derivados/AUDITORIA_COBERTURA_FUENTES_V149.md')}" target="_blank" rel="noopener">auditoría global ↗</a></div>`;
      panel.prepend(header);
      const legend=document.createElement('div');
      legend.className='source-register-legend';
      legend.innerHTML='<span class="primary">Publicación o institución de origen</span><span class="data">Dato, serie o archivo</span><span class="audit">Auditoría, método o cálculo</span>';
      header.after(legend);
    }
    panel.dataset.sourceCoverage=links.length?'ok':'missing';
    audit.push({tab:tab.id,label:tabLabel,references:links.length,...counts,status:links.length?'ok':'missing'});
  });
  window.SOURCE_COVERAGE_AUDIT_V149=audit;
}
normalizeSourceRegisters();

