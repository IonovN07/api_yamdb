from django.contrib.auth.tokens import default_token_generator
from django.core.mail import EmailMultiAlternatives
from django.db.models import Avg
from django.http import Http404
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status, permissions, viewsets 
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.pagination import (
    PageNumberPagination, LimitOffsetPagination
)
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import AccessToken

from api.filters import TitleFilter
from api.mixins import AllowedMethodsMixin, ListCreateDestroyViewSet
from api.serializers import (
    CategorySerializer,
    GenreSerializer,
    CommentSerializer,
    TitleViewSerializer,
    TitleWriteSerializer,
    ReviewSerializer,
    SignUpSerializer,
    TokenSerializer,
    UserProfileSerializer,
    UserSerializer
)
from reviews.models import Category, Genre, Review, Title, User
from api.permissions import (
    IsAdmin,
    IsAuthorModeratorAdminOrReadOnly,
    IsAdminOrReadOnly,
)


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


class TitleViewSet(AllowedMethodsMixin, viewsets.ModelViewSet):
    """Получить список всех произведений."""

    queryset = Title.objects.annotate(rating=Avg("reviews__score"))
    pagination_class = LimitOffsetPagination
    permission_classes = (IsAdminOrReadOnly,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = TitleFilter

    def get_serializer_class(self):
        if self.request.method in permissions.SAFE_METHODS:
            return TitleViewSerializer
        return TitleWriteSerializer


class CategoryViewSet(ListCreateDestroyViewSet):
    """Получить список всех категорий."""

    queryset = Category.objects.all()
    serializer_class = CategorySerializer


class GenreViewSet(ListCreateDestroyViewSet):
    """Получить список всех жанров."""

    queryset = Genre.objects.all()
    serializer_class = GenreSerializer


class ReviewViewSet(viewsets.ModelViewSet):
    """Получить список всех отзывов."""

    serializer_class = ReviewSerializer
    permission_classes = (IsAuthorModeratorAdminOrReadOnly,)
    http_method_names = ['get', 'post', 'patch', 'delete']
    pagination_class = PageNumberPagination

    def get_queryset(self):
        """Получение всех отзывов к произведению."""

        title = get_object_or_404(Title, id=self.kwargs['title_id'])
        return title.reviews.all().order_by('-id')


class CommentViewSet(viewsets.ModelViewSet):
    """Получить список всех комментариев."""
    serializer_class = CommentSerializer
    permission_classes = (IsAuthorModeratorAdminOrReadOnly,)
    http_method_names = ['get', 'post', 'patch', 'delete']
    pagination_class = PageNumberPagination

    def get_queryset(self):
        """
        Получение комментариев с проверкой принадлежности
        отзыва к произведению.
        """
        title = get_object_or_404(Title, id=self.kwargs['title_id'])
        review = get_object_or_404(
            Review,
            id=self.kwargs['review_id'],
            title=title  # Проверка что отзыв принадлежит произведению
        )
        return review.comments.all().order_by('-id')

    def perform_create(self, serializer):
        """Создание комментария с проверкой принадлежности отзыва."""

        title = get_object_or_404(Title, id=self.kwargs['title_id'])
        review = get_object_or_404(
            Review,
            id=self.kwargs['review_id'],
            title=title
        )
        serializer.save(author=self.request.user, review=review)

    def create(self, request, *args, **kwargs):
        """Обработка создания комментария с валидацией."""

        try:
            return super().create(request, *args, **kwargs)
        except ValidationError as e:
            if 'empty_comment' in e.get_codes().get('text', []):
                return Response(
                    {"text": ["Текст комментария не может быть пустым."]},
                    status=status.HTTP_400_BAD_REQUEST
                )
            raise
        except Exception as e:
            if isinstance(e, Http404):
                return Response(
                    {
                        "detail": "Отзыв не найден "
                        "или не принадлежит указанному произведению."
                    },
                    status=status.HTTP_404_NOT_FOUND
                )
            raise
