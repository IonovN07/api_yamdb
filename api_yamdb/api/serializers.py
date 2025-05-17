import datetime as dt

from django.db.models import Avg
from rest_framework import serializers

from reviews.models import Category, Genre, Title


class CategorySerializer(serializers.ModelSerializer):

    class Meta:
        model = Category
        fields = '__all__'


class GenreSerializer(serializers.ModelSerializer):

    class Meta:
        model = Genre
        fields = '__all__'


class TitleSerializer(serializers.ModelSerializer):

    category = serializers.SlugRelatedField(
        slug_field='slug',
        queryset=Category.objects.all(),
    )
    genre = serializers.SlugRelatedField(
        slug_field='slug',
        queryset=Genre.objects.all(),
        source='genres',
        many=True,
        required=True,

    )

    class Meta:
        model = Title
        fields = [
            'id',
            'name',
            'year',
            'rating',
            'description',
            'genre',
            'category',
        ]

    def to_representation(self, instance):
        """Дополняет представление данными о жанре, категории и рейтинге."""

        serialized_data = super().to_representation(instance)
        serialized_data['genre'] = (
            GenreSerializer(instance.genres.all(), many=True).data
        )
        serialized_data['category'] = (
            CategorySerializer(instance.category).data
        )
        serialized_data['rating'] = instance.rating
        return serialized_data
    
    def validate_year(self, year):
        '''Валидация поля год.'''

        if year > dt.datetime.today().year:
            raise serializers.ValidationError(
                'Год произведения не может быть больше текущего года.'
            )
        return year
