import os
from django.core.management.base import BaseCommand
from yaml import load as load_yaml, Loader
from django.db import transaction
from django.db.models import Count

from backend.models import (
    User, Shop, Category, Product, ProductInfo,
    Parameter, ProductParameter
)


class Command(BaseCommand):
    help = 'Полная перезагрузка данных магазина из YAML: удаляет старое и загружает новое'

    def add_arguments(self, parser):
        parser.add_argument(
            'file_path',
            type=str,
            help='/app/data/shop1.yaml'
        )

    def handle(self, *args, **options):
        file_path = options['file_path']

        if not os.path.exists(file_path):
            self.stdout.write(self.style.ERROR(f'Файл {file_path} не найден'))
            return

        with open(file_path, 'r', encoding='utf-8') as f:
            data = load_yaml(f.read(), Loader=Loader)

        shop_email = data.get('shop_email', 'shop@example.com')
        shop_name = data.get('shop', 'Unnamed Shop')

        try:
            with transaction.atomic():
                # Удаляем существующего поставщика и магазин
                existing_user = User.objects.filter(email=shop_email, type='shop').first()
                if existing_user:
                    self.stdout.write(f'Удаляем существующего поставщика {shop_email} и его магазин...')
                    Shop.objects.filter(user=existing_user).delete()
                    existing_user.delete()

                # Создаём пользователя-поставщика
                user = User.objects.create_user(
                    email=shop_email,
                    password=data.get('shop_password', 'password'),
                    first_name=shop_name,
                    last_name='Owner',
                    type='shop',
                    is_active=True
                )
                self.stdout.write(f'Создан пользователь-поставщик ID={user.id}')

                # Создаём магазин
                shop = Shop.objects.create(
                    name=shop_name,
                    user=user,
                    state=True
                )
                self.stdout.write(f'Создан магазин ID={shop.id}')

                # Загружаем категории и привязываем к магазину
                categories_created = 0
                for c in data.get('categories', []):
                    category, created = Category.objects.get_or_create(
                        id=c['id'],
                        defaults={'name': c['name']}
                    )
                    category.shops.add(shop)
                    if created:
                        categories_created += 1

                # Удаляем старые ProductInfo для магазина
                old_infos = ProductInfo.objects.filter(shop=shop)
                old_product_ids = list(old_infos.values_list('product_id', flat=True))
                deleted_infos = old_infos.delete()[0]
                self.stdout.write(f'Удалено ProductInfo: {deleted_infos}')

                # Удаляем «осиротевшие» товары без связей
                orphan_products = (
                    Product.objects
                    .filter(id__in=old_product_ids)
                    .annotate(info_count=Count('product_infos'))
                    .filter(info_count=0)
                )
                orphan_count = orphan_products.count()
                orphan_products.delete()
                self.stdout.write(f'Удалено орфанных товаров: {orphan_count}')

                # Загружаем товары и параметры из YAML
                products_created = 0
                for item in data.get('goods', []):
                    product, _ = Product.objects.get_or_create(
                        name=item['name'],
                        category_id=item['category']
                    )

                    info = ProductInfo.objects.create(
                        product=product,
                        external_id=item['id'],
                        model=item.get('model', ''),
                        price=item['price'],
                        price_rrc=item['price_rrc'],
                        quantity=item['quantity'],
                        shop=shop
                    )
                    products_created += 1

                    for pname, pval in item.get('parameters', {}).items():
                        parameter, _ = Parameter.objects.get_or_create(name=pname)
                        ProductParameter.objects.create(
                            product_info=info,
                            parameter=parameter,
                            value=str(pval)
                        )

                self.stdout.write(self.style.SUCCESS(
                    f'Загружено: {categories_created} категорий, {products_created} товаров'
                ))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Ошибка: {e}'))