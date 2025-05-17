from rest_framework import filters, mixins, viewsets

from review.models import Category, Genre, Title
from api.serializers import (
    CategorySerializer,
    GenreSerializer,
    TitleSerializer,
)


class TitleVievSet(viewsets.ModelViewSet):
    pass

class CategoryViewSet(ListCreateDestroyViewSet):
    pass

class GenreViewSet(ListCreateDestroyViewSet):
    pass