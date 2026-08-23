import assert from 'node:assert/strict'
import fs from 'node:fs'
import path from 'node:path'
import { auditPlotlyAxes, cleanAnnotationText } from '../src/features/legacy-parity/chartAudit.js'
import { desiredTraceTheme, plotlyThemePalettes } from '../src/features/legacy-parity/plotlyTheme.js'

const root = process.cwd()
const read = (...parts) => fs.readFileSync(path.join(root, ...parts), 'utf8')
const css = read('data', 'legacy-archive', 'dashito-legacy.css')
const app = read('src', 'AppNext.jsx')
const markup = read('src', 'features', 'legacy-parity', 'LegacyMarkup.jsx')
const disclosure = read('src', 'features', 'legacy-parity', 'LegacyDisclosure.jsx')
const charts = read('src', 'features', 'legacy-parity', 'LegacyChartEnhancements.jsx')
const styles = read('src', 'styles.css')
const parityFeature = read('src', 'features', 'legacy-parity', 'LegacyParityFeature.jsx')

for (const breakpoint of ['1180px', '900px', '768px', '520px', '380px', '800px', '560px']) {
  assert.match(css, new RegExp(breakpoint.replace('px', 'px').replace(/[.*+?^${}()|[\]\\]/g, '\\$&')), `falta breakpoint ${breakpoint}`)
}
for (const selector of [
  '.wealth-controls',
  '.wealth-history',
  '.wealth-history-grid > div',
  '.wealth-history-callout',
  '.social-compare-head',
  '.social-compare-thesis',
  '.mandate-name',
  '.mor-inline-kpis span',
  '.milei-cost-hero',
  '.milei-return-scenario',
  '.milei-unified-components > div',
  '.milei-financial-item',
  '.milei-cost-formula > div',
  '.milei-scale-track',
  '.milei-return-others-title',
  '.household-plus',
  '.method-shield',
]) {
  assert.ok(css.includes(selector), `falta cobertura de ${selector}`)
}
assert.match(css, /input\[type='checkbox'\]/)
assert.match(css, /appearance:\s*none/)
assert.match(css, /max-width:\s*118px/)
assert.match(css, /max-width:\s*104px/)
assert.match(css, /translate:\s*0 6px/)
assert.match(css, /#tab-social \.social-compare-head \.method-shield[\s\S]*?margin-top:\s*14px/, 'la metodología social debe respirar respecto de la introducción')
assert.doesNotMatch(css, /html\[data-dashito-theme\] \.method-shield \{[^}]*margin-top:\s*0/, 'la skin no debe borrar el ritmo vertical metodológico de Legacy')
assert.match(css, /html\[data-dashito-theme\] \.method-shield \.label \{[^}]*border-radius:\s*4px/, 'las etiquetas metodológicas deben usar radio corto')
assert.match(css, /html\[data-dashito-theme\] \.method-shield \{[^}]*display:\s*block/, 'los textos metodológicos extensos no deben repartirse en columnas flex')
assert.match(css, /:where\(\.label, \.eyebrow, \.kicker, \.audit-tag, \.metric-tag\) \{[^}]*border-radius:\s*6px/, 'las etiquetas editoriales deben evitar la forma de cápsula')
assert.match(css, /:where\(\.tag, \.rates-timeline-status\) \{[^}]*padding:\s*6px 10px[^}]*border-radius:\s*4px/, 'los tags deben tener aire interior y radio corto')
assert.match(css, /:where\(\.gini-stat-grid, \.family-stat-grid\) \+ \.method-shield \{[^}]*margin-top:\s*14px/, 'las explicaciones posteriores a grillas-resumen deben quedar separadas')

assert.ok(!app.includes('sin iframe'), 'quedó visible una etiqueta técnica')
assert.ok(!app.includes('componentes React'), 'quedó visible una etiqueta técnica')
assert.match(markup, /LegacyDisclosure/)
assert.match(markup, /tab-poverty.*tab-social.*tab-gini/s)
assert.match(disclosure, /useState\(false\)/, 'fuentes y fórmulas deben iniciar plegadas')
assert.match(charts, /applyPlotlyTheme/)
assert.match(styles, /@import url\('\/dashito-legacy\.css'\) layer\(legacy\)/, 'la skin debe compartir la capa CSS de Legacy actualizada')
assert.ok(!parityFeature.includes('data-legacy-theme'), 'la skin no debe inyectarse tarde ni provocar un flash de estilos')
assert.match(css, /#tab-story \.story-hero[\s\S]*?border-radius:\s*14px/, 'Storytelling debe usar la geometría del rediseño')
assert.match(css, /#tab-story \.story-nav a[\s\S]*?border-radius:\s*6px/, 'la navegación de capítulos no debe usar píldoras')
assert.match(css, /#tab-story \.story-chapter[\s\S]*?background:[^;]*var\(--da-surface\)/, 'los capítulos de Storytelling deben respetar cada skin')

const mixedAxis = auditPlotlyAxes({
  data: [{ y: [-2, 1, 1000] }],
  layout: { yaxis: { title: { text: 'Serie mixta' } } },
})[0]
assert.equal(mixedAxis.eligible, false)
assert.equal(mixedAxis.classification, 'linear')

const positiveAxis = auditPlotlyAxes({
  data: [{ y: [1, 10, 1000] }],
  layout: { yaxis: { title: { text: 'Serie positiva' } } },
})[0]
assert.equal(positiveAxis.eligible, true)
assert.equal(positiveAxis.classification, 'recommended')

const shortIndexAxis = auditPlotlyAxes({
  data: [{ y: [45, 100, 225] }],
  layout: { yaxis: { title: { text: 'Índice real relativo' } } },
})[0]
assert.equal(shortIndexAxis.eligible, false, 'un índice de rango corto debe conservar escala lineal')
assert.equal(shortIndexAxis.classification, 'linear')

const independentAxes = auditPlotlyAxes({
  data: [
    { y: [1, 10, 1000] },
    { yaxis: 'y2', y: [-12, 0, 8] },
  ],
  layout: {
    yaxis: { title: { text: 'Tasas e inflación' } },
    yaxis2: { title: { text: 'Saldo monetario' } },
  },
})
assert.equal(independentAxes.find((axis) => axis.key === 'yaxis')?.eligible, true, 'el eje izquierdo positivo debe admitir escala log')
assert.equal(independentAxes.find((axis) => axis.key === 'yaxis2')?.eligible, false, 'el eje derecho que cruza cero debe seguir lineal')
assert.match(charts, /insertAdjacentElement\('beforebegin', before\)/, 'el selector de escala debe aparecer antes del gráfico')
assert.match(charts, /Escala eje izquierdo/, 'el control debe identificar el eje que modifica')
assert.match(charts, /range: Array\.isArray\(axis\.range\) \? \[\.\.\.axis\.range\]/, 'el rango lineal debe guardarse sin referencias mutables de Plotly')
assert.match(charts, /dashitoScaleBusy/, 'los cambios de escala deben serializarse para no corromper el layout')
assert.match(charts, /ExternalLegend/, 'la leyenda móvil extensa debe salir del SVG scrolleable')
assert.match(charts, /reflowNominalAnnotations/, 'las etiquetas del gráfico nominal deben evitar la superposición')
assert.match(charts, /reflowPowerAnnotations/, 'las etiquetas del gráfico de poder adquisitivo deben ocupar franjas separadas')
assert.doesNotMatch(charts, /chart\.id === 'powerChart' \? \{ \.\.\.audited, eligibleAxes: \[\] \}/, 'el gráfico de poder adquisitivo no debe perder el selector semilogarítmico')
assert.match(charts, /allowPowerPrimaryLog\(audited\)/, 'el eje positivo de poder adquisitivo debe conservar la opción semilogarítmica')
assert.match(charts, /chart\.clientWidth <= 960/, 'la leyenda del gráfico de poder adquisitivo debe responder al ancho real del gráfico')
assert.match(charts, /presidentIndex % 2/, 'los mandatos deben alternar franjas cuando el gráfico queda angosto')
assert.equal(cleanAnnotationText('A<br>B'), 'A · B')

const paletteFingerprints = Object.values(plotlyThemePalettes).map((palette) => palette.series.join(','))
assert.equal(new Set(paletteFingerprints).size, 3, 'las tres skins deben tener paletas distintas')
const blue = desiredTraceTheme({ type: 'bar', y: [1], marker: {} }, 0, 'blue-dark')['marker.color']
const rose = desiredTraceTheme({ type: 'bar', y: [1], marker: {} }, 0, 'rose-dark')['marker.color']
const light = desiredTraceTheme({ type: 'bar', y: [1], marker: {} }, 0, 'rose-light')['marker.color']
assert.equal(new Set([blue, rose, light]).size, 3)

console.log('Épica de auditoría Dashito: 10 frentes verificados sin alterar el contenido Legacy.')
