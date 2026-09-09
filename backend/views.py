from backend.serializers import (
    OrderItemSerializer,
    ProductInfoSerializer,
    UserSerializer,
    ContactSerializer,
    OrderSerializer,
)
from django.contrib.auth import authenticate
from django.db import transaction
from django_filters.rest_framework import DjangoFilterBackend
from django.http import JsonResponse
from rest_framework.authtoken.models import Token
from rest_framework.filters import SearchFilter
from rest_framework.generics import CreateAPIView, ListAPIView
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
import yaml

from backend.models import (
    Category,
    Contact,
    Order,
    OrderItem,
    Parameter,
    Product,
    ProductInfo,
    ProductParameter,
    Shop,
    User,
)
from backend.serializers import (
    OrderItemSerializer,
    ProductInfoSerializer,
    UserSerializer,
)


class PartnerUpdateView(APIView):
    def post(self, request):
        try:
            with transaction.atomic():
                with open("data/shop1.yaml", "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f)
                    shop, _ = Shop.objects.update_or_create(name=data["shop"])

                    for category_data in data["categories"]:
                        category, _ = Category.objects.update_or_create(
                            id=category_data["id"],
                            defaults={"name": category_data["name"]},
                        )
                        category.shops.add(shop)

                    for item in data["goods"]:
                        product, _ = Product.objects.update_or_create(
                            name=item["model"], category_id=item["category"]
                        )
                        product_info, _ = ProductInfo.objects.update_or_create(
                            product=product,
                            shop=shop,
                            name=item["name"],
                            defaults={
                                "quantity": item["quantity"],
                                "price": item["price"],
                                "price_rrc": item["price_rrc"],
                            },
                        )

                        for name, value in item["parameters"].items():
                            parameter_obj, _ = Parameter.objects.get_or_create(
                                name=name
                            )
                            ProductParameter.objects.update_or_create(
                                product_info=product_info,
                                parameter=parameter_obj,
                                defaults={"value": str(value)},
                            )

            return JsonResponse({"Status": True})

        except Exception as e:
            return JsonResponse({"Status": False, "Errors": str(e)}, status=400)


class RegisterAccountView(CreateAPIView):
    serializer_class = UserSerializer
    permission_classes = (AllowAny,)


class LoginAccountView(APIView):
    permission_classes = (AllowAny,)

    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")

        if not email or not password:
            return JsonResponse(
                {"Status": False, "Errors": "Нужно заполнить все поля"}, status=400
            )

        user = authenticate(request, email=email, password=password)
        if user is not None:
            token, _ = Token.objects.get_or_create(user=user)
            return JsonResponse({"Status": True, "Token": token.key})
        return JsonResponse(
            {"Status": False, "Errors": "Неверный логин или пароль"}, status=403
        )


class ProductInfoView(ListAPIView):
    serializer_class = ProductInfoSerializer
    permission_classes = (AllowAny,)
    queryset = ProductInfo.objects.all()
    filter_backends = [DjangoFilterBackend, SearchFilter]
    search_fields = ["name", "product__name", "shop__name"]
    filterset_fields = ["shop_id", "product__category_id"]


class CartView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        cart = Order.objects.filter(user=request.user, status="new").first()

        if not cart:
            return JsonResponse({"Cart": []})
        items = cart.ordered_items.all()
        serializer = OrderItemSerializer(items, many=True)
        return JsonResponse({"Cart": serializer.data})

    def post(self, request):
        items = request.data.get("items")

        if not items or not isinstance(items, list):
            return JsonResponse(
                {
                    "Status": False,
                    "Errors": 'Необходим список товаров в формате [{"product_id": 1, "shop_id": 1, "quantity": 1}]',
                },
                status=400,
            )

        cart, _ = Order.objects.get_or_create(user=request.user, status="new")

        added_count = 0
        for item in items:
            product_id = item.get("product_id")
            shop_id = item.get("shop_id")
            quantity = item.get("quantity")

            if product_id and shop_id and quantity:
                OrderItem.objects.update_or_create(
                    order=cart,
                    product_id=product_id,
                    defaults={"shop_id": shop_id, "quantity": quantity},
                )
                added_count += 1

        return JsonResponse({"Status": True, "Added_items_count": added_count})

    def delete(self, request):
        items = request.data.get("items")
        if not items:
            return JsonResponse(
                {"Status": False, "Errors": "Не переданы ID товаров для удаления"},
                status=400,
            )
        if isinstance(items, str):
            items = items.split(",")
        cart = Order.objects.filter(user=request.user, status="new").first()

        if not cart:
            return JsonResponse(
                {"Status": False, "Errors": "Корзина не найдена или пуста"}, status=404
            )
        deleted_count = 0
        for item_id in items:
            deleted, _ = OrderItem.objects.filter(
                order=cart, product_id=item_id
            ).delete()
            if deleted:
                deleted_count += 1

        return JsonResponse({"Status": True, "Deleted_items_count": deleted_count})


class ContactView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        contacts = Contact.objects.filter(user=request.user)
        serializer = ContactSerializer(contacts, many=True)

        return JsonResponse({"Contacts": serializer.data})

    def post(self, request):
        serializer = ContactSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save(user=request.user)

            return JsonResponse(
                {
                    "Status": True,
                    "Contact": serializer.data,
                },
                status=201,
            )

        return JsonResponse(
            {
                "Status": False,
                "Errors": serializer.errors,
            },
            status=400,
        )

    def delete(self, request):
        contact_id = request.data.get("id")

        if not contact_id:
            return JsonResponse(
                {
                    "Status": False,
                    "Errors": "Не указан ID контакта",
                },
                status=400,
            )

        deleted, _ = Contact.objects.filter(
            id=contact_id,
            user=request.user,
        ).delete()

        if not deleted:
            return JsonResponse(
                {
                    "Status": False,
                    "Errors": "Контакт не найден",
                },
                status=404,
            )

        return JsonResponse(
            {
                "Status": True,
            }
        )


class ConfirmOrderView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        cart_id = request.data.get("cart_id")
        contact_id = request.data.get("contact_id")

        if not cart_id or not contact_id:
            return JsonResponse(
                {
                    "Status": False,
                    "Errors": "Необходимо указать ID корзины и ID контакта",
                },
                status=400,
            )

        try:
            cart = Order.objects.get(
                id=cart_id,
                user=request.user,
                status=Order.Status.NEW,
            )
        except Order.DoesNotExist:
            return JsonResponse(
                {
                    "Status": False,
                    "Errors": "Корзина не найдена",
                },
                status=404,
            )

        try:
            contact = Contact.objects.get(
                id=contact_id,
                user=request.user,
            )
        except Contact.DoesNotExist:
            return JsonResponse(
                {
                    "Status": False,
                    "Errors": "Контакт не найден",
                },
                status=404,
            )

        if not cart.ordered_items.exists():
            return JsonResponse(
                {
                    "Status": False,
                    "Errors": "Нельзя подтвердить пустую корзину",
                },
                status=400,
            )

        cart.contact = contact
        cart.status = Order.Status.CONFIRMED
        cart.save(update_fields=["contact", "status"])

        return JsonResponse(
            {
                "Status": True,
                "Order": OrderSerializer(cart).data,
            }
        )


class OrderListView(ListAPIView):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user).exclude(
            status=Order.Status.NEW
        )
