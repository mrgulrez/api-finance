"""URL patterns for dashboard analytics — /api/v1/dashboard/"""

from django.urls import path

from .views import ByCategoryView, RecentView, SummaryView, TrendsView

app_name = "dashboard"

urlpatterns = [
    path("summary/", SummaryView.as_view(), name="summary"),
    path("by-category/", ByCategoryView.as_view(), name="by-category"),
    path("trends/", TrendsView.as_view(), name="trends"),
    path("recent/", RecentView.as_view(), name="recent"),
]
