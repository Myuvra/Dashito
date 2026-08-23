#!/usr/bin/env python3
"""Agrega una lectura pública y simple de la brecha bancaria antes/después."""

from __future__ import annotations

from pathlib import Path


DATA_DIR = Path(__file__).resolve().parents[1]
ROOT_DIR = DATA_DIR.parent
INPUT_NAME = "dashboard_kawaii_125_fintech_visible_sin_superposicion.html"
OUTPUT_NAME = "dashboard_kawaii_126_lectura_simple_brecha_bancaria.html"
INPUT_HTML = DATA_DIR / INPUT_NAME
OUTPUT_HTML = DATA_DIR / OUTPUT_NAME
ROOT_OUTPUT_HTML = ROOT_DIR / OUTPUT_NAME


def replace_once(text: str, old: str, new: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"Se esperaba 1 coincidencia y hubo {count}: {old[:140]!r}")
    return text.replace(old, new, 1)


def main() -> None:
    html = INPUT_HTML.read_text(encoding="utf-8")

    html = replace_once(
        html,
        """@media(max-width:390px){#ratesMoneySection .rates-money-legend,.rates-money-kpi-grid,.rates-money-normalized,#ratesMoneyChart,.rates-fintech-panel,.rates-money-table-wrap,.rates-money-audit-grid,#ratesMoneySection .rates-money-actions,.rates-files-audit{margin-left:9px;margin-right:9px}}
</style>""",
        """@media(max-width:390px){#ratesMoneySection .rates-money-legend,.rates-money-kpi-grid,.rates-money-normalized,#ratesMoneyChart,.rates-fintech-panel,.rates-money-table-wrap,.rates-money-audit-grid,#ratesMoneySection .rates-money-actions,.rates-files-audit{margin-left:9px;margin-right:9px}}

/* v126 · lectura apta para todo público del antes/después */
.rates-public-reading{margin:-1px 20px 13px;padding:16px 17px;border:1px solid #e4d3ea;border-radius:19px;background:linear-gradient(135deg,#fffdf7 0%,#fff8fb 52%,#f8f6ff 100%);box-sizing:border-box;color:#66546e}
.rates-public-head{display:flex;align-items:flex-start;justify-content:space-between;gap:14px}
.rates-public-kicker{font-size:9.5px;font-weight:950;letter-spacing:.045em;text-transform:uppercase;color:#9c5b76}
.rates-public-head h3{margin:4px 0 0;font-size:18px;line-height:1.2;color:#5c4268}
.rates-public-lead{margin:6px 0 0;max-width:720px;font-size:11.2px;line-height:1.45;color:#735f79}
.rates-public-formula{flex:0 0 auto;padding:7px 10px;border:1px solid #ddcfeb;border-radius:999px;background:#fff;font-size:9.5px;font-weight:900;color:#6c53a1;white-space:nowrap}
.rates-public-steps{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:10px;margin-top:13px}
.rates-public-step{min-width:0;padding:13px 14px;border:1px solid #eadfea;border-radius:15px;background:#fff;box-sizing:border-box}
.rates-public-step.after{border-color:#e7bfd0;background:#fff9fb}.rates-public-step.before{border-color:#cde4d8;background:#f9fffb}.rates-public-step.effect{border-color:#d9cff0;background:#fbf9ff}
.rates-public-step-label{display:flex;align-items:center;gap:7px;font-size:9.2px;font-weight:950;letter-spacing:.03em;text-transform:uppercase;color:#816c89}
.rates-public-step-no{display:inline-grid;place-items:center;width:20px;height:20px;border-radius:50%;background:#f2e8f1;color:#805070;font-size:10px}
.rates-public-step-amount{margin:8px 0 5px;font-size:23px;line-height:1;font-weight:950;color:#704d7b;overflow-wrap:anywhere}
.rates-public-step.after .rates-public-step-amount{color:#a1456d}.rates-public-step.before .rates-public-step-amount{color:#3f876c}.rates-public-step.effect .rates-public-step-amount{color:#5b43a0}
.rates-public-step p{margin:0;font-size:11.2px;line-height:1.48;color:#75647b}
.rates-public-step .rates-public-delta{margin-top:7px;font-size:9.8px;font-weight:900;color:#5b43a0}
.rates-public-conclusion{margin-top:11px;padding:11px 13px;border-left:4px solid #a77bc2;border-radius:12px;background:rgba(255,255,255,.78);font-size:11.6px;line-height:1.55;color:#67546f}
.rates-public-conclusion b{color:#5b3f71}
@media(max-width:1100px){.rates-public-head{display:block}.rates-public-formula{display:inline-block;margin-top:9px}.rates-public-steps{grid-template-columns:1fr}}
@media(max-width:720px){.rates-public-reading{margin-left:14px;margin-right:14px;padding:14px}.rates-public-head h3{font-size:17px}.rates-public-step-amount{font-size:22px}}
@media(max-width:430px){.rates-public-reading{margin-left:11px;margin-right:11px;padding:13px}.rates-public-formula{white-space:normal;line-height:1.35}}
@media(max-width:390px){.rates-public-reading{margin-left:9px;margin-right:9px}}
</style>""",
    )

    html = replace_once(
        html,
        """              <b>Efecto mostrado:</b> a cada mes pos-shock le restamos el mes equivalente de la ventana espejo previa y acumulamos la diferencia.
              Las tres curvas usan <code>costo bancario adicional − rendimiento neto del plazo fijo</code> y pesos constantes de julio de 2026.
            </div>
          </div>
          <div class="family-mini-note" style="padding-top:8px">""",
        """              <b>Efecto mostrado:</b> a cada mes pos-shock le restamos el mes equivalente de la ventana espejo previa y acumulamos la diferencia.
              Las tres curvas usan <code>costo bancario adicional − rendimiento neto del plazo fijo</code> y pesos constantes de julio de 2026.
            </div>
          </div>
          <div class="rates-public-reading" id="ratesPublicReading">
            <div class="rates-public-head">
              <div>
                <div class="rates-public-kicker">En criollo · la cuenta sin vueltas</div>
                <h3>¿Cuánto le costó la brecha a los hogares y qué parte ya venía de antes?</h3>
                <p class="rates-public-lead">La “pinza” junta dos efectos: pagar préstamos más caros que su promedio real y recibir menos por los plazos fijos.</p>
              </div>
              <div class="rates-public-formula">después − lo que ya pasaba = efecto adicional</div>
            </div>
            <div class="rates-public-steps">
              <div class="rates-public-step after">
                <div class="rates-public-step-label"><span class="rates-public-step-no">1</span> Lo que costó después</div>
                <div class="rates-public-step-amount" id="ratesPublicAfter">—</div>
                <p>El costo neto estimado durante los 32 meses posteriores al shock.</p>
              </div>
              <div class="rates-public-step before">
                <div class="rates-public-step-label"><span class="rates-public-step-no">2</span> Menos lo que ya pasaba</div>
                <div class="rates-public-step-amount" id="ratesPublicBefore">—</div>
                <p>Aplicamos la misma cuenta a los 32 meses anteriores. Así no cargamos al período algo que ya venía ocurriendo.</p>
              </div>
              <div class="rates-public-step effect">
                <div class="rates-public-step-label"><span class="rates-public-step-no">3</span> Lo adicional del período</div>
                <div class="rates-public-step-amount" id="ratesPublicEffect">—</div>
                <p>Restamos dos bloques iguales de 32 meses para aislar el cambio.</p>
                <div class="rates-public-delta" id="ratesPublicEffectPct">—</div>
              </div>
            </div>
            <div class="rates-public-conclusion" id="ratesPublicConclusion">Calculando la lectura…</div>
          </div>
          <div class="family-mini-note" style="padding-top:8px">""",
    )

    html = replace_once(
        html,
        """  if(effectTotal)effectTotal.textContent=ratesMoneyCompact(s.diferencial_pinza);
  if(effectPct)effectPct.textContent=`${((p.pinza_neta_hogar/m.pinza_neta_hogar-1)*100).toLocaleString('es-AR',{minimumFractionDigits:1,maximumFractionDigits:1})}% vs antes`;
  document.getElementById('ratesMoneyNormalized').innerHTML=""",
        """  if(effectTotal)effectTotal.textContent=ratesMoneyCompact(s.diferencial_pinza);
  const publicPct=(p.pinza_neta_hogar/m.pinza_neta_hogar-1)*100;
  if(effectPct)effectPct.textContent=`${publicPct.toLocaleString('es-AR',{minimumFractionDigits:1,maximumFractionDigits:1})}% vs antes`;
  const publicAfter=document.getElementById('ratesPublicAfter');
  const publicBefore=document.getElementById('ratesPublicBefore');
  const publicEffect=document.getElementById('ratesPublicEffect');
  const publicEffectPct=document.getElementById('ratesPublicEffectPct');
  const publicConclusion=document.getElementById('ratesPublicConclusion');
  if(publicAfter)publicAfter.textContent=ratesMoneyArs(p.pinza_neta_hogar);
  if(publicBefore)publicBefore.textContent=ratesMoneyArs(m.pinza_neta_hogar);
  if(publicEffect)publicEffect.textContent=ratesMoneyArs(s.diferencial_pinza);
  if(publicEffectPct)publicEffectPct.textContent=publicPct<0?`${Math.abs(publicPct).toLocaleString('es-AR',{minimumFractionDigits:1,maximumFractionDigits:1})}% menos que en la ventana anterior`:`${publicPct.toLocaleString('es-AR',{minimumFractionDigits:1,maximumFractionDigits:1})}% más que en la ventana anterior`;
  if(publicConclusion)publicConclusion.innerHTML=publicPct<0
    ?`<b>Lectura rápida:</b> la pinza financiera representó <b>${ratesMoneyArs(p.pinza_neta_hogar)}</b> que los hogares pagaron de más por préstamos o dejaron de recibir por plazo fijo. Pero la misma cuenta daba <b>${ratesMoneyArs(m.pinza_neta_hogar)}</b> en los 32 meses anteriores. Al descontar “lo que ya pasaba”, el efecto adicional es <b>${ratesMoneyArs(s.diferencial_pinza)}</b>: en esta medición, la pinza fue <b>${Math.abs(publicPct).toLocaleString('es-AR',{minimumFractionDigits:1,maximumFractionDigits:1})}% menor</b> que antes.`
    :`<b>Lectura rápida:</b> la brecha representó un costo estimado de <b>${ratesMoneyArs(p.pinza_neta_hogar)}</b> para los hogares. Después de restar los <b>${ratesMoneyArs(m.pinza_neta_hogar)}</b> que ya aparecían en la ventana anterior, queda un efecto adicional de <b>${ratesMoneyArs(s.diferencial_pinza)}</b>.`;
  document.getElementById('ratesMoneyNormalized').innerHTML=""",
    )

    OUTPUT_HTML.write_text(html, encoding="utf-8", newline="\n")
    ROOT_OUTPUT_HTML.write_text(html, encoding="utf-8", newline="\n")
    print(f"Generado: {OUTPUT_HTML}")
    print(f"Generado: {ROOT_OUTPUT_HTML}")


if __name__ == "__main__":
    main()
