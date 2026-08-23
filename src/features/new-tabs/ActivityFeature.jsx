import { useState } from 'react'
import { Callout, ChartForSection, DashboardHero, DataTable, DownloadCsvButton, MethodDetails, RelatedLinks, SectionCard, SegmentedControl, SourcesPanel } from '../../components/dashboard/DashboardUI'
import { activityData } from '../../data/newFeatureData'
import { formatNumber, formatPercent, sources } from '../../data/catalog'

const metrics = (latest, mandate) => [
  { label: 'Actividad total', value: formatPercent(latest.sa_nov2023_100 - 100, 1, true), detail: 'jun-2026 vs. nov-2023', tone: latest.sa_nov2023_100 >= 100 ? 'positive' : 'negative' },
  { label: 'Actividad por habitante', value: formatPercent(latest.pc_sa_raw_nov2023_100 - 100, 1, true), detail: 'jun-2026 vs. nov-2023', tone: latest.pc_sa_raw_nov2023_100 >= 100 ? 'positive' : 'negative' },
  { label: 'Durante Milei', value: formatPercent(mandate.change_total_pct, 1, true), detail: 'EMAE desestacionalizado · dic-2023 → jun-2026', tone: mandate.change_total_pct >= 0 ? 'positive' : 'negative' },
  { label: 'Saldo post-shock', value: `${formatNumber(latest.cum_net_months_base, 2)} meses-base`, detail: 'área neta frente a nov-2023', tone: latest.cum_net_months_base >= 0 ? 'positive' : 'negative' },
]

export default function ActivityFeature({ onNavigate }) {
  const [view, setView] = useState('total')
  const latest = activityData.monthly.at(-1)
  const milei = activityData.mandates.find((row) => row.mandate === 'Javier Milei')
  const mainSeries = view === 'total'
    ? [{ name: 'Desestacionalizada', values: activityData.monthly.map((row) => row.sa_nov2023_100) }, { name: 'Tendencia-ciclo', values: activityData.monthly.map((row) => row.tc_nov2023_100), dashed: true }]
    : [{ name: 'Por habitante · desestacionalizada', values: activityData.monthly.map((row) => row.pc_sa_raw_nov2023_100) }, { name: 'Por habitante · tendencia-ciclo', values: activityData.monthly.map((row) => row.pc_tc_raw_nov2023_100), dashed: true }]
  const mirrorSeries = view === 'total'
    ? [{ name: 'Ventana espejo', values: activityData.mirrorWindow.map((row) => row.mirror_sa_index) }, { name: 'Post-shock', values: activityData.mirrorWindow.map((row) => row.post_sa_index) }]
    : [{ name: 'Ventana espejo por habitante', values: activityData.mirrorWindow.map((row) => row.mirror_pc_index) }, { name: 'Post-shock por habitante', values: activityData.mirrorWindow.map((row) => row.post_pc_index) }]
  const mandateRows = activityData.mandates.map((row) => ({
    mandate: row.mandate,
    period: `${row.start} → ${row.end}${row.partial_series === 'sí' ? ' · parcial' : ''}`,
    total: formatPercent(row.change_total_pct, 1, true),
    capita: formatPercent(row.change_per_capita_pct, 1, true),
    drawdown: formatPercent(row.max_drawdown_pct, 1, true),
    recovery: row.months_to_recover_prior_peak == null ? 'sin recuperar' : `${row.months_to_recover_prior_peak} meses`,
  }))

  return <main className="feature-canvas">
    <DashboardHero eyebrow="Actividad real · EMAE" title="La economía mensual, sin confundir rebote con bienestar" summary="El EMAE permite seguir la actividad entre publicaciones del PIB. Separamos el nivel total del nivel por habitante y hacemos visible la base noviembre de 2023 = 100." badge="INDEC · ene-2004 → jun-2026" metrics={metrics(latest, milei)} />
    <div className="feature-toolbar">
      <SegmentedControl label="Ver" value={view} onChange={setView} options={[{ value: 'total', label: 'Actividad total' }, { value: 'capita', label: 'Por habitante' }]} />
      <DownloadCsvButton rows={activityData.monthly} filename="emae_mensual_auditado.csv">Descargar serie</DownloadCsvButton>
    </div>

    <SectionCard title="Actividad real desde 2004" badge="nov-2023 = 100" wide>
      <ChartForSection chart={{ type: 'line', labels: activityData.monthly.map((row) => row.date), series: mainSeries, ariaLabel: 'EMAE total y por habitante desde 2004' }} />
      <Callout title="Qué sí responde">El índice muestra cuánto produce la economía respecto de la base elegida. No equivale por sí solo a PIB trimestral, ingreso disponible, consumo ni calidad de vida.</Callout>
    </SectionCard>

    <div className="feature-sections">
      <SectionCard title="Ventana espejo" badge="31 meses contra 31 meses">
        <ChartForSection chart={{ type: 'line', labels: activityData.mirrorWindow.map((row) => `mes ${row.relative_month}`), series: mirrorSeries, ariaLabel: 'Recuperación post-shock frente a una ventana anterior de igual duración' }} />
        <Callout title="Misma longitud, distinta fecha">El post-shock termina en jun-2026. La ventana espejo usa may-2021 → nov-2023; no es un contrafactual causal.</Callout>
      </SectionCard>
      <SectionCard title="Caídas y recuperaciones" badge="desde cada pico local">
        <ChartForSection chart={{ type: 'bar', horizontal: true, labels: activityData.drawdowns.map((row) => row.episode), series: [{ name: 'Caída máxima', values: activityData.drawdowns.map((row) => row.max_drawdown_pct) }], valueSuffix: '%', ariaLabel: 'Caída máxima de la actividad en episodios seleccionados' }} />
        <Callout title="El tiempo también importa">La pandemia tuvo la caída más profunda; el shock 2023–2024 fue menor en magnitud, pero recuperar el pico de jun-2022 llevó 42 meses.</Callout>
      </SectionCard>
    </div>

    <SectionCard title="Actividad dentro de cada mandato" badge="calculado desde la serie, no hardcodeado" wide><DataTable columns={[{ key: 'mandate', label: 'Gobierno' }, { key: 'period', label: 'Período observado' }, { key: 'total', label: 'Cambio total' }, { key: 'capita', label: 'Cambio por habitante' }, { key: 'drawdown', label: 'Máxima caída' }, { key: 'recovery', label: 'Recuperar pico previo' }]} rows={mandateRows} /></SectionCard>

    <MethodDetails><p>La serie principal usa el EMAE desestacionalizado del INDEC. El índice por habitante divide por la estimación de población y luego rebasa a noviembre de 2023 = 100. El área en meses-base suma las distancias mensuales contra esa referencia.</p></MethodDetails>
    <RelatedLinks title="Actividad no vive sola" onNavigate={onNavigate} items={[{ id: 'tab-growth', label: 'Ver crecimiento y PIB' }, { id: 'tab-consumption', label: 'Ver consumo' }, { id: 'tab-work', label: 'Ver trabajo' }, { id: 'tab-morosidad', label: 'Ver morosidad' }]} />
    <SourcesPanel items={[sources.indec]} audit="Derivados auditados de la nueva Legacy. 270 observaciones mensuales; ventana espejo 31 contra 31; sin interpolar meses faltantes." />
    <footer className="feature-footer"><span>🥔</span> Dashito Argento · actividad total y por habitante no son la misma película</footer>
  </main>
}

