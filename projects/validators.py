from django.core.validators import URLValidator
from django.core.exceptions import ValidationError
import re


def validate_github_url(link: str) -> None:
    """
    Валидация ссылки на GitHub репозиторий.
    Проверяет, что ссылка ведет на проект (репозиторий) на GitHub.
    """
    # Разрешенные паттерны для GitHub репозиториев
    allowed_patterns = [
        r'^https://github\.com/[\w\-\.]+/[\w\-\.]+/?$',  # https://github.com/user/repo
        r'^https://www\.github\.com/[\w\-\.]+/[\w\-\.]+/?$',  # https://www.github.com/user/repo
        r'^http://github\.com/[\w\-\.]+/[\w\-\.]+/?$',  # http://github.com/user/repo
        r'^http://www\.github\.com/[\w\-\.]+/[\w\-\.]+/?$',  # http://www.github.com/user/repo
    ]

    # Проверка валидности URL
    validator = URLValidator()
    try:
        validator(link)
    except Exception:
        raise ValidationError('Ссылка не является валидной.')

    # Проверка, что ссылка ведет на GitHub репозиторий
    is_github_repo = any(re.match(pattern, link)
                         for pattern in allowed_patterns)

    if not is_github_repo:
        raise ValidationError(
            'Ссылка должна вести на GitHub репозиторий. '
            'Пример: https://github.com/username/repository'
        )
