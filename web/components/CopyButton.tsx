'use client'

import { useState } from 'react'

export default function CopyButton({ text, label = 'Copy' }: { text: string; label?: string }) {
  const [state, setState] = useState<'idle' | 'ok' | 'err'>('idle')
  async function copy() {
    try {
      if (navigator.clipboard?.writeText) await navigator.clipboard.writeText(text)
      else {
        const ta = document.createElement('textarea')
        ta.value = text; ta.setAttribute('readonly', ''); ta.style.position = 'fixed'; ta.style.opacity = '0'
        document.body.appendChild(ta); ta.select(); document.execCommand('copy'); document.body.removeChild(ta)
      }
      setState('ok')
    } catch { setState('err') }
    setTimeout(() => setState('idle'), 1800)
  }
  return (
    <>
      <button type="button" className="copy-btn" onClick={copy}>
        {state === 'ok' ? 'Copied' : state === 'err' ? 'Press Ctrl+C' : label}
      </button>
      <span className="sr-only" role="status" aria-live="polite">
        {state === 'ok' ? 'Copied to clipboard' : state === 'err' ? 'Copy failed' : ''}
      </span>
    </>
  )
}
