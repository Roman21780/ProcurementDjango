# Procurement Platform API

![Python](https://img.shields.io/badge/python-3.11-blue.svg)
![Django](https://img.shields.io/badge/django-5.0-green.svg)
![DRF](https://img.shields.io/badge/DRF-3.14-red.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)

Платформа для автоматизации закупок товаров для розничных сетей. REST API сервис, реализующий функционал для управления заказами, товарами, магазинами и пользователями.

## 📋 Содержание

- [Возможности](#возможности)
- [Технологии](#технологии)
- [Требования](#требования)
- [Установка](#установка)
- [Конфигурация](#конфигурация)
- [API Документация](#api-документация)
- [Тестирование](#тестирование)
- [Мониторинг и Профилирование](#мониторинг-и-профилирование)
- [Deployment](#deployment)
- [Структура проекта](#структура-проекта)

---

## 🚀 Возможности

### Для покупателей:
- Регистрация и аутентификация (включая OAuth через Google/GitHub)
- Просмотр каталога товаров с фильтрацией
- Управление корзиной
- Оформление заказов
- Управление контактами и адресами доставки
- История заказов

### Для поставщиков:
- Управление магазином (вкл/выкл)
- Загрузка прайс-листов через YAML
- Просмотр заказов с товарами магазина
- Загрузка изображений товаров
- Управление ассортиментом

### Для администраторов:
- Расширенная админ-панель (Django Baton)
- Управление заказами и пользователями
- Мониторинг производительности (Silk)
- Статистика и аналитика
- Управление кэшем

---

## 🛠 Технологии

### Backend
- **Python 3.11** - основной язык
- **Django 5.0** - веб-фреймворк
- **Django REST Framework 3.14** - REST API
- **PostgreSQL** - основная база данных
- **Redis** - кэширование и брокер сообщений
- **Celery** - асинхронные задачи

### Документация и Мониторинг
- **DRF-Spectacular** - OpenAPI/Swagger документация
- **Sentry** - отслеживание ошибок
- **Django Silk** - профилирование SQL запросов
- **Coverage** - покрытие тестами

### Производительность
- **Django Cachalot** - автоматическое кэширование ORM запросов
- **Django Redis** - кэширование данных
- **Gunicorn** - WSGI сервер
- **Nginx** - reverse proxy

### Дополнительно
- **Django Baton** - современная админ-панель
- **Django ImageKit** - обработка изображений
- **Social Auth** - OAuth аутентификация
- **Docker & Docker Compose** - контейнеризация

---

## 📦 Требования

- Docker 24.0+
- Docker Compose 2.20+
- Git

Или для локальной разработки:
- Python 3.11+
- PostgreSQL 15+
- Redis 7+

---

## ⚙️ Установка

### 1. Клонирование репозитория

git clone https://github.com/yourusername/procurement-platform.git
cd procurement-platform

text

### 2. Настройка переменных окружения

Скопируйте примеры конфигурации
cp .env.example .env.production

Отредактируйте .env.production
nano .env.production

text

### 3. Запуск через Docker

Сборка образов
docker compose build

Запуск контейнеров
docker compose up -d

Применение миграций
docker compose exec web python manage.py migrate

Создание суперпользователя
docker compose exec web python manage.py createsuperuser

Сбор статических файлов
docker compose exec web python manage.py collectstatic --noinput

text

### 4. Загрузка тестовых данных (опционально)

Загрузка товаров для магазина 1
docker compose exec web python manage.py load_yaml_data /app/data/shop1.yaml

Загрузка товаров для магазина 2
docker compose exec web python manage.py load_yaml_data /app/data/shop2.yaml

text

### 5. Проверка работы

Проверка всех интеграций
docker compose exec web python manage.py check_setup

Просмотр логов
docker compose logs -f web

text

Приложение доступно по адресу: [**http://localhost**](http://localhost)

---

## 🔧 Конфигурация

### Основные переменные окружения

См. файл `.env.example` для полного списка.

**Критичные настройки:**
- `SECRET_KEY` - секретный ключ Django (генерируется автоматически)
- `DEBUG` - режим отладки (False в production)
- `DATABASE_URL` - строка подключения к PostgreSQL
- `REDIS_URL` - строка подключения к Redis
- `SENTRY_DSN` - DSN для Sentry (мониторинг ошибок)

**OAuth credentials:**
- `GOOGLE_OAUTH2_KEY` / `GOOGLE_OAUTH2_SECRET`
- `GITHUB_KEY` / `GITHUB_SECRET`

**Email настройки:**
- `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`

---

## 📚 API Документация

### Swagger UI
Интерактивная документация с возможностью тестирования:
http://localhost/api/docs/

text

### ReDoc
Альтернативная документация:
http://localhost/api/redoc/

text

### OpenAPI Schema
JSON схема API:
http://localhost/api/schema/

text

### Основные endpoints:

#### Аутентификация
POST /api/v1/user/register/ # Регистрация
POST /api/v1/user/login/ # Авторизация
POST /api/v1/user/register/confirm # Подтверждение email
GET /api/v1/user/details # Данные пользователя
POST /api/v1/user/details # Обновление профиля

text

#### Каталог
GET /api/v1/categories/ # Категории товаров
GET /api/v1/shops/ # Магазины
GET /api/v1/products/ # Товары
?shop_id=1 # Фильтр по магазину
?category_id=1 # Фильтр по категории

text

#### Корзина и заказы
GET /api/v1/basket/ # Получить корзину
POST /api/v1/basket/ # Добавить в корзину
PUT /api/v1/basket/ # Изменить количество
DELETE /api/v1/basket/ # Удалить из корзины
GET /api/v1/order/ # Список заказов
POST /api/v1/order/ # Оформить заказ

text

#### Поставщики
POST /api/v1/partner/update/ # Загрузить прайс-лист
GET /api/v1/partner/state # Статус магазина
POST /api/v1/partner/state # Изменить статус
GET /api/v1/partner/orders/ # Заказы с товарами магазина

text

#### Загрузка файлов
POST /api/v1/user/avatar # Загрузить аватар
POST /api/v1/partner/product/image # Загрузить изображение товара

text

---

## 🧪 Тестирование

### Запуск тестов

Все тесты
docker compose exec web python manage.py test backend

С подробным выводом
docker compose exec web python manage.py test backend --verbosity=2

Конкретный тест
docker compose exec web python manage.py test backend.tests.UserRegistrationTests

text

### Покрытие кода
[![codecov](https://codecov.io/gh/Roman21780/ProcurementDjango/tree/test1/graph/badge.svg/graph/badge.svg)](https://codecov.io/gh/Roman21780/ProcurementDjango)

Запуск с измерением покрытия
docker compose exec web coverage run --source='backend' manage.py test backend

Отчёт в консоли
docker compose exec web coverage report

HTML отчёт
docker compose exec web coverage html

Скопировать отчёт на хост
docker compose cp web:/app/htmlcov ./htmlcov

text

Откройте `htmlcov/index.html` в браузере для детального отчёта.

### Текущее покрытие: **30%+**

---

## 📊 Мониторинг и Профилирование

### 1. Admin Panel (Django Baton)
http://localhost/admin/

text
- Современный интерфейс
- Управление всеми моделями
- Статистика и аналитика

### 2. Sentry (Error Tracking)

**Тестовые endpoints (только в DEBUG режиме):**
Тест ошибки
curl http://localhost/api/v1/test/sentry/error

Тест исключения
curl http://localhost/api/v1/test/sentry/exception

Management команда
docker compose exec web python manage.py test_sentry --type=error

text

**Dashboard:** https://sentry.io

### 3. Silk (SQL Profiling)
http://localhost/silk/

text
- Все HTTP запросы
- SQL запросы с временем выполнения
- Профилирование Python кода
- N+1 проблемы

**CLI команды:**
Анализ запросов
docker compose exec web python manage.py analyze_queries

Анализ медленных запросов
docker compose exec web python manage.py analyze_queries --slow=0.5

Очистка данных
docker compose exec web python manage.py clear_silk --days=7

text

### 4. Redis Cache

**Статистика кэша:**
CLI
docker compose exec web python manage.py cache_stats

API
curl -H "Authorization: Token ADMIN_TOKEN"
http://localhost/api/v1/admin/cache/stats

text

**Очистка кэша:**
CLI
docker compose exec web python manage.py clear_cache --type=all

API
curl -X POST -H "Authorization: Token ADMIN_TOKEN"
-H "Content-Type: application/json"
-d '{"type":"all"}'
http://localhost/api/v1/admin/cache/clear

text

### 5. Performance Stats
curl -H "Authorization: Token ADMIN_TOKEN"
http://localhost/api/v1/admin/performance?hours=24

text

---

## 🚀 Deployment

### Production настройки

1. **Обновите .env.production:**
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
SECRET_KEY=your-very-secret-key
SENTRY_ENVIRONMENT=production

text

2. **Настройте HTTPS в nginx:**
Получите SSL сертификат (Let's Encrypt)
certbot --nginx -d yourdomain.com -d www.yourdomain.com

text

3. **Настройте firewall:**
ufw allow 80/tcp
ufw allow 443/tcp
ufw enable

text

4. **Запустите в production режиме:**
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d

text

5. **Настройте мониторинг:**
- Sentry для ошибок
- Health checks через `/api/v1/health/`
- Log aggregation (ELK, Papertrail)

### CI/CD

Пример GitHub Actions в `.github/workflows/deploy.yml`:

name: Deploy

on:
push:
branches: [main]

jobs:
deploy:
runs-on: ubuntu-latest
steps:
- uses: actions/checkout@v3
- name: Deploy to server
uses: appleboy/ssh-action@master
with:
host: ${{ secrets.HOST }}
username: ${{ secrets.USERNAME }}
key: ${{ secrets.SSH_KEY }}
script: |
cd /app/procurement-platform
git pull
docker compose build
docker compose up -d
docker compose exec -T web python manage.py migrate
docker compose exec -T web python manage.py collectstatic --noinput

text

---

## 📁 Структура проекта

procurement-platform/
├── backend/ # Основное Django приложение
│ ├── management/
│ │ └── commands/ # Management команды
│ ├── migrations/ # Миграции БД
│ ├── templates/ # HTML шаблоны
│ ├── admin.py # Админ-панель
│ ├── models.py # Модели данных
│ ├── serializers.py # DRF сериализаторы
│ ├── views.py # API views
│ ├── urls.py # URL маршруты
│ ├── tasks.py # Celery задачи
│ ├── signals.py # Django signals
│ ├── tests.py # Тесты
│ └── pipeline.py # Social auth pipeline
│
├── config/ # Конфигурация проекта
│ ├── settings.py # Настройки Django
│ ├── urls.py # Главные URL
│ ├── celery.py # Celery конфигурация
│ └── wsgi.py # WSGI entry point
│
├── data/ # Тестовые данные
│ ├── shop1.yaml
│ └── shop2.yaml
│
├── nginx/ # Конфигурация Nginx
│ └── nginx.conf
│
├── docker-compose.yml # Docker Compose конфигурация
├── Dockerfile # Docker образ приложения
├── requirements.txt # Python зависимости
├── .env.example # Пример переменных окружения
├── .gitignore
└── README.md

text

---

## 🔐 Безопасность

- Все пароли хешируются (Django PBKDF2)
- JWT токены для API аутентификации
- CORS настроен для разрешённых доменов
- CSRF защита
- SQL injection защита (Django ORM)
- XSS защита
- Rate limiting (настраивается)
- HTTPS в production

---

## 📝 Лицензия

MIT License - см. файл [LICENSE](LICENSE)

---

## 👥 Авторы

- **Ваше Имя** - [GitHub](https://github.com/yourusername)

---

## 🤝 Поддержка

Для вопросов и предложений:
- Email: support@procurement.com
- GitHub Issues: https://github.com/yourusername/procurement-platform/issues
- Telegram: @your_telegram

---

## 📈 Roadmap

- [ ] GraphQL API
- [ ] WebSocket уведомления
- [ ] Мобильное приложение
- [ ] Интеграция с платёжными системами
- [ ] Расширенная аналитика
- [ ] Multi-tenancy
- [ ] Internationalization (i18n)

---

## 🙏 Благодарности

- Django Team
- DRF Team
- Все контрибьюторы используемых библиотек

---

**Сделано с ❤️ в России**