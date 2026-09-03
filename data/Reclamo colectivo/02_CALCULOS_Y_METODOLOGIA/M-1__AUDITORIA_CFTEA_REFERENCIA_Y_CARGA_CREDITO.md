# Auditoría — Brecha de costo del crédito vs CFTEA teórico de referencia

Corte: 25-08-2026. Base: dashboard causal vigente.

## Qué se agregó
- Nueva sección en **Tasas e inflación**: `ratesCreditReferenceSection`.
- Serie mensual dic-2019→jul-2026 de inflación móvil 12m y TNA equivalente de inflación.
- Banda TNA de referencia: inflación equivalente +10 pp (piso) / +21 pp (techo) con componentes editables.
- Conversión homogénea TNA→CFTEA estandarizado: tasa mensual = TNA/12, IVA 21% sobre intereses, capitalización 12 meses.
- Brecha principal: `CFTEA observado estandarizado − CFTEA techo`.
- Banco en pesos: flujo mensual de préstamos personales × diferencia mensual observada vs techo × factor IPC a jul-2026.
- Fintech en pesos: proxy sobre stock real, sólo cuando la TNA es observada; no se prolonga feb→jul-2026.
- Simulador de préstamo con cuota francesa teórica.
- Capítulo de Storytelling: **Costo ≠ ganancia**.

## Resultados con parámetros default
Referencia = riesgo 5–10 pp + administración/capital/liquidez 3–6 pp + margen real 2–5 pp.

Último banco (2026-07):
- TNA inflación equivalente: 29.49%
- CFTEA ref techo: 81.47%
- CFTEA banco estandarizado: 115.95%
- Brecha vs techo: +34.48 pp

Último Fintech observado (2026-02):
- CFTEA ref techo: 80.23%
- CFTEA Fintech estandarizado: 410.14%
- Brecha vs techo: +329.91 pp

Banco, 32 meses post-shock:
- exceso bruto (sólo meses > techo): $0.512 billones de jul-2026
- saldo neto vs techo: $-0.818 billones
- espejo 32 meses · saldo neto: $-0.220 billones
- post − espejo · saldo neto: $-0.597 billones

Fintech (proxy stock):
- post observado hasta feb-2026 · exceso bruto: $4.624 billones
- espejo · exceso bruto: $2.860 billones

## Interpretación
Un saldo bancario negativo frente al techo **no significa que el crédito sea barato en términos absolutos**: significa que, al usar una referencia que incorpora la inflación móvil y un colchón alto de riesgo/costos/margen, los meses por debajo del techo compensan a los meses por encima. El exceso bruto contesta otra pregunta y por eso se muestra por separado.

## Qué NO mide
- No es una tasa legal/justa.
- No es CFTEA contractual completo: no incorpora cargos, seguros ni comisiones.
- No es ganancia bancaria.
- El proxy Fintech sobre stock no es originación mensual y no se suma automáticamente al banco.

## Datos faltantes para pasar de sobrecosto a beneficio
Costo de fondeo por cartera, mora/incobrabilidad de cohortes, previsiones, encajes, impuestos, costo de capital, gastos operativos asignables, recuperos, comisiones/seguros y estructura contractual/plazos.

## QA
El HTML agrega asserts de: banda techo>piso, CFTEA>TNA cuando corresponde, identidad de brecha y ventana bancaria 32 vs 32.

SHA-256 HTML: `b47a31d094f56cdafc6f9275e56d61d9ce7abe4293aae11d112043c284999b88`
