from django.urls import path
from backend.views import PartnerUpdateView

urlpatterns = [
    path("partner/update", PartnerUpdateView.as_view(), name="partner-update"),
]
