import Link from 'next/link'
import { NAV } from '@/lib/site'

export default function NotFound() {
  return (
    <div className="shell page">
      <header className="page-head">
        <p className="kicker">404</p>
        <h1>This page does not exist</h1>
        <p className="lede">Unlike a protected file, a missing page is not a security event. Try one of these:</p>
        <div className="btn-row">
          <Link className="btn btn-primary" href="/">Home</Link>
          {NAV.map((n) => <Link key={n.href} className="btn" href={n.href}>{n.label}</Link>)}
        </div>
      </header>
    </div>
  )
}
