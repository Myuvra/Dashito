import legacyData from './generated/legacy-data.json'

export const SNAPSHOT_CUTOFF = '2026-08-20'

const official = (label, href, detail) => ({ label, href, detail, kind: 'official' })
const secondary = (label, href, detail) => ({ label, href, detail, kind: 'secondary' })

export const sources = {
  indec: official('INDEC', 'https://www.indec.gob.ar/', 'Series y publicaciones oficiales de Argentina.'),
  idecba: official('IDECBA', 'https://www.estadisticaciudad.gob.ar/', 'Canastas y estratificación de hogares de CABA.'),
  bcra: official('BCRA', 'https://www.bcra.gob.ar/', 'Tasas, reservas, tipo de cambio y sistema financiero.'),
  anses: official('ANSES', 'https://www.anses.gob.ar/', 'Haberes, bonos y prestaciones sociales.'),
  economia: official('Ministerio de Economía', 'https://www.argentina.gob.ar/economia', 'Presupuesto, cuentas fiscales y deuda pública.'),
  presupuesto: official('Presupuesto Abierto', 'https://www.presupuestoabierto.gob.ar/', 'Ejecución presupuestaria nacional.'),
  arca: official('ARCA', 'https://www.arca.gob.ar/', 'Regímenes tributarios y estadísticas fiscales.'),
  uca: secondary('Observatorio de la Deuda Social Argentina · UCA', 'https://uca.edu.ar/es/observatorio-de-la-deuda-social-argentina', 'Movilidad, estrés económico y capacidad de ahorro.'),
  argendata: secondary('Argendata', 'https://argendata.fund.ar/', 'Series históricas armonizadas y documentación metodológica.'),
  bigmac: secondary('The Economist · Big Mac Index', 'https://github.com/TheEconomist/big-mac-data', 'Paridad cambiaria cruda y ajustada por PIB.'),
  risk: secondary('Argentina Financial Data', 'https://github.com/maximilianozurita/arg-financial-data', 'Serie pública secundaria del EMBI+ argentino.'),
  imf: secondary('FMI', 'https://www.imf.org/en/Countries/ARG', 'Programa, revisiones y escenarios macroeconómicos.'),
}

const entries = {
  power: ['powerData', 'powerHistoricalMonthly', 'powerTotalAllOfficial', 'powerPensionEffective', 'powerAggregateLossParams', 'powerRescueParams'],
  rates: ['ratesMoneyRows', 'ratesMoneySummary', 'ratesUsuryPostRows', 'ratesUsuryMirrorRows'],
  poverty: ['povertyData', 'duhaldePoverty', 'povertyMandateChanges'],
  gini: ['giniData', 'giniHistoricalData', 'giniPunctualData'],
  structure: ['structureCabaData', 'structureUcaData', 'structureFederalData'],
  family: ['familyData'],
  social: ['socialRecent'],
  consumption: ['consumptionData', 'consumptionMandates', 'consumptionCategoryData', 'consumptionMoreCategoryData'],
  work: ['workRows', 'workPunctualRows', 'workMetricMeta', 'workSectorMonthly'],
  housing: ['housingTenure', 'housingHistory', 'housingBuild'],
  investment: ['investmentAnnual', 'investmentReal'],
  growth: ['growthData', 'growthMandates'],
  debtPublic: ['debtPublicData', 'debtPublicMandates'],
  fiscal: ['fiscalAnnualData', 'fiscalYearGroups'],
  trade: ['tradeMandates', 'tradeYearGroups'],
  bcra: ['bcraData'],
  debtSpiral: ['debtObserved', 'debtClassBasket'],
  healthEducation: ['healthEducationData', 'healthEducationRecent', 'healthEducationProvHistory', 'healthEducationMandates'],
  wealth: ['wealthContributionData'],
  meli: ['meliBenefitData', 'meliOtherBenefitsData'],
  casta: ['castaSalaryLevels', 'castaInflationVsSalary', 'castaSideData'],
}

export const dataCatalog = Object.fromEntries(Object.entries(entries).map(([feature, keys]) => [
  feature,
  Object.fromEntries(keys.map((key) => [key, legacyData[key]])),
]))

export function latestFinite(values = []) {
  for (let index = values.length - 1; index >= 0; index -= 1) {
    if (Number.isFinite(Number(values[index]))) return Number(values[index])
  }
  return null
}

export function lastRow(rows = [], predicate = () => true) {
  for (let index = rows.length - 1; index >= 0; index -= 1) {
    if (predicate(rows[index])) return rows[index]
  }
  return null
}

export function average(values = []) {
  const finite = values.map(Number).filter(Number.isFinite)
  return finite.length ? finite.reduce((sum, value) => sum + value, 0) / finite.length : null
}

export function formatNumber(value, digits = 1) {
  if (!Number.isFinite(Number(value))) return 's/d'
  return Number(value).toLocaleString('es-AR', { minimumFractionDigits: digits, maximumFractionDigits: digits })
}

export function formatPercent(value, digits = 1, signed = false) {
  const number = Number(value)
  if (!Number.isFinite(number)) return 's/d'
  const sign = signed && number > 0 ? '+' : ''
  return `${sign}${formatNumber(number, digits)}%`
}

export function formatMoneyMillions(value, digits = 0) {
  if (!Number.isFinite(Number(value))) return 's/d'
  return `$ ${formatNumber(Number(value) / 1_000_000, digits)} M`
}

