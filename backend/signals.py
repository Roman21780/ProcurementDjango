from typing import Type
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver, Signal
from django_rest_passwordreset.signals import reset_password_token_created

from backend.models import ConfirmEmailToken, User, Order, ProductInfo
from backend.tasks import send_email_task, send_order_notifications_task, process_user_avatar, process_product_image
import os


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

        # Отправляем письмо асинхронно (delay), синхронно - без delay
        send_email_task.delay(
            'registration',
            instance.email,
            {
                'first_name': instance.first_name,
                'last_name': instance.last_name,
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


@receiver(post_save, sender=User)
def user_avatar_handler(sender, instance, created, **kwargs):
    """
    Обработка аватара пользователя после сохранения
    """
    if instance.avatar and not created:
        # Запускаем асинхронную обработку
        process_user_avatar.delay(instance.id)


@receiver(post_save, sender=ProductInfo)
def product_image_handler(sender, instance, created, **kwargs):
    """
    Обработка изображения товара после сохранения
    """
    if instance.image:
        # Запускаем асинхронную обработку
        process_product_image.delay(instance.id)


@receiver(pre_delete, sender=User)
def delete_user_avatar(sender, instance, **kwargs):
    """
    Удаление файла аватара при удалении пользователя
    """
    if instance.avatar:
        if os.path.isfile(instance.avatar.path):
            os.remove(instance.avatar.path)


@receiver(pre_delete, sender=ProductInfo)
def delete_product_image(sender, instance, **kwargs):
    """
    Удаление файла изображения при удалении товара
    """
    if instance.image:
        if os.path.isfile(instance.image.path):
            os.remove(instance.image.path)
