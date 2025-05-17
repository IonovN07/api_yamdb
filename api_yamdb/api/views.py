from django.db.models import Avg
from django.shortcuts import get_object_or_404
from rest_framework import viewsets
from rest_framework.pagination import (
    PageNumberPagination, LimitOffsetPagination
)
from django_filters.rest_framework import DjangoFilterBackend

from api.filters import TitleFilter
from api.mixins import AllowedMethodsMixin, ListCreateDestroyViewSet
from api.serializers import (
    CategorySerializer,
    GenreSerializer,
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


class TitleViewSet(AllowedMethodsMixin, viewsets.ModelViewSet):
    """Получить список всех произведений."""

    pagination_class = LimitOffsetPagination
    permission_classes = (IsAdminOrReadOnly,)
    filter_backends = (DjangoFilterBackend, )
    filterset_class = TitleFilter

    def get_queryset(self):
        return (
            Title.objects.annotate(rating=Avg('reviews__score'))
            .all().order_by('-year')
        )

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve'):
            return TitleReadSerializer
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
        """Получение всех комментов к отзыву."""

        review = get_object_or_404(Review, id=self.kwargs['review_id'])
        return review.comments.all().order_by('-id')
