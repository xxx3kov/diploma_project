from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import render
from rest_framework.views import APIView
import yaml

from backend.models import (
    Category,
    Parameter,
    Product,
    ProductInfo,
    ProductParameter,
    Shop,
)

# Create your views here.


class PartnerUpdateView(APIView):
    @transaction.atomic
    def post(self, request):
        try:
            with open("data/shop1.yaml", "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
                shop, _ = Shop.objects.update_or_create(name=data["shop"])
                for category_data in data["categories"]:
                    category, _ = Category.objects.update_or_create(
                        name=category_data["name"]
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

            return JsonResponse({"Status": True})

        except Exception as e:
            return JsonResponse({"Status": False, "Errors": str(e)}, status=400)
