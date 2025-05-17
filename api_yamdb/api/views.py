from django.shortcuts import get_object_or_404
from rest_framework import filters, mixins, viewsets
from rest_framework.pagination import PageNumberPagination
from rest_framework.viewsets import ModelViewSet, GenericViewSet
from rest_framework.mixins import (
    CreateModelMixin,
    DestroyModelMixin,
    ListModelMixin,
)

from api.filters import TitleFilter
from api.serializers import (
    CategorySerializer,
    GenreSerializer,
    TitleSerializer,
    CommentSerializer,
    TitleReadSerializer,
    TitleWriteSerializer,
    ReviewSerializer,
)
from reviews.models import Category, Genre, Title, Review
from users.permissions import (
    IsAuthorModeratorAdminOrReadOnly,
    IsAdminOrReadOnly,
)


class TitleViewSet(ModelViewSet):
    """Получить список всех объектов. Права доступа: Доступно без токена."""

    pass


class CategoryViewSet(
    CreateModelMixin,
    ListModelMixin,
    DestroyModelMixin,
    GenericViewSet
):
    """Получить список всех категорий. Доступ без токена."""

    pass


class GenreViewSet(
    CreateModelMixin,
    ListModelMixin,
    DestroyModelMixin,
    GenericViewSet
):
    """Получить список всех жанров. Доступ без токена."""

    pass


class ReviewViewSet(ModelViewSet):
    """Представление отзывов."""

    serializer_class = ReviewSerializer
    permission_classes = (IsAuthorModeratorAdminOrReadOnly,)
    http_method_names = ['get', 'post', 'patch', 'delete']
    pagination_class = PageNumberPagination

    def get_queryset(self):
        """Получение всех отзывов к произведению."""
        title = get_object_or_404(Title, id=self.kwargs['title_id'])
        return title.reviews.all().order_by('-id')


class CommentViewSet(ModelViewSet):
    """Представление комментариев."""

    serializer_class = CommentSerializer
    permission_classes = (IsAuthorModeratorAdminOrReadOnly,)
    http_method_names = ['get', 'post', 'patch', 'delete']
    pagination_class = PageNumberPagination

    def get_queryset(self):
        """Получение всех комментов к отзыву."""
        review = get_object_or_404(Review, id=self.kwargs['review_id'])
        return review.comments.all().order_by('-id')
