from django_filters import rest_framework as filters
from reviews.models import Title


class TitleFilter(filters.FilterSet):
    '''Фильтры для произведений.'''
    
    def create_char_filter(field_name):
        return filters.CharFilter(
            field_name=field_name,
            lookup_expr='icontains'
        )

    category = create_char_filter('category__slug')
    genre = create_char_filter('genre__slug')
    name = create_char_filter('name')
    year = filters.NumberFilter(field_name='year')

    class Meta:
        model = Title
        fields = '__all__'