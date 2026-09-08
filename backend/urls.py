from django.urls import path
from backend.views import PartnerUpdateView, RegisterAccountView

urlpatterns = [
    path("partner/update", PartnerUpdateView.as_view(), name="partner-update"),
    path("user/register", RegisterAccountView, name="user-register"),
]
