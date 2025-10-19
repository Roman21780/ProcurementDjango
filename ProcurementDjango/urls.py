"""
URL configuration for ProcurementDjango project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView
)
from backend.views import social_auth_complete
from baton.autodiscover import admin as baton_admin

def api_root(request):
    """Корневая страница API"""
    return JsonResponse({
        'message': 'Добро пожаловать в API системы закупок',
        'version': '1.0',
        'endpoints': {
            'admin': '/admin/',
            'api': '/api/v1/',
            'user_register': '/api/v1/user/register/',
            'user_login': '/api/v1/user/login/',
            'products': '/api/v1/products/',
            'categories': '/api/v1/categories/',
        }
    })

urlpatterns = [
    path('', api_root, name='api-root'),
    path('auth/', include('social_django.urls', namespace='social')),
    path('auth/complete/', social_auth_complete, name='social-auth-complete'),
    path('admin/', admin.site.urls),
    path('baton/', include('baton.urls')),
    path('api/v1/', include('backend.urls', namespace='backend')),

    # OpenAPI схема и документация
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]

# Условно добавляем debug toolbar только в режиме разработки
if settings.DEBUG:
    import debug_toolbar
    urlpatterns.append(path('__debug__/', include(debug_toolbar.urls)))

# Добавляем обработку медиа файлов в режиме разработки
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
