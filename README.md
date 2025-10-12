# Backend-приложение для автоматизации закупок

Система управления заказами для розничных сетей на Django REST Framework с возможностью импорта товаров, управления заказами и асинхронной обработкой задач.
(Django с Celery, Docker и PostgreSQL)

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

- **Backend**: Django 5.2, Django REST Framework
- **База данных**: PostgreSQL 15
- **Кэш/Брокер**: Redis 7
- **Асинхронные задачи**: Celery
- **Контейнеризация**: Docker, Docker Compose
- **Дополнительно**: CORS, Email отправка, YAML импорт/экспорт
- **Nginx**: веб-сервер
- **Gunicorn**: WSGI сервер

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

если нет прав
перейдите в нужную базу
\c diplom_db
Назначьте права на схему
GRANT ALL PRIVILEGES ON SCHEMA public TO diplom_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO diplom_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO diplom_user;
права на создание таблиц
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO diplom_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO diplom_user;      
```

4. **Настройте Redis:**
```bash
# Ubuntu/Debian
sudo apt install redis-server
sudo systemctl start redis

# или используйте Docker
docker run -d -p 6379:6379 redis:7-alpine
локальный запуск
docker run -d --name redis-local -p 6379:6379 redis:7-alpine
```

5. **Выполните миграции:**
```bash
python manage.py migrate
```

6. **Создайте суперпользователя:**
```bash
python manage.py createsuperuser
```

6a. **Создание пользователя-поставщика для загрузки данных**
```bash
python manage.py shell

from backend.models import User, Shop

# Создаем пользователя-поставщика
user = User.objects.create_user(
    email='shop@example.com',
    password='shoppassword123',
    first_name='Магазин',
    last_name='Владелец',
    type='shop',
    is_active=True
)

# Создаем магазин
shop = Shop.objects.create(
    name='Связной',
    user=user,
    state=True
)

print(f"Создан пользователь ID: {user.id}")
print(f"Создан магазин ID: {shop.id}")
exit()
```

6b**Создание management команды для загрузки YAML**
```bash
Создайте файл backend/management/__init__.py (пустой)
Создайте файл backend/management/commands/__init__.py (пустой)
Создайте файл backend/management/commands/load_yaml_data.py
```

6c**Загрузка данных из YAML**
```bash
python manage.py load_yaml_data "C:\Python\Diplom\ProcurementDjango\data\shop1.yaml"
```

7. **Запустите сервер разработки:**
```bash
python manage.py runserver
```

8. **В отдельных терминалах запустите Celery:**
```bash
# Worker
celery -A ProcurementDjango worker --loglevel=info

# Beat scheduler
celery -A ProcurementDjango beat --loglevel=info
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
Docker сервисы
web - Django приложение (порт 8000)

db - PostgreSQL база данных (порт 5432)

redis - Redis для Celery (порт 6379)

celery - Celery worker для асинхронных задач

celery-beat - Celery планировщик

nginx - веб-сервер для статики (порт 80)

### Логи приложения:
```bash
# Docker
docker-compose logs -f web

# Локально
tail -f logs/django.log
```

### Мониторинг Celery:
```bash
docker compose logs celery
# Flower (опционально)
pip install flower
celery -A diplom_project flower
# http://localhost:5555
```

# Django команды
docker compose exec web python manage.py shell
docker compose exec web python manage.py createsuperuser

# Загрузка тестовых данных
docker compose exec web python manage.py load_yaml_data /app/data/shop1.yaml

# Очистка тестовых данных
docker compose exec web python manage.py clear_test_data

# Перезапуск сервисов
docker compose restart web celery

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

#######################################################################
# Развертывание проекта на Linux:

логин VM: roman

sudo apt update && sudo apt upgrade -y
sudo apt install -y curl wget git vim nano htop tree

Установка SSH сервера (если не установлен)
sudo apt install -y openssh-server
sudo systemctl enable ssh
sudo systemctl start ssh

Проверка IP адреса
ip addr show

ssh-keygen  # для генерации ключа
нужно настроить проброс портов в VB: сеть: хост 2222, гость 22
ssh -p 2222 roman@localhost
скопировать ключ:
cat ~/.ssh/id_ed25519.pub
добавить ключ сюда:
nano ~/.ssh/authorized_keys


--------------------------------------------------------------------
Установка Docker на Linux
# Удаляем старые версии Docker (если есть)
for pkg in docker.io docker-doc docker-compose podman-docker containerd runc; do
    sudo apt-get remove $pkg
done

# Обновляем пакеты
sudo apt-get update

# Устанавливаем необходимые пакеты
sudo apt-get install -y ca-certificates curl gnupg lsb-release

# Добавляем официальный GPG ключ Docker
sudo mkdir -m 0755 -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

# Добавляем Docker репозиторий
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Обновляем пакеты и устанавливаем Docker
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Добавляем пользователя в группу docker
sudo usermod -aG docker $USER

# Включаем автозапуск Docker
sudo systemctl enable docker
sudo systemctl start docker

# Проверяем установку
docker --version
docker compose version

Проверка Docker (после перезагрузки)
# Перезагружаемся для применения групп
sudo reboot

# После перезагрузки проверяем Docker
docker run hello-world
--------------------------------------------------------------------

Клонирование репозитория
Переходим в домашнюю директорию
cd ~

git clone git@github.com:Roman21780/ProcurementDjango.git
cd ProcurementDjango

Проверяем структуру файлов
tree -L 2

git checkout dj_linux
git pull origin dj_linux

sudo apt install python3 python3-pip python3-venv -y

python3 -m venv venv
source venv/bin/activate

pip install --upgrade pip
pip install -r requirements.txt

Устанавливаем библиотеку gunicorn
nginx: устанавливается и запускается через докер-контейнер
если вручную, то выйти из виртуального окружения и выполнить:
sudo apt update
sudo apt install nginx -y
команды:
sudo systemctl start nginx
sudo systemctl enable nginx
sudo systemctl status nginx
sudo systemctl restart nginx


Создаем файл .env.production
nano .env.production  # отредактировать настройки
# В файле измените:
# - SECRET_KEY на случайную строку длиной 50+ символов
# - DB_PASSWORD на безопасный пароль базы данных
# - EMAIL_HOST_USER и EMAIL_HOST_PASSWORD на ваши данные
# - При необходимости измените другие параметры

Проверяем настройки settings.py
ALLOWED_HOSTS = ['*'] либо конкретный IP

Создание директорий и установка прав

## Устанавливаем права на выполнение скриптов
chmod +x deploy.sh

## Проверяем структуру проекта
ls -la

## Запустить автоматическое развёртывание
./deploy.sh

#################################################

## или развернуть вручную
python manage.py migrate

python manage.py createsuperuser

Собрать статические файлы:
python manage.py collectstatic --noinput

Запуск Redis 
sudo systemctl restart redis

Запуск Celery worker
celery -A ProcurementDjango worker --loglevel=info

Запуск Django
gunicorn --bind 0.0.0.0:8000 ProcurementDjango.wsgi:application

#################################################

Создайте конфигурационный файл /etc/nginx/sites-available/procurement:
server {
    listen 80;
    server_name your_server_ip_or_domain;

    location / {
        proxy_pass http://127.0.0.1:8000;  # gunicorn работает на localhost
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static/ {
        alias /path/to/your/staticfiles/;
    }
}

Создайте символическую ссылку и активируйте сайт:
sudo ln -s /etc/nginx/sites-available/procurement /etc/nginx/sites-enabled/

Перезагрузите nginx:
sudo systemctl restart nginx

Настройка автоматического запуска
Создайте systemd-сервис для Gunicorn и запустите его, чтобы он автоматически стартовал при перезагрузке.
Запустите Celery worker также через systemd или screen/tmux.
Настройте бэкап базы данных, логирование и мониторинг.

После выполненных настроек проект будет доступен по адресу http://your_server_ip.
Можно установить SSL (например, с помощью Certbot) для безопасного соединения.
В режиме DEBUG=False — отключается debug toolbar и включается полноценная безопасность.

## Мониторинг процесса развёртывания
## Следим за логами в реальном времени (в отдельном терминале)
## Подключаемся по SSH с Windows:
ssh -p 2222 user@localhost

## Или открываем новую сессию в VirtualBox
## Переходим в папку проекта
cd ~/ProcurementDjango

## Следим за логами
docker compose logs -f web
## или
docker compose logs -f celery

## Проверка статуса сервисов
## Проверяем запущенные контейнеры
docker compose ps

## Проверяем логи всех сервисов
docker compose logs --tail=50

## Проверяем состояние Docker системы
docker system df
docker stats --no-stream

## Проверка через curl на Linux
## Проверяем корневую страницу API
curl http://localhost:8000/

## Проверяем API endpoints
curl http://localhost:8000/api/v1/
curl http://localhost:8000/api/v1/products
curl http://localhost:8000/api/v1/categories

## Проверяем админку
curl -I http://localhost:8000/admin/

## Проверка с Windows (через проброс портов)
## В браузере на Windows откройте:
http://localhost:8000/          # Главная страница API
http://localhost:8000/admin/    # Админка Django
http://localhost:8000/api/v1/   # API root

## Загрузка тестовых данных
## Загружаем данные из YAML файлов
docker compose exec web python manage.py load_yaml_data /app/data/shop1.yaml
docker compose exec web python manage.py load_yaml_data /app/data/shop2.yaml

## Проверяем загруженные данные
docker compose exec web python manage.py shell -c "
from backend.models import Product, Shop, Category;
print(f'Товаров: {Product.objects.count()}');
print(f'Магазинов: {Shop.objects.count()}');
print(f'Категорий: {Category.objects.count()}')
"

## Полезные команды для отладки
## Вход в Django shell
docker compose exec web python manage.py shell

## Просмотр логов отдельных сервисов
docker compose logs web          # Django
docker compose logs celery       # Celery Worker
docker compose logs celery-beat  # Celery Scheduler
docker compose logs db           # PostgreSQL
docker compose logs redis        # Redis

## Перезапуск отдельных сервисов
docker compose restart web
docker compose restart celery

## Остановка и полный перезапуск
docker compose down
docker compose up -d

## Очистка Docker системы (осторожно!)
docker system prune -a --volumes

## Резервное копирование
## Создание бэкапа базы данных
docker compose exec db pg_dump -U diplom_user diplom_db > backup_$(date +%Y%m%d_%H%M%S).sql

## Создание архива проекта
tar -czf procurement_backup_$(date +%Y%m%d_%H%M%S).tar.gz ~/ProcurementDjango

## Мониторинг и обслуживание
## Использование ресурсов контейнерами
docker stats

## Дисковое пространство Docker
docker system df

## Логи системы
journalctl -u docker -f

## Обновление проекта
## Обновление кода из Git
cd ~/ProcurementDjango
git pull origin main

## Пересборка и перезапуск
docker compose down
docker compose build --no-cache
docker compose up -d

## Выполнение миграций после обновления
docker compose exec web python manage.py migrate


## Автор
- Roman (@RomnSpunov - Telegram)













