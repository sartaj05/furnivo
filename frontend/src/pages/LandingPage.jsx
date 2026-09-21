import { useState } from 'react'
import { Link } from 'react-router-dom'

const features = [
  {
    number: '01',
    title: 'Living product catalog',
    text: 'Present furniture, surfaces and interior materials with category, pricing, SKU and material details in one clean sales-ready library.',
  },
  {
    number: '02',
    title: 'Fast quotations',
    text: 'Turn selections into consistent customer quotations, track status and keep every commercial conversation easier to follow.',
  },
  {
    number: '03',
    title: 'Lead CRM',
    text: 'Capture enquiries, track deal value and move leads from new enquiry to qualified, proposal and won stages.',
  },
  {
    number: '04',
    title: 'Role-based workspace',
    text: 'Give admins, sales teams, designers and clients only the screens and controls they actually need.',
  },
]

export default function LandingPage() {
  const [menuOpen, setMenuOpen] = useState(false)

  return (
    <div className="marketing-page">
      <nav className="top-nav container">
        <Link className="brand" to="/">
          <span className="brand-mark">F</span>
          <span>Furnivo</span>
        </Link>

        <div className={menuOpen ? "nav-links nav-links-open" : "nav-links"}>
          <a href="#platform" onClick={() => setMenuOpen(false)}>Platform</a>
          <a href="#trust" onClick={() => setMenuOpen(false)}>Why Furnivo</a>
          <a href="#contact" onClick={() => setMenuOpen(false)}>Contact</a>
          <Link className="mobile-menu-link" to="/login">Sign in</Link>
          <Link className="mobile-menu-link" to="/register">Register</Link>
        </div>

        <div className="top-nav-actions">
          <Link className="nav-signin" to="/login">Sign in</Link>
          <Link className="button button-small" to="/register">Register</Link>
          <button
            className="mobile-nav-toggle"
            type="button"
            aria-label="Toggle navigation"
            aria-expanded={menuOpen}
            onClick={() => setMenuOpen((value) => !value)}
          >
            <span />
            <span />
            <span />
          </button>
        </div>
      </nav>

      <main>
        <section className="hero container">
          <div className="hero-copy">
            <span className="pill">Built for furniture, interiors & materials</span>
            <h1>
              Sell the space,
              <span>not the spreadsheet.</span>
            </h1>
            <p>
              A calm business suite for product discovery, quotations and lead follow-up.
              Built to make your brand feel considered before a salesperson even joins the conversation.
            </p>
            <div className="hero-actions">
              <Link className="button" to="/register">Create free demo account</Link>
              <a className="button button-ghost" href="#platform">See platform</a>
            </div>
            <div className="proof-row">
              <span>Catalog</span>
              <span>Quotation</span>
              <span>CRM</span>
              <span>Role access</span>
            </div>
          </div>

          <div className="hero-visual">
            <div className="visual-main">
              <img
                src="https://images.unsplash.com/photo-1600210492486-724fe5c67fb0?auto=format&fit=crop&w=1200&q=85"
                alt="Warm modern interior"
              />
              <div className="floating-card floating-card-left">
                <span>Pipeline</span>
                <strong>₹16.15L</strong>
                <small>Active opportunity value</small>
              </div>
            </div>
            <div className="floating-card floating-card-right">
              <span>Quotation Q-1042</span>
              <strong>₹1,86,400</strong>
              <small className="success-text">Sent to Northline Studio</small>
            </div>
          </div>
        </section>

        <section className="trust-strip" id="trust">
          <div className="container trust-grid">
            <div>
              <strong>One source of truth</strong>
              <span>for products and pricing</span>
            </div>
            <div>
              <strong>Fewer missed leads</strong>
              <span>with clear sales stages</span>
            </div>
            <div>
              <strong>Faster follow-up</strong>
              <span>with quote history in context</span>
            </div>
            <div>
              <strong>Demo-ready</strong>
              <span>even when the API is offline</span>
            </div>
          </div>
        </section>

        <section className="section container" id="platform">
          <div className="section-heading">
            <div>
              <p className="eyebrow">Platform</p>
              <h2>A showroom brain for the business behind the showroom.</h2>
            </div>
            <p>
              The interface uses warm neutrals, deep green and restrained terracotta to create
              a calm, premium visual identity that feels appropriate for design-led businesses.
            </p>
          </div>

          <div className="feature-grid">
            {features.map((feature) => (
              <article className="feature-card" key={feature.number}>
                <span>{feature.number}</span>
                <h3>{feature.title}</h3>
                <p>{feature.text}</p>
              </article>
            ))}
          </div>
        </section>

        <section className="showcase container">
          <div className="showcase-image">
            <img
              src="https://images.unsplash.com/photo-1600566753190-17f0baa2a6c3?auto=format&fit=crop&w=1200&q=85"
              alt="Interior materials and furniture"
            />
          </div>
          <div className="showcase-copy">
            <p className="eyebrow">Built for trust</p>
            <h2>Quiet design. Clear information. No dashboard carnival.</h2>
            <p>
              Customers see a composed catalog. Sales teams see pricing and pipeline.
              Designers see products and quotations. Admins get the complete operational view.
            </p>
            <Link to="/register" className="text-link">Create an account and enter the workspace →</Link>
          </div>
        </section>

        <section className="cta-section" id="contact">
          <div className="container cta-inner">
            <div>
              <p className="eyebrow">Ready for a walkthrough</p>
              <h2>Bring catalog, quotes and enquiries into one polished experience.</h2>
            </div>
            <Link className="button button-light" to="/register">Create account</Link>
          </div>
        </section>
      </main>

      <footer className="footer container">
        <Link className="brand" to="/">
          <span className="brand-mark">F</span>
          <span>Furnivo</span>
        </Link>
        <span>Furniture commerce, minus the operational clutter.</span>
      </footer>
    </div>
  )
}
