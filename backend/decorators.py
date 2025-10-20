from functools import wraps
from django.core.cache import cache
from rest_framework.response import Response
import hashlib
import json


def cache_api_response(timeout=300):
    """
    Декоратор для кэширования API responses.

    Args:
        timeout: время жизни кэша в секундах (по умолчанию 5 минут)

    Usage:
        @cache_api_response(timeout=60*10)  # 10 минут
        def get(self, request):
            ...
    """

    def decorator(func):
        @wraps(func)
        def wrapper(self, request, *args, **kwargs):
            # Создаем уникальный ключ кэша
            cache_key_data = {
                'path': request.path,
                'method': request.method,
                'query_params': dict(request.query_params),
                'user_id': getattr(request.user, 'id', None),
            }
            cache_key_string = json.dumps(cache_key_data, sort_keys=True)
            cache_key = f"api_response_{hashlib.md5(cache_key_string.encode()).hexdigest()}"

            # Проверяем кэш
            cached_response = cache.get(cache_key)
            if cached_response is not None:
                return Response(cached_response)

            # Если в кэше нет, выполняем запрос
            response = func(self, request, *args, **kwargs)

            # Кэшируем только успешные ответы
            if response.status_code == 200:
                cache.set(cache_key, response.data, timeout)

            return response

        return wrapper

    return decorator
