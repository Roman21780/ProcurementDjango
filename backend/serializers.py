from rest_framework import serializers
from backend.models import (
    User, Category, Shop, ProductInfo, Product,
    ProductParameter, OrderItem, Order, Contact
)


class ContactSerializer(serializers.ModelSerializer):
    """Сериализатор для контактов пользователя"""

    class Meta:
        model = Contact
        fields = ('id', 'city', 'street', 'house', 'structure', 'building', 'apartment', 'user', 'phone')
        read_only_fields = ('id',)
        extra_kwargs = {
            'user': {'write_only': True}
        }


class UserSerializer(serializers.ModelSerializer):
    """Сериализатор для пользователей"""
    contacts = ContactSerializer(many=True, read_only=True)

    class Meta:
        fields = ('id', 'first_name', 'last_name', 'email', 'company', 'position', 'contacts')
        read_only_fields = ('id',)


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
    """Сериализатор для позиций заказа"""

    class Meta:
        model = OrderItem
        fields = ('id', 'product_info', 'quantity', 'order',)
        read_only_fields = ('id',)
        extra_kwargs = {
            'order': {'write_only': True}
        }


class OrderItemCreateSerializer(OrderItemSerializer):
    """Сериализатор для создания позиций заказа"""
    product_info = ProductInfoSerializer(read_only=True)


class OrderSerializer(serializers.ModelSerializer):
    """Сериализатор для заказов"""
    ordered_items = OrderItemCreateSerializer(many=True, read_only=True)
    total_sum = serializers.IntegerField()
    contact = ContactSerializer(read_only=True)

    class Meta:
        model = Order
        fields = ('id', 'ordered_items', 'state', 'dt', 'total_sum', 'contact',)
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
