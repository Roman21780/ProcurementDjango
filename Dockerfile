# Базовый образ Python с конкретной версией
FROM python:3.13.0-slim as builder

# Оптимизация Python в Docker
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Устанавливаем системные зависимости
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Копируем и устанавливаем зависимости
WORKDIR /build
COPY requirements.txt .
RUN pip install --no-warn-script-location -r requirements.txt

# Финальный образ
FROM python:3.13.0-slim

# Копируем Python-зависимости из builder В СИСТЕМНУЮ ДИРЕКТОРИЮ
COPY --from=builder /usr/local/lib/python3.13/site-packages /usr/local/lib/python3.13/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Устанавливаем только необходимые пакеты
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Создаём непривилегированного пользователя
RUN addgroup --system django && adduser --system --ingroup django django

# Настройка рабочей директории
WORKDIR /app
RUN mkdir -p /app/staticfiles /app/media /app/logs /app/data /app/profiles \
    && chown -R django:django /app

# Создаём файл логов с правильными правами
RUN touch /app/logs/django.log && \
    chown django:django /app/logs/django.log && \
    chmod 666 /app/logs/django.log

# Копируем проект
COPY --chown=django:django . .

# Настраиваем переменные окружения
ENV PYTHONPATH="/app" \
    PATH="/usr/local/bin:${PATH}"

# Переключаемся на непривилегированного пользователя
USER django

# Открываем порт 8000 для Gunicorn
EXPOSE 8000

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health/ || exit 1

# Команда по умолчанию
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "3", \
    "--timeout", "60", "--worker-class", "gthread", "--threads", "2", \
    "--access-logfile", "-", "--error-logfile", "-", "--log-level", "info", \
    "ProcurementDjango.wsgi:application"]
