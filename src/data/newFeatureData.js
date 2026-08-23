import raw from './generated/new-tabs-data.json'

const byDate = (left, right) => String(left.date ?? left.period).localeCompare(String(right.date ?? right.period), 'es')
const ordered = (rows = []) => [...rows].sort(byDate)

export const delinquencyData = Object.freeze({
  households: ordered(raw.morosidadHogares),
  products: ordered(raw.morosidadProductos),
  pnfc: ordered(raw.morosidadPnfc),
  mirrorWindows: raw.morosidadVentanas,
  cumulative: ordered(raw.morosidadSaldo),
  people: ordered(raw.morosidadPersonas),
  correlations: [...raw.morosidadCorrelacion].sort((left, right) => left.lag_months - right.lag_months),
})

export const distributionData = Object.freeze({
  series: ordered(raw.penduloSerie),
  mandates: raw.penduloMandatos,
})

export const activityData = Object.freeze({
  monthly: ordered(raw.emaeMensual),
  mandates: raw.emaeMandatos,
  mirrorWindow: [...raw.emaeVentana].sort((left, right) => left.relative_month - right.relative_month),
  drawdowns: raw.emaeDrawdowns,
})

export function rowsToCsv(rows = []) {
  if (!rows.length) return ''
  const headers = [...new Set(rows.flatMap(Object.keys))]
  const quote = (value) => {
    if (value == null) return ''
    const text = String(value)
    return /[",\n\r]/.test(text) ? `"${text.replaceAll('"', '""')}"` : text
  }
  return `${headers.join(',')}\n${rows.map((row) => headers.map((header) => quote(row[header])).join(',')).join('\n')}\n`
}

