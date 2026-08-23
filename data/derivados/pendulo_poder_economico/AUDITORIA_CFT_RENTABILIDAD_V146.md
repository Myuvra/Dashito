# Auditoría · CFT y rentabilidad financiera v146

Fecha de corte editorial: 2026-08-21  
Archivo: `data/dashboard_kawaii_146_pendulo_cft_rentabilidad.html`  
SHA-256: `87bfec84d50e392fb6e8419986d3468e0fe0bae5f9709120114cf9c95efad8fb`

## CFT · fotografía comparable

- Fuente: BCRA, Informe de Inclusión Financiera · primer semestre de 2023, gráfico 18.
- Período: junio de 2023.
- Muestra: 15 entidades financieras y 15 PNFC con mayor cantidad de deudores entre quienes informaban préstamos personales al Régimen de Transparencia.
- Medida: promedio del CFT máximo ofrecido; EEFF = 321%, PNFC = 588%.
- Diferencia: +267 pp; cociente PNFC/EEFF = 1.8318.
- No es costo promedio pagado, ingreso del proveedor, saldo de cartera ni dato 2026.

## Rentabilidad bancaria · carril contable

- Fuente: BCRA, Informe sobre Bancos · mayo de 2026 y hoja 13 de su planilla oficial.
- Medida: ROA anualizado acumulado en tres y doce meses, en moneda homogénea.
- Sistema financiero: 3 meses a mayo de 2026 = 2.199157%; 12 meses = 1.065898%.
- Comparación interanual del ROA de doce meses: -0.674662 pp.
- La categoría EFNB no equivale a PNFC/fintech.

## Contrato de lectura y antidoble conteo

- CFT/TNA son precios del crédito desde la perspectiva del deudor.
- La pinza es un contrafactual monetario construido contra una norma histórica.
- ROA es resultado contable observado del intermediario como porcentaje del activo.
- Ninguno de estos indicadores se suma con los otros ni se usa como sustituto.
- No se infiere rentabilidad fintech desde TNA, CFT, EFNB o exposición contrafactual.

## Controles automáticos

- cft_eeff_is_321: PASS
- cft_pnfc_is_588: PASS
- cft_gap_is_267pp: PASS
- cft_ratio_is_1_83x: PASS
- roa_system_3m_matches_workbook: PASS
- roa_system_12m_matches_workbook: PASS
- roa_interannual_delta_matches: PASS
- efnb_caveat_visible: PASS
- cft_not_labeled_2026: PASS
- fintech_profitability_gap_visible: PASS
- observed_finance_preserved: PASS
- assets_preserved: PASS
- housing_preserved: PASS
- fiscal_preserved: PASS
- six_layers_preserved: PASS
- tab_count_preserved: PASS
- finance_metric_ids_unique: PASS
- html_ids_unique: PASS
