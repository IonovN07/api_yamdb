import datetime as dt

from django.shortcuts import get_object_or_404
from django.db.models import Avg
from rest_framework import serializers

from reviews.models import Category, Genre, Title, Review, Comment


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        lookup_field = 'slug'
        fields = ('name', 'slug')


class GenreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Genre
        lookup_field = 'slug'
        fields = ('name', 'slug')


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

class ReviewSerializer(serializers.ModelSerializer):
    author = serializers.SlugRelatedField(
        read_only=True,
        slug_field='username'
    )

    class Meta:
        model = Review
        fields = (
            'id',
            'text',
            'author',
            'score',
            'pub_date'
        )
        read_only_fields = ('title',)

    def validate(self, data):
        if self.context['request'].method == 'POST':
            title_id = self.context['view'].kwargs['title_id']
            title = get_object_or_404(Title, id=title_id)
            author = self.context['request'].user
            if Review.objects.filter(title=title, author=author).exists():
                raise serializers.ValidationError(
                    'You have already reviewed this title'
                )
            data['author'] = author
            data['title'] = title
        return data


class CommentSerializer(serializers.ModelSerializer):
    author = serializers.SlugRelatedField(
        read_only=True,
        slug_field='username'
    )

    class Meta:
        model = Comment
        fields = (
            'id',
            'text',
            'author',
            'pub_date'
        )
        read_only_fields = ('review',)

    def create(self, validated_data):
        validated_data['author'] = self.context['request'].user
        review_id = self.context['view'].kwargs['review_id']
        validated_data['review'] = get_object_or_404(Review, id=review_id)
        return super().create(validated_data)
