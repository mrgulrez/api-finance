"""
Root URL configuration for Finance Backend.

API v1 routes:
  /api/v1/auth/       → authentication (register, login, logout, token refresh)
  /api/v1/users/      → user management (admin)
  /api/v1/finance/    → financial records CRUD
  /api/v1/dashboard/  → analytics & summaries

Docs:
  /api/schema/  → OpenAPI schema (JSON)
  /api/docs/    → Swagger UI
  /api/redoc/   → ReDoc
"""

from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

urlpatterns = [
    # Django admin
    path("admin/", admin.site.urls),

    # API v1
    path(
        "api/v1/",
        include(
            [
                path("auth/", include("apps.users.auth_urls", namespace="auth")),
                path("users/", include("apps.users.urls", namespace="users")),
                path("finance/", include("apps.finance.urls", namespace="finance")),
                path("dashboard/", include("apps.dashboard.urls", namespace="dashboard")),
            ]
        ),
    ),

    # API Documentation
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
]
