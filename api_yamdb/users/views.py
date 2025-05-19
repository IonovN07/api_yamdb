import random

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.shortcuts import get_object_or_404
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import AccessToken

from .models import User
from .permissions import IsAdmin
from .serializers import (SignUpSerializer, TokenSerializer,
                          UserProfileSerializer, UserSerializer)


def generate_confirmation_code():
    return ''.join(str(random.randint(0, 9)) for _ in
                   range(settings.CONFIRMATION_CODE_LENGTH))


def send_confirmation_email(user, confirmation_code):
    subject = 'Код подтверждения YaMDb!'
    from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@yamdb.fake')
    to = [user.email]

    text_content = (
        f'Здравствуйте, {user.username}!\n\n'
        f'Ваш код подтверждения:\n\n{confirmation_code}\n\n'
        'Используйте этот код для получения токена.'
    )
    html_content = f'''
        <html>
            <body>
                <p>Здравствуйте, <strong>{user.username}</strong>!</p>
                <p>Ваш код подтверждения:</p>
                <p><code style="font-size: 1.2em;">{confirmation_code}</code></p>
                <p>Используйте этот код для получения токена.</p>
            </body>
        </html>
    '''

    msg = EmailMultiAlternatives(subject, text_content, from_email, to)
    msg.attach_alternative(html_content, "text/html")
    msg.send()


@api_view(['POST'])
@permission_classes([AllowAny])
def signup(request):
    serializer = SignUpSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    username = serializer.validated_data['username']
    email = serializer.validated_data['email']

    existing_users = list(
        User.objects.filter(username=username) | User.objects.filter(
            email=email))

    if not existing_users:
        user = User.objects.create(username=username, email=email)

    elif len(existing_users) == 1:
        user = existing_users[0]
        if user.username != username or user.email != email:
            errors = {}
            if user.username == username:
                errors['username'] = [
                    'Это имя уже занято другим пользователем.']
            if user.email == email:
                errors['email'] = [
                    'Этот email не соответствует данному имени.']
            raise ValidationError(errors)

    else:
        raise ValidationError({
            'username': ['Это имя уже занято другим пользователем.'],
            'email': ['Этот email уже используется другим пользователем.']
        })

    confirmation_code = generate_confirmation_code()
    user.confirmation_code = confirmation_code
    user.save()

    send_confirmation_email(user, confirmation_code)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([AllowAny])
def get_token(request):
    serializer = TokenSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    username = serializer.validated_data['username']
    code = serializer.validated_data['confirmation_code']

    user = get_object_or_404(User, username=username)

    if user.confirmation_code != code:
        raise ValidationError('Неверный код подтверждения.')

    user.confirmation_code = ''
    user.save()

    token = AccessToken.for_user(user)
    return Response({'token': str(token)}, status=status.HTTP_200_OK)


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all().order_by('id')
    serializer_class = UserSerializer
    permission_classes = [IsAdmin]
    lookup_field = 'username'
    filter_backends = [filters.SearchFilter]
    search_fields = ['username']
    http_method_names = ['get', 'post', 'patch', 'delete', 'head', 'options']

    @action(detail=False, methods=['get', 'patch'],
            url_path=settings.RESERVED_NAME,
            permission_classes=[IsAuthenticated])
    def me(self, request):
        if request.method == 'GET':
            return Response(UserProfileSerializer(request.user).data)

        serializer = UserProfileSerializer(
            request.user,
            data=request.data,
            partial=True,
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
