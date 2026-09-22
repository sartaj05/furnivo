# Furnivo V3

A responsive furniture / interiors / building-material sales suite built with React + Vite and Flask. It includes a marketing website, secure role-based workspace, catalog management, quotations, customers and lead CRM. The React app keeps an offline demo fallback so the UI remains usable without the API.

## V3 production features

1. **SQLAlchemy database foundation** with SQLite zero-config local development and `DATABASE_URL` support for PostgreSQL/MySQL. Flask-Migrate is wired for schema migrations.
2. **Secure authentication** with Werkzeug password hashing, JWT access tokens and server-side role checks.
3. **Product CRUD** for admins with search/category browsing for all allowed roles.
4. **Product variants** including finish, dimensions, variant SKU, stock status and price delta.
5. **Image upload workflow** using Cloudinary when `CLOUDINARY_URL` exists and local file storage otherwise. The frontend-only demo uses browser data URLs.
6. **Quotation line items** with products, variants, quantities, units and editable pricing.
7. **Quotation PDF generation** with ReportLab on Flask and jsPDF as the frontend-only fallback.
8. **Commercial calculations** including percentage discount, tax/GST, shipping and grand totals.
9. **Customer records** with company, contact, email, phone, GSTIN, billing address and project/delivery address.
10. **Lead follow-up workspace** with stages, owners, notes, tasks/reminders and activity context.
11. **Production planning and BOMs** with job cards, material quantities, wastage and production stages.
12. **Payment reconciliation** with settlement records, failed/disputed payments, partial refunds and invoice balance updates.
13. **Digital contracts and e-signatures** with locked signed versions and downloadable PDFs.
14. **Customer project portal** with production progress, schedules, invoices, documents and support requests.
15. **Operations tooling** with health checks, request IDs, rate limiting, database backups and admin deployment checks.
16. **Automated test and CI pipeline** with backend API tests, frontend component tests, coverage output and GitHub Actions.
17. **Secure session controls** with refresh rotation, logout/revocation, MFA challenges and secure cookies.
18. **GST workflows** with CGST/SGST/IGST calculations, HSN/SAC data, e-invoice records and e-way bills.
19. **Provider payment automation** with idempotency, dispute webhooks, live-ready refunds and payment receipts.
20. **Scalable data administration** with pagination, search, archived records, CSV imports and asynchronous jobs.

## Existing experience

- Responsive landing page and mobile navigation
- Login + public client registration
- Roles: `admin`, `sales`, `designer`, `client`
- Role-aware workspace navigation
- Frontend-only demo data fallback
- Hash routing for static hosting
- Responsive catalog, quote builder, customer records and CRM

## Demo accounts

| Role | Email | Password |
|---|---|---|
| Admin | `admin@furnivo.demo` | `admin123` |
| Sales | `sales@furnivo.demo` | `sales123` |
| Designer | `designer@furnivo.demo` | `design123` |
| Client | `client@furnivo.demo` | `client123` |

> Demo passwords are intentionally simple. Change/remove these seed credentials before a real deployment.

## Frontend-only demo

```bash
cd frontend
npm install
npm run dev
```

Do not set `VITE_API_URL` and the app uses local seeded data. CRUD-style demo changes are stored in browser `localStorage`.

## Run full React + Flask stack

Create a Python environment from the project root:

```bash
python -m venv .venv
# macOS/Linux
source .venv/bin/activate
# Windows PowerShell
# .venv\Scripts\Activate.ps1

pip install -r backend/requirements.txt
```

Copy `backend/.env.example` values into your environment as needed. SQLite is the default, so a separate database server is not required for local development.

Run the API:

```bash
python -m backend.app
```

The demo data is seeded automatically when `AUTO_SEED=true`.

Create `frontend/.env`:

```env
VITE_API_URL=http://localhost:5000/api
```

Then:

```bash
cd frontend
npm install
npm run dev
```

## PostgreSQL or MySQL

Set `DATABASE_URL` before starting Flask.

```env
# PostgreSQL
DATABASE_URL=postgresql+psycopg://user:password@localhost/furnivo

# MySQL
DATABASE_URL=mysql+pymysql://user:password@localhost/furnivo
```

For production, use migrations instead of relying on auto-seeding/table creation:

```bash
export FLASK_APP=backend.app
flask db init       # first time only if a migrations folder is not present
flask db migrate -m "initial schema"
flask db upgrade
```

Set `AUTO_SEED=false` in production.

The admin Operations screen is available at `/app/operations`. It exposes database health, payment provider configuration, rate-limit settings and manual backups. SQLite backups are copied locally; PostgreSQL and MySQL backups require `pg_dump` or `mysqldump` on the deployment host. Keep generated backups in external durable storage for real disaster recovery.

## Cloud product images

Without Cloudinary configuration, Flask saves images in `backend/uploads` and serves them from `/uploads/...`.

To use Cloudinary, set:

```env
CLOUDINARY_URL=cloudinary://API_KEY:API_SECRET@CLOUD_NAME
```

No React changes are required.

## Responsive targets

The UI is designed for approximately:

- compact phones: 320–420 px
- modern phones: 390–480 px
- tablets: 768–1024 px
- laptops/desktops: 1024 px+

Forms collapse to one column, quote lines reflow, tables use mobile card labels, filters remain scrollable, and the workspace navigation switches to a compact mobile arrangement.

## Git / GitHub

This ZIP already contains an initialized `.git` repository on the `main` branch with the full feature history and `.github/workflows/ci.yml`.

After creating an empty GitHub repository, connect and push it:

```bash
git remote add origin https://github.com/YOUR_USERNAME/furnivo.git
git push -u origin main
```

No GitHub remote is embedded in the ZIP because that requires your own GitHub account/repository URL.

## Free deployment

See [DEPLOYMENT.md](DEPLOYMENT.md) for the reusable Render, Supabase, Cloudinary, Vercel, secrets, health-check, and GitHub deployment guide. The repository includes `render.yaml`, a public database-aware `/api/health` endpoint, Cloudinary-backed product/field-proof upload routes, and an optional five-minute GitHub Actions health workflow. Add real provider values only in hosting secrets after pushing to your own GitHub repository.

## Feature-wise commit history

```text
chore: baseline responsive furnivo demo
feat: add sqlalchemy database foundation and migrations
feat: secure authentication with password hashing and jwt
feat: add product catalog crud api and admin controls
feat: add product variants finishes and dimensions
feat: add local and cloud ready image upload workflow
feat: build quotation line item workflow
feat: add quotation pdf generation and download
feat: add tax discount shipping and quote totals
feat: add customer company and project address records
feat: add lead notes tasks owners and activity timeline
```

## Recommended next production work

After these ten features, the highest-value additions are automated tests, refresh-token/session strategy, rate limiting, audit logs, email/WhatsApp notifications, CSV/Excel exports, dashboard analytics from live data, quote approval/version history, server-side pagination and object-level authorization for client users.
