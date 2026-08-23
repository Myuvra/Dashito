import { Download, ExternalLink, Heart, Info, Pin, Search, Sigma } from 'lucide-react'
import { BarChart, LineChart, StackedBarChart } from '../charts/Charts'
import { rowsToCsv } from '../../data/newFeatureData'

export function DashboardHero({ eyebrow, title, summary, badge, metrics = [] }) {
  return <section className="feature-hero">
    <div className="feature-hero__copy"><span className="feature-eyebrow">{eyebrow}</span><h1>{title}<Heart size={20} /></h1><p>{summary}</p></div>
    {badge ? <span className="feature-badge">{badge}</span> : null}
    {metrics.length ? <div className="metric-grid">{metrics.map((metric) => <MetricCard key={metric.label} {...metric} />)}</div> : null}
  </section>
}

export function MetricCard({ label, value, detail, tone = 'default' }) {
  return <article className={`metric-card tone-${tone}`}><span>{label}</span><strong>{value}</strong>{detail ? <small>{detail}</small> : null}</article>
}

export function SectionCard({ title, eyebrow, badge, children, wide = false, dense = false }) {
  return <section className={`feature-section ${wide ? 'feature-section--wide' : ''} ${dense ? 'feature-section--dense' : ''}`}>
    <header>{eyebrow ? <span>{eyebrow}</span> : null}<h2>{title}<Heart size={16} /></h2>{badge ? <small>{badge}</small> : null}</header>
    <div className="feature-section__body">{children}</div>
  </section>
}

export function Callout({ title, children, tone = 'info' }) {
  const Icon = tone === 'formula' ? Sigma : tone === 'pin' ? Pin : Info
  return <aside className={`callout callout--${tone}`}><Icon size={17} /><div>{title ? <strong>{title}</strong> : null}<div>{children}</div></div></aside>
}

export function FormulaGrid({ items = [] }) {
  return <div className="formula-grid">{items.map((item) => <article key={item.title}><span>{item.title}</span><code>{item.formula}</code><strong>{item.result}</strong>{item.note ? <small>{item.note}</small> : null}</article>)}</div>
}

export function DataTable({ columns = [], rows = [] }) {
  return <div className="data-table-wrap"><table className="data-table"><thead><tr>{columns.map((column) => <th key={column.key}>{column.label}</th>)}</tr></thead><tbody>{rows.map((row, rowIndex) => <tr key={row.id ?? rowIndex}>{columns.map((column) => <td key={column.key}>{column.render ? column.render(row) : row[column.key]}</td>)}</tr>)}</tbody></table></div>
}

export function SourcesPanel({ items = [], audit }) {
  return <section className="sources-panel"><h2><Search size={18} />Fuentes y auditoría</h2><div className="source-links">{items.map((item) => <a key={item.label} href={item.href} target="_blank" rel="noreferrer"><span>{item.label}</span><small>{item.detail}</small><ExternalLink size={13} /></a>)}</div>{audit ? <p>{audit}</p> : null}</section>
}

export function SegmentedControl({ label, value, options = [], onChange }) {
  return <div className="feature-control"><span>{label}</span><div className="segmented-control">{options.map((option) => <button key={option.value} type="button" className={value === option.value ? 'is-active' : ''} onClick={() => onChange(option.value)}>{option.label}</button>)}</div></div>
}

export function RelatedLinks({ title = 'Seguir leyendo', items = [], onNavigate }) {
  if (!items.length) return null
  return <nav className="related-links" aria-label={title}><strong>{title}</strong><div>{items.map((item) => <button key={item.id} type="button" onClick={() => onNavigate?.(item.id)}>{item.label}</button>)}</div></nav>
}

export function MethodDetails({ title = '¿Cómo calculamos este indicador?', children }) {
  return <details className="method-details"><summary>{title}</summary><div>{children}</div></details>
}

export function DownloadCsvButton({ rows, filename, children }) {
  const download = () => {
    const blob = new Blob([rowsToCsv(rows)], { type: 'text/csv;charset=utf-8' })
    const href = URL.createObjectURL(blob)
    const anchor = document.createElement('a')
    anchor.href = href
    anchor.download = filename
    anchor.click()
    URL.revokeObjectURL(href)
  }
  return <button className="download-button" type="button" onClick={download}><Download size={14} />{children}</button>
}

export function ChartForSection({ chart }) {
  if (!chart) return null
  if (chart.type === 'bar') return <BarChart {...chart} />
  if (chart.type === 'stacked') return <StackedBarChart {...chart} />
  return <LineChart {...chart} />
}
