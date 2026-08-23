import LegacyParityFeature from './legacy-parity/LegacyParityFeature'

export default function DashboardFeature({ activeId, onNavigate, theme }) {
  return <LegacyParityFeature activeId={activeId} onNavigate={onNavigate} theme={theme} />
}
