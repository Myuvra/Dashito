import { useEffect, useRef, useState } from 'react'
import LegacyMarkup from './LegacyMarkup'
import LegacyChartEnhancements from './LegacyChartEnhancements'
import runtimeManifest from '../../data/generated/legacy-runtime-manifest.json'

const legacyRuntimeVersion = '2026-08-31-v195-migracion10'

// La lista de runtime-scripts se deriva del manifiesto que emite
// import-legacy-parity.mjs (data-driven): así no hay que mantener nombres ni
// conteos a mano cuando el source Legacy suma o reordena scripts. Los `assets`
// externos (super-tabs EPICA) se activarán en una etapa aparte.
const runtimeScripts = runtimeManifest.runtime
  .map((file) => `/legacy/${file}?v=${legacyRuntimeVersion}`)

let runtimePromise

function loadScript(source) {
  const existing = document.querySelector(`script[data-legacy-runtime="${source}"]`)
  if (existing?.dataset.loaded === 'true') return Promise.resolve()
  return new Promise((resolve, reject) => {
    const script = existing || document.createElement('script')
    if (!existing) {
      script.src = source
      script.async = false
      script.dataset.legacyRuntime = source
      document.body.appendChild(script)
    }
    script.addEventListener('load', () => { script.dataset.loaded = 'true'; resolve() }, { once: true })
    script.addEventListener('error', () => reject(new Error(`No se pudo cargar ${source}`)), { once: true })
  })
}

function ensureRuntime() {
  const staleRuntime = [...document.querySelectorAll('script[data-legacy-runtime]')]
    .some((script) => !runtimeScripts.includes(script.dataset.legacyRuntime))
  if (staleRuntime) {
    window.location.reload()
    return new Promise(() => {})
  }
  runtimePromise ||= runtimeScripts.reduce((promise, source) => promise.then(() => loadScript(source)), Promise.resolve())
  return runtimePromise
}

// Tabs migrados desde index(8) cuyos scripts enganchan el render a un click en el
// botón al cargar (frágil con el montaje async de React). Dashito navega con
// activateTab, así que invocamos su render explícitamente al activar el tab.
const legacyTabRenderers = {
  'tab-credit-mora': ['renderCreditMora', 'renderCmLag'],
  'tab-mora-causal': ['renderMoraCausalAudit'],
  'tab-mora-anatomy': ['renderMoraAnatomy'],
  'tab-youth-credit': ['renderYouthCredit'],
  // Consumo: pulse + historia core + historia de supermercados v2 (8 charts nuevos).
  'tab-consumption': ['renderSupermarketPulse', 'renderConsumptionHistory', 'renderSupermarketHistory'],
  // Rates: ajuste bancario 2024 + sección nueva "referencia de crédito"
  // (renderCreditReference orquesta creditReference/creditGap/creditBurden + KPIs).
  'tab-rates': ['renderBankAdjustment2024', 'renderCreditReference'],
  'tab-fiscal': ['renderTaxMap'],
  // Super-tabs EPICA (materializados; render enganchado al click en el legacy).
  'tab-epica-households': ['renderEpicaHouseholds'],
  'tab-epica-dollars': ['renderEpicaDollars'],
  'tab-epica-caputo-colchon': ['renderEpicaCaputo'],
  'tab-epica-development': ['renderEpicaDevelopment'],
  'tab-epica-narratives': ['renderEpicaNarratives'],
  // Dossiers Frente B
  'tab-mora-ley': ['renderMoraLey'],
  'tab-reclamo-credito': ['renderReclamoCredito'],
  'tab-political-wealth': ['renderPoliticalWealth'],
}
function renderLegacyTabExtras(tabId) {
  const fns = legacyTabRenderers[tabId]
  if (!fns) return
  // setTimeout, no requestAnimationFrame: rAF se pausa cuando la pestaña no compone
  // frames (segundo plano), y estos renders deben correr igual al activar el tab.
  // Doble disparo: los tabs materializados (EPICA/dossiers) no auto-renderizan al
  // cargar, así que en un deep-link en frío el primer intento puede perder la
  // carrera con el layout (Plotly: "container is not an object"). El segundo
  // reintento es idempotente (Plotly.react) y asegura el render.
  const run = () => fns.forEach((name) => {
    try { window[name]?.() } catch { /* el render valida sus propios contenedores */ }
  })
  window.setTimeout(run, 90)
  window.setTimeout(run, 420)
}

export default function LegacyParityFeature({ activeId, onNavigate, theme }) {
  const [markup, setMarkup] = useState('')
  const [status, setStatus] = useState('loading')
  const activeRef = useRef(activeId)
  const navigateRef = useRef(onNavigate)
  const scopeRef = useRef(null)
  activeRef.current = activeId
  navigateRef.current = onNavigate

  useEffect(() => {
    let cancelled = false
    fetch(`/legacy/tabs.html?v=${legacyRuntimeVersion}`, { cache: 'no-store' })
      .then((response) => { if (!response.ok) throw new Error(`HTTP ${response.status}`); return response.text() })
      .then((html) => { if (!cancelled) setMarkup(html) })
      .catch(() => { if (!cancelled) setStatus('error') })
    return () => { cancelled = true }
  }, [])

  useEffect(() => {
    if (!markup) return
    let cancelled = false
    ensureRuntime().then(() => {
      if (cancelled) return
      const originalActivate = window.__dashitoLegacyActivateTab || window.activateTab?.bind(window)
      if (originalActivate && !window.__dashitoLegacyActivateTab) {
        window.__dashitoLegacyActivateTab = originalActivate
        window.activateTab = (tabId) => {
          window.__dashitoLegacyActivateTab(tabId)
          navigateRef.current?.(tabId)
        }
      }
      document.dispatchEvent(new Event('DOMContentLoaded'))
      window.__dashitoLegacyActivateTab?.(activeRef.current)
      renderLegacyTabExtras(activeRef.current)
      window.dispatchEvent(new Event('resize'))
      window.setTimeout(() => { if (!cancelled) setStatus('ready') }, 420)
    }).catch(() => { if (!cancelled) setStatus('error') })
    return () => { cancelled = true }
  }, [markup])

  useEffect(() => {
    if (status !== 'ready') return
    window.__dashitoLegacyActivateTab?.(activeId)
    renderLegacyTabExtras(activeId)
    window.dispatchEvent(new Event('resize'))
  }, [activeId, status])

  return <main className={`feature-canvas legacy-parity-canvas is-${status}`}>
    {status !== 'ready' ? <div className="legacy-parity-status" role="status">{status === 'error' ? 'No se pudo cargar la versión fiel de Legacy.' : 'Preparando el dashboard completo…'}</div> : null}
    <div className="legacy-theme-scope" ref={scopeRef}><div className="wrap legacy-parity-markup"><LegacyMarkup html={markup} /></div><LegacyChartEnhancements rootRef={scopeRef} activeId={activeId} ready={status === 'ready'} theme={theme} /></div>
  </main>
}
