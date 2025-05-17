from rest_framework import mixins, viewsets
from rest_framework.filters import SearchFilter
from users.permissions import IsAuthorModeratorAdminOrReadOnly


class ListCreateDestroyViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    filter_backends = (SearchFilter,)
    search_fields = ('name',)
    permission_classes = (IsAuthorModeratorAdminOrReadOnly,)
    lookup_field = 'slug'