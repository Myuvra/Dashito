import { mkdirSync, readFileSync, writeFileSync } from 'node:fs'
import { dirname, resolve } from 'node:path'

const root = resolve(import.meta.dirname, '..')
const inputPath = resolve(root, 'data/legacy-archive/legacy.html')
const outputPath = resolve(root, 'src/data/generated/legacy-data.json')
const source = readFileSync(inputPath, 'utf8')

function readExpression(start) {
  let braces = 0
  let brackets = 0
  let parens = 0
  let quote = null
  let escaped = false
  let lineComment = false
  let blockComment = false

  for (let index = start; index < source.length; index += 1) {
    const char = source[index]
    const next = source[index + 1]

    if (lineComment) {
      if (char === '\n') lineComment = false
      continue
    }
    if (blockComment) {
      if (char === '*' && next === '/') {
        blockComment = false
        index += 1
      }
      continue
    }
    if (quote) {
      if (escaped) escaped = false
      else if (char === '\\') escaped = true
      else if (char === quote) quote = null
      continue
    }
    if (char === '/' && next === '/') {
      lineComment = true
      index += 1
      continue
    }
    if (char === '/' && next === '*') {
      blockComment = true
      index += 1
      continue
    }
    if (char === '"' || char === "'" || char === '`') {
      quote = char
      continue
    }
    if (char === '{') braces += 1
    if (char === '}') braces -= 1
    if (char === '[') brackets += 1
    if (char === ']') brackets -= 1
    if (char === '(') parens += 1
    if (char === ')') parens -= 1
    if (char === ';' && braces === 0 && brackets === 0 && parens === 0) {
      return source.slice(start, index).trim()
    }
  }
  return null
}

const extraNames = new Set([
  'duhaldePoverty', 'povertyMandateChanges',
  'castaSalaryLevels', 'castaInflationVsSalary', 'castaMandateData',
  'consumptionMandates', 'workMetricMeta', 'housingTenure', 'housingBuild',
  'investmentReal', 'growthMandates', 'debtPublicMandates', 'fiscalYearGroups',
  'tradeMandates', 'tradeYearGroups', 'debtObserved', 'debtClassBasket',
  'healthEducationRecent', 'healthEducationProvMandates', 'healthEducationMandates',
  'powerTotalAllOfficial', 'powerPensionEffective', 'powerAggregateLossParams',
  'powerRescueParams', 'inflationAnnualX', 'inflationAnnualY', 'inflationAnnualMeta',
  'ratesUsuryEffect', 'ratesAccumData', 'ratesMoneySummary', 'socialRecent',
])
const assignmentPattern = /\bconst\s+([A-Za-z_$][\w$]*)\s*=\s*/g
const extracted = {}
const skipped = []

for (const match of source.matchAll(assignmentPattern)) {
  const name = match[1]
  const isCatalogName = /(Data|DATA|Series|Rows|History|Sources|Catalog|Metrics|Annual|Monthly)$/.test(name)
  if (!isCatalogName && !extraNames.has(name)) continue
  const expression = readExpression(match.index + match[0].length)
  if (!expression || !['{', '['].includes(expression[0])) continue
  try {
    const value = Function(`"use strict"; return (${expression});`)()
    const serialized = JSON.stringify(value)
    if (!serialized || serialized === '{}') continue
    extracted[name] = value
  } catch (error) {
    skipped.push({ name, reason: error.message })
  }
}

mkdirSync(dirname(outputPath), { recursive: true })
writeFileSync(outputPath, `${JSON.stringify(extracted)}\n`, 'utf8')
console.log(`Series extraídas: ${Object.keys(extracted).length}`)
console.log(Object.keys(extracted).join('\n'))
if (skipped.length) console.log(`Omitidas por depender de cálculos en ejecución: ${skipped.length}`)
