# Furnivo Demo

A demo-ready product catalog, quotation system, lead CRM, and marketing website for furniture / interiors / building-material businesses.

## Stack
- Frontend: React + Vite + React Router
- Backend: Flask + Flask-CORS
- Demo fallback: Local seeded data + locally registered demo users in the React app
- Styling: Custom CSS, no UI framework dependency

## Registration
- Public registration is available at `/#/register`.
- New self-registered users receive the safe `client` role.
- Registration works in both Flask API mode and frontend-only demo mode.

## Roles
- Admin: full access
- Sales: catalog, quotes, leads
- Designer: catalog, quotes
- Client: catalog and own-facing dashboard experience

## Demo accounts

| Role | Email | Password |
|---|---|---|
| Admin | admin@furnivo.demo | admin123 |
| Sales | sales@furnivo.demo | sales123 |
| Designer | designer@furnivo.demo | design123 |
| Client | client@furnivo.demo | client123 |

## Run frontend

```bash
cd frontend
npm install
npm run dev
```

The frontend works by itself using dummy data.

## Run backend

```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Then create `frontend/.env`:

```env
VITE_API_URL=http://localhost:5000/api
```

Restart the React dev server.

## Production frontend build

```bash
cd frontend
npm install
npm run build
```

Deploy the `frontend/dist` folder to Netlify, Vercel, Cloudflare Pages, GitHub Pages, or any static host. The app uses hash routing so login/register/dashboard URLs work without special rewrite rules.

If you deploy only the frontend and do not configure `VITE_API_URL`, the app automatically runs in demo mode.

## Suggested feature-wise Git commits

1. `chore: initialize react vite and flask project structure`
2. `feat: add trusted light visual system and shared layout styles`
3. `feat: build responsive marketing landing page`
4. `feat: add login and secure client registration flows`
5. `feat: add auth context and protected routes`
6. `feat: add role based navigation and dashboard`
7. `feat: add catalog browsing search and category filters`
8. `feat: add quotation builder and quotation history`
9. `feat: add lead crm pipeline and stage updates`
10. `feat: add offline demo data adapter and api fallback`
11. `feat: add flask authentication and catalog endpoints`
12. `feat: add flask quotation and lead crm endpoints`
13. `fix: add mobile navigation card tables touch targets and responsive polish`
14. `docs: add local setup deployment and demo credentials`

## Enhancement roadmap: demo to production

The included project is suitable for a portfolio, stakeholder demo, or frontend-first prototype. For a real business deployment, enhance it in these stages:

### Priority 1: production foundation
- PostgreSQL/MySQL database instead of in-memory Flask lists
- SQLAlchemy models and migrations
- Password hashing with Werkzeug/Bcrypt/Argon2
- Persistent JWT/session authentication with refresh/expiry strategy
- Server-side role and permission checks on every protected operation
- Environment-based secrets and CORS configuration
- Validation, rate limiting, structured error handling and audit logging

### Priority 2: furniture commerce workflow
- Product CRUD with categories, collections, brands, finishes, dimensions and variants
- Product image/file upload through cloud storage
- Customer/company records and project addresses
- Quote line items, quantity, unit, discounts, taxes, shipping and terms
- Quote PDF generation, version history and approve/reject flow
- Lead notes, reminders, tasks, owner assignment and activity timeline
- Lead-to-customer / lead-to-quotation conversion
- Search, pagination and server-side filters

### Priority 3: business polish
- Dashboard analytics from real data
- Email/WhatsApp notification integrations
- Export CSV/Excel and printable reports
- Saved product collections / wishlists
- Accessibility review and keyboard support
- Automated frontend/backend tests
- Error monitoring and analytics
- PWA/offline caching if field sales staff need unreliable-network support
- Image optimization and CDN delivery

## Responsive coverage in this version

The UI now has breakpoints and layout behavior for large desktop, laptop/tablet, mobile and compact phones. It includes a mobile landing-page menu, compact workspace navigation, horizontally scrollable catalog filters, stacked forms, card-style quotation rows on phones, larger touch targets, dynamic viewport support and safe-area spacing.

## Recommended commits for this v2 enhancement

1. `feat: add public client registration flow`
2. `feat: add flask register endpoint and offline registered users`
3. `feat: add responsive mobile marketing navigation`
4. `fix: optimize workspace navigation forms and quote tables for phones`
5. `chore: switch frontend to hash routing for static demo deployments`
6. `docs: document production enhancement roadmap and responsive coverage`
