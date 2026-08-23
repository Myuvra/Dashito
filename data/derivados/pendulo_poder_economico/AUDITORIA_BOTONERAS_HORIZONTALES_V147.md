# Auditoría · Botoneras horizontales del Péndulo v147

Fecha editorial: 2026-08-21  
Archivo: `data/dashboard_kawaii_147_pendulo_botoneras_horizontales.html`  
SHA-256: `887b669af2737513d41aa683607f07f3f6863b1532049dbe8f4300fb833d97ea`

## Cambio de jerarquía visual

- Se retiraron los controles `Ver como` y `Serie` de la tarjeta introductoria.
- Ambos grupos se trasladaron a la tarjeta del gráfico `El péndulo distributivo argentino`.
- El checkbox de promedio por gobierno se convirtió en un tercer grupo de la misma botonera.
- Los stickers quedan como guía previa y el dock completo aparece inmediatamente antes del gráfico.
- En escritorio funciona como una barra horizontal compacta.
- En móvil cada grupo ocupa su propia fila horizontal: `Ver como` y `Serie` permanecen descubiertos, y los botones de cada fila pueden desplazarse lateralmente sin envolver texto.
- La nota secundaria de `Guías` se oculta sólo en móvil para que el checkbox no genere un scrollbar innecesario.
- La navegación de capas A–F conserva el mismo patrón horizontal y pasa a ser sticky dentro del tab.
- No se duplicaron controles ni se modificó su lógica, datos o semántica.

## Controles automáticos

- controls_removed_from_hero: PASS
- controls_live_inside_main_chart_card: PASS
- controls_exist_once: PASS
- average_toggle_joined_to_toolbar: PASS
- controls_link_to_chart: PASS
- horizontal_nowrap_enabled: PASS
- horizontal_scroll_enabled: PASS
- mobile_groups_get_own_rows: PASS
- layer_nav_stays_horizontal: PASS
- cft_preserved: PASS
- roa_preserved: PASS
- six_layers_preserved: PASS
- tab_count_preserved: PASS
- html_ids_unique: PASS
