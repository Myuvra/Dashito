# Auditoría · Péndulo vivienda observada v143

Fecha editorial: 2026-08-21  
Archivo: `data/dashboard_kawaii_143_pendulo_vivienda_observada.html`  
SHA-256: `9fee6c15dee33a958f9bec757d97fbb5c4f1a0ad79b2ff64ffa20310aeb38f4c`

## Corrección de la tarjeta salarial

La función de Activos `pendPowerChange(value)` colisionaba con la función homónima que calculaba ventanas salariales por gobierno. Se renombró exclusivamente la función de Activos a `pendPowerAssetChange(value)`.

Resultados restaurados:

- Macri: -17.786097%
- Alberto: -12.493451%
- Milei: 4.202776%

## Vivienda observada

Fuente reutilizada: serie EPH ya archivada en el tab Vivienda, 31 aglomerados, semestral.

- Propietarios totales: 72.0% en 2S-2016 y 68.3% en 2S-2025; cambio -3.7 pp.
- Inquilinos: 17.7% en 2S-2016 y 20.5% en 2S-2025; cambio +2.8 pp.
- Desde 2S-2023: propietarios +1.7 pp; inquilinos -1.5 pp.

La condición de tenencia no mide valor, calidad, deuda hipotecaria ni alquiler/ingreso. Las categorías no se convierten en una puntuación de bienestar y los cambios no se atribuyen causalmente a un gobierno.

## Controles

- asset_salary_function_collision_removed: PASS
- asset_summary_uses_renamed_function: PASS
- salary_macri_restored: PASS
- salary_alberto_restored: PASS
- salary_milei_restored: PASS
- housing_coverage: PASS
- housing_latest_values: PASS
- housing_long_changes: PASS
- housing_post_2023_changes: PASS
- rent_income_gap_preserved: PASS
- housing_renderer_connected: PASS
- finance_preserved: PASS
- assets_preserved: PASS
- six_layers_preserved: PASS
- tab_count_preserved: PASS
- html_ids_unique: PASS
