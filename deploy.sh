#!/bin/bash

# Скрипт развёртывания проекта на Linux

set -e  # Прекратить выполнение при ошибке

echo "🚀 Начинаем развёртывание проекта Django Procurement..."

# Проверка установки Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker не установлен. Устанавливаем..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    rm get-docker.sh
    echo "✅ Docker установлен. Перезапустите систему и запустите скрипт снова."
    exit 1
fi

# Проверка Docker Compose
if ! command -v docker compose &> /dev/null; then
    echo "❌ Docker Compose не установлен. Устанавливаем..."
    sudo apt update
    sudo apt install docker-compose-plugin -y
fi

# Создание директорий
echo "📁 Создаём необходимые директории..."
mkdir -p data logs media staticfiles

# Копирование примера переменных окружения
if [ ! -f .env.production ]; then
    echo "📋 Создаём файл переменных окружения..."
    cp .env.production.example .env.production 2>/dev/null || {
        echo "⚠️  Файл .env.production.example не найден. Создайте .env.production вручную."
    }
fi

# Копирование файлов данных
echo "📋 Подготавливаем файлы данных..."
if [ -f "shop1.yaml" ] && [ ! -f "data/shop1.yaml" ]; then
    cp shop1.yaml data/
    echo "✅ shop1.yaml скопирован в data/"
fi

if [ -f "shop2.yaml" ] && [ ! -f "data/shop2.yaml" ]; then
    cp shop2.yaml data/
    echo "✅ shop2.yaml скопирован в data/"
fi

# Остановка существующих контейнеров
echo "🛑 Останавливаем существующие контейнеры..."
docker compose down --remove-orphans

# Сборка образов
echo "🔨 Собираем Docker образы..."
docker compose build --no-cache

# Запуск сервисов
echo "▶️ Запускаем сервисы..."
docker compose up -d

# Ожидание запуска базы данных
echo "⏳ Ожидаем запуск базы данных..."
sleep 20

# Ожидание готовности сервисов
echo "🔍 Проверяем готовность сервисов..."
timeout=60
counter=0
while ! docker compose exec -T web python manage.py check --deploy > /dev/null 2>&1; do
    if [ $counter -ge $timeout ]; then
        echo "❌ Тайм-аут ожидания готовности Django"
        exit 1
    fi
    echo "⏳ Ожидаем готовность Django... ($counter/$timeout)"
    sleep 5
    counter=$((counter + 5))
done

# Выполнение миграций
echo "🔄 Выполняем миграции..."
docker compose exec web python manage.py migrate

echo "⏳ Ждём стабилизации после миграций..."
sleep 10

# Сбор статических файлов
echo "📦 Собираем статические файлы..."
docker compose exec web python manage.py collectstatic --noinput

# Создание суперпользователя
echo "👤 Создаём суперпользователя..."
docker compose exec web python manage.py shell -c "
from django.contrib.auth import get_user_model;
User = get_user_model();
if not User.objects.filter(email='admin@example.com').exists():
    User.objects.create_superuser('admin@example.com', 'admin123', first_name='Admin', last_name='User')
    print('Суперпользователь создан: admin@example.com / admin123')
else:
    print('Суперпользователь уже существует')
"

# Загрузка тестовых данных
echo "📦 Загружаем тестовые данные..."
if [ -f "data/shop1.yaml" ]; then
    docker compose exec web python manage.py load_yaml_data /app/data/shop1.yaml
    echo "✅ Данные из shop1.yaml загружены"
else
    echo "⚠️ Файл data/shop1.yaml не найден"
fi

if [ -f "data/shop2.yaml" ]; then
    docker compose exec web python manage.py load_yaml_data /app/data/shop2.yaml
    echo "✅ Данные из shop2.yaml загружены"
else
    echo "⚠️ Файл data/shop2.yaml не найден"
fi

# Проверка статуса сервисов
echo "🔍 Проверяем статус сервисов..."
docker compose ps

echo ""
echo "🎉 Развёртывание завершено!"
echo ""
echo "📋 Полезная информация:"
echo "  🌐 Web интерфейс: http://localhost:8000"
echo "  🔧 Админка: http://localhost:8000/admin"
echo "  📊 API документация: http://localhost:8000/api/v1/"
echo "  👤 Суперпользователь: admin@example.com / admin123"
echo ""
echo "🔧 Полезные команды:"
echo "  docker compose logs web          # Логи Django"
echo "  docker compose logs celery       # Логи Celery"
echo "  docker compose logs -f web       # Следить за логами в реальном времени"
echo "  docker compose exec web python manage.py shell  # Django shell"
echo "  docker compose down              # Остановить все сервисы"
echo "  docker compose up -d             # Запустить все сервисы"
echo "  docker compose restart web       # Перезапустить веб-сервер"
echo ""
echo "🧪 Тестирование API:"
echo "  curl http://localhost:8000/api/v1/"
echo "  curl http://localhost:8000/api/v1/products"
echo "  curl http://localhost:8000/api/v1/categories"
