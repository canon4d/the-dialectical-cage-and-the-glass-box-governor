import CopyButton from './CopyButton'

export default function CodeBlock({ code, label }: { code: string; label?: string }) {
  return (
    <figure className="code">
      <div className="code-bar">
        <span className="code-label">{label ?? 'shell'}</span>
        <CopyButton text={code} />
      </div>
      <pre tabIndex={0} aria-label={label ? `${label} (scrollable)` : 'Code (scrollable)'}><code>{code}</code></pre>
    </figure>
  )
}
