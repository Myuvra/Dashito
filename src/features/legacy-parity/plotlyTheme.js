export const plotlyThemePalettes = {
  'blue-dark': {
    series: ['#38bdf8', '#818cf8', '#2dd4bf', '#fbbf24', '#f472b6', '#a78bfa', '#22c55e', '#fb7185'],
    positive: '#34d399',
    negative: '#fb7185',
  },
  'rose-dark': {
    series: ['#fb7185', '#fdba74', '#c4b5fd', '#5eead4', '#facc15', '#f472b6', '#67e8f9', '#a7f3d0'],
    positive: '#5eead4',
    negative: '#f43f5e',
  },
  'rose-light': {
    series: ['#be123c', '#6d28d9', '#0f766e', '#c2410c', '#1d4ed8', '#be185d', '#a16207', '#475569'],
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
