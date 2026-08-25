import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'

const root = resolve(import.meta.dirname, '..')
const source = readFileSync(resolve(root, '..', 'Legacy', 'inflacion', 'index.html'), 'utf8')
const imported = readFileSync(resolve(root, 'public', 'legacy', 'tabs.html'), 'utf8')
const manifest = JSON.parse(readFileSync(resolve(root, 'src', 'data', 'generated', 'legacy-tabs-manifest.json'), 'utf8'))
const runtimeFiles = [
  'runtime-core.js',
  'runtime-emae.js',
  'runtime-morosidad.js',
  'runtime-pendulo.js',
  'runtime-pendulo-power.js',
  'runtime-pendulo-finance.js',
  'runtime-pendulo-housing.js',
  'runtime-pendulo-fiscal.js',
  'runtime-roads.js',
  'runtime-tourism.js',
  'runtime-pendulo-cft.js',
  'runtime-bank-adjustment.js',
  'runtime-source-register.js',
  'runtime-consumption-supermarkets.js',
  'runtime-credit-mora.js',
]
const runtime = runtimeFiles.map((file) => readFileSync(resolve(root, 'public', 'legacy', file), 'utf8')).join('\n')

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

check('37 tabs en el manifiesto', manifest.length === 37)
check('37 ids únicos', new Set(manifest.map((tab) => tab.id)).size === 37)
check('Storytelling abre el manifiesto', manifest[0]?.id === 'tab-story')
check('orden continuo 0–36', manifest.every((tab, index) => tab.order === index))

const story = sectionFor(imported, 'tab-story') || ''
check('Storytelling conserva doce capítulos', (story.match(/\bclass=["'][^"']*\bstory-chapter\b[^"']*["']/gi) || []).length === 12)
check('Storytelling conserva seis indicadores', (story.match(/\bclass=["'][^"']*\bstory-stat(?:\s|["'])/gi) || []).length === 6)
check('Storytelling conserva su bloque público de fuentes', /\bstory-source-note\b/.test(story) && !/>[^<]*handover[^<]*</i.test(story))
check('V184 conserva el retiro móvil del cierre de Cuenta madre', /#tab-milei-cost>\.milei-cost-inset-start~\*/.test(readFileSync(resolve(root, 'public', 'legacy', 'base.css'), 'utf8')))
check('V185 conserva la separación de leyenda social', /legend\.y['"]?:mobile\?1\.09:1\.10/.test(runtime))

for (const tab of manifest) {
  const sourceSection = sectionFor(source, tab.id)
  check(`${tab.id} conserva el HTML exacto`, sourceSection && imported.includes(sourceSection))
  for (const chartId of tab.chartIds) check(`${tab.id} conserva runtime de ${chartId}`, runtime.includes(chartId))
}

const handlers = [...imported.matchAll(/\bon(?:click|change|input|submit)=["']([\s\S]*?)["']/gi)]
  .map((match) => match[1].match(/^\s*(?:return\s+)?([A-Za-z_$][\w$]*)\s*\(/)?.[1])
  .filter(Boolean)
for (const handler of new Set(handlers)) {
  check(`handler ${handler} disponible`, new RegExp(`(?:function\\s+${handler}\\s*\\(|(?:const|let|var)\\s+${handler}\\s*=)`).test(runtime))
}

for (const result of results) console.log(`${result.condition ? 'PASS' : 'FAIL'} ${result.label}`)
const failed = results.filter((result) => !result.condition)
console.log(`\n${results.length - failed.length}/${results.length} controles aprobados`)
if (failed.length) process.exit(1)
