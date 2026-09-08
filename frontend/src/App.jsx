import { useEffect, useMemo, useState } from 'react'

const API_BASE = import.meta.env.VITE_API_BASE || ''
const SHORTENER_ORIGIN = import.meta.env.VITE_SHORTENER_ORIGIN || 'http://127.0.0.1:8000'
const SHORT_CODE_LENGTH = 7
const SHORT_CODE_CHARS = 'abcdefghijklmnopqrstuvwxyz0123456789'

function createShortCode() {
  return Array.from({ length: SHORT_CODE_LENGTH }, () => SHORT_CODE_CHARS[Math.floor(Math.random() * SHORT_CODE_CHARS.length)]).join('')
}

function Icon({ children }) { return <span className="icon" aria-hidden="true">{children}</span> }
function formatDate(value) { return value ? new Intl.DateTimeFormat(undefined, { dateStyle: 'medium' }).format(new Date(value)) : '—' }

function App() {
  const [destinationUrl, setDestinationUrl] = useState('')
  const [shortCode, setShortCode] = useState('')
  const [result, setResult] = useState(null)
  const [analytics, setAnalytics] = useState(null)
  const [links, setLinks] = useState([])
  const [loading, setLoading] = useState(false)
  const [linksLoading, setLinksLoading] = useState(true)
  const [analyticsLoading, setAnalyticsLoading] = useState(false)
  const [error, setError] = useState('')
  const [copied, setCopied] = useState(false)

  async function loadLinks() {
    setLinksLoading(true)
    try {
      const response = await fetch(`${API_BASE}/api/v1/links`)
      const data = await response.json()
      if (!response.ok) throw new Error(data.detail || 'Could not load your links.')
      setLinks(Array.isArray(data) ? data : [])
    } catch (err) { setError(err.message || 'Could not load your links.') }
    finally { setLinksLoading(false) }
  }

  useEffect(() => { loadLinks() }, [])

  async function shortenUrl(event) {
    event.preventDefault(); setError(''); setResult(null); setAnalytics(null); setCopied(false)
    const code = shortCode.trim() || createShortCode()
    if (!/^[a-zA-Z0-9_-]{3,64}$/.test(code)) { setError('Use 3–64 letters, numbers, underscores, or hyphens for the short code.'); return }
    setLoading(true)
    try {
      const response = await fetch(`${API_BASE}/api/v1/links`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ destination_url: destinationUrl, short_code: code }) })
      const data = await response.json()
      if (!response.ok) throw new Error(data.detail || 'Could not create the link.')
      setShortCode(data.short_code); setResult(data); setDestinationUrl(''); await loadLinks()
    } catch (err) { setError(err.message || 'Something went wrong.') }
    finally { setLoading(false) }
  }

  async function loadAnalytics(shortCodeToLoad = result?.short_code) {
    if (!shortCodeToLoad) return
    setAnalyticsLoading(true); setError('')
    try {
      const response = await fetch(`${API_BASE}/api/v1/links/${encodeURIComponent(shortCodeToLoad)}/analytics`)
      const data = await response.json()
      if (!response.ok) throw new Error(data.detail || 'Could not load analytics.')
      setAnalytics(data); document.getElementById('analytics')?.scrollIntoView({ behavior: 'smooth', block: 'center' })
    } catch (err) { setError(err.message || 'Could not load analytics.') }
    finally { setAnalyticsLoading(false) }
  }

  async function copyLink(shortCodeToCopy = result?.short_code) {
    if (!shortCodeToCopy) return
    try { await navigator.clipboard.writeText(`${SHORTENER_ORIGIN}/${shortCodeToCopy}`); setCopied(shortCodeToCopy); window.setTimeout(() => setCopied(false), 1800) }
    catch { setError('Could not copy the link. Please copy it manually.') }
  }

  const shortLink = result ? `${SHORTENER_ORIGIN}/${result.short_code}` : ''
  const totalLinks = links.length
  const activeLinks = links.filter((link) => link.is_active && !(link.expires_at && new Date(link.expires_at) <= new Date())).length
  const expiredLinks = links.filter((link) => link.expires_at && new Date(link.expires_at) <= new Date()).length
  const visibleLinks = useMemo(() => [...links].sort((a, b) => new Date(b.created_at) - new Date(a.created_at)), [links])

  return (
    <div className="app-shell">
      <header className="navbar">
        <a className="brand" href="#home" aria-label="Smart Shortner home"><div className="brand-mark"><Icon>↗</Icon></div><span>Smart<span>Shortner</span></span></a>
        <nav className="nav-links" aria-label="Main navigation"><a href="#home">Home</a><a href="#dashboard">Dashboard</a><a href="#features">Features</a></nav>
        <a className="github-link" href="https://github.com/kapilraghav2801/URL-Shortner" target="_blank" rel="noreferrer">GitHub ↗</a>
      </header>

      <main id="home">
        <section className="hero">
          <div className="eyebrow"><span /> LINK INFRASTRUCTURE, SIMPLIFIED</div>
          <h1>Short links.<br /><em>Big possibilities.</em></h1>
          <p className="hero-copy">Turn long URLs into clean, memorable links — then track every click with a fast, production-ready backend.</p>
          <form className="shortener-card" onSubmit={shortenUrl}>
            <div className="field-row"><div className="input-wrap main-input"><Icon>↗</Icon><input type="url" value={destinationUrl} onChange={(event) => setDestinationUrl(event.target.value)} placeholder="Paste your long URL here..." aria-label="Destination URL" required /></div><button className="primary-button" type="submit" disabled={loading}>{loading ? 'Creating...' : 'Shorten URL'}{!loading && <span>→</span>}</button></div>
            <div className="custom-row"><label htmlFor="short-code">Short code <span>optional</span></label><div className="input-wrap custom-input"><span className="prefix">your.link/</span><input id="short-code" value={shortCode} onChange={(event) => setShortCode(event.target.value.replace(/\s/g, ''))} placeholder="auto-generated" maxLength={64} /></div><span className="field-help">Leave blank to generate one</span></div>
          </form>
          {error && <div className="alert error" role="alert">{error}</div>}
          {result && <section className="result-card" aria-live="polite"><div className="result-icon">✓</div><div className="result-content"><span className="result-label">YOUR SHORT LINK</span><a href={shortLink} target="_blank" rel="noreferrer">{shortLink}</a><p title={result.destination_url}>→ {result.destination_url}</p></div><div className="result-actions"><button className="secondary-button" type="button" onClick={() => copyLink()}>{copied === result.short_code ? 'Copied!' : 'Copy link'}</button><button className="ghost-button" type="button" onClick={() => loadAnalytics()} disabled={analyticsLoading}>{analyticsLoading ? 'Loading...' : 'View clicks'}</button></div></section>}
          {analytics && <div className="analytics-card" id="analytics"><div><span className="result-label">LINK ANALYTICS</span><strong>{analytics.total_clicks}</strong><span className="muted"> total clicks</span></div><div className="analytics-code">{SHORTENER_ORIGIN}/{analytics.short_code}</div></div>}
        </section>

        <section className="dashboard" id="dashboard">
          <div className="dashboard-heading"><div><div className="eyebrow"><span /> YOUR LINKS</div><h2>Link dashboard</h2><p>Everything you've shortened, in one place.</p></div><button className="refresh-button" type="button" onClick={loadLinks} disabled={linksLoading}>{linksLoading ? 'Refreshing...' : '↻ Refresh'}</button></div>
          <div className="stats-grid"><div className="stat-card"><span>Total links</span><strong>{totalLinks}</strong><small>created so far</small></div><div className="stat-card"><span>Active links</span><strong>{activeLinks}</strong><small>ready to redirect</small></div><div className="stat-card"><span>Expired</span><strong>{expiredLinks}</strong><small>past expiration date</small></div></div>
          <div className="links-panel"><div className="links-panel-head"><div><h3>Recent links</h3><p>Live data from your FastAPI backend.</p></div><span>{totalLinks} {totalLinks === 1 ? 'link' : 'links'}</span></div>
            {linksLoading ? <div className="empty-state"><div className="spinner" /><p>Loading your links...</p></div> : visibleLinks.length === 0 ? <div className="empty-state"><div className="empty-icon">↗</div><h3>No links yet</h3><p>Create your first short link above and it will appear here.</p></div> : <div className="link-list">{visibleLinks.map((link) => { const linkUrl = `${SHORTENER_ORIGIN}/${link.short_code}`; const expired = link.expires_at && new Date(link.expires_at) <= new Date(); const active = link.is_active && !expired; return <article className="link-row" key={link.id}><div className="link-symbol">↗</div><div className="link-info"><a href={linkUrl} target="_blank" rel="noreferrer">{linkUrl}</a><p title={link.destination_url}>{link.destination_url}</p></div><div className={`status ${active ? 'active' : 'inactive'}`}><span />{active ? 'Active' : expired ? 'Expired' : 'Inactive'}</div><div className="link-date">{formatDate(link.created_at)}</div><div className="row-actions"><button type="button" onClick={() => copyLink(link.short_code)}>{copied === link.short_code ? 'Copied' : 'Copy'}</button><button type="button" onClick={() => loadAnalytics(link.short_code)} disabled={analyticsLoading}>Analytics</button></div></article> })}</div>}
          </div>
        </section>

        <section className="trust-strip"><span>BUILT FOR THE NEXT STAGE</span><div><b>FastAPI</b><b>PostgreSQL</b><b>Async</b><b>Analytics-ready</b></div></section>
        <section className="features" id="features"><div className="section-heading"><div className="eyebrow"><span /> WHY SMART SHORTNER</div><h2>More than a shorter URL.</h2><p>A clean foundation today, with room to grow into the link platform you actually want.</p></div><div className="feature-grid"><article><div className="feature-number">01</div><h3>Custom links</h3><p>Choose memorable short codes or let Smart Shortner generate one for you.</p></article><article><div className="feature-number">02</div><h3>Click tracking</h3><p>Every redirect can record click events and request metadata.</p></article><article><div className="feature-number">03</div><h3>Built to scale</h3><p>Async FastAPI, PostgreSQL and a layered architecture give us a strong base.</p></article></div></section>
      </main>
      <footer><div className="brand small"><div className="brand-mark"><Icon>↗</Icon></div><span>Smart<span>Shortner</span></span></div><span>Built with purpose · MIT License</span></footer>
    </div>
  )
}

export default App
