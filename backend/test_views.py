from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from backend.models import (
    Shop, Category, Product, ProductInfo, Order,
    OrderItem, Contact, ConfirmEmailToken, Parameter, ProductParameter
)
from rest_framework.authtoken.models import Token
from django.core.files.uploadedfile import SimpleUploadedFile
from unittest.mock import patch

User = get_user_model()


class ConfirmAccountTests(APITestCase):
    """Тесты подтверждения email"""

    def setUp(self):
        # Очищаем базу перед каждым тестом
        User.objects.all().delete()
        ConfirmEmailToken.objects.all().delete()

        self.user = User.objects.create_user(
            email='confirm_test@example.com',
            password='TestPass123!',
            first_name='Test',
            last_name='User',
            company='Test Company',
            position='Test Position',
            is_active=False
        )
        self.token = ConfirmEmailToken.objects.create(user=self.user, key='testtoken123')
        self.url = reverse('backend:user-register-confirm')

    def test_confirm_account_success(self):
        """Успешное подтверждение email"""
        data = {
            'email': 'confirm_test@example.com',
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
            'email': 'confirm_test@example.com',
            'token': 'wrongtoken'
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_active)


class ProductInfoViewTests(APITestCase):
    """Тесты поиска товаров"""

    def setUp(self):
        # Очищаем базу
        Category.objects.all().delete()
        Shop.objects.all().delete()
        Product.objects.all().delete()
        ProductInfo.objects.all().delete()

        self.category = Category.objects.create(name='Тестовая категория')
        self.shop_user = User.objects.create_user(
            email='shop_products@example.com',
            password='TestPass123!',
            type='shop'
        )
        self.shop = Shop.objects.create(
            name='Тестовый магазин',
            state=True,
            user=self.shop_user
        )
        self.product = Product.objects.create(
            name='Тестовый товар',
            category=self.category
        )
        self.product_info = ProductInfo.objects.create(
            product=self.product,
            shop=self.shop,
            external_id=1,
            model='Модель 123',
            price=1000,
            price_rrc=1200,
            quantity=10
        )
        self.url = reverse('backend:products')

    def test_list_products(self):
        """Получение списка товаров"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 1)

    def test_filter_by_shop(self):
        """Фильтрация товаров по магазину"""
        response = self.client.get(f"{self.url}?shop_id={self.shop.id}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_filter_by_category(self):
        """Фильтрация товаров по категории"""
        response = self.client.get(f"{self.url}?category_id={self.category.id}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class PartnerStateTests(APITestCase):
    """Тесты управления статусом магазина"""

    def setUp(self):
        User.objects.all().delete()
        Shop.objects.all().delete()
        Token.objects.all().delete()

        self.user = User.objects.create_user(
            email='partner_state@example.com',
            password='TestPass123!',
            first_name='Partner',
            last_name='User',
            company='Partner Company',
            position='Owner',
            type='shop',
            is_active=True
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
        self.assertIn('state', response.data)

    def test_update_shop_state(self):
        """Изменение статуса магазина"""
        data = {'state': 'false'}
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.shop.refresh_from_db()
        self.assertFalse(self.shop.state)

    def test_unauthorized_access(self):
        """Попытка доступа без авторизации"""
        self.client.credentials()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class RegisterAccountTests(APITestCase):
    """Тесты регистрации пользователей"""

    def setUp(self):
        User.objects.all().delete()
        self.url = reverse('backend:user-register')

    def test_register_user_success(self):
        """Успешная регистрация пользователя"""
        valid_data = {
            'first_name': 'NewUser',
            'last_name': 'Test',
            'email': 'newuser@example.com',
            'password': 'TestPass123!',
            'company': 'Test Company',
            'position': 'Test Position',
            'type': 'buyer'
        }
        response = self.client.post(self.url, valid_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(email='newuser@example.com').exists())

    def test_register_existing_email(self):
        """Попытка регистрации с существующим email"""
        # Очищаем БД перед тестом
        User.objects.all().delete()

        User.objects.create_user(
            email='existing@example.com',
            password='TestPass123!',
            first_name='Existing',
            last_name='User',
            company='Company',
            position='Position'
        )

        duplicate_data = {
            'first_name': 'Test',
            'last_name': 'User',
            'email': 'existing@example.com',
            'password': 'TestPass123!',
            'company': 'Test Company',
            'position': 'Test Position',
            'type': 'buyer'
        }
        response = self.client.post(self.url, duplicate_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Errors', response.data)

    def test_register_invalid_password(self):
        """Попытка регистрации с некорректным паролем"""
        invalid_data = {
            'first_name': 'Test',
            'last_name': 'User',
            'email': 'invalid_pass@example.com',
            'password': '123',
            'company': 'Test Company',
            'position': 'Test Position',
            'type': 'buyer'
        }
        response = self.client.post(self.url, invalid_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Errors', response.data)


class LoginAccountTests(APITestCase):
    """Тесты авторизации пользователей"""

    def setUp(self):
        User.objects.all().delete()
        self.url = reverse('backend:user-login')
        self.user = User.objects.create_user(
            email='login_test@example.com',
            password='TestPass123!',
            first_name='Login',
            last_name='Test',
            company='Company',
            position='Position',
            is_active=True
        )

    def test_login_success(self):
        """Успешная авторизация"""
        data = {
            'email': 'login_test@example.com',
            'password': 'TestPass123!'
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('Token', response.data)

    def test_login_invalid_credentials(self):
        """Попытка входа с неверными учетными данными"""
        data = {
            'email': 'login_test@example.com',
            'password': 'WrongPass123!'
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn('Errors', response.data)


class AccountDetailsTests(APITestCase):
    """Тесты управления данными пользователя"""

    def setUp(self):
        User.objects.all().delete()
        Token.objects.all().delete()

        self.user = User.objects.create_user(
            email='details_test@example.com',
            password='TestPass123!',
            first_name='Details',
            last_name='User',
            company='Old Company',
            position='Old Position',
            is_active=True
        )
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        self.url = reverse('backend:user-details')

    def test_get_account_details(self):
        """Получение данных пользователя"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], 'details_test@example.com')

    def test_update_account_details(self):
        """Обновление данных пользователя"""
        data = {
            'first_name': 'Updated',
            'company': 'New Company',
            'position': 'New Position'
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'Updated')
        self.assertEqual(self.user.company, 'New Company')


class OrderViewTests(APITestCase):
    """Тесты работы с заказами"""

    def setUp(self):
        # Очищаем базу
        User.objects.all().delete()
        Token.objects.all().delete()
        Category.objects.all().delete()
        Shop.objects.all().delete()
        Product.objects.all().delete()
        ProductInfo.objects.all().delete()
        Contact.objects.all().delete()
        Order.objects.all().delete()

        # Создаем пользователя
        self.user = User.objects.create_user(
            email='order_user@example.com',
            password='TestPass123!',
            first_name='Order',
            last_name='User',
            company='Company',
            position='Position',
            is_active=True
        )
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')

        # Создаем тестовые данные
        self.category = Category.objects.create(name='Test Category')
        self.shop_user = User.objects.create_user(
            email='order_shop@example.com',
            password='TestPass123!',
            type='shop'
        )
        self.shop = Shop.objects.create(
            name='Test Shop',
            state=True,
            user=self.shop_user
        )
        self.product = Product.objects.create(
            name='Test Product',
            category=self.category
        )
        self.product_info = ProductInfo.objects.create(
            product=self.product,
            shop=self.shop,
            external_id=1,
            model='Model X',
            price=1000,
            price_rrc=1200,
            quantity=10
        )
        self.contact = Contact.objects.create(
            user=self.user,
            city='Test City',
            street='Test Street',
            phone='+79991234567'
        )
        self.url = reverse('backend:order')

    def test_create_order(self):
        """Создание заказа"""
        # Создаем корзину
        basket_url = reverse('backend:basket')
        basket_data = {
            'items': json.dumps([{
                'product_info': self.product_info.id,
                'quantity': 2
            }])
        }
        self.client.post(basket_url, basket_data, format='json')

        # Создаем заказ
        order_data = {
            'id': Order.objects.filter(user=self.user, state='basket').first().id,
            'contact': self.contact.id
        }
        response = self.client.post(self.url, order_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Order.objects.filter(user=self.user, state='new').exists())

    def test_get_orders_list(self):
        """Получение списка заказов"""
        # Создаем тестовый заказ
        order = Order.objects.create(
            user=self.user,
            contact=self.contact,
            state='new'
        )
        OrderItem.objects.create(
            order=order,
            product_info=self.product_info,
            quantity=1
        )

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreater(len(response.data), 0)


class PartnerOrdersTests(APITestCase):
    """Тесты заказов поставщика"""

    def setUp(self):
        # Очищаем базу
        User.objects.all().delete()
        Token.objects.all().delete()
        Shop.objects.all().delete()
        Category.objects.all().delete()
        Product.objects.all().delete()
        ProductInfo.objects.all().delete()
        Contact.objects.all().delete()
        Order.objects.all().delete()

        # Создаем пользователя-поставщика
        self.shop_user = User.objects.create_user(
            email='partner_orders@example.com',
            password='TestPass123!',
            first_name='Shop',
            last_name='Owner',
            company='Shop Company',
            position='Owner',
            type='shop',
            is_active=True
        )
        self.shop = Shop.objects.create(
            name='Test Shop',
            user=self.shop_user,
            state=True
        )
        self.token = Token.objects.create(user=self.shop_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')

        # Создаем покупателя и его заказ
        self.buyer = User.objects.create_user(
            email='partner_buyer@example.com',
            password='TestPass123!',
            first_name='Buyer',
            last_name='Test',
            company='Buyer Company',
            position='Manager'
        )
        self.category = Category.objects.create(name='Test Category')
        self.product = Product.objects.create(
            name='Test Product',
            category=self.category
        )
        self.product_info = ProductInfo.objects.create(
            product=self.product,
            shop=self.shop,
            external_id=1,
            model='Model X',
            price=1000,
            price_rrc=1200,
            quantity=10
        )
        self.contact = Contact.objects.create(
            user=self.buyer,
            city='Test City',
            street='Test Street',
            phone='+79991234567'
        )
        self.order = Order.objects.create(
            user=self.buyer,
            contact=self.contact,
            state='new'
        )
        self.order_item = OrderItem.objects.create(
            order=self.order,
            product_info=self.product_info,
            quantity=2
        )
        self.url = reverse('backend:partner-orders')

    def test_get_partner_orders(self):
        """Получение списка заказов поставщика"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreater(len(response.data), 0)

    def test_unauthorized_access(self):
        """Попытка доступа без авторизации"""
        self.client.credentials()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class ContactViewTests(APITestCase):
    """Тесты управления контактами"""

    def setUp(self):
        User.objects.all().delete()
        Token.objects.all().delete()
        Contact.objects.all().delete()

        self.user = User.objects.create_user(
            email='contact_user@example.com',
            password='TestPass123!',
            first_name='Contact',
            last_name='User',
            company='Company',
            position='Position',
            is_active=True
        )
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        self.url = reverse('backend:user-contact')

        # Тестовые данные контакта
        self.contact_data = {
            'city': 'Test City',
            'street': 'Test Street',
            'house': '123',
            'structure': '1',
            'building': 'A',
            'apartment': '45',
            'phone': '+79991234567'
        }

    def test_create_contact(self):
        """Создание контакта"""
        response = self.client.post(self.url, self.contact_data, format='json')
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_201_CREATED])
        self.assertTrue(Contact.objects.filter(user=self.user).exists())

    def test_get_contacts(self):
        """Получение списка контактов"""
        # Создаем тестовый контакт
        Contact.objects.create(user=self.user, **self.contact_data)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreater(len(response.data), 0)

    def test_delete_contacts(self):
        """Удаление контактов"""
        # Создаем тестовый контакт
        contact = Contact.objects.create(user=self.user, **self.contact_data)

        # Удаляем контакт
        response = self.client.delete(self.url, {'items': str(contact.id)}, format='json')
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_204_NO_CONTENT])
        self.assertFalse(Contact.objects.filter(id=contact.id).exists())


class UploadAvatarTests(APITestCase):
    """Тесты загрузки аватара пользователя"""

    def setUp(self):
        User.objects.all().delete()
        Token.objects.all().delete()

        self.user = User.objects.create_user(
            email='avatar_user@example.com',
            password='TestPass123!',
            first_name='Avatar',
            last_name='User',
            company='Company',
            position='Position',
            is_active=True
        )
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        self.url = reverse('backend:upload-avatar')

    def test_upload_avatar(self):
        """Успешная загрузка аватара"""
        # Создаем тестовый файл
        image = SimpleUploadedFile(
            name='test.jpg',
            content=b'fake image content',
            content_type='image/jpeg'
        )

        response = self.client.post(self.url, {'avatar': image}, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['Status'])

    def test_upload_invalid_file(self):
        """Попытка загрузки невалидного файла"""
        # Создаем текстовый файл вместо изображения
        text_file = SimpleUploadedFile(
            name='test.txt',
            content=b'not an image',
            content_type='text/plain'
        )

        response = self.client.post(self.url, {'avatar': text_file}, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Error', response.data)


import json
