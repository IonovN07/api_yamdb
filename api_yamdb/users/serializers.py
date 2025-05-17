from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from rest_framework import serializers

User = get_user_model()


def validate_reserved_username(value):
    if value.lower() == 'me':
        raise serializers.ValidationError("Имя 'me' не разрешено.")
    return value


class BaseUserSerializer(serializers.ModelSerializer):
    username = serializers.RegexField(
        required=True,
        max_length=150,
        regex=r'^[\w.@+-]+\Z'
    )
    email = serializers.EmailField(
        required=True,
        max_length=254
    )

    def validate_username(self, value):
        validate_reserved_username(value)

        request = self.context.get('request')
        instance = self.instance

        if request and request.method == 'PATCH' and request.user.is_admin:
            if instance and value == instance.username:
                return value

        qs = User.objects.filter(username=value)
        if instance:
            qs = qs.exclude(pk=instance.pk)
        if qs.exists():
            raise serializers.ValidationError("Такой username уже существует.")
        return value

    def validate_email(self, value):
        request = self.context.get('request')
        instance = self.instance

        if request and request.method == 'PATCH' and request.user.is_admin:
            if instance and value == instance.email:
                return value

        qs = User.objects.filter(email=value)
        if instance:
            qs = qs.exclude(pk=instance.pk)
        if qs.exists():
            raise serializers.ValidationError("Такой email уже используется.")
        return value

    class Meta:
        model = User
        fields = ('username', 'email')


class SignUpSerializer(serializers.Serializer):
    username = serializers.RegexField(
        required=True,
        max_length=150,
        regex=r'^[\w.@+-]+\Z'
    )
    email = serializers.EmailField(
        required=True,
        max_length=254
    )

    def validate_username(self, value):
        return validate_reserved_username(value)


class UserSerializer(BaseUserSerializer):
    class Meta(BaseUserSerializer.Meta):
        fields = BaseUserSerializer.Meta.fields + (
            'first_name', 'last_name', 'bio', 'role'
        )


class UserProfileSerializer(UserSerializer):
    role = serializers.CharField(read_only=True)


class TokenSerializer(serializers.Serializer):
    username = serializers.RegexField(
        required=True,
        max_length=150,
        regex=r'^[\w.@+-]+\Z'
    )
    confirmation_code = serializers.CharField(required=True)

    def validate_username(self, value):
        return validate_reserved_username(value)

    def validate(self, data):
        user = get_object_or_404(User, username=data['username'])
        if user.confirmation_code != data['confirmation_code']:
            raise serializers.ValidationError('Неверный код подтверждения.')
        data['user'] = user
        return data
