#!/usr/bin/env python3
"""Agrega al dashboard v123 el puente visual de amortización del shock salarial."""

from __future__ import annotations

from pathlib import Path


DATA_DIR = Path(__file__).resolve().parents[1]
ROOT_DIR = DATA_DIR.parent
INPUT_NAME = "dashboard_kawaii_123_salarios_junio_2026.html"
OUTPUT_NAME = "dashboard_kawaii_124_puente_amortizacion_shock.html"
INPUT_HTML = DATA_DIR / INPUT_NAME
OUTPUT_HTML = DATA_DIR / OUTPUT_NAME
ROOT_OUTPUT_HTML = ROOT_DIR / OUTPUT_NAME


def replace_once(text: str, old: str, new: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"Se esperaba 1 coincidencia y hubo {count}: {old[:100]!r}")
    return text.replace(old, new, 1)


def main() -> None:
    html = INPUT_HTML.read_text(encoding="utf-8")

    css_anchor = """@media(max-width:440px){
  #tab-milei-cost .milei-cost-kpis,#tab-milei-cost .milei-cost-formula{grid-template-columns:1fr}
  #tab-milei-cost .milei-cost-amount{font-size:32px}
}
</style>


<style id=\"rates-accum-v118\">"""
    css_replacement = """@media(max-width:440px){
  #tab-milei-cost .milei-cost-kpis,#tab-milei-cost .milei-cost-formula{grid-template-columns:1fr}
  #tab-milei-cost .milei-cost-amount{font-size:32px}
}

/* v124 · puente visible hasta amortiguar el shock */
#tab-milei-cost .milei-shock-bridge{
  margin-top:16px;padding:20px;border:2px solid #dfc6eb;border-radius:22px;
  background:linear-gradient(135deg,#fff8fc 0%,#faf7ff 54%,#f4fffb 100%);
  box-shadow:0 10px 26px rgba(107,70,125,.09);box-sizing:border-box
}
#tab-milei-cost .milei-shock-bridge .eyebrow{
  font-size:9px;font-weight:950;text-transform:uppercase;letter-spacing:.05em;color:#8d659d
}
#tab-milei-cost .milei-shock-bridge h2{
  margin:7px 0 5px;font-size:23px;line-height:1.15;color:#6c477b
}
#tab-milei-cost .milei-shock-bridge .lead{
  margin:0;max-width:1080px;font-size:11.5px;line-height:1.55;color:#735f7d
}
#tab-milei-cost .milei-bridge-grid{
  display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:10px;margin-top:15px
}
#tab-milei-cost .milei-bridge-card{
  min-width:0;padding:12px 13px;border:1px solid #e4d8ea;border-radius:15px;background:rgba(255,255,255,.9);box-sizing:border-box
}
#tab-milei-cost .milei-bridge-card .tag{
  font-size:8.5px;font-weight:950;text-transform:uppercase;letter-spacing:.03em;color:#907b9a
}
#tab-milei-cost .milei-bridge-card .val{
  margin-top:5px;font-size:20px;line-height:1.05;font-weight:950;color:#6d4c79
}
#tab-milei-cost .milei-bridge-card.recovered .val{color:#43866b}
#tab-milei-cost .milei-bridge-card.editorial .val{color:#a9782d}
#tab-milei-cost .milei-bridge-card.remaining{border-color:#e5b9ca;background:#fff8fb}
#tab-milei-cost .milei-bridge-card.remaining .val{color:#b1496d}
#tab-milei-cost .milei-shock-track{
  display:flex;height:18px;margin-top:15px;border-radius:999px;overflow:hidden;background:#f0eaf3;box-shadow:inset 0 0 0 1px #e2d8e7
}
#tab-milei-cost .milei-shock-track>span{display:block;height:100%;min-width:0}
#tab-milei-cost .milei-shock-track .salary{background:linear-gradient(90deg,#63b294,#83c7ae)}
#tab-milei-cost .milei-shock-track .editorial{background:linear-gradient(90deg,#e6bb61,#d89946)}
#tab-milei-cost .milei-shock-track .remaining{background:linear-gradient(90deg,#dc86a4,#bc4e73)}
#tab-milei-cost .milei-shock-legend{
  display:flex;flex-wrap:wrap;gap:7px 15px;margin-top:8px;font-size:9.5px;color:#77657d
}
#tab-milei-cost .milei-shock-legend span{display:flex;align-items:center;gap:5px}
#tab-milei-cost .milei-shock-legend i{width:9px;height:9px;border-radius:50%;display:inline-block}
#tab-milei-cost .milei-shock-formula{
  margin-top:13px;padding:12px 14px;border:1px solid #decfe6;border-radius:15px;background:#fff;
  font-size:13px;line-height:1.45;color:#684e72;text-align:center
}
#tab-milei-cost .milei-shock-formula strong{color:#ad4269;font-size:17px}
#tab-milei-cost .milei-shock-scenario{
  margin-top:10px;padding:11px 13px;border-left:4px solid #69b498;border-radius:12px;background:#f5fffa;
  font-size:10.5px;line-height:1.55;color:#5e766d
}
@media(max-width:980px){
  #tab-milei-cost .milei-bridge-grid{grid-template-columns:repeat(2,minmax(0,1fr))}
}
@media(max-width:760px){
  #tab-milei-cost .milei-shock-bridge{padding:16px 14px}
  #tab-milei-cost .milei-shock-bridge h2{font-size:20px}
}
@media(max-width:440px){
  #tab-milei-cost .milei-bridge-grid{grid-template-columns:1fr}
  #tab-milei-cost .milei-shock-formula{text-align:left;font-size:11px}
}
</style>


<style id=\"rates-accum-v118\">"""
    html = replace_once(html, css_anchor, css_replacement)

    html = replace_once(
        html,
        """    <div id=\"mileiCostHero\" class=\"milei-cost-hero\"></div>

    <div class=\"milei-cost-grid\" id=\"mileiCostCards\"></div>""",
        """    <div id=\"mileiCostHero\" class=\"milei-cost-hero\"></div>

    <section id=\"mileiShockBridge\" class=\"milei-shock-bridge\"></section>

    <div class=\"milei-cost-grid\" id=\"mileiCostCards\"></div>""",
    )

    html = replace_once(
        html,
        """  const hero=document.getElementById('mileiCostHero');
  const cards=document.getElementById('mileiCostCards');""",
        """  const hero=document.getElementById('mileiCostHero');
  const bridge=document.getElementById('mileiShockBridge');
  const cards=document.getElementById('mileiCostCards');""",
    )
    html = replace_once(
        html,
        "if(!hero||!cards||!formula||!attribution||!scale)return;",
        "if(!hero||!bridge||!cards||!formula||!attribution||!scale)return;",
    )

    old_calculations = """  const massJun26=loss.baseMonthlyMass*powerAggregateLossParams.cpiJun2026VsNov2023;
  const broad=p.taxPrivilegesAnnual+p.sideExtraCredit+p.penCatchupAnnualized+p.senateNetAnnualFloor+meliArs;

  hero.innerHTML=`"""
    new_calculations = """  const massJun26=loss.baseMonthlyMass*powerAggregateLossParams.cpiJun2026VsNov2023;
  const broad=p.taxPrivilegesAnnual+p.sideExtraCredit+p.penCatchupAnnualized+p.senateNetAnnualFloor+meliArs;
  const grossShock=loss.grossCurrent;
  const salaryRecovered=loss.recoveredCurrent;
  const salaryRemaining=loss.netCurrent;
  const finalRemaining=Math.max(0,salaryRemaining-broad);
  const salaryRecoveredPct=mileiCostPct(salaryRecovered,grossShock);
  const editorialPct=mileiCostPct(broad,grossShock);
  const finalRemainingPct=mileiCostPct(finalRemaining,grossShock);
  const latestRealLevel=powerTotalAllOfficial.yNov.at(-1);
  const monthlyBaseSurplus=Math.max(0,latestRealLevel/100-1);
  const monthsAtJuneLevel=monthlyBaseSurplus>0?lostMonths/monthlyBaseSurplus:null;

  hero.innerHTML=`"""
    html = replace_once(html, old_calculations, new_calculations)

    hero_end = """      <div class=\"milei-cost-kpi\"><div class=\"tag\">Promedio del período</div><div class=\"val\">≈ $ ${Math.round(perMonth).toLocaleString('es-AR')}/mes</div><div class=\"mini\">${months} meses; sólo sirve para volver intuitivo el acumulado.</div></div>
    </div>`;

  const card=(cls,pill,title,money,body,scaleText,tab,id)=>`<article class=\"milei-cost-card ${cls}\">"""
    bridge_render = """      <div class=\"milei-cost-kpi\"><div class=\"tag\">Promedio del período</div><div class=\"val\">≈ $ ${Math.round(perMonth).toLocaleString('es-AR')}/mes</div><div class=\"mini\">${months} meses; sólo sirve para volver intuitivo el acumulado.</div></div>
    </div>`;

  bridge.innerHTML=`
    <div class=\"eyebrow\">Puente de amortización · valores homogéneos a jun-2026</div>
    <h2>¿Cuánto falta para absorber por completo el shock salarial?</h2>
    <p class=\"lead\">La recuperación de los salarios ya cerró una parte del agujero bruto. Debajo superponemos, como segunda capa, la envolvente de recursos y beneficios que el dashboard ya auditó para mostrar el remanente final de manera directa.</p>
    <div class=\"milei-bridge-grid\">
      <div class=\"milei-bridge-card\"><div class=\"tag\">Agujero bruto generado</div><div class=\"val\">${powerMoneyBillions(grossShock)}</div></div>
      <div class=\"milei-bridge-card recovered\"><div class=\"tag\">Recuperado por salarios</div><div class=\"val\">− ${powerMoneyBillions(salaryRecovered)}</div></div>
      <div class=\"milei-bridge-card editorial\"><div class=\"tag\">Envolvente ya auditada</div><div class=\"val\">− ${powerMoneyBillions(broad)}</div></div>
      <div class=\"milei-bridge-card remaining\"><div class=\"tag\">Todavía falta amortiguar</div><div class=\"val\">${powerMoneyBillions(finalRemaining)}</div></div>
    </div>
    <div class=\"milei-shock-track\" aria-label=\"Progreso para amortiguar el shock\">
      <span class=\"salary\" style=\"width:${salaryRecoveredPct}%\"></span>
      <span class=\"editorial\" style=\"width:${editorialPct}%\"></span>
      <span class=\"remaining\" style=\"width:${finalRemainingPct}%\"></span>
    </div>
    <div class=\"milei-shock-legend\">
      <span><i style=\"background:#69b498\"></i>Recuperación salarial: ${salaryRecoveredPct.toLocaleString('es-AR',{minimumFractionDigits:1,maximumFractionDigits:1})}%</span>
      <span><i style=\"background:#dba348\"></i>Envolvente auditada: ${editorialPct.toLocaleString('es-AR',{minimumFractionDigits:1,maximumFractionDigits:1})}%</span>
      <span><i style=\"background:#c45579\"></i>Remanente: ${finalRemainingPct.toLocaleString('es-AR',{minimumFractionDigits:1,maximumFractionDigits:1})}%</span>
    </div>
    <div class=\"milei-shock-formula\">${powerMoneyBillions(grossShock)} − ${powerMoneyBillions(salaryRecovered)} − ${powerMoneyBillions(broad)} = <strong>${powerMoneyBillions(finalRemaining)}</strong> todavía por amortiguar</div>
    <div class=\"milei-shock-scenario\"><b>Trayectoria salarial sola:</b> después de la recuperación observada queda una brecha de <b>${powerMoneyBillions(salaryRemaining)}</b>, equivalente a <b>${lostMonths.toLocaleString('es-AR',{minimumFractionDigits:2,maximumFractionDigits:2})} sueldos-base</b>. Si el nivel real de junio (${latestRealLevel.toLocaleString('es-AR',{minimumFractionDigits:2,maximumFractionDigits:2})}) se sostuviera, ese saldo se absorbería en aproximadamente <b>${monthsAtJuneLevel?.toLocaleString('es-AR',{minimumFractionDigits:1,maximumFractionDigits:1})} meses</b>.</div>`;

  const card=(cls,pill,title,money,body,scaleText,tab,id)=>`<article class=\"milei-cost-card ${cls}\">"""
    html = replace_once(html, hero_end, bridge_render)

    html = replace_once(
        html,
        """    `<div class=\"milei-cost-disclaimer\"><b>Envolvente editorial:</b> si se colocan uno al lado del otro los conceptos ARS ya auditados, dan aproximadamente <b>${powerMoneyBillions(broad)}</b>, ≈ ${(broad/loss.netCurrent*100).toLocaleString('es-AR',{maximumFractionDigits:1})}% de la brecha salarial. <b>No lo llamamos “plata recuperable total”</b> porque suma unidades temporales y naturalezas distintas; sólo sirve como referencia de escala.</div>`;""",
        """    `<div class=\"milei-cost-disclaimer\"><b>Envolvente editorial:</b> los conceptos ARS ya auditados dan aproximadamente <b>${powerMoneyBillions(broad)}</b>, ≈ ${(broad/loss.netCurrent*100).toLocaleString('es-AR',{maximumFractionDigits:1})}% de la brecha salarial neta. Superpuestos como ejercicio de escala, el monto que todavía faltaría amortiguar es <b>${powerMoneyBillions(finalRemaining)}</b>.</div>`;""",
    )

    OUTPUT_HTML.write_text(html, encoding="utf-8", newline="\n")
    ROOT_OUTPUT_HTML.write_text(html, encoding="utf-8", newline="\n")
    print(f"Generado: {OUTPUT_HTML}")
    print(f"Generado: {ROOT_OUTPUT_HTML}")


if __name__ == "__main__":
    main()
