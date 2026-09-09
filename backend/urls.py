from django.urls import path
from backend.views import CartView, LoginAccountView, PartnerUpdateView, ProductInfoView, RegisterAccountView

urlpatterns = [
    path("partner/update", PartnerUpdateView.as_view(), name="partner-update"),
    path("user/register", RegisterAccountView.as_view(), name="user-register"),
    path("user/login", LoginAccountView.as_view(), name="user-login"),
    path('products/', ProductInfoView.as_view(), name='product'),
    path('cart/', CartView.as_view(), name='cart')
]
