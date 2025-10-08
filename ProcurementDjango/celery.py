import os
from celery import Celery
from celery.schedules import crontab

# Устанавливаем модуль настроек Django для программы 'celery'
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ProcurementDjango.settings')

app = Celery('ProcurementDjango')

# Объект конфигурации для дочерних процессов.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Загружаем модули задач из всех зарегистрированных Django app конфигураций.
app.autodiscover_tasks()

# Настройки расписания для периодических задач
app.conf.beat_schedule = {
    'cleanup-old-tokens': {
        'task': 'backend.tasks.cleanup_old_tokens_task',
        'schedule': crontab(minute=0, hour='*/1'),  # каждый час в начало часа
    },
}

# Часовой пояс для планировщика
app.conf.timezone = 'Europe/Moscow'

# Конфигурация брокера и результатов для Docker
# В контейнерном окружении используем имя сервиса 'redis' вместо localhost
if os.getenv('DOCKER_ENV'):
    app.conf.broker_url = 'redis://redis:6379/0'
    app.conf.result_backend = 'redis://redis:6379/0'
else:
    # Для локальной разработки используем localhost
    app.conf.broker_url = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0')
    app.conf.result_backend = os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')