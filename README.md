# Backend-приложение для автоматизации закупок

Система управления заказами для розничных сетей на Django REST Framework с возможностью импорта товаров, управления заказами и асинхронной обработкой задач.

## Возможности

### Базовый функционал
- ✅ Регистрация и авторизация пользователей (покупатели и поставщики)
- ✅ Каталог товаров с фильтрацией и поиском
- ✅ Корзина покупок
- ✅ Система заказов с контактными данными
- ✅ Импорт товаров из YAML файлов
- ✅ Email уведомления (регистрация, заказы, статусы)
- ✅ Административная панель Django

### Продвинутый функционал
- ✅ Асинхронная обработка задач (Celery + Redis)
- ✅ Экспорт товаров в YAML
- ✅ Управление статусами заказов в админке
- ✅ Email уведомления о смене статуса заказа
- ✅ API для поставщиков (управление прайс-листами)
- ✅ Docker контейнеризация

## Технический стек

- **Backend**: Django 4.2, Django REST Framework
- **База данных**: PostgreSQL 15
- **Кэш/Брокер**: Redis 7
- **Асинхронные задачи**: Celery
- **Контейнеризация**: Docker, Docker Compose
- **Дополнительно**: CORS, Email отправка, YAML импорт/экспорт

## Структура проекта

```
diplom_project/
├── diplom_project/          # Основные настройки Django
│   ├── settings.py         # Конфигурация приложения
│   ├── urls.py            # Главные URL маршруты
│   ├── celery.py          # Настройки Celery
│   └── wsgi.py            # WSGI конфигурация
├── backend/                # Основное приложение
│   ├── models.py          # Модели данных
│   ├── views.py           # API представления
│   ├── serializers.py     # Сериализаторы DRF
│   ├── urls.py            # URL маршруты API
│   ├── admin.py           # Административная панель
│   ├── signals.py         # Django сигналы
│   ├── tasks.py           # Асинхронные задачи Celery
│   └── migrations/        # Миграции базы данных
├── templates/              # HTML шаблоны
│   └── emails/            # Шаблоны email уведомлений
├── static/                # Статические файлы
├── media/                 # Загружаемые файлы
├── requirements.txt       # Python зависимости
├── docker-compose.yml     # Docker Compose конфигурация
├── Dockerfile            # Docker образ
├── .env                  # Переменные окружения
└── README.md             # Документация
```

## Установка и запуск

### Вариант 1: Docker (рекомендуется)

1. **Клонируйте репозиторий:**
```bash
git clone <repository-url>
cd diplom_project
```

2. **Создайте файл .env:**
```bash
cp .env.example .env
# Отредактируйте .env файл с вашими настройками
```

3. **Запустите контейнеры:**
```bash
docker-compose up --build
```

4. **Выполните миграции:**
```bash
docker-compose exec web python manage.py migrate
```

5. **Создайте суперпользователя:**
```bash
docker-compose exec web python manage.py createsuperuser
```

6. **Загрузите тестовые данные (опционально):**
```bash
docker-compose exec web python manage.py loaddata fixtures/test_data.json
```

### Вариант 2: Локальная установка

1. **Подготовьте окружение:**
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# или
venv\Scripts\activate     # Windows
```

2. **Установите зависимости:**
```bash
pip install -r requirements.txt
```

3. **Настройте базу данных PostgreSQL:**
```sql
CREATE DATABASE diplom_db;
CREATE USER diplom_user WITH PASSWORD 'password';
GRANT ALL PRIVILEGES ON DATABASE diplom_db TO diplom_user;
```

4. **Настройте Redis:**
```bash
# Ubuntu/Debian
sudo apt install redis-server
sudo systemctl start redis

# или используйте Docker
docker run -d -p 6379:6379 redis:7-alpine
```

5. **Выполните миграции:**
```bash
python manage.py migrate
```

6. **Создайте суперпользователя:**
```bash
python manage.py createsuperuser
```

7. **Запустите сервер разработки:**
```bash
python manage.py runserver
```

8. **В отдельных терминалах запустите Celery:**
```bash
# Worker
celery -A diplom_project worker --loglevel=info

# Beat scheduler
celery -A diplom_project beat --loglevel=info
```

## API Endpoints

### Пользователи
- `POST /api/v1/user/register` - Регистрация
- `POST /api/v1/user/register/confirm` - Подтверждение email
- `POST /api/v1/user/login` - Авторизация
- `GET/POST /api/v1/user/details` - Профиль пользователя
- `POST /api/v1/user/password_reset` - Сброс пароля

### Каталог
- `GET /api/v1/categories` - Список категорий
- `GET /api/v1/shops` - Список магазинов
- `GET /api/v1/products` - Список товаров (с фильтрацией)

### Корзина и заказы
- `GET/POST/PUT/DELETE /api/v1/basket` - Управление корзиной
- `GET/POST /api/v1/order` - Управление заказами
- `GET/POST/PUT/DELETE /api/v1/user/contact` - Контактные данные

### Поставщики
- `POST /api/v1/partner/update` - Обновление прайс-листа
- `GET/POST /api/v1/partner/state` - Статус магазина
- `GET /api/v1/partner/orders` - Заказы поставщика

### Примеры запросов

**Регистрация пользователя:**
```bash
curl -X POST http://localhost:8000/api/v1/user/register \
  -H "Content-Type: application/json" \
  -d '{
    "first_name": "Иван",
    "last_name": "Петров",
    "email": "ivan@example.com",
    "password": "securepassword123",
    "company": "ООО Рога и копыта",
    "position": "Менеджер"
  }'
```

**Получение товаров:**
```bash
curl -X GET "http://localhost:8000/api/v1/products?category_id=224&shop_id=1" \
  -H "Authorization: Token your-auth-token"
```

**Добавление товара в корзину:**
```bash
curl -X POST http://localhost:8000/api/v1/basket \
  -H "Content-Type: application/json" \
  -H "Authorization: Token your-auth-token" \
  -d '{
    "items": "[{\"product_info\": 1, \"quantity\": 2}]"
  }'
```

## Импорт товаров

Система поддерживает импорт товаров из YAML файлов следующего формата:

```yaml
shop: Связной
categories:
  - id: 224
    name: Смартфоны
  - id: 15
    name: Аксессуары
goods:
  - id: 4216292
    category: 224
    model: apple/iphone/xs-max
    name: Смартфон Apple iPhone XS Max 512GB (золотистый)
    price: 110000
    price_rrc: 116990
    quantity: 14
    parameters:
      "Диагональ (дюйм)": 6.5
      "Разрешение (пикс)": 2688x1242
      "Встроенная память (Гб)": 512
      "Цвет": золотистый
```

## Администрирование

1. **Доступ к админке:** http://localhost:8000/admin/
2. **Управление пользователями** - создание, редактирование, блокировка
3. **Управление заказами** - просмотр, изменение статусов
4. **Управление каталогом** - товары, категории, магазины
5. **Мониторинг задач** - Celery задачи и результаты

## Мониторинг и логи

### Логи приложения:
```bash
# Docker
docker-compose logs -f web

# Локально
tail -f logs/django.log
```

### Мониторинг Celery:
```bash
# Flower (опционально)
pip install flower
celery -A diplom_project flower
# http://localhost:5555
```

## Тестирование

```bash
# Запуск тестов
python manage.py test

# С покрытием
coverage run --source='.' manage.py test
coverage report
coverage html
```

## Развертывание в production

1. **Настройте переменные окружения:**
```bash
DEBUG=False
SECRET_KEY=your-production-secret-key
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
```

2. **Используйте HTTPS**
3. **Настройте nginx как reverse proxy**
4. **Используйте gunicorn вместо runserver**
5. **Настройте SSL сертификаты**

## Возможные улучшения

- [ ] Добавление API документации (Swagger/OpenAPI)
- [ ] Реализация системы скидок и промокодов
- [ ] Интеграция с платежными системами
- [ ] Уведомления через WebSocket
- [ ] Мобильное приложение
- [ ] Аналитика и отчеты
- [ ] Многоязычность (i18n)
- [ ] GraphQL API

## Поддержка

При возникновении проблем:
1. Проверьте логи приложения
2. Убедитесь, что все сервисы запущены
3. Проверьте настройки в .env файле
4. Обратитесь к документации Django и DRF

## Лицензия

Этот проект создан в образовательных целях.