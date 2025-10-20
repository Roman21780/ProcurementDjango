from django.core.management.base import BaseCommand
from django.db import connection, reset_queries
from django.test.utils import override_settings
import time
from backend.models import ProductInfo


class Command(BaseCommand):
    help = 'Тестирование производительности'

    @override_settings(DEBUG=True)
    def handle(self, *args, **options):
        self.stdout.write('🚀 Тестирование производительности...\n')

        # Тест 1: Без оптимизации
        self.stdout.write('❌ Без оптимизации (N+1):')
        reset_queries()
        start = time.time()

        products = ProductInfo.objects.all()[:50]
        for p in products:
            _ = p.product.name
            _ = p.shop.name
            _ = list(p.product_parameters.all())

        duration_bad = time.time() - start
        queries_bad = len(connection.queries)

        # Тест 2: С оптимизацией
        self.stdout.write('\n✅ С оптимизацией (select_related + prefetch):')
        reset_queries()
        start = time.time()

        products = ProductInfo.objects.select_related(
            'product', 'shop', 'product__category'
        ).prefetch_related(
            'product_parameters__parameter'
        ).all()[:50]

        for p in products:
            _ = p.product.name
            _ = p.shop.name
            _ = list(p.product_parameters.all())

        duration_good = time.time() - start
        queries_good = len(connection.queries)

        # Результаты
        self.stdout.write('\n' + '=' * 60)
        self.stdout.write('📊 РЕЗУЛЬТАТЫ:')
        self.stdout.write('=' * 60)

        self.stdout.write(f'\n❌ Без оптимизации:')
        self.stdout.write(f'   Время: {duration_bad:.3f} сек')
        self.stdout.write(f'   SQL запросов: {queries_bad}')

        self.stdout.write(f'\n✅ С оптимизацией:')
        self.stdout.write(f'   Время: {duration_good:.3f} сек')
        self.stdout.write(f'   SQL запросов: {queries_good}')

        improvement_time = (1 - duration_good / duration_bad) * 100
        improvement_queries = queries_bad - queries_good

        self.stdout.write(f'\n🎯 УЛУЧШЕНИЕ:')
        self.stdout.write(
            self.style.SUCCESS(
                f'   ⚡ Время: {improvement_time:.1f}% быстрее'
            )
        )
        self.stdout.write(
            self.style.SUCCESS(
                f'   📉 Запросов: сокращено на {improvement_queries}'
            )
        )
