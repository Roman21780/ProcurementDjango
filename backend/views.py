from distutils.util import strtobool
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


class ConfirmAccount(APIView):
    """
    Подтверждение email адреса
    """


class AccountDetails(APIView):
    """
    Управление данными пользователя
    """


class LoginAccount(APIView):
    """
    Авторизация пользователей
    """


class CategoryView(ListAPIView):
    """
    Просмотр категорий товаров
    """


class ShopView(ListAPIView):
    """
    Просмотр списка активных магазинов
    """


class ProductInfoView(APIView):
    """
    Поиск товаров с фильтрацией
    """


class BasketView(APIView):
    """
    Управление корзиной пользователя
    """


class ContactView(APIView):
    """
    Управление контактной информацией
    """


class OrderView(APIView):
    """
    Управление заказами пользователей
    """


# Представления для поставщиков

class PartnerUpdate(APIView):
    """
    Обновление прайс-листа поставщиком
    """


class PartnerState(APIView):
    """
    Управление статусом поставщика
    """


class PartnerOrders(APIView):
    """
    Заказы поставщика
    """


class OrderStatusUpdateView(APIView):
    """
    Обновление статуса заказа (для админки)
    """

















