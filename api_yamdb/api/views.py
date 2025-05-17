from rest_framework import filters, mixins, viewsets
from django_filters.rest_framework import DjangoFilterBackend

from api.filters import TitleFilter
from api.mixins import  ListCreateDestroyViewSet
from api.serializers import (
    CategorySerializer,
    GenreSerializer,
    TitleSerializer,
)
from users.permissions import(
    IsAdminOrReadOnly
    )
from review.models import Category, Genre, Title

class TitleViewSet(viewsets.ModelViewSet):
    serializer_class = TitleSerializer
    permission_classes = (IsAdminOrReadOnly,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = TitleFilter

    def get_queryset(self):
        return (
            Title.objects.annotate(rating=Avg('reviews__score'))
            .all()
            .order_by('-year')
            .select_related('category')
            .prefetch_related('genres')
        )


class CategoryViewSet(ListCreateDestroyViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer


class GenreViewSet(ListCreateDestroyViewSet):
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer