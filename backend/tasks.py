from csv import excel

from celery import shared_task
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from django.db.models.expressions import result
from django.template.loader import render_to_string
from requests import get
from yaml import load as load_yaml, Loader
import logging

from backend.models import (
    Shop, Category, Product, ProductInfo, Parameter,
    ProductParameter, User
)

logger = logging.getLogger(__name__)


@shared_task
def send_email_task(email_type, recipient_email, context=None):
    """
    Асинхронная отправка email

    Args:
        email_type: тип письма (registration, order_confirmation, order_status_changed)
        recipient_email: email получателя
        context: дополнительные данные для шаблона
    """
    try:
        if context is None:
            context = {}

        email_templates = {
            'registration': {
                'subject': 'Подтверждение регистрации',
                'template': 'emails/registration_confirmation.html',
            },
            'order_confirmation': {
                'subject': 'Подтверждение заказа',
                'template': 'emails/order_confirmation.html',
            },
            'order_status_changed': {
                'subject': 'Изменение статуса заказа',
                'template': 'emails/order_status_changed.html',
            },
            'password_reset': {
                'subject': 'Сброс пароля',
                'template': 'emails/password_reset.html',
            }
        }

        if email_type not in email_templates:
            logger.error(f"Unknown email type: {email_type}")
            return False

        template_info = email_templates[email_type]

        # Создаем HTML содержимое из шаблона
        html_content = render_to_string(template_info['template'], context)

        # Создаем и отправляем письмо
        msg = EmailMultiAlternatives(
            subject=template_info['subject'],
            body=html_content,
            from_email=settings.EMAIL_HOST_USER,
            to=[recipient_email],
        )
        msg.attach_alternative(html_content, "text/html")

        result = msg.send()

        if result:
            logger.info(f"Email sent successfully to {recipient_email}")
            return True
        else:
            logger.error(f"Failed to send email to {recipient_email}")
            return False

    except Exception as e:
        logger.error(f"Error sending email to {recipient_email}: {str(e)}")
        return False


@shared_task
def import_shop_data_task(url, user_id):
    """
    Асинхронный импорт данных магазина из YAML файла

    Args:
        url: URL файла с данными
        user_id: ID пользователя-поставщика
    """
    try:
        logger.info(f"Starting import from {url} for user {user_id}")

        # Получаем данные по URL
        response = get(url)
        response.raise_for_status()

        # Парсим YAML
        data = load_yaml(response.content, Loader=Loader)

        if not data or 'shop' not in data:
            logger.error("Invalid YAML structure")
            return {'success': False, 'error': 'Invalid YAML structure'}

        # Получаем или создаем магазин
        shop, created = Shop.objects.get_or_create(
            name=data['shop'],
            user_id=user_id
        )

        if created:
            logger.info(f"Created new shop {shop.name}")

        # Обрабатываем категории
        categories_created = 0
        if 'categories' in data:
            for category_data in data['categories']:
                category, created = Category.objects.get_or_create(
                    id=category_data['id'],
                    defaults={'name': category_data['name']}
                )
                category.shops.add(shop.id)
                if created:
                    categories_created += 1

        logger.info(f"Processed {len(data.get('categories', []))} categories, created {categories_created}")

        # Удаляем старые товары магазина
        old_products_count = ProductInfo.objects.filter(shop_id=shop.id).count()
        ProductInfo.objects.filter(shop_id=shop.id).delete()
        logger.info(f"Removed {old_products_count} old products")

        # Обрабатываем товары
        products_created = 0
        parameters_created = 0

        if 'goods' in data:
            for item in data['goods']:
                try:
                    # Создаем или получаем товар
                    product, created = Product.objects.get_or_create(
                        name=item['name'],
                        category_id=item['category']
                    )

                    # Создаем информацию о товаре
                    product_info = ProductInfo.objects.create(
                        product_id=product.id,
                        external_id=item['id'],
                        model=item.get('model', ''),
                        price=item['price'],
                        price_rrc=item['price_rrc'],
                        quantity=item['quantity'],
                        shop_id=shop.id
                    )
                    products_created += 1

                    # Создаем параметры товара
                    if 'parameters' in item:
                        for param_name, param_value in item['parameters'].items():
                            parameter, _ = Parameter.objects.get_or_create(name=param_name)
                            ProductParameter.objects.create(
                                product_info_id=product_info.id,
                                parameter_id=parameter.id,
                                value=str(param_value)
                            )
                            parameters_created += 1

                except Exception as e:
                    logger.error(f"Error processing item {item.get('id')}: {str(e)}")
                    continue

        logger.info(f"Import completed: {products_created} products, {parameters_created} parameters")

        # Отправляем уведомление об успешном импорте
        user = User.objects.get(id=user_id)
        send_email_task.delay(
            'import_completed',
            user.email,
            {
                'shop_name': shop.name,
                'products_count': products_created,
                'categories_count': categories_created
            }
        )

        return {
            'success': True,
            'products_created': products_created,
            'categories_created': categories_created,
            'parameters_created': parameters_created
        }

    except Exception as e:
        logger.error(f"Import failed for user {user_id}: {str(e)}")

        # Отправляем уведомление об ошибке
        try:
            user = User.objects.get(id=user_id)
            send_email_task.delay(
                'import_failed',
                user.email,
                {'error': str(e)}
            )
        except:
            pass

        return {'success': False, 'error': str(e)}


@shared_task
def export_products_task(shop_id, user_id):
    """
    Асинхронный экспорт товаров магазина в YAML формат

    Args:
        shop_id: ID магазина
        user_id: ID пользователя
    """


@shared_task
def cleanup_old_tokens_task():
    """
    Очистка старых токенов подтверждения email (запускается по расписанию)
    """


@shared_task
def send_order_notifications_task(order_id):
    """
    Отправка уведомлений о новом заказе

    Args:
        order_id: ID заказа
    """




