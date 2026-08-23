# Auditoría · Capa Activos ampliada v145

Fecha de corte editorial: 2026-08-21  
Archivo: `data/dashboard_kawaii_145_pendulo_activos_ampliado.html`  
SHA-256: `e1b926a5e5edbe280ba65d3502e430b7b8bc374c24622ef113134d12754385d2`

## Cambio principal

Se agrega el CER oficial del BCRA como **referencia de principal indexado**, no como bono, depósito ni activo autónomo. La capa permite cambiar la fecha hipotética de entrada y vuelve a base 100 todas las curvas visibles.

Fuente CER: código 3540 de `tas5_ser.txt`, observación de fin de cada mes.  
Catálogo: https://www.bcra.gob.ar/archivos/Pdfs/PublicacionesEstadisticas/es_series.txt  
Serie: https://www.bcra.gob.ar/archivos/Pdfs/PublicacionesEstadisticas/tas5_ser.txt

## Fórmula

```text
CER_real_t = 100 × (CER_fin_mes_t / CER_fin_mes_base) × (IPC_base / IPC_t)
```

La interfaz puede volver a rebasar esta trayectoria y las demás en marzo de 2024, diciembre de 2024 o diciembre de 2025. El resultado de diciembre de 2023 es especialmente sensible al rezago del CER frente al IPC después del shock.

## Resultado por fecha de entrada

- 2023-12: CER 129.00; PF 79.52; A3500 67.77.
- 2024-03: CER 114.36; PF 95.34; A3500 77.57.
- 2024-12: CER 100.78; PF 103.01; A3500 92.82.
- 2025-12: CER 100.98; PF 96.52; A3500 86.08.

## Contrato de lectura

- Efectivo y plazo fijo son escenarios de tenencia/renovación.
- A3500 es una referencia mayorista, no una operación minorista.
- CER es un coeficiente: no incluye cupón, cotización, duración, comisión ni default de un instrumento.
- Salario real es ingreso de referencia, no activo.
- Ninguna línea informa cuántas personas accedieron, cuánto poseían ni cómo cambió el patrimonio de los hogares.
- Acciones, bonos, inmuebles y patrimonio siguen como huecos visibles hasta disponer de retornos totales y coberturas compatibles.

## Controles automáticos

- cer_months_complete: PASS
- cer_base_is_100: PASS
- cer_last_is_finite: PASS
- cer_is_labeled_reference: PASS
- entry_date_selector_present: PASS
- active_layer_tab_scrolls_into_mobile_view: PASS
- five_asset_traces_present: PASS
- access_layer_present: PASS
- assets_not_called_observed_wealth: PASS
- market_assets_keep_visible_gaps: PASS
- salary_bug_stays_fixed: PASS
- finance_preserved: PASS
- housing_preserved: PASS
- fiscal_preserved: PASS
- six_layers_preserved: PASS
- tab_count_preserved: PASS
- metric_ids_unique: PASS
- html_ids_unique: PASS
