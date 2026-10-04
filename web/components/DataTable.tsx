import type { ReactNode } from 'react'

export interface Col<T> { key: string; label: string; num?: boolean; mono?: boolean; render?: (row: T) => ReactNode }

/** Wide table on desktop; on narrow screens each row becomes a labelled card (CSS only). */
export default function DataTable<T>({ cols, rows, caption, rowKey }: {
  cols: Col<T>[]; rows: T[]; caption: string; rowKey: (r: T) => string
}) {
  return (
    <div className="table-wrap" role="region" aria-label={caption} tabIndex={0}>
      <table className="dt">
        <caption className="sr-only">{caption}</caption>
        <thead>
          <tr>{cols.map((c) => <th key={c.key} scope="col" className={c.num ? 'num' : undefined}>{c.label}</th>)}</tr>
        </thead>
        <tbody>
          {rows.map((r) => (
            <tr key={rowKey(r)}>
              {cols.map((c) => (
                <td key={c.key} data-label={c.label} className={[c.num ? 'num' : '', c.mono ? 'mono' : ''].join(' ').trim() || undefined}>
                  {c.render ? c.render(r) : String((r as unknown as Record<string, unknown>)[c.key] ?? '')}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
