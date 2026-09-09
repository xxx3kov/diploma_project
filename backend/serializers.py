from rest_framework import serializers
from .models import (
    Shop,
    Category,
    Product,
    ProductInfo,
    Parameter,
    ProductParameter,
    Contact,
    Order,
    OrderItem,
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
    product_parameters = ProductParameterSerializer(read_only=True, many=True)
    shop = serializers.StringRelatedField()
    product = serializers.StringRelatedField()

    class Meta:
        model = ProductInfo
        fields = ["name", "quantity", "price", "shop", "product", "product_parameters"]


# Сериализатор корзины
class OrderItemSerializer(serializers.ModelSerializer):
    total_sum = serializers.SerializerMethodField()
    price = serializers.SerializerMethodField()
    product = serializers.StringRelatedField()
    shop = serializers.StringRelatedField()

    class Meta:
        model = OrderItem
        fields = ['product', 'shop', 'price', 'quantity', 'total_sum']

    def get_price(self, obj):
        return ProductInfo.objects.get(shop=obj.shop, product=obj.product).price

    def get_total_sum(self, obj):
        return self.get_price(obj) * obj.quantity

# Сериализатор контактов
class ContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contact
        fields = ['id', 'type', 'value']
        read_only_fields = ['id']