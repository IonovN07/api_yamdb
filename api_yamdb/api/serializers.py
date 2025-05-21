from django.conf import settings
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from rest_framework import serializers
from rest_framework.exceptions import NotFound

from reviews.models import Category, Genre, Title, Review, Comment

User = get_user_model()


def validate_reserved_username(username: str):
    if username == settings.RESERVED_NAME:
        raise serializers.ValidationError('Имя \'me\' не разрешено.')
    return username


class UserSerializer(serializers.ModelSerializer):
    username = serializers.RegexField(
        regex=settings.USERNAME_REGEX,
        max_length=settings.USERNAME_MAX_LENGTH,
        required=True,
    )
    email = serializers.EmailField(
        max_length=settings.EMAIL_MAX_LENGTH,
        required=True,
    )

    def validate_username(self, username):
        username = validate_reserved_username(username)
        qs = User.objects.filter(username=username)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError('Такой username уже существует.')
        return username

    def validate_email(self, email):
        qs = User.objects.filter(email=email)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError('Этот email уже используется.')
        return email

    class Meta:
        model = User
        fields = (
            'username', 'email',
            'first_name', 'last_name',
            'bio', 'role',
        )


class UserProfileSerializer(UserSerializer):
    class Meta(UserSerializer.Meta):
        read_only_fields = ('role',)


class SignUpSerializer(serializers.Serializer):
    username = serializers.RegexField(
        regex=settings.USERNAME_REGEX,
        max_length=settings.USERNAME_MAX_LENGTH,
        required=True,
    )
    email = serializers.EmailField(
        max_length=settings.EMAIL_MAX_LENGTH,
        required=True,
    )

    def validate_username(self, username):
        return validate_reserved_username(username)


class TokenSerializer(serializers.Serializer):
    username = serializers.RegexField(
        regex=settings.USERNAME_REGEX,
        max_length=settings.USERNAME_MAX_LENGTH,
        required=True,
    )
    confirmation_code = serializers.CharField(
        required=True,
        max_length=settings.CONFIRMATION_CODE_LENGTH,
    )

    def validate_username(self, username):
        return validate_reserved_username(username)


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
        all_fields = (
            'id',
            'name',
            'year',
            'rating',
            'description',
            'genre',
            'category'
        )
        fields = all_fields
        read_only_fields = all_fields


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

    # def validate_genre(self, genre):
    #     if not genre:
    #         raise serializers.ValidationError(
    #             "Жанр произведения не может быть пустым"
    #         )
    #     return genre

    def to_representation(self, instance):
        return TitleViewSerializer(instance).data


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
