import random

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.db import IntegrityError
from django.db.models import Avg
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, mixins, permissions, status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.exceptions import ValidationError
from rest_framework.pagination import (
    LimitOffsetPagination, PageNumberPagination
)
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import AccessToken

from api.filters import TitleFilter
from api.permissions import (
    IsAdmin, IsAdminOrReadOnly, IsAuthorModeratorAdminOrReadOnly
)
from api.serializers import (
    CategorySerializer, CommentSerializer,
    GenreSerializer, ReviewSerializer,
    SignUpSerializer, TitleViewSerializer,
    TitleWriteSerializer, TokenSerializer,
    UserProfileSerializer, UserSerializer
)
from reviews.models import Category, Genre, Review, Title, User


def generate_confirmation_code():
    return ''.join(random.choices(
        settings.ALLOWED_CONFIRMATION_SYMBOLS,
        k=settings.CONFIRMATION_CODE_LENGTH
    ))


def send_confirmation_email(user):
    subject = 'Код подтверждения YaMDb!'
    from_email = settings.DEFAULT_FROM_EMAIL
    to = [user.email]

    text_content = (
        f'Здравствуйте, {user.username}!\n\n'
        f'Ваш код подтверждения:\n\n{user.confirmation_code}\n\n'
        'Используйте этот код для получения токена.'
    )
    html_content = f'''
        <html>
            <body>
                <p>Здравствуйте, <strong>{user.username}</strong>!</p>
                <p>Ваш код подтверждения:</p>
                <p>
                    <code style="font-size: 1.2em;">
                    {user.confirmation_code}</code>
                </p>
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
    USERNAME_ERROR = "Это имя уже занято другим пользователем."
    EMAIL_ERROR = "Этот email уже используется другим пользователем."

    serializer = SignUpSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    username = serializer.validated_data['username']
    email = serializer.validated_data['email']

    try:
        user, _ = User.objects.get_or_create(
            username=username,
            email=email
        )
    except IntegrityError:
        raise ValidationError(
            {'username': [USERNAME_ERROR]}
            if User.objects.filter(username=username).exists()
            else {'email': [EMAIL_ERROR]}
        )

    user.confirmation_code = generate_confirmation_code()
    user.save(update_fields=['confirmation_code'])
    send_confirmation_email(user)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([AllowAny])
def get_token(request):
    serializer = TokenSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    username = serializer.validated_data['username']
    code = serializer.validated_data['confirmation_code']

    user = get_object_or_404(User, username=username)

    if user.confirmation_code and user.confirmation_code == code:
        token = AccessToken.for_user(user)
        return Response({"token": str(token)}, status=status.HTTP_200_OK)

    if user.confirmation_code:
        user.confirmation_code = ''
        user.save(update_fields=['confirmation_code'])
    raise ValidationError('Неверный код.')


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
    def self_profile(self, request):
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


class TitleViewSet(viewsets.ModelViewSet):
    """Получить список всех произведений."""

    queryset = (
        Title.objects.annotate(rating=Avg("reviews__score"))
        .order_by(*Title._meta.ordering)
    )
    pagination_class = LimitOffsetPagination
    permission_classes = (IsAdminOrReadOnly,)
    http_method_names = ['get', 'post', 'patch', 'delete']
    filter_backends = (DjangoFilterBackend,)
    filterset_class = TitleFilter

    def get_serializer_class(self):
        if self.request.method in permissions.SAFE_METHODS:
            return TitleViewSerializer
        return TitleWriteSerializer


class BaseCategoryGenreView(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    filter_backends = (filters.SearchFilter,)
    search_fields = ('name',)
    permission_classes = (IsAdminOrReadOnly,)
    lookup_field = 'slug'


class CategoryViewSet(BaseCategoryGenreView):
    """Получить список всех категорий."""

    queryset = Category.objects.all()
    serializer_class = CategorySerializer


class GenreViewSet(BaseCategoryGenreView):
    """Получить список всех жанров."""

    queryset = Genre.objects.all()
    serializer_class = GenreSerializer


class ReviewViewSet(viewsets.ModelViewSet):
    """Получить список всех отзывов."""

    serializer_class = ReviewSerializer
    permission_classes = (IsAuthorModeratorAdminOrReadOnly,)
    http_method_names = ['get', 'post', 'patch', 'delete']
    pagination_class = PageNumberPagination

    def get_title(self):
        return get_object_or_404(Title, id=self.kwargs['title_id'])

    def get_queryset(self):
        return self.get_title().reviews.all()

    def perform_create(self, serializer):
        serializer.save(author=self.request.user, title=self.get_title())


class CommentViewSet(viewsets.ModelViewSet):
    """Получить список всех комментариев."""

    serializer_class = CommentSerializer
    permission_classes = (IsAuthorModeratorAdminOrReadOnly,)
    http_method_names = ['get', 'post', 'patch', 'delete']
    pagination_class = PageNumberPagination

    def get_review(self):
        return get_object_or_404(
            Review,
            id=self.kwargs['review_id'],
        )

    def get_queryset(self):
        return self.get_review().comments.all()

    def perform_create(self, serializer):
        serializer.save(author=self.request.user, review=self.get_review())
