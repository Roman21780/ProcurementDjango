from django.core.management.base import BaseCommand
from django.core.cache import cache
from cacheops import invalidate_all


class Command(BaseCommand):
    help = 'Очистка кэша Redis'

    def add_arguments(self, parser):
        parser.add_argument(
            '--all',
            action='store_true',
            help='Очистить весь кэш',
        )
        parser.add_argument(
            '--model',
            type=str,
            help='Очистить кэш для модели (например: backend.Product)',
        )

    def handle(self, *args, **options):
        if options['all']:
            cache.clear()
            invalidate_all()
            self.stdout.write(self.style.SUCCESS('✅ Весь кэш очищен!'))
        elif options['model']:
            from django.apps import apps
            try:
                app_label, model_name = options['model'].split('.')
                model = apps.get_model(app_label, model_name)
                from cacheops import invalidate_model
                invalidate_model(model)
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Кэш для {model_name} очищен!')
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'❌ Ошибка: {str(e)}')
                )
        else:
            self.stdout.write(
                self.style.WARNING('⚠️  Укажите --all или --model')
            )
