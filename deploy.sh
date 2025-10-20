#!/bin/bash

# Скрипт развёртывания проекта Django Procurement
# Использование: ./deploy.sh [--dry-run] [--skip-backup]

set -e  # Прекратить выполнение при ошибке

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Параметры по умолчанию
DRY_RUN=false
SKIP_BACKUP=false

# Обработка аргументов командной строки
while [[ $# -gt 0 ]]; do
    case $1 in
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --skip-backup)
            SKIP_BACKUP=true
            shift
            ;;
        *)
            echo "Неизвестный параметр: $1"
            exit 1
            ;;
    esac
done

# Функция для вывода сообщений
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

# Функция для вывода предупреждений
warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] ⚠️  $1${NC}"
}

# Функция для вывода ошибок
error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ❌ $1${NC}" >&2
    exit 1
}

# Проверка прав администратора
check_root() {
    if [ "$(id -u)" -ne 0 ]; then
        error "Скрипт должен быть запущен с правами администратора (sudo)"
    fi
}

# Проверка установки Docker
check_docker() {
    if ! command -v docker &> /dev/null; then
        log "Docker не установлен. Устанавливаем..."
        if [ "$DRY_RUN" = false ]; then
            curl -fsSL https://get.docker.com -o get-docker.sh
            sh get-docker.sh
            usermod -aG docker $USER
            rm get-docker.sh
            log "✅ Docker установлен. Перезапустите систему и запустите скрипт снова."
            exit 0
        else
            log "✅ [DRY RUN] Docker будет установлен"
        fi
    fi
}

# Проверка Docker Compose
check_docker_compose() {
    if ! command -v docker-compose &> /dev/null; then
        log "Docker Compose не установлен. Устанавливаем..."
        if [ "$DRY_RUN" = false ]; then
            apt-get update
            apt-get install -y docker-compose-plugin
        else
            log "✅ [DRY RUN] Docker Compose будет установлен"
        fi
    fi
}

# Создание директорий
create_directories() {
    log "Создаём необходимые директории..."
    local dirs=("data" "logs" "media" "staticfiles" "backups")

    for dir in "${dirs[@]}"; do
        if [ ! -d "$dir" ]; then
            if [ "$DRY_RUN" = false ]; then
                mkdir -p "$dir"
                chmod 755 "$dir"
            fi
            log "✅ Создана директория: $dir"
        fi
    done
}

# Копирование файлов окружения
setup_environment() {
    if [ ! -f .env.production ]; then
        log "Создаём файл переменных окружения..."
        if [ -f .env.production.example ]; then
            if [ "$DRY_RUN" = false ]; then
                cp .env.production.example .env.production
                chmod 600 .env.production
            fi
            log "✅ Файл .env.production создан из примера"
        else
            warn "Файл .env.production.example не найден. Создайте .env.production вручную."
        fi
    fi
}

# Копирование файлов данных
copy_data_files() {
    local files=("shop1.yaml" "shop2.yaml")

    for file in "${files[@]}"; do
        if [ -f "$file" ] && [ ! -f "data/$file" ]; then
            if [ "$DRY_RUN" = false ]; then
                cp "$file" data/
                chmod 644 "data/$file"
            fi
            log "✅ $file скопирован в data/"
        fi
    done
}

# Остановка контейнеров
stop_containers() {
    log "Останавливаем существующие контейнеры..."
    if [ "$DRY_RUN" = false ]; then
        docker compose down --remove-orphans
    else
        log "✅ [DRY RUN] Контейнеры будут остановлены"
    fi
}

# Сборка образов
build_images() {
    log "Собираем Docker образы..."
    if [ "$DRY_RUN" = false ]; then
        docker compose build --no-cache
    else
        log "✅ [DRY RUN] Образы будут собраны с --no-cache"
    fi
}

# Запуск сервисов
start_services() {
    log "Запускаем сервисы..."
    if [ "$DRY_RUN" = false ]; then
        docker compose up -d
    else
        log "✅ [DRY RUN] Сервисы будут запущены в фоновом режиме"
    fi
}

# Ожидание готовности сервисов
wait_for_services() {
    local timeout=60
    local counter=0

    log "Ожидаем запуск базы данных..."
    sleep 5

    log "Проверяем готовность сервисов..."
    while ! docker compose exec -T web python manage.py check --deploy > /dev/null 2>&1; do
        if [ $counter -ge $timeout ]; then
            error "Тайм-аут ожидания готовности Django"
        fi
        log "⏳ Ожидаем готовность Django... ($counter/$timeout)"
        sleep 5
        counter=$((counter + 5))
    done
}

# Выполнение миграций
run_migrations() {
    log "Выполняем миграции..."
    if [ "$DRY_RUN" = false ]; then
        docker compose exec web python manage.py migrate
        log "✅ Миграции успешно применены"
    else
        log "✅ [DRY RUN] Будут выполнены миграции"
    fi
}

# Сбор статических файлов
collect_static() {
    log "Собираем статические файлы..."
    if [ "$DRY_RUN" = false ]; then
        docker compose exec web python manage.py collectstatic --noinput
        log "✅ Статические файлы собраны"
    else
        log "✅ [DRY RUN] Будут собраны статические файлы"
    fi
}

# Создание суперпользователя
create_superuser() {
    log "Проверяем существование суперпользователя..."
    if [ "$DRY_RUN" = false ]; then
        docker compose exec web python manage.py shell -c "
from django.contrib.auth import get_user_model;
User = get_user_model();
if not User.objects.filter(email='admin@example.com').exists():
    User.objects.create_superuser('admin@example.com', 'admin123', first_name='Admin', last_name='User')
    print('✅ Суперпользователь создан: admin@example.com / admin123')
else:
    print('ℹ️  Суперпользователь уже существует')
"
    else
        log "✅ [DRY RUN] Будет создан суперпользователь: admin@example.com / admin123"
    fi
}

# Загрузка тестовых данных
load_test_data() {
    local files=("data/shop1.yaml" "data/shop2.yaml")

    for file in "${files[@]}"; do
        if [ -f "$file" ]; then
            log "Загружаем данные из $file..."
            if [ "$DRY_RUN" = false ]; then
                docker compose exec web python manage.py load_yaml_data "/app/$file"
                log "✅ Данные из $file загружены"
            else
                log "✅ [DRY RUN] Будут загружены данные из $file"
            fi
        else
            warn "Файл $file не найден, пропускаем..."
        fi
    done
}

# Проверка статуса сервисов
check_services_status() {
    log "Проверяем статус сервисов..."
    if [ "$DRY_RUN" = false ]; then
        docker compose ps
    else
        log "✅ [DRY RUN] Будет выполнен вывод статуса сервисов"
    fi
}

# Резервное копирование базы данных
backup_database() {
    if [ "$SKIP_BACKUP" = true ]; then
        warn "Пропускаем резервное копирование базы данных (--skip-backup)"
        return
    fi

    local timestamp=$(date +'%Y%m%d_%H%M%S')
    local backup_dir="backups"
    local backup_file="$backup_dir/db_backup_$timestamp.sql"

    log "Создаём резервную копию базы данных..."

    if [ ! -d "$backup_dir" ]; then
        mkdir -p "$backup_dir"
    fi

    if [ "$DRY_RUN" = false ]; then
        if docker compose exec -T db pg_dump -U ${DB_USER:-diplom_user} ${DB_NAME:-diplom_db} > "$backup_file"; then
            log "✅ Резервная копия создана: $backup_file"
        else
            warn "Не удалось создать резервную копию базы данных"
        fi
    else
        log "✅ [DRY RUN] Будет создана резервная копия базы данных: $backup_file"
    fi
}

# Основная функция
main() {
    log "🚀 Начинаем развёртывание проекта Django Procurement..."

    if [ "$DRY_RUN" = true ]; then
        warn "РЕЖИМ ПРОСМОТРА (DRY RUN) - изменения не будут применены"
    fi

    check_root
    check_docker
    check_docker_compose
    create_directories
    setup_environment
    copy_data_files
    backup_database
    stop_containers
    build_images
    start_services
    wait_for_services
    run_migrations
    collect_static
    create_superuser
    load_test_data
    check_services_status

    log ""
    log "🎉 Развёртывание завершено!"
    log ""
    log "📋 Полезная информация:"
    log "  🌐 Web интерфейс: http://localhost:8000"
    log "  🔧 Админка: http://localhost:8000/admin"
    log "  📊 API документация: http://localhost:8000/api/v1/"
    log "  👤 Суперпользователь: admin@example.com / admin123"
    log ""
    log "🔧 Полезные команды:"
    log "  docker compose logs web          # Логи Django"
    log "  docker compose logs celery       # Логи Celery"
    log "  docker compose logs -f web       # Следить за логами в реальном времени"
    log "  docker compose exec web python manage.py shell  # Django shell"
    log "  docker compose down              # Остановить все сервисы"
    log "  docker compose up -d             # Запустить все сервисы"
    log "  docker compose restart web       # Перезапустить веб-сервер"
}

# Запуск основной функции
main