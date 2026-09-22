import yaml
from django.contrib.auth import authenticate
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.db import transaction
from django_filters.rest_framework import DjangoFilterBackend
from django.utils.http import (
    urlsafe_base64_decode,
    urlsafe_base64_encode,
)
from django.utils.encoding import force_bytes
from rest_framework.authtoken.models import Token
from rest_framework.filters import SearchFilter
from rest_framework.generics import CreateAPIView, ListAPIView, RetrieveAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView


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
from backend.permissions import IsSupplier
from backend.serializers import (
    ContactSerializer,
    OrderDetailSerializer,
    OrderItemSerializer,
    OrderSerializer,
    ProductDetailSerializer,
    ProductInfoSerializer,
    SupplierOrderSerializer,
    UserSerializer,
)


class PartnerUpdateView(APIView):
    permission_classes = [IsSupplier]

    def post(self, request):
        file = request.FILES.get("file")

        if not file:
            return Response(
                {"Status": False, "Errors": "Файл не загружен"},
                status=400,
            )

        try:
            with transaction.atomic():
                data = yaml.safe_load(file.read().decode("utf-8"))
                shop, _ = Shop.objects.update_or_create(
                    name=data["shop"],
                    defaults={
                        "supplier": request.user,
                    },
                )

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
                        parameter_obj, _ = Parameter.objects.get_or_create(name=name)
                        ProductParameter.objects.update_or_create(
                            product_info=product_info,
                            parameter=parameter_obj,
                            defaults={"value": str(value)},
                        )

            return Response({"Status": True})

        except Exception as e:
            return Response({"Status": False, "Errors": str(e)}, status=400)


class RegisterAccountView(CreateAPIView):
    serializer_class = UserSerializer
    permission_classes = (AllowAny,)

    def perform_create(self, serializer):
        user = serializer.save()

        send_mail(
            subject="Подтверждение регистрации",
            message=(
                f"Здравствуйте, {user.first_name}!\n\n"
                "Ваша регистрация успешно завершена."
            ),
            from_email=None,
            recipient_list=[user.email],
        )


class LoginAccountView(APIView):
    permission_classes = (AllowAny,)

    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")

        if not email or not password:
            return Response(
                {"Status": False, "Errors": "Нужно заполнить все поля"}, status=400
            )

        user = authenticate(request, email=email, password=password)
        if user is not None:
            token, _ = Token.objects.get_or_create(user=user)
            return Response({"Status": True, "Token": token.key})
        return Response(
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
        cart = Order.objects.filter(
            user=request.user,
            status=Order.Status.NEW,
        ).first()

        if not cart:
            return Response({"Cart": []})

        items = cart.ordered_items.all()
        serializer = OrderItemSerializer(items, many=True)

        return Response({"Cart": serializer.data})

    def post(self, request):
        items = request.data.get("items")

        if not items or not isinstance(items, list):
            return Response(
                {
                    "Status": False,
                    "Errors": (
                        "Необходим список товаров в формате "
                        '[{"product_id": 1, "shop_id": 1, "quantity": 1}]'
                    ),
                },
                status=400,
            )

        cart, _ = Order.objects.get_or_create(
            user=request.user,
            status=Order.Status.NEW,
        )

        added_count = 0

        for item in items:
            product_id = item.get("product_id")
            shop_id = item.get("shop_id")
            quantity = item.get("quantity")

            if not product_id or not shop_id or not quantity:
                continue

            product_info = (
                ProductInfo.objects.select_related("shop")
                .filter(
                    product_id=product_id,
                    shop_id=shop_id,
                )
                .first()
            )

            if not product_info:
                return Response(
                    {
                        "Status": False,
                        "Errors": (
                            f"Товар {product_id} " f"отсутствует у магазина {shop_id}"
                        ),
                    },
                    status=400,
                )

            if not product_info.shop.accepts_orders:
                return Response(
                    {
                        "Status": False,
                        "Errors": ("Поставщик временно " "не принимает заказы"),
                    },
                    status=400,
                )

            OrderItem.objects.update_or_create(
                order=cart,
                product_id=product_id,
                defaults={
                    "shop_id": shop_id,
                    "quantity": quantity,
                },
            )

            added_count += 1

        return Response(
            {
                "Status": True,
                "Added_items_count": added_count,
            }
        )

    def delete(self, request):
        items = request.data.get("items")

        if not items:
            return Response(
                {
                    "Status": False,
                    "Errors": "Не переданы ID товаров для удаления",
                },
                status=400,
            )

        if isinstance(items, str):
            items = items.split(",")

        cart = Order.objects.filter(
            user=request.user,
            status=Order.Status.NEW,
        ).first()

        if not cart:
            return Response(
                {
                    "Status": False,
                    "Errors": "Корзина не найдена или пуста",
                },
                status=404,
            )

        deleted_count = 0

        for item_id in items:
            deleted, _ = OrderItem.objects.filter(
                order=cart,
                product_id=item_id,
            ).delete()

            if deleted:
                deleted_count += 1

        return Response(
            {
                "Status": True,
                "Deleted_items_count": deleted_count,
            }
        )


class ContactView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        contacts = Contact.objects.filter(user=request.user)
        serializer = ContactSerializer(contacts, many=True)

        return Response({"Contacts": serializer.data})

    def post(self, request):
        serializer = ContactSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save(user=request.user)

            return Response(
                {
                    "Status": True,
                    "Contact": serializer.data,
                },
                status=201,
            )

        return Response(
            {
                "Status": False,
                "Errors": serializer.errors,
            },
            status=400,
        )

    def delete(self, request):
        contact_id = request.data.get("id")

        if not contact_id:
            return Response(
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
            return Response(
                {
                    "Status": False,
                    "Errors": "Контакт не найден",
                },
                status=404,
            )

        return Response(
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
            return Response(
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
            return Response(
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
            return Response(
                {
                    "Status": False,
                    "Errors": "Контакт не найден",
                },
                status=404,
            )

        if not cart.ordered_items.exists():
            return Response(
                {
                    "Status": False,
                    "Errors": "Нельзя подтвердить пустую корзину",
                },
                status=400,
            )

        cart.contact = contact
        cart.status = Order.Status.CONFIRMED
        cart.save(update_fields=["contact", "status"])
        send_mail(
            subject="Заказ подтверждён",
            message=(
                f"Здравствуйте, {request.user.first_name}!\n\n"
                f"Ваш заказ №{cart.id} подтверждён.\n"
                f"Адрес доставки: {contact.address}, "
                f"{contact.city}, ул. {contact.street}, дом {contact.house}."
            ),
            from_email=None,
            recipient_list=[contact.email],
        )
        return Response(
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


class OrderDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, request, pk):
        try:
            return (
                Order.objects.filter(
                    id=pk,
                    user=request.user,
                )
                .exclude(status=Order.Status.NEW)
                .prefetch_related(
                    "ordered_items__product",
                    "ordered_items__shop",
                )
                .get()
            )
        except Order.DoesNotExist:
            return None

    def get(self, request, pk):
        order = self.get_object(request, pk)

        if not order:
            return Response(
                {
                    "Status": False,
                    "Errors": "Заказ не найден",
                },
                status=404,
            )

        serializer = OrderDetailSerializer(order)

        return Response(serializer.data)


class ProductDetailView(RetrieveAPIView):
    serializer_class = ProductDetailSerializer
    permission_classes = [AllowAny]

    queryset = Product.objects.prefetch_related(
        "product_infos__shop",
        "product_infos__product_parameters__parameter",
    )


class PasswordResetRequestView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get("email")

        if not email:
            return Response(
                {
                    "Status": False,
                    "Errors": "Необходимо указать email",
                },
                status=400,
            )

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response(
                {
                    "Status": True,
                    "Message": "Если пользователь существует, письмо отправлено",
                }
            )

        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)

        send_mail(
            subject="Восстановление пароля",
            message=(
                "Для восстановления пароля используйте следующие данные:\n\n"
                f"uid: {uid}\n"
                f"token: {token}\n"
            ),
            from_email=None,
            recipient_list=[user.email],
        )

        return Response(
            {
                "Status": True,
                "Message": "Письмо для восстановления пароля отправлено",
            }
        )


class PasswordResetConfirmView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        uid = request.data.get("uid")
        token = request.data.get("token")
        password = request.data.get("password")

        if not uid or not token or not password:
            return Response(
                {
                    "Status": False,
                    "Errors": "Необходимо передать uid, token и password",
                },
                status=400,
            )

        try:
            user_id = urlsafe_base64_decode(uid).decode()
            user = User.objects.get(pk=user_id)
        except (
            User.DoesNotExist,
            ValueError,
            TypeError,
            OverflowError,
        ):
            return Response(
                {
                    "Status": False,
                    "Errors": "Недействительная ссылка восстановления",
                },
                status=400,
            )

        if not default_token_generator.check_token(user, token):
            return Response(
                {
                    "Status": False,
                    "Errors": "Недействительный или просроченный токен",
                },
                status=400,
            )

        user.set_password(password)
        user.save(update_fields=["password"])

        Token.objects.filter(user=user).delete()

        return Response(
            {
                "Status": True,
                "Message": "Пароль успешно изменён",
            }
        )


class SupplierOrderAcceptanceView(APIView):
    permission_classes = [IsSupplier]

    def post(self, request):
        accepts_orders = request.data.get("accepts_orders")

        if not isinstance(accepts_orders, bool):
            return Response(
                {
                    "Status": False,
                    "Errors": "Поле accepts_orders должно быть true или false",
                },
                status=400,
            )

        shop = getattr(request.user, "shop", None)

        if shop is None:
            return Response(
                {
                    "Status": False,
                    "Errors": "У пользователя нет магазина",
                },
                status=400,
            )

        shop.accepts_orders = accepts_orders
        shop.save(update_fields=["accepts_orders"])

        return Response(
            {
                "Status": True,
                "accepts_orders": shop.accepts_orders,
            }
        )

    def get(self, request):
        shop = getattr(request.user, "shop", None)

        if shop is None:
            return Response(
                {
                    "Status": False,
                    "Errors": "У пользователя нет магазина",
                },
                status=400,
            )

        orders = (
            Order.objects.filter(
                ordered_items__shop=shop,
            )
            .exclude(
                status=Order.Status.NEW,
            )
            .distinct()
            .prefetch_related(
                "ordered_items__product",
                "ordered_items__shop",
            )
        )

        for order in orders:
            order._supplier_items = list(order.ordered_items.filter(shop=shop))

        serializer = SupplierOrderSerializer(
            orders,
            many=True,
        )

        return Response(
            {
                "Orders": serializer.data,
            }
        )


class SupplierOrderStatusView(APIView):
    permission_classes = [IsSupplier]

    def patch(self, request, pk):
        shop = getattr(request.user, "shop", None)

        if shop is None:
            return Response(
                {
                    "Status": False,
                    "Errors": "У пользователя нет магазина",
                },
                status=400,
            )

        try:
            order = (
                Order.objects.filter(
                    id=pk,
                    ordered_items__shop=shop,
                )
                .distinct()
                .get()
            )
        except Order.DoesNotExist:
            return Response(
                {
                    "Status": False,
                    "Errors": "Заказ не найден",
                },
                status=404,
            )

        status_value = request.data.get("status")

        valid_statuses = {choice[0] for choice in Order.Status.choices}

        if status_value not in valid_statuses:
            return Response(
                {
                    "Status": False,
                    "Errors": (
                        "Недопустимый статус заказа. "
                        f"Допустимые значения: {sorted(valid_statuses)}"
                    ),
                },
                status=400,
            )

        order.status = status_value
        order.save(update_fields=["status"])
        order._supplier_items = list(order.ordered_items.filter(shop=shop))
        return Response(
            {
                "Status": True,
                "Order": SupplierOrderSerializer(order).data,
            }
        )
