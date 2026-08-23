# Auditoría metodológica · EMAE / actividad real

Corte de datos: **2026-06**. Construcción: **2026-08-21**.

## Archivos y fuentes

- EMAE original, desestacionalizada y tendencia-ciclo: INDEC, base 2004=100. Como entrada tabular se usa el CSV oficial de Datos Argentina, conciliado con el XLS y el informe de junio de 2026 archivados.
- Población 2022 en adelante: proyecciones INDEC derivadas del Censo 2022; el total anual se obtiene sumando edades y sexos y corresponde al 1 de julio.
- Población histórica 2003–2021: trayectoria anual del Banco Mundial, reescalada por un factor único `1.016025293746` para coincidir exactamente con INDEC en 2022. Es un complemento institucional, no una serie publicada como empalme por INDEC.
- Metodología EMAE: documento oficial INDEC archivado en `/data/fuentes/emae/metodologia/`.

## Transformaciones

### Bases

La interfaz permite: `nov-2023 = 100`, `ene-2017 = 100` y la base original INDEC `2004 = 100`. Para per cápita, la tercera opción usa **promedio mensual 2004 = 100**, porque el cociente EMAE/población no conserva mecánicamente la base publicada del EMAE.

### Población mensual y per cápita

Cada estimación anual se ubica al 1 de julio. Entre dos puntos anuales se interpola linealmente por días. Luego: `EMAE_pc_t = EMAE_t / población_t`. El resultado es un índice de actividad agregada por habitante, no PIB per cápita ni ingreso por persona.

### Cicatriz

Con referencia nov-2023: `gap_t = EMAE_SA_t / EMAE_SA_nov23 - 1`. Desde dic-2023, pérdida = `Σ max(0,-gap_t)`, recuperación = `Σ max(0,gap_t)` y saldo = `Σ gap_t`. La unidad es **meses equivalentes de actividad-base**.

### Drawdown y tiempo bajo el agua

El drawdown mensual estándar es `EMAE_t / max(EMAE_1…EMAE_t) - 1`. Para los episodios históricos se informa además un pico local previo explícito, su piso y la primera recuperación. `Meses bajo el agua` cuenta observaciones debajo del umbral; la profundidad acumulada suma `max(0, 1 - EMAE_t/umbral)`.

### Mandatos

El mes de asunción se atribuye al gobierno entrante: dic-2007, dic-2015, dic-2019 y dic-2023. Néstor está truncado a ene-2004 por el inicio de la serie mensual; Milei está truncado al último dato disponible. Recuperación del nivel inicial se mide luego de la primera caída bajo ese nivel. Recuperación del pico previo usa el máximo observado antes del mandato.

### Ventana espejo

Hay 31 meses completos post-shock (2023-12–2026-06) y exactamente 31 meses previos (2021-05–2023-11). Cada ventana se normaliza a 100 en su primer mes. El diferencial es `saldo_post - saldo_espejo`; positivo significa mejor recorrido relativo, no necesariamente nivel absoluto alto.

### Rebote vs crecimiento nuevo

El máximo total previo fue 2022-06; el máximo per cápita previo fue 2011-09. Se informa por separado si alguna vez se recuperó y si el último dato permanece arriba. Esto evita confundir una recuperación transitoria con un nuevo máximo sostenido.

## Limitaciones

- EMAE es provisional y revisable; tendencia-ciclo también cambia con nuevos extremos de serie.
- EMAE per cápita es una construcción analítica: usa población interpolada y no reemplaza PIB per cápita.
- La serie mensual comienza en 2004; no se inventa un drawdown 2001–2002.
- Las comparaciones de mandatos no controlan por contexto internacional, pandemia, punto de partida ni composición sectorial.
- El saldo en meses-base mide trayectoria relativa, no pesos, bienestar ni causalidad política.

## Pruebas programáticas

- PASS · nov-2023 produce exactamente 100 en las cuatro series reescaladas
- PASS · EMAE per cápita = EMAE / población mensual
- PASS · resúmenes por mandato concilian con la serie mensual
- PASS · drawdown usa el máximo acumulado correcto mes a mes
- PASS · ventana espejo y post-shock tienen exactamente 31 meses
- PASS · todos los KPIs se recalculan exactamente desde la serie mensual
- PASS · KPIs concilian también al releer los CSV derivados escritos
- PASS · títulos, selector, ejes y notas declaran bases consistentes
- PASS · los cinco CSV y sus controles de descarga quedaron embebidos

## Resultado de construcción

- Insumo HTML: `dashboard_kawaii_133_aporte_grandes_fortunas.html` (no sobrescrito).
- Salida HTML: `dashboard_kawaii_134_emae_actividad_real.html`.
- Último EMAE SA: `154.117263822133`.
- Saldo post-shock: `0.772830548046` meses-base.
