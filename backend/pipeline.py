from rest_framework.authtoken.models import Token


def create_user_profile(backend, user, response, *args, **kwargs):
    """
    Кастомный pipeline для создания профиля пользователя
    и генерации токена при первой авторизации через соц. сети
    """
    if kwargs.get('is_new'):
        # Установите дефолтные значения для новых пользователей
        if not user.first_name and response.get('given_name'):
            user.first_name = response.get('given_name', '')

        if not user.last_name and response.get('family_name'):
            user.last_name = response.get('family_name', '')

        if not user.company:
            user.company = 'Not specified'

        if not user.position:
            user.position = 'User'

        user.is_active = True
        user.save()

        # Создаём токен для API
        Token.objects.get_or_create(user=user)
