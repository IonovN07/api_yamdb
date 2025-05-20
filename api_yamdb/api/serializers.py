import datetime as dt

from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from rest_framework import serializers
from rest_framework.exceptions import NotFound

from reviews.models import Category, Genre, Title, Review, Comment

User = get_user_model()


def validate_reserved_username(value):
    if value.lower() == 'me':
        raise serializers.ValidationError("Имя 'me' не разрешено.")
    return value


class BaseUserSerializer(serializers.ModelSerializer):
    username = serializers.RegexField(
        required=True,
        max_length=150,
        regex=r'^[\w.@+-]+\Z'
    )
    email = serializers.EmailField(
        required=True,
        max_length=254
    )

    def validate_username(self, value):
        validate_reserved_username(value)

        request = self.context.get('request')
        instance = self.instance

        if request and request.method == 'PATCH' and request.user.is_admin:
            if instance and value == instance.username:
                return value

        qs = User.objects.filter(username=value)
        if instance:
            qs = qs.exclude(pk=instance.pk)
        if qs.exists():
            raise serializers.ValidationError("Такой username уже существует.")
        return value

    def validate_email(self, value):
        request = self.context.get('request')
        instance = self.instance

        if request and request.method == 'PATCH' and request.user.is_admin:
            if instance and value == instance.email:
                return value

        qs = User.objects.filter(email=value)
        if instance:
            qs = qs.exclude(pk=instance.pk)
        if qs.exists():
            raise serializers.ValidationError("Такой email уже используется.")
        return value

    class Meta:
        model = User
        fields = ('username', 'email')


class SignUpSerializer(serializers.Serializer):
    username = serializers.RegexField(
        required=True,
        max_length=150,
        regex=r'^[\w.@+-]+\Z'
    )
    email = serializers.EmailField(
        required=True,
        max_length=254
    )

    def validate_username(self, value):
        return validate_reserved_username(value)


class UserSerializer(BaseUserSerializer):
    class Meta(BaseUserSerializer.Meta):
        fields = BaseUserSerializer.Meta.fields + (
            'first_name', 'last_name', 'bio', 'role'
        )


class UserProfileSerializer(UserSerializer):
    role = serializers.CharField(read_only=True)


class TokenSerializer(serializers.Serializer):
    username = serializers.RegexField(
        required=True,
        max_length=150,
        regex=r'^[\w.@+-]+\Z'
    )
    confirmation_code = serializers.CharField(required=True)

    def validate_username(self, value):
        return validate_reserved_username(value)

    def validate(self, data):
        user = get_object_or_404(User, username=data['username'])
        if user.confirmation_code != data['confirmation_code']:
            raise serializers.ValidationError('Неверный код подтверждения.')
        data['user'] = user
        return data


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


class TitleViewSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    genre = GenreSerializer(
        read_only=True,
        many=True
    )
    rating = serializers.IntegerField(read_only=True, default=None)

    class Meta:
        model = Title
        fields = (
            'id', 'name', 'year', 'rating', 'description', 'genre', 'category'
        )


class TitleWriteSerializer(serializers.ModelSerializer):
    category = serializers.SlugRelatedField(
        queryset=Category.objects.all(),
        slug_field='slug'
    )
    genre = serializers.SlugRelatedField(
        queryset=Genre.objects.all(),
        slug_field='slug',
        many=True
    )
    rating = serializers.IntegerField(read_only=True, default=None)

    class Meta:
        fields = (
            'id', 'name', 'year', 'rating', 'description', 'genre', 'category'
        )
        model = Title

    def validate_year(self, year):
        '''Валидация поля год.'''

        if year > dt.datetime.today().year:
            raise serializers.ValidationError(
                'Год произведения не может быть больше текущего года.'
            )
        return year

    def validate_genre(self, genre):
        if not genre:
            raise serializers.ValidationError(
                "Жанр произведения не может быть пустым"
            )
        return genre

    def to_representation(self, instance):
        representation = TitleViewSerializer(instance).data
        return representation


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
    text = serializers.CharField(required=True, min_length=1)

    class Meta:
        model = Comment
        fields = ('id', 'text', 'author', 'pub_date')
        read_only_fields = ('review',)

    def validate_text(self, value):
        """Проверка, что текст комментария не пустой."""
        if not value.strip():
            raise serializers.ValidationError(
                "Текст комментария не может быть пустым.",
                code='empty_comment'
            )
        return value

    def create(self, validated_data):
        """Создание комментария с проверкой существования отзыва."""
        review_id = self.context['view'].kwargs['review_id']
        try:
            review = Review.objects.get(id=review_id)
        except Review.DoesNotExist:
            raise NotFound(detail="Отзыв не найден")

        validated_data['author'] = self.context['request'].user
        validated_data['review'] = review
        return super().create(validated_data)
