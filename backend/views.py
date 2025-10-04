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
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from requests import get
from ujson import loads as load_json
from yaml import load as load_yaml, Loader
from django.shortcuts import get_object_or_404

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
from backend.signals import new_user_registered_signal, new_order_signal
from backend.tasks import send_email_task, import_shop_data_task


class RegisterAccount(APIView):
    """
    Регистрация новых пользователей
    """

    def post(self, request, *args, **kwargs):
        """Регистрация нового пользователя"""

        # Проверяем обязательные поля
        required_fields = {'first_name', 'last_name', 'email', 'password', 'company', 'position'}
        if not required_fields.issubset(request.data.keys()):
            return JsonResponse({
                'Status': False,
                'Errors': 'Не указаны все необходимые аргументы'
            })

        # Проверяем пароль на сложность
        try:
            validate_password(request.data['password'])
        except ValidationError as password_error:
            return JsonResponse({
                'Status': False,
                'Errors': {'password': password_error.messages}
            })

        # Создаем пользователя
        user_serializer = UserSerializer(data=request.data)
        if user_serializer.is_valid():
            user = user_serializer.save()
            user.set_password(request.data['password'])
            user.save()
            new_user_registered_signal.send(sender=self.__class__, user_id=user.id)
            return JsonResponse({'Status': True})
        else:
            return JsonResponse({
                'Status': False,
                'Errors': user_serializer.errors
            })


class ConfirmAccount(APIView):
    """
    Подтверждение email адреса
    """

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
                return JsonResponse({'Status': True})
            else:
                return JsonResponse({
                    'Status': False,
                    'Errors': 'Неправильно указан токен или email'
                })

        return JsonResponse({
            'Status': False,
            'Errors': 'Не указаны все необходимые аргументы'
        })


class AccountDetails(APIView):
    """
    Управление данными пользователя
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        """Получить данные пользователя"""

        serializer = UserSerializer(request.user)
        return Response(serializer.data)

    def post(self, request, *args, **kwargs):
        """Обновить данные пользователя"""

        # Если передан пароль, проверяем его
        if 'password' in request.data:
            try:
                validate_password(request.data['password'])
            except ValidationError as password_error:
                return JsonResponse({
                    'Status': False,
                    'Errors': {'password': password_error.messages}
                })
            else:
                request.user.set_password(request.data['password'])

        # Обновляем остальные данные
        user_serializer = UserSerializer(request.user, data=request.data, partial=True)
        if user_serializer.is_valid():
            user_serializer.save()
            return JsonResponse({'Status': True})
        else:
            return JsonResponse({
                'Status': False,
                'Errors': user_serializer.errors
            })


class LoginAccount(APIView):
    """
    Авторизация пользователей
    """

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
                    return JsonResponse({
                        'Status': True,
                        'Token': token.key
                    })

            return JsonResponse({
                'Status': False,
                'Errors': 'Не удалось авторизовать'
            })

        return JsonResponse({
            'Status': False,
            'Errors': 'Не указаны все необходимые аргументы'
        })


class CategoryView(ListAPIView):
    """
    Просмотр категорий товаров
    """
    queryset = Category.objects.all()
    serializer_class = CategorySerializer


class ShopView(ListAPIView):
    """
    Просмотр списка активных магазинов
    """
    queryset = Shop.objects.filter(state=True)
    serializer_class = ShopSerializer


class ProductInfoView(APIView):
    """
    Поиск товаров с фильтрацией
    """

    def get(self, request, *args, **kwargs):
        """Получить список товаров с фильтрацией"""

        query = Q(shop__state=True)
        shop_id = request.query_params.get('shop_id')
        category_id = request.query_params.get('category_id')

        if shop_id:
            query = query & Q(shop_id=shop_id)

        if category_id:
            query = query & Q(product__category_id=category_id)

        # Фильтруем и отбрасываем дубликаты
        queryset = ProductInfo.objects.filter(query).select_related(
            'shop' 'product__category'
        ).prefetch_related(
            'product_parameters__parameter'
        ).distinct()

        serializer = ProductInfoSerializer(queryset, many=True)
        return Response(serializer.data)


class BasketView(APIView):
    """
    Управление корзиной пользователя
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        """Получить содержимое корзины"""

        basket = Order.objects.filter(
            user_id=request.user.id,
            state='basket'
        ).prefetch_related(
            'ordered_items__product_info__product__category',
            'ordered_items__product_info__product_parameters__parameter'
        ).annotate(
            total_sum=Sum(F('ordered_items__quantity') * F('ordered_items__product_info__price'))
        ).distinct()

        serializer = OrderSerializer(basket, many=True)
        return Response(serializer.data)

    def post(self, request, *args, **kwargs):
        """Добавить товары в корзину"""

        items_string = request.data.get('items')
        if items_string:
            try:
                items_dict = load_json(items_string)
            except ValueError:
                return JsonResponse({
                    'Status': False,
                    'Errors': 'Неверный формат запроса'
                })
            else:
                basket, _ = Order.objects.get_or_create(
                    user_id=request.user.id,
                    state='basket'
                )
                object_created = 0

                for order_item in items_dict:
                    order_item.update({'order': basket.id})
                    serializer = OrderItemSerializer(data=order_item)

                    if serializer.is_valid():
                        try:
                            serializer.save()
                        except IntegrityError as error:
                            return JsonResponse({
                                'Status': False,
                                'Errors': str(error)
                            })
                        else:
                            object_created += 1
                    else:
                        return JsonResponse({
                            'Status': False,
                            'Errors': serializer.errors
                        })

                return JsonResponse({
                    'Status': True,
                    'Создано объектов': object_created
                })

        return JsonResponse({
            'Status': False,
            'Errors': 'не указаны все необходимые документы'
        })

    def put(self, request, *args, **kwargs):
        """Обновить количество товаров в корзине"""

        items_string = request.data.get('items')
        if items_string:
            try:
                items_dict = load_json(items_string)
            except ValueError:
                return JsonResponse({
                    'Status': False,
                    'Errors': 'Неверный формат запроса'
                })
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

                return JsonResponse({
                    'Status': True,
                    'Обновлено объектов': objects_updated
                })

        return JsonResponse({
            'Status': False,
            'Errors': 'Не указаны все необходимые аргументы'
        })

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
                deleted_count = OrderItem.objects.filter(query).delete()
                return JsonResponse({
                    'Status': True,
                    'Удалено объектов': deleted_count
                })

        return JsonResponse({
            'Status': False,
            'Errors': 'Не указаны все необходимые аргументы'
        })


class ContactView(APIView):
    """
    Управление контактной информацией
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        """Получить контакты пользователя"""

        contact = Contact.objects.filter(user_id=request.user.id)
        serializer = ContactSerializer(contact, many=True)
        return Response(serializer.data)

    def post(self, request, *args, **kwargs):
        """Создать новый контакт"""

        if {'city', 'street', 'phone'}.issubset(request.data.keys()):
            request.data._mutable = True
            request.data.update({'user': request.user.id})
            serializer = ContactSerializer(data=request.data)

            if serializer.is_valid():
                serializer.save()
                return JsonResponse({'Status': True})
            else:
                return JsonResponse({
                    'Status': False,
                    'Errors': serializer.errors
                })

        return JsonResponse({
            'Status': False,
            'Errors': 'Не указаны все необходимые аргументы'
        })

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
                        return JsonResponse({'Status': True})
                    else:
                        return JsonResponse({
                            'Status': False,
                            'Errors': serializer.errors
                        })

        return JsonResponse({
            'Status': False,
            'Errors': 'Не указаны все необходимые аргументы'
        })

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
                deleted_count = Contact.objects.filter(query).delete()
                return JsonResponse({
                    'Status': True,
                    'Удалено объектов': deleted_count
                })

        return JsonResponse({
            'Status': False,
            'Errors': 'Не указаны все необходимые аргументы'
        })


class OrderView(APIView):
    """
    Управление заказами пользователей
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        """Получить заказы пользователя"""

        order = Order.objects.filter(
            user_id=request.user.id,
        ).exclude(state='basket').prefetch_related(
            'ordered_items__product_info__product__category',
            'ordered_items__product_info__product_parameters__parameter'
        ).select_related('contact').annotate(
            total_sum=Sum(F('ordered_items__quantity') * F('ordered_items__product_info__price'))
        ).distinct()

        serializer = OrderSerializer(order, many=True)
        return Response(serializer.data)

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
                    return JsonResponse({
                        'Status': False,
                        'Errors': 'Неправильно указаны аргументы'
                    })
                else:
                    if is_updated:
                        new_order_signal.send(sender=self.__class__, user_id=request.user.id)
                        return JsonResponse({'Status': True})

        return JsonResponse({
            'Status': False,
            'Errors': 'Не указаны все необходимые аргументы'
        })


# Представления для поставщиков

class PartnerUpdate(APIView):
    """
    Обновление прайс-листа поставщиком
    """

    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        """Обновить прайс-лист"""

        if request.user.type != 'shop':
            return JsonResponse({
                'Status': False,
                'Error': 'Только для магазинов'
            }, status=403)

        url = request.data.get('url')
        if url:
            validate_url = URLValidator()
            try:
                validate_url(url)
            except ValidationError as e:
                return JsonResponse({
                    'Status': False,
                    'Error': str(e)
                })
            else:
                # Запускаем асинхронную задачу импорта
                task = import_shop_data_task.delay(url, request.user.id)
                return JsonResponse({
                    'Status': True,
                    'task_id': task.id
                })

        return JsonResponse({
            'Status': False,
            'Errors': 'Не указаны все необходимые аргументы'
        })


class PartnerState(APIView):
    """
    Управление статусом поставщика
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        """Получить статус поставщика"""

        if request.user.type != 'shop':
            return JsonResponse({
                'Status': False,
                'Error': 'Только для магазинов'
            }, status=403)

        shop = request.user.shop
        serializer = ShopSerializer(shop)
        return Response(serializer.data)

    def post(self, request, *args, **kwargs):
        """Изменить статус поставщика"""

        if request.user.type != 'shop':
            return JsonResponse({
                'Status': False,
                'Error': 'Только для магазинов'
            }, status=403)

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
                return JsonResponse({'Status': True})
            except ValueError as error:
                return JsonResponse({
                    'Status': False,
                    'Errors': str(error)
                })

        return JsonResponse({
            'Status': False,
            'Errors': 'Не указаны все необходимые аргументы'
        })


class PartnerOrders(APIView):
    """
    Заказы поставщика
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        """Получить заказы поставщика"""

        if request.user.type != 'shop':
            return JsonResponse({
                'Status': False,
                'Error': 'Только для магазинов'
            }, status=403)

        order = Order.objects.filter(
            ordered_items__product_info__shop__user_id=request.user.id
        ).exclude(state='basket').prefetch_related(
            'ordered_items__product_info__product__category',
            'ordered_items__product_info__product_parameters__parameter'
        ).select_related('contact').annotate(
            total_sum=Sum(F('ordered_items__quantity') * F('ordered_items__product_info__price'))
        ).distinct()

        serializer = OrderSerializer(order, many=True)
        return Response(serializer.data)


class OrderStatusUpdateView(APIView):
    """
    Обновление статуса заказа (для админки)
    """

    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        """Обновить статус заказа"""

        if not request.user.is_staff:
            return JsonResponse({
                'Status': False,
                'Error': 'Недостаточно прав'
            }, status=403)

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

                return JsonResponse({'Status': True})
            except Exception as e:
                return JsonResponse({
                    'Status': False,
                    'Error': str(e)
                })

        return JsonResponse({
            'Status': False,
            'Errors': 'Не указаны все необходимые аргументы'
        })
