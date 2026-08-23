# Auditoría · Péndulo distributivo

Fecha de corte: 2026-08-21  
Fuente principal: INDEC — Cuenta de Generación del Ingreso e Insumo de Mano de Obra.

## Resultado reproducible

- Serie histórica: 1993–2007, anual, economía total y sector privado.
- Serie moderna: 2016-T1–2026-T1, trimestral, economía total y total excluido sector público.
- No hay observaciones ni interpolación para 2008–2015.
- Último dato privado normalizado (2026-T1): trabajo/hogares 57.580014%; EEB 42.419986%; péndulo +15.160028.
- Ventana Milei observada (2024-T1 → 2026-T1): cambio +8.771052 puntos del índice.

## Fórmulas

```text
denominador = RTA + IMB + EEB
share_hogares = (RTA + IMB) / denominador × 100
share_capital = EEB / denominador × 100
pendulo = ((RTA + IMB) - EEB) / denominador × 100
```

En el tramo moderno, los otros impuestos netos de subsidios quedan fuera del denominador. En 1993–2007 el archivo indica que otros impuestos a la producción están incluidos en IMB/EEB; no se pueden retirar sin inventar una apertura. Por eso no se trata a ambos segmentos como una serie homogénea.

## Controles automáticos

| Control | Resultado |
|---|---:|
| modern_period_count_41 | PASS |
| historical_year_count_15 | PASS |
| no_observations_2008_2015 | PASS |
| modern_accounting_closure_max_abs_lt_1e_3_million_pesos | PASS |
| historical_accounting_closure_max_abs_lt_1e_5 | PASS |
| normalized_shares_sum_100 | PASS |
| pendulum_equals_share_difference | PASS |
| all_values_finite | PASS |
| mandates_computed_for_two_universes | PASS |


Máximo error absoluto de cierre contable moderno: 0.000637393444777.  
Máximo error absoluto de cierre contable histórico: 5.82076609135e-11.  
Máximo error de suma de participaciones: 2.84217094304e-14 puntos porcentuales.

## Asignación por gobierno

- Serie histórica anual: 1993–1999 Menem; 2000–2001 De la Rúa; 2002 Duhalde; 2003–2007 Néstor Kirchner.
- 2002 tiene un único dato anual: no permite inferir movimiento dentro del mandato.
- 2008–2015: sin serie comparable; CFK I y II se muestran como “sin dato”.
- Serie moderna trimestral: 2016–2019 Macri; 2020–2023 Alberto Fernández; 2024–2026-T1 Milei.
- 2023-T4 no se divide por día: se asigna a Alberto Fernández y Milei comienza en 2024-T1.

## Fuentes archivadas

- `data/fuentes/pendulo_distributivo/indec/serie_cgi_07_26.xls`
- `data/fuentes/pendulo_distributivo/indec/cgi_cuadro1_total_1993_2007.xls`
- `data/fuentes/pendulo_distributivo/indec/cgi_apendice4_privado_1993_2007.xls`
- `data/fuentes/pendulo_distributivo/indec/cgi_07_26.pdf`
- `data/fuentes/pendulo_distributivo/metodologia/metodologia_24_cuentas_nacionales.pdf`

El JSON de extracción se genera con `extract_cgi_xls.ps1`. Los CSV, estadísticas por mandato, pruebas y HTML se regeneran con `build_pendulo_tab.py`.
