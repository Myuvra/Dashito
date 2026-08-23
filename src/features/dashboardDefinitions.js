import { average, dataCatalog, formatMoneyMillions, formatNumber, formatPercent, lastRow, latestFinite, sources } from '../data/catalog'

const { power, rates, poverty, gini, structure, family, social, consumption, work, housing, investment, growth, debtPublic, fiscal, bcra, debtSpiral, healthEducation, wealth, meli, casta } = dataCatalog

const metric = (label, value, detail, tone) => ({ label, value, detail, tone })
const line = (labels, series, extras = {}) => ({ type: 'line', labels, series, ...extras })
const bar = (labels, series, extras = {}) => ({ type: 'bar', labels, series, ...extras })
const stacked = (labels, series, extras = {}) => ({ type: 'stacked', labels, series, ...extras })
const sourceSet = (...items) => items

const powerLatest = Object.fromEntries(power.powerData.series.map((series) => [series.name, latestFinite(series.yNov)]))
const ratesLatest = lastRow(rates.ratesMoneyRows)
const fintechOfficial = lastRow(rates.ratesMoneyRows, (row) => row.fintech_tasa_observada)
const povertyLatest = latestFinite(poverty.povertyData.values)
const giniLatest = latestFinite(gini.giniData.values)
const structureLast = structure.structureCabaData.dates.length - 1
const workLatest = lastRow(work.workRows)
const tenureLatest = lastRow(housing.housingTenure)
const investmentLatest = lastRow(investment.investmentAnnual)
const growthLatest = growth.growthData.years.length - 1
const debtLatest = debtPublic.debtPublicData.years.length - 1
const fiscalYears = Object.keys(fiscal.fiscalAnnualData).map(Number)
const fiscalValues = fiscalYears.map((year) => fiscal.fiscalAnnualData[year].gdp)
const bcraSnapshot = bcra.bcraData.snapshot

const presidentialRows = [
  { president: 'Eduardo Duhalde', period: 'ene-2002 → abr-2003', accumulated: '≈44,5%', monthly: '≈2,33%/mes', method: 'IPC-GBA histórico' },
  { president: 'Néstor Kirchner', period: 'may-2003 base → dic-2007', accumulated: '≈61,4%', monthly: '≈0,87%/mes', method: 'reconstrucción histórica' },
  { president: 'Cristina Fernández', period: 'ene-2008 → nov-2015', accumulated: '≈539,2%', monthly: '≈1,97%/mes', method: 'Argendata armonizado' },
  { president: 'Mauricio Macri', period: 'ene-2016 → nov-2019', accumulated: '≈258,6%', monthly: '≈2,75%/mes', method: 'serie armonizada' },
  { president: 'Alberto Fernández', period: 'dic-2019 → nov-2023', accumulated: '≈930,7%', monthly: '≈4,98%/mes', method: 'IPC INDEC nacional' },
  { president: 'Javier Milei', period: 'dic-2023 → jul-2026', accumulated: '≈328,8%', monthly: '≈4,65%/mes', method: 'IPC INDEC nacional' },
]

export const dashboardDefinitions = {
  'tab-power': {
    eyebrow: 'Poder adquisitivo · índices reales',
    title: 'Salarios, jubilaciones e inflación sin mezclar bases',
    summary: 'Cada serie conserva su metodología y su fecha disponible. La referencia principal es noviembre de 2023 = 100.',
    badge: 'INDEC · ANSES · corte editorial 20/08/2026',
    metrics: [
      metric('Total salarios', formatNumber(latestFinite(power.powerTotalAllOfficial.yNov), 2), 'incluye no registrado · jun-2026', 'positive'),
      metric('Total registrado', formatNumber(powerLatest['Total registrado (INDEC)'], 2), 'jun-2026', 'negative'),
      metric('Privado registrado', formatNumber(powerLatest['Privado registrado'], 2), 'jun-2026'),
      metric('Jubilación mínima base', formatNumber(powerLatest['Jubilación mínima base (sin bonos)'], 2), 'jul-2026', 'positive'),
    ],
    sections: [
      { title: 'Poder adquisitivo ajustado por IPC nacional', badge: 'nov-2023 = 100', chart: line(power.powerData.dates, power.powerData.series.map((item) => ({ name: item.name, values: item.yNov, dashed: item.dash === 'dash' })), { ariaLabel: 'Evolución real de salarios y jubilaciones' }), callout: { title: 'Cómo leerlo', text: 'Arriba de 100 implica mayor poder adquisitivo que en la base; debajo de 100 implica menor. RIPTE no representa al conjunto de trabajadores y el privado no registrado es una estimación EPH con rezago.' } },
      { title: 'Jubilación mínima: dos películas distintas', chart: line(power.powerPensionEffective.dates, [{ name: 'Mínima + bono máximo', values: power.powerPensionEffective.yNov }, { name: 'Mínima base', values: power.powerData.series.find((item) => item.name.startsWith('Jubilación mínima base'))?.yNov.slice(-power.powerPensionEffective.dates.length) || [] }], { ariaLabel: 'Jubilación mínima base y con bono' }), callout: { title: 'No son series rivales', text: 'La mínima base mide el haber legal. La segunda reconstruye el ingreso efectivo de quien cobra exactamente la mínima y accede al bono máximo.' } },
    ],
    formulas: [
      { title: 'Índice real', formula: '(serie nominal / IPC nivel general) / valor real en mes base × 100', result: 'El rebasing cambia la referencia visual, no la trayectoria subyacente.' },
      { title: 'Total salarios · jun-2026', formula: '9.442,50 / 2.157,73 / 4,19963 × 100', result: '104,20 · ≈ +4,20% real frente a nov-2023' },
    ],
    sources: sourceSet(sources.indec, sources.anses),
  },
  'tab-rates': {
    eyebrow: 'Crédito, ahorro e inflación',
    title: 'La pinza financiera vista desde el hogar',
    summary: 'Las tasas nominales se llevan a una ventana mensual comparable y luego se deflactan con el IPC mediante Fisher.',
    badge: 'BCRA + INDEC · tasas reales técnicas',
    metrics: [
      metric('Préstamo bancario real', formatPercent(ratesLatest.banco_real, 2, true), 'jul-2026 · mensual', 'negative'),
      metric('Plazo fijo real', formatPercent(ratesLatest.pf_real, 2, true), 'jul-2026 · 30 días', 'warning'),
      metric('Fintech PNFC', formatPercent(fintechOfficial.fintech_real, 2, true), 'feb-2026 · último dato observado', 'negative'),
      metric('Pinza banco vs. PF', `${formatNumber(ratesLatest.banco_real - ratesLatest.pf_real, 2)} pp`, 'jul-2026'),
    ],
    sections: [
      { title: 'Tasa mensual real estandarizada', badge: '2019–2026', chart: line(rates.ratesMoneyRows.map((row) => row.fecha), [{ name: 'Préstamo bancario', values: rates.ratesMoneyRows.map((row) => row.banco_real) }, { name: 'Plazo fijo 30–59 días', values: rates.ratesMoneyRows.map((row) => row.pf_real) }, { name: 'Fintech PNFC', values: rates.ratesMoneyRows.map((row) => row.fintech_real), dashed: true }], { valueSuffix: '%', ariaLabel: 'Tasas mensuales reales' }), callout: { title: 'Signo económico', text: 'Para préstamos, positivo es costo real para el hogar. Para el plazo fijo, positivo es rendimiento real. La Fintech conserva el último dato oficial cuando la publicación todavía no llega al mes corriente.' } },
      { title: 'Balance ampliado pos-shock', chart: bar(['Banco', 'Fintech', 'Plazo fijo', 'Total'], [{ name: 'Impacto hogar · $ billones', values: [rates.ratesMoneySummary.post.impacto_hogar_banco, rates.ratesMoneySummary.post.impacto_hogar_fintech, rates.ratesMoneySummary.post.impacto_hogar_pf, rates.ratesMoneySummary.post.impacto_hogar_total_ampliado].map((value) => value / 1e12) }], { valueSuffix: ' B', ariaLabel: 'Impacto financiero acumulado sobre el hogar' }), callout: { title: 'Convención', text: '+ favorable para el hogar; − desfavorable. No es ganancia contable de bancos o Fintech: muestra de qué lado cae el efecto económico medido.' } },
    ],
    formulas: [
      { title: 'Préstamo bancario real', formula: '[(1 + 5,476%) / (1 + 2,114%) − 1] × 100', result: '≈ +3,29% mensual real' },
      { title: 'Plazo fijo real', formula: '[(1 + 1,731%) / (1 + 2,114%) − 1] × 100', result: '≈ −0,37% real a 30 días' },
      { title: 'Fintech PNFC', formula: '[(1 + 12,020%) / (1 + 2,896%) − 1] × 100', result: '≈ +8,87% mensual real · feb-2026' },
    ],
    related: [{ id: 'tab-morosidad', label: 'Ver si el crédito caro terminó en mora →' }],
    sources: sourceSet(sources.bcra, sources.indec),
  },
  'tab-pres': {
    eyebrow: 'Inflación por presidencia', title: 'Acumulados, promedios y años de transición', summary: 'La convención atribuye el mes de asunción al gobierno entrante cuando el dato mensual permite identificarlo.', badge: 'IPC nacional + reconstrucción histórica',
    metrics: presidentialRows.slice(-3).map((row) => metric(row.president, row.accumulated, row.monthly)),
    table: { columns: [{ key: 'president', label: 'Presidente' }, { key: 'period', label: 'Período considerado' }, { key: 'accumulated', label: 'Inflación acumulada' }, { key: 'monthly', label: 'Mensual equivalente' }, { key: 'method', label: 'Serie' }], rows: presidentialRows },
    sections: [{ title: 'Mensual equivalente aproximada', chart: bar(presidentialRows.map((row) => row.president.split(' ').at(-1)), [{ name: '% mensual equivalente', values: [2.33, .87, 1.97, 2.75, 4.98, 4.65] }], { valueSuffix: '%', ariaLabel: 'Inflación mensual equivalente por presidencia' }), callout: { title: 'Cautela de corte', text: 'Diciembre de 2023 se atribuye a Javier Milei porque asumió el 10/12 y el shock cambiario principal ocurrió bajo su gestión. El IPC mensual no separa días previos y posteriores.' } }],
    sources: sourceSet(sources.indec, sources.argendata),
  },
  'tab-poverty': {
    eyebrow: 'Pobreza de personas', title: 'Nivel absoluto y cambios dentro de cada mandato', summary: 'Se muestran las observaciones comparables disponibles, dejando visibles los cambios metodológicos y los huecos.', badge: 'INDEC · EPH',
    metrics: [metric('Último dato', formatPercent(povertyLatest, 1), '2S-2025', 'positive'), metric('Pico reciente', '52,9%', '1S-2024', 'negative'), metric('Inicio de serie', '58,2%', '2S-2003')],
    sections: [{ title: 'Pobreza de personas: nivel absoluto', chart: line(poverty.povertyData.dates, [{ name: 'Pobreza', values: poverty.povertyData.values }], { valueSuffix: '%', ariaLabel: 'Pobreza de personas desde 2003' }), callout: { title: 'Comparabilidad', text: 'El 2015-II no tiene dato comparable. La observación 2016-I corresponde a un semestre móvil y está rotulada por separado.' } }, { title: 'Cambio dentro de cada mandato', chart: bar(poverty.povertyMandateChanges.map((item) => item.name || item.president || item.label), [{ name: 'Cambio en puntos porcentuales', values: poverty.povertyMandateChanges.map((item) => item.change ?? item.delta ?? item.value) }], { valueSuffix: ' pp', ariaLabel: 'Cambios de pobreza por mandato' }) }],
    sources: sourceSet(sources.indec, sources.argendata),
  },
  'tab-social': {
    eyebrow: 'Asistencia social', title: 'Transferencias e inversión social en términos reales', summary: 'Las variaciones se presentan programa por programa para evitar que una suma agregada oculte movimientos opuestos.', badge: 'Presupuesto Abierto · ANSES',
    metrics: social.socialRecent.labels.slice(0, 3).map((label, index) => metric(label, formatPercent(social.socialRecent.y2026[index], 1, true), '2026 vs. 2025', social.socialRecent.y2026[index] >= 0 ? 'positive' : 'negative')),
    sections: [{ title: 'Qué pasó después de 2024', chart: bar(social.socialRecent.labels, [{ name: '2025', values: social.socialRecent.y2025 }, { name: '2026', values: social.socialRecent.y2026 }], { valueSuffix: '%', ariaLabel: 'Variación real por programa social' }), callout: { title: 'Lectura', text: 'Una mejora en AUH puede convivir con caídas reales en Progresar, políticas alimentarias u otros programas. No se promedian categorías con objetivos distintos.' } }],
    sources: sourceSet(sources.presupuesto, sources.anses, sources.indec),
  },
  'tab-gini': {
    eyebrow: 'Distribución del ingreso', title: 'Desigualdad medida con el coeficiente de Gini', summary: 'Cero representa igualdad perfecta; uno, máxima concentración. Se preservan los cortes metodológicos de EPH.', badge: 'INDEC · EPH',
    metrics: [metric('Último Gini', formatNumber(giniLatest, 3), '1T-2026'), metric('Máximo reciente', formatNumber(Math.max(...gini.giniData.values), 3), 'serie comparable', 'negative'), metric('Mínimo reciente', formatNumber(Math.min(...gini.giniData.values), 3), 'serie comparable', 'positive')],
    sections: [{ title: 'Gini histórico publicado por INDEC', chart: line(gini.giniData.labels, [{ name: 'Coeficiente de Gini', values: gini.giniData.values }], { ariaLabel: 'Coeficiente de Gini trimestral' }), callout: { title: 'No mide riqueza', text: 'El Gini mostrado resume la distribución del ingreso per cápita familiar. No es un índice de patrimonio ni identifica por sí solo la causa de un cambio.' } }],
    sources: sourceSet(sources.indec),
  },
  'tab-structure': {
    eyebrow: 'Más allá de la pobreza', title: 'Vulnerabilidad, clase media y movilidad social', summary: 'No ser pobre no equivale automáticamente a pertenecer a la clase media. Las capas se presentan sin mezclar CABA, EPH urbana y UCA.', badge: 'IDECBA · INDEC · UCA',
    metrics: [metric('Personas no pobres', `${formatNumber(100 - structure.structureCabaData.pobreza[structureLast], 1)}%`, 'CABA · 1T-2026'), metric('Vulnerables + medio frágil', `${formatNumber(structure.structureCabaData.vulnerable[structureLast] + structure.structureCabaData.fragil[structureLast], 1)}%`, 'CABA · 1T-2026', 'warning'), metric('Sector medio', formatPercent(structure.structureCabaData.media[structureLast], 1), 'CABA · 1T-2026', 'positive'), metric('Acomodados', formatPercent(structure.structureCabaData.acomodados[structureLast], 1), 'CABA · 1T-2026')],
    sections: [
      { title: 'Estratos de ingresos en CABA', chart: stacked(structure.structureCabaData.periods, [{ name: 'Pobreza', values: structure.structureCabaData.pobreza }, { name: 'Vulnerable', values: structure.structureCabaData.vulnerable }, { name: 'Medio frágil', values: structure.structureCabaData.fragil }, { name: 'Clase media', values: structure.structureCabaData.media }, { name: 'Acomodados', values: structure.structureCabaData.acomodados }], { ariaLabel: 'Estratos de ingresos en CABA' }), callout: { title: 'Tres niveles, tres fuentes', text: 'IDECBA permite una estratificación fina en CABA; INDEC mide pobreza e indigencia por regiones; UCA aporta fragilidad, movilidad y estrés. No forman una única serie nacional.' } },
      { title: 'Movilidad de pobreza 2024 → 2025', chart: bar(structure.structureUcaData.mobility.map((item) => item.label), [{ name: '% de personas', values: structure.structureUcaData.mobility.map((item) => item.value) }], { valueSuffix: '%', ariaLabel: 'Movilidad de pobreza según UCA' }), callout: { title: 'Estrés y ahorro', text: `En 2025, ${formatNumber(structure.structureUcaData.stress2025, 1)}% reportó estrés económico y sólo ${formatNumber(structure.structureUcaData.saving2025, 1)}% capacidad de ahorro.` } },
      { title: 'Pobreza e indigencia por región', chart: bar(structure.structureFederalData.regions, [{ name: 'Pobreza', values: structure.structureFederalData.poverty }, { name: 'Indigencia', values: structure.structureFederalData.indigence }], { valueSuffix: '%', ariaLabel: 'Pobreza e indigencia por región' }) },
    ],
    sources: sourceSet(sources.idecba, sources.indec, sources.uca),
  },
  'tab-family': {
    eyebrow: 'Canastas y hogares', title: '¿Cuánto necesita realmente una familia?', summary: 'Se distingue el hogar tipo de GBA usado por INDEC del hogar propietario de CABA usado por IDECBA.', badge: 'hogares de referencia distintos',
    metrics: [metric('CBT GBA · hogar 4', `$ ${formatNumber(family.familyData.geo.gbaPoverty / 1e6, 3)} M`, 'jul-2026'), metric('Pobreza CABA · hogar 1', `$ ${formatNumber(family.familyData.geo.cabaPoverty / 1e6, 3)} M`, 'jul-2026'), metric('Entrada a clase media', `$ ${formatNumber(family.familyData.thresholds[3].value / 1e6, 3)} M`, 'CABA · hogar propietario'), metric('Brecha clase media', `+${formatNumber((family.familyData.thresholds[3].value / family.familyData.thresholds[1].value - 1) * 100, 1)}%`, 'vs. línea de pobreza', 'warning')],
    sections: [{ title: 'Escalera de ingresos · CABA', chart: bar(family.familyData.thresholds.map((item) => item.label), [{ name: '$ millones mensuales', values: family.familyData.thresholds.map((item) => item.value / 1e6) }], { valueSuffix: ' M', ariaLabel: 'Umbrales de ingresos de un hogar de CABA' }), callout: { title: 'No ser pobre ≠ ser clase media', text: 'La Canasta Total es una línea de pobreza; no pretende medir un presupuesto de vida cómoda ni el ingreso típico de una familia.' } }, { title: 'Costo de no ser propietario', chart: bar(family.familyData.housing.categories, [{ name: 'Propietario', values: family.familyData.housing.owner.map((value) => value / 1e6) }, { name: 'No propietario', values: family.familyData.housing.nonowner.map((value) => value / 1e6) }], { valueSuffix: ' M', ariaLabel: 'Canastas por condición de propiedad' }) }],
    sources: sourceSet(sources.indec, sources.idecba),
  },
  'tab-risk': { eyebrow: 'EMBI+ Argentina', title: 'Riesgo país: costo de la desconfianza financiera', summary: 'La visualización resume por mes una serie diaria para conservar legibilidad entre 2002 y la fecha de corte.', badge: 'fuente pública secundaria · indicador original J.P. Morgan', remoteSource: 'risk', remoteTitle: 'Riesgo país desde Duhalde', sources: sourceSet(sources.risk), callout: { title: 'Cómo leerlo', text: 'Menor es mejor para financiarse, pero el EMBI+ no mide bienestar social. Cien puntos básicos equivalen a un punto porcentual de spread sobre deuda de referencia.' } },
  'tab-bigmac': { eyebrow: 'Paridad cambiaria didáctica', title: 'Índice Big Mac: peso barato, caro o simplemente distinto', summary: 'La medida raw compara precios con EE.UU.; la ajustada por PIB pregunta qué cabría esperar para un país con nuestro nivel de ingresos.', badge: 'The Economist · observaciones disponibles', remoteSource: 'bigmac', remoteTitle: 'Sobre/subvaluación del peso', sources: sourceSet(sources.bigmac), callout: { title: 'No es una recomendación cambiaria', text: 'Acercarse a cero no significa automáticamente mayor bienestar. Para discutir sostenibilidad hay que cruzar productividad, salarios, reservas, inflación y comercio exterior.' } },
  'tab-wholesale': { eyebrow: 'Precios antes de la góndola', title: 'Mayoristas: costos que no se mueven todos juntos', summary: 'IPIM, IPIB e IPP describen etapas y coberturas distintas. La baja del índice general puede convivir con subas en manufacturas o electricidad.', badge: 'INDEC · julio 2026', metrics: [metric('Última lectura', 'debajo de 0,8%', 'jul-2026'), metric('Índice principal', 'IPIM', 'precios internos al por mayor'), metric('Auditoría', '3 índices', 'no son intercambiables')], sections: [{ title: 'Qué mide cada índice', callout: { title: 'IPIM · IPIB · IPP', text: 'IPIM incluye impuestos y productos importados; IPIB trabaja a precios básicos; IPP se concentra en producción nacional. Las etiquetas se mantienen separadas para no fabricar una única serie.' } }], sources: sourceSet(sources.indec) },
  'tab-health-education': {
    eyebrow: 'Gasto público consolidado', title: 'Salud y educación: cuánto invertimos realmente', summary: 'La serie histórica usa gasto público consolidado como porcentaje del PIB y separa nivel de gobierno.', badge: 'última foto consolidada · 2024',
    metrics: [metric('Educación', formatPercent(latestFinite(healthEducation.healthEducationData.education), 2), 'del PIB · 2024'), metric('Salud total', formatPercent(latestFinite(healthEducation.healthEducationData.health), 2), 'del PIB · 2024'), metric('Salud pública', formatPercent(latestFinite(healthEducation.healthEducationData.healthPublic), 2), 'del PIB · 2024')],
    sections: [{ title: 'Gasto consolidado en salud y educación', chart: line(healthEducation.healthEducationData.years, [{ name: 'Educación', values: healthEducation.healthEducationData.education }, { name: 'Salud total', values: healthEducation.healthEducationData.health }, { name: 'Salud pública', values: healthEducation.healthEducationData.healthPublic }], { valueSuffix: '%', ariaLabel: 'Gasto consolidado como porcentaje del PIB' }), callout: { title: 'Comparabilidad', text: 'La ejecución presupuestaria 2025–2026 es una foto más reciente, pero no reemplaza al gasto público consolidado y no se empalma como si fuera la misma serie.' } }],
    sources: sourceSet(sources.economia, sources.presupuesto),
  },
  'tab-consumption': {
    eyebrow: 'Consumo privado real', title: 'Consumo: ¿la gente compra más o menos?', summary: 'La columna vertebral es Cuentas Nacionales a precios constantes. Los consumos físicos se muestran aparte cuando su universo lo permite.', badge: '2002–2025 anual · 2023 = 100',
    metrics: [metric('2024 vs. 2023', '−2,9%', 'consumo real total', 'negative'), metric('2025 vs. 2024', '+7,9%', 'recuperación anual', 'positive'), metric('2025 vs. 2023', '+4,8%', 'total · +4,4% per cápita', 'positive')],
    sections: [{ title: 'Consumo real total y por habitante', chart: line(consumption.consumptionData.years, [{ name: 'Consumo real total', values: consumption.consumptionData.totalIndex }, { name: 'Real por habitante', values: consumption.consumptionData.perCapIndex }], { ariaLabel: 'Índice de consumo privado real' }), callout: { title: 'Base anual', text: 'La base 2023 = 100 es anual, no noviembre. Sirve para contestar si después de la caída de 2024 y el rebote de 2025 el consumo volvió al nivel anual previo.' } }, { title: 'Variación anual', chart: bar(consumption.consumptionData.years, [{ name: 'Cambio anual', values: consumption.consumptionData.growth }], { valueSuffix: '%', ariaLabel: 'Variación anual del consumo' }) }],
    sources: sourceSet(sources.indec),
  },
  'tab-work': {
    eyebrow: 'Mercado de trabajo', title: 'Trabajo: ¿hay más empleo y de qué calidad?', summary: 'La EPH puntual y la continua se presentan como metodologías distintas. La última foto se complementa con empleo registrado por sector.', badge: 'INDEC · EPH + SIPA',
    metrics: [metric('Actividad', formatPercent(workLatest.activity, 1), workLatest.label), metric('Empleo', formatPercent(workLatest.employment, 1), workLatest.label, 'positive'), metric('Desocupación', formatPercent(workLatest.unemployment, 1), workLatest.label, 'negative'), metric('Subocupación', formatPercent(workLatest.underemployment, 1), workLatest.label, 'warning')],
    sections: [{ title: 'Actividad, empleo y desocupación', chart: line(work.workRows.map((row) => row.label), [{ name: 'Actividad', values: work.workRows.map((row) => row.activity) }, { name: 'Empleo', values: work.workRows.map((row) => row.employment) }, { name: 'Desocupación', values: work.workRows.map((row) => row.unemployment) }], { valueSuffix: '%', ariaLabel: 'Tasas del mercado de trabajo' }), callout: { title: 'Cambio metodológico', text: 'En 2003 cambia la EPH; no sólo cambia la economía. Las series puntual y continua no se fuerzan dentro de una única línea.' } }, { title: 'Puestos registrados por sector', chart: bar(work.workSectorMonthly.map((row) => row.sector), [{ name: 'Variación', values: work.workSectorMonthly.map((row) => row.value) }], { horizontal: true, valueSuffix: '%', ariaLabel: 'Cambio del empleo registrado por sector' }) }],
    sources: sourceSet(sources.indec, sources.economia),
  },
  'tab-investment': {
    eyebrow: 'Formación bruta de capital fijo', title: 'Inversión: capacidad productiva para mañana', summary: 'Se distingue la inversión como porcentaje del PIB de su variación real anual y de quién la ejecuta.', badge: 'INDEC · Cuentas Nacionales',
    metrics: [metric('Inversión / PIB', formatPercent(investmentLatest.total, 1), '2025'), metric('Variación real', formatPercent(lastRow(investment.investmentReal).growth, 1, true), '2025', lastRow(investment.investmentReal).growth >= 0 ? 'positive' : 'negative'), metric('Gobierno', formatPercent(investment.investmentAnnual.at(-2).gov, 1), '2024 · último desglose')],
    sections: [{ title: 'Inversión como porcentaje del PIB', chart: line(investment.investmentAnnual.map((row) => row.year), [{ name: 'Total', values: investment.investmentAnnual.map((row) => row.total) }, { name: 'Gobierno', values: investment.investmentAnnual.map((row) => row.gov) }, { name: 'Resto de sectores', values: investment.investmentAnnual.map((row) => row.rest) }], { valueSuffix: '%', ariaLabel: 'Inversión como porcentaje del PIB' }) }, { title: 'Cambio real año contra año', chart: bar(investment.investmentReal.map((row) => row.year), [{ name: 'Variación real', values: investment.investmentReal.map((row) => row.growth) }], { valueSuffix: '%', ariaLabel: 'Variación real de la inversión' }) }],
    sources: sourceSet(sources.indec),
  },
  'tab-housing': {
    eyebrow: 'Tenencia y acceso', title: 'Vivienda: ¿es más fácil tener dónde vivir?', summary: 'Tenencia, alquiler, costos de construcción y crédito hipotecario responden preguntas diferentes.', badge: 'INDEC · BCRA · 2016–2026',
    metrics: [metric('Propietarios', formatPercent(tenureLatest.owner_total, 1), tenureLatest.period), metric('Inquilinos', formatPercent(tenureLatest.renter, 1), tenureLatest.period, 'warning'), metric('ICC GBA', formatPercent(housing.housingBuild[0].value, 1, true), 'jun-2026 · mensual')],
    sections: [{ title: 'Tenencia de vivienda', chart: line(housing.housingTenure.map((row) => row.period), [{ name: 'Propietarios', values: housing.housingTenure.map((row) => row.owner_total) }, { name: 'Inquilinos', values: housing.housingTenure.map((row) => row.renter) }, { name: 'Ocupantes', values: housing.housingTenure.map((row) => row.occupant) }], { valueSuffix: '%', ariaLabel: 'Tenencia de vivienda en hogares urbanos' }), callout: { title: 'Universo', text: 'La serie reciente usa hogares de 31 aglomerados urbanos. No se extrapola automáticamente al total nacional.' } }, { title: 'Costo de construcción · junio 2026', chart: bar(housing.housingBuild.map((row) => row.name), [{ name: 'Variación mensual', values: housing.housingBuild.map((row) => row.value) }], { valueSuffix: '%', ariaLabel: 'Índice del costo de la construcción' }) }],
    sources: sourceSet(sources.indec, sources.bcra),
  },
  'tab-growth': {
    eyebrow: 'PIB real', title: 'Crecimiento: ¿la economía produce más o menos?', summary: 'El nivel total, el nivel por habitante y la variación anual contestan preguntas distintas.', badge: 'INDEC · revisión publicada en 2026',
    metrics: [metric('PIB 2025', formatPercent(growth.growthData.growth[growthLatest], 1, true), 'variación anual', 'positive'), metric('PIB 1T-2026', formatPercent(growth.growthData.recent.q1_2026_yoy, 1, true), 'interanual', 'positive'), metric('EMAE mayo', formatPercent(growth.growthData.recent.emae_may_2026_mom_sa, 1, true), 'mensual desestacionalizado', 'negative')],
    sections: [{ title: 'Nivel real total y por habitante', chart: line(growth.growthData.years, [{ name: 'PIB real total · 2023=100', values: growth.growthData.levelIndex }, { name: 'PIB real por habitante', values: growth.growthData.perCapIndex }], { ariaLabel: 'Índice de PIB real' }) }, { title: 'Año por año', chart: bar(growth.growthData.years, [{ name: 'Crecimiento real', values: growth.growthData.growth }], { valueSuffix: '%', ariaLabel: 'Crecimiento anual del PIB' }), callout: { title: 'Atribución', text: 'Los años de transición mezclan meses de dos gobiernos. Una barra anual no prueba causalidad presidencial.' } }],
    sources: sourceSet(sources.indec),
  },
  'tab-fiscal': {
    eyebrow: 'Sector público nacional', title: 'Resultado fiscal: superávit o déficit', summary: 'El resultado financiero incluye intereses; el primario permite mirar las cuentas antes de ese costo.', badge: 'Ministerio de Economía · 2002–2026',
    metrics: [metric('2024', formatPercent(fiscal.fiscalAnnualData[2024].gdp, 2, true), 'resultado financiero / PIB', 'positive'), metric('2025', formatPercent(fiscal.fiscalAnnualData[2025].gdp, 1, true), 'aproximado', 'positive'), metric('2026', formatPercent(fiscal.fiscalAnnualData[2026].gdp, 1, true), 'ene–jul · parcial', 'positive')],
    sections: [{ title: 'Resultado financiero como porcentaje del PIB', chart: bar(fiscalYears, [{ name: 'Resultado financiero / PIB', values: fiscalValues }], { valueSuffix: '%', ariaLabel: 'Resultado fiscal anual' }), callout: { title: 'Parciales y aproximaciones', text: '2025 y 2026 están rotulados como aproximados o parciales. No se comparan como cierres definitivos.' } }],
    sources: sourceSet(sources.economia, sources.presupuesto),
  },
  'tab-trade': { eyebrow: 'Sector externo', title: 'Balanza comercial: qué vendemos y compramos', summary: 'Exportaciones, importaciones y saldo se leen juntas. Superávit no equivale automáticamente a bienestar.', badge: 'INDEC · Intercambio comercial argentino', metrics: [metric('Ventana', '2002–jun-2026', 'corte editorial'), metric('Mandatos', '6', 'fechas de asunción explícitas'), metric('Unidad', 'USD millones', 'valores corrientes')], sections: [{ title: 'Cómo leer el saldo comercial', callout: { title: 'Superávit ≠ siempre bueno', text: 'Puede mejorar por exportaciones fuertes o por una caída de importaciones asociada a recesión. El análisis conserva por separado cantidades, precios y contexto macro.' } }], sources: sourceSet(sources.indec) },
  'tab-bcra': {
    eyebrow: 'Reservas, dólar y tasas', title: 'La placa del BCRA, traducida', summary: 'Las reservas brutas, las compras del banco central, el tipo de cambio y las tasas tienen fechas y unidades diferentes.', badge: 'BCRA · corte agosto 2026',
    metrics: [metric('Reservas brutas', `USD ${formatNumber(bcraSnapshot.reserve, 0)} M`, bcraSnapshot.reserve_date), metric('Dólar mayorista', `$ ${formatNumber(bcraSnapshot.fx, 2)}`, bcraSnapshot.fx_date), metric('TAMAR', formatPercent(bcraSnapshot.tamar, 2), bcraSnapshot.rate_date), metric('BADLAR', formatPercent(bcraSnapshot.badlar, 2), bcraSnapshot.rate_date)],
    sections: [{ title: 'Reservas internacionales brutas', chart: line(bcra.bcraData.reserve.dates, [{ name: 'Reservas brutas · USD M', values: bcra.bcraData.reserve.stock }], { ariaLabel: 'Reservas internacionales brutas' }), callout: { title: 'Brutas no son netas', text: 'La cifra visible no descuenta encajes, swaps, préstamos ni otras obligaciones. Comprar dólares tampoco suma reservas dólar por dólar.' } }, { title: 'Tipo de cambio mayorista', chart: line(bcra.bcraData.fx.dates, [{ name: 'ARS por USD', values: bcra.bcraData.fx.level }], { ariaLabel: 'Tipo de cambio mayorista' }) }],
    sources: sourceSet(sources.bcra),
  },
  'tab-debt-spiral': {
    eyebrow: 'Deuda familiar', title: 'La bola de nieve: ingreso, canasta y crédito', summary: 'La simulación separa el shock observado de los supuestos futuros. No es una predicción individual.', badge: 'BCRA + INDEC · escenario editable',
    metrics: [metric('Shock dic-2023', '+25,5%', 'inflación mensual', 'negative'), metric('Préstamo bancario', formatPercent(lastRow(debtSpiral.debtObserved).bank, 2), 'tasa mensual equivalente'), metric('Fintech', formatPercent(lastRow(debtSpiral.debtObserved).fintech, 2), 'tasa mensual equivalente', 'negative')],
    sections: [{ title: 'Tasas e inflación observadas', chart: line(debtSpiral.debtObserved.map((row) => row.date), [{ name: 'Inflación', values: debtSpiral.debtObserved.map((row) => row.infl) }, { name: 'Crédito bancario', values: debtSpiral.debtObserved.map((row) => row.bank) }, { name: 'Fintech', values: debtSpiral.debtObserved.map((row) => row.fintech) }], { valueSuffix: '%', ariaLabel: 'Inflación y tasas de crédito familiar' }) }, { title: 'Canasta de clase media', chart: line(debtSpiral.debtClassBasket.dates, [{ name: 'Canasta alimentaria', values: debtSpiral.debtClassBasket.food }, { name: 'Canasta total', values: debtSpiral.debtClassBasket.total }], { ariaLabel: 'Canastas del hogar de referencia' }), callout: { title: 'Qué demuestra', text: 'La simulación muestra sensibilidad al rezago salarial, el costo financiero y el umbral de consumo. No demuestra que todos los hogares recorran el mismo sendero.' } }],
    sources: sourceSet(sources.bcra, sources.indec),
  },
  'tab-program': { eyebrow: 'Programa y escenarios', title: 'Escenarios plausibles aun siguiendo el plan', summary: 'Los presets no afirman que el programa fracase: prueban cuánto depende el sendero de crecimiento, tasas, reservas y acceso al mercado.', badge: 'escenarios, no pronósticos', metrics: [metric('Base', 'Continuidad', 'sendero FMI 2027–2031'), metric('Flojo', 'Menos rebote', 'crecimiento y PIB en USD'), metric('Tenso', 'Financiamiento caro', 'renovación más difícil', 'warning'), metric('Débil', 'Menos reservas', 'restricción externa', 'negative')], sections: [{ title: 'Escenarios plausibles', callout: { title: 'No hace falta que todo se rompa', text: 'El plan fiscal puede continuar y aun así enfrentar crecimiento menor, tasas más altas o una restricción externa. Cada escenario cambia una familia de supuestos y conserva las demás.' } }], sources: sourceSet(sources.imf, sources.economia, sources.bcra) },
  'tab-wealth-contribution': {
    eyebrow: 'Aporte voluntario progresivo', title: 'Grandes fortunas: cuánto recauda cada supuesto', summary: 'La simulación mantiene separados patrimonio, cantidad de aportantes, progresividad y participación voluntaria.', badge: 'escenario didáctico auditado',
    metrics: [metric('Objetivo', formatMoneyMillions(wealth.wealthContributionData.target, 0), 'recaudación objetivo'), metric('Nodos patrimoniales', formatNumber(wealth.wealthContributionData.nodes.length, 0), 'distribución simulada'), metric('FX jun-2026', `$ ${formatNumber(wealth.wealthContributionData.fxJun2026, 0)}`, 'ARS/USD')],
    sections: [{ title: 'Distribución patrimonial simulada', chart: line(wealth.wealthContributionData.nodes.map((_, index) => index + 1), [{ name: 'Patrimonio · $ millones', values: wealth.wealthContributionData.nodes.map((node) => node.w / 1e6) }], { ariaLabel: 'Distribución patrimonial simulada' }), callout: { title: 'No es un padrón real', text: 'Los nodos reconstruyen una distribución para probar tasas y participación. No identifican personas ni reemplazan estadísticas tributarias oficiales.' } }],
    sources: sourceSet(sources.arca, sources.economia),
  },
  'tab-milei-cost': {
    eyebrow: 'Cuenta unificada del hogar', title: 'Lo que te robó Milei: componentes y compensaciones', summary: 'La cuenta combina crédito bancario, Fintech y plazo fijo usando una convención explícita desde la perspectiva del hogar.', badge: 'pesos constantes de jul-2026',
    metrics: [metric('Crédito bancario', '−$ 1,04 B', 'cambio pos-shock vs. espejo', 'negative'), metric('Fintech', '−$ 1,85 B', 'estimación integrada', 'negative'), metric('Plazo fijo', '+$ 4,96 B', 'mejora relativa', 'positive'), metric('Balance ampliado', '+$ 2,07 B', 'diferencial pos-shock', 'positive')],
    sections: [{ title: 'Balance por pata financiera', chart: bar(['Crédito bancario', 'Fintech', 'Plazo fijo', 'Balance'], [{ name: '$ billones', values: [-1.04, -1.85, 4.96, 2.07] }], { valueSuffix: ' B', ariaLabel: 'Balance financiero del hogar' }), callout: { title: 'A quién le convino', text: 'El resultado positivo proviene principalmente de quienes ya tenían plazo fijo; no implica que a deudores bancarios o usuarios Fintech les haya ido mejor.' } }],
    sources: sourceSet(sources.bcra, sources.indec),
  },
  'tab-meli-benefits': {
    eyebrow: 'Regímenes promocionales', title: 'Privilegios fiscales: el caso Mercado Libre', summary: 'Se separan ganancias, contribuciones sociales y derechos de exportación para no sumar beneficios de naturaleza distinta sin etiqueta.', badge: 'ARCA · balances · 2008–1T26',
    metrics: [metric('Períodos', formatNumber(meli.meliBenefitData.labels.length, 0), 'observaciones'), metric('Ganancias · último', formatPercent(latestFinite(meli.meliBenefitData.income), 1), 'alícuota informada'), metric('Régimen', 'Economía del Conocimiento', 'último período')],
    sections: [{ title: 'Beneficios por período', chart: line(meli.meliBenefitData.labels, [{ name: 'Ganancias', values: meli.meliBenefitData.income }, { name: 'Contribuciones sociales', values: meli.meliBenefitData.social }, { name: 'Derechos de exportación', values: meli.meliBenefitData.exportDuty }], { valueSuffix: '%', ariaLabel: 'Beneficios tributarios de Mercado Libre' }), callout: { title: 'Incidencia', text: 'Un beneficio tributario no equivale automáticamente a una transferencia en efectivo ni a un costo idéntico para cada hogar.' } }],
    sources: sourceSet(sources.arca, sources.economia),
  },
  'tab-casta': {
    eyebrow: 'Cargos y presupuesto', title: 'La casta: salarios, inflación y cajas públicas', summary: 'Se separan remuneraciones nominales, poder adquisitivo y presupuesto de inteligencia.', badge: 'Presupuesto Abierto · normativa oficial',
    metrics: casta.castaSalaryLevels.labels.slice(0, 3).map((label, index) => metric(label, `$ ${formatNumber(casta.castaSalaryLevels.values[index] / 1e6, 2)} M`, 'remuneración informada')),
    sections: [{ title: 'Cuánto cobran arriba', chart: bar(casta.castaSalaryLevels.labels, [{ name: '$ millones', values: casta.castaSalaryLevels.values.map((value) => value / 1e6) }], { valueSuffix: ' M', ariaLabel: 'Remuneraciones de autoridades' }) }, { title: 'Sueldo político versus inflación', chart: line(casta.castaInflationVsSalary.labels, [{ name: 'IPC', values: casta.castaInflationVsSalary.cpi }, { name: 'Autoridades', values: casta.castaInflationVsSalary.authorities }, { name: 'Presidente', values: casta.castaInflationVsSalary.president }], { ariaLabel: 'Índice de salarios políticos e inflación' }), callout: { title: 'Índices, no montos', text: 'La base dic-2023 = 100 permite comparar trayectorias. No implica que todos los cargos tengan el mismo nivel salarial.' } }],
    sources: sourceSet(sources.presupuesto, sources.economia),
  },
  'tab-debt-public': {
    eyebrow: 'Deuda pública', title: 'Cuánto debemos y respecto de qué', summary: 'Stock en dólares, deuda sobre PIB, moneda y acreedor son dimensiones diferentes del mismo balance soberano.', badge: 'Secretaría de Finanzas · 1T-2026',
    metrics: [metric('Stock bruto', `USD ${formatNumber(debtPublic.debtPublicData.stockUsd[debtLatest], 0)} M`, '1T-2026'), metric('Deuda / PIB', formatPercent(debtPublic.debtPublicData.debtGdp[debtLatest], 1), '1T-2026'), metric('Moneda extranjera', formatPercent(debtPublic.debtPublicData.foreignCurrency[debtLatest], 1), 'del stock bruto')],
    sections: [{ title: 'Stock y deuda sobre PIB', chart: line(debtPublic.debtPublicData.labels, [{ name: 'Stock · USD miles de millones', values: debtPublic.debtPublicData.stockUsd.map((value) => value / 1000) }, { name: 'Deuda / PIB', values: debtPublic.debtPublicData.debtGdp }], { ariaLabel: 'Deuda pública argentina' }), callout: { title: 'La paradoja 2025 → 1T-2026', text: 'El stock puede subir al mismo tiempo que el ratio deuda/PIB baja. El denominador, el tipo de cambio y la valuación también cambian.' } }, { title: 'Composición por moneda', chart: line(debtPublic.debtPublicData.labels, [{ name: 'Moneda extranjera', values: debtPublic.debtPublicData.foreignCurrency }, { name: 'Moneda nacional', values: debtPublic.debtPublicData.foreignCurrency.map((value) => Number.isFinite(value) ? 100 - value : null) }], { valueSuffix: '%', ariaLabel: 'Composición de la deuda por moneda' }) }],
    sources: sourceSet(sources.economia),
  },
}
