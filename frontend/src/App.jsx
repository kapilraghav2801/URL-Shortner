import { useState } from 'react'

const API_BASE = import.meta.env.VITE_API_BASE || ''

function Icon({ children }) {
  return <span className="icon" aria-hidden="true">{children}</span>
}

function App() {
  const [destinationUrl, setDestinationUrl] = useState('')
  const [shortCode, setShortCode] = useState('')
  const [result, setResult] = useState(null)
  const [analytics, setAnalytics] = useState(null)
  const [loading, setLoading] = useState(false)
  const [analyticsLoading, setAnalyticsLoading] = useState(false)
  const [error, setError] = useState('')
  const [copied, setCopied] = useState(false)

  async function shortenUrl(event) {
    event.preventDefault()
    setError('')
    setResult(null)
    setAnalytics(null)
    setCopied(false)
    setLoading(true)

    try {
      const response = await fetch(`${API_BASE}/api/v1/links`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          destination_url: destinationUrl,
          short_code: shortCode.trim(),
        }),
      })

      const data = await response.json()
      if (!response.ok) {
        throw new Error(data.detail || 'Could not create the link.')
      }

      setResult(data)
    } catch (err) {
      setError(err.message || 'Something went wrong.')
    } finally {
      setLoading(false)
    }
  }

  async function loadAnalytics() {
    if (!result?.short_code) return
    setAnalyticsLoading(true)
    setError('')

    try {
      const response = await fetch(
        `${API_BASE}/api/v1/links/${encodeURIComponent(result.short_code)}/analytics`,
      )
      const data = await response.json()
      if (!response.ok) throw new Error(data.detail || 'Could not load analytics.')
      setAnalytics(data)
    } catch (err) {
      setError(err.message || 'Could not load analytics.')
    } finally {
      setAnalyticsLoading(false)
    }
  }

  async function copyLink() {
    if (!result?.short_code) return
    const origin = window.location.origin
    const link = `${origin}/${result.short_code}`
    await navigator.clipboard.writeText(link)
    setCopied(true)
    window.setTimeout(() => setCopied(false), 1800)
  }

  const shortLink = result ? `${window.location.origin}/${result.short_code}` : ''

  return (
    <div className="app-shell">
      <header className="navbar">
        <div className="brand">
          <div className="brand-mark"><Icon>↗</Icon></div>
          <span>Smart<span>Shortner</span></span>
        </div>
        <nav className="nav-links">
          <a href="#home">Home</a>
          <a href="#features">Features</a>
          <a href="#analytics">Analytics</a>
        </nav>
        <a className="github-link" href="https://github.com/kapilraghav2801/URL-Shortner" target="_blank" rel="noreferrer">
          GitHub ↗
        </a>
      </header>

      <main id="home">
        <section className="hero">
          <div className="eyebrow"><span /> LINK INFRASTRUCTURE, SIMPLIFIED</div>
          <h1>Short links.<br /><em>Big possibilities.</em></h1>
          <p className="hero-copy">
            Turn long URLs into clean, memorable links — then track every click with a fast, production-ready backend.
          </p>

          <form className="shortener-card" onSubmit={shortenUrl}>
            <div className="field-row">
              <div className="input-wrap main-input">
                <Icon>↗</Icon>
                <input
                  type="url"
                  value={destinationUrl}
                  onChange={(event) => setDestinationUrl(event.target.value)}
                  placeholder="Paste your long URL here..."
                  required
                />
              </div>
              <button className="primary-button" type="submit" disabled={loading}>
                {loading ? 'Creating...' : 'Shorten URL'}
                {!loading && <span>→</span>}
              </button>
            </div>
            <div className="custom-row">
              <label htmlFor="short-code">Custom short code <span>optional</span></label>
              <div className="input-wrap custom-input">
                <span className="prefix">smart.ly/</span>
                <input
                  id="short-code"
                  value={shortCode}
                  onChange={(event) => setShortCode(event.target.value.replace(/\s/g, ''))}
                  placeholder="my-link"
                  maxLength={64}
                />
              </div>
            </div>
          </form>

          {error && <div className="alert error">{error}</div>}

          {result && (
            <section className="result-card" aria-live="polite">
              <div className="result-icon">✓</div>
              <div className="result-content">
                <span className="result-label">YOUR SHORT LINK</span>
                <a href={shortLink} target="_blank" rel="noreferrer">{shortLink}</a>
                <p title={result.destination_url}>→ {result.destination_url}</p>
              </div>
              <div className="result-actions">
                <button className="secondary-button" onClick={copyLink}>{copied ? 'Copied!' : 'Copy link'}</button>
                <button className="ghost-button" onClick={loadAnalytics} disabled={analyticsLoading}>
                  {analyticsLoading ? 'Loading...' : 'View clicks'}
                </button>
              </div>
            </section>
          )}

          {analytics && (
            <div className="analytics-card" id="analytics">
              <div>
                <span className="result-label">LINK ANALYTICS</span>
                <strong>{analytics.total_clicks}</strong>
                <span className="muted"> total clicks</span>
              </div>
              <div className="analytics-code">smart.ly/{analytics.short_code}</div>
            </div>
          )}
        </section>

        <section className="trust-strip">
          <span>BUILT FOR THE NEXT STAGE</span>
          <div><b>FastAPI</b><b>PostgreSQL</b><b>Async</b><b>Analytics-ready</b></div>
        </section>

        <section className="features" id="features">
          <div className="section-heading">
            <div className="eyebrow"><span /> WHY SMART SHORTNER</div>
            <h2>More than a shorter URL.</h2>
            <p>A clean foundation today, with room to grow into the link platform you actually want.</p>
          </div>
          <div className="feature-grid">
            <article><div className="feature-number">01</div><h3>Custom links</h3><p>Choose memorable short codes instead of random-looking URLs.</p></article>
            <article><div className="feature-number">02</div><h3>Click tracking</h3><p>Every redirect can record click events and request metadata.</p></article>
            <article><div className="feature-number">03</div><h3>Built to scale</h3><p>Async FastAPI, PostgreSQL and a layered architecture give us a strong base.</p></article>
          </div>
        </section>
      </main>

      <footer><div className="brand small"><div className="brand-mark"><Icon>↗</Icon></div><span>Smart<span>Shortner</span></span></div><span>Built with purpose · MIT License</span></footer>
    </div>
  )
}

export default App
