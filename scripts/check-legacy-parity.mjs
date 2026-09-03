import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'

// ────────────────────────────────────────────────────────────────────────────
// Test de paridad Legacy · DATA-DRIVEN
//
// Verifica que los artefactos importados reproduzcan FIELMENTE el source de
// verdad `Legacy/inflacion/index.html`. No codifica conteos fijos ni guards de
// versión: deriva la lista de tabs y de scripts del propio source/manifiesto.
// Regla: ante cualquier divergencia, manda el source.
// ────────────────────────────────────────────────────────────────────────────

const root = resolve(import.meta.dirname, '..')
const source = readFileSync(resolve(root, '..', 'railway-dashboard', 'index.html'), 'utf8')
const imported = readFileSync(resolve(root, 'public', 'legacy', 'tabs.html'), 'utf8')
const manifest = JSON.parse(readFileSync(resolve(root, 'src', 'data', 'generated', 'legacy-tabs-manifest.json'), 'utf8'))
const runtimeManifest = JSON.parse(readFileSync(resolve(root, 'src', 'data', 'generated', 'legacy-runtime-manifest.json'), 'utf8'))
const runtime = runtimeManifest.runtime
  .map((file) => readFileSync(resolve(root, 'public', 'legacy', file), 'utf8'))
  .join('\n')

function decodeText(value) {
  return value.replace(/<[^>]+>/g, ' ').replace(/&nbsp;/gi, ' ').replace(/&amp;/gi, '&').replace(/\s+/g, ' ').trim()
}
function sourceTabIds(documentHtml) {
  return [...documentHtml.matchAll(/<button\b([^>]*)>[\s\S]*?<\/button>/gi)]
    .map((m) => (/\btab-btn\b/i.test(m[1]) ? m[1].match(/\bdata-tab=["']([^"']+)["']/i)?.[1] : null))
    .filter(Boolean)
}
function sectionFor(documentHtml, id) {
  const startMatch = new RegExp(`<section\\b[^>]*\\bid=["']${id}["'][^>]*>`, 'i').exec(documentHtml)
  if (!startMatch) return null
  const tags = /<\/?section\b[^>]*>/gi
  tags.lastIndex = startMatch.index
  let depth = 0
  let match
  while ((match = tags.exec(documentHtml))) {
    depth += /^<\/section/i.test(match[0]) ? -1 : 1
    if (depth === 0) return documentHtml.slice(startMatch.index, tags.lastIndex)
  }
  return null
}

const results = []
const check = (label, condition) => results.push({ label, condition: Boolean(condition) })

// ── Los tabs estáticos reproducen exactamente los del source (ids y orden) ──
// Los tabs `dynamic` (super-tabs EPICA) no son <section> del source: se
// materializan al import desde assets/epica-*.js, así que se validan aparte.
const srcIds = sourceTabIds(source)
const staticManifest = manifest.filter((t) => !t.dynamic)
const dynamicManifest = manifest.filter((t) => t.dynamic)
check('el source tiene al menos un tab', srcIds.length > 0)
check(`manifiesto reproduce los ${srcIds.length} tabs estáticos del source`, staticManifest.length === srcIds.length)
check('ids estáticos === ids del source (mismo orden)', staticManifest.every((tab, i) => tab.id === srcIds[i]))
check('orden continuo 0..n', manifest.every((tab, i) => tab.order === i))
check('ids únicos', new Set(manifest.map((t) => t.id)).size === manifest.length)
check('el primer tab abre el dashboard', manifest[0]?.id === srcIds[0])

// ── Cada sección estática se preserva byte a byte y cada chart tiene runtime ─
for (const tab of staticManifest) {
  const sourceSection = sectionFor(source, tab.id)
  check(`${tab.id} conserva el HTML exacto del source`, sourceSection && imported.includes(sourceSection))
  for (const chartId of tab.chartIds) check(`${tab.id} conserva runtime de ${chartId}`, runtime.includes(chartId))
}

// ── Super-tabs EPICA materializados: sección presente + charts con runtime ──
for (const tab of dynamicManifest) {
  check(`${tab.id} materializado como <section> en tabs.html`, new RegExp(`<section\\b[^>]*\\bid=["']${tab.id}["']`).test(imported))
  for (const chartId of tab.chartIds) check(`${tab.id} conserva runtime de ${chartId}`, runtime.includes(chartId))
}
const dynSectionsPresent = dynamicManifest.filter((t) => new RegExp(`<section\\b[^>]*\\bid=["']${t.id}["']`).test(imported)).length
check('todos los tabs dinámicos (EPICA + dossiers) materializados en tabs.html', dynSectionsPresent === dynamicManifest.length)

// ── Todo handler inline del markup tiene su definición en runtime ────────────
const handlers = [...imported.matchAll(/\bon(?:click|change|input|submit)=["']([\s\S]*?)["']/gi)]
  .map((m) => m[1].match(/^\s*(?:return\s+)?([A-Za-z_$][\w$]*)\s*\(/)?.[1])
  .filter(Boolean)
for (const handler of new Set(handlers)) {
  check(`handler ${handler} disponible`, new RegExp(`(?:function\\s+${handler}\\s*\\(|(?:const|let|var)\\s+${handler}\\s*=|window\\.${handler}\\s*=)`).test(runtime))
}

// ── Capa presentable: el ancla de inyección de super-tabs se preserva ────────
check('tabs.html conserva id="dash-main-tabs"', /id=["']dash-main-tabs["']/.test(imported))

for (const result of results) console.log(`${result.condition ? 'PASS' : 'FAIL'} ${result.label}`)
const failed = results.filter((result) => !result.condition)
console.log(`\n${results.length - failed.length}/${results.length} controles aprobados`)
if (failed.length) process.exit(1)
