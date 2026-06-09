# Advance Company Management System

Frontend build reference for the Advance Company full-stack system.

This project is a member management platform with authentication, financial deposits, beneficiary management, document storage, applications, reporting, notifications, and admin analytics.

## Stack

- Backend: Django, Django REST Framework, PostgreSQL, JWT auth, Supabase file storage, optional Redis cache.
- Frontend: Angular 18, Angular Router, HttpClient, RxJS, SCSS/Tailwind styling.
- Deployment targets present in repo: Render/Railway-style backend config, Netlify frontend config, Dockerfiles, Docker Compose, Nginx.

## Repository Layout

```text
backend/
  advance_company/        Django project settings, URLs, Celery, ASGI/WSGI
  apps/
    accounts/             Auth, users, 2FA, biometric device metadata
    financial/            Accounts, deposits, interest, M-Pesa callback
    beneficiary/          Beneficiary CRUD and verification workflow
    documents/            Secure document upload and verification
    applications/         Member applications and admin review
    reports/              Report generation and activity logs
    notifications/        User notifications
    analytics/            Admin analytics
    health/               Health and metrics endpoints
frontend/
  src/app/core/           Guards, interceptors, services, models
  src/app/features/       Auth, dashboard, financial, beneficiaries, documents, etc.
  src/app/shared/         Header, sidebar, stat cards, loading, notification dropdown
```

## Base URLs

Backend API routes are mounted under:

```text
/api/
```

Current production frontend environment:

```ts
apiUrl: 'https://advance-company-backend-v1-0-3.onrender.com/api'
```

For local development, the frontend should normally use:

```ts
apiUrl: 'http://localhost:8000/api'
```

Create `frontend/src/app/environments/environment.ts` if it is missing:

```ts
export const environment = {
  production: false,
  apiUrl: 'http://localhost:8000/api',
  apiTimeout: 30000
};
```

## Authentication Model

The backend uses JWT Bearer authentication through `djangorestframework-simplejwt`.

Store both tokens after login/register:

```json
{
  "tokens": {
    "access": "...",
    "refresh": "..."
  }
}
```

Authenticated requests must include:

```http
Authorization: Bearer <access_token>
```

Refresh endpoint:

```http
POST /api/token/refresh/
Body: { "refresh": "<refresh_token>" }
```

JWT settings:

- Access token lifetime: 30 minutes
- Refresh token lifetime: 7 days
- Refresh tokens rotate and old refresh tokens are blacklisted
- JWT user id claim is `user_id`
- User primary key is `uuid`

## Standard Response Shape

Many auth endpoints return this wrapper:

```json
{
  "success": true,
  "message": "User-friendly message",
  "toast_type": "success",
  "data": {}
}
```

Error responses may include:

```json
{
  "success": false,
  "message": "Validation failed",
  "toast_type": "error",
  "errors": {}
}
```

Important frontend note: not every endpoint uses this wrapper. Some DRF viewsets return raw serializer data or DRF paginated data directly. Frontend services should handle both:

- Wrapped: `response.data`
- Raw list/object: `response`
- Paginated: `{ count, next, previous, results }`

## User Roles

Supported roles:

- `user`: normal member
- `admin`: administrator

Admin-only frontend areas currently include:

- `/admin/analytics`
- `/admin/beneficiary-verification`
- Deposit approval/rejection
- Application approval/rejection
- Document/beneficiary verification

## Frontend Routes

Main Angular routes:

```text
/auth
/dashboard
/financial
/deposit-form
/beneficiary
/documents
/applications
/reports
/settings
/support
/notifications
/admin/analytics
/admin/beneficiary-verification
```

Most app routes use `authGuard`; admin routes also use `adminGuard`.

## API Endpoint Map

All endpoints below are relative to `/api`.

### Auth and Users

Public:

```http
POST /auth/register/
POST /auth/login/
POST /auth/verify-email/
POST /auth/resend-verification/
POST /auth/verify-2fa/
POST /auth/forgot-password/
POST /auth/reset-password-confirm/
POST /token/refresh/
```

Protected user router:

```http
GET    /auth/users/
GET    /auth/users/{uuid}/
PATCH  /auth/users/{uuid}/
DELETE /auth/users/{uuid}/
POST   /auth/users/change_password/
POST   /auth/users/enable_2fa/
POST   /auth/users/confirm_2fa/
POST   /auth/users/disable_2fa/
GET    /auth/users/regenerate_backup_codes/
POST   /auth/users/register_biometric/
GET    /auth/users/biometric_devices/
DELETE /auth/users/{uuid}/biometric-devices/{device_id}/
DELETE /auth/users/delete_account/
POST   /auth/users/upload_profile_photo/
DELETE /auth/users/delete_profile_photo/
```

User fields returned by `UserSerializer` include:

```text
uuid, email, phone_number, full_name, role, age, gender,
marital_status, number_of_kids, profession, salary_range,
spouse_name, spouse_age, spouse_profession, profile_photo,
identity_document, activity_status, created_at, updated_at,
biometric_enabled, fingerprint_enabled, face_id_enabled,
has_biometric, biometric_devices_count
```

Registration body:

```json
{
  "email": "member@example.com",
  "phone_number": "0712345678",
  "full_name": "Member Name",
  "password": "StrongPassword123!",
  "password_confirm": "StrongPassword123!",
  "role": "user"
}
```

Login body:

```json
{
  "email": "member@example.com",
  "password": "StrongPassword123!"
}
```

If 2FA is enabled, login returns `requires_2fa`, `temp_token`, and `email`; then call `/auth/verify-2fa/`.

### Financial

```http
GET  /financial/accounts/
GET  /financial/accounts/{uuid}/
GET  /financial/accounts/my_account/

GET  /financial/deposits/
POST /financial/deposits/
GET  /financial/deposits/{uuid}/
GET  /financial/deposits/can_deposit/
GET  /financial/deposits/monthly_summary/
GET  /financial/deposits/pending_approvals/       admin
POST /financial/deposits/{uuid}/approve_deposit/  admin
POST /financial/deposits/{uuid}/reject_deposit/   admin

GET  /financial/interest/
GET  /financial/interest/{uuid}/

POST /financial/mpesa/callback/
```

Deposit rules:

- Monthly deposit amount is fixed at KES `20000.00`.
- A member can only have one completed monthly deposit.
- Payment methods: `mpesa`, `bank`, `mansa_x`.
- Status values: `pending`, `processing`, `completed`, `failed`, `cancelled`.

Deposit creation body should include at least:

```json
{
  "payment_method": "mpesa",
  "mpesa_phone": "254712345678",
  "notes": "Optional note"
}
```

### Beneficiaries

```http
GET    /beneficiary/
POST   /beneficiary/
GET    /beneficiary/{uuid}/
PATCH  /beneficiary/{uuid}/
DELETE /beneficiary/{uuid}/
POST   /beneficiary/{uuid}/verify/       admin
POST   /beneficiary/{uuid}/reject/       admin
POST   /beneficiary/{uuid}/mark_deceased/
GET    /beneficiary/pending_verification/ admin
GET    /beneficiary/statistics/
```

Beneficiary fields:

```text
uuid, user, user_name, user_email, user_phone, name, relation,
age, gender, phone_number, profession, salary_range,
percentage_allocation, identity_document, birth_certificate,
death_certificate, death_certificate_number, additional_documents,
status, verification_status, created_at, updated_at
```

Choices:

- Relation: `spouse`, `child`, `parent`, `sibling`, `other`
- Gender: `M`, `F`, `O`
- Status: `active`, `deceased`, `removed`
- Verification: `verified`, `pending`, `rejected`

Upload bodies should use `FormData` because documents are file fields.

### Documents

```http
GET    /documents/
POST   /documents/
GET    /documents/{uuid}/
PATCH  /documents/{uuid}/
DELETE /documents/{uuid}/
GET    /documents/{uuid}/view_url/
POST   /documents/{uuid}/verify/       admin
POST   /documents/{uuid}/reject/       admin
```

Document fields:

```text
uuid, user, user_name, category, title, file, file_url,
status, rejection_reason, uploaded_at, updated_at
```

Categories:

- `identity`
- `beneficiary`
- `birth_certificate`
- `death_certificate`
- `additional`

Status values:

- `pending`
- `verified`
- `rejected`

Use `FormData` for create/update:

```text
category: identity
title: National ID
file: <File>
```

### Applications

```http
GET    /applications/
POST   /applications/
GET    /applications/{id}/
PATCH  /applications/{id}/
DELETE /applications/{id}/
GET    /applications/choices/
POST   /applications/{id}/approve/       admin
POST   /applications/{id}/reject/        admin
POST   /applications/{id}/review/        admin
```

Application fields:

```text
id, user, user_name, application_type, reason, supporting_document,
status, admin_comments, submitted_at, reviewed_at, approved_at,
reviewed_by, created_at, updated_at, activities
```

Application types:

```text
new_membership, membership_withdrawal, membership_transfer,
loan, loan_top_up, loan_restructure,
withdrawal, contribution_change,
beneficiary_update, personal_details_change, next_of_kin_update,
statement_request, other
```

Status values:

```text
pending, under_review, approved, rejected
```

Use `FormData` if `supporting_document` is included.

### Reports

```http
GET  /reports/
POST /reports/
GET  /reports/{uuid}/
POST /reports/generate_financial_report/
POST /reports/generate_compensatory_report/
POST /reports/generate_activity_report/
POST /reports/{uuid}/resend_report_email/
GET  /reports/dashboard_summary/
GET  /reports/summary/
GET  /reports/deposit_trends/
GET  /reports/activity-logs/
```

Reports support generated PDF/file workflows. File URLs may be returned as direct storage URLs.

### Notifications

```http
GET    /notifications/
GET    /notifications/{uuid}/
GET    /notifications/unread/
GET    /notifications/unread_count/
GET    /notifications/recent/
POST   /notifications/{uuid}/mark_as_read/
POST   /notifications/mark_all_as_read/
DELETE /notifications/clear_all/
DELETE /notifications/{uuid}/delete_notification/
```

Frontend should poll `unread_count` or call it after successful mutations.

### Admin Analytics

```http
GET /admin/analytics/members/
GET /admin/analytics/summary/
GET /admin/analytics/export/?format=excel
GET /admin/analytics/export/?format=pdf
```

Note: `frontend/src/app/core/services/admin-analytics.service.ts` currently references `/admin/analytics/trends/`, but the backend does not expose a `trends` action in `apps.analytics.views`. Use the trend data embedded in `members/`, add a backend `trends` action, or update the frontend service.

### Health

```http
GET /health/
GET /health/metrics/
```

## Frontend Service Pattern

The existing Angular `ApiService` expects endpoint strings without the `/api` prefix:

```ts
this.api.get('auth/users/');
this.api.post('auth/login/', payload);
this.api.upload('documents/', formData);
```

For file uploads:

- Use `FormData`
- Do not manually set `Content-Type`; Angular will add the multipart boundary
- Keep `Authorization: Bearer ...` through the auth interceptor

For UUID routes:

```ts
this.api.get(`beneficiary/${beneficiary.uuid}/`);
```

## Local Development

Backend:

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Frontend:

```bash
cd frontend
npm install
npm start
```

Useful backend commands:

```bash
python manage.py createsuperuser
python manage.py quick_seed
python manage.py check_system
```

Docker Compose is also available from the repo root:

```bash
docker compose up --build
```

## Backend Environment Variables

The backend reads configuration from `backend/.env`.

Required or commonly used values:

```env
SECRET_KEY=
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
CORS_ALLOWED_ORIGINS=http://localhost:4200
CSRF_TRUSTED_ORIGINS=http://localhost:4200
DATABASE_URL=postgres://USER:PASSWORD@HOST:PORT/DB_NAME
REDIS_URL=

SUPABASE_URL=
SUPABASE_KEY=
SUPABASE_BUCKET=

EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=
EMAIL_HOST_PASSWORD=
DEFAULT_FROM_EMAIL=
RESEND_API_KEY=

MPESA_ENVIRONMENT=sandbox
MPESA_CONSUMER_KEY=
MPESA_CONSUMER_SECRET=
MPESA_SHORTCODE=
MPESA_PASSKEY=
MPESA_CALLBACK_URL=

FRONTEND_URL=http://localhost:4200
```

## Important Integration Notes

- IDs are UUIDs. Do not assume numeric `id` except where the application model exposes `id` as a UUID.
- Some services still refer to `id` in method names, but the actual value should be a UUID.
- Auth responses are wrapped; many CRUD viewsets are raw DRF responses.
- Profile photos, identity documents, beneficiary documents, application documents, and general documents are multipart uploads.
- CORS must include the frontend origin exactly, including scheme and port.
- Passwords must be at least 12 characters and pass Django validators.
- Email verification is implemented, but login currently does not enforce `email_verified` because that check is commented in the backend.
- Rate throttles are configured for auth endpoints; handle `429` in the frontend.
- File URLs may be absolute or storage-provider URLs depending on serializer and storage backend.

## Suggested Frontend Build Checklist

1. Configure `environment.apiUrl`.
2. Implement login/register and store `access` plus `refresh`.
3. Add an HTTP interceptor for Bearer tokens and refresh handling.
4. Normalize backend responses in one helper so wrapped and raw DRF responses both work.
5. Build route guards from current user role.
6. Use `FormData` for all file-bearing create/update forms.
7. Use UUID strings for all detail, update, delete, and action URLs.
8. Surface `message` and `toast_type` where present.
9. Handle admin-only states separately from member states.
10. Test upload, token refresh, deposit creation, and admin approval flows end to end.
