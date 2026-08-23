// Una escala logarítmica sólo mejora la lectura cuando el eje cubre, como
// mínimo, dos órdenes de magnitud. En rangos cortos de índices o porcentajes
// deforma visualmente variaciones que se entienden mejor en escala lineal.
const LOG_RATIO_MINIMUM = 100

function flattenNumeric(value) {
  if (value == null) return []
  if (Array.isArray(value) || ArrayBuffer.isView(value)) return Array.from(value).flatMap(flattenNumeric)
  const number = Number(value)
  return Number.isFinite(number) ? [number] : []
}

function axisKey(trace) {
  const reference = trace?.yaxis || 'y'
  return reference === 'y' ? 'yaxis' : `yaxis${reference.slice(1)}`
}

function titleText(axis = {}) {
  if (typeof axis.title === 'string') return axis.title
  return axis.title?.text || 'Eje Y'
}

export function auditPlotlyAxes(chart) {
  const byAxis = new Map()
  for (const trace of chart?.data || []) {
    if (trace?.visible === false || trace?.visible === 'legendonly') continue
    const key = axisKey(trace)
    const values = flattenNumeric(trace?.y)
    if (!byAxis.has(key)) byAxis.set(key, [])
    byAxis.get(key).push(...values)
  }

  return [...byAxis.entries()].map(([key, values]) => {
    const invalid = values.some((value) => value <= 0)
    const positives = values.filter((value) => value > 0)
    const min = positives.length ? Math.min(...positives) : null
    const max = positives.length ? Math.max(...positives) : null
    const ratio = min && max ? max / min : 0
    const eligible = values.length >= 3 && !invalid && ratio >= LOG_RATIO_MINIMUM
    return {
      key,
      label: titleText(chart?.layout?.[key]),
      min,
      max,
      ratio,
      eligible,
      classification: invalid ? 'linear' : ratio >= 100 ? 'recommended' : eligible ? 'optional' : 'linear',
      reason: invalid
        ? 'contiene cero o valores negativos'
        : eligible
          ? `rango ${ratio.toLocaleString('es-AR', { maximumFractionDigits: 1 })}×`
          : 'la dispersión no justifica escala logarítmica',
    }
  })
}

export function cleanAnnotationText(text) {
  return String(text || '')
    .replace(/<br\s*\/?>/gi, ' · ')
    .replace(/<[^>]+>/g, '')
    .replace(/\n/g, ' · ')
    .replace(/\s+/g, ' ')
    .trim()
}

export function chartAnnotationSummary(chart) {
  const annotations = chart?.layout?.annotations || []
  const result = []
  const seen = new Set()
  for (const annotation of annotations) {
    const text = cleanAnnotationText(annotation?.text)
    if (!text || text === '♡' || seen.has(text)) continue
    seen.add(text)
    result.push({ text, x: annotation?.x == null ? '' : String(annotation.x) })
  }
  return result
}

export function chartAudit(chart) {
  const axes = auditPlotlyAxes(chart)
  const annotations = chartAnnotationSummary(chart)
  return {
    axes,
    annotations,
    eligibleAxes: axes.filter((axis) => axis.eligible),
    hasMobileAnnotationReflow: annotations.length >= 4,
  }
}
