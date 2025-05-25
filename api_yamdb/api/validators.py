import re

from django.conf import settings
from django.core.exceptions import ValidationError


def validate_username_value(value):
    if value == settings.RESERVED_NAME:
        raise ValidationError(
            f'Имя "{settings.RESERVED_NAME}" не разрешено.'
        )

    if not re.match(settings.USERNAME_REGEX, value):
        raise ValidationError(
            'Введите корректное имя. Разрешены буквы, цифры и ./@/+/-.'
        )


class UsernameValidatorMixin:
    def validate_username(self, value):
        validate_username_value(value)
        return value
