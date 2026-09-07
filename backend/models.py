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
    name = models.CharField(verbose_name="Название", max_length=50)

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
    name = models.CharField(verbose_name="Имя", max_length=50)
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
    name = models.CharField(verbose_name="Название", max_length=50)

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
        on_delete=models.CASCADE,
    )
    parameter = models.ForeignKey(
        Parameter,
        verbose_name="Параметр",
        related_name="product_parameters",
        on_delete=models.CASCADE,
    )
    value = models.CharField(verbose_name="Значение", max_length=100)

    class Meta:
        verbose_name = "Параметр"
        verbose_name_plural = "Список параметров"
        constraints = [
            models.UniqueConstraint(
                fields=["product_info", "parameter"], name="unique_product_parameter"
            ),
        ]

    def __str__(self):
        return f"{self.parameter.name}: {self.value}"


class Contact(models.Model):
    type = models.CharField(verbose_name="Тип связи", max_length=50)
    user = models.ForeignKey(
        User,
        verbose_name="Пользователь",
        related_name="contacts",
        on_delete=models.CASCADE,
    )
    value = models.CharField(verbose_name="Адрес/телефон/mail", max_length=100)

    class Meta:
        verbose_name = "Контакт"
        verbose_name_plural = "Список контактов"
        ordering = ["type"]

    def __str__(self):
        return f"{self.user}: {self.value}"


class Order(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="orders",
        verbose_name="Пользователь",
    )
    dt = models.DateTimeField(auto_now_add=True)

    class Status(models.TextChoices):
        NEW = "new", "Новый"
        CONFIRMED = "confirmed", "Подтверждён"
        SHIPPED = "shipped", "Отправлен"
        DELIVERED = "delivered", "Доставлен"
        CANCELLED = "cancelled", "Отменён"

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.NEW,
    )

    class Meta:
        verbose_name = "Заказ"
        verbose_name_plural = "Список заказов"
        ordering = ["-dt"]

    def __str__(self):
        return f"{self.user}:{self.status}"


class OrderItem(models.Model):
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="ordered_items",
        verbose_name="Заказ",
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="ordered_items",
        verbose_name="Продукт",
    )
    shop = models.ForeignKey(
        Shop, on_delete=models.CASCADE, related_name="ordered_items"
    )
    quantity = models.PositiveIntegerField(verbose_name="Количество")

    class Meta:
        verbose_name = "Заказанная позиция"
        verbose_name_plural = "Список заказанных позиций"
        constraints = [
            models.UniqueConstraint(
                fields=["order", "product"], name="unique_order_item"
            ),
        ]
