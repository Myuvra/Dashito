import { cpSync, mkdirSync, readFileSync, writeFileSync, readdirSync, rmSync, existsSync } from 'node:fs'
import { basename, dirname, resolve } from 'node:path'

// ────────────────────────────────────────────────────────────────────────────
// Importador de paridad Legacy · DATA-DRIVEN
//
// El source `Legacy/inflacion/index.html` es la ÚNICA fuente de verdad. Este
// script NO codifica cuántos tabs ni cuántos scripts hay: los deriva del propio
// source y emite manifiestos que consumen React (LegacyParityFeature.jsx) y el
// test (check-legacy-parity.mjs).
//
// Super-tabs EPICA: el source los entrega como assets JS externos
// (`assets/epica-*.js`) que inyectan style + nav + secciones + charts en runtime.
// Como el LegacyMarkup de Dashito reconstruye el markup como elementos React (no
// innerHTML) y descarta los <script>, aquí PRE-MATERIALIZAMOS al import: se
// extraen las secciones y el <style> (→ tabs.html / base.css como los otros tabs)
// y del asset se conserva sólo el JS de render/interactividad.
//
// PRESERVA la capa presentable que vive sólo en Dashito y no se regenera:
//   - themeSource `data/legacy-archive/dashito-legacy.css` (3 skins, tokens --da-*)
//   - los enhancements React en src/features/legacy-parity/*
// ────────────────────────────────────────────────────────────────────────────

const projectRoot = resolve(import.meta.dirname, '..')
// Source de verdad: el bundle deployable `railway-dashboard` (index.html + assets
// + research). Es mínimo: NO contiene data/derivados ni los dossiers pesados, así
// que para esas descargas caemos a `dataRoot` (el repo completo Legacy/inflacion)
// cuando exista. Así el HTML/assets salen del bundle y los datos no se rompen.
const legacyRoot = resolve(projectRoot, '..', 'railway-dashboard')
const dataRoot = [resolve(legacyRoot), resolve(projectRoot, '..', 'Legacy', 'inflacion')]
  .find((root) => existsSync(resolve(root, 'data', 'derivados'))) || legacyRoot
const sourcePath = resolve(legacyRoot, 'index.html')
const html = readFileSync(sourcePath, 'utf8')

const publicLegacy = resolve(projectRoot, 'public', 'legacy')
const generatedData = resolve(projectRoot, 'src', 'data', 'generated')
mkdirSync(publicLegacy, { recursive: true })
mkdirSync(generatedData, { recursive: true })

// Limpia runtime previos para no dejar archivos huérfanos con nombres viejos.
for (const file of readdirSync(publicLegacy)) {
  if (/^(runtime-|plotly).*\.js$/.test(file)) rmSync(resolve(publicLegacy, file))
}
const legacyAssets = resolve(publicLegacy, 'assets')
if (existsSync(legacyAssets)) rmSync(legacyAssets, { recursive: true, force: true })

function decodeText(value) {
  return value
    .replace(/<[^>]+>/g, ' ')
    .replace(/&nbsp;/gi, ' ')
    .replace(/&middot;/gi, '·')
    .replace(/&iquest;/gi, '¿')
    .replace(/&aacute;/gi, 'á').replace(/&eacute;/gi, 'é').replace(/&iacute;/gi, 'í')
    .replace(/&oacute;/gi, 'ó').replace(/&uacute;/gi, 'ú').replace(/&ntilde;/gi, 'ñ')
    .replace(/&amp;/gi, '&')
    .replace(/\s+/g, ' ')
    .trim()
}

function tabButtons(documentHtml) {
  return [...documentHtml.matchAll(/<button\b([^>]*)>([\s\S]*?)<\/button>/gi)]
    .map((match) => {
      const attributes = match[1]
      if (!/\btab-btn\b/i.test(attributes)) return null
      const id = attributes.match(/\bdata-tab=["']([^"']+)["']/i)?.[1]
      return id ? { id, label: decodeText(match[2]) } : null
    })
    .filter(Boolean)
}

function sectionFor(documentHtml, id) {
  const startMatch = new RegExp(`<section\\b[^>]*\\bid=["']${id}["'][^>]*>`, 'i').exec(documentHtml)
  if (!startMatch) throw new Error(`No se encontró ${id} en Legacy`)
  const start = startMatch.index
  const tags = /<\/?section\b[^>]*>/gi
  tags.lastIndex = start
  let depth = 0
  let match
  while ((match = tags.exec(documentHtml))) {
    depth += /^<\/section/i.test(match[0]) ? -1 : 1
    if (depth === 0) return documentHtml.slice(start, tags.lastIndex)
  }
  throw new Error(`No se pudo cerrar ${id}`)
}

// Secciones <section> TOP-LEVEL de un fragmento (depth-aware, ignora anidadas).
function topLevelSections(fragment) {
  const tags = /<\/?section\b[^>]*>/gi
  const out = []
  let depth = 0
  let start = -1
  let match
  while ((match = tags.exec(fragment))) {
    if (/^<\//.test(match[0])) {
      depth -= 1
      if (depth === 0 && start >= 0) { out.push(fragment.slice(start, tags.lastIndex).trim()); start = -1 }
    } else {
      if (depth === 0) start = match.index
      depth += 1
    }
  }
  return out
}

// Separa un asset EPICA en: css del <style>, botones de nav, secciones de panel y
// el JS "limpio" (sin la inyección de style/nav/secciones), conservando el render
// y la interactividad. Los templates extraídos no contienen backticks internos.
// Encuentra las llamadas `.insertAdjacentHTML('<pos>', <str>)` y extrae el string
// del 2º argumento respetando el tipo de comilla (backtick / ' / "). Devuelve
// rango [start,end) y contenido, para poder removerlas del JS limpio.
function findInsertAdjacent(js) {
  const out = []
  const head = /\.insertAdjacentHTML\(\s*(['"`])(?:afterend|beforebegin|afterbegin|beforeend)\1\s*,\s*/g
  let m
  while ((m = head.exec(js))) {
    let i = head.lastIndex
    const q = js[i]
    if (q !== '`' && q !== "'" && q !== '"') continue
    i += 1
    let content = ''
    while (i < js.length) {
      const c = js[i]
      if (c === '\\') { content += c + (js[i + 1] ?? ''); i += 2; continue }
      if (c === q) { i += 1; break }
      content += c; i += 1
    }
    while (i < js.length && /\s/.test(js[i])) i += 1
    if (js[i] === ')') i += 1
    if (js[i] === ';') i += 1
    out.push({ start: m.index, end: i, content })
  }
  return out
}

// Separa un asset (super-tab EPICA / political-wealth / dossiers) en: css del
// <style>, botones de nav, secciones de panel y el JS "limpio" (sin la inyección
// de style/nav/secciones), conservando render e interactividad. Clasifica cada
// insertAdjacentHTML por CONTENIDO: <section> → panel, .tab-btn → nav; cualquier
// otro (p.ej. un <th> dentro de un render) se deja intacto. Data-only (sin style
// ni inyección de tabs) pasa entero al JS limpio.
function parseEpicaAsset(js) {
  const removals = []
  const styleTc = js.match(/style\.textContent\s*=\s*`([\s\S]*?)`\s*;/)
  const styleCss = styleTc ? styleTc[1] : ''
  const styleAnchor = js.indexOf("document.createElement('style')")
  const appendIdx = js.indexOf('document.head.appendChild(style);')
  if (styleAnchor >= 0 && appendIdx >= 0) {
    const lineStart = js.lastIndexOf('\n', js.lastIndexOf('const style', appendIdx)) + 1
    removals.push([lineStart, appendIdx + 'document.head.appendChild(style);'.length])
  }
  const buttons = []
  const sections = []
  for (const { start, end, content } of findInsertAdjacent(js)) {
    if (/<section\b/i.test(content)) {
      for (const sec of topLevelSections(content)) sections.push(sec)
      removals.push([start, end])
    } else if (/\btab-btn\b/i.test(content) && /\bdata-tab=/i.test(content)) {
      for (const b of content.matchAll(/<button\b[^>]*\bdata-tab=["']([^"']+)["'][^>]*>([\s\S]*?)<\/button>/gi)) {
        buttons.push({ id: b[1], label: decodeText(b[2]) })
      }
      removals.push([start, end])
    }
    // resto (p.ej. <th> dentro de un render): NO se toca.
  }
  let clean = js
  for (const [a, b] of removals.sort((x, y) => y[0] - x[0])) clean = clean.slice(0, a) + clean.slice(b)
  return { styleCss, buttons, sections, clean }
}

// ── Tabs estáticos (derivados del source, sin conteo fijo) ──────────────────
const staticButtons = tabButtons(html)
if (staticButtons.length === 0) throw new Error('No se encontró ningún tab-btn en el source Legacy')

const staticTabs = staticButtons.map((tab, index) => {
  const markup = sectionFor(html, tab.id)
  return {
    ...tab,
    order: index,
    headings: [...markup.matchAll(/<h[1-4]\b[^>]*>([\s\S]*?)<\/h[1-4]>/gi)].map((mm) => decodeText(mm[1])),
    chartIds: [...markup.matchAll(/\bid=["']([^"']*Chart)["']/g)].map((mm) => mm[1]),
    noteCount: (markup.match(/\b(?:note|caveat|callout|reading|method|audit)\b/gi) || []).length,
    markup,
    dynamic: false,
  }
})

// ── Scripts inline + assets EPICA materializados ────────────────────────────
const scriptMatches = [...html.matchAll(/<script\b([^>]*)>([\s\S]*?)<\/script>/gi)]
const inlineRuntime = []
const epicaRuntime = []
const epicaStyles = []
const epicaTabs = []
let inlineIndex = 0
let epicaIndex = 0
for (const match of scriptMatches) {
  const srcAttrRaw = match[1].match(/\bsrc=["']([^"']+)["']/i)?.[1]
  if (srcAttrRaw) {
    const srcAttr = srcAttrRaw.split('?')[0] // el bundle versiona con ?v=…
    const assetPath = resolve(legacyRoot, srcAttr)
    if (!existsSync(assetPath)) throw new Error(`Asset EPICA referenciado no existe: ${srcAttr}`)
    const { styleCss, buttons, sections, clean } = parseEpicaAsset(readFileSync(assetPath, 'utf8'))
    if (styleCss) epicaStyles.push(styleCss)
    const labelById = new Map(buttons.map((b) => [b.id, b.label]))
    for (const markup of sections) {
      const id = markup.match(/<section\b[^>]*\bid=["']([^"']+)["']/i)?.[1]
      if (!id) throw new Error(`Sección EPICA sin id en ${srcAttr}`)
      epicaTabs.push({
        id,
        label: labelById.get(id) || id,
        headings: [...markup.matchAll(/<h[1-4]\b[^>]*>([\s\S]*?)<\/h[1-4]>/gi)].map((mm) => decodeText(mm[1])),
        chartIds: [...markup.matchAll(/\bid=["']([^"']*Chart)["']/g)].map((mm) => mm[1]),
        noteCount: (markup.match(/\b(?:note|caveat|callout|reading|method|audit)\b/gi) || []).length,
        markup,
        dynamic: true,
      })
    }
    const name = `runtime-epica-${String(epicaIndex).padStart(2, '0')}.js`
    writeFileSync(resolve(publicLegacy, name), `${clean}\n`, 'utf8')
    epicaRuntime.push(name)
    epicaIndex += 1
  } else {
    const name = `runtime-${String(inlineIndex).padStart(2, '0')}.js`
    writeFileSync(resolve(publicLegacy, name), `${match[2]}\n`, 'utf8')
    inlineRuntime.push(name)
    inlineIndex += 1
  }
}
// Los EPICA cargan al final: Plotly (00) y core ya definieron todo lo que usan.
const runtime = [...inlineRuntime, ...epicaRuntime]
const tabs = [...staticTabs, ...epicaTabs.map((tab, i) => ({ ...tab, order: staticTabs.length + i }))]

// ── tabs.html (controles ocultos + secciones estáticas + secciones EPICA) ───
const controls = `<div class="legacy-parity-controls" id="dash-main-tabs" hidden>${tabs
  .map((tab) => `<button class="tab-btn${tab.order === 0 ? ' active' : ''}" data-tab="${tab.id}" type="button">${tab.label}</button>`)
  .join('')}</div>`
writeFileSync(resolve(publicLegacy, 'tabs.html'), `${controls}\n${tabs.map((tab) => tab.markup).join('\n')}\n`, 'utf8')

// ── Estilos → base.css (source <style> + estilos EPICA extraídos) ───────────
const styles = [...html.matchAll(/<style(?:\s[^>]*)?>([\s\S]*?)<\/style>/gi)].map((mm) => mm[1])
const epicaStyleBlock = epicaStyles.length
  ? `\n\n/* ── super-tabs EPICA (materializados desde assets/epica-*.js) ── */\n${epicaStyles.join('\n\n')}`
  : ''
writeFileSync(resolve(publicLegacy, 'base.css'), `${styles.join('\n\n')}${epicaStyleBlock}\n`, 'utf8')

// ── themeSource → public/dashito-legacy.css (round-trip inverso, PRESERVADO) ─
const themeSource = resolve(projectRoot, 'data', 'legacy-archive', 'dashito-legacy.css')
const scopedTheme = readFileSync(themeSource, 'utf8')
  .replace(/html\[data-dashito-theme(?:=[^\]]+)?\](?:\s+body)?/g, (selector) => `${selector.replace(/\s+body$/, '')} .legacy-theme-scope`)
writeFileSync(resolve(projectRoot, 'public', 'dashito-legacy.css'), scopedTheme, 'utf8')

// ── Derivados + research citados por los tabs (descargas/fetch) ─────────────
// derivados salen de dataRoot (el bundle no los trae).
for (const folder of [
  'emae', 'morosidad', 'pendulo_distributivo', 'pendulo_poder_economico',
  'rutas_publico_privado', 'vacaciones_turismo',
  'supermercados', 'tasas', 'credito_consumo',
]) {
  const source = resolve(dataRoot, 'data', 'derivados', folder)
  if (!existsSync(source)) continue
  const destination = resolve(projectRoot, 'data', 'derivados', folder)
  mkdirSync(dirname(destination), { recursive: true })
  cpSync(source, destination, { recursive: true, force: true })
}
// research/*: todas las carpetas (epica_dashito_2026, political_wealth_*, …) que
// los super-tabs linkean. Los tabs SÓLO usan `derived/*.csv|json`; nunca las
// `sources/` (xls/txt/zip/pdf crudos) ni la microdata `eph_raw/`. Filtramos esos
// pesos para no bloatear el repo (el bundle ya es mínimo, pero un source completo
// no lo es) y limpiamos el dest antes de copiar para no acumular archivos stale.
const researchRoot = resolve(legacyRoot, 'research')
const researchDest = resolve(projectRoot, 'data', 'research')
if (existsSync(researchDest)) rmSync(researchDest, { recursive: true, force: true })
if (existsSync(researchRoot)) {
  const SKIP = /(?:^|[\\/])(?:sources|eph_raw)(?:[\\/]|$)|\.(?:xls|xlsx|zip|pdf)$/i
  cpSync(researchRoot, researchDest, { recursive: true, force: true, filter: (src) => !SKIP.test(src) })
}
// Carpetas de datos de los dossiers Frente B (CSV linkeados; espeja la ruta href
// relativa para que resuelvan bajo /data/… en Dashito). Salen de dataRoot.
for (const rel of ['Mora/05_ANALISIS_Y_CALCULOS/datos', 'Reclamo colectivo/02_CALCULOS_Y_METODOLOGIA']) {
  const src = resolve(dataRoot, rel)
  if (!existsSync(src)) continue
  const dest = resolve(projectRoot, 'data', rel)
  mkdirSync(dirname(dest), { recursive: true })
  cpSync(src, dest, { recursive: true, force: true })
}

// ── Manifiestos ─────────────────────────────────────────────────────────────
const tabManifest = tabs.map(({ id, label, order, headings, chartIds, noteCount, dynamic }) => ({ id, label, order, headings, chartIds, noteCount, dynamic }))
writeFileSync(resolve(generatedData, 'legacy-tabs-manifest.json'), `${JSON.stringify(tabManifest, null, 2)}\n`, 'utf8')
writeFileSync(resolve(generatedData, 'legacy-runtime-manifest.json'), `${JSON.stringify({ runtime, inlineRuntime, epicaRuntime }, null, 2)}\n`, 'utf8')
writeFileSync(resolve(projectRoot, 'data', 'legacy-archive', 'legacy.html'), html, 'utf8')

const totalCharts = tabManifest.reduce((sum, tab) => sum + tab.chartIds.length, 0)
console.log(`Paridad Legacy importada: ${tabs.length} tabs (${staticTabs.length} estáticos + ${epicaTabs.length} EPICA), ${totalCharts} contenedores de gráficos.`)
console.log(`Runtime: ${inlineRuntime.length} inline + ${epicaRuntime.length} EPICA.`)
tabs.forEach((tab) => console.log(`${String(tab.order + 1).padStart(2, '0')} ${tab.id}${tab.dynamic ? ' ·EPICA' : ''}: ${tab.headings.length} títulos · ${tab.chartIds.length} gráficos`))
