# Finance Backend

A complete Django 5 REST API backend for a Finance Dashboard system featuring role-based access control (RBAC), JWT authentication, financial records editing with soft deletion, and analytical summary endpoints using efficient ORM aggregaation.

## Architecture & Tech Stack

- **Framework**: Django 5 + Django REST Framework (DRF)
- **Database**: SQLite by default (switch to Postgres via `DATABASE_URL` environment variable)
- **Authentication**: JWT token pairs via `djangorestframework-simplejwt`
- **Filtering**: `django-filter` and native DRF search/ordering
- **CORS**: `django-cors-headers` configured for Next.js / React frontend
- **API Docs**: Swagger and ReDoc generated automatically using `drf-spectacular`
- **Logging**: Custom request logging middleware tracking duration in milliseconds

## Project Structure

```text
finance_backend/
├── config/              # Base settings, urls, wsgi/asgi entry points
├── apps/
│   ├── core/            # Middleware, custom exceptions, pagination, RBAC permissions, mixins
│   ├── users/           # Custom User model (email login), JWT token views, role management
│   ├── finance/         # Financial records CRUD, soft delete, custom QuerySet aggregation
│   └── dashboard/       # Read-only analytical APIs relying on finance aggregations
├── manage.py            # Standard Django command utility
├── requirements.txt     # Locked dependencies
├── .env.example         # Example settings configuration
└── db.sqlite3           # (Generated on migrate)
```

## Setup Instructions

1. **Clone and Setup Virtual Environment:**
   ```bash
   python -m venv venv
   # Windows
   .\venv\Scripts\activate
   # macOS/Linux
   source venv/bin/activate
   ```

2. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure Environment Variables:**
   ```bash
   cp .env.example .env
   # Use the default SQLite settings without changing anything, 
   # or configure your DATABASE_URL for Postgres.
   ```

4. **Initialize Database:**
   ```bash
   python manage.py makemigrations users finance dashboard
   python manage.py migrate
   ```

5. **Seed Database with Test Data:**
   Creates 3 users (VIEWER, ANALYST, ADMIN) and 30 random records.
   ```bash
   python manage.py seed_data
   ```

6. **Start the Development Server:**
   ```bash
   python manage.py runserver
   ```
   Server runs on `http://127.0.0.1:8000/`

## Environment Variables Explained

- `SECRET_KEY`: Django cryptographic signing setup key.
- `DEBUG`: Set to `True` for development, `False` for production.
- `ALLOWED_HOSTS`: Comma-separated domain names allowed to serve the app.
- `DATABASE_URL`: Connection string (e.g. `sqlite:///db.sqlite3` or `postgres://user:pass@host:5432/dbname`)
- `JWT_ACCESS_TOKEN_LIFETIME_MINUTES`: Access token expiration (default 60).
- `JWT_REFRESH_TOKEN_LIFETIME_DAYS`: Refresh token expiration (default 7).
- `CORS_ALLOWED_ORIGINS`: Comma-separated frontend URL origins for CORS.
- `DJANGO_LOG_LEVEL`: Application logging level (`INFO`, `DEBUG`, `WARNING`).

## Role-Based Access Control (RBAC)

- **VIEWER**: Can read dashboard summaries and view financial records.
- **ANALYST**: Inherits VIEWER abilities + can create and update financial records.
- **ADMIN**: Inherits ANALYST abilities + can soft delete records and fully manage other users (change roles, deactivate).

## API Endpoints

### 1. Authentication & Users
*Provides JWT tokens and handles user creation / role assignment.*

| Method | Endpoint | Required Role | Description |
|--------|----------|---------------|-------------|
| `POST` | `/api/v1/auth/register/` | Public | Register a new core user with VIEWER role. |
| `POST` | `/api/v1/auth/login/` | Public | Get access & refresh JWT tokens + user profile. |
| `POST` | `/api/v1/auth/logout/` | Any Auth | Blacklist your refresh token. |
| `POST` | `/api/v1/auth/token/refresh/` | Public | Refresh the short-lived access token. |
| `GET` | `/api/v1/users/` | ADMIN | List all non-deleted users. |
| `GET` | `/api/v1/users/{id}/` | Owner / ADMIN | Retrieve single user's detail. |
| `PATCH`| `/api/v1/users/{id}/` | Owner / ADMIN | Update user profile (`full_name`). |
| `PATCH`| `/api/v1/users/{id}/role/` | ADMIN | Update a user's role. |
| `PATCH`| `/api/v1/users/{id}/status/` | ADMIN | Activate / Deactivate a user account. |
| `DELETE`|`/api/v1/users/{id}/` | ADMIN | Soft delete a user account. |

### 2. Finance Operations
*Financial Record CRUD endpoints. Support filtering, pagination, and sorting.*

| Method | Endpoint | Required Role | Description |
|--------|----------|---------------|-------------|
| `GET` | `/api/v1/finance/records/` | VIEWER+ | List records. Only shows user's own records unless ADMIN. filters: `?type=`, `?category=`, `?date_from=`, `?date_to=`, `?search=`, `?ordering=` |
| `POST` | `/api/v1/finance/records/` | ANALYST+ | Create a new financial record. |
| `GET` | `/api/v1/finance/records/{id}/` | VIEWER+ | Retrieve specific record. |
| `PUT` | `/api/v1/finance/records/{id}/` | ANALYST+ | Fully update a record. |
| `PATCH`| `/api/v1/finance/records/{id}/` | ANALYST+ | Partially update a record. |
| `DELETE`|`/api/v1/finance/records/{id}/` | ADMIN | Soft delete a record. |

### 3. Dashboard Analytics
*All analytical endpoints utilize direct ORM queries (`Sum`, `Count`) optimizing memory and speed.*

| Method | Endpoint | Required Role | Description |
|--------|----------|---------------|-------------|
| `GET` | `/api/v1/dashboard/summary/` | VIEWER+ | Gross values: `total_income`, `total_expenses`, `net_balance`, `record_count`, etc. |
| `GET` | `/api/v1/dashboard/by-category/`| VIEWER+ | `count`, `total`, and `percentage_of_total` per category, separated by Income and Expense. |
| `GET` | `/api/v1/dashboard/trends/` | VIEWER+ | Monthly or weekly accumulation (append `?period=weekly` or `?period=monthly`). |
| `GET` | `/api/v1/dashboard/recent/` | VIEWER+ | Return latest N records (default 10 via `?limit=10`). |

## API Documentation
Once the local server is running, explore detailed endpoint schemas and easily test requests via Swagger:
- **Swagger UI**: `http://127.0.0.1:8000/api/docs/`
- **ReDoc**: `http://127.0.0.1:8000/api/redoc/`
- **OpenAPI JSON**: `http://127.0.0.1:8000/api/schema/`

## Assumptions & Design Choices

1. Users use email login exclusively. Standard username field has been removed to simplify user management.
2. User management operations are restricted to `ADMIN` users via Role-Based Access Control (RBAC).
3. The Finance app uses `select_related('user')` aggressively and performs aggregation strictly at the DB layer to prevent N+1 and out-of-memory queries.
4. "Soft DELETE" ensures we retain audit parity. Items flagged `is_deleted` are stripped from the default active queryset but retained for admin tracking.
5. All JSON responses adhere to a consistent standard envelope providing `success`, `data`, and robust DRF constraint validation error payloads.
