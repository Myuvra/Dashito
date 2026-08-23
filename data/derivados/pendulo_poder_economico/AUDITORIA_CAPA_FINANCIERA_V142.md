# Auditoría · capa financiera observada v142

Fecha editorial: 2026-08-21  
Archivo: `data/dashboard_kawaii_142_pendulo_financiero_observado.html`  
SHA-256: `caaf9bc7900b95ebcfdec3e32b0ce54d710bef9c72cb76849097bffa1acbf357`

## Qué se agregó

- Película mensual desde enero de 2019 de costo real del crédito bancario, costo real fintech y rendimiento real del plazo fijo.
- Tramo fintech observado hasta febrero de 2026 y extensión marzo–julio separada visualmente.
- Cuatro lecturas actuales con perspectiva explícita: deudor, ahorrista y brecha bruta.
- Glosario visible que distingue TNA, tasa real mensual, CFT faltante y rentabilidad contable.
- El spread queda rotulado como diferencia de precios financieros, nunca como ganancia.

## Últimos valores visibles

- Crédito bancario, julio de 2026: 3.292465% real mensual.
- Plazo fijo, julio de 2026: -0.374889% real mensual.
- Banco − plazo fijo, julio de 2026: 3.667354 pp.
- Fintech, último observado febrero de 2026: 8.867079% real mensual.

Fórmula de la brecha mostrada:

```text
brecha_real_banco_pf_t = tasa_real_banco_t − rendimiento_real_pf_t
3,292465 − (−0,374889) = 3,667354 pp en julio de 2026
```

Las tasas reales ya provienen de la transformación Fisher auditada del tab Tasas e inflación. CFT queda ausente porque no hay una serie continua comparable integrada. ROA/ROE y resultados reales permanecen en un carril separado.

## Controles

- coverage_2019_2026: PASS
- fintech_observed_ends_feb_2026: PASS
- fintech_extension_is_visible: PASS
- gap_formula_exact: PASS
- cft_missing_declared: PASS
- profitability_separate: PASS
- finance_renderer_connected: PASS
- six_layers_preserved: PASS
- asset_module_preserved: PASS
- original_cgi_formula_preserved: PASS
- tab_count_preserved: PASS
- html_ids_unique: PASS
- metric_ids_unique: PASS
