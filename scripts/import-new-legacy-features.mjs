import { mkdirSync, readFileSync, writeFileSync } from 'node:fs'
import { dirname, resolve } from 'node:path'

const projectRoot = resolve(import.meta.dirname, '..')
const legacyRoot = resolve(projectRoot, '..', 'Legacy', 'inflacion', 'data', 'derivados')
const outputPath = resolve(projectRoot, 'src', 'data', 'generated', 'new-tabs-data.json')

const files = {
  morosidadHogares: 'morosidad/morosidad_hogares.csv',
  morosidadProductos: 'morosidad/morosidad_por_producto.csv',
  morosidadPnfc: 'morosidad/morosidad_pnfc.csv',
  morosidadVentanas: 'morosidad/morosidad_ventana_espejo.csv',
  morosidadSaldo: 'morosidad/morosidad_saldo_acumulado.csv',
  morosidadPersonas: 'morosidad/situacion_deudores_personas.csv',
  morosidadCorrelacion: 'morosidad/correlacion_tasa_real_mora.csv',
  penduloSerie: 'pendulo_distributivo/cgi_pendulo.csv',
  penduloMandatos: 'pendulo_distributivo/cgi_mandatos.csv',
  emaeMensual: 'emae/emae_mensual_limpio.csv',
  emaeMandatos: 'emae/emae_mandatos.csv',
  emaeVentana: 'emae/emae_ventana_espejo.csv',
  emaeDrawdowns: 'emae/emae_drawdowns.csv',
}

function parseCsv(text) {
  const rows = []
  let row = []
  let field = ''
  let quoted = false
  for (let index = 0; index < text.length; index += 1) {
    const char = text[index]
    if (char === '"' && quoted && text[index + 1] === '"') { field += '"'; index += 1 }
    else if (char === '"') quoted = !quoted
    else if (char === ',' && !quoted) { row.push(field); field = '' }
    else if ((char === '\n' || char === '\r') && !quoted) {
      if (char === '\r' && text[index + 1] === '\n') index += 1
      row.push(field)
      if (row.some((value) => value !== '')) rows.push(row)
      row = []
      field = ''
    } else field += char
  }
  if (field || row.length) { row.push(field); rows.push(row) }
  const headers = (rows.shift() || []).map((header) => header.replace(/^\uFEFF/, '').trim())
  return rows.map((values) => Object.fromEntries(headers.map((header, index) => [header, parseValue(values[index] ?? '')])))
}

function parseValue(value) {
  const trimmed = value.trim()
  if (!trimmed) return null
  if (/^-?(?:\d+\.?\d*|\.\d+)(?:e[+-]?\d+)?$/i.test(trimmed)) return Number(trimmed)
  return trimmed
}

const output = Object.fromEntries(Object.entries(files).map(([key, relativePath]) => {
  const path = resolve(legacyRoot, relativePath)
  return [key, parseCsv(readFileSync(path, 'utf8'))]
}))

mkdirSync(dirname(outputPath), { recursive: true })
writeFileSync(outputPath, `${JSON.stringify(output)}\n`, 'utf8')
console.log(`Tabs nuevos importados: ${Object.keys(output).length} datasets`)
Object.entries(output).forEach(([key, rows]) => console.log(`${key}: ${rows.length} filas`))
