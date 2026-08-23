# Auditoría · Péndulo fiscal observado v144

Fecha editorial: 2026-08-21  
Archivo: `data/dashboard_kawaii_144_pendulo_fiscal_observado.html`  
SHA-256: `5a978cb14c5deec2af859d8e71c72a428e7f1f719b4dfd2ae3a5a567bf23242a`

## Resultado financiero del SPN

La visualización principal reutiliza la serie fiscal ya archivada en el dashboard. Para comparar años se privilegia el resultado financiero como porcentaje del PIB.

- 2023: -4.398249% del PIB; año de transición.
- 2024: 0.302236% del PIB.
- 2025: ≈ 0.200000% del PIB.
- 2026: ≈ 0.100000% del PIB; acumulado enero–julio.

Superávit indica un saldo favorable para el balance estatal, no una mejora automática del bienestar de los hogares. La serie agregada no identifica incidencia por quintil.

## Partidas vinculadas

- Privilegios fiscales · recorte prudente: $ 1,23 billones/año · CONTRAFACTUAL TRIBUTARIO · 2026 anual · evidencia B.
- Mercado Libre · beneficios documentados: $ 223,08 mil M · BENEFICIO OBSERVADO + CONVERSIÓN · 2024–1T26 · pesos jun-2026 · evidencia B/C.
- SIDE · refuerzo de crédito: + $ 49,30 mil M · CRÉDITO PRESUPUESTARIO · julio de 2026 · evidencia A/B.
- Cúpula PEN · extra nominal anualizado: ≈ $ 9,78 mil M/año · ESCENARIO SALARIAL · escala 2026 vs congelar dic-2023 · evidencia C.
- Senado · piso del salto de dietas: ≥ $ 2,28 mil M/año netos · PISO DERIVADO · salto aprobado en 2024 · evidencia C.

Estas tarjetas no se suman entre sí ni al resultado fiscal. Mezclan un contrafactual tributario, un beneficio documentado con conversión, una autorización presupuestaria y dos escenarios/pisos salariales de poderes distintos.

## Antidoble conteo

- Crédito presupuestario no equivale a ejecución.
- Gasto tributario no equivale a recaudación recuperable uno-a-uno.
- Resultado fiscal neto ya agrega recursos y gastos del universo cubierto.
- Períodos, monedas y actores deben homogeneizarse antes de cualquier escenario conjunto.

## Controles

- fiscal_coverage_2002_2026: PASS
- fiscal_2023_value: PASS
- fiscal_2024_value: PASS
- fiscal_2025_is_approx: PASS
- fiscal_2026_is_partial: PASS
- component_measure_types_distinct: PASS
- components_not_summed: PASS
- household_incidence_not_inferred: PASS
- fiscal_renderer_connected: PASS
- salary_bug_stays_fixed: PASS
- finance_preserved: PASS
- housing_preserved: PASS
- assets_preserved: PASS
- six_layers_preserved: PASS
- tab_count_preserved: PASS
- metric_ids_unique: PASS
- html_ids_unique: PASS
