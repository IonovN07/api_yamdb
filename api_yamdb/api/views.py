import random

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.db.models import Avg
from django.http import Http404
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status, permissions, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.exceptions import ValidationError
from rest_framework.pagination import (
    PageNumberPagination, LimitOffsetPagination
)
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
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
    '''Получить список всех отзывов.'''

    serializer_class = ReviewSerializer
    permission_classes = (IsAuthorModeratorAdminOrReadOnly,)
    http_method_names = ['get', 'post', 'patch', 'delete']
    pagination_class = PageNumberPagination

    def get_queryset(self):
        title = get_object_or_404(Title, id=self.kwargs.get('title_id'))
        return title.reviews.all()

    def perform_create(self, serializer):
        title = get_object_or_404(Title, id=self.kwargs.get('title_id'))
        serializer.save(author=self.request.user, title=title)


class CommentViewSet(viewsets.ModelViewSet):
    '''Получить список всех комментариев.'''

    serializer_class = CommentSerializer
    permission_classes = (IsAuthorModeratorAdminOrReadOnly,)
    http_method_names = ['get', 'post', 'patch', 'delete']
    pagination_class = PageNumberPagination

    def get_queryset(self):
        review = get_object_or_404(Review, id=self.kwargs.get('review_id'))
        return review.comments.all()

    def perform_create(self, serializer):
        review = get_object_or_404(Review, id=self.kwargs.get('review_id'))
        serializer.save(author=self.request.user, review=review)
