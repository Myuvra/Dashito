import { useMemo, useState } from 'react'
import { Callout, ChartForSection, DashboardHero, DataTable, DownloadCsvButton, MethodDetails, RelatedLinks, SectionCard, SegmentedControl, SourcesPanel } from '../../components/dashboard/DashboardUI'
import { distributionData } from '../../data/newFeatureData'
import { formatNumber, formatPercent, sources } from '../../data/catalog'

const signed = (value, digits = 1) => `${Number(value) > 0 ? '+' : ''}${formatNumber(value, digits)}`

function segmentedRows(rows) {
  const output = []
  let segment = rows[0]?.segment
  rows.forEach((row) => {
    if (segment && row.segment !== segment) output.push({ date: '2008–2015 · sin serie comparable', period: 'corte', segment: 'gap' })
    output.push(row)
    segment = row.segment
  })
  return output
}

export default function DistributionFeature({ onNavigate }) {
  const [universe, setUniverse] = useState('private')
  const [perspective, setPerspective] = useState('pendulum')
  const rows = useMemo(() => segmentedRows(distributionData.series.filter((row) => row.universe === universe)), [universe])
  const observed = rows.filter((row) => row.segment !== 'gap')
  const latest = observed.at(-1)
  const mandate = distributionData.mandates.find((row) => row.universe === universe && row.mandate === 'Javier Milei')
  const labels = rows.map((row) => row.period)
  const charts = {
    pendulum: [{ name: 'Índice del péndulo', values: rows.map((row) => row.pendulo) }],
    shares: [{ name: 'Trabajo asalariado · RTA', values: rows.map((row) => row.share_rta) }, { name: 'Ingreso mixto · IMB', values: rows.map((row) => row.share_imb) }, { name: 'Excedente societario · EEB', values: rows.map((row) => row.share_capital) }],
    change: [{ name: 'Cambio desde el inicio del mandato', values: rows.map((row) => row.change_since_mandate_start) }],
  }
  const mandateRows = distributionData.mandates.filter((row) => row.universe === universe).map((row) => ({
    mandate: row.mandate,
    period: `${row.start_period} → ${row.end_period}`,
    start: formatNumber(row.start, 1),
    end: formatNumber(row.end, 1),
    change: signed(row.change, 1),
    direction: row.change > 0 ? '→ trabajo / hogares' : row.change < 0 ? '← capital societario' : 'sin cambio',
    average: formatNumber(row.average, 1),
  }))

  return <main className="feature-canvas">
    <DashboardHero eyebrow="Cuenta de Generación del Ingreso" title="El péndulo distributivo argentino" summary="Ponemos a prueba una hipótesis política con una pregunta medible: qué parte del ingreso generado va a trabajo e ingreso mixto, y qué parte queda como excedente societario." badge="INDEC · CGI · 1993–2007 y 2016–2026" metrics={[
      { label: 'Trabajo + hogares', value: formatPercent(latest.share_households, 1), detail: `${latest.period} · ${universe === 'private' ? 'sector privado' : 'economía total'}`, tone: 'positive' },
      { label: 'Excedente societario', value: formatPercent(latest.share_capital, 1), detail: 'EEB sobre el total normalizado' },
      { label: 'Péndulo actual', value: signed(latest.pendulo, 1), detail: '+100 hogares · 0 empate · −100 capital' },
      { label: 'Cambio durante Milei', value: signed(mandate.change, 1), detail: mandate.change > 0 ? 'hacia trabajo / hogares' : 'hacia excedente societario', tone: mandate.change >= 0 ? 'positive' : 'negative' },
    ]} />
    <div className="feature-toolbar feature-toolbar--wrap">
      <SegmentedControl label="Serie" value={universe} onChange={setUniverse} options={[{ value: 'private', label: 'Sector privado' }, { value: 'total', label: 'Total economía' }]} />
      <SegmentedControl label="Ver como" value={perspective} onChange={setPerspective} options={[{ value: 'pendulum', label: 'Índice' }, { value: 'shares', label: 'Participación %' }, { value: 'change', label: 'Cambio del mandato' }]} />
      <DownloadCsvButton rows={observed} filename={`pendulo_${universe}.csv`}>Descargar serie</DownloadCsvButton>
    </div>

    <SectionCard title="El péndulo distributivo argentino" badge="el hueco metodológico no se empalma" wide>
      <ChartForSection chart={{ type: 'line', labels, series: charts[perspective], min: perspective === 'pendulum' ? -100 : undefined, max: perspective === 'pendulum' ? 100 : undefined, valueSuffix: perspective === 'shares' ? '%' : '', ariaLabel: 'Distribución del ingreso entre trabajo, hogares y excedente societario' }} />
      <Callout title="Cómo leer este gráfico">Subir significa mayor participación relativa de RTA + IMB; bajar significa mayor participación del EEB. El hueco 2008–2015 queda vacío porque no hay un empalme metodológicamente defendible.</Callout>
    </SectionCard>

    <div className="feature-sections">
      <SectionCard title="¿Quién se queda con el ingreso generado?" badge="RTA + IMB + EEB = 100">
        <ChartForSection chart={{ type: 'line', labels, series: charts.shares, valueSuffix: '%', ariaLabel: 'Participación de trabajo asalariado, ingreso mixto y excedente societario' }} />
        <Callout title="Tres componentes, no dos">RTA aproxima trabajo asalariado; IMB incluye autónomos y emprendimientos de hogares; EEB aproxima excedente societario. “Trabajo/hogares” es una abreviación narrativa.</Callout>
      </SectionCard>
      <SectionCard title="¿Cuánta verdad tiene la frase?" badge="hipótesis, no veredicto">
        <div className="narrative-card"><blockquote>“El péndulo argentino es entre la gente que no quiere dejarse cagar por las corpos y la gente que no entiende que la están cagando.”</blockquote><h3>Lo que sí podemos medir</h3><p>Participación del trabajo, ingreso mixto, excedente societario y su evolución durante cada gobierno.</p><h3>Lo que no demuestra</h3><p>No prueba intenciones de votantes, explotación, calidad institucional ni que toda ganancia empresaria sea extraordinaria.</p></div>
        <Callout title="Conclusión neutral">La distribución sí oscila y ofrece una base económica para hablar de un “péndulo”. Reducir el comportamiento electoral a personas que entienden o no entienden que las perjudican excede lo que estos datos pueden demostrar.</Callout>
      </SectionCard>
    </div>

    <SectionCard title="¿Hacia dónde se movió durante cada gobierno?" badge="ocurrencia no implica causalidad" wide><DataTable columns={[{ key: 'mandate', label: 'Gobierno' }, { key: 'period', label: 'Período' }, { key: 'start', label: 'Inicio' }, { key: 'end', label: 'Final' }, { key: 'change', label: 'Cambio' }, { key: 'direction', label: 'Dirección observada' }, { key: 'average', label: 'Promedio' }]} rows={mandateRows} /></SectionCard>

    <MethodDetails><p>Péndulo = ((RTA + IMB) − EEB) / (RTA + IMB + EEB) × 100. El índice excluye impuestos netos de subsidios para normalizar el reparto. No mide por sí solo bienestar, eficiencia, productividad, explotación ni calidad institucional. Un cambio ocurrido durante un gobierno tampoco prueba que sus políticas sean la única causa.</p></MethodDetails>
    <RelatedLinks title="Participación relativa no es bienestar absoluto" onNavigate={onNavigate} items={[{ id: 'tab-power', label: 'Ver salarios reales' }, { id: 'tab-gini', label: 'Ver desigualdad' }, { id: 'tab-poverty', label: 'Ver pobreza' }, { id: 'tab-consumption', label: 'Ver consumo' }, { id: 'tab-growth', label: 'Ver crecimiento' }, { id: 'tab-casta', label: 'Ver La casta' }]} />
    <SourcesPanel items={[sources.indec]} audit="Fuente: INDEC — Cuenta de Generación del Ingreso e Insumo de Mano de Obra. Segmentos históricos y modernos se mantienen separados; no se interpolan 2008–2015." />
    <footer className="feature-footer"><span>🥔</span> Dashito Argento · una hipótesis incómoda merece datos incómodamente claros</footer>
  </main>
}
