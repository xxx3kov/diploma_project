from django.contrib.auth.base_user import BaseUserManager
from django.db import models
from django.contrib.auth.models import AbstractUser

# Create your models here.


class UserManager(BaseUserManager):
    """
    Миксин для управления пользователями
    """

    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        """
        Create and save a user with the given username, email, and password.
        """
        if not email:
            raise ValueError("Email должен быть указан")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self._create_user(email, password, **extra_fields)


class User(AbstractUser):
    """Пользователь сервиса."""

    username = None
    email = models.EmailField(unique=True)
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []
    objects = UserManager()


class Shop(models.Model):
    """Магазин-поставщик товаров."""

    name = models.CharField(verbose_name="Наименование", max_length=50, unique=True)
    url = models.URLField(verbose_name="Ссылка")

    class Meta:
        verbose_name = "Магазин"
        verbose_name_plural = "Магазины"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Category(models.Model):
    """Категория товаров."""

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
    """Товар."""

    category = models.ForeignKey(
        Category,
        verbose_name="Категория",
        on_delete=models.CASCADE,
        related_name="products",
    )
    name = models.CharField(verbose_name="Название", max_length=255)

    class Meta:
        verbose_name = "Продукт"
        verbose_name_plural = "Список продуктов"
        ordering = ["name"]

    def __str__(self):
        return self.name


class ProductInfo(models.Model):
    """Информация о товаре у конкретного магазина."""

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
    name = models.CharField(verbose_name="Имя", max_length=255)
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
    """Характеристика товара."""

    name = models.CharField(verbose_name="Название", max_length=50)

    class Meta:
        verbose_name = "Имя параметра"
        verbose_name_plural = "Список имён параметров"
        ordering = ["name"]

    def __str__(self):
        return self.name


class ProductParameter(models.Model):
    """Значение характеристики конкретной товарной позиции."""

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
    """Контактная информация пользователя."""

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
    """Заказ пользователя."""

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
    """Отдельная товарная позиция внутри заказа."""

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
