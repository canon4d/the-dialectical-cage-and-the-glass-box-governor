/** The mechanism, as responsive HTML/CSS: a row on wide screens, a column on phones. */
export default function Flow() {
  const Node = ({ k, t, d, tone }: { k: string; t: string; d: string; tone?: string }) => (
    <li className={`flow-node ${tone ?? ''}`}>
      <span className="flow-k">{k}</span>
      <strong>{t}</strong>
      <span className="flow-d">{d}</span>
    </li>
  )
  return (
    <figure className="flow" aria-label="Request path: agent, request, reference monitor, protected effect, evidence">
      <ol className="flow-row">
        <Node k="untrusted" t="Agent / model" d="May request anything, including adversarial actions." />
        <li className="flow-arrow" aria-hidden="true">→</li>
        <Node k="request" t="Action request" d="principal · effect · resource · capability" />
        <li className="flow-arrow" aria-hidden="true">→</li>
        <Node k="trusted core" t="Reference monitor" d="19 ordered checks, one lock around check + commit." tone="is-core" />
        <li className="flow-arrow" aria-hidden="true">→</li>
        <Node k="only if ALLOW" t="Protected effect" d="write_file · delete_file on two declared files." />
      </ol>
      <div className="flow-evidence">
        <span aria-hidden="true">↓</span>
        <span><strong>Evidence record</strong> for every decision, ALLOW or BLOCK — hash-chained, reconstructible.</span>
      </div>
      <figcaption>
        Trust boundary: everything left of the monitor is untrusted. In v0.1 that boundary is a convention inside one process, not an operating-system barrier — see <a href="/limitations/">Limitations</a>.
      </figcaption>
    </figure>
  )
}
