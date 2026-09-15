# Orders API

Backend-приложение интернет-магазина на Django и Django REST Framework.

Проект предоставляет API для регистрации и авторизации пользователей, просмотра товаров, работы с корзиной и контактами, оформления заказов и загрузки товарных данных поставщиком.

## Технологии

* Python
* Django
* Django REST Framework
* Django Filter
* SQLite
* PyYAML
* Token Authentication
* Ruff

## Установка

Клонировать репозиторий и перейти в директорию проекта:

```bash
git clone https://github.com/xxx3kov/diploma_project
cd diploma_project
```

Создать виртуальное окружение:

```bash
python -m venv env
```

Активировать виртуальное окружение.

Linux/macOS:

```bash
source env/bin/activate
```

Windows PowerShell:

```powershell
.\env\Scripts\Activate.ps1
```

Установить зависимости:

```bash
pip install -r requirements.txt
```

## Настройка базы данных

Выполнить миграции:

```bash
python manage.py migrate
```

При необходимости создать администратора:

```bash
python manage.py createsuperuser
```

## Запуск проекта

Запустить сервер разработки:

```bash
python manage.py runserver
```

После запуска API доступно по адресу:

```text
http://127.0.0.1:8000/api/v1/
```

## API

### Регистрация

```http
POST /api/v1/user/register/
```

Регистрация нового пользователя.

Пример запроса:

```json
{
    "email": "user@example.com",
    "password": "password123",
    "first_name": "Иван",
    "last_name": "Иванов"
}
```

После успешной регистрации пользователь получает токен авторизации.

### Авторизация

```http
POST /api/v1/user/login/
```

Для авторизации необходимо передать email и пароль.

Полученный токен используется в защищённых запросах:

```http
Authorization: Token <TOKEN>
```

## Товары

Получение списка товаров:

```http
GET /api/v1/products/
```

Поддерживаются поиск и фильтрация товаров.

## Корзина

Получение содержимого корзины:

```http
GET /api/v1/cart/
```

Добавление товара в корзину:

```http
POST /api/v1/cart/
```

Удаление товара из корзины:

```http
DELETE /api/v1/cart/
```

Работа с корзиной доступна только авторизованным пользователям.

## Контакты

Получение сохранённых контактов:

```http
GET /api/v1/contacts/
```

Добавление контакта:

```http
POST /api/v1/contacts/
```

Удаление контакта:

```http
DELETE /api/v1/contacts/
```

## Заказы

Подтверждение заказа:

```http
POST /api/v1/orders/confirm/
```

Получение списка заказов пользователя:

```http
GET /api/v1/orders/
```

Получение информации о конкретном заказе:

```http
GET /api/v1/orders/<id>/
```

Пользователь может получать информацию только о собственных заказах.

## Поставщик

Для поставщика предусмотрена отдельная роль пользователя.

Для пользователя-поставщика поле:

```json
{
    "is_supplier": true
}
```

### Загрузка товаров

Поставщик может загрузить YAML-файл с информацией о магазине, категориях и товарах:

```http
POST /api/v1/partner/update/
```

Файл передаётся через `multipart/form-data` с параметром:

```text
file
```

Для выполнения запроса пользователь должен быть авторизован и иметь права поставщика.

Пример структуры YAML:

```yaml
shop: Связной

categories:
  - id: 224
    name: Смартфоны

goods:
  - id: 1
    category: 224
    model: iPhone
    name: iPhone
    quantity: 10
    price: 50000
    price_rrc: 55000
    parameters:
      Цвет: Чёрный
      Диагональ: "6.1"
```

При загрузке данные магазина, категорий, товаров и характеристик обновляются в базе данных.

## Основной сценарий работы

1. Пользователь регистрируется.
2. Пользователь авторизуется и получает токен.
3. Пользователь просматривает товары.
4. Добавляет товары в корзину.
5. Добавляет контактные данные.
6. Подтверждает заказ.
7. Просматривает список своих заказов.
8. При необходимости открывает детали конкретного заказа.

Поставщик:

1. Авторизуется как пользователь с ролью поставщика.
2. Загружает YAML-файл через API.
3. Данные магазина и товаров обновляются в базе данных.

## Структура проекта

```text
diploma_project/
├── backend/
│   ├── admin.py
│   ├── apps.py
│   ├── migrations/
│   ├── models.py
│   ├── permissions.py
│   ├── serializers.py
│   ├── urls.py
│   └── views.py
├── orders/
│   ├── settings.py
│   ├── urls.py
│   ├── asgi.py
│   └── wsgi.py
├── manage.py
├── requirements.txt
└── README.md
```

## Проверка проекта

Проверка Django:

```bash
python manage.py check
```

Проверка миграций:

```bash
python manage.py makemigrations --check --dry-run
```

Проверка кода:

```bash
ruff check .
```

Проверка форматирования:

```bash
ruff format --check .
```
