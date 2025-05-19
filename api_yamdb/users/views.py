from django.contrib.auth.tokens import default_token_generator
from django.core.mail import EmailMultiAlternatives
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import AccessToken

from .models import User
from .permissions import IsAdmin
from .serializers import (SignUpSerializer, TokenSerializer,
                          UserProfileSerializer, UserSerializer)


class SignUpView(APIView):
    """
    Регистрация пользователя и отправка кода подтверждения.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = SignUpSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        username = serializer.validated_data["username"]
        email = serializer.validated_data["email"]

        user = User.objects.filter(username=username).first()
        email_owner = User.objects.filter(email=email).first()

        if not user:
            if email_owner:
                raise ValidationError({
                    "email": [
                        "Этот email уже используется другим пользователем."]
                })
            user = User.objects.create(username=username, email=email)
        else:
            if email_owner and user != email_owner:
                raise ValidationError({
                    "username": ["Это имя уже занято другим пользователем."],
                    "email": ["Этот email не соответствует данному имени."]
                })
            if not email_owner:
                raise ValidationError({
                    "username": ["Это имя уже занято другим пользователем."]
                })

        user.confirmation_code = default_token_generator.make_token(user)
        user.save()
        self.send_confirmation_email(user, user.confirmation_code)

        return Response(serializer.data, status=status.HTTP_200_OK)

    def send_confirmation_email(self, user, confirmation_code):
        subject = 'Код подтверждения YaMDb!'
        from_email = 'noreply@yamdb.fake'
        to = [user.email]

        text_content = (
            f'Здравствуйте, {user.username}!\n\n'
            f'Ваша роль в системе: {user.role}\n'
            'Ваш код подтверждения:\n\n'
            f'{confirmation_code}\n\n'
            'Используйте этот код для получения токена.'
        )
        html_content = f'''
            <html>
                <body>
                    <p>Здравствуйте, <strong>{user.username}</strong>!</p>
                    <p>Ваша роль в системе: <strong>{user.role}</strong></p>
                    <p>Ваш код подтверждения:</p>
                    <p><code style="font-size: 1.2em;">
                    {confirmation_code}</code></p>
                    <p>Используйте этот код для получения токена.</p>
                </body>
            </html>
        '''

        msg = EmailMultiAlternatives(subject, text_content, from_email, to)
        msg.attach_alternative(html_content, "text/html")
        msg.send()


class GetTokenView(APIView):
    """
        Получение токена с помощью confirmation_code.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = TokenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data['user']
        token = AccessToken.for_user(user)

        return Response({'token': str(token)}, status=status.HTTP_200_OK)


class UserViewSet(viewsets.ModelViewSet):
    """
    Работа с пользователями. Доступ только администраторам.
    Эндпоинт `/users/me/` доступен любому аутентифицированному.
    """
    queryset = User.objects.all().order_by('username')
    serializer_class = UserSerializer
    permission_classes = [IsAdmin]
    lookup_field = 'username'
    filter_backends = [filters.SearchFilter]
    search_fields = ['username']
    http_method_names = ['get', 'post', 'patch', 'delete', 'head', 'options']

    def get_permissions(self):
        if self.request.user.is_authenticated and (
                self.action == 'me' or self.request.path.endswith('/users/me/')
        ):
            return [IsAuthenticated()]
        return [permission() for permission in self.permission_classes]

    def put(self, request, *args, **kwargs):
        return Response(
            {"detail": "Метод PUT запрещён."},
            status=status.HTTP_405_METHOD_NOT_ALLOWED
        )

    @action(detail=False, methods=['get', 'patch'], url_path='me')
    def me(self, request):
        if request.method == 'GET':
            serializer = UserProfileSerializer(request.user)
            return Response(serializer.data)

        serializer = UserProfileSerializer(
            request.user,
            data=request.data,
            partial=True,
            context={'instance': request.user}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
