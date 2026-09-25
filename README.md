# Furnivo

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
21. **Quote-to-payment automation** where client approval creates a contract, signing creates a deposit order/invoice, and successful payment activates the order.
22. **Furniture visual configurator MVP** with selectable materials, fabrics, colors, finishes, dimensions, live server-validated pricing, saved specifications and direct quotation handoff.
23. **Business control center** with BOM costing, wastage-aware material planning, stock reservations, shortage and purchase-order suggestions, project profitability, timeline events and notification automation templates.
24. **Mobile production execution** with QR visit check-in/out, GPS/proof capture, worker time tracking, material issue/return records and offline sync.
25. **Supplier procurement automation** with planning-shortage-to-PO conversion, supplier quote references, landed cost, delivery dates, quality ratings and supplier performance.
26. **Delivery and installation management** with ETA, assigned teams, customer confirmation, completion proof and delivery status workflows.
27. **Accounting control center** with invoice collection summaries, overdue tracking, payment reminder generation and accounting integration support.
28. **Enterprise branch security** with branches, user assignments, branch-linked warehouses and protected access boundaries.
29. **Notification automation** with role broadcasts, provider delivery tracking, retry visibility and demo-safe fallback.
30. **Delivery route planning** with driver data, stop ordering, route optimization and estimated route distance.
31. **Warranty service operations** with technician work fields, parts used, visit scheduling, SLA follow-up and customer feedback ratings.
32. **Advanced production scheduling** with workshop tasks, worker/machine capacity, dependencies and deadline alerts.
33. **Customer mobile self-service portal** with project summaries, delivery ETA, invoices, warranties and service requests.
34. **Furniture recommendation engine** with room, material, color and budget-based product suggestions.
35. **Inventory forecasting** using open production BOM demand, reorder levels, projected stock and stockout risk.
36. **Quality control workflow** with inspection checklists, defect notes, photo-ready evidence, approval gates and rework status.
32. **Advanced production scheduling** with workshop tasks, worker/machine capacity, dependencies and deadline alerts.
33. **Customer mobile self-service portal** with project summaries, delivery ETA, invoices, warranties and service requests.
34. **Furniture recommendation engine** with room, material, color and budget-based product suggestions.
35. **Inventory forecasting** using open production BOM demand, reorder levels, projected stock and stockout risk.
36. **Quality control workflow** with inspection checklists, defect notes, photo-ready evidence, approval gates and rework status.
27. **Accounting control center** with invoice collection summaries, overdue tracking, payment reminder generation and accounting integration support.
28. **Enterprise branch security** with branches, user assignments, branch-linked warehouses and protected access boundaries.
29. **Notification automation** with role broadcasts, provider delivery tracking, retry visibility and demo-safe fallback.
30. **Delivery route planning** with driver data, stop ordering, route optimization and estimated route distance.
31. **Warranty service operations** with technician work fields, parts used, visit scheduling, SLA follow-up and customer feedback ratings.

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

## Fresh setup on another computer

These steps assume Windows PowerShell and start from the project root. The same project also works on macOS/Linux with the equivalent virtual-environment activation command.

### 1. Create the Python environment

```powershell
cd "D:\New folder (3)\furnivo"
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r backend\requirements.txt
```

If PowerShell blocks activation, run this once in a PowerShell window for your user account:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

SQLite is the default local database, so no separate database server is required. Optional backend settings are documented in [backend/.env.example](backend/.env.example).

### 2. Apply database migrations

Run this from the project root using the project virtual environment:

```powershell
.\.venv\Scripts\python.exe -m flask --app backend.app db upgrade
```

The current contact-inquiry migration completed successfully with:

```text
Running upgrade i8d1f7a45b93 -> j9e2b8c56d04, add public contact fields to leads
```

If the terminal is already inside the `backend` directory, use `app` instead of `backend.app`:

```powershell
..\.venv\Scripts\python.exe -m flask --app app db upgrade
```

Do not use `--app backend.app` while already inside `backend`; that makes Flask search for `backend.backend.app`.

### 3. Start the Flask backend

From the project root:

```powershell
.\.venv\Scripts\python.exe -m backend.app
```

The API runs at `http://localhost:5000`. The health endpoint is `http://localhost:5000/api/health`.

Alternatively, from inside `backend`:

```powershell
..\.venv\Scripts\python.exe app.py
```

For local development, `AUTO_SEED=true` creates or updates demo data. For production, use `AUTO_SEED=false` and run migrations explicitly.

### 4. Start the React frontend

Open a second terminal from the project root:

```powershell
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`. To connect React to the Flask API, create `frontend/.env` with:

```env
VITE_API_URL=http://localhost:5000/api
```

If `VITE_API_URL` is missing or the API is unavailable, the frontend automatically uses its local demo data and stores changes in browser `localStorage`.

### 5. Verify the installation

Run these checks from the project root:

```powershell
.\.venv\Scripts\python.exe -m pytest -q backend\tests
cd frontend
npm test -- --run
npm run build
```

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

When your terminal is already inside `backend`, this also works:

```powershell
python app.py
```

For production, use the configured Gunicorn/Render start command instead of Flask's development server.

The demo data is seeded automatically when `AUTO_SEED=true`.
On local development SQLite, startup also applies pending migrations and repairs columns from older demo databases before seeding. Production keeps migrations explicit through the Render start command.

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

## Remaining features and deployment gaps

The main Furnivo business workflow is implemented. The remaining work is mostly production integration, operations and hardening rather than missing screens.

The latest feature update adds:

- AI design assistant briefs with room/style/material/color inputs, optional image URL, product recommendations, a deterministic demo fallback, and an optional `OPENAI_API_KEY` provider hook.
- Drag-and-drop production Gantt dependencies backed by production task APIs.
- Live collaboration activity feed backed by audit events and demo-safe polling.
- Predictive supplier lead times, quality defect/rework metrics, and purchase recommendations.
- Multi-tenant workspace creation/switching with membership, subscription-plan foundations, and active workspace tracking.

The AI assistant works in demo mode without credentials. Configure `OPENAI_API_KEY` and `OPENAI_DESIGN_MODEL` only when the OpenAI provider is ready; the key is read server-side and is never returned by the API.

The latest feature update adds:

- AI design assistant briefs with room/style/material/color inputs, optional image URL, product recommendations, a deterministic demo fallback, and an optional `OPENAI_API_KEY` provider hook.
- Drag-and-drop production Gantt dependencies backed by production task APIs.
- Live collaboration activity feed backed by audit events and demo-safe polling.
- Predictive supplier lead times, quality defect/rework metrics, and purchase recommendations.
- Multi-tenant workspace creation/switching with membership, subscription-plan foundations, and active workspace tracking.

The AI assistant works in demo mode without credentials. Configure `OPENAI_API_KEY` and `OPENAI_DESIGN_MODEL` only when the OpenAI provider is ready; the key is read server-side and is never returned by the API.

### Ready for deployment

- The frontend runs with demo data when `VITE_API_URL` is missing or the API is unavailable.
- The frontend uses the Flask API when `VITE_API_URL` is configured and reachable.
- Render configuration, PostgreSQL migrations, Cloudinary uploads, `/api/health`, CI checks and an optional deploy hook are included.
- The current setup is suitable for a preview, demo or early client deployment after configuring the provider secrets in [DEPLOYMENT.md](DEPLOYMENT.md).

### Remaining high-priority work

1. **Real provider configuration and verification**
   - Connect and test the selected Stripe/Razorpay account, HTTP email provider, WhatsApp provider and accounting provider for the new quote-to-payment workflow.
   - Configure signed webhook verification, live refund settings, retry delivery and failure alerts.
   - The application safely defaults to demo providers until these values are configured.

2. **Staging and production environments**
   - Use separate Supabase databases, Render services, Cloudinary folders and secrets.
   - Run migrations and smoke tests in staging before changing production.
   - Add a manual production approval and rollback procedure.

3. **External backup and restore automation**
   - Schedule PostgreSQL backups outside the application filesystem.
   - Keep retention copies and verify that a backup can be restored.
   - The Operations screen can create/list backups, but hosted backups still need durable external storage.

4. **Production security hardening**
   - Add login lockout and stronger administrator controls.
   - Review every client-owned record and sensitive action with production test accounts.
   - Add secret rotation, security headers, centralized error monitoring and alerting.

5. **Broader automated testing**
   - Add end-to-end tests for login, client quote approval, order conversion, payments, uploads, field proof and portal access.
   - Add PostgreSQL integration tests and coverage thresholds for important backend routes.

6. **Reliable background processing**
   - Move notification retries, report refreshes, catalog indexing and scheduled reminders to an external worker or scheduler when usage grows.
   - The current in-process job runner is suitable for low-volume deployments only.

7. **Advanced reporting and integrations**
   - Add live profit-margin forecasting, capacity forecasting and customer lifetime value.
   - Complete provider-specific accounting sync and GST/e-invoice production adapters.

### Recommended order before real customer data

1. Configure Supabase, Cloudinary, Render secrets and the frontend API URL.
2. Keep `AUTO_SEED=false` and remove or change all demo credentials.
3. Deploy and verify `/api/health`, login, database migrations, uploads and client record isolation.
4. Configure external backups and test a restore.
5. Enable real payment/notification providers only after their webhooks and failure paths are tested.

The project does not need another business feature before the first deployment. The next best implementation is staging/production separation followed by external backups and full end-to-end deployment testing.
