import { SNAPSHOT_CUTOFF } from './catalog'

const REMOTE = {
  risk: 'https://raw.githubusercontent.com/maximilianozurita/arg-financial-data/main/data/financiero/riesgo_pais_embi.csv',
  bigmac: 'https://raw.githubusercontent.com/TheEconomist/big-mac-data/master/output-data/big-mac-full-index.csv',
}

function parseCsv(text) {
  const rows = []
  let row = []
  let field = ''
  let quoted = false
  for (let index = 0; index < text.length; index += 1) {
    const char = text[index]
    if (char === '"' && text[index + 1] === '"' && quoted) { field += '"'; index += 1 }
    else if (char === '"') quoted = !quoted
    else if (char === ',' && !quoted) { row.push(field); field = '' }
    else if ((char === '\n' || char === '\r') && !quoted) {
      if (char === '\r' && text[index + 1] === '\n') index += 1
      row.push(field); field = ''
      if (row.some(Boolean)) rows.push(row)
      row = []
    } else field += char
  }
  if (field || row.length) { row.push(field); rows.push(row) }
  const headers = rows.shift() || []
  return rows.map((values) => Object.fromEntries(headers.map((header, index) => [header, values[index] ?? ''])))
}

function median(values) {
  const sorted = values.map(Number).filter(Number.isFinite).sort((a, b) => a - b)
  if (!sorted.length) return null
  const middle = Math.floor(sorted.length / 2)
  return sorted.length % 2 ? sorted[middle] : (sorted[middle - 1] + sorted[middle]) / 2
}

export async function fetchRiskSource(signal) {
  const response = await fetch(REMOTE.risk, { signal })
  if (!response.ok) throw new Error('No se pudo cargar la serie EMBI+.')
  const rows = parseCsv(await response.text()).filter((row) => row.fecha >= '2002-01-01' && row.fecha <= SNAPSHOT_CUTOFF && Number.isFinite(Number(row.valor)))
  const groups = new Map()
  rows.forEach((row) => {
    const month = row.fecha.slice(0, 7)
    groups.set(month, [...(groups.get(month) || []), Number(row.valor)])
  })
  const labels = [...groups.keys()].sort()
  return { labels, series: [{ name: 'EMBI+ · mediana mensual', values: labels.map((label) => median(groups.get(label))) }] }
}

export async function fetchBigMacSource(signal) {
  const response = await fetch(REMOTE.bigmac, { signal })
  if (!response.ok) throw new Error('No se pudo cargar el índice Big Mac.')
  const rows = parseCsv(await response.text()).filter((row) => row.iso_a3 === 'ARG' && row.date >= '2002-01-01' && row.date <= SNAPSHOT_CUTOFF)
  return {
    labels: rows.map((row) => row.date),
    series: [
      { name: 'Raw USD', values: rows.map((row) => Number(row.USD_raw) * 100) },
      { name: 'Ajustado por PIB', values: rows.map((row) => row.USD_adjusted === '' ? null : Number(row.USD_adjusted) * 100) },
    ],
  }
}

export const remoteSources = { risk: fetchRiskSource, bigmac: fetchBigMacSource }

