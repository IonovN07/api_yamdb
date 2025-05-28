import re

from django.conf import settings
from django.core.exceptions import ValidationError


def validate_username_value(value):
    if value == settings.RESERVED_NAME:
        raise ValidationError(
            f'Имя "{settings.RESERVED_NAME}" не разрешено.'
        )

    invalid_chars = re.sub(settings.USERNAME_REGEX, '', value)

    if invalid_chars:
        unique_invalids = ' '.join(dict.fromkeys(invalid_chars))
        raise ValidationError(
            f'Имя содержит недопустимые символы: {unique_invalids}'
        )
