import { useEffect, useRef, useState } from 'react'
import LegacyMarkup from './LegacyMarkup'
import LegacyChartEnhancements from './LegacyChartEnhancements'

const legacyRuntimeVersion = '2026-08-22-v185-storytelling'

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
  '/legacy/runtime-source-register.js',
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
      window.dispatchEvent(new Event('resize'))
      window.setTimeout(() => { if (!cancelled) setStatus('ready') }, 420)
    }).catch(() => { if (!cancelled) setStatus('error') })
    return () => { cancelled = true }
  }, [markup])

  useEffect(() => {
    if (status !== 'ready') return
    window.__dashitoLegacyActivateTab?.(activeId)
    window.dispatchEvent(new Event('resize'))
  }, [activeId, status])

  return <main className={`feature-canvas legacy-parity-canvas is-${status}`}>
    {status !== 'ready' ? <div className="legacy-parity-status" role="status">{status === 'error' ? 'No se pudo cargar la versión fiel de Legacy.' : 'Preparando el dashboard completo…'}</div> : null}
    <div className="legacy-theme-scope" ref={scopeRef}><div className="wrap legacy-parity-markup"><LegacyMarkup html={markup} /></div><LegacyChartEnhancements rootRef={scopeRef} activeId={activeId} ready={status === 'ready'} theme={theme} /></div>
  </main>
}
