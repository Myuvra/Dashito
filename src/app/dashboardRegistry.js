import {
  Activity, BarChart3, BookOpenText, BriefcaseBusiness, Building2, ChartNoAxesCombined,
  CircleDollarSign, Factory, Gauge, HandCoins, HeartPulse, History, House,
  Landmark, LineChart, PackageOpen, Percent, PiggyBank, Plane, Route, Scale,
  ShieldCheck, Ship, ShoppingBasket, TrendingDown, TrendingUp, Users, WalletCards,
} from 'lucide-react'
import legacyTabs from '../data/generated/legacy-tabs-manifest.json'

const metadata = {
  'tab-story': { slug: 'historia', aliases: ['storytelling'], icon: BookOpenText, group: 'Destacados', shortLabel: 'Historia' },
  'tab-power': { slug: 'poder-adquisitivo', icon: WalletCards },
  'tab-rates': { slug: 'tasas-inflacion', icon: Percent },
  'tab-pres': { slug: 'inflacion-presidencias', icon: History },
  'tab-poverty': { slug: 'pobreza', icon: Users },
  'tab-social': { slug: 'asistencia-social', icon: HandCoins },
  'tab-gini': { slug: 'desigualdad', icon: Scale },
  'tab-structure': { slug: 'estructura-social', icon: BarChart3 },
  'tab-family': { slug: 'canasta-familiar', icon: ShoppingBasket },
  'tab-risk': { slug: 'riesgo-pais', icon: Gauge },
  'tab-bigmac': { slug: 'indice-big-mac', icon: CircleDollarSign },
  'tab-wholesale': { slug: 'precios-mayoristas', icon: Factory },
  'tab-health-education': { slug: 'salud-educacion', icon: HeartPulse },
  'tab-consumption': { slug: 'consumo', icon: PackageOpen },
  'tab-work': { slug: 'trabajo', icon: BriefcaseBusiness },
  'tab-investment': { slug: 'inversion', icon: Building2 },
  'tab-housing': { slug: 'vivienda', icon: House },
  'tab-growth': { slug: 'crecimiento', icon: ChartNoAxesCombined },
  'tab-emae': { slug: 'actividad-real', icon: Activity },
  'tab-morosidad': { slug: 'morosidad', icon: TrendingDown },
  'tab-credit-mora': { slug: 'credito-mora', icon: WalletCards },
  'tab-mora-causal': { slug: 'mora-causal', icon: Activity },
  'tab-mora-anatomy': { slug: 'mora-anatomia', icon: BarChart3 },
  'tab-youth-credit': { slug: 'credito-joven', icon: Users },
  'tab-pendulo': { slug: 'pendulo-poder-economico', aliases: ['pendulo-distributivo'], icon: Scale },
  'tab-roads': { slug: 'rutas-publico-privado', icon: Route },
  'tab-tourism': { slug: 'vacaciones-turismo', icon: Plane },
  'tab-debt-public': { slug: 'deuda-publica', icon: Landmark },
  'tab-fiscal': { slug: 'resultado-fiscal', icon: PiggyBank },
  'tab-trade': { slug: 'balanza-comercial', icon: Ship },
  'tab-bcra': { slug: 'bcra', icon: Activity },
  'tab-debt-spiral': { slug: 'espiral-deuda', icon: TrendingUp },
  'tab-program': { slug: 'programa-escenarios', icon: LineChart },
  'tab-wealth-contribution': { slug: 'grandes-fortunas', icon: CircleDollarSign },
  'tab-milei-cost': { slug: 'lo-que-te-robo-milei', icon: TrendingDown },
  'tab-meli-benefits': { slug: 'privilegios-fiscales', icon: Building2 },
  'tab-casta': { slug: 'la-casta', icon: ShieldCheck },
}

const categoryIds = [
  { id: 'featured', label: 'Destacados', ids: ['tab-story', 'tab-power', 'tab-rates', 'tab-poverty', 'tab-emae', 'tab-morosidad', 'tab-pendulo', 'tab-debt-public', 'tab-milei-cost'] },
  { id: 'households', label: 'Hogares', ids: ['tab-power', 'tab-poverty', 'tab-social', 'tab-gini', 'tab-structure', 'tab-family', 'tab-health-education', 'tab-consumption', 'tab-work', 'tab-housing', 'tab-morosidad', 'tab-credit-mora', 'tab-mora-causal', 'tab-mora-anatomy', 'tab-youth-credit'] },
  { id: 'prices', label: 'Precios y dólar', ids: ['tab-rates', 'tab-pres', 'tab-risk', 'tab-bigmac', 'tab-wholesale', 'tab-bcra'] },
  { id: 'activity', label: 'Actividad', ids: ['tab-consumption', 'tab-work', 'tab-investment', 'tab-housing', 'tab-growth', 'tab-emae', 'tab-roads', 'tab-tourism', 'tab-trade'] },
  { id: 'state', label: 'Estado y deuda', ids: ['tab-social', 'tab-health-education', 'tab-debt-public', 'tab-fiscal', 'tab-bcra', 'tab-debt-spiral', 'tab-program'] },
  { id: 'power', label: 'Poder económico', ids: ['tab-pendulo', 'tab-wealth-contribution', 'tab-milei-cost', 'tab-meli-benefits', 'tab-casta'] },
]

export const dashboards = legacyTabs.map((tab) => ({
  id: tab.id,
  slug: metadata[tab.id].slug,
  aliases: metadata[tab.id].aliases || [],
  label: tab.label,
  icon: metadata[tab.id].icon,
  description: tab.headings[0] || tab.label,
  categories: categoryIds.filter((category) => category.ids.includes(tab.id)).map((category) => category.label),
  group: metadata[tab.id].group || categoryIds.find((category) => category.ids.includes(tab.id))?.label || 'Dashboard',
  shortLabel: metadata[tab.id].shortLabel || tab.label,
  legacyOrder: tab.order,
}))

export const dashboardCategories = [
  ...categoryIds.map((category) => ({ ...category, items: category.ids.map((id) => dashboards.find((item) => item.id === id)).filter(Boolean) })),
  { id: 'all', label: 'Ver todo', ids: dashboards.map((item) => item.id), items: dashboards },
]
