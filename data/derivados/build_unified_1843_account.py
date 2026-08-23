#!/usr/bin/env python3
"""Unifica el tab Milei alrededor del agujero bruto de $18,43 billones."""

from __future__ import annotations

from pathlib import Path


DATA_DIR = Path(__file__).resolve().parents[1]
ROOT_DIR = DATA_DIR.parent
INPUT_NAME = "dashboard_kawaii_126_lectura_simple_brecha_bancaria.html"
OUTPUT_NAME = "dashboard_kawaii_127_cuenta_unificada_18_43.html"
INPUT_HTML = DATA_DIR / INPUT_NAME
OUTPUT_HTML = DATA_DIR / OUTPUT_NAME
ROOT_OUTPUT_HTML = ROOT_DIR / OUTPUT_NAME


def replace_once(text: str, old: str, new: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"Se esperaba 1 coincidencia y hubo {count}: {old[:160]!r}")
    return text.replace(old, new, 1)


def main() -> None:
    html = INPUT_HTML.read_text(encoding="utf-8")

    # El puente pasa de cuatro a cinco etapas e incorpora la pinza como alivio potencial.
    html = replace_once(
        html,
        "display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:10px;margin-top:15px",
        "display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:10px;margin-top:15px",
    )
    html = replace_once(
        html,
        """#tab-milei-cost .milei-bridge-card.recovered .val{color:#43866b}
#tab-milei-cost .milei-bridge-card.editorial .val{color:#a9782d}""",
        """#tab-milei-cost .milei-bridge-card.recovered .val{color:#43866b}
#tab-milei-cost .milei-bridge-card.financial{border-color:#cfd4f0;background:#f8f9ff}
#tab-milei-cost .milei-bridge-card.financial .val{color:#5962ad}
#tab-milei-cost .milei-bridge-card.editorial .val{color:#a9782d}""",
    )
    html = replace_once(
        html,
        """#tab-milei-cost .milei-shock-track .salary{background:linear-gradient(90deg,#63b294,#83c7ae)}
#tab-milei-cost .milei-shock-track .editorial{background:linear-gradient(90deg,#e6bb61,#d89946)}""",
        """#tab-milei-cost .milei-shock-track .salary{background:linear-gradient(90deg,#63b294,#83c7ae)}
#tab-milei-cost .milei-shock-track .financial{background:linear-gradient(90deg,#7f8bd4,#5962ad)}
#tab-milei-cost .milei-shock-track .editorial{background:linear-gradient(90deg,#e6bb61,#d89946)}""",
    )
    html = replace_once(
        html,
        """#tab-milei-cost .milei-shock-formula strong{color:#ad4269;font-size:17px}
#tab-milei-cost .milei-shock-scenario{""",
        """#tab-milei-cost .milei-shock-formula strong{color:#ad4269;font-size:17px}
#tab-milei-cost .milei-unified-components{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:8px;margin-top:10px}
#tab-milei-cost .milei-unified-components>div{min-width:0;padding:10px 11px;border:1px solid #eadfc8;border-radius:13px;background:#fffdf7;box-sizing:border-box}
#tab-milei-cost .milei-unified-components span{display:block;font-size:8px;font-weight:950;text-transform:uppercase;letter-spacing:.025em;color:#8d765a}
#tab-milei-cost .milei-unified-components b{display:block;margin-top:5px;font-size:14px;color:#a9782d;overflow-wrap:anywhere}
#tab-milei-cost .milei-shock-scenario{""",
    )
    html = replace_once(
        html,
        """@media(max-width:980px){
  #tab-milei-cost .milei-bridge-grid{grid-template-columns:repeat(2,minmax(0,1fr))}
}
@media(max-width:760px){
  #tab-milei-cost .milei-shock-bridge{padding:16px 14px}""",
        """@media(max-width:1200px){
  #tab-milei-cost .milei-bridge-grid,#tab-milei-cost .milei-unified-components{grid-template-columns:repeat(3,minmax(0,1fr))}
}
@media(max-width:760px){
  #tab-milei-cost .milei-bridge-grid,#tab-milei-cost .milei-unified-components{grid-template-columns:repeat(2,minmax(0,1fr))}
  #tab-milei-cost .milei-shock-bridge{padding:16px 14px}""",
    )
    html = replace_once(
        html,
        """@media(max-width:440px){
  #tab-milei-cost .milei-bridge-grid{grid-template-columns:1fr}""",
        """@media(max-width:440px){
  #tab-milei-cost .milei-bridge-grid,#tab-milei-cost .milei-unified-components{grid-template-columns:1fr}""",
    )

    html = replace_once(
        html,
        "<h3>Pinza financiera · cálculo en auditoría</h3>",
        "<h3>Pinza financiera · cuánto descontaría si se soluciona</h3>",
    )
    html = replace_once(
        html,
        "<h3>Cómo sale el número grande · sin magia y sin doble IPC</h3>",
        "<h3>Cómo se arma la cuenta madre de $18,43 billones</h3>",
    )
    html = replace_once(
        html,
        "<h3>Qué se puede atribuir a Milei —y qué sería tramposo atribuirle</h3>",
        "<h3>Cómo entra cada componente en la cuenta madre</h3>",
    )
    html = replace_once(
        html,
        """      <h3>Escala relativa frente a la brecha salarial</h3>
      <div class="family-mini-note" style="padding-top:0">
        Estas barras sirven sólo para dimensionar. <b>No constituyen una suma fiscal homogénea:</b> mezclan un stock contrafactual acumulado con flujos anuales, beneficios tributarios y créditos presupuestarios.
      </div>""",
        """      <h3>Todo medido contra el agujero bruto de $18,43 billones</h3>
      <div class="family-mini-note" style="padding-top:0">
        Todas las barras usan la misma cuenta madre como denominador. Así se ve de inmediato cuánto representa cada recuperación, solución o partida dentro del agujero bruto generado.
      </div>""",
    )

    html = replace_once(
        html,
        """  const broad=p.taxPrivilegesAnnual+p.sideExtraCredit+p.penCatchupAnnualized+p.senateNetAnnualFloor+meliArs;
  const grossShock=loss.grossCurrent;
  const salaryRecovered=loss.recoveredCurrent;
  const salaryRemaining=loss.netCurrent;
  const finalRemaining=Math.max(0,salaryRemaining-broad);
  const salaryRecoveredPct=mileiCostPct(salaryRecovered,grossShock);
  const editorialPct=mileiCostPct(broad,grossShock);
  const finalRemainingPct=mileiCostPct(finalRemaining,grossShock);""",
        """  const broad=p.taxPrivilegesAnnual+p.sideExtraCredit+p.penCatchupAnnualized+p.senateNetAnnualFloor+meliArs;
  const grossShock=loss.grossCurrent;
  const salaryRecovered=loss.recoveredCurrent;
  const salaryRemaining=loss.netCurrent;
  const financialRelief=Math.max(0,ratesMoneySummary.post.pinza_neta_hogar);
  const fintechExposure=Math.max(0,ratesMoneySummary.fintech.exposicion_constante);
  const remainingAfterPinza=Math.max(0,salaryRemaining-financialRelief);
  const finalRemaining=Math.max(0,remainingAfterPinza-broad);
  const salaryRecoveredPct=mileiCostPct(salaryRecovered,grossShock);
  const financialReliefPct=mileiCostPct(financialRelief,grossShock);
  const editorialPct=mileiCostPct(broad,grossShock);
  const finalRemainingPct=mileiCostPct(finalRemaining,grossShock);""",
    )

    old_hero = """  hero.innerHTML=`
    <div class="milei-cost-eyebrow">Resultado central · asalariados urbanos · dic-2023 → ${powerAccumShortDate(loss.latestDate)}</div>
    <div class="milei-cost-title">Lo que te “robó” Milei, si definimos “robar” como pérdida acumulada de poder adquisitivo frente a mantener nov-2023</div>
    <div class="milei-cost-amount">${powerMoneyBillions(loss.netCurrent)}</div>
    <div class="milei-cost-sub">
      No es una transferencia literal al Estado. Es la <b>brecha salarial real neta acumulada</b> del Total índice de salarios, escalada a ${(loss.salaried/1e6).toLocaleString('es-AR',{maximumFractionDigits:1})} M de asalariados urbanos y expresada en pesos de jun-2026.
      La magnitud equivale a <b>${lostMonths.toLocaleString('es-AR',{minimumFractionDigits:2,maximumFractionDigits:2})} meses de la masa salarial-base</b>: menos de un mes completo de salarios distribuido como pérdida a lo largo de ${months} meses.
    </div>
    <div class="milei-cost-kpis">
      <div class="milei-cost-kpi"><div class="tag">Agujero bruto</div><div class="val">${powerMoneyBillions(loss.grossCurrent)}</div><div class="mini">Sólo meses por debajo de la base.</div></div>
      <div class="milei-cost-kpi"><div class="tag">Recuperado después</div><div class="val">${powerMoneyBillions(loss.recoveredCurrent)}</div><div class="mini">Meses posteriores arriba de 100.</div></div>
      <div class="milei-cost-kpi"><div class="tag">Equiv. por asalariado</div><div class="val">$ ${Math.round(loss.perWorkerCurrent).toLocaleString('es-AR')}</div><div class="mini">Acumulado a pesos de jun-2026.</div></div>
      <div class="milei-cost-kpi"><div class="tag">Promedio del período</div><div class="val">≈ $ ${Math.round(perMonth).toLocaleString('es-AR')}/mes</div><div class="mini">${months} meses; sólo sirve para volver intuitivo el acumulado.</div></div>
    </div>`;"""
    new_hero = """  hero.innerHTML=`
    <div class="milei-cost-eyebrow">Cuenta unificada · asalariados urbanos · dic-2023 → ${powerAccumShortDate(loss.latestDate)}</div>
    <div class="milei-cost-title">Agujero bruto generado: la cuenta madre desde la que descontamos cada recuperación o solución</div>
    <div class="milei-cost-amount">${powerMoneyBillions(grossShock)}</div>
    <div class="milei-cost-sub">
      Este es el total de las caídas salariales mensuales antes de restar la recuperación posterior. Desde acá descontamos siempre contra la misma base: recuperación salarial observada, pinza financiera si se corrigiera y envolvente de recursos ya auditada.
    </div>
    <div class="milei-cost-kpis">
      <div class="milei-cost-kpi"><div class="tag">Recuperado por salarios</div><div class="val">− ${powerMoneyBillions(salaryRecovered)}</div><div class="mini">Recuperación ya observada.</div></div>
      <div class="milei-cost-kpi"><div class="tag">Saldo salarial</div><div class="val">${powerMoneyBillions(salaryRemaining)}</div><div class="mini">Lo que queda después de la recuperación.</div></div>
      <div class="milei-cost-kpi"><div class="tag">Pinza si se soluciona</div><div class="val">− ${powerMoneyBillions(financialRelief)}</div><div class="mini">Alivio potencial sobre la cuenta madre.</div></div>
      <div class="milei-cost-kpi"><div class="tag">Envolvente auditada</div><div class="val">− ${powerMoneyBillions(broad)}</div><div class="mini">Partidas y beneficios ya relevados.</div></div>
    </div>`;"""
    html = replace_once(html, old_hero, new_hero)

    old_bridge = """  bridge.innerHTML=`
    <div class="eyebrow">Puente de amortización · valores homogéneos a jun-2026</div>
    <h2>¿Cuánto falta para absorber por completo el shock salarial?</h2>
    <p class="lead">La recuperación de los salarios ya cerró una parte del agujero bruto. Debajo superponemos, como segunda capa, la envolvente de recursos y beneficios que el dashboard ya auditó para mostrar el remanente final de manera directa.</p>
    <div class="milei-bridge-grid">
      <div class="milei-bridge-card"><div class="tag">Agujero bruto generado</div><div class="val">${powerMoneyBillions(grossShock)}</div></div>
      <div class="milei-bridge-card recovered"><div class="tag">Recuperado por salarios</div><div class="val">− ${powerMoneyBillions(salaryRecovered)}</div></div>
      <div class="milei-bridge-card editorial"><div class="tag">Envolvente ya auditada</div><div class="val">− ${powerMoneyBillions(broad)}</div></div>
      <div class="milei-bridge-card remaining"><div class="tag">Todavía falta amortiguar</div><div class="val">${powerMoneyBillions(finalRemaining)}</div></div>
    </div>
    <div class="milei-shock-track" aria-label="Progreso para amortiguar el shock">
      <span class="salary" style="width:${salaryRecoveredPct}%"></span>
      <span class="editorial" style="width:${editorialPct}%"></span>
      <span class="remaining" style="width:${finalRemainingPct}%"></span>
    </div>
    <div class="milei-shock-legend">
      <span><i style="background:#69b498"></i>Recuperación salarial: ${salaryRecoveredPct.toLocaleString('es-AR',{minimumFractionDigits:1,maximumFractionDigits:1})}%</span>
      <span><i style="background:#dba348"></i>Envolvente auditada: ${editorialPct.toLocaleString('es-AR',{minimumFractionDigits:1,maximumFractionDigits:1})}%</span>
      <span><i style="background:#c45579"></i>Remanente: ${finalRemainingPct.toLocaleString('es-AR',{minimumFractionDigits:1,maximumFractionDigits:1})}%</span>
    </div>
    <div class="milei-shock-formula">${powerMoneyBillions(grossShock)} − ${powerMoneyBillions(salaryRecovered)} − ${powerMoneyBillions(broad)} = <strong>${powerMoneyBillions(finalRemaining)}</strong> todavía por amortiguar</div>
    <div class="milei-shock-scenario"><b>Trayectoria salarial sola:</b> después de la recuperación observada queda una brecha de <b>${powerMoneyBillions(salaryRemaining)}</b>, equivalente a <b>${lostMonths.toLocaleString('es-AR',{minimumFractionDigits:2,maximumFractionDigits:2})} sueldos-base</b>. Si el nivel real de junio (${latestRealLevel.toLocaleString('es-AR',{minimumFractionDigits:2,maximumFractionDigits:2})}) se sostuviera, ese saldo se absorbería en aproximadamente <b>${monthsAtJuneLevel?.toLocaleString('es-AR',{minimumFractionDigits:1,maximumFractionDigits:1})} meses</b>.</div>`;"""
    new_bridge = """  bridge.innerHTML=`
    <div class="eyebrow">Cuenta unificada · todo parte de ${powerMoneyBillions(grossShock)}</div>
    <h2>¿Cuánto quedaría si, además de recuperarse los salarios, se solucionara la pinza financiera?</h2>
    <p class="lead">La pinza entra como descuento potencial: no agrega otro daño al total. Preguntamos cuánto aliviaría la cuenta madre si el costo de préstamos y el menor rendimiento del ahorro se corrigieran por completo.</p>
    <div class="milei-bridge-grid">
      <div class="milei-bridge-card"><div class="tag">1 · Agujero bruto</div><div class="val">${powerMoneyBillions(grossShock)}</div></div>
      <div class="milei-bridge-card recovered"><div class="tag">2 · Recuperado por salarios</div><div class="val">− ${powerMoneyBillions(salaryRecovered)}</div></div>
      <div class="milei-bridge-card financial"><div class="tag">3 · Pinza solucionada</div><div class="val">− ${powerMoneyBillions(financialRelief)}</div></div>
      <div class="milei-bridge-card editorial"><div class="tag">4 · Envolvente auditada</div><div class="val">− ${powerMoneyBillions(broad)}</div></div>
      <div class="milei-bridge-card remaining"><div class="tag">5 · Todavía falta</div><div class="val">${powerMoneyBillions(finalRemaining)}</div></div>
    </div>
    <div class="milei-shock-track" aria-label="Cuenta unificada para amortiguar el shock">
      <span class="salary" style="width:${salaryRecoveredPct}%"></span>
      <span class="financial" style="width:${financialReliefPct}%"></span>
      <span class="editorial" style="width:${editorialPct}%"></span>
      <span class="remaining" style="width:${finalRemainingPct}%"></span>
    </div>
    <div class="milei-shock-legend">
      <span><i style="background:#69b498"></i>Recuperación salarial: ${salaryRecoveredPct.toLocaleString('es-AR',{minimumFractionDigits:1,maximumFractionDigits:1})}%</span>
      <span><i style="background:#6670bb"></i>Pinza si se soluciona: ${financialReliefPct.toLocaleString('es-AR',{minimumFractionDigits:1,maximumFractionDigits:1})}%</span>
      <span><i style="background:#dba348"></i>Envolvente auditada: ${editorialPct.toLocaleString('es-AR',{minimumFractionDigits:1,maximumFractionDigits:1})}%</span>
      <span><i style="background:#c45579"></i>Remanente: ${finalRemainingPct.toLocaleString('es-AR',{minimumFractionDigits:1,maximumFractionDigits:1})}%</span>
    </div>
    <div class="milei-shock-formula">${powerMoneyBillions(grossShock)} − ${powerMoneyBillions(salaryRecovered)} − ${powerMoneyBillions(financialRelief)} − ${powerMoneyBillions(broad)} = <strong>${powerMoneyBillions(finalRemaining)}</strong> todavía por amortiguar</div>
    <div class="milei-unified-components" aria-label="Desglose de la envolvente auditada">
      <div><span>Privilegios fiscales</span><b>− ${powerMoneyBillions(p.taxPrivilegesAnnual)}</b></div>
      <div><span>Mercado Libre</span><b>− ${mileiCostMoney(meliArs)}</b></div>
      <div><span>SIDE</span><b>− ${mileiCostMoney(p.sideExtraCredit)}</b></div>
      <div><span>Cúpula PEN</span><b>− ${mileiCostMoney(p.penCatchupAnnualized)}</b></div>
      <div><span>Dietas del Senado</span><b>− ${mileiCostMoney(p.senateNetAnnualFloor)}</b></div>
    </div>
    <div class="milei-shock-scenario"><b>La pinza como solución:</b> después de la recuperación salarial quedaban <b>${powerMoneyBillions(salaryRemaining)}</b>. Corregir por completo la pinza banco/PF descontaría <b>${powerMoneyBillions(financialRelief)}</b> y llevaría el saldo a <b>${powerMoneyBillions(remainingAfterPinza)}</b>. La capa Fintech de <b>${mileiCostMoney(fintechExposure)}</b> queda visible dentro de la auditoría financiera y representa ≈ <b>${mileiCostPct(fintechExposure,grossShock).toLocaleString('es-AR',{minimumFractionDigits:2,maximumFractionDigits:2})}%</b> de la cuenta madre.</div>`;"""
    html = replace_once(html, old_bridge, new_bridge)

    html = replace_once(
        html,
        """    card('hot','Pérdida de ingresos','Brecha salarial real acumulada',powerMoneyBillions(loss.netCurrent),
      'Es el dato central. Resume la distancia mensual del Total índice de salarios contra sostener nov-2023=100. La recuperación posterior ya está restada: no estamos sumando sólo las caídas.',
      `Saldo neto = −${lostMonths.toLocaleString('es-AR',{minimumFractionDigits:2,maximumFractionDigits:2})} meses-base · ${powerAccumShortDate(loss.latestDate)}.`, 'tab-power','powerAggregateLossBox')+""",
        """    card('hot','Pérdida de ingresos','Saldo salarial después de la recuperación',powerMoneyBillions(loss.netCurrent),
      'Es el saldo intermedio de la cuenta madre: al agujero bruto se le resta la recuperación salarial ya observada.',
      `Representa ≈ ${mileiCostPct(loss.netCurrent,grossShock).toLocaleString('es-AR',{maximumFractionDigits:1})}% de los ${powerMoneyBillions(grossShock)} iniciales.`, 'tab-power','powerAggregateLossBox')+""",
    )
    html = replace_once(
        html,
        "`Escala ≈ ${mileiCostPct(p.taxPrivilegesAnnual,loss.netCurrent).toLocaleString('es-AR',{maximumFractionDigits:1})}% de la brecha salarial. No implica que eliminarlos recupere peso por peso esa brecha.`",
        "`Si se corrigieran o reasignaran, descontarían ${powerMoneyBillions(p.taxPrivilegesAnnual)}: ≈ ${mileiCostPct(p.taxPrivilegesAnnual,grossShock).toLocaleString('es-AR',{maximumFractionDigits:1})}% de la cuenta madre.`",
    )
    html = replace_once(
        html,
        "`Escala ≈ ${mileiCostPct(p.sideExtraCredit,loss.netCurrent).toLocaleString('es-AR',{maximumFractionDigits:2})}% de la brecha.`",
        "`Si ese refuerzo se reasignara, descontaría ${mileiCostMoney(p.sideExtraCredit)}: ≈ ${mileiCostPct(p.sideExtraCredit,grossShock).toLocaleString('es-AR',{maximumFractionDigits:2})}% de la cuenta madre.`",
    )
    html = replace_once(
        html,
        "`Equivalente nominal por período: ${mileiCostMoney(meli.nominalBn*1e9)} · homogéneo jun-26: ${mileiCostMoney(meliArs)}.`",
        "`Si se reorientara, descontaría ${mileiCostMoney(meliArs)}: ≈ ${mileiCostPct(meliArs,grossShock).toLocaleString('es-AR',{maximumFractionDigits:2})}% de la cuenta madre.`",
    )
    html = replace_once(
        html,
        "`El salto inmediato estimado fue ≈ +126% real. El monto anual es un piso neto, no costo fiscal bruto.`",
        "`Si se corrigiera ese piso anual, descontaría ${mileiCostMoney(p.senateNetAnnualFloor)}: ≈ ${mileiCostPct(p.senateNetAnnualFloor,grossShock).toLocaleString('es-AR',{maximumFractionDigits:2})}% de la cuenta madre.`",
    )
    html = replace_once(
        html,
        "'Lo mostramos justamente para que el tab no seleccione sólo cifras que empujan una narrativa.', 'tab-casta','castaInflationChart');",
        "`Si se revirtiera sólo el extra nominal anualizado, descontaría ${mileiCostMoney(p.penCatchupAnnualized)}: ≈ ${mileiCostPct(p.penCatchupAnnualized,grossShock).toLocaleString('es-AR',{maximumFractionDigits:2})}% de la cuenta madre.`, 'tab-casta','castaInflationChart');",
    )

    old_formula = """  formula.innerHTML=`
    <div><div class="step">1 · Brecha mensual</div><div class="formula">Cada mes: (índice real / 100) − 1. Negativo = pérdida; positivo = recuperación.</div></div>
    <div><div class="step">2 · Saldo acumulado</div><div class="formula">Σ dic-2023→${powerAccumShortDate(loss.latestDate)} = <b>−${lostMonths.toLocaleString('es-AR',{minimumFractionDigits:4,maximumFractionDigits:4})} meses-base</b>.</div></div>
    <div><div class="step">3 · Masa salarial base</div><div class="formula">$ ${Math.round(loss.wageBaseNov).toLocaleString('es-AR')} × ${(loss.salaried/1e6).toLocaleString('es-AR',{maximumFractionDigits:1})} M = <b>${powerMoneyBillions(loss.baseMonthlyMass)}</b> de nov-2023 por mes.</div></div>
    <div><div class="step">4 · Pesos comparables</div><div class="formula">${lostMonths.toLocaleString('es-AR',{minimumFractionDigits:4,maximumFractionDigits:4})} × ${powerMoneyBillions(loss.baseMonthlyMass)} × ${powerAggregateLossParams.cpiJun2026VsNov2023.toLocaleString('es-AR',{minimumFractionDigits:5,maximumFractionDigits:5})} = <b>${powerMoneyBillions(loss.netCurrent)}</b>.</div></div>`;"""
    new_formula = """  formula.innerHTML=`
    <div><div class="step">1 · Sólo las caídas</div><div class="formula">Σ meses debajo de nov-2023=100 = <b>−${gap.grossLoss.toLocaleString('es-AR',{minimumFractionDigits:4,maximumFractionDigits:4})} sueldos-base</b>.</div></div>
    <div><div class="step">2 · Cuenta madre</div><div class="formula">Caídas × masa salarial-base × IPC = <b>${powerMoneyBillions(grossShock)}</b>.</div></div>
    <div><div class="step">3 · Recuperación observada</div><div class="formula">Los meses posteriores arriba de 100 recuperaron <b>${powerMoneyBillions(salaryRecovered)}</b>; saldo salarial: <b>${powerMoneyBillions(salaryRemaining)}</b>.</div></div>
    <div><div class="step">4 · Soluciones superpuestas</div><div class="formula">Pinza <b>−${powerMoneyBillions(financialRelief)}</b> + envolvente <b>−${powerMoneyBillions(broad)}</b> ⇒ remanente <b>${powerMoneyBillions(finalRemaining)}</b>.</div></div>`;"""
    html = replace_once(html, old_formula, new_formula)

    old_attribution = """  attribution.innerHTML=`<table class="milei-cost-table"><thead><tr><th>Dato</th><th>Qué demuestra</th><th>Atribución justa</th><th>Qué NO demuestra</th><th>¿Se suma al “total”?</th></tr></thead><tbody>
    <tr><td>Brecha salarial ${powerMoneyBillions(loss.netCurrent)}</td><td>Pérdida acumulada frente al contrafactual nov-2023=100.</td><td class="attr-partial">Resultado macro del período Milei; políticas del gobierno son parte del contexto causal, pero la cifra sola no identifica causalidad peso por peso.</td><td>No demuestra transferencia al Estado ni que cada peso tenga una única causa presidencial.</td><td><b>Es el total central</b>, no una partida fiscal.</td></tr>
    <tr><td>Privilegios fiscales ${powerMoneyBillions(p.taxPrivilegesAnnual)}/año</td><td>Costo tributario estimado de un subconjunto prudente.</td><td class="attr-partial">Política fiscal vigente bajo Milei; algunos tratamientos son heredados.</td><td>No garantiza recaudación contrafactual uno-a-uno si se eliminan.</td><td>No: se compara escala; es flujo anual.</td></tr>
    <tr><td>Mercado Libre ${mileiCostMoney(meliArs)}</td><td>Beneficios documentados durante 2024–1T26 homogeneizados a jun-26.</td><td class="attr-partial">Ocurren durante Milei, pero el régimen antecede a su gobierno.</td><td>No es una transferencia personal a Galperín ni una política creada por Milei.</td><td>No: período y naturaleza distintos.</td></tr>
    <tr><td>SIDE +${mileiCostMoney(p.sideExtraCredit)}</td><td>Refuerzo de crédito presupuestario.</td><td class="attr-yes">Decisión presupuestaria del PEN.</td><td>Crédito no significa ejecución efectiva.</td><td>No: es crédito puntual.</td></tr>
    <tr><td>Senado ≥${mileiCostMoney(p.senateNetAnnualFloor)}/año</td><td>Piso del aumento de dietas.</td><td class="attr-no">Decisión del Senado, no del PEN.</td><td>No puede presentarse como “Milei se subió el sueldo”.</td><td>No: flujo anual y poder distinto.</td></tr>
    <tr><td>Min/Sec/Sub −31,4% real</td><td>La escala política comparable sigue perdiendo contra IPC.</td><td class="attr-yes">Escala del PEN durante Milei.</td><td>No sostiene la tesis de enriquecimiento real de esos cargos.</td><td>No; funciona como control negativo.</td></tr>
  </tbody></table>`;"""
    new_attribution = """  attribution.innerHTML=`<table class="milei-cost-table"><thead><tr><th>Componente</th><th>Monto visible</th><th>Cómo entra en los ${powerMoneyBillions(grossShock)}</th><th>Saldo después de aplicarlo</th></tr></thead><tbody>
    <tr><td>Agujero salarial bruto</td><td><b>${powerMoneyBillions(grossShock)}</b></td><td class="attr-partial">Es la cuenta madre: 100% del punto de partida.</td><td>${powerMoneyBillions(grossShock)}</td></tr>
    <tr><td>Recuperación salarial observada</td><td>−${powerMoneyBillions(salaryRecovered)}</td><td class="attr-yes">Se descuenta porque la mejora ya ocurrió.</td><td><b>${powerMoneyBillions(salaryRemaining)}</b></td></tr>
    <tr><td>Pinza banco/PF si se soluciona</td><td>−${powerMoneyBillions(financialRelief)}</td><td class="attr-yes">Se descuenta como alivio potencial del problema financiero.</td><td><b>${powerMoneyBillions(remainingAfterPinza)}</b></td></tr>
    <tr><td>Envolvente auditada</td><td>−${powerMoneyBillions(broad)}</td><td class="attr-partial">Superpone privilegios fiscales, Mercado Libre, SIDE, PEN y Senado como capacidad potencial.</td><td><b>${powerMoneyBillions(finalRemaining)}</b></td></tr>
    <tr><td>Fintech · exposición visible</td><td>${mileiCostMoney(fintechExposure)}</td><td class="attr-partial">Queda dentro de la misma escala financiera para mostrar su tamaño frente a la cuenta madre.</td><td>${mileiCostPct(fintechExposure,grossShock).toLocaleString('es-AR',{minimumFractionDigits:2,maximumFractionDigits:2})}% del total</td></tr>
    <tr><td>Autoridades superiores del PEN</td><td>−31,4% real</td><td class="attr-no">Funciona como control del relato; no agrega un monto ARS a la cuenta.</td><td>Sin modificación monetaria</td></tr>
  </tbody></table>`;"""
    html = replace_once(html, old_attribution, new_attribution)

    old_scale = """  const scaleRows=[
    ['Privilegios fiscales · anual',p.taxPrivilegesAnnual],
    ['Mercado Libre · 2024–1T26 a jun-26',meliArs],
    ['SIDE · crédito adicional 2026',p.sideExtraCredit],
    ['Cúspide PEN · anualización nominal',p.penCatchupAnnualized],
    ['Senado · piso anual neto',p.senateNetAnnualFloor]
  ];
  scale.innerHTML=scaleRows.map(([name,v])=>{const pct=mileiCostPct(v,loss.netCurrent);return `<div class="milei-scale-row"><div class="milei-scale-head"><span>${name}</span><b>${pct.toLocaleString('es-AR',{minimumFractionDigits:pct<1?2:1,maximumFractionDigits:pct<1?2:1})}%</b></div><div class="milei-scale-track"><div class="milei-scale-fill" style="width:${Math.min(100,pct)}%"></div></div></div>`}).join('')+
    `<div class="milei-cost-disclaimer"><b>Envolvente editorial:</b> los conceptos ARS ya auditados dan aproximadamente <b>${powerMoneyBillions(broad)}</b>, ≈ ${(broad/loss.netCurrent*100).toLocaleString('es-AR',{maximumFractionDigits:1})}% de la brecha salarial neta. Superpuestos como ejercicio de escala, el monto que todavía faltaría amortiguar es <b>${powerMoneyBillions(finalRemaining)}</b>.</div>`;"""
    new_scale = """  const scaleRows=[
    ['Recuperación salarial observada',salaryRecovered],
    ['Pinza banco/PF si se soluciona',financialRelief],
    ['Envolvente auditada total',broad],
    ['Privilegios fiscales · anual',p.taxPrivilegesAnnual],
    ['Mercado Libre · 2024–1T26 a jun-26',meliArs],
    ['SIDE · crédito adicional 2026',p.sideExtraCredit],
    ['Fintech · exposición visible',fintechExposure],
    ['Cúspide PEN · anualización nominal',p.penCatchupAnnualized],
    ['Senado · piso anual neto',p.senateNetAnnualFloor]
  ];
  scale.innerHTML=scaleRows.map(([name,v])=>{const pct=mileiCostPct(v,grossShock);return `<div class="milei-scale-row"><div class="milei-scale-head"><span>${name}</span><b>${pct.toLocaleString('es-AR',{minimumFractionDigits:pct<1?2:1,maximumFractionDigits:pct<1?2:1})}%</b></div><div class="milei-scale-track"><div class="milei-scale-fill" style="width:${Math.min(100,pct)}%"></div></div></div>`}).join('')+
    `<div class="milei-cost-disclaimer"><b>Cuenta unificada:</b> ${powerMoneyBillions(grossShock)} − ${powerMoneyBillions(salaryRecovered)} − ${powerMoneyBillions(financialRelief)} − ${powerMoneyBillions(broad)} = <b>${powerMoneyBillions(finalRemaining)}</b> todavía por amortiguar.</div>`;"""
    html = replace_once(html, old_scale, new_scale)

    # La tarjeta financiera repite, en lenguaje directo, cómo descuenta de la cuenta madre.
    html = replace_once(
        html,
        """    <p class="milei-financial-summary"><b>Efecto financiero visible:</b> ${ratesMoneyArs(p.pinza_neta_hogar)} acumulados en banco/PF + ${ratesMoneyArs(fintech.exposicion_constante)} de exposición Fintech para dimensionar el costo de la pinza financiera del período.</p>`;""",
        """    <p class="milei-financial-summary"><b>Cómo entra en la cuenta de $18,43 billones:</b> si la pinza banco/PF se solucionara por completo, descontaría <b>${ratesMoneyArs(p.pinza_neta_hogar)}</b>. Después de la recuperación salarial, el saldo bajaría de <b>${powerMoneyBillions(powerAggregateLossEstimate().netCurrent)}</b> a <b>${powerMoneyBillions(Math.max(0,powerAggregateLossEstimate().netCurrent-p.pinza_neta_hogar))}</b>. La exposición Fintech de ${ratesMoneyArs(fintech.exposicion_constante)} queda visible en la misma escala financiera.</p>`;""",
    )

    OUTPUT_HTML.write_text(html, encoding="utf-8", newline="\n")
    ROOT_OUTPUT_HTML.write_text(html, encoding="utf-8", newline="\n")
    print(f"Generado: {OUTPUT_HTML}")
    print(f"Generado: {ROOT_OUTPUT_HTML}")


if __name__ == "__main__":
    main()
