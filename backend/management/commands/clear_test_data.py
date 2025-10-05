from django.core.management.base import BaseCommand
from django.db import transaction
from backend.models import User, Shop, Order, OrderItem, Contact, ConfirmEmailToken
from rest_framework.authtoken.models import Token


class Command(BaseCommand):
    help = 'Очистка тестовых данных (пользователи, заказы, контакты)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--keep-superuser',
            action='store_true',
            help='Сохранить суперпользователя',
        )

    def handle(self, *args, **options):
        try:
            with transaction.atomic():
                def get_deleted_count(delete_result):
                    if isinstance(delete_result, tuple):
                        return delete_result[0]
                    return delete_result

                # Удаляем токены подтверждения email
                deleted_tokens = ConfirmEmailToken.objects.all().delete()
                count = get_deleted_count(deleted_tokens)
                self.stdout.write(f"Удалено токенов подтверждения: {count}")

                # Удаляем токены авторизации
                deleted_auth_tokens = Token.objects.all().delete()
                count = get_deleted_count(deleted_auth_tokens)
                self.stdout.write(f"Удалено токенов авторизации: {count}")

                # Удаляем заказы
                deleted_orders = Order.objects.all().delete()
                count = get_deleted_count(deleted_orders)
                self.stdout.write(f"Удалено заказов: {count}")

                # Удаляем контакты
                deleted_contacts = Contact.objects.all().delete()
                count = get_deleted_count(deleted_contacts)
                self.stdout.write(f"Удалено контактов: {count}")

                # НЕ удаляем магазины - они нужны для товаров из YAML

                # Удаляем пользователей, НО сохраняем:
                # 1. Суперпользователя (если указано)
                # 2. Пользователя-поставщика с email shop@example.com
                exclude_emails = ['shop@example.com']  # Пользователь из YAML

                if options['keep_superuser']:
                    # Удаляем всех кроме суперпользователя и поставщика YAML
                    deleted_users = User.objects.filter(
                        is_superuser=False
                    ).exclude(email__in=exclude_emails).delete()
                    count = get_deleted_count(deleted_users)
                    self.stdout.write(f"Удалено пользователей (кроме суперпользователя и поставщика YAML): {count}")
                else:
                    # Удаляем всех кроме поставщика YAML
                    deleted_users = User.objects.exclude(email__in=exclude_emails).delete()
                    count = get_deleted_count(deleted_users)
                    self.stdout.write(f"Удалено пользователей (кроме поставщика YAML): {count}")

                self.stdout.write(
                    self.style.SUCCESS('Очистка данных завершена успешно!')
                )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Ошибка при очистке данных: {str(e)}')
            )
