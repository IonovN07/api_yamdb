from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone

from reviews.validators import validate_username_value

USERNAME_MAX_LENGTH = 150
EMAIL_MAX_LENGTH = 254
NAME_MAX_LENGTH = 150

MAX_DISPLAY_LENGTH = 15
MIN_RATING = 1
MAX_RATING = 10

USER = 'user'
MODERATOR = 'moderator'
ADMIN = 'admin'
ROLE_CHOICES = [
    (USER, 'user'),
    (MODERATOR, 'moderator'),
    (ADMIN, 'admin')
]


def current_year():
    return timezone.now().year


class User(AbstractUser):
    username = models.CharField(
        verbose_name="Логин",
        max_length=USERNAME_MAX_LENGTH,
        unique=True,
        validators=[validate_username_value],
    )
    email = models.EmailField(
        verbose_name="Почта",
        max_length=EMAIL_MAX_LENGTH,
        unique=True,
    )
    first_name = models.CharField(
        verbose_name="Имя",
        max_length=NAME_MAX_LENGTH,
        blank=True,
    )
    last_name = models.CharField(
        verbose_name="Фамилия",
        max_length=NAME_MAX_LENGTH,
        blank=True,
    )
    bio = models.TextField(
        verbose_name="Биография",
        blank=True,
    )
    role = models.CharField(
        verbose_name="Роль",
        max_length=max(len(role) for role, _ in ROLE_CHOICES),
        choices=ROLE_CHOICES,
        default=USER,
    )
    confirmation_code = models.CharField(
        max_length=settings.CONFIRMATION_CODE_LENGTH,
        blank=True,
    )

    @property
    def is_admin(self):
        return self.role == ADMIN or self.is_staff

    @property
    def is_moderator(self):
        return self.role == MODERATOR


class BaseNameSlugModel(models.Model):
    """Базовый класс для моделей с общими свойствами."""

    name = models.CharField(
        max_length=256,
        verbose_name='Название',
    )
    slug = models.SlugField(unique=True, verbose_name='Слаг')

    class Meta:
        ordering = ('name',)
        abstract = True

    def __str__(self):
        return self.name[:MAX_DISPLAY_LENGTH]


class Category(BaseNameSlugModel):
    """Модель описывает таблицу с категориями произведений."""

    class Meta(BaseNameSlugModel.Meta):
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'


class Genre(BaseNameSlugModel):
    """Модель описывает таблицу с жанрами произведений."""

    class Meta(BaseNameSlugModel.Meta):
        verbose_name = 'Жанр'
        verbose_name_plural = 'Жанры'


class Title(models.Model):
    """Модель описывает таблицу с произведениями,
    на которые можно писать отзывы.
    """

    name = models.CharField(
        max_length=256,
        verbose_name='Название',
        help_text='Название произведения.'
    )
    year = models.SmallIntegerField(
        verbose_name='Год',
        validators=[
            MaxValueValidator(
                current_year, message='Год не может быть больше текущего.'
            )
        ]
    )
    description = models.TextField(blank=True, verbose_name='Описание')
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name='Категория',
    )
    genre = models.ManyToManyField(
        Genre,
        verbose_name='Жанр'
    )

    class Meta:
        ordering = ('name',)
        verbose_name = 'Произведение'
        verbose_name_plural = 'Произведения'
        default_related_name = 'titles'

    def __str__(self):
        return (
            f'{self.name[:MAX_DISPLAY_LENGTH]} '
            f'{self.year} '
            f'{{self.category={self.category.name[:MAX_DISPLAY_LENGTH]}}}'
        )


class BaseContentModel(models.Model):
    """Абстрактная модель для отзывов и комментариев."""

    text = models.TextField(
        verbose_name='Текст',
        help_text='Текст отзыва или комментария'
    )
    pub_date = models.DateTimeField(
        verbose_name='Дата публикации',
        auto_now_add=True
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор',
    )

    class Meta:
        abstract = True
        ordering = ('-pub_date',)
        default_related_name = '%(class)ss'

    def __str__(self):
        return f'{self.author.username}: {self.text[:MAX_DISPLAY_LENGTH]}...'


class Review(BaseContentModel):
    """Модель отзывов на произведения."""

    title = models.ForeignKey(
        Title,
        on_delete=models.CASCADE,
        verbose_name='Произведение',
    )
    score = models.IntegerField(
        verbose_name='Оценка',
        help_text=f'Оценка произведению от {MIN_RATING} до {MAX_RATING}',
        validators=(MinValueValidator(MIN_RATING),
                    MaxValueValidator(MAX_RATING),)
    )

    class Meta(BaseContentModel.Meta):
        verbose_name = 'Отзыв'
        verbose_name_plural = 'Отзывы'
        constraints = (
            models.UniqueConstraint(
                fields=['title', 'author'],
                name='reviews_unique',
            ),
        )


class Comment(BaseContentModel):
    """Модель комментариев к отзывам."""

    review = models.ForeignKey(
        Review,
        on_delete=models.CASCADE,
        verbose_name='Отзыв',
    )

    class Meta(BaseContentModel.Meta):
        verbose_name = 'Комментарий'
        verbose_name_plural = 'Комментарии'
