import { useId, useMemo, useState } from 'react'

const WIDTH = 1000
const HEIGHT = 380
const PADDING = { top: 28, right: 24, bottom: 48, left: 64 }
const chartColors = Array.from({ length: 8 }, (_, index) => `var(--chart-${index + 1})`)

function finiteValues(series) {
  return series.flatMap((item) => item.values || []).map(Number).filter(Number.isFinite)
}

function extent(series, explicitMin, explicitMax) {
  const values = finiteValues(series)
  const hasExplicitMin = Number.isFinite(explicitMin)
  const hasExplicitMax = Number.isFinite(explicitMax)
  let min = hasExplicitMin ? explicitMin : Math.min(...values)
  let max = hasExplicitMax ? explicitMax : Math.max(...values)
  if (!Number.isFinite(min) || !Number.isFinite(max)) return [0, 1]
  if (min === max) { min -= 1; max += 1 }
  const padding = (max - min) * .08
  return [hasExplicitMin ? min : min - padding, hasExplicitMax ? max : max + padding]
}

function compact(value) {
  const number = Number(value)
  if (!Number.isFinite(number)) return 's/d'
  if (Math.abs(number) >= 1_000_000) return `${(number / 1_000_000).toLocaleString('es-AR', { maximumFractionDigits: 1 })} M`
  if (Math.abs(number) >= 1_000) return `${(number / 1_000).toLocaleString('es-AR', { maximumFractionDigits: 1 })} k`
  return number.toLocaleString('es-AR', { maximumFractionDigits: Math.abs(number) < 1 ? 2 : 1 })
}

function sampleIndexes(length, maxPoints = 150) {
  if (length <= maxPoints) return Array.from({ length }, (_, index) => index)
  const indexes = []
  for (let index = 0; index < maxPoints; index += 1) indexes.push(Math.round(index * (length - 1) / (maxPoints - 1)))
  return [...new Set(indexes)]
}

export function ChartLegend({ series }) {
  return <div className="chart-legend">{series.map((item, index) => <span key={`${item.name}-${index}`}><i style={{ background: chartColors[index % chartColors.length] }} />{item.name}</span>)}</div>
}

export function LineChart({ labels = [], series = [], min, max, valueSuffix = '', ariaLabel = 'Gráfico de líneas' }) {
  const id = useId().replaceAll(':', '')
  const [hoverIndex, setHoverIndex] = useState(null)
  const indexes = useMemo(() => sampleIndexes(labels.length), [labels.length])
  const [low, high] = extent(series, min, max)
  const innerWidth = WIDTH - PADDING.left - PADDING.right
  const innerHeight = HEIGHT - PADDING.top - PADDING.bottom
  const x = (index) => PADDING.left + (labels.length <= 1 ? 0 : index / (labels.length - 1)) * innerWidth
  const y = (value) => PADDING.top + (1 - (Number(value) - low) / (high - low)) * innerHeight
  const paths = series.map((item) => {
    let path = ''
    let drawing = false
    indexes.forEach((index) => {
      const value = Number(item.values?.[index])
      if (!Number.isFinite(value)) { drawing = false; return }
      path += `${drawing ? 'L' : 'M'}${x(index).toFixed(2)},${y(value).toFixed(2)} `
      drawing = true
    })
    return path.trim()
  })
  const ticks = Array.from({ length: 5 }, (_, index) => low + (high - low) * index / 4)
  const labelIndexes = [0, Math.floor((labels.length - 1) / 2), labels.length - 1].filter((value, index, self) => value >= 0 && self.indexOf(value) === index)
  const hoveredValues = hoverIndex == null ? [] : series.map((item, seriesIndex) => ({ name: item.name, value: Number(item.values?.[hoverIndex]), color: chartColors[seriesIndex % chartColors.length] })).filter((item) => Number.isFinite(item.value))
  const tooltipWidth = 270
  const tooltipHeight = 32 + hoveredValues.length * 19
  const tooltipX = hoverIndex == null ? 0 : Math.min(Math.max(x(hoverIndex) - tooltipWidth / 2, PADDING.left), WIDTH - PADDING.right - tooltipWidth)

  return <figure className="chart" aria-label={ariaLabel}>
    <ChartLegend series={series} />
    <svg viewBox={`0 0 ${WIDTH} ${HEIGHT}`} role="img" aria-labelledby={`${id}-title`} onMouseLeave={() => setHoverIndex(null)}>
      <title id={`${id}-title`}>{ariaLabel}</title>
      <defs><clipPath id={`${id}-clip`}><rect x={PADDING.left} y={PADDING.top} width={innerWidth} height={innerHeight} /></clipPath></defs>
      {ticks.map((tick) => <g key={tick}><line className="chart-grid" x1={PADDING.left} x2={WIDTH - PADDING.right} y1={y(tick)} y2={y(tick)} /><text className="chart-axis-label" x={PADDING.left - 12} y={y(tick) + 4} textAnchor="end">{compact(tick)}{valueSuffix}</text></g>)}
      <line className="chart-axis" x1={PADDING.left} x2={WIDTH - PADDING.right} y1={HEIGHT - PADDING.bottom} y2={HEIGHT - PADDING.bottom} />
      {labelIndexes.map((index) => <text key={index} className="chart-axis-label" x={x(index)} y={HEIGHT - 17} textAnchor={index === 0 ? 'start' : index === labels.length - 1 ? 'end' : 'middle'}>{String(labels[index] ?? '').slice(0, 12)}</text>)}
      <g clipPath={`url(#${id}-clip)`}>{paths.map((path, index) => <path key={`${series[index]?.name}-${index}`} d={path} fill="none" stroke={chartColors[index % chartColors.length]} strokeWidth={series[index]?.emphasis ? 4 : 2.8} strokeDasharray={series[index]?.dashed ? '8 7' : undefined} vectorEffect="non-scaling-stroke" />)}</g>
      <g className="chart-hit-zones">{indexes.map((index, sampledIndex) => { const previous = indexes[sampledIndex - 1]; const next = indexes[sampledIndex + 1]; const left = previous == null ? PADDING.left : (x(previous) + x(index)) / 2; const right = next == null ? WIDTH - PADDING.right : (x(index) + x(next)) / 2; return <rect key={index} x={left} y={PADDING.top} width={Math.max(2, right - left)} height={innerHeight} fill="transparent" tabIndex={sampledIndex % Math.max(1, Math.ceil(indexes.length / 24)) === 0 ? 0 : undefined} onMouseEnter={() => setHoverIndex(index)} onFocus={() => setHoverIndex(index)} onTouchStart={() => setHoverIndex(index)}><title>{`${labels[index]} · ${series.map((item) => `${item.name}: ${compact(item.values?.[index])}${valueSuffix}`).join(' · ')}`}</title></rect> })}</g>
      {hoverIndex != null && hoveredValues.length ? <g className="chart-tooltip" transform={`translate(${tooltipX},${PADDING.top + 5})`} pointerEvents="none"><rect className="chart-tooltip__box" width={tooltipWidth} height={tooltipHeight} rx="7" /><text className="chart-tooltip__title" x="12" y="20">{String(labels[hoverIndex]).slice(0, 28)}</text>{hoveredValues.map((item, index) => <g key={`${item.name}-${index}`} transform={`translate(12,${37 + index * 19})`}><circle r="4" cy="-3" fill={item.color} /><text className="chart-tooltip__text" x="10">{`${String(item.name).slice(0, 25)}: ${compact(item.value)}${valueSuffix}`}</text></g>)}</g> : null}
    </svg>
  </figure>
}

export function BarChart({ labels = [], series = [], horizontal = false, valueSuffix = '', ariaLabel = 'Gráfico de barras' }) {
  if (horizontal) return <HorizontalBarChart labels={labels} series={series} valueSuffix={valueSuffix} ariaLabel={ariaLabel} />
  const allValues = finiteValues(series)
  const low = Math.min(0, ...allValues)
  const high = Math.max(1, ...allValues)
  const innerWidth = WIDTH - PADDING.left - PADDING.right
  const innerHeight = HEIGHT - PADDING.top - PADDING.bottom
  const groups = Math.max(labels.length, 1)
  const groupWidth = innerWidth / groups
  const barWidth = Math.min(62, groupWidth * .72 / Math.max(series.length, 1))
  const y = (value) => PADDING.top + (1 - (Number(value) - low) / (high - low)) * innerHeight
  const zeroY = y(0)
  const labelEvery = Math.max(1, Math.ceil(labels.length / 8))
  return <figure className="chart" aria-label={ariaLabel}>
    <ChartLegend series={series} />
    <svg viewBox={`0 0 ${WIDTH} ${HEIGHT}`} role="img">
      {[0, .25, .5, .75, 1].map((ratio) => { const value = low + (high - low) * ratio; return <g key={ratio}><line className="chart-grid" x1={PADDING.left} x2={WIDTH - PADDING.right} y1={y(value)} y2={y(value)} /><text className="chart-axis-label" x={PADDING.left - 12} y={y(value) + 4} textAnchor="end">{compact(value)}{valueSuffix}</text></g> })}
      {series.flatMap((item, seriesIndex) => labels.map((_, index) => {
        const value = Number(item.values?.[index])
        if (!Number.isFinite(value)) return null
        const center = PADDING.left + groupWidth * index + groupWidth / 2
        const offset = (seriesIndex - (series.length - 1) / 2) * barWidth
        const top = value >= 0 ? y(value) : zeroY
        return <rect key={`${seriesIndex}-${index}`} x={center + offset - barWidth * .44} y={top} width={barWidth * .88} height={Math.max(1, Math.abs(y(value) - zeroY))} rx="4" fill={chartColors[seriesIndex % chartColors.length]}><title>{`${labels[index]} · ${item.name}: ${compact(value)}${valueSuffix}`}</title></rect>
      }))}
      {labels.map((label, index) => index % labelEvery === 0 || index === labels.length - 1 ? <text key={`${label}-${index}`} className="chart-axis-label" x={PADDING.left + groupWidth * index + groupWidth / 2} y={HEIGHT - 17} textAnchor="middle">{String(label).slice(0, 11)}</text> : null)}
    </svg>
  </figure>
}

function HorizontalBarChart({ labels, series, valueSuffix, ariaLabel }) {
  const values = series[0]?.values || []
  const max = Math.max(1, ...values.map((value) => Math.abs(Number(value) || 0)))
  return <figure className="chart chart--horizontal" aria-label={ariaLabel}>
    {labels.map((label, index) => {
      const value = Number(values[index]) || 0
      return <div className="hbar" key={`${label}-${index}`}><div className="hbar__top"><span>{label}</span><strong>{compact(value)}{valueSuffix}</strong></div><div className="hbar__track"><i style={{ width: `${Math.max(2, Math.abs(value) / max * 100)}%`, background: value < 0 ? 'var(--negative)' : chartColors[index % chartColors.length] }} /></div></div>
    })}
  </figure>
}

export function StackedBarChart({ labels = [], series = [], valueSuffix = '%', ariaLabel = 'Gráfico de barras apiladas' }) {
  return <figure className="chart chart--stacked" aria-label={ariaLabel}>
    <ChartLegend series={series} />
    <div className="stacked-list">{labels.map((label, index) => {
      const total = series.reduce((sum, item) => sum + (Number(item.values?.[index]) || 0), 0) || 1
      return <div className="stacked-row" key={`${label}-${index}`}><span>{label}</span><div>{series.map((item, seriesIndex) => { const value = Number(item.values?.[index]) || 0; return <i key={`${item.name}-${seriesIndex}`} title={`${item.name}: ${compact(value)}${valueSuffix}`} style={{ width: `${Math.max(0, value / total * 100)}%`, background: chartColors[seriesIndex % chartColors.length] }} /> })}</div><strong>{compact(total)}{valueSuffix}</strong></div>
    })}</div>
  </figure>
}
