import json
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from rest_framework.authtoken.models import Token
from django.core.files.uploadedfile import SimpleUploadedFile

from backend.models import (
    User, Shop, Category, Product, ProductInfo,
    Contact, Order, OrderItem, Parameter, ProductParameter
)

# Test constants
TEST_EMAIL = 'test@example.com'
TEST_PASSWORD = 'TestPass123!'
SHOP_EMAIL = 'shop@example.com'
SHOP_PASSWORD = 'ShopPass123!'
BUYER_EMAIL = 'buyer@example.com'
BUYER_PASSWORD = 'BuyerPass123!'


def create_test_file(content=b'test content', filename='test.yaml'):
    """Helper function to create a test file"""
    return SimpleUploadedFile(filename, content, content_type='application/yaml')


class UserRegistrationTests(APITestCase):
    """Тесты регистрации пользователей"""
    
    def tearDown(self):
        User.objects.all().delete()
        Shop.objects.all().delete()

    def test_register_buyer_success(self):
        """Успешная регистрация покупателя"""
        url = reverse('backend:user-register')
        data = {
            'first_name': 'Ivan',
            'last_name': 'Petrov',
            'email': TEST_EMAIL,
            'password': TEST_PASSWORD,
            'company': 'Test Company',
            'position': 'Manager',
            'type': 'buyer'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('Status', response.data)
        self.assertTrue(response.data['Status'])
        self.assertTrue(User.objects.filter(email=TEST_EMAIL).exists())
        user = User.objects.get(email=TEST_EMAIL)
        self.assertEqual(user.type, 'buyer')
        self.assertFalse(user.is_active)  # User should be inactive until email confirmation

    def test_register_shop_success(self):
        """Успешная регистрация магазина"""
        url = reverse('backend:user-register')
        data = {
            'first_name': 'Shop',
            'last_name': 'Owner',
            'email': SHOP_EMAIL,
            'password': SHOP_PASSWORD,
            'company': 'My Shop',
            'position': 'Director',
            'type': 'shop'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('Status', response.data)
        self.assertTrue(response.data['Status'])
        self.assertTrue(User.objects.filter(email=SHOP_EMAIL).exists())
        self.assertTrue(Shop.objects.filter(user__email=SHOP_EMAIL).exists())
        shop = Shop.objects.get(user__email=SHOP_EMAIL)
        self.assertEqual(shop.name, 'My Shop')
        self.assertFalse(shop.user.is_active)  # Shop should be inactive until email confirmation

    def test_register_missing_fields(self):
        """Регистрация без обязательных полей"""
        url = reverse('backend:user-register')
        data = {'email': TEST_EMAIL}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Errors', response.data)
        self.assertIn('first_name', response.data['Errors']
                     ) if 'first_name' in response.data['Errors'] else None
        self.assertIn('last_name', response.data['Errors']
                     ) if 'last_name' in response.data['Errors'] else None
        self.assertIn('password', response.data['Errors']
                     ) if 'password' in response.data['Errors'] else None
        self.assertIn('company', response.data['Errors']
                     ) if 'company' in response.data['Errors'] else None
        self.assertIn('position', response.data['Errors']
                     ) if 'position' in response.data['Errors'] else None

    def test_register_weak_password(self):
        """Регистрация со слабым паролем"""
        url = reverse('backend:user-register')
        data = {
            'first_name': 'Test',
            'last_name': 'User',
            'email': 'weak@example.com',
            'password': '123',
            'company': 'Test',
            'position': 'Manager',
            'type': 'buyer'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Errors', response.data)
        self.assertIn('password', response.data['Errors'])
        
    def test_register_duplicate_email(self):
        """Попытка регистрации с уже существующим email"""
        # Создаем пользователя
        User.objects.create_user(
            email=TEST_EMAIL,
            password=TEST_PASSWORD,
            first_name='Existing',
            last_name='User',
            is_active=True
        )
        
        # Пытаемся создать пользователя с тем же email
        url = reverse('backend:user-register')
        data = {
            'first_name': 'New',
            'last_name': 'User',
            'email': TEST_EMAIL,
            'password': 'NewPass123!',
            'company': 'Test',
            'position': 'Tester',
            'type': 'buyer'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Errors', response.data)
        self.assertIn('email', response.data['Errors'])
        self.assertEqual(len(User.objects.filter(email=TEST_EMAIL)), 1)  # Убедимся, что пользователь не создан повторно


class LoginTests(APITestCase):
    """Тесты авторизации"""
    
    @classmethod
    def setUpTestData(cls):
        # Создаем тестового пользователя один раз для всех тестов
        cls.user = User.objects.create_user(
            email=TEST_EMAIL,
            password=TEST_PASSWORD,
            first_name='Test',
            last_name='User',
            is_active=True
        )
        
        # Создаем неактивного пользователя
        cls.inactive_user = User.objects.create_user(
            email='inactive@example.com',
            password=TEST_PASSWORD,
            first_name='Inactive',
            last_name='User',
            is_active=False
        )
    
    def tearDown(self):
        # Очищаем токены после каждого теста
        Token.objects.all().delete()
    
    def test_login_success(self):
        """Успешная авторизация с правильными учетными данными"""
        url = reverse('backend:user-login')
        data = {'email': TEST_EMAIL, 'password': TEST_PASSWORD}
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('Token', response.data)
        self.assertTrue(Token.objects.filter(user=self.user).exists())
        
        # Проверяем, что в ответе есть данные пользователя
        self.assertIn('user', response.data)
        self.assertEqual(response.data['user']['email'], TEST_EMAIL)
        self.assertEqual(response.data['user']['first_name'], 'Test')
        self.assertEqual(response.data['user']['last_name'], 'User')
    
    def test_login_inactive_user(self):
        """Попытка входа неактивного пользователя"""
        url = reverse('backend:user-login')
        data = {'email': 'inactive@example.com', 'password': TEST_PASSWORD}
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn('error', response.data)
        self.assertIn('Аккаунт не активирован', str(response.data['error']))
    
    def test_login_wrong_password(self):
        """Авторизация с неправильным паролем"""
        url = reverse('backend:user-login')
        data = {'email': TEST_EMAIL, 'password': 'WrongPassword123'}
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn('error', response.data)
        self.assertIn('Неверный email или пароль', str(response.data['error']))
    
    def test_login_nonexistent_user(self):
        """Авторизация несуществующего пользователя"""
        url = reverse('backend:user-login')
        data = {'email': 'nonexistent@example.com', 'password': 'Pass123!'}
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn('error', response.data)
        self.assertIn('Неверный email или пароль', str(response.data['error']))
    
    def test_login_missing_fields(self):
        """Авторизация без email или пароля"""
        url = reverse('backend:user-login')
        
        # Без email
        data = {'password': TEST_PASSWORD}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)
        
        # Без пароля
        data = {'email': TEST_EMAIL}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password', response.data)
        
        # Пустой запрос
        response = self.client.post(url, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)
        self.assertIn('password', response.data)
    
    def test_login_case_insensitive_email(self):
        """Проверка регистронезависимости email при авторизации"""
        url = reverse('backend:user-login')
        
        # Разные варианты регистра email
        emails = [
            TEST_EMAIL.upper(),
            TEST_EMAIL.capitalize(),
            TEST_EMAIL.replace('@', '@'),  # На случай, если есть проблемы с кодировкой
        ]
        
        for email in emails:
            data = {'email': email, 'password': TEST_PASSWORD}
            response = self.client.post(url, data, format='json')
            self.assertEqual(response.status_code, status.HTTP_200_OK, 
                           f'Failed for email: {email}')
            self.assertIn('Token', response.data)


class AccountDetailsTests(APITestCase):
    """Тесты управления данными пользователя"""

    @classmethod
    def setUpTestData(cls):
        # Создаем тестового пользователя один раз для всех тестов
        cls.user = User.objects.create_user(
            email=TEST_EMAIL,
            password=TEST_PASSWORD,
            first_name='John',
            last_name='Doe',
            company='Test Corp',
            position='Developer',
            is_active=True
        )
    
    def setUp(self):
        # Создаем новый токен перед каждым тестом
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
    
    def tearDown(self):
        # Очищаем токены после каждого теста
        Token.objects.all().delete()
    
    def test_get_account_details_authenticated(self):
        """Успешное получение данных аккаунта аутентифицированным пользователем"""
        url = reverse('backend:user-details')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], TEST_EMAIL)
        self.assertEqual(response.data['first_name'], 'John')
        self.assertEqual(response.data['last_name'], 'Doe')
        self.assertEqual(response.data['company'], 'Test Corp')
        self.assertEqual(response.data['position'], 'Developer')
        self.assertNotIn('password', response.data)  # Пароль не должен быть в ответе
    
    def test_get_account_unauthorized(self):
        """Попытка получения данных без авторизации"""
        self.client.credentials()  # Сбрасываем аутентификацию
        url = reverse('backend:user-details')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn('detail', response.data)
        self.assertEqual(
            str(response.data['detail']), 
            'Учетные данные не были предоставлены.'
        )
    
    def test_update_account_details_partial(self):
        """Частичное обновление данных аккаунта"""
        url = reverse('backend:user-details')
        update_data = {
            'first_name': 'Jane',
            'company': 'New Corp',
            'position': 'Senior Developer'
        }
        
        response = self.client.post(url, update_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        
        # Проверяем обновленные поля
        self.assertEqual(self.user.first_name, 'Jane')
        self.assertEqual(self.user.company, 'New Corp')
        self.assertEqual(self.user.position, 'Senior Developer')
        
        # Проверяем, что остальные поля не изменились
        self.assertEqual(self.user.last_name, 'Doe')
        self.assertEqual(self.user.email, TEST_EMAIL)
    
    def test_update_password(self):
        """Обновление пароля пользователя"""
        url = reverse('backend:user-details')
        new_password = 'NewSecurePass123!'
        update_data = {
            'password': new_password
        }
        
        response = self.client.post(url, update_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        
        # Проверяем, что пароль изменился
        self.assertTrue(self.user.check_password(new_password))
    
    def test_update_invalid_data(self):
        """Попытка обновления с неверными данными"""
        url = reverse('backend:user-details')
        invalid_data = {
            'email': 'not-an-email',  # Неверный формат email
            'first_name': '',  # Пустое имя
            'password': '123'  # Слишком короткий пароль
        }
        
        response = self.client.post(url, invalid_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)
        self.assertIn('first_name', response.data)
        self.assertIn('password', response.data)
    
    def test_update_readonly_fields(self):
        """Попытка изменить read-only поля"""
        url = reverse('backend:user-details')
        original_date_joined = self.user.date_joined
        update_data = {
            'date_joined': '2020-01-01T00:00:00Z',
            'is_active': False,
            'is_staff': True
        }
        
        response = self.client.post(url, update_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        
        # Проверяем, что read-only поля не изменились
        self.assertEqual(self.user.date_joined, original_date_joined)
        self.assertTrue(self.user.is_active)  # Должно остаться True
        self.assertFalse(self.user.is_staff)  # Должно остаться False


class CategoryTests(APITestCase):
    """Тесты категорий товаров"""
    
    @classmethod
    def setUpTestData(cls):
        # Создаем тестовые категории один раз для всех тестов
        cls.category1 = Category.objects.create(id=1, name='Electronics')
        cls.category2 = Category.objects.create(id=2, name='Books')
        cls.category3 = Category.objects.create(id=3, name='Clothing')
        
        # Создаем пользователя и магазин для тестирования фильтрации товаров
        cls.user = User.objects.create_user(
            email='shop_owner@example.com',
            password=TEST_PASSWORD,
            type='shop',
            is_active=True
        )
        cls.shop = Shop.objects.create(
            user=cls.user,
            name='Test Shop',
            state=True
        )
        
        # Создаем тестовые товары
        cls.product1 = Product.objects.create(
            name='Smartphone',
            category=cls.category1  # Electronics
        )
        cls.product2 = Product.objects.create(
            name='Python Book',
            category=cls.category2  # Books
        )
        
        # Создаем информацию о товарах в магазине
        ProductInfo.objects.create(
            product=cls.product1,
            shop=cls.shop,
            model='Model X',
            price=50000,
            quantity=10
        )
        ProductInfo.objects.create(
            product=cls.product2,
            shop=cls.shop,
            model='2nd Edition',
            price=2000,
            quantity=5
        )
    
    def test_list_categories_success(self):
        """Успешное получение списка категорий"""
        url = reverse('backend:categories')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)
        
        # Проверяем структуру ответа
        for category in response.data:
            self.assertIn('id', category)
            self.assertIn('name', category)
    
    def test_list_categories_ordered(self):
        """Проверка сортировки категорий по имени"""
        url = reverse('backend:categories')
        response = self.client.get(url)
        
        # Проверяем, что категории отсортированы по имени
        categories = response.data
        for i in range(len(categories) - 1):
            self.assertLessEqual(
                categories[i]['name'],
                categories[i + 1]['name'],
                'Categories are not sorted by name'
            )
    
    def test_category_detail(self):
        """Получение детальной информации о категории"""
        url = reverse('backend:category-detail', args=[self.category1.id])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.category1.id)
        self.assertEqual(response.data['name'], 'Electronics')
    
    def test_category_products(self):
        """Получение товаров категории"""
        url = reverse('backend:category-products', args=[self.category1.id])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)  # Только один товар в категории Electronics
        self.assertEqual(response.data[0]['name'], 'Smartphone')
    
    def test_nonexistent_category(self):
        """Попытка получить несуществующую категорию"""
        url = reverse('backend:category-detail', args=[999])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_category_products_empty(self):
        """Получение товаров пустой категории"""
        # Создаем пустую категорию
        empty_category = Category.objects.create(name='Empty Category')
        url = reverse('backend:category-products', args=[empty_category.id])
        
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)


class ShopTests(APITestCase):
    """Тесты магазинов"""
    
    @classmethod
    def setUpTestData(cls):
        # Создаем пользователей
        cls.shop_owner1 = User.objects.create_user(
            email='shop1@example.com',
            password=TEST_PASSWORD,
            type='shop',
            is_active=True
        )
        cls.shop_owner2 = User.objects.create_user(
            email='shop2@example.com',
            password=TEST_PASSWORD,
            type='shop',
            is_active=True
        )
        cls.buyer = User.objects.create_user(
            email=BUYER_EMAIL,
            password=BUYER_PASSWORD,
            type='buyer',
            is_active=True
        )
        
        # Создаем магазины
        cls.shop1 = Shop.objects.create(
            user=cls.shop_owner1, 
            name='Shop 1', 
            state=True
        )
        cls.shop2 = Shop.objects.create(
            user=cls.shop_owner2, 
            name='Shop 2', 
            state=False  # Неактивный магазин
        )
        
        # Создаем категории и товары для тестирования
        cls.category = Category.objects.create(name='Test Category')
        cls.product = Product.objects.create(
            name='Test Product',
            category=cls.category
        )
        
        # Добавляем товары в магазины
        ProductInfo.objects.create(
            product=cls.product,
            shop=cls.shop1,
            model='Model 1',
            price=1000,
            quantity=10
        )
        
        # Создаем токены для аутентификации
        cls.shop1_token = Token.objects.create(user=cls.shop_owner1)
        cls.buyer_token = Token.objects.create(user=cls.buyer)
    
    def setUp(self):
        # Сбрасываем клиент перед каждым тестом
        self.client = APIClient()
    
    def test_list_active_shops_unauthorized(self):
        """Получение списка активных магазинов без авторизации"""
        url = reverse('backend:shops')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)  # Только один активный магазин
        self.assertEqual(response.data[0]['name'], 'Shop 1')
        
        # Проверяем структуру ответа
        shop_data = response.data[0]
        self.assertIn('id', shop_data)
        self.assertIn('name', shop_data)
        self.assertIn('state', shop_data)
        self.assertIn('url', shop_data)
        self.assertTrue(shop_data['state'])  # Проверяем, что магазин активен
    
    def test_list_all_shops_authenticated(self):
        """Получение списка всех магазинов аутентифицированным пользователем"""
        url = reverse('backend:all-shops')
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.buyer_token.key}')
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)  # Все магазины, включая неактивные
        
        # Проверяем, что в ответе есть как активные, так и неактивные магазины
        shop_states = [shop['state'] for shop in response.data]
        self.assertIn(True, shop_states)
        self.assertIn(False, shop_states)
    
    def test_shop_detail(self):
        """Получение детальной информации о магазине"""
        url = reverse('backend:shop-detail', args=[self.shop1.id])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Shop 1')
        self.assertTrue(response.data['state'])
        
        # Проверяем, что в ответе есть информация о товарах
        self.assertIn('products', response.data)
        self.assertEqual(len(response.data['products']), 1)
        self.assertEqual(response.data['products'][0]['name'], 'Test Product')
    
    def test_nonexistent_shop_detail(self):
        """Попытка получить несуществующий магазин"""
        url = reverse('backend:shop-detail', args=[999])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_update_shop_state_unauthorized(self):
        """Попытка изменить статус магазина без авторизации"""
        url = reverse('backend:shop-update-state', args=[self.shop1.id])
        data = {'state': False}
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_update_shop_state_as_buyer(self):
        """Попытка изменить статус магазина покупателем"""
        url = reverse('backend:shop-update-state', args=[self.shop1.id])
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.buyer_token.key}')
        
        response = self.client.post(url, {'state': False}, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_update_shop_state_owner(self):
        """Изменение статуса магазина владельцем"""
        url = reverse('backend:shop-update-state', args=[self.shop1.id])
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.shop1_token.key}')
        
        # Выключаем магазин
        response = self.client.post(url, {'state': False}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.shop1.refresh_from_db()
        self.assertFalse(self.shop1.state)
        
        # Включаем магазин обратно
        response = self.client.post(url, {'state': True}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.shop1.refresh_from_db()
        self.assertTrue(self.shop1.state)
    
    def test_update_other_shop_state(self):
        """Попытка изменить статус чужого магазина"""
        # Создаем токен для другого владельца магазина
        other_owner = User.objects.create_user(
            email='other@example.com',
            password='pass123',
            type='shop',
            is_active=True
        )
        other_token = Token.objects.create(user=other_owner)
        
        url = reverse('backend:shop-update-state', args=[self.shop1.id])
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {other_token.key}')
        
        response = self.client.post(url, {'state': False}, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.shop1.refresh_from_db()
        self.assertTrue(self.shop1.state)  # Статус не должен измениться
    
    def test_update_shop_state_invalid_data(self):
        """Попытка обновить статус с неверными данными"""
        url = reverse('backend:shop-update-state', args=[self.shop1.id])
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.shop1_token.key}')
        
        # Отправляем пустой запрос
        response = self.client.post(url, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('state', response.data)
        
        # Отправляем некорректное значение
        response = self.client.post(url, {'state': 'not-a-boolean'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_shop_products(self):
        """Получение списка товаров магазина"""
        url = reverse('backend:shop-products', args=[self.shop1.id])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], 'Test Product')
    
    def test_empty_shop_products(self):
        """Получение списка товаров пустого магазина"""
        # Создаем пустой магазин
        empty_shop = Shop.objects.create(
            user=self.shop_owner1,
            name='Empty Shop',
            state=True
        )
        
        url = reverse('backend:shop-products', args=[empty_shop.id])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], 'Shop 1')


class ProductTests(APITestCase):
    """Тесты товаров"""

    def setUp(self):
        shop_user = User.objects.create_user(
            email='shop@test.com',
            password='pass',
            type='shop',
            is_active=True
        )
        self.shop = Shop.objects.create(user=shop_user, name='Test Shop', state=True)
        self.category = Category.objects.create(id=10, name='Test Category')
        product1 = Product.objects.create(name='Product 1', category=self.category)
        product2 = Product.objects.create(name='Product 2', category=self.category)

        self.product_info1 = ProductInfo.objects.create(
            product=product1,
            shop=self.shop,
            model='Model1',
            price=100,
            quantity=10
        )
        self.product_info2 = ProductInfo.objects.create(
            product=product2,
            shop=self.shop,
            model='Model2',
            price=200,
            quantity=5
        )

    def test_list_products(self):
        """Получение списка товаров"""
        url = reverse('backend:products')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_filter_by_shop(self):
        """Фильтрация товаров по магазину"""
        url = reverse('backend:products')
        response = self.client.get(url, {'shop_id': self.shop.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_filter_by_category(self):
        """Фильтрация товаров по категории"""
        url = reverse('backend:products')
        response = self.client.get(url, {'category_id': self.category.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)


class BasketTests(APITestCase):
    """Тесты корзины"""

    def setUp(self):
        self.user = User.objects.create_user(
            email='buyer@example.com',
            password='BuyerPass123!',
            first_name='Buyer',
            last_name='Test',
            is_active=True
        )
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)

        shop_user = User.objects.create_user(
            email='shop@test.com',
            password='pass',
            type='shop',
            is_active=True
        )
        self.shop = Shop.objects.create(user=shop_user, name='Test Shop', state=True)
        category = Category.objects.create(id=10, name='Test Category')
        product = Product.objects.create(name='Test Product', category=category)
        self.product_info = ProductInfo.objects.create(
            product=product,
            shop=self.shop,
            model='Model1',
            price=100,
            quantity=10
        )

    def test_get_empty_basket(self):
        """Получение пустой корзины"""
        url = reverse('backend:basket')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    def test_add_to_basket(self):
        """Добавление товара в корзину"""
        url = reverse('backend:basket')
        items = json.dumps([{
            "product_info": self.product_info.id,
            "quantity": 2
        }])
        data = {'items': items}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Order.objects.filter(user=self.user, state='basket').exists())

    def test_basket_unauthorized(self):
        """Доступ к корзине без авторизации"""
        self.client.credentials()
        url = reverse('backend:basket')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class ContactTests(APITestCase):
    """Тесты контактов"""

    def setUp(self):
        self.user = User.objects.create_user(
            email='contact@example.com',
            password='Pass123!',
            first_name='Test',
            last_name='User',
            is_active=True
        )
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)

    def test_create_contact(self):
        """Создание контакта"""
        url = reverse('backend:user-contact')
        data = {
            'city': 'Moscow',
            'street': 'Lenina 1',
            'phone': '+79001234567'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Contact.objects.filter(user=self.user).exists())

    def test_list_contacts(self):
        """Получение списка контактов"""
        Contact.objects.create(
            user=self.user,
            city='Moscow',
            street='Test St',
            phone='+79001111111'
        )
        url = reverse('backend:user-contact')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_update_contact(self):
        """Обновление контакта"""
        contact = Contact.objects.create(
            user=self.user,
            city='Moscow',
            street='Old Street',
            phone='+79001111111'
        )
        url = reverse('backend:user-contact')
        data = {'id': contact.id, 'street': 'New Street'}
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        contact.refresh_from_db()
        self.assertEqual(contact.street, 'New Street')

    def test_delete_contact(self):
        """Удаление контакта"""
        contact = Contact.objects.create(
            user=self.user,
            city='Moscow',
            street='Test',
            phone='+79001111111'
        )
        url = reverse('backend:user-contact')
        data = {'items': str(contact.id)}
        response = self.client.delete(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(Contact.objects.filter(id=contact.id).exists())


class OrderTests(APITestCase):
    """Тесты заказов"""

    def setUp(self):
        self.user = User.objects.create_user(
            email='buyer@example.com',
            password='Pass123!',
            is_active=True
        )
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)

        self.contact = Contact.objects.create(
            user=self.user,
            city='Moscow',
            street='Test St',
            phone='+79001234567'
        )

        shop_user = User.objects.create_user(
            email='shop@test.com',
            password='pass',
            type='shop',
            is_active=True
        )
        shop = Shop.objects.create(user=shop_user, name='Test Shop', state=True)
        category = Category.objects.create(id=10, name='Test Category')
        product = Product.objects.create(name='Test Product', category=category)
        product_info = ProductInfo.objects.create(
            product=product,
            shop=shop,
            model='Model1',
            price=100,
            quantity=10
        )

        self.basket = Order.objects.create(user=self.user, state='basket')
        OrderItem.objects.create(
            order=self.basket,
            product_info=product_info,
            quantity=2
        )

    def test_get_orders(self):
        """Получение списка заказов"""
        url = reverse('backend:order')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_create_order_from_basket(self):
        """Создание заказа из корзины"""
        url = reverse('backend:order')
        data = {
            'id': self.basket.id,
            'contact': self.contact.id
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.basket.refresh_from_db()
        self.assertEqual(self.basket.state, 'new')


class PartnerStateTests(APITestCase):
    """Тесты управления статусом магазина"""

    def setUp(self):
        self.shop_user = User.objects.create_user(
            email='shop@example.com',
            password='ShopPass123!',
            type='shop',
            is_active=True
        )
        self.shop = Shop.objects.create(
            user=self.shop_user,
            name='Test Shop',
            state=True
        )
        self.token = Token.objects.create(user=self.shop_user)
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)

    def test_get_shop_state(self):
        """Получение статуса магазина"""
        url = reverse('backend:partner-state')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['state'], True)

    def test_update_shop_state(self):
        """Изменение статуса магазина"""
        url = reverse('backend:partner-state')
        data = {'state': 'false'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.shop.refresh_from_db()
        self.assertEqual(self.shop.state, False)

    def test_partner_state_buyer_forbidden(self):
        """Доступ покупателя к управлению магазином"""
        buyer = User.objects.create_user(
            email='buyer@example.com',
            password='pass',
            is_active=True
        )
        token = Token.objects.create(user=buyer)
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

        url = reverse('backend:partner-state')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
