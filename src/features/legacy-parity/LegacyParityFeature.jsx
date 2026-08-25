import { useEffect, useRef, useState } from 'react'
import LegacyMarkup from './LegacyMarkup'
import LegacyChartEnhancements from './LegacyChartEnhancements'

const legacyRuntimeVersion = '2026-08-25-v194-migracion-index8'

const runtimeScripts = [
  '/legacy/plotly.js',
  '/legacy/runtime-core.js',
  '/legacy/runtime-emae.js',
  '/legacy/runtime-morosidad.js',
  '/legacy/runtime-pendulo.js',
  '/legacy/runtime-pendulo-power.js',
  '/legacy/runtime-pendulo-finance.js',
  '/legacy/runtime-pendulo-housing.js',
  '/legacy/runtime-pendulo-fiscal.js',
  '/legacy/runtime-roads.js',
  '/legacy/runtime-tourism.js',
  '/legacy/runtime-pendulo-cft.js',
  '/legacy/runtime-bank-adjustment.js',
  '/legacy/runtime-source-register.js',
  '/legacy/runtime-consumption-supermarkets.js',
  '/legacy/runtime-credit-mora.js',
].map((source) => `${source}?v=${legacyRuntimeVersion}`)

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
  'tab-consumption': ['renderSupermarketPulse'],
  // Charts existentes con el mismo patrón (render enganchado a un click en el botón).
  'tab-rates': ['renderBankAdjustment2024'],
  'tab-fiscal': ['renderTaxMap'],
}
function renderLegacyTabExtras(tabId) {
  const fns = legacyTabRenderers[tabId]
  if (!fns) return
  // setTimeout, no requestAnimationFrame: rAF se pausa cuando la pestaña no compone
  // frames (segundo plano), y estos renders deben correr igual al activar el tab.
  window.setTimeout(() => fns.forEach((name) => {
    try { window[name]?.() } catch { /* el render valida sus propios contenedores */ }
  }), 90)
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
