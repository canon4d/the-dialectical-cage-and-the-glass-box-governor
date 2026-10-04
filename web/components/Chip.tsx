const EPI: Record<string, string> = {
  D: 'Derivation', A: 'Declared assumption', S: 'Security / invariant claim', E: 'Empirical assurance', R: 'Residual / open',
}

export function StatusChip({ status }: { status: string }) {
  return <span className={`chip st-${status}`}>{status.replace(/_/g, ' ')}</span>
}

export function EpiChip({ label }: { label: string }) {
  return <span className={`chip ep-${label}`} title={EPI[label] ?? label}><b>{label}</b><span className="sr-only"> — {EPI[label] ?? label}</span></span>
}
