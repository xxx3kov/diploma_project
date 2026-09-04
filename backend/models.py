from django.db import models
from django.contrib.auth.models import AbstractUser

# Create your models here.


class User(AbstractUser):
    pass


class Shop(models.Model):
    name = models.CharField(verbose_name="Наименование", max_length=50, unique=True)
    url = models.URLField(verbose_name="Ссылка")

    class Meta:
        verbose_name = "Магазин"
        verbose_name_plural = "Магазины"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Category(models.Model):
    shops = models.ManyToManyField(
        Shop, verbose_name="Магазины", related_name="categories"
    )
    name = models.CharField(verbose_name="Название", max_length=50, unique=True)

    class Meta:
        verbose_name = "Категория"
        verbose_name_plural = "Категории"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Product(models.Model):
    category = models.ForeignKey(
        Category,
        verbose_name="Категория",
        on_delete=models.CASCADE,
        related_name="products",
    )
    name = models.CharField(verbose_name="Название")

    class Meta:
        verbose_name = "Продукт"
        verbose_name_plural = "Список продуктов"
        ordering = ["name"]

    def __str__(self):
        return self.name


class ProductInfo(models.Model):
    product = models.ForeignKey(
        Product,
        verbose_name="Продукт",
        on_delete=models.CASCADE,
        related_name="product_infos",
    )
    shop = models.ForeignKey(
        Shop,
        verbose_name="Магазин",
        on_delete=models.CASCADE,
        related_name="product_infos",
    )
    name = models.CharField(verbose_name="Имя")
    quantity = models.PositiveIntegerField(verbose_name="Количество")
    price = models.DecimalField(
        verbose_name="Стоимость", max_digits=10, decimal_places=2
    )
    price_rrc = models.DecimalField(
        verbose_name="Розничная стоимость", max_digits=10, decimal_places=2
    )

    class Meta:
        verbose_name = "Информация о продукте"
        verbose_name_plural = "Информационный список продуктов"
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(
                fields=["product", "shop", "name"], name="unique_product_info"
            )
        ]

    def __str__(self):
        return self.name


class Parameter(models.Model):
    name = models.CharField(verbose_name="Название")

    class Meta:
        verbose_name = "Имя параметра"
        verbose_name_plural = "Список имён параметров"
        ordering = ["name"]

    def __str__(self):
        return self.name


class ProductParameter(models.Model):
    product_info = models.ForeignKey(
        ProductInfo,
        verbose_name="Информация о продукте",
        related_name="product_parameters",
    )
    parameter = models.ForeignKey(
        Parameter, verbose_name="Параметр", related_name="product_parameters"
    )
    value = models.CharField(verbose_name="Значение", max_length=100)

    class Meta:
        verbose_name = "Параметр"
        verbose_name_plural = "Список параметров"
        ordering = ["name"]

    def __str__(self):
        return f"{self.parameter.name}: {self.value}"
