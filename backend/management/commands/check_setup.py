from django.core.management.base import BaseCommand
from django.core.cache import cache
from django_redis import get_redis_connection
import sentry_sdk


class Command(BaseCommand):
    help = 'Check if all integrations are working'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('=== Checking Integrations ===\n'))

        # 1. Tests
        self.stdout.write('1. Tests: Run `python manage.py test backend`')

        # 2. DRF-Spectacular
        self.stdout.write('2. DRF-Spectacular: http://localhost/api/docs/')

        # 3. Social Auth
        self.stdout.write('3. Social Auth: Check settings.AUTHENTICATION_BACKENDS')

        # 4. Django Baton
        self.stdout.write('4. Django Baton: http://localhost/admin/')

        # 5. ImageKit
        self.stdout.write('5. ImageKit: Check MEDIA_ROOT and MEDIA_URL')

        # 6. Sentry
        try:
            sentry_sdk.capture_message('Integration check', level='info')
            self.stdout.write(self.style.SUCCESS('6. Sentry: ✓ Working'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'6. Sentry: ✗ {str(e)}'))

        # 7. Redis Cache
        try:
            cache.set('test_key', 'test_value', 10)
            value = cache.get('test_key')
            if value == 'test_value':
                self.stdout.write(self.style.SUCCESS('7. Redis Cache: ✓ Working'))
            else:
                self.stdout.write(self.style.ERROR('7. Redis Cache: ✗ Not working'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'7. Redis Cache: ✗ {str(e)}'))

        # 8. Silk
        self.stdout.write('8. Silk: http://localhost/silk/')

        self.stdout.write(self.style.SUCCESS('\n=== Check Complete ==='))
