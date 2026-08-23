from pathlib import Path


SOURCE = Path(r"C:\Github\inflacion\data\dashboard_kawaii_131_a_quien_le_conviene.html")
OUTPUT = Path(r"C:\Github\inflacion\data\dashboard_kawaii_132_checkbox_foco_post_shock.html")


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: se esperaba 1 coincidencia y aparecieron {count}")
    return text.replace(old, new, 1)


if not SOURCE.exists():
    raise FileNotFoundError(SOURCE)
if OUTPUT.exists():
    raise FileExistsError(f"No se pisa una versión existente: {OUTPUT}")

html = SOURCE.read_text(encoding="utf-8")

css = r'''
<style id="rates-timeline-checkbox-v132">
/* v132 · foco cronológico opcional, inspirado en el control de Mayoristas */
.rates-timeline-toggle{display:flex;align-items:center;justify-content:space-between;gap:14px;margin:0 0 14px;padding:12px 15px;border:1px solid #ddcfe8;border-radius:17px;background:linear-gradient(135deg,#fff9fc,#f8fbff);box-sizing:border-box;color:#67556e}
.rates-timeline-toggle label{display:flex;align-items:center;gap:10px;cursor:pointer;font-size:11px;line-height:1.4;font-weight:900;color:#5e436b}
.rates-timeline-toggle input{width:18px;height:18px;flex:0 0 auto;accent-color:#a764b3;cursor:pointer}
.rates-timeline-toggle .copy{display:flex;flex-direction:column;gap:2px}
.rates-timeline-toggle .copy small{font-size:9.5px;font-weight:650;color:#7d6c81}
.rates-timeline-status{flex:0 0 auto;padding:6px 9px;border:1px solid #d5c8e2;border-radius:999px;background:#fff;font-size:9px;font-weight:900;color:#755c82;white-space:nowrap}
.mobile-range-control.rates-focus-disabled{opacity:.42;pointer-events:none;filter:grayscale(.35)}
@media(max-width:720px){.rates-timeline-toggle{align-items:flex-start;flex-direction:column;margin-left:0;margin-right:0}.rates-timeline-status{white-space:normal}}
</style>
'''
html = replace_once(html, "</head>", css + "</head>", "CSS del checkbox")

toggle = r'''    <div class="rates-timeline-toggle" id="ratesTimelineToggleBox">
      <label for="ratesPostShockOnly">
        <input id="ratesPostShockOnly" type="checkbox">
        <span class="copy">
          Ocultar el tramo previo al shock en los gráficos ① y ②
          <small>Al activarlo, ambos gráficos enfocan dic-2023 → jul-2026. Sólo cambia lo visible: no modifica datos, saldos ni cálculos.</small>
        </span>
      </label>
      <span class="rates-timeline-status" id="ratesTimelineStatus">Vista completa</span>
    </div>
    <div class="grid">
      <main class="two">
        <section class="card">
          <div class="card-head">
            <div class="card-title">① Contexto nominal anual <span>♡</span></div>'''
html = replace_once(
    html,
    '''    <div class="grid">
      <main class="two">
        <section class="card">
          <div class="card-head">
            <div class="card-title">① Contexto nominal anual <span>♡</span></div>''',
    toggle,
    "control cronológico del tab Tasas",
)

focus_js = r'''
function bindRatesTimelineFocus(){
  const toggle=document.getElementById('ratesPostShockOnly');
  if(!toggle||toggle.dataset.bound)return;
  toggle.dataset.bound='1';
  toggle.addEventListener('change',applyRatesTimelineFocus);
}

function applyRatesTimelineFocus(){
  const toggle=document.getElementById('ratesPostShockOnly');
  if(!toggle)return;
  const focused=toggle.checked;
  const status=document.getElementById('ratesTimelineStatus');
  const nominalSlider=document.getElementById('nominalRange');
  const realSlider=document.getElementById('realRange');
  const nominalControl=document.getElementById('nominalRangeControl');
  const realControl=document.getElementById('realRangeControl');

  if(status)status.textContent=focused?'Foco pos-shock · dic-2023 → jul-2026':'Vista completa / control manual';
  if(nominalSlider)nominalSlider.disabled=focused;
  if(realSlider)realSlider.disabled=focused;
  if(nominalControl)nominalControl.classList.toggle('rates-focus-disabled',focused);
  if(realControl)realControl.classList.toggle('rates-focus-disabled',focused);

  const nominalChart=document.getElementById('nominalChart');
  const realChart=document.getElementById('realChart');
  if(typeof Plotly==='undefined'||!nominalChart?.data||!realChart?.data)return;

  if(focused){
    Plotly.relayout('nominalChart',{'xaxis.autorange':false,'xaxis.range':[2022.55,2026.5]});
    Plotly.relayout('realChart',{'xaxis.autorange':false,'xaxis.range':['2023-12-01','2026-08-01']});
    const nf=document.getElementById('nominalRangeFrom'),nt=document.getElementById('nominalRangeTo');
    const rf=document.getElementById('realRangeFrom'),rt=document.getElementById('realRangeTo');
    if(nf)nf.textContent='dic-2023'; if(nt)nt.textContent='2026';
    if(rf)rf.textContent='dic-2023'; if(rt)rt.textContent='2026';
  }else if(window.innerWidth<=720){
    applyNominalRange();
    applyRealRange();
  }else{
    Plotly.relayout('nominalChart',{'xaxis.autorange':false,'xaxis.range':[2001.5,2026.5]});
    Plotly.relayout('realChart',{'xaxis.autorange':false,'xaxis.range':['2019-01-01','2026-08-01']});
  }
}

'''
html = replace_once(
    html,
    '''function setupNativeRanges() {''',
    focus_js + '''function setupNativeRanges() {''',
    "funciones del foco pos-shock",
)

html = replace_once(
    html,
    '''    applyNominalRange();
    applyRealRange();
    Plotly.Plots.resize(document.getElementById('nominalChart'));''',
    '''    applyNominalRange();
    applyRealRange();
    bindRatesTimelineFocus();
    applyRatesTimelineFocus();
    Plotly.Plots.resize(document.getElementById('nominalChart'));''',
    "reaplicar foco tras render responsive",
)

html = replace_once(
    html,
    '''  applyPowerRange();
  applyNominalRange();
  applyRealRange();
}, 150);''',
    '''  applyPowerRange();
  applyNominalRange();
  applyRealRange();
  bindRatesTimelineFocus();
  applyRatesTimelineFocus();
}, 150);''',
    "inicialización del checkbox",
)

OUTPUT.write_text(html, encoding="utf-8")
print(OUTPUT)
