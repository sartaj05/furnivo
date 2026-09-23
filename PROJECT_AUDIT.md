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
- Client quotation portal with assigned quote access, PDF download, approve/reject/request-changes actions and comments.
- Quote revision history with versioned status and client-response events.
- Customer records with project/billing information and GSTIN.
- Lead CRM with stage movement, owners, notes, tasks/reminders and new lead capture.
- Order conversion from quotations with production, delivery, installation and project updates.
- Inventory quantities, reserved stock, reorder levels, supplier/location data and low-stock indicators.
- In-app notifications with automation triggers for quotes, leads, tasks and project updates.
- Configurable email SMTP and WhatsApp webhook delivery with delivery status tracking.
- Invoices generated from orders with payment links, partial payments, balances and receipts.
- Supplier records and purchase orders with expected dates, statuses and product costs.
- Business reports with live API/demo metrics and CSV/Excel-compatible plus PDF exports.
- Admin audit log with resource filtering and object-level client record filtering.
- Local demo CRUD persistence in `localStorage`.
- Dashboard metrics sourced from the active API or demo data.
- Production job cards with BOM materials, per-item wastage and production status stages.
- Payment reconciliation records with failed/disputed states, partial/full refunds and invoice balance updates.
- Digital contracts with terms, client e-signatures, locked versions and downloadable PDFs.
- Customer project portal with progress, production, schedules, documents and support tickets.
- Admin Operations screen with database health, request IDs, rate limiting, backup creation/history and deployment checklist.
- Backend API tests and frontend component test coverage wired into GitHub Actions CI.
- Refresh-token rotation, cookie-based access token support, session revocation and MFA challenge flow.
- GST tax modes, HSN/SAC summaries, e-invoice IRN records and e-way bill records.
- Payment idempotency, dispute webhook handling, provider-ready refunds and downloadable receipts.
- Paginated searchable catalog/customer/lead APIs, CSV imports, archived-record filters and background jobs.
- Quote-to-payment automation: client quote approval creates a contract, contract signing creates a deposit order/invoice, and a paid deposit confirms the order.
- Furniture visual configurator MVP: material, fabric, color, finish, dimensions, quantity, live pricing, saved configurations and direct quote handoff.

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

- Broader automated frontend/backend unit and end-to-end coverage beyond the current API workflow suite and configurator coverage.
- Audit log for sensitive changes such as price, quote status and permissions.
- Email/WhatsApp notifications and scheduled reminders.
- More advanced accounting exports beyond the current reports and CSV/Excel exports.
- Provider-specific production templates, retry queues and delivery webhooks for email/WhatsApp notifications.
- Provider-specific refund calls require `PAYMENT_LIVE_REFUNDS=true` plus live Stripe/Razorpay credentials; demo mode remains the safe default.
- External distributed job queue and worker scaling beyond the in-process background job runner.
- Object-level authorization for client-owned records; current access is role-level.
- Live analytics beyond the current dashboard counts and totals.
- Secret rotation, external backup storage, centralized log shipping and full production deployment automation.

## Verification

- `python -m compileall -q backend` passes.
- `npm run build` passes after installing frontend dependencies.
- Flask API smoke test passes in the project virtual environment: health, admin login, products, quotes and leads returned successfully.
- Additional smoke checks pass for client quote response, quote history, orders, inventory and notifications.
- Additional smoke checks pass for invoices/payments, procurement, reports, audit logs and notification delivery configuration handling.
- The smoke test uses development defaults; replace `SECRET_KEY` and `JWT_SECRET_KEY` with long production secrets before deployment.
