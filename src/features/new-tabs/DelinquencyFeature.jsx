import { Callout, ChartForSection, DashboardHero, DownloadCsvButton, MethodDetails, RelatedLinks, SectionCard, SourcesPanel } from '../../components/dashboard/DashboardUI'
import { delinquencyData } from '../../data/newFeatureData'
import { formatNumber, formatPercent, sources } from '../../data/catalog'

const signed = (value, digits = 1, suffix = '') => `${Number(value) > 0 ? '+' : ''}${formatNumber(value, digits)}${suffix}`

function seriesByCategory(rows, categories) {
  const dates = [...new Set(rows.map((row) => row.date))].sort()
  const lookup = new Map(rows.map((row) => [`${row.date}|${row.category}`, row.ratio_pct]))
  return { labels: dates, series: categories.map((category) => ({ name: category, values: dates.map((date) => lookup.get(`${date}|${category}`) ?? null) })) }
}

export default function DelinquencyFeature({ onNavigate }) {
  const latestBank = delinquencyData.households.at(-1)
  const nov2023 = delinquencyData.households.find((row) => row.date === '2023-11-01')
  const latestPnfc = delinquencyData.pnfc.at(-1)
  const bankRows = delinquencyData.products.filter((row) => row.universe === 'Bancos · hogares')
  const pnfcRows = delinquencyData.products.filter((row) => row.universe === 'PNFC')
  const bankProducts = seriesByCategory(bankRows, ['Total hogares', 'Personales + tarjetas (combinado)'])
  const pnfcProducts = seriesByCategory(pnfcRows, ['Total PNFC', 'Préstamos personales PNFC', 'Tarjetas PNFC', 'Grupo Fintech'])
  const bankBefore = delinquencyData.mirrorWindows.find((row) => row.universe === 'Bancos · hogares' && row.window.startsWith('ANTES'))
  const bankAfter = delinquencyData.mirrorWindows.find((row) => row.universe === 'Bancos · hogares' && row.window.startsWith('DESPUÉS'))
  const pnfcBefore = delinquencyData.mirrorWindows.find((row) => row.universe === 'PNFC · total' && row.window.startsWith('ANTES'))
  const pnfcAfter = delinquencyData.mirrorWindows.find((row) => row.universe === 'PNFC · total' && row.window.startsWith('DESPUÉS'))
  const maxCorrelation = delinquencyData.correlations.reduce((best, row) => row.correlation > best.correlation ? row : best)

  return <main className="feature-canvas">
    <DashboardHero eyebrow="Morosidad · capacidad de pago" title="¿La gente puede pagar sus deudas?" summary="Separamos bancos, personales + tarjetas y PNFC/Fintech. Más deuda no significa automáticamente más mora: acá medimos la proporción irregular dentro de cada universo." badge="BCRA · may-2016 → may-2026" metrics={[
      { label: 'Morosidad hogares', value: formatPercent(latestBank.households_pct, 1), detail: 'de cada $100 financiados · may-2026', tone: 'negative' },
      { label: 'Vs. promedio histórico', value: signed(latestBank.excess_vs_historical_mean_pp, 1, ' pp'), detail: `promedio pre-shock ${formatPercent(latestBank.historical_mean_pre_shock_pct, 1)}`, tone: latestBank.excess_vs_historical_mean_pp > 0 ? 'negative' : 'positive' },
      { label: 'Personales + tarjetas', value: formatPercent(latestBank.households_personal_cards_pct, 1), detail: 'cartera bancaria combinada · may-2026', tone: 'negative' },
      { label: 'Post vs. espejo', value: signed(bankAfter.differential_post_minus_mirror_pp_month, 1, ' pp-mes'), detail: 'positivo = mayor deterioro', tone: bankAfter.differential_post_minus_mirror_pp_month > 0 ? 'negative' : 'positive' },
    ]} />
    <div className="feature-toolbar feature-toolbar--downloads">
      <DownloadCsvButton rows={delinquencyData.households} filename="morosidad_hogares.csv">Hogares</DownloadCsvButton>
      <DownloadCsvButton rows={delinquencyData.products} filename="morosidad_por_producto.csv">Por producto</DownloadCsvButton>
      <DownloadCsvButton rows={delinquencyData.mirrorWindows} filename="morosidad_ventana_espejo.csv">Ventana espejo</DownloadCsvButton>
    </div>

    <SectionCard title="Morosidad bancaria de hogares" badge="% del saldo financiado" wide>
      <ChartForSection chart={{ type: 'line', labels: delinquencyData.households.map((row) => row.date), series: [{ name: 'Hogares', values: delinquencyData.households.map((row) => row.households_pct), emphasis: true }, { name: 'Personales + tarjetas', values: delinquencyData.households.map((row) => row.households_personal_cards_pct) }, { name: 'Promedio histórico pre-shock', values: delinquencyData.households.map((row) => row.historical_mean_pre_shock_pct), dashed: true }], valueSuffix: '%', ariaLabel: 'Morosidad bancaria de hogares y promedio histórico' }} />
      <Callout title="Lectura actual">La mora de hogares está {formatNumber(latestBank.excess_vs_historical_mean_pp, 1)} pp sobre su promedio histórico y {formatNumber(latestBank.households_pct - nov2023.households_pct, 1)} pp sobre nov-2023. Es un porcentaje del saldo, no una cantidad de personas que entraron en mora ese mes.</Callout>
    </SectionCard>

    <div className="feature-sections">
      <SectionCard title="Qué parte del crédito bancario se deterioró" badge="universo homogéneo: bancos">
        <ChartForSection chart={{ type: 'line', ...bankProducts, valueSuffix: '%', ariaLabel: 'Morosidad bancaria total y personales más tarjetas' }} />
        <Callout title="Límite de apertura">La fuente comparable disponible agrupa personales + tarjetas. No inventamos una separación mensual que el derivado no respalda.</Callout>
      </SectionCard>
      <SectionCard title="PNFC y Fintech" badge="mora >90 días · universo distinto">
        <ChartForSection chart={{ type: 'line', ...pnfcProducts, valueSuffix: '%', ariaLabel: 'Morosidad de proveedores no financieros y Fintech' }} />
        <Callout title="Comparar tendencia, no nivel">Bancos y PNFC usan universos y definiciones diferentes. En feb-2026 el total PNFC fue {formatPercent(latestPnfc.pnfc_total_pct, 1)} y personales PNFC {formatPercent(latestPnfc.pnfc_personal_pct, 1)}.</Callout>
      </SectionCard>
      <SectionCard title="Saldo acumulado contra la norma" badge="pp-mes">
        <ChartForSection chart={{ type: 'line', labels: delinquencyData.cumulative.map((row) => row.date), series: [{ name: 'Desvío acumulado', values: delinquencyData.cumulative.map((row) => row.cumulative_excess_pp_month) }], valueSuffix: ' pp-mes', ariaLabel: 'Saldo acumulado de morosidad respecto del promedio histórico' }} />
        <Callout title="Intensidad por duración">Suma mora mensual menos promedio histórico. Positivo significa más mora que la norma; no es dinero perdido ni número de morosos.</Callout>
      </SectionCard>
      <SectionCard title="Ventana espejo: antes, después y diferencial" badge="mismas observaciones">
        <ChartForSection chart={{ type: 'bar', horizontal: true, labels: ['Bancos · antes', 'Bancos · después', 'Bancos · diferencial', 'PNFC · antes', 'PNFC · después', 'PNFC · diferencial'], series: [{ name: 'Saldo vs. promedio', values: [bankBefore.balance_vs_historical_mean_pp_month, bankAfter.balance_vs_historical_mean_pp_month, bankAfter.differential_post_minus_mirror_pp_month, pnfcBefore.balance_vs_historical_mean_pp_month, pnfcAfter.balance_vs_historical_mean_pp_month, pnfcAfter.differential_post_minus_mirror_pp_month] }], valueSuffix: ' pp-mes', ariaLabel: 'Comparación de ventanas espejo de morosidad bancaria y PNFC' }} />
        <Callout title="No alcanza con que ambas ventanas sean malas">Bancos: {bankBefore.observations} meses contra {bankAfter.observations}; diferencial {signed(bankAfter.differential_post_minus_mirror_pp_month, 1, ' pp-mes')}. PNFC: {pnfcBefore.observations} contra {pnfcAfter.observations}; diferencial {signed(pnfcAfter.differential_post_minus_mirror_pp_month, 1, ' pp-mes')}.</Callout>
      </SectionCard>
      <SectionCard title="Personas fuera de situación regular" badge="snapshots · no serie mensual">
        <ChartForSection chart={{ type: 'stacked', labels: delinquencyData.people.map((row) => `${row.provider.replace('PNFC ', '')} · ${row.date.slice(0, 4)}`), series: [{ name: 'Situación regular', values: delinquencyData.people.map((row) => row.regular_pct) }, { name: 'Fuera de regular', values: delinquencyData.people.map((row) => row.outside_regular_pct) }], valueSuffix: '%', ariaLabel: 'Personas deudoras regulares y fuera de situación regular en PNFC' }} />
        <Callout title="Pesos y personas no son lo mismo">Los valores 2025 son snapshots oficiales; los de 2024 se reconstruyen desde la variación publicada y están rotulados como derivados.</Callout>
      </SectionCard>
      <SectionCard title="Tasa real hoy, mora después" badge="exploratorio · rezagos 0–6 meses">
        <ChartForSection chart={{ type: 'bar', labels: delinquencyData.correlations.map((row) => `${row.lag_months}m`), series: [{ name: 'Correlación', values: delinquencyData.correlations.map((row) => row.correlation) }], ariaLabel: 'Correlación entre tasa real de préstamos personales y morosidad con rezagos' }} />
        <Callout title="Correlación temporal ≠ causalidad">La asociación más alta aparece a {maxCorrelation.lag_months} meses, r = {formatNumber(maxCorrelation.correlation, 2)}. No demuestra que la tasa sea la única causa del deterioro.</Callout>
      </SectionCard>
    </div>

    <SectionCard title="Lectura automática" badge="qué muestran los datos, sin sobreactuar" wide>
      <div className="automatic-reading"><p><strong>¿Mejoró o empeoró?</strong> Empeoró: la irregularidad bancaria subió {formatNumber(latestBank.households_pct - nov2023.households_pct, 1)} pp frente a nov-2023 y el saldo post-shock superó a la ventana espejo en {formatNumber(bankAfter.differential_post_minus_mirror_pp_month, 1)} pp-mes.</p><p><strong>¿Dónde se concentró?</strong> Personales + tarjetas bancarias llegaron a {formatPercent(latestBank.households_personal_cards_pct, 1)}. En PNFC, préstamos personales cerraron en {formatPercent(latestPnfc.pnfc_personal_pct, 1)} y el grupo Fintech en {formatPercent(latestPnfc.fintech_pct, 1)}.</p><p><strong>¿Fue sólo monetario?</strong> No: los snapshots PNFC también muestran más personas fuera de situación regular en 2025. Son universos distintos y no se suman entre sí.</p></div>
    </SectionCard>

    <MethodDetails><p>La mora bancaria es cartera irregular sobre financiaciones a hogares. PNFC usa mora mayor a 90 días dentro de cada categoría. El promedio histórico se calcula antes del shock; el saldo en pp-mes suma los desvíos mensuales. Stock irregular no equivale a nuevos morosos: también cambia por pagos, refinanciaciones, castigos y originaciones.</p></MethodDetails>
    <RelatedLinks title="Cruzar sin inventar causalidad" onNavigate={onNavigate} items={[{ id: 'tab-rates', label: 'Ver tasas e inflación' }, { id: 'tab-power', label: 'Ver poder adquisitivo' }, { id: 'tab-work', label: 'Ver trabajo' }, { id: 'tab-consumption', label: 'Ver consumo' }, { id: 'tab-emae', label: 'Ver actividad real' }]} />
    <SourcesPanel items={[sources.bcra]} audit="Derivados auditados de la nueva Legacy: 11/11 pruebas de Morosidad aprobadas. Bancos y PNFC se presentan separados; no se mezclan porcentajes de saldos con porcentajes de personas." />
    <footer className="feature-footer"><span>🥔</span> Dashito Argento · deuda, mora y personas son tres preguntas diferentes</footer>
  </main>
}

