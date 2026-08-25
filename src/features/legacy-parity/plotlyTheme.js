// Paletas categóricas validadas (dataviz: banda de luminosidad OKLCH, piso de
// croma, separación CVD protan/deutan y visión normal) contra la superficie de
// cada skin. Orden fijo de series: ámbar · cian · verde · índigo · magenta ·
// violeta · naranja · teal · rojo. El 9º (rojo) se sumó para series con más de
// ocho trazas; se distingue en uso por trazo (dash) además del tono. Los tonos
// favorable/desfavorable reusan los tokens --mint/--negative de cada skin,
// reforzados con el signo +$/−$ en la lectura.
export const plotlyThemePalettes = {
  'blue-dark': {
    series: ['#b28d00', '#12a0cf', '#12a466', '#6a68ff', '#dd2f86', '#b552e6', '#cf7000', '#0f9795', '#f2596b'],
    positive: '#34d399',
    negative: '#fb7185',
  },
  'rose-dark': {
    series: ['#9d7c00', '#008db7', '#00995c', '#6866ff', '#e50085', '#bb00fa', '#be6600', '#009391', '#ff6f61'],
    positive: '#5eead4',
    negative: '#f43f5e',
  },
  'rose-light': {
    series: ['#8b6d00', '#007399', '#a15500', '#008a7f', '#5122ff', '#b5005e', '#9500c0', '#007d4d', '#c62828'],
    positive: '#0f766e',
    negative: '#be123c',
  },
}

function colorsEqual(current, next) {
  if (Array.isArray(current) && Array.isArray(next)) return current.length === next.length && current.every((value, index) => value === next[index])
  return current === next
}

function categoricalColors(values, palette) {
  const assigned = new Map()
  return values.map((value) => {
    const key = String(value)
    if (!assigned.has(key)) assigned.set(key, palette.series[assigned.size % palette.series.length])
    return assigned.get(key)
  })
}

function markerColors(trace, fallback, palette) {
  const current = trace?.marker?.color
  if (!Array.isArray(current) && !ArrayBuffer.isView(current)) return fallback
  const original = Array.from(current)
  const y = Array.from(trace?.y || []).map(Number)
  const hasPositive = y.some((value) => Number.isFinite(value) && value >= 0)
  const hasNegative = y.some((value) => Number.isFinite(value) && value < 0)
  if (y.length === original.length && hasPositive && hasNegative) {
    return y.map((value) => value < 0 ? palette.negative : palette.positive)
  }
  return categoricalColors(original, palette)
}

export function desiredTraceTheme(trace, index, theme) {
  const palette = plotlyThemePalettes[theme] || plotlyThemePalettes['blue-dark']
  const fallback = palette.series[index % palette.series.length]
  const update = {}
  const type = trace?.type || 'scatter'
  const lineTypes = new Set(['scatter', 'scattergl', 'box', 'violin'])
  const markerTypes = new Set(['scatter', 'scattergl', 'bar', 'box', 'violin', 'histogram'])
  if (lineTypes.has(type)) update['line.color'] = fallback
  if (markerTypes.has(type)) update['marker.color'] = markerColors(trace, fallback, palette)
  if (trace?.fill && trace.fill !== 'none') update.fillcolor = `${fallback}24`
  if (type === 'pie') {
    const count = Array.from(trace.labels || trace.values || []).length
    update['marker.colors'] = Array.from({ length: count }, (_, colorIndex) => palette.series[colorIndex % palette.series.length])
  }
  return update
}

export function applyPlotlyTheme(chart, theme) {
  if (!window.Plotly || !chart?.data) return false
  if (chart.dataset.dashitoPalette === theme) return false
  let changed = false
  chart.data.forEach((trace, index) => {
    const desired = desiredTraceTheme(trace, index, theme)
    const update = {}
    for (const [path, value] of Object.entries(desired)) {
      const current = path.split('.').reduce((target, property) => target?.[property], trace)
      if (!colorsEqual(current, value)) update[path] = value
    }
    if (Object.keys(update).length) {
      window.Plotly.restyle(chart, update, [index])
      changed = true
    }
  })
  chart.dataset.dashitoPalette = theme
  return changed
}
