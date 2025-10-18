from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from backend.models import (
    User, Shop, Category, Product, ProductInfo,
    Contact, Order, OrderItem, Parameter, ProductParameter
)
from rest_framework.authtoken.models import Token
import json


class UserRegistrationTests(APITestCase):
    """Тесты регистрации пользователей"""

    def test_register_buyer_success(self):
        """Успешная регистрация покупателя"""
        url = reverse('backend:user-register')
        data = {
            'first_name': 'Ivan',
            'last_name': 'Petrov',
            'email': 'ivan@example.com',
            'password': 'SecurePass123!',
            'company': 'Test Company',
            'position': 'Manager',
            'type': 'buyer'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(email='ivan@example.com').exists())
        user = User.objects.get(email='ivan@example.com')
        self.assertEqual(user.type, 'buyer')

    def test_register_shop_success(self):
        """Успешная регистрация магазина"""
        url = reverse('backend:user-register')
        data = {
            'first_name': 'Shop',
            'last_name': 'Owner',
            'email': 'shop@example.com',
            'password': 'ShopPass123!',
            'company': 'My Shop',
            'position': 'Director',
            'type': 'shop'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(email='shop@example.com').exists())
        self.assertTrue(Shop.objects.filter(user__email='shop@example.com').exists())

    def test_register_missing_fields(self):
        """Регистрация без обязательных полей"""
        url = reverse('backend:user-register')
        data = {'email': 'test@example.com'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_weak_password(self):
        """Регистрация со слабым паролем"""
        url = reverse('backend:user-register')
        data = {
            'first_name': 'Test',
            'last_name': 'User',
            'email': 'weak@example.com',
            'password': '123',
            'company': 'Test',
            'position': 'Manager'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class LoginTests(APITestCase):
    """Тесты авторизации"""

    def setUp(self):
        self.user = User.objects.create_user(
            email='login@example.com',
            password='TestPass123!',
            first_name='Test',
            last_name='User',
            is_active=True
        )

    def test_login_success(self):
        """Успешная авторизация"""
        url = reverse('backend:user-login')
        data = {'email': 'login@example.com', 'password': 'TestPass123!'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('Token', response.data)
        self.assertTrue(Token.objects.filter(user=self.user).exists())

    def test_login_wrong_password(self):
        """Авторизация с неправильным паролем"""
        url = reverse('backend:user-login')
        data = {'email': 'login@example.com', 'password': 'WrongPassword'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_nonexistent_user(self):
        """Авторизация несуществующего пользователя"""
        url = reverse('backend:user-login')
        data = {'email': 'ghost@example.com', 'password': 'Pass123!'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_missing_fields(self):
        """Авторизация без email или пароля"""
        url = reverse('backend:user-login')
        data = {'email': 'login@example.com'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class AccountDetailsTests(APITestCase):
    """Тесты управления данными пользователя"""

    def setUp(self):
        self.user = User.objects.create_user(
            email='user@example.com',
            password='Pass123!',
            first_name='John',
            last_name='Doe',
            company='Test Corp',
            position='Developer',
            is_active=True
        )
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)

    def test_get_account_details(self):
        """Получение данных аккаунта"""
        url = reverse('backend:user-details')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], 'user@example.com')

    def test_update_account_details(self):
        """Обновление данных аккаунта"""
        url = reverse('backend:user-details')
        data = {'first_name': 'Jane', 'company': 'New Corp'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'Jane')

    def test_get_account_unauthorized(self):
        """Получение данных без авторизации"""
        self.client.credentials()
        url = reverse('backend:user-details')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class CategoryTests(APITestCase):
    """Тесты категорий товаров"""

    def setUp(self):
        Category.objects.create(id=1, name='Electronics')
        Category.objects.create(id=2, name='Books')
        Category.objects.create(id=3, name='Clothing')

    def test_list_categories(self):
        """Получение списка категорий"""
        url = reverse('backend:categories')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)

    def test_category_names(self):
        """Проверка имён категорий"""
        url = reverse('backend:categories')
        response = self.client.get(url)
        names = [cat['name'] for cat in response.data]
        self.assertIn('Electronics', names)
        self.assertIn('Books', names)


class ShopTests(APITestCase):
    """Тесты магазинов"""

    def setUp(self):
        user1 = User.objects.create_user(
            email='shop1@example.com',
            password='pass',
            type='shop',
            is_active=True
        )
        user2 = User.objects.create_user(
            email='shop2@example.com',
            password='pass',
            type='shop',
            is_active=True
        )
        Shop.objects.create(user=user1, name='Shop 1', state=True)
        Shop.objects.create(user=user2, name='Shop 2', state=False)

    def test_list_active_shops(self):
        """Получение списка активных магазинов"""
        url = reverse('backend:shops')
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
