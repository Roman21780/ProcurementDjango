from typing import Dict, Any, Optional
from django.core.validators import RegexValidator, EmailValidator
from rest_framework import serializers
from backend.models import (
    User, Category, Shop, ProductInfo, Product,
    ProductParameter, OrderItem, Order, Contact
)
from drf_spectacular.utils import extend_schema_field, extend_schema_serializer

# Common validators
PHONE_REGEX = r'^\+7\d{10}$'
PHONE_ERROR = 'Номер телефона должен быть в формате +7XXXXXXXXXX'


@extend_schema_serializer(exclude_fields=('user',))
class ContactSerializer(serializers.ModelSerializer):
    """
    Сериализатор для контактной информации пользователя.
    
    Поля:
        id: Уникальный идентификатор контакта (только чтение)
        city: Название города (обязательное)
        street: Название улицы (обязательное)
        house: Номер дома (обязательное)
        structure: Строение/Корпус (необязательное)
        building: Строение (необязательное)
        apartment: Номер квартиры/офиса (обязательное)
        phone: Контактный телефон в формате +7XXXXXXXXXX (обязательное)
    """
    
    class Meta:
        model = Contact
        fields = ('id', 'city', 'street', 'house', 'structure', 'building', 'apartment', 'user', 'phone')
        read_only_fields = ('id',)
        extra_kwargs = {
            'user': {
                'write_only': True,
                'help_text': 'ID пользователя, к которому привязан контакт'
            },
            'city': {
                'help_text': 'Город проживания',
                'required': True,
                'max_length': 50,
                'error_messages': {
                    'required': 'Поле города обязательно для заполнения',
                    'max_length': 'Название города не должно превышать 50 символов'
                }
            },
            'street': {
                'help_text': 'Название улицы',
                'required': True,
                'max_length': 100,
                'error_messages': {
                    'required': 'Поле улицы обязательно для заполнения',
                    'max_length': 'Название улицы не должно превышать 100 символов'
                }
            },
            'house': {
                'help_text': 'Номер дома',
                'max_length': 15,
                'required': True,
                'error_messages': {
                    'required': 'Поле номера дома обязательно для заполнения',
                    'max_length': 'Номер дома не должен превышать 15 символов'
                }
            },
            'structure': {
                'help_text': 'Строение/Корпус (необязательно)',
                'max_length': 15,
                'required': False,
                'allow_blank': True,
                'error_messages': {
                    'max_length': 'Номер корпуса не должен превышать 15 символов'
                }
            },
            'building': {
                'help_text': 'Строение (необязательно)',
                'max_length': 15,
                'required': False,
                'allow_blank': True,
                'error_messages': {
                    'max_length': 'Номер строения не должен превышать 15 символов'
                }
            },
            'apartment': {
                'help_text': 'Квартира/Офис',
                'max_length': 15,
                'required': True,
                'error_messages': {
                    'required': 'Поле квартиры/офиса обязательно для заполнения',
                    'max_length': 'Номер квартиры/офиса не должен превышать 15 символов'
                }
            },
            'phone': {
                'help_text': 'Контактный телефон в формате +7XXXXXXXXXX',
                'validators': [
                    RegexValidator(
                        regex=PHONE_REGEX,
                        message=PHONE_ERROR
                    )
                ],
                'required': True,
                'error_messages': {
                    'required': 'Поле телефона обязательно для заполнения'
                }
            }
        }


class UserSerializer(serializers.ModelSerializer):
    """
    Сериализатор для работы с данными пользователя.
    
    Включает в себя контактную информацию пользователя.
    """
    contacts = ContactSerializer(many=True, read_only=True)
    email = serializers.EmailField(
        validators=[
            EmailValidator(
                message='Введите корректный email адрес'
            )
        ],
        required=True,
        help_text='Электронная почта пользователя'
    )

    class Meta:
        model = User
        fields = ('id', 'first_name', 'last_name', 'email', 'company', 'position', 'type', 'contacts')
        read_only_fields = ('id',)
        extra_kwargs = {
            'first_name': {
                'required': True,
                'max_length': 30,
                'help_text': 'Имя пользователя',
                'error_messages': {
                    'required': 'Имя обязательно для заполнения',
                    'max_length': 'Имя не должно превышать 30 символов'
                }
            },
            'last_name': {
                'required': True,
                'max_length': 30,
                'help_text': 'Фамилия пользователя',
                'error_messages': {
                    'required': 'Фамилия обязательна для заполнения',
                    'max_length': 'Фамилия не должна превышать 30 символов'
                }
            },
            'company': {
                'required': False,
                'max_length': 100,
                'help_text': 'Название компании',
                'allow_blank': True,
                'error_messages': {
                    'max_length': 'Название компании не должно превышать 100 символов'
                }
            },
            'position': {
                'required': False,
                'max_length': 100,
                'help_text': 'Должность в компании',
                'allow_blank': True,
                'error_messages': {
                    'max_length': 'Название должности не должно превышать 100 символов'
                }
            },
            'type': {
                'help_text': 'Тип пользователя (покупатель, продавец и т.д.)',
                'default': 'buyer'
            }
        }


class CategorySerializer(serializers.ModelSerializer):
    """Сериализатор для категорий"""

    class Meta:
        model = Category
        fields = ('id', 'name')
        read_only_fields = ('id',)


class ShopSerializer(serializers.ModelSerializer):
    """Сериализатор для магазинов"""

    class Meta:
        model = Shop
        fields = ('id', 'name', 'state',)
        read_only_fields = ('id',)


class ProductSerializer(serializers.ModelSerializer):
    """Сериализатор для товаров"""
    category = serializers.StringRelatedField()

    class Meta:
        model = Product
        fields = ('name', 'category',)


class ProductParameterSerializer(serializers.ModelSerializer):
    """Сериализатор для параметров товара"""
    parameter = serializers.StringRelatedField()

    class Meta:
        model = ProductParameter
        fields = ('parameter', 'value')


class ProductInfoSerializer(serializers.ModelSerializer):
    """Сериализатор для информации о товаре"""
    product = ProductSerializer(read_only=True)
    product_parameters = ProductParameterSerializer(many=True, read_only=True)

    class Meta:
        model = ProductInfo
        fields = ('id', 'model', 'product', 'shop', 'quantity', 'price', 'price_rrc', 'product_parameters',)
        read_only_fields = ('id',)


class OrderItemSerializer(serializers.ModelSerializer):
    """
    Сериализатор для работы с позициями заказа.
    
    Поля:
        id: Уникальный идентификатор позиции (только чтение)
        product_info: Информация о товаре
        quantity: Количество товара (целое число, больше 0)
        order: Ссылка на заказ (только для записи)
    """
    
    class Meta:
        model = OrderItem
        fields = ('id', 'product_info', 'quantity', 'order')
        read_only_fields = ('id',)
        extra_kwargs = {
            'order': {
                'write_only': True,
                'help_text': 'ID заказа, к которому относится позиция'
            },
            'product_info': {
                'help_text': 'ID информации о товаре',
                'required': True,
                'error_messages': {
                    'required': 'Необходимо указать информацию о товаре'
                }
            },
            'quantity': {
                'help_text': 'Количество товара (целое число, больше 0)',
                'min_value': 1,
                'required': True,
                'error_messages': {
                    'required': 'Необходимо указать количество товара',
                    'min_value': 'Количество товара должно быть не менее 1'
                }
            }
        }


class OrderItemCreateSerializer(OrderItemSerializer):
    """Сериализатор для создания позиций заказа"""
    product_info = ProductInfoSerializer(read_only=True)


class OrderSerializer(serializers.ModelSerializer):
    """Сериализатор для заказов"""
    ordered_items = OrderItemCreateSerializer(many=True, read_only=True)
    calculated_total = serializers.DecimalField(
        max_digits=12, decimal_places=2, read_only=True
    )
    contact = ContactSerializer(read_only=True)

    class Meta:
        model = Order
        fields = ('id', 'ordered_items', 'state', 'dt', 'calculated_total', 'contact',)
        read_only_fields = ('id',)


class OrderStatusUpdateSerializer(serializers.ModelSerializer):
    """Сериализатор для обновления статуса заказа"""

    class Meta:
        model = Order
        fields = ('id', 'state',)
        read_only_fields = ('id',)


class ShopStatusSerializer(serializers.ModelSerializer):
    """Сериализатор для статуса магазина"""

    class Meta:
        model = Shop
        fields = ('id', 'name', 'state', 'user')
        read_only_fields = ('id', 'name', 'user')
