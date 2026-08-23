import { useEffect, useMemo, useRef, useState } from 'react'
import { createPortal } from 'react-dom'
import { chartAudit } from './chartAudit'
import { applyPlotlyTheme } from './plotlyTheme'

const annotationReflowCharts = new Set([
  'investmentChart', 'powerChart', 'nominalChart', 'realChart', 'socialLongChart',
  'povertyChart', 'giniChart', 'consumptionChart', 'growthChart', 'workChart',
  'wholesaleChart', 'bigMacChart',
])

function tickValues(min, max) {
  if (!(min > 0) || !(max > min)) return []
  const values = []
  const start = Math.floor(Math.log10(min))
  const end = Math.ceil(Math.log10(max))
  for (let exponent = start; exponent <= end; exponent += 1) {
    for (const factor of [1, 2, 5]) {
      const value = factor * (10 ** exponent)
      if (value >= min * .98 && value <= max * 1.02) values.push(value)
    }
  }
  return values
}

function formatTick(value, axis) {
  const formatted = new Intl.NumberFormat('es-AR', { maximumFractionDigits: 2, maximumSignificantDigits: 4 }).format(value)
  return `${axis?.tickprefix || ''}${formatted}${axis?.ticksuffix || ''}`
}

function allowPowerPrimaryLog(audit) {
  const axes = audit.axes.map((axis) => axis.key === 'yaxis' && axis.min > 0
    ? {
        ...axis,
        eligible: true,
        classification: axis.classification === 'recommended' ? 'recommended' : 'optional',
        reason: axis.classification === 'recommended'
          ? axis.reason
          : 'comparación proporcional opcional para la serie histórica de índices',
      }
    : axis)
  return { ...audit, axes, eligibleAxes: axes.filter((axis) => axis.eligible) }
}

function captureAxisState(axis = {}) {
  return {
    type: axis.type,
    autorange: axis.autorange,
    range: Array.isArray(axis.range) ? [...axis.range] : axis.range,
    tickmode: axis.tickmode,
    tickvals: Array.isArray(axis.tickvals) ? [...axis.tickvals] : axis.tickvals,
    ticktext: Array.isArray(axis.ticktext) ? [...axis.ticktext] : axis.ticktext,
    tickprefix: axis.tickprefix,
    ticksuffix: axis.ticksuffix,
  }
}

function reflowNominalAnnotations(annotations = [], chartWidth = 0) {
  const compact = chartWidth > 0 && chartWidth < 1200
  return annotations.map((annotation) => {
    const text = String(annotation?.text || '')
    if (text.includes('Diciembre 2023') || (text.includes('dic-23') && text.includes('+25,5%'))) {
      return {
        ...annotation,
        ax: compact ? 52 : 68,
        ay: compact ? -84 : -72,
        xanchor: 'left',
        align: 'left',
      }
    }
    if (text.includes('Hasta 30/11/2023') || (text.includes('ene–nov') && text.includes('148,1%'))) {
      return {
        ...annotation,
        ax: compact ? -86 : -74,
        ay: compact ? 50 : 38,
        xanchor: 'right',
        align: 'left',
      }
    }
    if ((text.includes('10/12/2023') && text.includes('asume Milei')) || (text.includes('10/12') && text.includes('Milei'))) {
      return {
        ...annotation,
        y: compact ? .76 : .79,
        ax: compact ? 54 : 62,
        ay: compact ? 18 : 10,
        xanchor: 'left',
        align: 'left',
      }
    }
    if (text.includes('Franjas = mandatos')) {
      return {
        ...annotation,
        x: compact ? .37 : .43,
        y: compact ? 1.025 : 1.03,
        font: { ...annotation.font, size: compact ? 9 : 10 },
      }
    }
    if (text.includes('Fintech PNFC desde abr-2019')) {
      return {
        ...annotation,
        y: compact ? .94 : .97,
        font: { ...annotation.font, size: compact ? 9 : 11 },
      }
    }
    return annotation
  })
}

function reflowPowerAnnotations(annotations = [], chartWidth = 0) {
  const compact = chartWidth > 0 && chartWidth < 1200
  const staggerPresidents = chartWidth > 0 && chartWidth <= 960
  const presidents = [
    'Eduardo Duhalde', 'Néstor Kirchner', 'Cristina Fernández',
    'Mauricio Macri', 'Alberto Fernández', 'Javier Milei',
  ]

  return annotations.map((annotation) => {
    const text = String(annotation?.text || '')
    const presidentIndex = presidents.findIndex((president) => text.includes(president))
    if (presidentIndex >= 0) {
      return {
        ...annotation,
        y: staggerPresidents ? (presidentIndex % 2 ? 1.17 : 1.105) : compact ? 1.105 : 1.095,
        yanchor: 'bottom',
      }
    }
    if (text.includes('Franjas = mandatos')) {
      return {
        ...annotation,
        x: compact ? .42 : .46,
        y: compact ? 1.035 : 1.03,
        yanchor: 'bottom',
        font: { ...annotation.font, size: compact ? 8 : 9 },
      }
    }
    if (text.includes('pandemia 2020–2021') || text.includes('pandemia\n2020–2021')) {
      return {
        ...annotation,
        y: compact ? .895 : .91,
        yanchor: 'top',
      }
    }
    if (text.includes('base = 100')) {
      return {
        ...annotation,
        y: compact ? .965 : .975,
        xanchor: 'right',
        yanchor: 'top',
        align: 'right',
        font: { ...annotation.font, size: compact ? 9 : 10 },
      }
    }
    if (text.includes('espejo') && text.includes('<b>+')) {
      return {
        ...annotation,
        ax: compact ? -62 : -54,
        ay: compact ? 58 : 50,
        xanchor: 'right',
        yanchor: 'top',
        align: 'right',
      }
    }
    if (text.includes('saldo perdido')) {
      return {
        ...annotation,
        ax: compact ? -72 : -60,
        ay: compact ? 42 : 34,
        xanchor: 'right',
        align: 'right',
      }
    }
    return annotation
  })
}

function annotationPositions(annotations = []) {
  return annotations.map(({ text, x, y, ax, ay, xanchor, yanchor, align, font }) => ({
    text, x, y, ax, ay, xanchor, yanchor, align, fontSize: font?.size,
  }))
}

function syncNominalAnnotationLayout(chart) {
  if (chart.id !== 'nominalChart' || chart.clientWidth <= 720 || chart.dataset.dashitoAnnotationRelayout === 'true') return
  const current = chart.layout?.annotations || []
  const next = reflowNominalAnnotations(current, chart.clientWidth)
  if (JSON.stringify(annotationPositions(current)) === JSON.stringify(annotationPositions(next))) return
  chart.dataset.dashitoAnnotationRelayout = 'true'
  Promise.resolve(window.Plotly.relayout(chart, { annotations: next }))
    .finally(() => { delete chart.dataset.dashitoAnnotationRelayout })
}

function syncPowerAnnotationLayout(chart, { externalLegend = false } = {}) {
  if (chart.id !== 'powerChart' || chart.dataset.dashitoPowerAnnotationRelayout === 'true') return
  const current = chart.layout?.annotations || []
  const next = window.innerWidth <= 720 ? current : reflowPowerAnnotations(current, chart.clientWidth)
  const targetTopMargin = externalLegend
    ? (window.innerWidth <= 720 ? 96 : chart.clientWidth <= 960 ? 136 : 112)
    : chart.clientWidth < 1200 ? 196 : 176
  const positionsMatch = JSON.stringify(annotationPositions(current)) === JSON.stringify(annotationPositions(next))
  const showLegend = !externalLegend
  if (positionsMatch && chart.layout?.margin?.t === targetTopMargin && chart.layout?.showlegend === showLegend) return
  chart.dataset.dashitoPowerAnnotationRelayout = 'true'
  Promise.resolve(window.Plotly.relayout(chart, { annotations: next, 'margin.t': targetTopMargin, showlegend: showLegend }))
    .finally(() => { delete chart.dataset.dashitoPowerAnnotationRelayout })
}

function ScaleControl({ chart, axes, blockedAxes = [], axisCount = axes.length }) {
  const [scale, setScale] = useState('linear')
  const [pending, setPending] = useState(false)
  const originalAxes = useRef(null)
  const signature = axes.map((axis) => `${axis.key}:${axis.min}:${axis.max}`).join('|')

  useEffect(() => {
    setScale('linear')
    originalAxes.current = null
  }, [signature])

  const apply = async (nextScale) => {
    if (!window.Plotly || !chart?.data || pending || nextScale === scale) return
    if (!originalAxes.current) {
      originalAxes.current = Object.fromEntries(axes.map(({ key }) => [key, captureAxisState(chart.layout?.[key])]))
    }
    const update = {}
    for (const axisAudit of axes) {
      const key = axisAudit.key
      const original = originalAxes.current[key] || {}
      if (nextScale === 'log') {
        const values = tickValues(axisAudit.min, axisAudit.max)
        update[`${key}.type`] = 'log'
        update[`${key}.autorange`] = true
        update[`${key}.range`] = null
        update[`${key}.tickmode`] = 'array'
        update[`${key}.tickvals`] = values
        update[`${key}.ticktext`] = values.map((value) => formatTick(value, original))
      } else {
        update[`${key}.type`] = original.type || 'linear'
        update[`${key}.autorange`] = original.autorange ?? !original.range
        update[`${key}.range`] = original.range || null
        update[`${key}.tickmode`] = original.tickmode || 'auto'
        update[`${key}.tickvals`] = original.tickvals || null
        update[`${key}.ticktext`] = original.ticktext || null
      }
    }
    setPending(true)
    chart.dataset.dashitoScaleBusy = 'true'
    try {
      await window.Plotly.relayout(chart, update)
      setScale(nextScale)
    } finally {
      delete chart.dataset.dashitoScaleBusy
      setPending(false)
    }
  }

  const eligibleDescription = axes
    .map((axis) => `${axis.label}: ${axis.classification === 'recommended' ? 'log recomendable' : 'log opcional'} (${axis.reason})`)
    .join('. ')
  const blockedDescription = blockedAxes.length
    ? ` ${blockedAxes.map((axis) => `${axis.label}: permanece lineal porque ${axis.reason}`).join('. ')}.`
    : ''
  const onlyPrimaryAxis = axisCount > 1 && axes.length === 1 && axes[0].key === 'yaxis'
  const controlLabel = onlyPrimaryAxis ? 'Escala eje izquierdo' : axes.length > 1 ? 'Escala ejes Y' : 'Escala Y'
  return <div className="legacy-scale-control" aria-label={`${controlLabel} del gráfico`}>
    <span>{controlLabel}</span>
    <div role="group" aria-label={`Elegir ${controlLabel.toLocaleLowerCase('es-AR')}`}>
      <button type="button" disabled={pending} aria-pressed={scale === 'linear'} onClick={() => apply('linear')}>Lineal</button>
      <button type="button" disabled={pending} aria-pressed={scale === 'log'} onClick={() => apply('log')}>Log</button>
    </div>
    <span className="legacy-scale-help" tabIndex="0" title={`Escala logarítmica: cambia la representación proporcional, no los datos ni sus valores emergentes. ${eligibleDescription}.${blockedDescription}`}>ⓘ</span>
  </div>
}

function legendStrokeStyle(dash) {
  if (dash === 'dot') return 'dotted'
  if (dash && dash !== 'solid') return 'dashed'
  return 'solid'
}

function ExternalLegend({ chart, items }) {
  const [hiddenGroups, setHiddenGroups] = useState(() => new Set(items.filter((item) => !item.visible).map((item) => item.key)))

  useEffect(() => {
    setHiddenGroups(new Set(items.filter((item) => !item.visible).map((item) => item.key)))
  }, [items])

  const toggle = async (item) => {
    if (!window.Plotly || chart.dataset.dashitoLegendBusy === 'true') return
    const hide = !hiddenGroups.has(item.key)
    chart.dataset.dashitoLegendBusy = 'true'
    try {
      await window.Plotly.restyle(chart, { visible: hide ? 'legendonly' : true }, item.traceIndices)
      setHiddenGroups((current) => {
        const next = new Set(current)
        if (hide) next.add(item.key)
        else next.delete(item.key)
        return next
      })
    } finally {
      delete chart.dataset.dashitoLegendBusy
    }
  }

  return <div className="legacy-external-legend" aria-label="Series del gráfico">
    {items.map((item) => <button
      type="button"
      key={item.key}
      className={hiddenGroups.has(item.key) ? 'is-hidden' : ''}
      aria-pressed={!hiddenGroups.has(item.key)}
      onClick={() => toggle(item)}
    >
      <i style={{ borderTopColor: item.color, borderTopStyle: legendStrokeStyle(item.dash) }} />
      <span>{item.name}</span>
    </button>)}
  </div>
}

function AnnotationList({ annotations }) {
  if (annotations.length < 4) return null
  return <details className="legacy-mobile-annotations">
    <summary>Hitos y anotaciones del gráfico</summary>
    <ul>{annotations.map((annotation) => <li key={`${annotation.x}-${annotation.text}`}><span>{annotation.x}</span>{annotation.text}</li>)}</ul>
  </details>
}

function ScaleTools({ entry }) {
  const audit = entry.audit
  return <div className="legacy-chart-tools">
    <ScaleControl
      chart={entry.chart}
      axes={audit.eligibleAxes}
      blockedAxes={audit.axes.filter((axis) => !axis.eligible)}
      axisCount={audit.axes.length}
    />
  </div>
}

function AnnotationTools({ entry }) {
  return <div className="legacy-chart-tools legacy-chart-tools--annotations">
    <AnnotationList annotations={entry.audit.annotations} />
  </div>
}

function externalLegendItems(chart) {
  return (chart.data || []).flatMap((trace, index) => {
    if (trace?.showlegend === false) return []
    const group = trace?.legendgroup || `trace-${index}`
    const traceIndices = chart.data.reduce((indices, candidate, candidateIndex) => {
      const candidateGroup = candidate?.legendgroup || `trace-${candidateIndex}`
      if (candidateGroup === group) indices.push(candidateIndex)
      return indices
    }, [])
    const visible = traceIndices.some((traceIndex) => chart.data[traceIndex]?.visible !== false && chart.data[traceIndex]?.visible !== 'legendonly')
    const color = trace?.line?.color || trace?.marker?.color || 'currentColor'
    return [{
      key: `${group}:${trace?.name || index}`,
      name: trace?.name || `Serie ${index + 1}`,
      traceIndices,
      visible,
      color: Array.isArray(color) ? color[0] : color,
      dash: trace?.line?.dash || 'solid',
    }]
  })
}

export default function LegacyChartEnhancements({ rootRef, activeId, ready, theme }) {
  const [entries, setEntries] = useState([])
  const hostsRef = useRef(new Map())
  const activeKey = useMemo(() => `${activeId}:${ready}`, [activeId, ready])

  useEffect(() => {
    if (!ready) return undefined
    const root = rootRef.current
    if (!root) return undefined

    const scan = () => {
      const next = []
      for (const chart of root.querySelectorAll('.js-plotly-plot')) {
        if (!chart.id || !chart.data || !chart.layout) continue
        applyPlotlyTheme(chart, theme)
        let hosts = hostsRef.current.get(chart)
        if (!hosts?.before?.isConnected || !hosts?.after?.isConnected) {
          hosts?.before?.remove()
          hosts?.after?.remove()
          const before = document.createElement('div')
          const after = document.createElement('div')
          before.className = 'legacy-chart-tools-host legacy-chart-tools-host--before'
          after.className = 'legacy-chart-tools-host legacy-chart-tools-host--after'
          chart.insertAdjacentElement('beforebegin', before)
          chart.insertAdjacentElement('afterend', after)
          hosts = { before, after }
          hostsRef.current.set(chart, hosts)
        }
        const audited = chartAudit(chart)
        const audit = chart.id === 'powerChart' ? allowPowerPrimaryLog(audited) : audited
        const externalLegend = chart.id === 'powerChart' && (window.innerWidth <= 720 || chart.clientWidth <= 960)
        syncNominalAnnotationLayout(chart)
        syncPowerAnnotationLayout(chart, { externalLegend })
        const legendItems = externalLegend ? externalLegendItems(chart) : []
        if (externalLegend) {
          chart.dataset.dashitoExternalLegend = 'true'
        } else if (chart.dataset.dashitoExternalLegend === 'true') {
          delete chart.dataset.dashitoExternalLegend
        }
        const reflow = annotationReflowCharts.has(chart.id) && audit.hasMobileAnnotationReflow
        if (reflow) chart.dataset.mobileAnnotationReflow = 'true'
        else delete chart.dataset.mobileAnnotationReflow
        const signature = JSON.stringify({
          axes: audit.axes.map(({ key, min, max, classification }) => ({ key, min, max, classification })),
          annotations: audit.annotations,
          externalLegend,
          legendItems,
          reflow,
        })
        next.push({ chart, hosts, audit, externalLegend, legendItems, reflow, signature })
      }
      for (const [chart, hosts] of hostsRef.current) {
        if (!chart.isConnected) {
          hosts.before.remove()
          hosts.after.remove()
          hostsRef.current.delete(chart)
        }
      }
      setEntries((current) => {
        const before = current.map((entry) => `${entry.chart.id}:${entry.signature}`).join('|')
        const after = next.map((entry) => `${entry.chart.id}:${entry.signature}`).join('|')
        return before === after ? current : next
      })
    }

    scan()
    const timer = window.setInterval(scan, 500)
    window.addEventListener('resize', scan)
    return () => {
      window.clearInterval(timer)
      window.removeEventListener('resize', scan)
    }
  }, [activeKey, ready, rootRef, theme])

  useEffect(() => () => {
    for (const hosts of hostsRef.current.values()) {
      hosts.before.remove()
      hosts.after.remove()
    }
    hostsRef.current.clear()
  }, [])

  return entries.flatMap((entry) => [
    entry.externalLegend
      ? createPortal(<ExternalLegend chart={entry.chart} items={entry.legendItems} />, entry.hosts.before, `chart-legend-${entry.chart.id}`)
      : null,
    entry.audit.eligibleAxes.length
      ? createPortal(<ScaleTools entry={entry} />, entry.hosts.before, `chart-scale-${entry.chart.id}`)
      : null,
    entry.reflow
      ? createPortal(<AnnotationTools entry={entry} />, entry.hosts.after, `chart-annotations-${entry.chart.id}`)
      : null,
  ]).filter(Boolean)
}
