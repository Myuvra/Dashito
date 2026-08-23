from pathlib import Path


SOURCE = Path(r"C:\Github\inflacion\data\dashboard_kawaii_130_devoluciones_y_signos_hogar.html")
OUTPUT = Path(r"C:\Github\inflacion\data\dashboard_kawaii_131_a_quien_le_conviene.html")


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
<style id="rates-who-benefits-v131">
/* v131 · traducción distributiva: a quién favorece y a quién perjudica cada cifra */
.rates-public-who{margin-top:10px;padding:10px 11px;border-radius:12px;border:1px solid #e3d8e7;background:#fff;box-sizing:border-box;font-size:10px;line-height:1.45;color:#6b596f}
.rates-public-who .question{display:block;margin-bottom:4px;font-size:8.5px;font-weight:950;letter-spacing:.04em;text-transform:uppercase;color:#8a6d8e}
.rates-public-who .winner,.rates-who-note .winner{color:#2f8063;font-weight:900}
.rates-public-who .loser,.rates-who-note .loser{color:#ad416a;font-weight:900}
.rates-public-who .nuance{display:block;margin-top:4px;color:#76677a;font-size:9px}
.rates-public-step.before .rates-public-who{border-color:#bcdccd;background:#f7fffb}
.rates-public-step.after .rates-public-who{border-color:#e8bdce;background:#fff8fb}
.rates-public-step.effect .rates-public-who{border-color:#cfc2eb;background:#fbf9ff}
.rates-who-strip{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:9px;margin-top:11px}
.rates-who-chip{min-width:0;padding:10px 11px;border:1px solid #e2d6e7;border-radius:12px;background:#fff;font-size:9.5px;line-height:1.45;color:#6c5a70;box-sizing:border-box}
.rates-who-chip b{display:block;margin-bottom:3px;color:#5d4269;font-size:10px}

#ratesMoneySection .rates-money-kpi .rates-who-note{margin-top:10px;padding:10px 11px;border-radius:12px;border:1px solid #e3d9e7;background:rgba(255,255,255,.88);font-size:10px;line-height:1.45;color:#6b596f;box-sizing:border-box}
#ratesMoneySection .rates-money-kpi .rates-who-title{display:block;margin-bottom:4px;font-size:8px;font-weight:950;letter-spacing:.04em;text-transform:uppercase;color:#886b8d}
#ratesMoneySection .rates-money-kpi .rates-who-detail{display:block;margin-top:4px;font-size:9px;color:#78687c}
#ratesMoneySection .rates-money-kpi.favorable .rates-who-note{border-color:#b8dccb;background:#f7fffb}
#ratesMoneySection .rates-money-kpi.desfavorable .rates-who-note{border-color:#e5bacc;background:#fff8fb}
.rates-who-method{margin:-4px 20px 16px;padding:11px 13px;border-left:5px solid #a278bd;border-radius:12px;background:#fbf8ff;color:#6b5970;font-size:10px;line-height:1.5;box-sizing:border-box}
.rates-who-method b{color:#5a3e69}
@media(max-width:1100px){.rates-who-strip{grid-template-columns:1fr}}
@media(max-width:720px){.rates-who-method{margin-left:14px;margin-right:14px}.rates-public-who{padding:9px 10px}}
@media(max-width:430px){.rates-who-method{margin-left:11px;margin-right:11px}#ratesMoneySection .rates-money-kpi .rates-who-note{padding:9px 10px}}
@media(max-width:390px){.rates-who-method{margin-left:9px;margin-right:9px}}
</style>
'''
html = replace_once(html, "</head>", css + "</head>", "CSS de notas en criollo")

html = replace_once(
    html,
    '''                <p>Saldo ampliado de banco + Fintech + plazo fijo durante los 32 meses anteriores.</p>''',
    '''                <p>Saldo ampliado de banco + Fintech + plazo fijo durante los 32 meses anteriores.</p>
                <div class="rates-public-who"><span class="question">¿A quién le convenía?</span><span class="winner">Al banco que captaba depósitos baratos</span>; <span class="loser">perjudicaba sobre todo a ahorristas de plazo fijo</span>.<span class="nuance">En esa ventana, crédito bancario y Fintech eran relativamente mejores para deudores; el rojo total lo explica principalmente el bajo rendimiento del PF.</span></div>''',
    "nota de la ventana espejo",
)
html = replace_once(
    html,
    '''                <p>Saldo ampliado durante los 32 meses posteriores al shock.</p>''',
    '''                <p>Saldo ampliado durante los 32 meses posteriores al shock.</p>
                <div class="rates-public-who"><span class="question">¿A quién le convino?</span><span class="winner">A bancos y Fintech del lado que presta o paga los depósitos</span>; <span class="loser">perjudicó tanto a deudores como a ahorristas</span>.<span class="nuance">Las tres patas quedaron negativas para el hogar frente a sus normas históricas.</span></div>''',
    "nota del período pos-shock",
)
html = replace_once(
    html,
    '''                <p>Un resultado positivo indica que el período posterior fue menos desfavorable.</p>
                <div class="rates-public-delta" id="ratesPublicEffectPct">—</div>''',
    '''                <p>Un resultado positivo indica que el período posterior fue menos desfavorable.</p>
                <div class="rates-public-delta" id="ratesPublicEffectPct">—</div>
                <div class="rates-public-who"><span class="question">¿A quién le convino la mejora?</span><span class="winner">Principalmente a quienes tenían plazo fijo</span>; <span class="loser">no a quienes debían a bancos o Fintech</span>.<span class="nuance">El PF mejoró más de lo que empeoraron las dos patas de crédito. Por eso el total da verde aunque no todos ganen.</span></div>''',
    "nota del diferencial",
)

html = replace_once(
    html,
    '''            <div class="rates-public-conclusion" id="ratesPublicConclusion">Calculando la lectura…</div>''',
    '''            <div class="rates-public-conclusion" id="ratesPublicConclusion">Calculando la lectura…</div>
            <div class="rates-who-strip" aria-label="Resumen de ganadores y perjudicados">
              <div class="rates-who-chip"><b>Crédito bancario</b>Si el impacto hogar es negativo, favorece relativamente al prestamista y perjudica al deudor.</div>
              <div class="rates-who-chip"><b>Fintech</b>Si el impacto hogar es negativo, favorece relativamente a la Fintech/prestamista y perjudica a quien tomó el crédito.</div>
              <div class="rates-who-chip"><b>Plazo fijo</b>Si el impacto hogar es positivo, favorece al ahorrista; si es negativo, abarata al banco la captación de esos pesos.</div>
            </div>''',
    "resumen distributivo",
)

html = replace_once(
    html,
    '''  <div class="rates-money-kpi-grid" id="ratesMoneyGrid"></div>
  <div class="rates-money-normalized" id="ratesMoneyNormalized"></div>''',
    '''  <div class="rates-money-kpi-grid" id="ratesMoneyGrid"></div>
  <div class="rates-who-method"><b>“Le conviene” en este bloque significa que esa parte queda relativamente favorecida frente a la norma o frente a la ventana espejo.</b> No convierte automáticamente la cifra en ganancia contable de bancos o Fintech: muestra de qué lado cae el efecto económico medido.</div>
  <div class="rates-money-normalized" id="ratesMoneyNormalized"></div>''',
    "nota metodológica distributiva",
)

old_grid = r'''  el.innerHTML=`
    <div class="rates-money-kpi primary ${ratesMoneyKpiClass(d.impacto_hogar_total_ampliado)}"><div class="tag">Diferencial post-shock vs espejo · balance ampliado</div><div class="big">${ratesMoneyArs(d.impacto_hogar_total_ampliado,2,true)}</div><div class="mini"><b>${ratesMoneyChangeWord(d.impacto_hogar_total_ampliado)}</b>. Fórmula: saldo post-shock − saldo espejo. Incluye banco + Fintech + plazo fijo.</div></div>
    <div class="rates-money-kpi ${ratesMoneyKpiClass(d.impacto_hogar_banco)}"><div class="tag">Cambio en crédito bancario</div><div class="big">${ratesMoneyArs(d.impacto_hogar_banco,2,true)}</div><div class="mini"><b>${ratesMoneyChangeWord(d.impacto_hogar_banco)}</b> respecto de la ventana espejo.</div></div>
    <div class="rates-money-kpi fintech ${ratesMoneyKpiClass(d.impacto_hogar_fintech)}"><div class="tag">Cambio en Fintech</div><div class="big">${ratesMoneyArs(d.impacto_hogar_fintech,2,true)}</div><div class="mini"><b>${ratesMoneyChangeWord(d.impacto_hogar_fintech)}</b>. Estimación mensual sobre stock real; ${p.fintech_meses_tna_conservada} meses prolongan el último dato oficial.</div></div>
    <div class="rates-money-kpi ${ratesMoneyKpiClass(d.impacto_hogar_pf)}"><div class="tag">Cambio en plazo fijo</div><div class="big">${ratesMoneyArs(d.impacto_hogar_pf,2,true)}</div><div class="mini"><b>${ratesMoneyChangeWord(d.impacto_hogar_pf)}</b> respecto de la ventana espejo.</div></div>
    <div class="rates-money-kpi ${ratesMoneyKpiClass(p.impacto_hogar_total_ampliado)}"><div class="tag">Saldo ampliado · post-shock</div><div class="big">${ratesMoneyArs(p.impacto_hogar_total_ampliado,2,true)}</div><div class="mini"><b>${ratesMoneyWord(p.impacto_hogar_total_ampliado)}</b> contra las normas históricas.</div></div>
    <div class="rates-money-kpi ${ratesMoneyKpiClass(m.impacto_hogar_total_ampliado)}"><div class="tag">Saldo ampliado · espejo</div><div class="big">${ratesMoneyArs(m.impacto_hogar_total_ampliado,2,true)}</div><div class="mini"><b>${ratesMoneyWord(m.impacto_hogar_total_ampliado)}</b> contra las normas históricas.</div></div>`;'''
new_grid = r'''  el.innerHTML=`
    <div class="rates-money-kpi primary ${ratesMoneyKpiClass(d.impacto_hogar_total_ampliado)}"><div class="tag">Diferencial post-shock vs espejo · balance ampliado</div><div class="big">${ratesMoneyArs(d.impacto_hogar_total_ampliado,2,true)}</div><div class="mini"><b>${ratesMoneyChangeWord(d.impacto_hogar_total_ampliado)}</b>. Fórmula: saldo post-shock − saldo espejo. Incluye banco + Fintech + plazo fijo.</div><div class="rates-who-note"><span class="rates-who-title">En criollo · ¿a quién le convino?</span><span class="winner">A ahorristas con plazo fijo</span>, cuya mejora dominó el total. <span class="loser">No a deudores bancarios ni Fintech</span>: esas dos patas empeoraron.<span class="rates-who-detail">El balance conjunto mejoró, pero no todos los grupos ganaron.</span></div></div>
    <div class="rates-money-kpi ${ratesMoneyKpiClass(d.impacto_hogar_banco)}"><div class="tag">Cambio en crédito bancario</div><div class="big">${ratesMoneyArs(d.impacto_hogar_banco,2,true)}</div><div class="mini"><b>${ratesMoneyChangeWord(d.impacto_hogar_banco)}</b> respecto de la ventana espejo.</div><div class="rates-who-note"><span class="rates-who-title">¿A quién le convino?</span><span class="winner">Al banco/prestamista</span>; <span class="loser">perjudicó a quien tenía un préstamo personal</span>.<span class="rates-who-detail">El crédito quedó más costoso para el deudor frente al período comparable.</span></div></div>
    <div class="rates-money-kpi fintech ${ratesMoneyKpiClass(d.impacto_hogar_fintech)}"><div class="tag">Cambio en Fintech</div><div class="big">${ratesMoneyArs(d.impacto_hogar_fintech,2,true)}</div><div class="mini"><b>${ratesMoneyChangeWord(d.impacto_hogar_fintech)}</b>. Estimación mensual sobre stock real; ${p.fintech_meses_tna_conservada} meses prolongan el último dato oficial.</div><div class="rates-who-note"><span class="rates-who-title">¿A quién le convino?</span><span class="winner">A la Fintech/prestamista</span>; <span class="loser">perjudicó a usuarios endeudados</span>.<span class="rates-who-detail">Es una proxy de carga extraordinaria, no una ganancia neta contable.</span></div></div>
    <div class="rates-money-kpi ${ratesMoneyKpiClass(d.impacto_hogar_pf)}"><div class="tag">Cambio en plazo fijo</div><div class="big">${ratesMoneyArs(d.impacto_hogar_pf,2,true)}</div><div class="mini"><b>${ratesMoneyChangeWord(d.impacto_hogar_pf)}</b> respecto de la ventana espejo.</div><div class="rates-who-note"><span class="rates-who-title">¿A quién le convino?</span><span class="winner">Al ahorrista con plazo fijo</span>; para el banco implica pagar más por captar esos pesos.<span class="rates-who-detail">Esta mejora explica que el diferencial conjunto termine positivo.</span></div></div>
    <div class="rates-money-kpi ${ratesMoneyKpiClass(p.impacto_hogar_total_ampliado)}"><div class="tag">Saldo ampliado · post-shock</div><div class="big">${ratesMoneyArs(p.impacto_hogar_total_ampliado,2,true)}</div><div class="mini"><b>${ratesMoneyWord(p.impacto_hogar_total_ampliado)}</b> contra las normas históricas.</div><div class="rates-who-note"><span class="rates-who-title">¿A quién le convino este saldo?</span><span class="winner">Al lado financiero que presta o remunera depósitos</span>; <span class="loser">perjudicó al conjunto medido de deudores y ahorristas</span>.<span class="rates-who-detail">Banco, Fintech y PF quedaron negativos para el hogar en esta ventana.</span></div></div>
    <div class="rates-money-kpi ${ratesMoneyKpiClass(m.impacto_hogar_total_ampliado)}"><div class="tag">Saldo ampliado · espejo</div><div class="big">${ratesMoneyArs(m.impacto_hogar_total_ampliado,2,true)}</div><div class="mini"><b>${ratesMoneyWord(m.impacto_hogar_total_ampliado)}</b> contra las normas históricas.</div><div class="rates-who-note"><span class="rates-who-title">¿A quién le convenía este saldo?</span><span class="winner">Principalmente al banco que captaba depósitos baratos</span>; <span class="loser">perjudicaba a ahorristas de PF</span>.<span class="rates-who-detail">Crédito bancario y Fintech sí eran relativamente favorables a deudores; el rojo total venía del PF.</span></div></div>`;'''
html = replace_once(html, old_grid, new_grid, "notas por cada KPI monetario")

html = replace_once(
    html,
    '''  if(publicConclusion)publicConclusion.innerHTML=`<b>Lectura rápida:</b> crédito bancario <b>${ratesMoneyChangeWord(d.impacto_hogar_banco)} ${ratesMoneyArs(d.impacto_hogar_banco,2,true)}</b>; Fintech <b>${ratesMoneyChangeWord(d.impacto_hogar_fintech)} ${ratesMoneyArs(d.impacto_hogar_fintech,2,true)}</b>; plazo fijo <b>${ratesMoneyChangeWord(d.impacto_hogar_pf)} ${ratesMoneyArs(d.impacto_hogar_pf,2,true)}</b>. El balance ampliado <b>${ratesMoneyChangeWord(d.impacto_hogar_total_ampliado)} ${ratesMoneyArs(d.impacto_hogar_total_ampliado,2,true)}</b>, aunque el saldo post-shock siguió ${ratesMoneyWord(p.impacto_hogar_total_ampliado)}.`;''',
    '''  if(publicConclusion)publicConclusion.innerHTML=`<b>Lectura rápida:</b> crédito bancario <b>${ratesMoneyChangeWord(d.impacto_hogar_banco)} ${ratesMoneyArs(d.impacto_hogar_banco,2,true)}</b> y perjudicó a deudores; Fintech <b>${ratesMoneyChangeWord(d.impacto_hogar_fintech)} ${ratesMoneyArs(d.impacto_hogar_fintech,2,true)}</b> y perjudicó a sus usuarios endeudados; plazo fijo <b>${ratesMoneyChangeWord(d.impacto_hogar_pf)} ${ratesMoneyArs(d.impacto_hogar_pf,2,true)}</b> y favoreció a ahorristas. El balance ampliado <b>${ratesMoneyChangeWord(d.impacto_hogar_total_ampliado)} ${ratesMoneyArs(d.impacto_hogar_total_ampliado,2,true)}</b>, aunque el saldo post-shock siguió ${ratesMoneyWord(p.impacto_hogar_total_ampliado)}.`;''',
    "conclusión en criollo",
)

OUTPUT.write_text(html, encoding="utf-8")
print(OUTPUT)
