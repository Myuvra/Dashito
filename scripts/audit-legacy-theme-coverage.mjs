import fs from 'node:fs'
import path from 'node:path'
import process from 'node:process'

const root = process.cwd()
const basePath = path.join(root, 'public', 'legacy', 'base.css')
const themePath = path.join(root, 'data', 'legacy-archive', 'dashito-legacy.css')
const baseCss = fs.readFileSync(basePath, 'utf8').replace(/\/\*[\s\S]*?\*\//g, '')
const themeCss = fs.readFileSync(themePath, 'utf8')

const requiredCoverage = [
  '.wealth-history-grid > div',
  '.wealth-history-callout',
  '.social-compare-head',
  '.method-shield',
]

function luminance(hex) {
  const normalized = hex.length === 4
    ? hex.slice(1).split('').map((value) => value + value).join('')
    : hex.slice(1)
  if (normalized.length !== 6) return 0
  const channels = normalized.match(/.{2}/g).map((value) => parseInt(value, 16) / 255)
  const linear = channels.map((value) => value <= .03928 ? value / 12.92 : ((value + .055) / 1.055) ** 2.4)
  return .2126 * linear[0] + .7152 * linear[1] + .0722 * linear[2]
}

function hasLightBackground(body) {
  const declarations = body.match(/background(?:-color)?\s*:[^;}]+/gi) || []
  return declarations.some((declaration) => {
    if (/\b(?:white|snow|floralwhite|seashell)\b/i.test(declaration)) return true
    const colors = declaration.match(/#[0-9a-f]{3,8}\b/gi) || []
    return colors.some((color) => (color.length === 4 || color.length === 7) && luminance(color) >= .82)
  })
}

const candidates = []
for (const match of baseCss.matchAll(/([^{}]+)\{([^{}]*)\}/g)) {
  const selector = match[1].trim().replace(/^@[^\n]+/g, '').trim()
  if (!selector || !hasLightBackground(match[2])) continue
  for (const part of selector.split(',')) {
    const clean = part.trim()
    if (clean && !clean.startsWith('@')) candidates.push(clean)
  }
}

function covered(selector) {
  const ids = [...selector.matchAll(/#[a-z][\w-]*/gi)].map((match) => match[0])
  const classes = [...selector.matchAll(/\.[a-z][\w-]*/gi)].map((match) => match[0])
  const elements = selector
    .replace(/[#.][a-z][\w-]*/gi, ' ')
    .match(/(?:^|[\s>+~])([a-z][\w-]*)/gi)
    ?.map((token) => token.trim()) || []
  if ([...ids, ...classes, ...elements].some((token) => themeCss.includes(token))) return true

  const themedSuffixes = [
    'card', 'apb', 'editorial', 'recent', 'watch', 'kpi', 'stat', 'snap', 'piece',
    'control', 'note', 'warning', 'caveat', 'disclaimer', 'legend', 'summary',
    'status', 'formula', 'quality', 'change', 'service', 'table-wrap', 'audit',
  ]
  return classes.some((token) => themedSuffixes.some((suffix) => token.slice(1).endsWith(`-${suffix}`)))
}

const unique = [...new Set(candidates)]
const uncovered = unique.filter((selector) => !covered(selector))
const missingRequired = requiredCoverage.filter((selector) => !themeCss.includes(selector))

console.log(`Auditoría de fondos heredados: ${unique.length} selectores claros; ${unique.length - uncovered.length} cubiertos explícitamente; ${uncovered.length} para revisión preventiva.`)
if (uncovered.length) {
  console.log('Cola preventiva (no bloqueante):')
  uncovered.slice(0, 100).forEach((selector) => console.log(`  - ${selector}`))
  if (uncovered.length > 100) console.log(`  … y ${uncovered.length - 100} más`)
}

if (missingRequired.length) {
  console.error(`Faltan coberturas P0: ${missingRequired.join(', ')}`)
  process.exitCode = 1
} else {
  console.log('Coberturas P0 verificadas: grandes fortunas y asistencia social.')
}
