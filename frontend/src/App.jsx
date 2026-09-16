import { useEffect, useMemo, useState } from 'react'
import './analytics.css'

const API_BASE = import.meta.env.VITE_API_BASE || ''
const SHORTENER_ORIGIN = import.meta.env.VITE_SHORTENER_ORIGIN || 'http://127.0.0.1:8000'

function Icon({ children }) {
  return <span className="icon" aria-hidden="true">{children}</span>
}

function formatDate(value) {
  return value ? new Intl.DateTimeFormat(undefined, { month: 'short', day: 'numeric', year: 'numeric' }).format(new Date(value)) : '—'
}

function formatDateTime(value) {
  return value ? new Intl.DateTimeFormat(undefined, { month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit' }).format(new Date(value)) : '—'
}

function isExpired(link) {
  return Boolean(link.expires_at && new Date(link.expires_at) <= new Date())
}

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
  const [copied, setCopied] = useState('')
  const [search, setSearch] = useState('')
  const [filter, setFilter] = useState('all')

  async function loadLinks() {
    setLinksLoading(true)
    try {
      const response = await fetch(`${API_BASE}/api/v1/links`)
      const data = await response.json()
      if (!response.ok) throw new Error(data.detail || 'Could not load your links.')
      setLinks(Array.isArray(data) ? data : [])
    } catch (err) {
      setError(err.message || 'Could not load your links.')
    } finally {
      setLinksLoading(false)
    }
  }

  useEffect(() => { loadLinks() }, [])

  async function shortenUrl(event) {
    event.preventDefault()
    setError('')
    setResult(null)
    setAnalytics(null)
    setCopied('')

    const requestedCode = shortCode.trim()
    if (requestedCode && !/^[a-zA-Z0-9_-]{3,64}$/.test(requestedCode)) {
      setError('Use 3–64 letters, numbers, underscores, or hyphens for the short code.')
      return
    }

    setLoading(true)
    try {
      const payload = { destination_url: destinationUrl }
      if (requestedCode) payload.short_code = requestedCode

      const response = await fetch(`${API_BASE}/api/v1/links`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      })
      const data = await response.json()
      if (!response.ok) throw new Error(data.detail || 'Could not create the link.')

      setShortCode(data.short_code)
      setResult(data)
      setDestinationUrl('')
      await loadLinks()
    } catch (err) {
      setError(err.message || 'Something went wrong.')
    } finally {
      setLoading(false)
    }
  }

  async function loadAnalytics(shortCodeToLoad) {
    if (!shortCodeToLoad) return
    setAnalyticsLoading(true)
    setError('')
    try {
      const response = await fetch(`${API_BASE}/api/v1/links/${encodeURIComponent(shortCodeToLoad)}/analytics`)
      const data = await response.json()
      if (!response.ok) throw new Error(data.detail || 'Could not load analytics.')
      setAnalytics(data)
      window.setTimeout(() => document.getElementById('analytics')?.scrollIntoView({ behavior: 'smooth', block: 'center' }), 50)
    } catch (err) {
      setError(err.message || 'Could not load analytics.')
    } finally {
      setAnalyticsLoading(false)
    }
  }

  async function copyLink(code) {
    if (!code) return
    try {
      await navigator.clipboard.writeText(`${SHORTENER_ORIGIN}/${code}`)
      setCopied(code)
      window.setTimeout(() => setCopied(''), 1800)
    } catch {
      setError('Could not copy the link. Please copy it manually.')
    }
  }

  const totalClicks = useMemo(() => links.reduce((sum, link) => sum + (link.short_code === analytics?.short_code ? analytics.total_clicks : 0), 0), [links, analytics])
  const totalLinks = links.length
  const activeLinks = links.filter((link) => link.is_active && !isExpired(link)).length
  const expiredLinks = links.filter(isExpired).length
  const visibleLinks = useMemo(() => {
    const query = search.trim().toLowerCase()
    return [...links]
      .filter((link) => {
        const expired = isExpired(link)
        const statusMatch = filter === 'all' || (filter === 'active' ? link.is_active && !expired : expired || !link.is_active)
        const searchMatch = !query || link.short_code.toLowerCase().includes(query) || link.destination_url.toLowerCase().includes(query)
        return statusMatch && searchMatch
      })
      .sort((a, b) => new Date(b.created_at) - new Date(a.created_at))
  }, [links, search, filter])

  const resultLink = result ? `${SHORTENER_ORIGIN}/${result.short_code}` : ''

  return (
    <div className="app-shell">
      <div className="ambient ambient-one" />
      <div className="ambient ambient-two" />

      <header className="navbar">
        <a className="brand" href="#home" aria-label="Smart Shortner home">
          <div className="brand-mark"><Icon>↗</Icon></div>
          <span>Smart<span>Shortner</span></span>
        </a>
        <nav className="nav-links" aria-label="Main navigation">
          <a className="active" href="#home">Overview</a>
          <a href="#dashboard">Links</a>
          <a href="#features">Features</a>
        </nav>
        <div className="nav-actions">
          <span className="live-pill"><i /> Live</span>
          <a className="github-link" href="https://github.com/kapilraghav2801/URL-Shortner" target="_blank" rel="noreferrer">GitHub ↗</a>
        </div>
      </header>

      <main id="home">
        <section className="hero">
          <div className="hero-copy-block">
            <div className="eyebrow"><span /> LINK INTELLIGENCE PLATFORM</div>
            <h1>Make every link<br /><em>worth clicking.</em></h1>
            <p className="hero-copy">Create memorable short links, understand every click, and build your own link infrastructure — without the enterprise price tag.</p>
            <div className="hero-meta">
              <span><b>01</b> Create</span><span><b>02</b> Share</span><span><b>03</b> Understand</span>
            </div>
          </div>

          <div className="creator-shell">
            <div className="creator-topline"><span>CREATE NEW LINK</span><span className="secure-label">● Local development</span></div>
            <form className="shortener-card" onSubmit={shortenUrl}>
              <label className="field-label">Destination URL</label>
              <div className="field-row">
                <div className="input-wrap main-input"><Icon>↗</Icon><input type="url" value={destinationUrl} onChange={(event) => setDestinationUrl(event.target.value)} placeholder="https://your-long-url.com/..." aria-label="Destination URL" required /></div>
                <button className="primary-button" type="submit" disabled={loading}>{loading ? 'Creating…' : 'Create link'}<span>→</span></button>
              </div>
              <div className="creator-options">
                <div>
                  <label className="field-label" htmlFor="short-code">Custom alias <span>optional</span></label>
                  <div className="input-wrap custom-input"><span className="prefix">{SHORTENER_ORIGIN.replace(/^https?:\/\//, '')}/</span><input id="short-code" value={shortCode} onChange={(event) => setShortCode(event.target.value.replace(/\s/g, ''))} placeholder="auto" maxLength={64} /></div>
                </div>
                <div className="creator-hint"><span>✦</span> Leave blank and the backend will generate a unique code.</div>
              </div>
            </form>
            {error && <div className="alert error" role="alert"><span>!</span>{error}</div>}
            {result && (
              <section className="result-card" aria-live="polite">
                <div className="result-icon">✓</div>
                <div className="result-content"><span className="result-label">LINK CREATED</span><a href={resultLink} target="_blank" rel="noreferrer">{resultLink}</a><p title={result.destination_url}>{result.destination_url}</p></div>
                <div className="result-actions"><button className="secondary-button" type="button" onClick={() => copyLink(result.short_code)}>{copied === result.short_code ? 'Copied ✓' : 'Copy link'}</button><button className="ghost-button" type="button" onClick={() => loadAnalytics(result.short_code)} disabled={analyticsLoading}>{analyticsLoading ? 'Loading…' : 'Analytics →'}</button></div>
              </section>
            )}
          </div>
        </section>

        <section className="metrics-strip" aria-label="Platform metrics">
          <div><span>Total links</span><strong>{totalLinks}</strong><small>created</small></div>
          <div><span>Active links</span><strong>{activeLinks}</strong><small>ready to share</small></div>
          <div><span>Expired</span><strong>{expiredLinks}</strong><small>past deadline</small></div>
          <div className="metric-accent"><span>Infrastructure</span><strong>100%</strong><small>API connected</small></div>
        </section>

        <section className="dashboard" id="dashboard">
          <div className="dashboard-heading">
            <div><div className="eyebrow"><span /> WORKSPACE</div><h2>Your link universe.</h2><p>One place to create, search and understand every short link.</p></div>
            <button className="refresh-button" type="button" onClick={loadLinks} disabled={linksLoading}><Icon>↻</Icon>{linksLoading ? 'Syncing…' : 'Refresh data'}</button>
          </div>

          <div className="workspace-toolbar">
            <div className="search-box"><Icon>⌕</Icon><input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search links or destinations…" /></div>
            <div className="filter-tabs"><button className={filter === 'all' ? 'selected' : ''} onClick={() => setFilter('all')}>All <span>{totalLinks}</span></button><button className={filter === 'active' ? 'selected' : ''} onClick={() => setFilter('active')}>Active <span>{activeLinks}</span></button><button className={filter === 'inactive' ? 'selected' : ''} onClick={() => setFilter('inactive')}>Inactive <span>{expiredLinks + (totalLinks - activeLinks - expiredLinks)}</span></button></div>
          </div>

          <div className="links-panel">
            <div className="links-panel-head"><div><span className="panel-kicker">LINKS</span><h3>Recent activity</h3></div><span className="result-count">{visibleLinks.length} shown</span></div>
            {linksLoading ? <div className="empty-state"><div className="spinner" /><p>Syncing your workspace…</p></div> : visibleLinks.length === 0 ? <div className="empty-state"><div className="empty-icon">⌁</div><h3>{search ? 'No matches' : 'Your workspace is empty'}</h3><p>{search ? 'Try a different search term.' : 'Create a short link above to get started.'}</p></div> : (
              <div className="link-list">
                {visibleLinks.map((link, index) => {
                  const linkUrl = `${SHORTENER_ORIGIN}/${link.short_code}`
                  const expired = isExpired(link)
                  const active = link.is_active && !expired
                  return (
                    <article className="link-row" key={link.id}>
                      <div className="link-index">{String(index + 1).padStart(2, '0')}</div>
                      <div className="link-symbol">↗</div>
                      <div className="link-info"><a href={linkUrl} target="_blank" rel="noreferrer">{linkUrl}</a><p title={link.destination_url}>{link.destination_url}</p></div>
                      <div className={`status ${active ? 'active' : expired ? 'expired' : 'inactive'}`}><span />{active ? 'Active' : expired ? 'Expired' : 'Inactive'}</div>
                      <div className="link-date">{formatDate(link.created_at)}</div>
                      <div className="row-actions"><button type="button" onClick={() => copyLink(link.short_code)}>{copied === link.short_code ? 'Copied' : 'Copy'}</button><button className="analytics-action" type="button" onClick={() => loadAnalytics(link.short_code)} disabled={analyticsLoading}>View analytics</button></div>
                    </article>
                  )
                })}
              </div>
            )}
          </div>

          {analytics && (
            <section className="analytics-detail" id="analytics">
              <div className="analytics-detail-head">
                <div><div className="eyebrow"><span /> LINK INTELLIGENCE</div><h3>Performance snapshot</h3><p>{SHORTENER_ORIGIN}/{analytics.short_code}</p></div>
                <div className="analytics-updated">Updated {formatDateTime(new Date())}</div>
              </div>
              <div className="analytics-metric-grid">
                <div className="analytics-metric"><span>All time</span><strong>{analytics.total_clicks}</strong><small>Total clicks</small><div className="metric-line"><i style={{ width: `${Math.min(100, analytics.total_clicks * 10)}%` }} /></div></div>
                <div className="analytics-metric"><span>Today</span><strong>{analytics.clicks_today}</strong><small>Since midnight</small><div className="metric-line"><i style={{ width: `${Math.min(100, analytics.clicks_today * 20)}%` }} /></div></div>
                <div className="analytics-metric"><span>This week</span><strong>{analytics.clicks_this_week}</strong><small>Current week</small><div className="metric-line"><i style={{ width: `${Math.min(100, analytics.clicks_this_week * 12)}%` }} /></div></div>
                <div className="analytics-metric"><span>This month</span><strong>{analytics.clicks_this_month}</strong><small>Current month</small><div className="metric-line"><i style={{ width: `${Math.min(100, analytics.clicks_this_month * 8)}%` }} /></div></div>
              </div>
            </section>
          )}
        </section>

        <section className="capabilities" id="features">
          <div className="section-heading"><div className="eyebrow"><span /> DESIGNED FOR WHAT'S NEXT</div><h2>A short link is just the beginning.</h2><p>The interface is ready to grow with the backend — analytics, link controls, QR codes, custom domains and more.</p></div>
          <div className="capability-grid">
            <article className="capability-card featured"><div className="cap-icon">◉</div><span>01 / INSIGHT</span><h3>Click intelligence</h3><p>Move from a simple counter to a complete picture of how your links perform.</p><div className="card-arrow">↗</div></article>
            <article className="capability-card"><div className="cap-icon">⌁</div><span>02 / CONTROL</span><h3>Link lifecycle</h3><p>Expiration and activation controls keep shared links under your command.</p><div className="card-arrow">↗</div></article>
            <article className="capability-card"><div className="cap-icon">⌗</div><span>03 / SCALE</span><h3>Link infrastructure</h3><p>Async FastAPI and PostgreSQL give the product a serious foundation.</p><div className="card-arrow">↗</div></article>
          </div>
        </section>
      </main>

      <footer><div className="brand small"><div className="brand-mark"><Icon>↗</Icon></div><span>Smart<span>Shortner</span></span></div><div className="footer-links"><span>FastAPI</span><span>PostgreSQL</span><span>Async</span><span>MIT License</span></div></footer>
    </div>
  )
}

export default App
