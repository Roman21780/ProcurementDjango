import sentry_sdk
from django.utils.deprecation import MiddlewareMixin
from django.http import HttpRequest
from typing import Any, Optional, Dict


class SentryContextMiddleware(MiddlewareMixin):
    """
    Middleware для добавления дополнительного контекста в Sentry
    """

    def process_request(self, request: HttpRequest) -> None:
        """Добавляем информацию о запросе в Sentry"""
        try:
            if hasattr(request, 'user') and hasattr(request.user, 'is_authenticated') and request.user.is_authenticated:
                with sentry_sdk.configure_scope() as scope:
                    user_data: Dict[str, Any] = {
                        'id': getattr(request.user, 'id', None),
                        'email': getattr(request.user, 'email', None),
                        'username': getattr(request.user, 'email', None),
                    }
                    if hasattr(request.user, 'type'):
                        user_data['type'] = request.user.type
                        scope.set_tag('user_type', request.user.type)

                    scope.user = user_data

            # Добавляем информацию о запросе
            with sentry_sdk.configure_scope() as scope:
                scope.set_tag('request_method', request.method)
                scope.set_tag('request_path', request.path)

                # Добавляем IP адрес
                x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
                ip = x_forwarded_for.split(',')[0] if x_forwarded_for else request.META.get('REMOTE_ADDR')
                if ip:
                    scope.set_tag('ip_address', ip)

        except Exception as e:
            sentry_sdk.capture_exception(e)

        return None

    def process_exception(self, request: HttpRequest, exception: Exception) -> None:
        """Добавляем дополнительный контекст при возникновении исключения"""
        try:
            with sentry_sdk.configure_scope() as scope:
                scope.set_context('request_data', {
                    'method': request.method,
                    'path': request.path,
                    'query_params': dict(request.GET),
                    'user_agent': request.META.get('HTTP_USER_AGENT', ''),
                })
                sentry_sdk.capture_exception(exception)
        except Exception as e:
            # В случае ошибки при логировании, логируем её в Sentry
            sentry_sdk.capture_exception(e)