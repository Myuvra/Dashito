from pathlib import Path


SOURCE = Path(r"C:\Github\inflacion\data\dashboard_kawaii_129_fondo_patron_svg.html")
OUTPUT = Path(r"C:\Github\inflacion\data\dashboard_kawaii_130_devoluciones_y_signos_hogar.html")


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
<style id="household-signs-and-returns-v130">
/* v130 · signos desde el hogar + escenario explícito de devolución/compensación */
.household-sign-key{
  margin:0 0 14px;padding:15px 17px;border:2px solid #cfc0e7;border-radius:19px;
  background:linear-gradient(135deg,rgba(255,250,253,.97),rgba(246,255,250,.97));
  color:#65526d;box-sizing:border-box
}
.household-sign-key h2{margin:0 0 5px;color:#5c3d6c;font-size:18px;line-height:1.25}
.household-sign-key>p{margin:0 0 11px;font-size:11px;line-height:1.5}
.household-sign-key-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:9px}
.household-sign-key-grid>div{padding:11px 12px;border:1px solid #e5dbe9;border-radius:13px;background:#fff;font-size:10.5px;line-height:1.45;box-sizing:border-box}
.household-sign-key-grid b{display:block;margin-bottom:3px;font-size:12px}
.household-sign-key .positive b{color:#348165}.household-sign-key .negative b{color:#b0476d}.household-sign-key .delta b{color:#6043a6}
#ratesMoneySection .rates-money-kpi{position:relative;padding-top:42px}
#ratesMoneySection .rates-money-kpi.primary{padding-top:46px}
#ratesMoneySection .rates-money-kpi::before{position:absolute;top:12px;left:14px;padding:4px 8px;border-radius:999px;font-size:8px;font-weight:950;letter-spacing:.035em;text-transform:uppercase}
#ratesMoneySection .rates-money-kpi.favorable::before{content:"+$ · a favor del hogar";color:#267457;background:#ddf5e9;border:1px solid #a9d7c3}
#ratesMoneySection .rates-money-kpi.desfavorable::before{content:"−$ · en contra del hogar";color:#9f315c;background:#ffe3ed;border:1px solid #e7afc4}
#ratesMoneySection .rates-money-kpi.neutral::before{content:"$0 · neutro para el hogar";color:#6e6175;background:#f1edf3;border:1px solid #d8cedc}

#tab-milei-cost .milei-cost-kpi .val.household-relief,
#tab-milei-cost .milei-bridge-card .val.household-relief{color:#2f8264}
.milei-return-scenario{margin:18px 0;padding:22px;border:2px solid #a9d7c3;border-radius:24px;background:linear-gradient(135deg,rgba(247,255,251,.97),rgba(255,249,252,.97));box-shadow:0 12px 30px rgba(75,120,99,.11);box-sizing:border-box;color:#624f69}
.milei-return-eyebrow{display:inline-block;padding:5px 10px;border:1px solid #e6b8ca;border-radius:999px;background:#fff2f7;color:#9d4265;font-size:9px;font-weight:950;letter-spacing:.04em;text-transform:uppercase}
.milei-return-scenario h2{margin:10px 0 7px;font-size:25px;line-height:1.15;color:#583767}
.milei-return-scenario .lead{max-width:1060px;margin:0;font-size:12px;line-height:1.6}
.milei-return-sign-rule{display:flex;gap:10px;align-items:center;margin:13px 0;padding:11px 13px;border-left:5px solid #50a37f;border-radius:12px;background:#fff;color:#5c4b64;font-size:11px;line-height:1.5}
.milei-return-sign-rule .plus{flex:0 0 auto;font-size:22px;font-weight:950;color:#318064}
.milei-return-main{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:11px;margin-top:14px}
.milei-return-card{position:relative;min-width:0;padding:15px;border:1px solid #dfd4e4;border-radius:17px;background:#fff;box-sizing:border-box}
.milei-return-card:not(:last-child)::after{content:"→";position:absolute;right:-10px;top:50%;z-index:2;transform:translateY(-50%);display:grid;place-items:center;width:20px;height:20px;border-radius:50%;background:#755485;color:#fff;font-weight:950}
.milei-return-card.start{border-color:#e7c0d0;background:#fff8fb}.milei-return-card.bank{border-color:#bdd1fa;background:#f8faff}.milei-return-card.fintech{border-color:#e9b9cc;background:#fff7fb}.milei-return-card.end{border-color:#acd8c4;background:#f5fff9}
.milei-return-card .step{font-size:8.5px;font-weight:950;letter-spacing:.035em;text-transform:uppercase;color:#8a718f;line-height:1.35}
.milei-return-card h3{margin:6px 0 4px;font-size:15px;line-height:1.25;color:#5c4169}
.milei-return-card .return-amount{font-size:24px;line-height:1.05;font-weight:950;color:#2f8264}
.milei-return-card.start .return-amount,.milei-return-card.end .return-amount{color:#a14367}
.milei-return-card .breakdown{margin-top:6px;font-size:9.5px;line-height:1.45;color:#756579}
.milei-return-card .after{margin-top:9px;padding-top:8px;border-top:1px dashed #ded2e3;font-size:10px;line-height:1.4}
.milei-return-card .after b{color:#5c3b6d}
.milei-return-others-title{margin:18px 0 8px;font-size:13px;font-weight:950;color:#684674}
.milei-return-others{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:9px}
.milei-return-other{min-width:0;padding:12px;border:1px solid #ead5b0;border-radius:14px;background:#fffdf7;box-sizing:border-box}
.milei-return-other .actor{font-size:8.5px;font-weight:950;line-height:1.35;text-transform:uppercase;color:#826e52}
.milei-return-other .amount{margin:5px 0 3px;font-size:17px;font-weight:950;color:#2f8264}
.milei-return-other .action{font-size:9.5px;line-height:1.45;color:#70616f}
.milei-return-other .after{margin-top:6px;padding-top:6px;border-top:1px dashed #e3d6c1;font-size:9px;color:#6a5870}
.milei-return-total{display:grid;grid-template-columns:1fr auto;gap:14px;align-items:center;margin-top:14px;padding:14px 16px;border:2px solid #bdaadd;border-radius:16px;background:#fbf8ff}
.milei-return-total p{margin:0;font-size:11px;line-height:1.55}.milei-return-total .amount{font-size:28px;font-weight:950;color:#a14367;white-space:nowrap}
.milei-return-caveat{margin:10px 2px 0;font-size:9.5px;line-height:1.5;color:#7c6a80}
.household-plus{color:#2f8264;font-weight:950}.hole-minus{color:#a14367;font-weight:950}
@media(max-width:1100px){.milei-return-main{grid-template-columns:repeat(2,minmax(0,1fr))}.milei-return-card:nth-child(2)::after{display:none}.milei-return-others{grid-template-columns:repeat(3,minmax(0,1fr))}}
@media(max-width:720px){.household-sign-key-grid{grid-template-columns:1fr}.milei-return-scenario{padding:16px 14px}.milei-return-scenario h2{font-size:21px}.milei-return-others{grid-template-columns:repeat(2,minmax(0,1fr))}.milei-return-total{grid-template-columns:1fr}.milei-return-total .amount{font-size:24px}}
@media(max-width:480px){.milei-return-main,.milei-return-others{grid-template-columns:1fr}.milei-return-card::after{display:none!important}.milei-return-card .return-amount{font-size:22px}.milei-return-scenario{margin-left:0;margin-right:0}}
</style>
'''
html = replace_once(html, "</head>", css + "</head>", "CSS v130")

rates_key = r'''  <section id="tab-rates" class="tab-panel">
    <div class="household-sign-key" id="ratesHouseholdSignKey">
      <h2>Antes de mirar los números: todos los $ están puestos del lado del hogar</h2>
      <p>Esta regla vale para los montos monetarios del tab. Las tasas y los puntos porcentuales técnicos se explican aparte.</p>
      <div class="household-sign-key-grid">
        <div class="positive"><b>+$ = favorable para el hogar</b>Más ingreso, mejor rendimiento o una mejora frente al período comparable.</div>
        <div class="negative"><b>−$ = desfavorable para el hogar</b>Crédito más caro, menor rendimiento o una pérdida contra la norma histórica.</div>
        <div class="delta"><b>Diferencial: post-shock − espejo</b>Positivo significa que mejoró; negativo, que empeoró. Un saldo puede seguir bajo cero aunque haya mejorado.</div>
      </div>
    </div>
    <div class="grid">'''
html = replace_once(
    html,
    '  <section id="tab-rates" class="tab-panel">\n    <div class="grid">',
    rates_key,
    "leyenda de signos del hogar",
)

scenario_shell = '''    <section id="mileiShockBridge" class="milei-shock-bridge"></section>

    <section class="milei-return-scenario" id="mileiReturnScenario">
      <div id="mileiReturnScenarioContent"></div>
    </section>'''
html = replace_once(
    html,
    '    <section id="mileiShockBridge" class="milei-shock-bridge"></section>',
    scenario_shell,
    "contenedor del escenario de devoluciones",
)

html = replace_once(
    html,
    "  const bridge=document.getElementById('mileiShockBridge');\n  const cards=document.getElementById('mileiCostCards');",
    "  const bridge=document.getElementById('mileiShockBridge');\n  const returns=document.getElementById('mileiReturnScenarioContent');\n  const cards=document.getElementById('mileiCostCards');",
    "referencia JS del escenario",
)
html = replace_once(
    html,
    "  if(!hero||!bridge||!cards||!formula||!attribution||!scale)return;",
    "  if(!hero||!bridge||!returns||!cards||!formula||!attribution||!scale)return;",
    "guardia JS del escenario",
)

old_calcs = '''  const financialRelief=Math.max(0,-ratesMoneySummary.post.impacto_hogar_total_ampliado);
  const fintechExposure=Math.abs(ratesMoneySummary.diferencial.impacto_hogar_fintech);
  const remainingAfterPinza=Math.max(0,salaryRemaining-financialRelief);
  const finalRemaining=Math.max(0,remainingAfterPinza-broad);'''
new_calcs = '''  const bankCreditReturn=Math.max(0,-ratesMoneySummary.post.impacto_hogar_banco);
  const bankPfReturn=Math.max(0,-ratesMoneySummary.post.impacto_hogar_pf);
  const bankReturn=bankCreditReturn+bankPfReturn;
  const fintechReturn=Math.max(0,-ratesMoneySummary.post.impacto_hogar_fintech);
  const financialRelief=bankReturn+fintechReturn;
  const fintechWindowChange=Math.abs(ratesMoneySummary.diferencial.impacto_hogar_fintech);
  const remainingAfterBank=Math.max(0,salaryRemaining-bankReturn);
  const remainingAfterFintech=Math.max(0,remainingAfterBank-fintechReturn);
  const remainingAfterPinza=remainingAfterFintech;
  const remainingAfterTax=Math.max(0,remainingAfterFintech-p.taxPrivilegesAnnual);
  const remainingAfterMeli=Math.max(0,remainingAfterTax-meliArs);
  const remainingAfterSide=Math.max(0,remainingAfterMeli-p.sideExtraCredit);
  const remainingAfterPen=Math.max(0,remainingAfterSide-p.penCatchupAnnualized);
  const finalRemaining=Math.max(0,remainingAfterPen-p.senateNetAnnualFloor);'''
html = replace_once(html, old_calcs, new_calcs, "cálculos de devolución por actor")

# El signo visible en estas tarjetas ahora representa el efecto sobre el hogar.
replacements = [
    ('<div class="milei-cost-kpi"><div class="tag">Recuperado por salarios</div><div class="val">− ${powerMoneyBillions(salaryRecovered)}</div><div class="mini">Recuperación ya observada.</div></div>',
     '<div class="milei-cost-kpi"><div class="tag">Ya volvió por salarios</div><div class="val household-relief">+ ${powerMoneyBillions(salaryRecovered)}</div><div class="mini">A favor de los hogares · recuperación observada.</div></div>'),
    ('<div class="milei-cost-kpi"><div class="tag">Pinza si se soluciona</div><div class="val">− ${powerMoneyBillions(financialRelief)}</div><div class="mini">Alivio potencial sobre la cuenta madre.</div></div>',
     '<div class="milei-cost-kpi"><div class="tag">Si bancos + Fintech devolvieran / compensaran</div><div class="val household-relief">+ ${powerMoneyBillions(financialRelief)}</div><div class="mini">Volvería al hogar; por eso baja el agujero.</div></div>'),
    ('<div class="milei-cost-kpi"><div class="tag">Envolvente auditada</div><div class="val">− ${powerMoneyBillions(broad)}</div><div class="mini">Partidas y beneficios ya relevados.</div></div>',
     '<div class="milei-cost-kpi"><div class="tag">Si se recuperara la envolvente</div><div class="val household-relief">+ ${powerMoneyBillions(broad)}</div><div class="mini">Volvería o se reasignaría a favor del hogar.</div></div>'),
    ('<h2>¿Cuánto quedaría si, además de recuperarse los salarios, se solucionara la pinza financiera?</h2>',
     '<h2>¿Cuánto quedaría si bancos, Fintech y partidas auditadas devolvieran “lo robado” o compensaran estos montos?</h2>'),
    ('<p class="lead">La pinza entra como descuento potencial: no agrega otro daño al total. Preguntamos cuánto aliviaría la cuenta madre si el costo de préstamos y el menor rendimiento del ahorro se corrigieran por completo.</p>',
     '<p class="lead">Cada monto verde es positivo para el hogar. En la fórmula se resta del agujero porque representa dinero que volvería, una compensación o recursos que se reasignarían.</p>'),
    ('<div class="milei-bridge-card recovered"><div class="tag">2 · Recuperado por salarios</div><div class="val">− ${powerMoneyBillions(salaryRecovered)}</div></div>',
     '<div class="milei-bridge-card recovered"><div class="tag">2 · Volvió por salarios</div><div class="val household-relief">+ ${powerMoneyBillions(salaryRecovered)}</div></div>'),
    ('<div class="milei-bridge-card financial"><div class="tag">3 · Pinza solucionada</div><div class="val">− ${powerMoneyBillions(financialRelief)}</div></div>',
     '<div class="milei-bridge-card financial"><div class="tag">3 · Devolverían bancos + Fintech</div><div class="val household-relief">+ ${powerMoneyBillions(financialRelief)}</div></div>'),
    ('<div class="milei-bridge-card editorial"><div class="tag">4 · Envolvente auditada</div><div class="val">− ${powerMoneyBillions(broad)}</div></div>',
     '<div class="milei-bridge-card editorial"><div class="tag">4 · Volvería por otras partidas</div><div class="val household-relief">+ ${powerMoneyBillions(broad)}</div></div>'),
    ('<div><span>Privilegios fiscales</span><b>− ${powerMoneyBillions(p.taxPrivilegesAnnual)}</b></div>',
     '<div><span>Privilegios fiscales</span><b class="household-plus">+ ${powerMoneyBillions(p.taxPrivilegesAnnual)} al hogar</b></div>'),
    ('<div><span>Mercado Libre</span><b>− ${mileiCostMoney(meliArs)}</b></div>',
     '<div><span>Mercado Libre</span><b class="household-plus">+ ${mileiCostMoney(meliArs)} al hogar</b></div>'),
    ('<div><span>SIDE</span><b>− ${mileiCostMoney(p.sideExtraCredit)}</b></div>',
     '<div><span>SIDE</span><b class="household-plus">+ ${mileiCostMoney(p.sideExtraCredit)} al hogar</b></div>'),
    ('<div><span>Cúpula PEN</span><b>− ${mileiCostMoney(p.penCatchupAnnualized)}</b></div>',
     '<div><span>Cúpula PEN</span><b class="household-plus">+ ${mileiCostMoney(p.penCatchupAnnualized)} al hogar</b></div>'),
    ('<div><span>Dietas del Senado</span><b>− ${mileiCostMoney(p.senateNetAnnualFloor)}</b></div>',
     '<div><span>Dietas del Senado</span><b class="household-plus">+ ${mileiCostMoney(p.senateNetAnnualFloor)} al hogar</b></div>'),
]
for old, new in replacements:
    html = replace_once(html, old, new, "semántica visible de signos")

old_scenario_copy = '''    <div class="milei-shock-scenario"><b>La pinza como solución:</b> después de la recuperación salarial quedaban <b>${powerMoneyBillions(salaryRemaining)}</b>. Corregir por completo la pinza ampliada descontaría <b>${powerMoneyBillions(financialRelief)}</b> y llevaría el saldo a <b>${powerMoneyBillions(remainingAfterPinza)}</b>. La pata Fintech de <b>${mileiCostMoney(fintechExposure)}</b> ya está incluida en la pinza ampliada y representa ≈ <b>${mileiCostPct(fintechExposure,grossShock).toLocaleString('es-AR',{minimumFractionDigits:2,maximumFractionDigits:2})}%</b> de la cuenta madre.</div>`;'''
new_scenario_copy = '''    <div class="milei-shock-scenario"><b>Lectura corta:</b> después de la recuperación salarial quedaban <b>${powerMoneyBillions(salaryRemaining)}</b>. Si bancos y Fintech compensaran el saldo negativo pos-shock, volverían <b class="household-plus">+${powerMoneyBillions(financialRelief)} al hogar</b> y el agujero bajaría a <b>${powerMoneyBillions(remainingAfterPinza)}</b>. La cuenta incluye banco <b>${powerMoneyBillions(bankReturn)}</b> y Fintech <b>${powerMoneyBillions(fintechReturn)}</b>, sin doble conteo.</div>`;'''
html = replace_once(html, old_scenario_copy, new_scenario_copy, "lectura corta de devolución")

return_render = r'''
  returns.innerHTML=`
    <div class="milei-return-eyebrow">“Si devolvieran lo robado” · ejercicio contrafactual por actor</div>
    <h2>“Si devolvieran lo cobrado o reasignaran estos recursos”, ¿cuánto del agujero se amortiguaría?</h2>
    <p class="lead">Partimos del saldo salarial que todavía falta recuperar. Después aplicamos cada devolución o compensación una sola vez y mostramos, paso a paso, cuánto agujero queda.</p>
    <div class="milei-return-sign-rule"><span class="plus">+$</span><span><b>En este bloque, verde siempre significa dinero o alivio a favor del hogar.</b> La cuenta resta ese alivio del agujero: no es un “menos para la gente”, sino un “menos deuda por amortiguar”.</span></div>
    <div class="milei-return-main">
      <article class="milei-return-card start">
        <div class="step">Punto de partida</div><h3>Saldo después de la recuperación salarial</h3>
        <div class="return-amount">${powerMoneyBillions(salaryRemaining)}</div>
        <div class="breakdown">Este es el agujero que todavía queda; no es dinero a favor del hogar.</div>
      </article>
      <article class="milei-return-card bank">
        <div class="step">Si los bancos devolvieran “lo robado” / compensaran</div><h3>Crédito bancario + plazo fijo</h3>
        <div class="return-amount">+ ${powerMoneyBillions(bankReturn)}</div>
        <div class="breakdown">Crédito: ${powerMoneyBillions(bankCreditReturn)} · ahorro en PF: ${powerMoneyBillions(bankPfReturn)}.</div>
        <div class="after">El agujero bajaría a <b>${powerMoneyBillions(remainingAfterBank)}</b>.</div>
      </article>
      <article class="milei-return-card fintech">
        <div class="step">Si las Fintech devolvieran “lo robado” / compensaran</div><h3>Pata Fintech separada</h3>
        <div class="return-amount">+ ${powerMoneyBillions(fintechReturn)}</div>
        <div class="breakdown">Saldo pos-shock contra su norma histórica. No está duplicado dentro de bancos.</div>
        <div class="after">El agujero bajaría a <b>${powerMoneyBillions(remainingAfterFintech)}</b>.</div>
      </article>
      <article class="milei-return-card end">
        <div class="step">Después de toda la pinza</div><h3>Lo que todavía faltaría amortiguar</h3>
        <div class="return-amount">${powerMoneyBillions(remainingAfterFintech)}</div>
        <div class="breakdown">Bancos + Fintech devolverían/compensarían ${powerMoneyBillions(financialRelief)} en este contrafactual.</div>
      </article>
    </div>
    <div class="milei-return-others-title">Y si también volvieran o se reasignaran las otras partidas auditadas:</div>
    <div class="milei-return-others">
      <article class="milei-return-other"><div class="actor">Privilegios fiscales prudentes</div><div class="amount">+ ${powerMoneyBillions(p.taxPrivilegesAnnual)}</div><div class="action">Si se recuperaran o reasignaran.</div><div class="after">Quedaría ${powerMoneyBillions(remainingAfterTax)}.</div></article>
      <article class="milei-return-other"><div class="actor">Mercado Libre</div><div class="amount">+ ${mileiCostMoney(meliArs)}</div><div class="action">Si no hubiera recibido esos beneficios/subsidios fiscales, o se recuperara un equivalente.</div><div class="after">Quedaría ${powerMoneyBillions(remainingAfterMeli)}.</div></article>
      <article class="milei-return-other"><div class="actor">SIDE</div><div class="amount">+ ${mileiCostMoney(p.sideExtraCredit)}</div><div class="action">Si devolviera o no utilizara el refuerzo de crédito.</div><div class="after">Quedaría ${powerMoneyBillions(remainingAfterSide)}.</div></article>
      <article class="milei-return-other"><div class="actor">Cúpula del PEN</div><div class="amount">+ ${mileiCostMoney(p.penCatchupAnnualized)}</div><div class="action">Si se revirtiera el extra nominal anualizado.</div><div class="after">Quedaría ${powerMoneyBillions(remainingAfterPen)}.</div></article>
      <article class="milei-return-other"><div class="actor">Dietas del Senado</div><div class="amount">+ ${mileiCostMoney(p.senateNetAnnualFloor)}</div><div class="action">Si se revirtiera el piso anual relevado.</div><div class="after">Quedaría ${powerMoneyBillions(finalRemaining)}.</div></article>
    </div>
    <div class="milei-return-total">
      <p><b>Resultado del ejercicio completo:</b> primero volvieron ${powerMoneyBillions(salaryRecovered)} por recuperación salarial; después sumamos ${powerMoneyBillions(financialRelief)} de bancos + Fintech y ${powerMoneyBillions(broad)} de las otras partidas. Todo es alivio a favor del hogar.</p>
      <div class="amount">Faltaría ${powerMoneyBillions(finalRemaining)}</div>
    </div>
    <div class="milei-return-caveat"><b>Lectura editorial contrafactual:</b> “devolver” agrupa mecanismos distintos —compensación financiera, reasignación presupuestaria o recuperación de beneficios— y no afirma una deuda judicial determinada. Las tarjetas de auditoría conservan la naturaleza y el período de cada dato.</div>`;

'''
html = replace_once(html, "  const card=(cls,pill,title,money,body,scaleText,tab,id)=>", return_render + "  const card=(cls,pill,title,money,body,scaleText,tab,id)=>", "render del escenario")

html = replace_once(
    html,
    '<div><div class="step">4 · Soluciones superpuestas</div><div class="formula">Pinza <b>−${powerMoneyBillions(financialRelief)}</b> + envolvente <b>−${powerMoneyBillions(broad)}</b> ⇒ remanente <b>${powerMoneyBillions(finalRemaining)}</b>.</div></div>',
    '<div><div class="step">4 · Alivios a favor del hogar</div><div class="formula"><b class="household-plus">+${powerMoneyBillions(financialRelief)}</b> volverían por bancos + Fintech y <b class="household-plus">+${powerMoneyBillions(broad)}</b> por otras partidas. Al restarlos del agujero, quedarían <b>${powerMoneyBillions(finalRemaining)}</b>.</div></div>',
    "fórmula didáctica",
)

old_rows = '''    <tr><td>Recuperación salarial observada</td><td>−${powerMoneyBillions(salaryRecovered)}</td><td class="attr-yes">Se descuenta porque la mejora ya ocurrió.</td><td><b>${powerMoneyBillions(salaryRemaining)}</b></td></tr>
    <tr><td>Balance financiero ampliado si se soluciona</td><td>−${powerMoneyBillions(financialRelief)}</td><td class="attr-yes">Se descuenta como alivio potencial del problema financiero.</td><td><b>${powerMoneyBillions(remainingAfterPinza)}</b></td></tr>
    <tr><td>Envolvente auditada</td><td>−${powerMoneyBillions(broad)}</td><td class="attr-partial">Superpone privilegios fiscales, Mercado Libre, SIDE, PEN y Senado como capacidad potencial.</td><td><b>${powerMoneyBillions(finalRemaining)}</b></td></tr>
    <tr><td>Fintech · diferencial incluido</td><td>${mileiCostMoney(fintechExposure)}</td><td class="attr-partial">Está incluida en el balance financiero ampliado; se muestra aquí sólo para transparentar su aporte.</td><td>${mileiCostPct(fintechExposure,grossShock).toLocaleString('es-AR',{minimumFractionDigits:2,maximumFractionDigits:2})}% del total</td></tr>'''
new_rows = '''    <tr><td>Recuperación salarial observada</td><td class="household-plus">+${powerMoneyBillions(salaryRecovered)} al hogar</td><td class="attr-yes">Como vuelve al hogar, se resta del agujero.</td><td><b>${powerMoneyBillions(salaryRemaining)}</b></td></tr>
    <tr><td>Si bancos compensaran · crédito + PF</td><td class="household-plus">+${powerMoneyBillions(bankReturn)} al hogar</td><td class="attr-yes">Crédito ${powerMoneyBillions(bankCreditReturn)} + plazo fijo ${powerMoneyBillions(bankPfReturn)}.</td><td><b>${powerMoneyBillions(remainingAfterBank)}</b></td></tr>
    <tr><td>Si Fintech compensaran</td><td class="household-plus">+${powerMoneyBillions(fintechReturn)} al hogar</td><td class="attr-yes">Pata Fintech pos-shock separada, sin doble conteo.</td><td><b>${powerMoneyBillions(remainingAfterFintech)}</b></td></tr>
    <tr><td>Si se recuperara la envolvente auditada</td><td class="household-plus">+${powerMoneyBillions(broad)} al hogar</td><td class="attr-partial">Agrupa privilegios fiscales, Mercado Libre, SIDE, PEN y Senado.</td><td><b>${powerMoneyBillions(finalRemaining)}</b></td></tr>
    <tr><td>Fintech · cambio vs espejo</td><td>${mileiCostMoney(fintechWindowChange)}</td><td class="attr-partial">Es la variación entre ventanas, no el monto usado como devolución. Se conserva para responder si mejoró o empeoró.</td><td>${mileiCostPct(fintechWindowChange,grossShock).toLocaleString('es-AR',{minimumFractionDigits:2,maximumFractionDigits:2})}% del total</td></tr>'''
html = replace_once(html, old_rows, new_rows, "tabla de atribución")

html = replace_once(html, "['Fintech · diferencial incluido',fintechExposure]", "['Fintech · saldo pos-shock si compensara',fintechReturn]", "escala Fintech")
html = replace_once(
    html,
    '<div class="milei-cost-disclaimer"><b>Cuenta unificada:</b> ${powerMoneyBillions(grossShock)} − ${powerMoneyBillions(salaryRecovered)} − ${powerMoneyBillions(financialRelief)} − ${powerMoneyBillions(broad)} = <b>${powerMoneyBillions(finalRemaining)}</b> todavía por amortiguar.</div>',
    '<div class="milei-cost-disclaimer"><b>Signo hogar:</b> salarios <span class="household-plus">+${powerMoneyBillions(salaryRecovered)}</span>, bancos + Fintech <span class="household-plus">+${powerMoneyBillions(financialRelief)}</span> y otras partidas <span class="household-plus">+${powerMoneyBillions(broad)}</span> son alivios. Se restan del agujero de ${powerMoneyBillions(grossShock)} y quedan <b>${powerMoneyBillions(finalRemaining)}</b> por amortiguar.</div>',
    "resumen de escala",
)

# Auditoría financiera: separar saldos pos-shock que integrarían la devolución de los diferenciales entre ventanas.
old_fin_audit = '''  if(milei)milei.innerHTML=`
    <div class="milei-financial-grid">
      <div class="milei-financial-item">
        <div class="audit-tag">Balance ampliado banco + Fintech + PF · pos-shock</div>
        <div class="audit-amount">${ratesMoneyArs(p.impacto_hogar_total_ampliado,2,true)}</div>
        <p>Ventana espejo: <b>${ratesMoneyArs(m.impacto_hogar_total_ampliado,2,true)}</b> · diferencial post − espejo: <b>${ratesMoneyArs(d.impacto_hogar_total_ampliado,2,true)}</b>.</p>
      </div>
      <div class="milei-financial-item fintech">
        <div class="audit-tag">Fintech · ya incorporado al balance ampliado</div>
        <div class="audit-amount">${ratesMoneyArs(d.impacto_hogar_fintech,2,true)}</div>
        <p>Diferencial Fintech entre ventanas. Saldo pos-shock: <b>${ratesMoneyArs(p.impacto_hogar_fintech,2,true)}</b>. Incluye ${p.fintech_meses_tna_observada} meses con TNA oficial y ${p.fintech_meses_tna_conservada} meses estimados.</p>
      </div>
    </div>
    <p class="milei-financial-summary"><b>Cómo entra en la cuenta de $18,43 billones:</b> si se eliminara por completo el saldo financiero negativo pos-shock del balance ampliado, el alivio potencial sería <b>${ratesMoneyArs(financialRelief)}</b>. Para responder si mejoró o empeoró, el dato correcto es el diferencial post − espejo: <b>${ratesMoneyArs(d.impacto_hogar_total_ampliado,2,true)}</b>. Sin Fintech, banco + PF da <b>${ratesMoneyArs(d.impacto_hogar_total,2,true)}</b>.</p>`;'''
new_fin_audit = '''  if(milei)milei.innerHTML=`
    <div class="milei-financial-grid">
      <div class="milei-financial-item">
        <div class="audit-tag">Si los bancos compensaran · crédito + plazo fijo</div>
        <div class="audit-amount household-plus">+${ratesMoneyArs(Math.max(0,-p.impacto_hogar_banco-p.impacto_hogar_pf))} al hogar</div>
        <p>Crédito bancario: <b>${ratesMoneyArs(Math.max(0,-p.impacto_hogar_banco))}</b> · plazo fijo: <b>${ratesMoneyArs(Math.max(0,-p.impacto_hogar_pf))}</b>. Son saldos pos-shock contra sus normas históricas.</p>
      </div>
      <div class="milei-financial-item fintech">
        <div class="audit-tag">Si las Fintech compensaran · pata separada</div>
        <div class="audit-amount household-plus">+${ratesMoneyArs(Math.max(0,-p.impacto_hogar_fintech))} al hogar</div>
        <p>No está duplicada dentro de bancos. Incluye ${p.fintech_meses_tna_observada} meses con TNA oficial y ${p.fintech_meses_tna_conservada} meses estimados.</p>
      </div>
    </div>
    <p class="milei-financial-summary"><b>Cómo entra en la cuenta de $18,43 billones:</b> bancos + Fintech compensarían <b class="household-plus">+${ratesMoneyArs(financialRelief)} a favor del hogar</b>; por eso el mismo monto se resta del agujero. Para responder si mejoró o empeoró, usamos otro dato: diferencial post − espejo <b>${ratesMoneyArs(d.impacto_hogar_total_ampliado,2,true)}</b>.</p>`;'''
html = replace_once(html, old_fin_audit, new_fin_audit, "auditoría de bancos y Fintech")

OUTPUT.write_text(html, encoding="utf-8")
print(OUTPUT)
