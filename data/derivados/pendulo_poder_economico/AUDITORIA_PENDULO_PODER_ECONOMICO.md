# Auditoría · Péndulo del poder económico v141

Fecha de corte editorial: 2026-08-21  
Archivo: `data/dashboard_kawaii_141_pendulo_poder_economico.html`  
SHA-256: `508ca259aaa7fd0930f52326e97acf6f580102237df4aed59595aef68750c211`

## Alcance de esta primera etapa

- El Péndulo CGI original se conserva sin alterar fórmulas, datos ni asignación por gobierno.
- Se incorporan seis capas navegables: Producción, Finanzas, Vivienda, Fiscal, Activos y Laboratorio.
- Finanzas resume los cálculos ya auditados del tab Tasas e inflación; no los recalcula con otra semántica.
- Vivienda y Fiscal muestran cobertura y huecos antes que fabricar incidencia contemporánea.
- El índice compuesto permanece deshabilitado hasta que existan componentes compatibles.
- Se crea un registro de métricas y una matriz de riesgo de doble conteo.

## La ventaja de ya tener capital

Base común real: diciembre de 2023 = 100.

- Efectivo sin remunerar, julio de 2026: 29.257014.
- Plazo fijo renovado mensualmente, julio de 2026: 79.517915.
- Dólar A3500 real, julio de 2026: 67.765810.
- Salario real como referencia, último dato 2026-06: 120.103905.

Fórmulas:

```text
efectivo_real_t = 100 × IPC_base / IPC_t
dólar_real_t = 100 × (A3500_t / A3500_base) × (IPC_base / IPC_t)
PF_real_t = PF_real_t-1 × (1 + rendimiento_real_mensual_t)
salario_real_t = 100 × índice_salario_real_t / índice_salario_real_base
```

El salario es una referencia de ingreso, no un activo. A3500 es referencia mayorista. El plazo fijo supone renovación mensual al promedio de 30–59 días. Ninguna curva informa quién poseía el activo.

## Clasificación de evidencia

Se separan dos ejes:

1. calidad/cobertura de fuente: A–D;
2. transformación: observado, derivado, contrafactual, reconstrucción o escenario.

El registro completo está en `metric_registry.json`. La matriz de solapamientos está en `double_count_matrix.csv`.

## Controles automáticos

- original_cgi_formula_preserved: PASS
- six_layer_buttons: PASS
- financial_summary_uses_audited_global: PASS
- asset_base_is_100: PASS
- asset_salary_has_visible_gap: PASS
- composite_is_disabled: PASS
- tab_count_preserved: PASS
- html_ids_unique: PASS
- metric_ids_unique: PASS
