from django.db import transaction
from django.http import JsonResponse
from rest_framework.generics import CreateAPIView
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
import yaml

from backend.models import (
    Category,
    Parameter,
    Product,
    ProductInfo,
    ProductParameter,
    Shop,
    User,
)
from backend.serializers import UserSerializer


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
    permission_classes=(AllowAny, )