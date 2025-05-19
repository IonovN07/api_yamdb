from django.db.models import Avg
from django.shortcuts import get_object_or_404
from django.http import Http404
from rest_framework import permissions, viewsets, status
from rest_framework.pagination import (
    PageNumberPagination, LimitOffsetPagination
)
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.exceptions import ValidationError

from api.filters import TitleFilter
from api.mixins import AllowedMethodsMixin, ListCreateDestroyViewSet
from api.serializers import (
    CategorySerializer,
    GenreSerializer,
    CommentSerializer,
    TitleViewSerializer,
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
        """Получение комментариев с проверкой принадлежности отзыва к произведению."""
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
            title=title  # Проверка связи отзыва с произведением
        )
        serializer.save(author=self.request.user, review=review)

    def create(self, request, *args, **kwargs):
        """Обработка создания комментария с валидацией."""
        try:
            # Проверка принадлежности выполняется в perform_create
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
                    {"detail": "Отзыв не найден или не принадлежит указанному произведению."},
                    status=status.HTTP_404_NOT_FOUND
                )
            raise
