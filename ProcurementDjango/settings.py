"""
Django settings for ProcurementDjango project.
"""

import os
from pathlib import Path


from dotenv import load_dotenv
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration
from sentry_sdk.integrations.celery import CeleryIntegration
from sentry_sdk.integrations.redis import RedisIntegration
from sentry_sdk.integrations.logging import LoggingIntegration
import logging

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv('DEBUG', 'True').lower() in ('true', '1', 't')

# Sentry Configuration
SENTRY_DSN = os.getenv('SENTRY_DSN', '')
SENTRY_ENVIRONMENT = os.getenv('SENTRY_ENVIRONMENT', 'development')

if SENTRY_DSN:
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[
            DjangoIntegration(
                transaction_style='url',
                middleware_spans=True,
                signals_spans=True,
                cache_spans=True,
            ),
            CeleryIntegration(
                monitor_beat_tasks=True,
                propagate_traces=True,
            ),
            RedisIntegration(),
            LoggingIntegration(
                level=logging.INFO,
                event_level=logging.ERROR
            ),
        ],

        environment=SENTRY_ENVIRONMENT,

        # Частота отправки трейсов производительности
        # 1.0 = 100% для development, 0.1-0.3 для production
        traces_sample_rate=1.0,

        # Профилирование производительности
        profiles_sample_rate=1.0,

        # Отправлять персональные данные (email, IP) для дебага
        send_default_pii=True,

        # Прикреплять полный стек вызовов
        attach_stacktrace=True,

        # Функция для фильтрации событий перед отправкой
        before_send=lambda event, hint: event,
    )

# Загружаем переменные окружения
load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-change-me-in-production')

# Исправлена обработка ALLOWED_HOSTS с обрезкой пробелов
ALLOWED_HOSTS = [host.strip() for host in os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1,10.0.2.15').split(',')]

# Application definition
INSTALLED_APPS = [
    'baton',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # REST Framework
    'rest_framework',
    'rest_framework.authtoken',
    'django_rest_passwordreset',

    # cache
    'cacheops',

    # silk
    'silk',

    # CORS
    'corsheaders',

    # Celery
    'django_celery_beat',
    'django_celery_results',

    # imagekit
    'imagekit',

    # Local apps
    'backend',

    # spectacular
    'drf_spectacular',

    # social
    'social_django',

    # baton
    'baton.autodiscover',
]

# Django Baton Configuration
BATON = {
    'SITE_HEADER': 'Procurement Platform',
    'SITE_TITLE': 'Procurement Admin',
    'INDEX_TITLE': 'Панель управления закупками',
    'SUPPORT_HREF': 'mailto:sapunovrm21780@gmail.com',
    'COPYRIGHT': 'Copyright © 2025 Procurement Platform',
    'POWERED_BY': '<a href="https://github.com/Roman21780/ProcurementDjango">Procurement Team</a>',
    'CONFIRM_UNSAVED_CHANGES': True,
    'SHOW_MULTIPART_UPLOADING': True,
    'ENABLE_IMAGES_PREVIEW': True,
    'CHANGELIST_FILTERS_IN_MODAL': True,
    'CHANGELIST_FILTERS_ALWAYS_OPEN': False,
    'CHANGELIST_FILTERS_FORM': True,
    'MENU_ALWAYS_COLLAPSED': False,
    'MENU_TITLE': 'Меню',
    'MESSAGES_TOASTS': False,
    'GRAVATAR_DEFAULT_IMG': 'retro',
    'GRAVATAR_ENABLED': True,
    'LOGIN_SPLASH': '/static/core/img/login-splash.png',
    'FORCE_THEME': None,  # None, 'light', 'dark'

    # Меню навигации
    'MENU': (
        {'type': 'title', 'label': 'Главная', 'apps': ('auth',)},
        {
            'type': 'app',
            'name': 'auth',
            'label': 'Аутентификация',
            'icon': 'fa fa-lock',
            'models': (
                {
                    'name': 'user',
                    'label': 'Пользователи',
                },
                {
                    'name': 'group',
                    'label': 'Группы',
                },
            )
        },
        {'type': 'title', 'label': 'Управление заказами', 'apps': ('backend',)},
        {
            'type': 'app',
            'name': 'backend',
            'label': 'Основные модули',
            'icon': 'fa fa-shopping-cart',
            'models': (
                {
                    'name': 'user',
                    'label': 'Пользователи',
                    'icon': 'fa fa-users'
                },
                {
                    'name': 'shop',
                    'label': 'Магазины',
                    'icon': 'fa fa-store'
                },
                {
                    'name': 'category',
                    'label': 'Категории',
                    'icon': 'fa fa-tags'
                },
                {
                    'name': 'product',
                    'label': 'Товары',
                    'icon': 'fa fa-box'
                },
                {
                    'name': 'productinfo',
                    'label': 'Информация о товарах',
                    'icon': 'fa fa-info-circle'
                },
                {
                    'name': 'parameter',
                    'label': 'Параметры',
                    'icon': 'fa fa-sliders-h'
                },
                {
                    'name': 'order',
                    'label': 'Заказы',
                    'icon': 'fa fa-shopping-bag'
                },
                {
                    'name': 'orderitem',
                    'label': 'Товары в заказах',
                    'icon': 'fa fa-list'
                },
                {
                    'name': 'contact',
                    'label': 'Контакты',
                    'icon': 'fa fa-address-book'
                },
            )
        },
        {'type': 'title', 'label': 'Система', 'apps': ('authtoken', 'django_celery_beat', 'django_celery_results')},
        {
            'type': 'app',
            'name': 'authtoken',
            'label': 'API Токены',
            'icon': 'fa fa-key',
        },
        {
            'type': 'app',
            'name': 'django_celery_beat',
            'label': 'Celery Beat',
            'icon': 'fa fa-clock',
        },
        {
            'type': 'app',
            'name': 'django_celery_results',
            'label': 'Celery Results',
            'icon': 'fa fa-tasks',
        },
        {'type': 'free', 'label': 'API Документация', 'url': '/api/docs/', 'icon': 'fa fa-book'},
        {'type': 'free', 'label': 'Перейти на сайт', 'url': '/', 'icon': 'fa fa-home'},
    ),

    # Analytics
    'ANALYTICS': {
        'CREDENTIALS': os.path.join(BASE_DIR, 'credentials.json'),
        'VIEW_ID': '12345678',
    }
}

AUTHENTICATION_BACKENDS = [
    'social_core.backends.google.GoogleOAuth2',
    'social_core.backends.github.GithubOAuth2',
    'django.contrib.auth.backends.ModelBackend',
]

# Social Auth
SOCIAL_AUTH_JSONFIELD_ENABLED = True
SOCIAL_AUTH_USER_MODEL = 'backend.User'
SOCIAL_AUTH_LOGIN_REDIRECT_URL = '/api/v1/user/details'
SOCIAL_AUTH_NEW_USER_REDIRECT_URL = '/api/v1/user/details'

# Google OAuth2
SOCIAL_AUTH_GOOGLE_OAUTH2_KEY = os.getenv('GOOGLE_OAUTH2_KEY', '')
SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET = os.getenv('GOOGLE_OAUTH2_SECRET', '')
SOCIAL_AUTH_GOOGLE_OAUTH2_SCOPE = [
    'https://www.googleapis.com/auth/userinfo.email',
    'https://www.googleapis.com/auth/userinfo.profile',
]

# GitHub OAuth2
SOCIAL_AUTH_GITHUB_KEY = os.getenv('GITHUB_KEY', '')
SOCIAL_AUTH_GITHUB_SECRET = os.getenv('GITHUB_SECRET', '')
SOCIAL_AUTH_GITHUB_SCOPE = ['user:email']

# Pipeline для создания пользователей
SOCIAL_AUTH_PIPELINE = (
    'social_core.pipeline.social_auth.social_details',
    'social_core.pipeline.social_auth.social_uid',
    'social_core.pipeline.social_auth.auth_allowed',
    'social_core.pipeline.social_auth.social_user',
    'social_core.pipeline.user.get_username',
    'social_core.pipeline.user.create_user',
    'backend.pipeline.create_user_profile',  # Кастомный pipeline
    'social_core.pipeline.social_auth.associate_user',
    'social_core.pipeline.social_auth.load_extra_data',
    'social_core.pipeline.user.user_details',
)


# Условно добавляем debug_toolbar только в режиме разработки
if DEBUG:
    INSTALLED_APPS.insert(-1, 'debug_toolbar')

MIDDLEWARE = [
    'silk.middleware.SilkyMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'backend.middleware.SentryContextMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# Добавляем debug_toolbar middleware только в режиме разработки
if DEBUG:
    MIDDLEWARE.insert(0, 'debug_toolbar.middleware.DebugToolbarMiddleware')

ROOT_URLCONF = 'ProcurementDjango.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'ProcurementDjango.wsgi.application'

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME', 'diplom_db'),
        'USER': os.getenv('DB_USER', 'diplom_user'),
        'PASSWORD': os.getenv('DB_PASSWORD', 'password'),
        'HOST': os.getenv('DB_HOST', 'db'),
        'PORT': os.getenv('DB_PORT', '5432'),
        'OPTIONS': {
            'connect_timeout': 20,
        },
    }
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'ru-ru'
TIME_ZONE = 'Europe/Moscow'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# ImageKit
IMAGEKIT_DEFAULT_CACHEFILE_BACKEND = 'imagekit.cachefiles.backends.Simple'
IMAGEKIT_CACHEFILE_DIR = 'cache'
IMAGEKIT_PILLOW_DEFAULT_OPTIONS = {
    'quality': 85,
}

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Custom user model
AUTH_USER_MODEL = 'backend.User'

# REST Framework settings
REST_FRAMEWORK = {
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 40,
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
    ],
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.TokenAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticatedOrReadOnly',
    ],
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle'
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '1000/day',
        'user': '10000/day'
    }
}

SPECTACULAR_SETTINGS = {
    'TITLE': 'Procurement API',
    'DESCRIPTION': 'API для платформы заказа товаров для розничных сетей',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,

    # Настройки безопасности
    'SECURITY': [
        {
            'tokenAuth': []
        }
    ],
    'COMPONENT_SPLIT_REQUEST': True,

    # Схемы аутентификации
    'APPEND_COMPONENTS': {
        'securitySchemes': {
            'tokenAuth': {
                'type': 'apiKey',
                'in': 'header',
                'name': 'Authorization',
                'description': 'Token-based authentication. Format: Token <your-token>'
            }
        }
    },

    # Дополнительные настройки
    'SCHEMA_PATH_PREFIX': r'/api/v1',
    'SWAGGER_UI_SETTINGS': {
        'deepLinking': True,
        'persistAuthorization': True,
        'displayOperationId': True,
    },
    'SWAGGER_UI_FAVICON_HREF': '/static/favicon.ico',
}

# Email settings
EMAIL_BACKEND = os.getenv('EMAIL_BACKEND', 'django.core.mail.backends.console.EmailBackend')
EMAIL_HOST = os.getenv('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', '587'))
EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', 'True').lower() in ('true', '1', 't')
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER

# CORS settings - расширены для поддержки VM IP
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "http://10.0.2.15:8000",
    "http://10.0.2.15",
]
CORS_ALLOW_CREDENTIALS = True

# Celery Configuration
# В Docker окружении используем имя сервиса Redis
if os.getenv('DOCKER_ENV'):
    CELERY_BROKER_URL = 'redis://redis:6379/0'
    CELERY_RESULT_BACKEND = 'redis://redis:6379/0'
else:
    # Для локальной разработки используем localhost или переменные окружения
    CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0')
    CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')

CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE

# Security settings для production
if not DEBUG:
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'
    SECURE_SSL_REDIRECT = False  # True если используете HTTPS
    SESSION_COOKIE_SECURE = False  # True если используете HTTPS
    CSRF_COOKIE_SECURE = False  # True если используете HTTPS

# Debug toolbar settings - улучшена поддержка Docker
if DEBUG:
    try:
        import socket
        hostname, _, ips = socket.gethostbyname_ex(socket.gethostname())
        INTERNAL_IPS = [
            '127.0.0.1',
            '10.0.2.15',
        ]
        # Для Docker контейнеров
        INTERNAL_IPS += [ip[:-1] + '1' for ip in ips]
    except:
        INTERNAL_IPS = ['127.0.0.1', '10.0.2.15']

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'django.log',
            'formatter': 'verbose',
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
        'backend': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
        'celery': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# ============================================================
# DJANGO-SILK CONFIGURATION
# ============================================================

# Включить профайлер Python
SILKY_PYTHON_PROFILER = DEBUG
SILKY_PYTHON_PROFILER_BINARY = True
SILKY_PYTHON_PROFILER_RESULT_PATH = BASE_DIR / 'profiles'

# Максимальные размеры
SILKY_MAX_REQUEST_BODY_SIZE = 1024 * 1024  # 1MB
SILKY_MAX_RESPONSE_BODY_SIZE = 1024 * 1024  # 1MB
SILKY_MAX_RECORDED_REQUESTS = 10000

# Аутентификация для Silk UI
SILKY_AUTHENTICATION = True  # Требовать авторизацию
SILKY_AUTHORISATION = True  # Требовать права администратора

# Записывать 100% запросов
SILKY_INTERCEPT_PERCENT = 100
SILKY_META = True


# ============================================================
# REDIS CACHE CONFIGURATION
# ============================================================

# Базовая конфигурация Django Cache (для view caching, sessions)
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/1'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'SOCKET_CONNECT_TIMEOUT': 5,
            'SOCKET_TIMEOUT': 5,
            'COMPRESSOR': 'django_redis.compressors.zlib.ZlibCompressor',
            'CONNECTION_POOL_KWARGS': {
                'max_connections': 50,
                'retry_on_timeout': True,
            },
            'IGNORE_EXCEPTIONS': True,  # Не падать, если Redis недоступен
        },
        'KEY_PREFIX': 'procurement',
        'TIMEOUT': 300,  # Таймаут по умолчанию 5 минут
    }
}

# Конфигурация django-cacheops для автоматического кэширования ORM
CACHEOPS_REDIS = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/1')

# Настройки кэширования для моделей
CACHEOPS = {
    # Кэшировать все запросы к Category на 1 час
    'backend.category': {'ops': 'all', 'timeout': 60 * 60},

    # Кэшировать запросы к Shop на 30 минут
    'backend.shop': {'ops': 'all', 'timeout': 60 * 30},

    # Кэшировать запросы к Product на 15 минут
    'backend.product': {'ops': 'get', 'timeout': 60 * 15},

    # Кэшировать ProductInfo на 10 минут (часто меняется)
    'backend.productinfo': {'ops': ('get', 'fetch'), 'timeout': 60 * 10},

    # Кэшировать параметры на 1 час
    'backend.parameter': {'ops': 'all', 'timeout': 60 * 60},

    # Кэшировать ProductParameter на 15 минут
    'backend.productparameter': {'ops': ('get', 'fetch'), 'timeout': 60 * 15},

    # User - кэшировать только get запросы на 5 минут
    'backend.user': {'ops': 'get', 'timeout': 60 * 5},

    # Contact, Order, OrderItem - НЕ кэшировать (критичные данные)
}

# Дополнительные настройки cacheops
CACHEOPS_DEGRADE_ON_FAILURE = True  # Не падать если Redis недоступен
CACHEOPS_DEFAULTS = {
    'timeout': 60 * 15  # Таймаут по умолчанию 15 минут
}

# Отключить кэширование в DEBUG режиме (опционально)
if DEBUG:
    CACHEOPS_ENABLED = True  # Можно поставить False для отладки
else:
    CACHEOPS_ENABLED = True

# Создаем директорию для логов с обработкой ошибок
try:
    os.makedirs(BASE_DIR / 'logs', exist_ok=True)
except OSError as e:
    print(f"Warning: Could not create logs directory: {e}")