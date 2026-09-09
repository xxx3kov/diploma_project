from django.urls import path

from backend.views import (
    CartView,
    ConfirmOrderView,
    ContactView,
    LoginAccountView,
    OrderListView,
    PartnerUpdateView,
    ProductInfoView,
    RegisterAccountView,
)

urlpatterns = [
    path(
        "partner/update",
        PartnerUpdateView.as_view(),
        name="partner-update",
    ),
    path(
        "user/register",
        RegisterAccountView.as_view(),
        name="user-register",
    ),
    path(
        "user/login",
        LoginAccountView.as_view(),
        name="user-login",
    ),
    path(
        "products/",
        ProductInfoView.as_view(),
        name="product",
    ),
    path(
        "cart/",
        CartView.as_view(),
        name="cart",
    ),
    path(
        "contacts/",
        ContactView.as_view(),
        name="contacts",
    ),
    path(
        "orders/confirm/",
        ConfirmOrderView.as_view(),
        name="order-confirm",
    ),
    path(
        "orders/",
        OrderListView.as_view(),
        name="orders",
    ),
]
