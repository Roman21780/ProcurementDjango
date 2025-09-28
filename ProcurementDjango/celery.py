import os
from celery import Celery

# Устанавливаем модуль настроек Django для программы 'celery'
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ProcurementDjango.settings')

app = Celery('ProcurementDjango')

# объект конфигурации для дочерних процессов.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Загружаем модули задач из всех зарегистрированных Django app конфигураций.
app.autodiscover_tasks()

# Настройки расписания для периодических задач
app.conf.beat_schedule = {
    'cleanup-old-tokens': {
        'task': 'backend.tasks.cleanup_old_tokens_task',
        'schedule': 3600.0, # каждый час
    },
}
app.conf.timezone = 'Europe/Moscow'
