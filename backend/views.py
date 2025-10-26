from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
from django.db import IntegrityError
from django.db.models import Q, Sum, F
from django.http import JsonResponse
from rest_framework.authtoken.models import Token
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.request import Request
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from requests import get
from ujson import loads as load_json
from yaml import load as load_yaml, Loader
from django.shortcuts import get_object_or_404
from typing import Any

from backend.models import (
    Shop, Category, Product, ProductInfo, Parameter,
    ProductParameter, Order, OrderItem, Contact,
    ConfirmEmailToken, User
)
from backend.serializers import (
    UserSerializer, CategorySerializer, ShopSerializer,
    ProductInfoSerializer, OrderItemSerializer, OrderSerializer,
    ContactSerializer, OrderStatusUpdateSerializer
)
from backend.signals import new_user_registered, new_order
from backend.tasks import send_email_task, import_shop_data_task
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample
from drf_spectacular.types import OpenApiTypes
from django.shortcuts import redirect
from django.contrib.auth import get_user_model
from rest_framework.decorators import api_view
from rest_framework.parsers import MultiPartParser, FormParser
import sentry_sdk
from django.core.cache import cache
from django.views.decorators.cache import cache_page
from django.utils.decorators import method_decorator
from backend.decorators import cache_api_response
from silk.profiling.profiler import silk_profile
from django_redis import get_redis_connection
from django.utils import timezone
from rest_framework.permissions import AllowAny


class HealthCheckView(APIView):
    """
    Endpoint для проверки здоровья приложения (healthcheck).
    Используется Docker для определения статуса контейнера.
    """
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        return Response(
            {
                "status": "healthy",
                "message": "Application is running",
                "timestamp": str(timezone.now())
            },
            status=status.HTTP_200_OK
        )


class SentryTestView(APIView):
    """
    APIView для тестирования интеграции Sentry.
    Вызывает различные типы исключений для проверки их отлавливания в Sentry.
    """

    @extend_schema(
        summary="Тестирование Sentry - деление на ноль",
        description="Вызывает ZeroDivisionError для проверки отлова ошибок в Sentry",
        responses={
            500: {
                "description": "Internal Server Error - ошибка будет отправлена в Sentry"
            }
        },
        tags=['Testing']
    )
    def get(self, request, *args, **kwargs):
        """
        Тестовый endpoint для проверки Sentry.
        Вызывает исключение деления на ноль.
        """
        # Добавляем контекст для Sentry
        with sentry_sdk.configure_scope() as scope:
            scope.set_tag("test_type", "division_by_zero")
            scope.set_context("request_info", {
                "method": request.method,
                "path": request.path,
                "user_email": getattr(request.user, 'email', 'Anonymous'),
            })

        # Вызываем исключение
        division_by_zero = 1 / 0

        return Response({"message": "This will never be reached"})

    @extend_schema(
        summary="Тестирование Sentry - KeyError",
        description="Вызывает KeyError для проверки отлова ошибок в Sentry",
        responses={
            500: {
                "description": "Internal Server Error - ошибка будет отправлена в Sentry"
            }
        },
        tags=['Testing']
    )
    def post(self, request, *args, **kwargs):
        """
        Тестовый endpoint для проверки Sentry.
        Вызывает KeyError при обращении к несуществующему ключу.
        """
        with sentry_sdk.configure_scope() as scope:
            scope.set_tag("test_type", "key_error")
            scope.set_user({
                "id": getattr(request.user, 'id', None),
                "email": getattr(request.user, 'email', None),
            })

        # Вызываем KeyError
        test_dict = {"key1": "value1"}
        value = test_dict["nonexistent_key"]

        return Response({"message": "This will never be reached"})

    @extend_schema(
        summary="Тестирование Sentry - Custom Exception",
        description="Вызывает пользовательское исключение с дополнительным контекстом",
        responses={
            500: {
                "description": "Internal Server Error - ошибка будет отправлена в Sentry"
            }
        },
        tags=['Testing']
    )
    def put(self, request, *args, **kwargs):
        """
        Тестовый endpoint с пользовательским исключением и расширенным контекстом.
        """
        with sentry_sdk.configure_scope() as scope:
            scope.set_tag("test_type", "custom_exception")
            scope.set_context("custom_data", {
                "request_data": request.data,
                "query_params": dict(request.query_params),
                "headers": dict(request.headers),
            })
            scope.set_level("error")

        # Отправляем пользовательское сообщение в Sentry
        sentry_sdk.capture_message(
            "Custom test message from Sentry integration",
            level="info"
        )

        # Вызываем пользовательское исключение
        raise ValueError("This is a custom test exception for Sentry")


class UploadAvatarView(APIView):
    """
    Загрузка аватара пользователя
    """
    permission_classes = [IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser)

    @extend_schema(
        summary="Загрузить аватар",
        description="Загрузить изображение профиля пользователя",
        request={
            'multipart/form-data': {
                'type': 'object',
                'properties': {
                    'avatar': {
                        'type': 'string',
                        'format': 'binary'
                    }
                }
            }
        },
        responses={200: UserSerializer},
        tags=['Пользователи']
    )
    def post(self, request, *args, **kwargs):
        """Загрузить аватар"""
        if 'avatar' not in request.FILES:
            return Response({
                'Status': False,
                'Error': 'Файл не был загружен'
            }, status=status.HTTP_400_BAD_REQUEST)

        avatar = request.FILES['avatar']

        # Проверка размера файла (макс. 5MB)
        if avatar.size > 5 * 1024 * 1024:
            return Response({
                'Status': False,
                'Error': 'Файл слишком большой (макс. 5MB)'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Проверка типа файла
        allowed_types = ['image/jpeg', 'image/png', 'image/jpg']
        if avatar.content_type not in allowed_types:
            return Response({
                'Status': False,
                'Error': 'Неподдерживаемый формат файла'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Сохраняем аватар
        request.user.avatar = avatar
        request.user.save()

        serializer = UserSerializer(request.user, context={'request': request})
        return Response({
            'Status': True,
            'data': serializer.data
        }, status=status.HTTP_200_OK)


class UploadProductImageView(APIView):
    """
    Загрузка изображения товара
    """
    permission_classes = [IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser)

    @extend_schema(
        summary="Загрузить изображение товара",
        description="Загрузить изображение для товара (только для поставщиков)",
        request={
            'multipart/form-data': {
                'type': 'object',
                'properties': {
                    'product_info_id': {'type': 'integer'},
                    'image': {'type': 'string', 'format': 'binary'}
                }
            }
        },
        tags=['Поставщик']
    )
    def post(self, request, *args, **kwargs):
        """Загрузить изображение товара"""
        if request.user.type != 'shop':
            return Response({
                'Status': False,
                'Error': 'Только для магазинов'
            }, status=status.HTTP_403_FORBIDDEN)

        product_info_id = request.data.get('product_info_id')
        if not product_info_id:
            return Response({
                'Status': False,
                'Error': 'Не указан product_info_id'
            }, status=status.HTTP_400_BAD_REQUEST)

        if 'image' not in request.FILES:
            return Response({
                'Status': False,
                'Error': 'Файл не был загружен'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            product_info = ProductInfo.objects.get(
                id=product_info_id,
                shop__user=request.user
            )
        except ProductInfo.DoesNotExist:
            return Response({
                'Status': False,
                'Error': 'Товар не найден'
            }, status=status.HTTP_404_NOT_FOUND)

        image = request.FILES['image']

        # Проверка размера (макс. 10MB)
        if image.size > 10 * 1024 * 1024:
            return Response({
                'Status': False,
                'Error': 'Файл слишком большой (макс. 10MB)'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Сохраняем изображение
        product_info.image = image
        product_info.save()

        serializer = ProductInfoSerializer(product_info, context={'request': request})
        return Response({
            'Status': True,
            'data': serializer.data
        }, status=status.HTTP_200_OK)


class RegisterAccount(APIView):
    """
    Регистрация новых пользователей
    Создание нового аккаунта покупателя или поставщика.
    После регистрации магазина автоматически создается объект Shop.
    """

    permission_classes = [AllowAny]

    @extend_schema(
        summary="Регистрация пользователя",
        description="""
            Регистрирует нового пользователя в системе.

            **Типы пользователей:**
            - `buyer` - покупатель (по умолчанию)
            - `shop` - поставщик (автоматически создается магазин)

            После успешной регистрации на email отправляется письмо с подтверждением.
            """,
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'first_name': {'type': 'string', 'example': 'Иван'},
                    'last_name': {'type': 'string', 'example': 'Петров'},
                    'email': {'type': 'string', 'format': 'email', 'example': 'ivan@example.com'},
                    'password': {'type': 'string', 'format': 'password', 'example': 'SecurePass123!'},
                    'company': {'type': 'string', 'example': 'ООО Рога и Копыта'},
                    'position': {'type': 'string', 'example': 'Менеджер'},
                    'type': {'type': 'string', 'enum': ['buyer', 'shop'], 'default': 'buyer'}
                },
                'required': ['first_name', 'last_name', 'email', 'password', 'company', 'position']
            }
        },
        responses={
            201: {
                'description': 'Пользователь успешно создан',
                'content': {
                    'application/json': {
                        'example': {'Status': True}
                    }
                }
            },
            400: {
                'description': 'Ошибка валидации данных',
                'content': {
                    'application/json': {
                        'example': {
                            'Status': False,
                            'Errors': 'Не указаны все необходимые аргументы'
                        }
                    }
                }
            }
        },
        tags=['Пользователи']
    )
    def post(self, request, *args, **kwargs):
        """Регистрация нового пользователя"""

        # Проверяем обязательные поля
        required_fields = {'first_name', 'last_name', 'email', 'password', 'company', 'position'}
        if not required_fields.issubset(request.data.keys()):
            return Response({
                'Status': False,
                'Errors': 'Не указаны все необходимые аргументы'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Проверяем пароль на сложность
        try:
            validate_password(request.data['password'])
        except ValidationError as password_error:
            return Response({
                'Status': False,
                'Errors': {'password': password_error.messages}
            }, status=status.HTTP_400_BAD_REQUEST)

        # Создаем пользователя
        user_serializer = UserSerializer(data=request.data)
        if user_serializer.is_valid():
            user = user_serializer.save()
            user.set_password(request.data['password'])
            user.save()

            # Если тип пользователя — shop, создаём магазин
            if request.data.get('type') == 'shop':
                Shop.objects.get_or_create(
                    user=user,
                    defaults={'name': request.data.get('company', user.company), 'state': True}
                )

            new_user_registered.send(sender=self.__class__, user_id=user.id)
            return Response({'Status': True}, status=status.HTTP_201_CREATED)
        else:
            return Response({
                'Status': False,
                'Errors': user_serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)


class ConfirmAccount(APIView):
    """
    Подтверждение email адреса
    """

    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        """Подтверждение email по токену"""

        if {'email', 'token'}.issubset(request.data.keys()):
            token = ConfirmEmailToken.objects.filter(
                user__email=request.data['email'],
                key=request.data['token']
            ).first()

            if token:
                token.user.is_active = True
                token.user.save()
                token.delete()
                return Response({'Status': True}, status=status.HTTP_200_OK)
            else:
                return Response({
                    'Status': False,
                    'Errors': 'Неправильно указан токен или email'
                }, status=status.HTTP_400_BAD_REQUEST)

        return Response({
            'Status': False,
            'Errors': 'Не указаны все необходимые аргументы'
        }, status=status.HTTP_400_BAD_REQUEST)


class AccountDetails(APIView):
    """
    Управление данными пользователя
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        """Получить данные пользователя"""

        serializer = UserSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        """Обновить данные пользователя"""

        # Если передан пароль, проверяем его
        if 'password' in request.data:
            try:
                validate_password(request.data['password'])
            except ValidationError as password_error:
                return Response({
                    'Status': False,
                    'Errors': {'password': password_error.messages}
                }, status=status.HTTP_400_BAD_REQUEST)
            else:
                request.user.set_password(request.data['password'])

        # Обновляем остальные данные
        user_serializer = UserSerializer(request.user, data=request.data, partial=True)
        if user_serializer.is_valid():
            user_serializer.save()
            return Response({'Status': True}, status=status.HTTP_200_OK)
        else:
            return Response({
                'Status': False,
                'Errors': user_serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)


class LoginAccount(APIView):
    """
    Авторизация пользователей
    """

    permission_classes = [AllowAny]

    @extend_schema(
        summary="Авторизация",
        description="Авторизация пользователя по email и паролю. Возвращает токен для API.",
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'email': {'type': 'string', 'format': 'email'},
                    'password': {'type': 'string', 'format': 'password'}
                },
                'required': ['email', 'password'],
                'example': {
                    'email': 'user@example.com',
                    'password': 'mypassword123'
                }
            }
        },
        responses={
            200: {
                'description': 'Успешная авторизация',
                'content': {
                    'application/json': {
                        'example': {
                            'Status': True,
                            'Token': 'a1b2c3d4e5f6g7h8i9j0'
                        }
                    }
                }
            },
            401: {
                'description': 'Неверные учетные данные'
            }
        },
        tags=['Пользователи']
    )
    def post(self, request, *args, **kwargs):
        """Авторизация пользователя"""

        if {'email', 'password'}.issubset(request.data.keys()):
            user = authenticate(
                request,
                username=request.data['email'],
                password=request.data['password']
            )

            if user is not None:
                if user.is_active:
                    token, _ = Token.objects.get_or_create(user=user)
                    return Response({
                        'Status': True,
                        'Token': token.key
                    }, status=status.HTTP_200_OK)

            return Response({
                'Status': False,
                'Errors': 'Не удалось авторизовать'
            }, status=status.HTTP_401_UNAUTHORIZED)

        return Response({
            'Status': False,
            'Errors': 'Не указаны все необходимые аргументы'
        }, status=status.HTTP_400_BAD_REQUEST)


class CategoryView(ListAPIView):
    """
    Просмотр категорий товаров
    Возвращает список всех доступных категорий товаров.
    Результаты кэшируются на 1 час (автоматически через cacheops).
    """
    queryset = Category.objects.all()
    serializer_class = CategorySerializer

    @method_decorator(cache_page(60 * 60))  # Дополнительное кэширование на 1 час
    @extend_schema(
        summary="Список категорий",
        description='Получение списка всех категорий. Результаты кэшируются.',
        responses={200: CategorySerializer(many=True)},
        tags=['Каталог']
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class ShopView(ListAPIView):
    """
    Просмотр списка активных магазинов
    Результаты кэшируются на 30 минут.
    """
    queryset = Shop.objects.filter(state=True)
    serializer_class = ShopSerializer

    @method_decorator(cache_page(60 * 30))
    @extend_schema(
        summary='Список магазинов',
        responses={200: ShopSerializer(many=True)},
        tags=['Каталог']
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class ProductInfoView(APIView):
    """
    Поиск товаров с фильтрацией
    Использует автоматическое кэширование через cacheops.
    """

    @silk_profile(name='ProductInfo List')
    @cache_api_response(timeout=60 * 10)  # Кэш на 10 минут
    @extend_schema(
        summary="Список товаров",
        description="""
            Получить список товаров с возможностью фильтрации.
            Результаты кэшируются.
            **Параметры фильтрации:**
            - `shop_id` - ID магазина
            - `category_id` - ID категории
            """,
        parameters=[
            OpenApiParameter(
                name='shop_id',
                type=OpenApiTypes.INT,
                location='query',
                description='ID магазина для фильтрации',
                required=False
            ),
            OpenApiParameter(
                name='category_id',
                type=OpenApiTypes.INT,
                location='query',
                description='ID категории для фильтрации',
                required=False
            ),
        ],
        responses={200: ProductInfoSerializer(many=True)},
        tags=['Каталог']
    )
    def get(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """
        Получить список товаров с фильтрацией.

        Параметры запроса:
            shop_id (int, optional): ID магазина для фильтрации
            category_id (int, optional): ID категории для фильтрации

        Возвращает:
            Response: Список товаров с информацией о магазинах и категориях
        """
        shop_id = request.query_params.get('shop_id')
        category_id = request.query_params.get('category_id')

        try:
            # Добавляем хлебные крошки для отслеживания
            sentry_sdk.add_breadcrumb(
                category='query',
                message='Fetching product info',
                level='info',
                data={
                    'shop_id': shop_id,
                    'category_id': category_id
                }
            )

            # Строим базовый запрос
            query = Q(shop__state=True)

            # Применяем фильтры, если они предоставлены
            if shop_id:
                try:
                    shop_id_int = int(shop_id)
                    query &= Q(shop__id=shop_id_int)
                    sentry_sdk.add_breadcrumb(
                        category='filter',
                        message=f'Filtering by shop_id: {shop_id_int}',
                        level='debug'
                    )
                except (ValueError, TypeError) as e:
                    sentry_sdk.capture_exception(e)
                    return Response(
                        {'error': 'shop_id должен быть числом'},
                        status=status.HTTP_400_BAD_REQUEST
                    )

            if category_id:
                try:
                    category_id_int = int(category_id)
                    query &= Q(product__category__id=category_id_int)
                    sentry_sdk.add_breadcrumb(
                        category='filter',
                        message=f'Filtering by category_id: {category_id_int}',
                        level='debug'
                    )
                except (ValueError, TypeError) as e:
                    sentry_sdk.capture_exception(e)
                    return Response(
                        {'error': 'category_id должен быть числом'},
                        status=status.HTTP_400_BAD_REQUEST
                    )

            # Выполняем запрос к БД
            try:
                queryset = (
                    ProductInfo.objects
                    .filter(query)
                    .select_related('shop', 'product__category')
                    .prefetch_related('product_parameters__parameter')
                    .distinct()
                )

                serializer = ProductInfoSerializer(
                    queryset,
                    many=True,
                    context={'request': request}  # Добавляем контекст для построения полных URL
                )

                return Response(serializer.data, status=status.HTTP_200_OK)

            except Exception as db_error:
                sentry_sdk.capture_exception(db_error)
                return Response(
                    {'error': 'Ошибка при получении данных из базы'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

        except Exception as e:
            # Логируем непредвиденные ошибки
            sentry_sdk.capture_exception(e)
            return Response(
                {'error': 'Внутренняя ошибка сервера'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class BasketView(APIView):
    """
    Управление корзиной пользователя
    """
    permission_classes = [IsAuthenticated]

    @silk_profile(name='Basket Get')
    @extend_schema(
        summary="Получить корзину",
        description="Возвращает текущее содержимое корзины пользователя",
        responses={200: OrderSerializer(many=True)},
        tags=['Корзина и заказы']
    )
    def get(self, request, *args, **kwargs):
        """Получить содержимое корзины"""

        basket = Order.objects.filter(
            user_id=request.user.id,
            state='basket'
        ).prefetch_related(
            'ordered_items__product_info__product__category',
            'ordered_items__product_info__product_parameters__parameter'
        ).annotate(
            total=Sum(F('ordered_items__quantity') * F('ordered_items__product_info__price'))
        ).distinct()

        serializer = OrderSerializer(basket, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Добавить товары в корзину",
        description="""
            Добавить один или несколько товаров в корзину.

            Формат данных:
            ```
            {
                "items": "[{\"product_info\": 1, \"quantity\": 2}]"
            }
            ```
            """,
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'items': {
                        'type': 'string',
                        'description': 'JSON-строка с массивом товаров',
                        'example': '[{"product_info": 1, "quantity": 2}]'
                    }
                }
            }
        },
        responses={
            201: {
                'description': 'Товары добавлены',
                'content': {
                    'application/json': {
                        'example': {
                            'Status': True,
                            'Создано объектов': 1
                        }
                    }
                }
            }
        },
        tags=['Корзина и заказы']
    )
    def post(self, request, *args, **kwargs):
        """Добавить товары в корзину"""

        items_string = request.data.get('items')
        if items_string:
            try:
                items_dict = load_json(items_string)
            except ValueError:
                return Response({
                    'Status': False,
                    'Errors': 'Неверный формат запроса'
                }, status=status.HTTP_400_BAD_REQUEST)
            else:
                basket, _ = Order.objects.get_or_create(
                    user_id=request.user.id,
                    state='basket'
                )
                objects_created = 0

                for order_item in items_dict:
                    order_item.update({'order': basket.id})
                    serializer = OrderItemSerializer(data=order_item)

                    if serializer.is_valid():
                        try:
                            serializer.save()
                        except IntegrityError as error:
                            return Response({
                                'Status': False,
                                'Errors': str(error)
                            }, status=status.HTTP_400_BAD_REQUEST)
                        else:
                            objects_created += 1
                    else:
                        return Response({
                            'Status': False,
                            'Errors': serializer.errors
                        }, status=status.HTTP_400_BAD_REQUEST)

                return Response({
                    'Status': True,
                    'Создано объектов': objects_created
                }, status=status.HTTP_201_CREATED)

        return Response({
            'Status': False,
            'Errors': 'Не указаны все необходимые аргументы'
        }, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        summary="Обновить количество",
        description="Изменить количество товаров в корзине",
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'items': {
                        'type': 'string',
                        'example': '[{"id": 1, "quantity": 5}]'
                    }
                }
            }
        },
        tags=['Корзина и заказы']
    )
    def put(self, request, *args, **kwargs):
        """Обновить количество товаров в корзине"""

        items_string = request.data.get('items')
        if items_string:
            try:
                items_dict = load_json(items_string)
            except ValueError:
                return Response({
                    'Status': False,
                    'Errors': 'Неверный формат запроса'
                }, status=status.HTTP_400_BAD_REQUEST)
            else:
                basket, _ = Order.objects.get_or_create(
                    user_id=request.user.id,
                    state='basket'
                )
                objects_updated = 0

                for order_item in items_dict:
                    if (isinstance(order_item.get('id'), int) and
                            isinstance(order_item.get('quantity'), int)):
                        objects_updated += OrderItem.objects.filter(
                            order_id=basket.id,
                            id=order_item['id']
                        ).update(quantity=order_item['quantity'])

                return Response({
                    'Status': True,
                    'Обновлено объектов': objects_updated
                }, status=status.HTTP_200_OK)

        return Response({
            'Status': False,
            'Errors': 'Не указаны все необходимые аргументы'
        }, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        summary="Удалить товары",
        description="Удалить товары из корзины",
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'items': {
                        'type': 'string',
                        'example': '1,2,3'
                    }
                }
            }
        },
        tags=['Корзина и заказы']
    )
    def delete(self, request, *args, **kwargs):
        """Удалить товары из корзины"""

        items_string = request.data.get('items')
        if items_string:
            items_list = items_string.split(',')
            basket, _ = Order.objects.get_or_create(
                user_id=request.user.id,
                state='basket'
            )
            query = Q()
            objects_deleted = False

            for order_item_id in items_list:
                if order_item_id.isdigit():
                    query = query | Q(order_id=basket.id, id=order_item_id)
                    objects_deleted = True

            if objects_deleted:
                deleted_count = OrderItem.objects.filter(query).delete()[0]
                return Response({
                    'Status': True,
                    'Удалено объектов': deleted_count
                }, status=status.HTTP_200_OK)

        return Response({
            'Status': False,
            'Errors': 'Не указаны все необходимые аргументы'
        }, status=status.HTTP_400_BAD_REQUEST)


class ContactView(APIView):
    """
    Управление контактной информацией
    """

    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Список контактов",
        description="Получить список контактов пользователя",
        responses={200: ContactSerializer(many=True)},
        tags=['Контакты']
    )
    def get(self, request, *args, **kwargs):
        """Получить контакты пользователя"""

        contact = Contact.objects.filter(user_id=request.user.id)
        serializer = ContactSerializer(contact, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Создать контакт",
        description="Добавить новый адрес доставки",
        request=ContactSerializer,
        responses={201: {'Status': True}},
        tags=['Контакты']
    )
    def post(self, request, *args, **kwargs):
        """Создать новый контакт"""

        if {'city', 'street', 'phone'}.issubset(request.data.keys()):
            # Создаем изменяемую копию данных
            data = request.data.copy()
            data['user'] = request.user.id
            serializer = ContactSerializer(data=data)

            if serializer.is_valid():
                serializer.save()
                return Response({'Status': True}, status=status.HTTP_201_CREATED)
            else:
                return Response({
                    'Status': False,
                    'Errors': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)

        return Response({
            'Status': False,
            'Errors': 'Не указаны все необходимые аргументы'
        }, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, *args, **kwargs):
        """Обновить контакт"""
        if 'id' in request.data:
            if str(request.data['id']).isdigit():
                contact = Contact.objects.filter(
                    id=request.data['id'],
                    user_id=request.user.id
                ).first()

                if contact:
                    serializer = ContactSerializer(
                        contact,
                        data=request.data,
                        partial=True
                    )
                    if serializer.is_valid():
                        serializer.save()
                        return Response({'Status': True}, status=status.HTTP_200_OK)
                    else:
                        return Response({
                            'Status': False,
                            'Errors': serializer.errors
                        }, status=status.HTTP_400_BAD_REQUEST)

        return Response({
            'Status': False,
            'Errors': 'Не указаны все необходимые аргументы'
        }, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, *args, **kwargs):
        """Удалить контакты"""

        items_string = request.data.get('items')
        if items_string:
            items_list = items_string.split(',')
            query = Q()
            objects_deleted = False

            for contact_id in items_list:
                if contact_id.isdigit():
                    query = query | Q(user_id=request.user.id, id=contact_id)
                    objects_deleted = True

            if objects_deleted:
                deleted_count = Contact.objects.filter(query).delete()[0]
                return Response({
                    'Status': True,
                    'Удалено объектов': deleted_count
                }, status=status.HTTP_200_OK)

        return Response({
            'Status': False,
            'Errors': 'Не указаны все необходимые аргументы'
        }, status=status.HTTP_400_BAD_REQUEST)


class OrderView(APIView):
    """
    Управление заказами пользователей
    """

    permission_classes = [IsAuthenticated]

    @silk_profile(name='Order List')
    def get(self, request, *args, **kwargs):
        """Получить заказы пользователя"""

        order = Order.objects.filter(
            user_id=request.user.id,
        ).exclude(state='basket').prefetch_related(
            'ordered_items__product_info__product__category',
            'ordered_items__product_info__product_parameters__parameter'
        ).select_related('contact').annotate(
            total=Sum(F('ordered_items__quantity') * F('ordered_items__product_info__price'))
        ).distinct()

        serializer = OrderSerializer(order, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        """Создать заказ из корзины"""

        if {'id', 'contact'}.issubset(request.data.keys()):
            if str(request.data['id']).isdigit():
                try:
                    is_updated = Order.objects.filter(
                        user_id=request.user.id,
                        id=request.data['id'],
                    ).update(
                        contact_id=request.data['contact'],
                        state='new'
                    )
                except IntegrityError:
                    return Response({
                        'Status': False,
                        'Errors': 'Неправильно указаны аргументы'
                    }, status=status.HTTP_400_BAD_REQUEST)
                else:
                    if is_updated:
                        new_order.send(sender=self.__class__, user_id=request.user.id, order_id=request.data['id'])
                        return Response({'Status': True}, status=status.HTTP_201_CREATED)

        return Response({
            'Status': False,
            'Errors': 'Не указаны все необходимые аргументы'
        }, status=status.HTTP_400_BAD_REQUEST)


# Представления для поставщиков

class PartnerUpdate(APIView):
    """
    Обновление прайс-листа поставщиком
    """

    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Загрузить прайс-лист",
        description="""
            Загружает товары из YAML-файла по URL.

            Формат YAML:
            ```
            shop: Название магазина
            categories:
              - id: 1
                name: Категория
            goods:
              - id: 1
                category: 1
                model: Модель
                name: Название
                price: 1000
                price_rrc: 1200
                quantity: 10
                parameters:
                  Параметр: Значение
            ```
            """,
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'url': {
                        'type': 'string',
                        'format': 'uri',
                        'example': 'https://example.com/price.yaml'
                    }
                },
                'required': ['url']
            }
        },
        responses={
            202: {
                'description': 'Задача принята в обработку',
                'content': {
                    'application/json': {
                        'example': {
                            'Status': True,
                            'task_id': 'abc123'
                        }
                    }
                }
            }
        },
        tags=['Поставщик']
    )
    def post(self, request, *args, **kwargs):
        """Обновить прайс-лист"""

        if request.user.type != 'shop':
            return Response({
                'Status': False,
                'Error': 'Только для магазинов'
            }, status=status.HTTP_403_FORBIDDEN)

        url = request.data.get('url')
        if url:
            validate_url = URLValidator()
            try:
                validate_url(url)
            except ValidationError as e:
                return Response({
                    'Status': False,
                    'Error': str(e)
                }, status=status.HTTP_400_BAD_REQUEST)
            else:
                # Запускаем асинхронную задачу импорта
                task = import_shop_data_task.delay(url, request.user.id)
                return Response({
                    'Status': True,
                    'task_id': task.id
                }, status=status.HTTP_202_ACCEPTED)

        return Response({
            'Status': False,
            'Errors': 'Не указаны все необходимые аргументы'
        }, status=status.HTTP_400_BAD_REQUEST)


class PartnerState(APIView):
    """
    Управление статусом поставщика
    """

    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Получить статус магазина",
        description="Возвращает текущий статус (включен/выключен) магазина поставщика",
        responses={200: ShopSerializer},
        tags=['Поставщик']
    )
    def get(self, request, *args, **kwargs):
        """Получить статус поставщика"""

        if request.user.type != 'shop':
            return Response({
                'Status': False,
                'Error': 'Только для магазинов'
            }, status=status.HTTP_403_FORBIDDEN)

        shop = request.user.shop
        serializer = ShopSerializer(shop)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Изменить статус магазина",
        description="""
            Включить или выключить магазин.

            Принимает строковое значение: "true", "false", "1", "0", "yes", "no"
            """,
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'state': {
                        'type': 'string',
                        'enum': ['true', 'false', '1', '0', 'yes', 'no'],
                        'example': 'true'
                    }
                }
            }
        },
        responses={200: {'Status': True}},
        tags=['Поставщик']
    )
    def post(self, request, *args, **kwargs):
        """Изменить статус поставщика"""

        if request.user.type != 'shop':
            return Response({
                'Status': False,
                'Error': 'Только для магазинов'
            }, status=status.HTTP_403_FORBIDDEN)

        def strtobool(val):
            val = str(val).lower()
            if val in ("y", "yes", "t", "true", "on", "1"):
                return True
            elif val in ("n", "no", "f", "false", "off", "0"):
                return False
            else:
                raise ValueError(f"invalid truth value {val}")

        state = request.data.get('state')
        if state:
            try:
                Shop.objects.filter(
                    user_id=request.user.id
                ).update(state=strtobool(state))
                return Response({'Status': True}, status=status.HTTP_200_OK)
            except ValueError as error:
                return Response({
                    'Status': False,
                    'Errors': str(error)
                }, status=status.HTTP_400_BAD_REQUEST)

        return Response({
            'Status': False,
            'Errors': 'Не указаны все необходимые аргументы'
        }, status=status.HTTP_400_BAD_REQUEST)


class PartnerOrders(APIView):
    """
    Заказы поставщика
    """

    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Заказы с товарами магазина",
        description="Возвращает все заказы покупателей, содержащие товары данного магазина",
        responses={200: OrderSerializer(many=True)},
        tags=['Поставщик']
    )
    def get(self, request, *args, **kwargs):
        """Получить заказы поставщика"""

        if request.user.type != 'shop':
            return Response({
                'Status': False,
                'Error': 'Только для магазинов'
            }, status=status.HTTP_403_FORBIDDEN)

        # Получаем объект магазина текущего пользователя
        try:
            shop = request.user.shop
        except Shop.DoesNotExist:
            return Response({
                'Status': False,
                'Error': 'Магазин не найден'
            }, status=status.HTTP_404_NOT_FOUND)

        # Фильтруем заказы клиентов, где есть товары этого магазина
        orders = (Order.objects
            .filter(ordered_items__product_info__shop=shop)
            .exclude(state='basket')
            .prefetch_related(
                'ordered_items__product_info__product__category',
                'ordered_items__product_info__product_parameters__parameter'
            )
            .select_related('contact')
            .annotate(
                calculated_total=Sum(
                    F('ordered_items__quantity') *
                    F('ordered_items__product_info__price')
                )
            )
            .distinct()
        )

        serializer = OrderSerializer(orders, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

User = get_user_model()
@api_view(['GET'])
def social_auth_complete(request):
    """
    Callback после успешной авторизации через социальную сеть.
    Возвращает токен пользователя.
    """
    user = request.user
    if user.is_authenticated:
        token, _ = Token.objects.get_or_create(user=user)
        return Response({
            'Status': True,
            'Token': token.key,
            'user': {
                'id': user.id,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
            }
        })
    return Response(
        {'Status': False, 'Error': 'Not authenticated'},
        status=401
    )



class OrderStatusUpdateView(APIView):
    """
    Обновление статуса заказа (для админки)
    """

    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        """Обновить статус заказа"""

        if not request.user.is_staff:
            return Response({
                'Status': False,
                'Error': 'Недостаточно прав'
            }, status=status.HTTP_403_FORBIDDEN)

        order_id = request.data.get('order_id')
        new_state = request.data.get('state')

        if order_id and new_state:
            try:
                order = get_object_or_404(Order, id=order_id)
                old_state = order.state
                order.state = new_state
                order.save()

                # Отправляем уведомление о смене статуса
                send_email_task.delay(
                    'order_status_changed',
                    order.user.email,
                    {
                        'order_id': order.id,
                        'old_state': old_state,
                        'new_state': new_state
                    }
                )

                return Response({'Status': True}, status=status.HTTP_200_OK)
            except Exception as e:
                return Response({
                    'Status': False,
                    'Error': str(e)
                }, status=status.HTTP_400_BAD_REQUEST)

        return Response({
            'Status': False,
            'Errors': 'Не указаны все необходимые аргументы'
        }, status=status.HTTP_400_BAD_REQUEST)


class CacheStatsView(APIView):
    """
    View для отображения статистики кэширования.
    Доступен только администраторам.
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Статистика кэша",
        description="Получить статистику использования кэша Redis",
        tags=['Мониторинг']
    )
    def get(self, request):
        if not request.user.is_staff:
            return Response(
                {'Error': 'Доступно только администраторам'},
                status=status.HTTP_403_FORBIDDEN
            )

        from backend.cache_utils import get_cache_stats

        try:
            # Получаем клиент Redis
            redis_client = get_redis_connection("default")
            redis_info = redis_client.info()

            stats = get_cache_stats()
            stats['redis_info'] = {
                'used_memory_human': redis_info.get('used_memory_human'),
                'connected_clients': redis_info.get('connected_clients'),
                'total_commands_processed': redis_info.get('total_commands_processed'),
                'keyspace_hits': redis_info.get('keyspace_hits', 0),
                'keyspace_misses': redis_info.get('keyspace_misses', 0),
            }

            return Response(stats, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {'Error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
