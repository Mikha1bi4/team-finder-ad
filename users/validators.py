from django.core.exceptions import ValidationError
import re
from .models import User
from django.core.validators import URLValidator


def validate_phone_number(phone: str) -> None:
    if not phone.startswith('+7') and not phone.startswith('8'):
        raise ValidationError(
            'Номер должен начинаться с +7 или 8.'
        )

    if phone.startswith('8'):
        phone = '+7' + phone[1:]

    if not re.fullmatch(r'^\+7\d{10}$', phone):
        raise ValidationError(
                    'Номер должен состоять только из цифр.'
                )

    if User.objects.filter(phone=phone).exists():
        raise ValidationError(
                        'Данный номер уже используется другим пользователем'
                    )


def validate_github_url(link: str) -> None:

    allowed_patterns = [
        r'^https://github\.com/[\w\-\.]+/?$',
        r'^https://www\.github\.com/[\w\-\.]+/?$',
        r'^http://github\.com/[\w\-\.]+/?$',
        r'^http://www\.github\.com/[\w\-\.]+/?$',
    ]

    validator = URLValidator()
    try:
        validator(link)
    except ValidationError:
        raise ValidationError(
                        'Ссылка не является валидной.'
                    )

    is_github = any(re.match(pattern, link) for pattern in allowed_patterns)

    if not is_github:
        raise ValidationError(
                        'Ссылка не ведет на GitHub.'
                    )
