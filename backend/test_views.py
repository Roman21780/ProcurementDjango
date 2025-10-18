from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from django.contrib.auth import get_user_model
from backend.models import Shop, Category, Product, ProductInfo, Order, OrderItem, Contact, ConfirmEmailToken
from rest_framework.authtoken.models import Token
import json

User = get_user_model()

class ConfirmAccountTests(APITestCase):
    """Тесты подтверждения email"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='TestPass123!',
            first_name='Test',
            last_name='User',
            is_active=False
        )
        self.token = ConfirmEmailToken.objects.create(user=self.user, key='testtoken123')
        self.url = reverse('backend:user-register-confirm')
    
    def test_confirm_account_success(self):
        """Успешное подтверждение email"""
        data = {
            'email': 'test@example.com',
            'token': 'testtoken123'
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_active)
        self.assertFalse(ConfirmEmailToken.objects.filter(key='testtoken123').exists())
    
    def test_confirm_account_invalid_token(self):
        """Попытка подтверждения с неверным токеном"""
        data = {
            'email': 'test@example.com',
            'token': 'wrongtoken'
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_active)


class ProductInfoViewTests(APITestCase):
    """Тесты поиска товаров"""
    
    def setUp(self):
        self.category = Category.objects.create(name='Тестовая категория')
        self.shop = Shop.objects.create(name='Тестовый магазин', state=True)
        self.product = Product.objects.create(
            name='Тестовый товар',
            category=self.category
        )
        self.product_info = ProductInfo.objects.create(
            product=self.product,
            shop=self.shop,
            model='Модель 123',
            price=1000,
            quantity=10
        )
        self.url = reverse('backend:products')
    
    def test_list_products(self):
        """Получение списка товаров"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], 'Тестовый товар')
    
    def test_filter_by_shop(self):
        """Фильтрация товаров по магазину"""
        response = self.client.get(f"{self.url}?shop_id={self.shop.id}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], 'Тестовый товар')
    
    def test_filter_by_category(self):
        """Фильтрация товаров по категории"""
        response = self.client.get(f"{self.url}?category_id={self.category.id}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], 'Тестовый товар')


class PartnerStateTests(APITestCase):
    """Тесты управления статусом магазина"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='partner@example.com',
            password='TestPass123!',
            first_name='Partner',
            last_name='User',
            type='shop'
        )
        self.shop = Shop.objects.create(
            user=self.user,
            name='Партнерский магазин',
            state=True
        )
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        self.url = reverse('backend:partner-state')
    
    def test_get_shop_state(self):
        """Получение статуса магазина"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['state'], True)
    
    def test_update_shop_state(self):
        """Изменение статуса магазина"""
        data = {'state': False}
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.shop.refresh_from_db()
        self.assertFalse(self.shop.state)
    
    def test_unauthorized_access(self):
        """Попытка доступа без авторизации"""
        self.client.credentials()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
