from rest_framework import serializers

from .models import (
    Contact,
    Order,
    OrderItem,
    Product,
    ProductInfo,
    ProductParameter,
    Shop,
    User,
)


# Сериализатор для магазинов
class ShopSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shop
        fields = ["id", "name", "url"]


# Сериализатор пользователя
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["email", "password", "first_name", "last_name"]
        extra_kwargs = {"password": {"write_only": True}}

    def create(self, validated_data):
        # Автоматически хэширует пароль
        user = User.objects.create_user(**validated_data)
        return user


# Сериализатор характеристик
class ProductParameterSerializer(serializers.ModelSerializer):
    parameter = serializers.StringRelatedField()

    class Meta:
        model = ProductParameter
        fields = ["parameter", "value"]


# Сериализатор информации продукта
class ProductInfoSerializer(serializers.ModelSerializer):
    product_parameters = ProductParameterSerializer(
        read_only=True,
        many=True,
    )
    shop = serializers.StringRelatedField()
    product = serializers.StringRelatedField()
    description = serializers.CharField(
        source="product.description",
        read_only=True,
    )

    class Meta:
        model = ProductInfo
        fields = [
            "name",
            "description",
            "shop",
            "product",
            "product_parameters",
            "price",
            "quantity",
        ]


class ProductDetailSerializer(serializers.ModelSerializer):
    product_infos = ProductInfoSerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = ["id", "name", "description", "product_infos"]


# Сериализатор корзины
class OrderItemSerializer(serializers.ModelSerializer):
    total_sum = serializers.SerializerMethodField()
    price = serializers.SerializerMethodField()
    product = serializers.StringRelatedField()
    shop = serializers.StringRelatedField()

    class Meta:
        model = OrderItem
        fields = ["product", "shop", "price", "quantity", "total_sum"]

    def get_price(self, obj):
        product_info = getattr(obj, "_product_info", None)

        if product_info is None:
            product_info = (
                ProductInfo.objects.filter(shop=obj.shop, product=obj.product)
                .order_by("id")
                .first()
            )

        return product_info.price if product_info else 0

    def get_total_sum(self, obj):
        return self.get_price(obj) * obj.quantity


class SupplierOrderSerializer(serializers.ModelSerializer):
    number = serializers.IntegerField(
        source="id",
        read_only=True,
    )
    date = serializers.DateTimeField(
        source="dt",
        read_only=True,
    )
    status = serializers.CharField(read_only=True)
    items = serializers.SerializerMethodField()
    total_sum = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = [
            "number",
            "date",
            "status",
            "total_sum",
            "items",
        ]

    def _get_supplier_items(self, obj):
        return getattr(obj, "_supplier_items", obj.ordered_items.all())

    def get_items(self, obj):
        items = self._get_supplier_items(obj)

        return OrderItemSerializer(
            items,
            many=True,
        ).data

    def get_total_sum(self, obj):
        total = 0

        for item in self._get_supplier_items(obj):
            product_info = ProductInfo.objects.filter(
                shop=item.shop,
                product=item.product,
            ).first()

            if product_info:
                total += product_info.price * item.quantity

        return total


# Сериализатор контактов
class ContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contact
        fields = [
            "id",
            "last_name",
            "first_name",
            "middle_name",
            "email",
            "phone",
            "address",
            "city",
            "street",
            "house",
            "building",
            "structure",
            "apartment",
        ]
        read_only_fields = ["id"]


# Сериализатор заказа
class OrderSerializer(serializers.ModelSerializer):
    number = serializers.IntegerField(
        source="id",
        read_only=True,
    )
    date = serializers.DateTimeField(
        source="dt",
        read_only=True,
    )
    total_sum = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = [
            "number",
            "date",
            "total_sum",
            "status",
        ]

    def get_total_sum(self, obj):
        total = 0

        for item in obj.ordered_items.all():
            try:
                price = ProductInfo.objects.get(
                    product=item.product,
                    shop=item.shop,
                ).price
            except ProductInfo.DoesNotExist:
                price = 0

            total += price * item.quantity

        return total


class OrderDetailSerializer(serializers.ModelSerializer):
    number = serializers.IntegerField(source="id", read_only=True)
    date = serializers.DateTimeField(source="dt", read_only=True)
    total_sum = serializers.SerializerMethodField()
    items = OrderItemSerializer(
        source="ordered_items",
        many=True,
        read_only=True,
    )

    class Meta:
        model = Order
        fields = [
            "number",
            "date",
            "status",
            "total_sum",
            "items",
        ]

    def get_total_sum(self, obj):
        total = 0

        for item in obj.ordered_items.all():
            try:
                price = ProductInfo.objects.get(
                    product=item.product,
                    shop=item.shop,
                ).price
            except ProductInfo.DoesNotExist:
                price = 0

            total += price * item.quantity

        return total
