# Auditoría · aporte voluntario progresivo de grandes fortunas

Fecha de construcción: 2026-08-20. Unidad común: pesos de junio de 2026.

1. **Pregunta.** Se prueba si un aporte patrimonial voluntario y progresivo puede compensar una meta de $4,98 billones sin superar un tope individual elegido.
2. **Base oficial.** ARCA, Anuario de Estadísticas Tributarias 2023, cuadro 2.5.1.2.1.1: 895.111 declaraciones con bienes y $27.922.627 millones declarados para el período fiscal 2022.
3. **Actualización.** IPC nacional INDEC dic-2022=1134.5875, jun-2026=11826.4103; factor=10.42353305. No se mezclan pesos nominales de años distintos.
4. **Universo.** Declarantes de Bienes Personales, no toda la población rica ni una lista de personas. Patrimonio declarado no equivale a ingreso anual ni a riqueza nacional WID.
5. **Distribución.** Los tramos cerrados se desagregan en nueve nodos dentro de sus límites y se calibran para preservar la media oficial.
6. **Cola abierta.** El tramo oficial >$5.000 millones de 2022 tiene 181 casos. Se usa Pareto α=1.8924, calibrada por mínimo y media, preservando casos y patrimonio. Es una estimación, no microdato.
7. **Fórmula.** aporteᵢ = min[λ × peso(patrimonioᵢ) × max(patrimonioᵢ−umbral,0), tope × patrimonioᵢ]. λ se resuelve por bisección para alcanzar la meta dada la participación.
8. **Participación.** 25/50/75/100% es participación esperada homogénea dentro de cada nodo. No modela selección estratégica; se muestra como escenario, no pronóstico conductual.
9. **Escenario inicial (tope 3%).** Umbral $1 B, 100% de participación, tope 3%: recaudación 4.748105 billones; 44966.6 aportantes esperados; tasa efectiva mediana 3.0000%.
10. **Comparación histórica.** El Aporte Solidario fue obligatorio, extraordinario y por única vez. AFIP informó $248.006 M en 2021; a precios de jun-2026 (aproximación dic-2021) son $5.036 billones. El mínimo legal de $200 M de dic-2020 equivale a $6.130 B. No se lo llama antecedente legal del esquema voluntario.
11. **Subdeclaración.** El escenario base no corrige evasión, valuaciones ni activos omitidos. La sensibilidad +20% es mecánica y visible; WID se usa sólo para recordar que la riqueza neta nacional y la base fiscal declarada son universos diferentes.
12. **No doble conteo.** La contribución es una compensación hipotética separada. No aumenta el daño del tab “Lo que te robó Milei” ni se suma a pérdidas, privilegios, SIDE, Mercado Libre o la pinza financiera.

## Resultado histórico comparable

- Recaudación oficial 2021: $248.006 millones.
- Reexpresión aproximada a junio de 2026: $5,035,596,095,615.
- Aportantes informados: alrededor de 10.000.
- Pago medio real aproximado: $503,559,610 por aportante.
- Tasas legales: 2%–3,5% sobre los bienes, con incremento para activos del exterior según la Ley 27.605.
- Tasa efectiva histórica promedio: **no publicada en los agregados oficiales revisados**; se evita inventarla.

## Archivos reproducibles

- `distribucion_patrimonial.csv`
- `simulacion_aporte_voluntario.csv`
- `sensibilidad_aporte.csv`
- `../lo_que_te_robo_reconciliacion.csv`
