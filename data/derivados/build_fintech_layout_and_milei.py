#!/usr/bin/env python3
"""Corrige el bloque Fintech y lo hace visible en “Lo que te robó Milei”."""

from __future__ import annotations

from pathlib import Path


DATA_DIR = Path(__file__).resolve().parents[1]
ROOT_DIR = DATA_DIR.parent
INPUT_NAME = "dashboard_kawaii_124_puente_amortizacion_shock.html"
OUTPUT_NAME = "dashboard_kawaii_125_fintech_visible_sin_superposicion.html"
INPUT_HTML = DATA_DIR / INPUT_NAME
OUTPUT_HTML = DATA_DIR / OUTPUT_NAME
ROOT_OUTPUT_HTML = ROOT_DIR / OUTPUT_NAME


def replace_once(text: str, old: str, new: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"Se esperaba 1 coincidencia y hubo {count}: {old[:120]!r}")
    return text.replace(old, new, 1)


def main() -> None:
    html = INPUT_HTML.read_text(encoding="utf-8")

    html = replace_once(
        html,
        """.rates-fintech-panel{display:grid;grid-template-columns:minmax(260px,.8fr) minmax(0,1.2fr);gap:16px;align-items:center;margin:12px 20px;padding:15px;border:1px solid #edcbd9;border-radius:18px;background:#fff8fb;box-sizing:border-box}
#ratesFintechChart{min-height:210px}""",
        """.rates-fintech-panel{display:grid;grid-template-columns:minmax(260px,.72fr) minmax(0,1.28fr);gap:16px;align-items:center;margin:12px 20px;padding:15px;border:1px solid #edcbd9;border-radius:18px;background:#fff8fb;box-sizing:border-box;overflow:hidden}
#ratesFintechChart{min-width:0;min-height:0;height:auto;width:100%;overflow:hidden}
.rates-fintech-snapshot{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:9px;min-width:0}
.rates-fintech-metric{min-width:0;padding:12px;border:1px solid #eed4df;border-radius:14px;background:#fff;box-sizing:border-box}
.rates-fintech-metric .metric-tag{font-size:8px;font-weight:950;text-transform:uppercase;letter-spacing:.035em;color:#9b7687}
.rates-fintech-metric .metric-value{margin-top:6px;font-size:19px;line-height:1.05;font-weight:950;color:#9f4d6f;overflow-wrap:anywhere}
.rates-fintech-metric.exposure{border-color:#e8b7ca;background:#fff8fb}.rates-fintech-metric.exposure .metric-value{color:#b23f68}
.rates-fintech-metric .metric-note{margin-top:5px;font-size:8.5px;line-height:1.35;color:#83717b}
#tab-milei-cost .milei-financial-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:11px;margin-top:10px}
#tab-milei-cost .milei-financial-item{min-width:0;padding:14px;border:1px solid #e8d6e0;border-radius:16px;background:#fff;box-sizing:border-box}
#tab-milei-cost .milei-financial-item.fintech{border-color:#e8b7ca;background:#fff8fb}
#tab-milei-cost .milei-financial-item .audit-tag{font-size:8.5px;font-weight:950;text-transform:uppercase;letter-spacing:.035em;color:#94758a}
#tab-milei-cost .milei-financial-item.fintech .audit-amount{color:#b23f68}
#tab-milei-cost .milei-financial-summary{margin-top:10px!important;padding:10px 12px;border-left:4px solid #cf6d91;border-radius:11px;background:#fff8fb}""",
    )

    html = replace_once(
        html,
        """@media(max-width:1024px){.rates-usury-callout{grid-template-columns:1fr}.rates-fintech-panel{grid-template-columns:1fr}.rates-money-audit-grid{grid-template-columns:1fr}}""",
        """@media(max-width:1024px){.rates-usury-callout{grid-template-columns:1fr}.rates-fintech-panel{grid-template-columns:1fr}.rates-money-audit-grid{grid-template-columns:1fr}}\n@media(max-width:760px){.rates-fintech-snapshot{grid-template-columns:1fr}#tab-milei-cost .milei-financial-grid{grid-template-columns:1fr}}""",
    )

    old_milei = """  const milei=document.getElementById('mileiFinancialAuditContent');
  if(milei)milei.innerHTML=`<div class=\"audit-amount\">${ratesMoneyArs(p.pinza_neta_hogar)}</div><p>Pinza neta pos-shock estimada para los flujos bancarios auditados, a pesos de ${s.referencia}. Diferencial contra la ventana espejo: <b>${ratesMoneyArs(s.diferencial_pinza)}</b>.</p><p><b>No se suma al total del tab:</b> permanece como tarjeta separada hasta descartar doble conteo con otros contrafactuales.</p>`;"""
    new_milei = """  const milei=document.getElementById('mileiFinancialAuditContent');
  if(milei)milei.innerHTML=`
    <div class=\"milei-financial-grid\">
      <div class=\"milei-financial-item\">
        <div class=\"audit-tag\">Banco + plazo fijo · acumulado pos-shock</div>
        <div class=\"audit-amount\">${ratesMoneyArs(p.pinza_neta_hogar)}</div>
        <p>Pinza neta estimada sobre los flujos bancarios auditados, a pesos de ${s.referencia}. Diferencial contra la ventana espejo: <b>${ratesMoneyArs(s.diferencial_pinza)}</b>.</p>
      </div>
      <div class=\"milei-financial-item fintech\">
        <div class=\"audit-tag\">Fintech · exposición puntual feb-2026</div>
        <div class=\"audit-amount\">${ratesMoneyArs(fintech.exposicion_constante)}</div>
        <p>Stock de cartera de <b>${ratesMoneyArs(fintech.saldo_nominal)}</b> expuesto a una brecha real de <b>${Number(fintech.brecha_pp).toLocaleString('es-AR',{minimumFractionDigits:2,maximumFractionDigits:2})} pp</b>, reexpresado a ${s.referencia}.</p>
      </div>
    </div>
    <p class=\"milei-financial-summary\"><b>Efecto financiero visible:</b> ${ratesMoneyArs(p.pinza_neta_hogar)} acumulados en banco/PF + ${ratesMoneyArs(fintech.exposicion_constante)} de exposición Fintech para dimensionar el costo de la pinza financiera del período.</p>`;"""
    html = replace_once(html, old_milei, new_milei)

    old_chart = """  Plotly.react('ratesFintechChart',[{type:'bar',orientation:'h',x:[s.fintech.exposicion_constante],y:['Fintech · feb-2026'],marker:{color:'#ff6387'},text:[ratesMoneyCompact(s.fintech.exposicion_constante)],textposition:'outside',cliponaxis:false,hovertemplate:'Exposición a la brecha real: <b>$%{x:,.0f}</b><extra></extra>'}],{paper_bgcolor:'rgba(255,255,255,0)',plot_bgcolor:'#fff8fb',font:{color:'#5e4670',family:'Inter,system-ui,sans-serif'},margin:{l:mobile?120:145,r:mobile?55:90,t:25,b:48},xaxis:{title:'Pesos constantes de jul-2026',gridcolor:'#f0dce5',fixedrange:true},yaxis:{fixedrange:true},showlegend:false},{responsive:true,displaylogo:false,displayModeBar:false,scrollZoom:false,doubleClick:false});"""
    new_chart = """  const fintechEl=document.getElementById('ratesFintechChart');
  if(fintechEl)fintechEl.innerHTML=`<div class=\"rates-fintech-snapshot\">
    <div class=\"rates-fintech-metric\"><div class=\"metric-tag\">Stock de cartera</div><div class=\"metric-value\">${ratesMoneyArs(s.fintech.saldo_nominal)}</div><div class=\"metric-note\">Foto ${s.fintech.fecha}</div></div>
    <div class=\"rates-fintech-metric\"><div class=\"metric-tag\">Brecha real</div><div class=\"metric-value\">+${Number(s.fintech.brecha_pp).toLocaleString('es-AR',{minimumFractionDigits:2,maximumFractionDigits:2})} pp</div><div class=\"metric-note\">contra promedio histórico Fintech</div></div>
    <div class=\"rates-fintech-metric exposure\"><div class=\"metric-tag\">Exposición estimada</div><div class=\"metric-value\">${ratesMoneyArs(s.fintech.exposicion_constante)}</div><div class=\"metric-note\">a pesos de ${s.referencia}</div></div>
  </div>`;"""
    html = replace_once(html, old_chart, new_chart)

    html = replace_once(
        html,
        """  document.getElementById('ratesFintechNote').innerHTML=`Foto de <b>${fintech.fecha}</b>: stock Fintech total ${ratesMoneyArs(fintech.saldo_nominal)} × brecha real de ${Number(fintech.brecha_pp).toLocaleString('es-AR',{minimumFractionDigits:2,maximumFractionDigits:2})} pp, reexpresado a ${s.referencia}. No equivale a intereses cobrados ni a crédito nuevo.`;""",
        """  document.getElementById('ratesFintechNote').innerHTML=`Foto de <b>${fintech.fecha}</b>: stock Fintech total ${ratesMoneyArs(fintech.saldo_nominal)} × brecha real de ${Number(fintech.brecha_pp).toLocaleString('es-AR',{minimumFractionDigits:2,maximumFractionDigits:2})} pp, reexpresado a ${s.referencia}. Muestra cuánto capital quedó expuesto al diferencial.`;""",
    )

    OUTPUT_HTML.write_text(html, encoding="utf-8", newline="\n")
    ROOT_OUTPUT_HTML.write_text(html, encoding="utf-8", newline="\n")
    print(f"Generado: {OUTPUT_HTML}")
    print(f"Generado: {ROOT_OUTPUT_HTML}")


if __name__ == "__main__":
    main()
