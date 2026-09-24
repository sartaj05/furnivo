import { useEffect, useState } from 'react'
import { Link, Navigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { submitContactInquiry } from '../lib/api'

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

const initialContactForm = {
  name: '',
  company: '',
  email: '',
  phone: '',
  interest: 'General enquiry',
  message: '',
  website: '',
}

export default function LandingPage() {
  const user = useAuth()?.user
  const [menuOpen, setMenuOpen] = useState(false)
  const [contactForm, setContactForm] = useState(initialContactForm)
  const [contactStatus, setContactStatus] = useState({ type: '', message: '' })
  const [contactSubmitting, setContactSubmitting] = useState(false)

  useEffect(() => {
    const sectionId = new URLSearchParams(window.location.search).get('section')
    if (!sectionId) return undefined

    const timer = window.setTimeout(() => {
      document.getElementById(sectionId)?.scrollIntoView({ block: 'start' })
    }, 0)

    return () => window.clearTimeout(timer)
  }, [])

  const navigateToSection = (event, sectionId) => {
    event.preventDefault()
    setMenuOpen(false)

    const url = new URL(window.location.href)
    url.searchParams.set('section', sectionId)
    window.history.replaceState(null, '', url.toString())
    document.getElementById(sectionId)?.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }

  async function submitContact(event) {
    event.preventDefault()
    setContactSubmitting(true)
    setContactStatus({ type: '', message: '' })
    try {
      const result = await submitContactInquiry(contactForm)
      setContactStatus({ type: 'success', message: result.message || 'Thanks, your enquiry has been received.' })
      setContactForm(initialContactForm)
    } catch (error) {
      setContactStatus({ type: 'error', message: error.message || 'We could not send your enquiry. Please try again.' })
    } finally {
      setContactSubmitting(false)
    }
  }

  if (user) return <Navigate to="/app" replace />

  return (
    <div className="marketing-page">
      <nav className="top-nav container">
        <Link className="brand" to="/">
          <span className="brand-mark">F</span>
          <span>Furnivo</span>
        </Link>

        <div className={menuOpen ? "nav-links nav-links-open" : "nav-links"}>
          <a href="/?section=platform" onClick={(event) => navigateToSection(event, 'platform')}>Platform</a>
          <a href="/?section=why-furnivo" onClick={(event) => navigateToSection(event, 'why-furnivo')}>Why Furnivo</a>
          <a href="/?section=contact" onClick={(event) => navigateToSection(event, 'contact')}>Contact</a>
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
              <a className="button button-ghost" href="/?section=platform" onClick={(event) => navigateToSection(event, 'platform')}>See platform</a>
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

        <section className="why-section" id="why-furnivo">
          <div className="container">
            <div className="section-heading">
              <div>
                <p className="eyebrow">Why Furnivo</p>
                <h2>Less chasing. More considered customer conversations.</h2>
              </div>
              <p>
                Furnivo gives furniture and interior teams one calm workspace for the details
                that usually get scattered across spreadsheets, chats and follow-up calls.
              </p>
            </div>
            <div className="why-grid">
              <article className="why-card why-card-feature">
                <span className="why-card-kicker">Designed around your workflow</span>
                <h3>From first enquiry to final installation.</h3>
                <p>Keep product choices, pricing, approvals, production updates and customer context connected from the first conversation.</p>
                <ul className="why-list">
                  <li><strong>For sales</strong><span>Faster quotes and a clearer follow-up rhythm.</span></li>
                  <li><strong>For designers</strong><span>Detailed furniture configurations that production can understand.</span></li>
                  <li><strong>For operations</strong><span>Inventory, schedules, deliveries and service in one view.</span></li>
                </ul>
              </article>
              <aside className="why-proof">
                <p className="eyebrow">A better operating picture</p>
                <div><strong>01</strong><span>One connected customer record</span></div>
                <div><strong>02</strong><span>Demo mode when the API is offline</span></div>
                <div><strong>03</strong><span>Real workflows when your team is ready</span></div>
              </aside>
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
            <h2>Quiet design. Clear information. Focused workflows.</h2>
            <p>
              Customers see a composed catalog. Sales teams see pricing and pipeline.
              Designers see products and quotations. Admins get the complete operational view.
            </p>
            <Link to="/register" className="text-link">Create an account and enter the workspace →</Link>
          </div>
        </section>

        <section className="contact-section" id="contact">
          <div className="container">
            <div className="section-heading contact-heading">
              <div>
                <p className="eyebrow">Contact Furnivo</p>
                <h2>Tell us what you are building.</h2>
              </div>
              <p>Share a little about your furniture, interiors or materials workflow. Our team will get back to you with a useful next step.</p>
            </div>
            <div className="contact-grid">
              <div className="contact-details">
                <p className="contact-intro">Whether you are replacing scattered tools or planning your first operational workspace, we can help you map the right starting point.</p>
                <div className="contact-detail"><span>General enquiries</span><a href="mailto:hello@furnivo.in">hello@furnivo.in</a></div>
                <div className="contact-detail"><span>Sales & walkthroughs</span><a href="mailto:hello@furnivo.in">Book a conversation</a></div>
                <div className="contact-detail"><span>Typical response</span><strong>Within one business day</strong></div>
                <Link className="text-link" to="/register">Prefer to explore first? Create a free demo account →</Link>
              </div>
              <form className="contact-form" onSubmit={submitContact}>
                <div className="contact-form-grid">
                  <label>Name<input required minLength="2" value={contactForm.name} onChange={(event) => setContactForm({ ...contactForm, name: event.target.value })} placeholder="Your name" /></label>
                  <label>Company<input value={contactForm.company} onChange={(event) => setContactForm({ ...contactForm, company: event.target.value })} placeholder="Studio or company" /></label>
                  <label>Email<input required type="email" value={contactForm.email} onChange={(event) => setContactForm({ ...contactForm, email: event.target.value })} placeholder="you@company.com" /></label>
                  <label>Phone <span className="optional-label">optional</span><input type="tel" value={contactForm.phone} onChange={(event) => setContactForm({ ...contactForm, phone: event.target.value })} placeholder="+91" /></label>
                  <label className="contact-form-span">What can we help with?<select value={contactForm.interest} onChange={(event) => setContactForm({ ...contactForm, interest: event.target.value })}><option>General enquiry</option><option>Catalog & products</option><option>Quotations</option><option>Design consultation</option><option>Production & delivery</option></select></label>
                  <label className="contact-form-span">Project details<textarea required minLength="10" rows="5" value={contactForm.message} onChange={(event) => setContactForm({ ...contactForm, message: event.target.value })} placeholder="Tell us what you would like to improve…" /></label>
                  <input className="contact-honeypot" tabIndex="-1" autoComplete="off" aria-hidden="true" value={contactForm.website} onChange={(event) => setContactForm({ ...contactForm, website: event.target.value })} />
                </div>
                {contactStatus.message && <p className={`contact-status contact-status-${contactStatus.type}`} role="status">{contactStatus.message}</p>}
                <button className="button" type="submit" disabled={contactSubmitting}>{contactSubmitting ? 'Sending…' : 'Send enquiry'}</button>
              </form>
            </div>
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
