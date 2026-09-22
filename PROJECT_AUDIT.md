# Furnivo project audit

## Current status

The application is a working React/Vite + Flask/SQLAlchemy sales workspace. The frontend can run without Flask by using seeded browser data, and it uses the Flask API whenever `VITE_API_URL` is configured and reachable.

## Working features

- Marketing landing page with responsive navigation and registration CTA.
- Login and public registration with four roles: admin, sales, designer and client.
- Role-aware navigation and protected routes.
- Product catalog browsing, search and category filters.
- Admin product create, edit and archive flows.
- Product variants for finish, dimensions, price delta and stock status.
- Product image upload through Cloudinary or local Flask storage; browser data URL in demo mode.
- Quotation builder with products, variants, quantities, discount, tax/GST, shipping and totals.
- Quote PDF download through Flask/ReportLab or jsPDF in demo mode.
- Quote status changes for admin and sales.
- Customer records with project/billing information and GSTIN.
- Lead CRM with stage movement, owners, notes, tasks/reminders and new lead capture.
- Local demo CRUD persistence in `localStorage`.
- Dashboard metrics sourced from the active API or demo data.

## Offline/demo behavior

The API adapter now has an 8-second network timeout, recovers from invalid local storage, and publishes the active `Demo`/`Live` mode to the workspace shell. HTTP authorization/validation errors still surface to the user; only backend-unreachable failures fall back to demo data.

Demo accounts:

| Role | Email | Password |
| --- | --- | --- |
| Admin | `admin@furnivo.demo` | `admin123` |
| Sales | `sales@furnivo.demo` | `sales123` |
| Designer | `designer@furnivo.demo` | `design123` |
| Client | `client@furnivo.demo` | `client123` |

## Missing or partial features

These are not implemented as production features yet:

- Automated frontend/backend unit and integration tests.
- Refresh tokens, server-side session revocation and rate limiting.
- Audit log for sensitive changes such as price, quote status and permissions.
- Email/WhatsApp notifications and scheduled reminders.
- CSV/Excel exports.
- Quote version history, approval workflow and client quote approval screen.
- Server-side pagination/filtering for larger catalogs and CRM data.
- Object-level authorization for client-owned records; current access is role-level.
- Live analytics beyond the current dashboard counts and totals.
- Production deployment configuration, secret rotation and observability.

## Verification

- `python -m compileall -q backend` passes.
- `npm run build` passes after installing frontend dependencies.
- Flask API smoke test passes in the project virtual environment: health, admin login, products, quotes and leads returned successfully.
- The smoke test uses development defaults; replace `SECRET_KEY` and `JWT_SECRET_KEY` with long production secrets before deployment.
