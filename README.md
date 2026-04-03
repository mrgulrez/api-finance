# Finance Dashboard — Backend + Frontend

A production-quality finance dashboard system featuring JWT authentication, role-based access control (RBAC), full CRUD for financial records, ORM-powered aggregation analytics, a polished React frontend, and a 53-test pytest suite that verifies all core behaviors.

---

## Architecture Overview

```
┌────────────────────────────────────────────────────────────┐
│                    React Frontend (Vite)                    │
│  Login · Dashboard · Ledger · Users · Email Auth Flows     │
└────────────────────────────┬───────────────────────────────┘
                             │ HTTP / JWT Bearer Token
┌────────────────────────────▼───────────────────────────────┐
│               Django REST Framework (API v1)                │
│                                                            │
│  ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌────────┐  │
│  │   auth/   │  │  users/   │  │ finance/  │  │dashboard│ │
│  │ register  │  │ list/role │  │ records   │  │summary  │ │
│  │ login     │  │ status    │  │ CRUD      │  │trends   │ │
│  │ logout    │  │ soft-del  │  │ filter    │  │category │ │
│  │ verify    │  │           │  │ ordering  │  │recent   │ │
│  │ pwd-reset │  │           │  │ paginate  │  │         │ │
│  └───────────┘  └───────────┘  └───────────┘  └────────┘  │
│                                                            │
│  ┌────────────────── core/ ──────────────────────────────┐ │
│  │ RBAC Permissions · Pagination · Exception Handler     │ │
│  │ Response Mixin · Request Logging Middleware           │ │
│  └──────────────────────────────────────────────────────┘ │
└────────────────────────────┬───────────────────────────────┘
                             │ ORM / SQL
                  ┌──────────▼──────────┐
                  │  SQLite (dev) /      │
                  │  PostgreSQL (prod)   │
                  └─────────────────────┘
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend Framework | Django 5.0 + Django REST Framework 3.15 |
| Authentication | `djangorestframework-simplejwt` (JWT + token blacklist) |
| Database | SQLite (dev) / PostgreSQL (prod via `DATABASE_URL`) |
| Filtering | `django-filter` + DRF's built-in SearchFilter, OrderingFilter |
| API Documentation | `drf-spectacular` (Swagger + ReDoc auto-generated) |
| Email | Gmail SMTP with app password |
| Static Files | WhiteNoise (production) |
| Testing | pytest + pytest-django (53 tests, 0 failures) |
| Frontend | React 18 + Vite + TypeScript |
| Charts | Recharts (AreaChart, PieChart) |
| Styling | Vanilla CSS with CSS Variables (glassmorphism theme) |

---

## Project Structure

```
finance_backend/
├── config/
│   ├── settings.py       # All config, driven by env vars
│   └── urls.py           # Root URL routing
├── apps/
│   ├── core/             # Shared infrastructure
│   │   ├── exceptions.py   # Custom JSON error handler (standardized envelope)
│   │   ├── middleware.py   # Request logging with response time tracking
│   │   ├── mixins.py       # ApiResponseMixin – success/error response helpers
│   │   ├── pagination.py   # StandardPageNumberPagination with metadata
│   │   └── permissions.py  # IsAdminRole, IsAnalystOrAdmin, IsViewerOrAbove
│   ├── users/            # User model, auth, and user management
│   │   ├── models.py      # Custom User (email login, VIEWER/ANALYST/ADMIN roles)
│   │   ├── managers.py    # UserManager (email-based creation)
│   │   ├── serializers.py # Registration, JWT custom response, role/status update
│   │   ├── views.py       # RegisterView, LoginView, LogoutView, VerifyEmail,
│   │   │                  # ForgotPassword, ResetPassword, UserViewSet
│   │   ├── auth_urls.py   # /api/v1/auth/* routes
│   │   ├── urls.py        # /api/v1/users/* routes
│   │   └── utils.py       # send_verification_email, send_password_reset_email
│   ├── finance/          # Financial records domain
│   │   ├── models.py      # FinancialRecord (amount, type, category, date, soft-delete)
│   │   ├── managers.py    # Fat QuerySet: active(), summary(), by_category(), trends()
│   │   ├── serializers.py # Full + lightweight list serializers with validation
│   │   ├── filters.py     # FinancialRecordFilter (date range, type, category)
│   │   └── views.py       # FinancialRecordViewSet with action-level RBAC
│   └── dashboard/        # Read-only analytics layer
│       ├── views.py       # SummaryView, ByCategoryView, TrendsView, RecentView
│       └── serializers.py # Dashboard response shape serializers
├── tests/                # pytest test suite
│   ├── conftest.py       # Shared fixtures (users, api clients, sample records)
│   ├── test_auth.py      # Registration, login, logout tests (10 tests)
│   ├── test_rbac.py      # RBAC enforcement + validation + filtering (19 tests)
│   ├── test_dashboard.py # Analytics correctness + structure (11 tests)
│   └── test_users.py     # User management, soft delete, profile (13 tests)
├── pytest.ini            # Pytest configuration
├── requirements.txt      # All dependencies
├── .env.example          # Environment variable template
└── Procfile              # Gunicorn production startup command
```

---

## Quick Start

### 1. Clone and create virtual environment

```bash
git clone <repo-url>
cd finance_backend

python -m venv venv
# Windows
.\venv\Scripts\activate
# macOS/Linux
source venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment

```bash
cp .env.example .env
# Edit .env with your settings (SECRET_KEY, email credentials, etc.)
```

### 4. Initialize database

```bash
python manage.py migrate
```

### 5. Seed sample data

Creates **3 role-differentiated users** (VIEWER, ANALYST, ADMIN) and **30 randomized financial records**.

```bash
python manage.py seed_data
```

**Generated credentials:**

| Email | Password | Role |
|---|---|---|
| `viewer@finance.dev` | `viewer123!` | VIEWER |
| `analyst@finance.dev` | `analyst123!` | ANALYST |
| `admin@finance.dev` | `admin123!` | ADMIN |

### 6. Run development server

```bash
python manage.py runserver
```

Server: `http://127.0.0.1:8000/`

---

## Running Tests

```bash
python -m pytest tests/ -v
```

**53 tests across 4 suites — all pass:**

```
tests/test_auth.py      .......... (10 tests)
tests/test_rbac.py      ................... (19 tests)
tests/test_dashboard.py ........... (11 tests)
tests/test_users.py     ............. (13 tests)

53 passed in 83s
```

---

## API Reference

All responses follow a consistent JSON envelope:

**Success:**
```json
{
  "success": true,
  "data": { ... },
  "message": "Optional human-readable message"
}
```

**Error:**
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Human readable description",
    "details": { "field": ["error message"] }
  }
}
```

**Pagination:**
```json
{
  "success": true,
  "data": [ ... ],
  "pagination": {
    "total_count": 100,
    "total_pages": 5,
    "current_page": 2,
    "page_size": 20,
    "next": "http://localhost:8000/api/v1/finance/records/?page=3",
    "previous": "http://localhost:8000/api/v1/finance/records/?page=1"
  }
}
```

---

### Authentication Endpoints

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `POST` | `/api/v1/auth/register/` | Public | Register. Account starts inactive until email is verified. |
| `POST` | `/api/v1/auth/login/` | Public | Returns JWT access + refresh tokens + user profile. |
| `POST` | `/api/v1/auth/logout/` | Any | Blacklists the refresh token (session invalidation). |
| `POST` | `/api/v1/auth/token/refresh/` | Public | Exchange refresh token for new access token. |
| `POST` | `/api/v1/auth/verify-email/` | Public | Verify email with `uidb64` + `token` from email link. |
| `POST` | `/api/v1/auth/forgot-password/` | Public | Send password reset email. |
| `POST` | `/api/v1/auth/reset-password/` | Public | Set new password with `uidb64` + `token`. |

### User Management Endpoints

| Method | Endpoint | Required Role | Description |
|---|---|---|---|
| `GET` | `/api/v1/users/` | ADMIN | List all active users with pagination. |
| `GET` | `/api/v1/users/{id}/` | Owner / ADMIN | Retrieve a user's profile. |
| `PATCH` | `/api/v1/users/{id}/` | Owner / ADMIN | Update `full_name`. |
| `PATCH` | `/api/v1/users/{id}/role/` | ADMIN | Change user role. |
| `PATCH` | `/api/v1/users/{id}/status/` | ADMIN | Activate / deactivate user. |
| `DELETE` | `/api/v1/users/{id}/` | ADMIN | Soft-delete user (data preserved). |

### Financial Records Endpoints

| Method | Endpoint | Required Role | Description |
|---|---|---|---|
| `GET` | `/api/v1/finance/records/` | VIEWER+ | List records (own only, unless ADMIN). |
| `POST` | `/api/v1/finance/records/` | ANALYST+ | Create a new financial record. |
| `GET` | `/api/v1/finance/records/{id}/` | VIEWER+ | Retrieve a single record. |
| `PUT/PATCH` | `/api/v1/finance/records/{id}/` | ANALYST+ | Full or partial update. |
| `DELETE` | `/api/v1/finance/records/{id}/` | ADMIN | Soft-delete (is_deleted=True). |

**Query Parameters:**

| Param | Example | Description |
|---|---|---|
| `?search=` | `?search=rent` | Full-text search across `category` and `description` |
| `?type=` | `?type=INCOME` or `?type=EXPENSE` | Filter by transaction type |
| `?category=` | `?category=salary` | Filter by exact category name |
| `?date_from=` | `?date_from=2024-01-01` | Filter records on or after date |
| `?date_to=` | `?date_to=2024-12-31` | Filter records on or before date |
| `?ordering=` | `?ordering=-amount` | Sort results (prefix `-` for descending) |
| `?page=` | `?page=2` | Navigate pages |
| `?page_size=` | `?page_size=50` | Records per page (max 100) |

### Dashboard Analytics Endpoints

| Method | Endpoint | Required Role | Description |
|---|---|---|---|
| `GET` | `/api/v1/dashboard/summary/` | VIEWER+ | Aggregate totals: income, expenses, net, counts. |
| `GET` | `/api/v1/dashboard/by-category/` | VIEWER+ | Per-category breakdown with percentage of total. |
| `GET` | `/api/v1/dashboard/trends/?period=monthly` | VIEWER+ | Monthly income/expenses/net for last 12 months. |
| `GET` | `/api/v1/dashboard/trends/?period=weekly` | VIEWER+ | Weekly income/expenses/net for last 8 weeks. |
| `GET` | `/api/v1/dashboard/recent/?limit=10` | VIEWER+ | Last N financial records (default 10, max 50). |

> Dashboard endpoints are always scoped to the authenticated user's data, unless the user is ADMIN (who sees all records).

---

## Interactive API Documentation

Once the server is running:

- **Swagger UI**: `http://127.0.0.1:8000/api/docs/`
- **ReDoc**: `http://127.0.0.1:8000/api/redoc/`
- **OpenAPI JSON Schema**: `http://127.0.0.1:8000/api/schema/`

---

## Role-Based Access Control (RBAC)

```
VIEWER < ANALYST < ADMIN
```

| Action | VIEWER | ANALYST | ADMIN |
|---|---|---|---|
| View dashboard analytics | ✅ | ✅ | ✅ |
| List financial records (own) | ✅ | ✅ | ✅ |
| List ALL records | ❌ | ❌ | ✅ |
| Create financial record | ❌ | ✅ | ✅ |
| Update financial record | ❌ | ✅ (own) | ✅ |
| Delete financial record | ❌ | ❌ | ✅ |
| View user list | ❌ | ❌ | ✅ |
| Change user roles | ❌ | ❌ | ✅ |
| Deactivate/delete users | ❌ | ❌ | ✅ |

RBAC is implemented at the action level inside each ViewSet's `get_permissions()` — not at URL or middleware level — ensuring granular, testable enforcement.

---

## Design Decisions & Assumptions

1. **Email-based authentication**: The username field is removed. All authentication uses email + password. This is cleaner for B2B finance applications where emails serve as unique operator identifiers.

2. **Fat QuerySet (Manager) Pattern**: All business logic and ORM aggregation lives in `FinancialRecordQuerySet` (see `apps/finance/managers.py`). Views are thin — they call manager methods, not raw ORM directly. This keeps Views testable and Domain logic contained.

3. **Soft Delete everywhere**: Both `User` and `FinancialRecord` implement soft delete via `is_deleted=True`. Records are never permanently removed from the database, which is essential for audit compliance in financial systems. The default queryset automatically filters `is_deleted=False`.

4. **Standardized JSON API envelope**: Every response (success or error) follows `{ success, data/error, message/pagination }`. This means the frontend can write a single `api.get()` wrapper without handling inconsistent shapes.

5. **ORM-only aggregations**: Dashboard analytics (`SummaryView`, `ByCategoryView`, `TrendsView`) use Django ORM `Sum()`, `Count()`, `TruncMonth()`, `TruncWeek()` and conditional aggregates (`filter=Q(...)`) — never Python loops over querysets. This ensures O(1) memory usage regardless of dataset size.

6. **Action-level RBAC**: Permission classes are applied at the action/method level inside `get_permissions()`, not at the URL level. This allows fine-grained control: ANALYST can `POST` records but cannot `DELETE` them on the same endpoint.

7. **Email verification is enforced**: New registrations are created with `is_active=False`. Django SimpleJWT will return a 401 for inactive accounts, until the email link is clicked. This prevents unauthorized use of the system.

8. **select_related() everywhere**: All querysets that serialize user data call `.select_related("user")` to prevent N+1 database query patterns.

9. **Consistent pagination metadata**: All list endpoints return pagination metadata (`total_count`, `total_pages`, `current_page`, `next`, `previous`) — enabling the frontend to render page controls without additional API calls.

---

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `SECRET_KEY` | *(required)* | Django cryptographic signing key |
| `DEBUG` | `False` | Enable debug mode |
| `ALLOWED_HOSTS` | `localhost,127.0.0.1` | Allowed origin hosts |
| `DATABASE_URL` | `sqlite:///db.sqlite3` | Database connection string |
| `JWT_ACCESS_TOKEN_LIFETIME_MINUTES` | `60` | Access token TTL in minutes |
| `JWT_REFRESH_TOKEN_LIFETIME_DAYS` | `7` | Refresh token TTL in days |
| `CORS_ALLOWED_ORIGINS` | `http://localhost:5173` | Frontend origin(s) for CORS |
| `DJANGO_LOG_LEVEL` | `INFO` | Logging verbosity |
| `EMAIL_HOST_USER` | `""` | Gmail address for SMTP |
| `EMAIL_HOST_PASSWORD` | `""` | Gmail App Password |
| `DEFAULT_FROM_EMAIL` | `noreply@finance.local` | "From" address on sent emails |
| `FRONTEND_URL` | `http://localhost:5173` | Base URL for email links |
