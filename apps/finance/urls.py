"""URL patterns for financial records — /api/v1/finance/"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import FinancialRecordViewSet

app_name = "finance"

router = DefaultRouter()
router.register("records", FinancialRecordViewSet, basename="record")

urlpatterns = [
    path("", include(router.urls)),
]
