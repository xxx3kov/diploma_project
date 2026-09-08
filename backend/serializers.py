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