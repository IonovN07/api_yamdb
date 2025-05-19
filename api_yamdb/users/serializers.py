from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework import serializers

User = get_user_model()


def validate_reserved_username(username: str):
    if username == settings.RESERVED_NAME:
        raise serializers.ValidationError('Имя \'me\' не разрешено.')
    return username


class UserSerializer(serializers.ModelSerializer):
    username = serializers.RegexField(
        regex=settings.USERNAME_REGEX,
        max_length=settings.USERNAME_MAX_LENGTH,
        required=True,
    )
    email = serializers.EmailField(
        max_length=settings.EMAIL_MAX_LENGTH,
        required=True,
    )

    def validate_username(self, username):
        username = validate_reserved_username(username)
        qs = User.objects.filter(username=username)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError('Такой username уже существует.')
        return username

    def validate_email(self, email):
        qs = User.objects.filter(email=email)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError('Этот email уже используется.')
        return email

    class Meta:
        model = User
        fields = (
            'username', 'email',
            'first_name', 'last_name',
            'bio', 'role',
        )


class UserProfileSerializer(UserSerializer):
    class Meta(UserSerializer.Meta):
        read_only_fields = ('role',)


class SignUpSerializer(serializers.Serializer):
    username = serializers.RegexField(
        regex=settings.USERNAME_REGEX,
        max_length=settings.USERNAME_MAX_LENGTH,
        required=True,
    )
    email = serializers.EmailField(
        max_length=settings.EMAIL_MAX_LENGTH,
        required=True,
    )

    def validate_username(self, username):
        return validate_reserved_username(username)


class TokenSerializer(serializers.Serializer):
    username = serializers.RegexField(
        regex=settings.USERNAME_REGEX,
        max_length=settings.USERNAME_MAX_LENGTH,
        required=True,
    )
    confirmation_code = serializers.CharField(
        required=True,
        max_length=settings.CONFIRMATION_CODE_LENGTH,
    )

    def validate_username(self, username):
        return validate_reserved_username(username)
