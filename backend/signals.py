from typing import Type
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.db.models.signals import post_save
from django.dispatch import receiver, Signal
from django_rest_passwordreset.signals import reset_password_token_created

from backend.models import ConfirmEmailToken, User, Order
from backend.tasks import send_email_task, send_order_notifications_task


# Пользовательские сигналы
new_user_registered = Signal()
new_order = Signal()


@receiver(reset_password_token_created)
def password_reset_token_created(sender, instance, reset_password_token, **kwargs):
    """
    Отправляем письмо с токеном для сброса пароля
    """
    send_email_task.delay(
        'password_reset',
        reset_password_token.user.email,
        {'token': reset_password_token.key}
    )


@receiver(post_save, sender=User)
def new_user_registered_signal(sender: Type[User], instance: User, created: bool, **kwargs):
    """
    Отправляем письмо с подтверждением почты при регистрации
    """
    if created and not instance.is_active:
        # Создаем токен подтверждения
        token, _ = ConfirmEmailToken.objects.get_or_create(user_id=instance.pk)

        # Отправляем письмо асинхронно
        send_email_task.delay(
            'registration',
            instance.email,
            {
                'user': instance,
                'token': token.key
            }
        )


@receiver(new_order)
def new_order_signal(user_id, order_id=None, **kwargs):
    """
    Отправляем письма при создании нового заказа
    """
    if order_id:
        # Запускаем асинхронную задачу отправки уведомлений
        send_order_notifications_task.delay(order_id)
