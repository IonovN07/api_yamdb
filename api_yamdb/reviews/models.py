from django.contrib.auth.models import AbstractUser
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone

from api_yamdb.settings import LENGTH_STR
# from users.models import User


USER = 'user'
MODERATOR = 'moderator'
ADMIN = 'admin'
ROLE_CHOICES = [
    (USER, 'user'),
    (MODERATOR, 'moderator'),
    (ADMIN, 'admin')
]


class User(AbstractUser):
    email = models.EmailField(unique=True)
    bio = models.TextField(blank=True)
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default=USER
    )
    confirmation_code = models.CharField(
        max_length=255,
        blank=True,
    )

    @property
    def is_admin(self):
        return self.role == ADMIN or self.is_superuser

    @property
    def is_moderator(self):
        return self.role == MODERATOR


class Category(models.Model):
    """Данная модель описывает таблицу с категориями произведений."""

    name = models.CharField(
        max_length=256,
        verbose_name='Название',
        help_text='Название категории, не более 256 символов'
    )
    slug = models.SlugField(unique=True, verbose_name='Слаг')

    class Meta:
        ordering = ['name']
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'

    def __str__(self):
        return self.name[:21]


class Genre(models.Model):
    """ Данная модель описывает таблицу с жанрами произведений."""

    name = models.CharField(
        max_length=256,
        verbose_name='Название',
        help_text='Название жанра, не более 256 символов'
    )
    slug = models.SlugField(unique=True, verbose_name='Слаг')

    class Meta:
        ordering = ['name']
        verbose_name = 'Жанр'
        verbose_name_plural = 'Жанры'

    def __str__(self):
        return self.name[:21]


class Title(models.Model):
    """Данная модель описывает таблицу с произведениями,
    на которые можно писать отзывы.
    """

    name = models.CharField(
        max_length=256,
        verbose_name='Название',
        help_text='Название произведения, не более 256 символов'
    )
    year = models.SmallIntegerField(
        verbose_name='Год',
        validators=[MaxValueValidator(timezone.now().year)],
    )
    description = models.TextField(blank=True, verbose_name='Описание')
    category = models.ForeignKey(
        'Category',
        on_delete=models.SET_NULL,
        null=True,
        verbose_name='Категория',
    )
    genre = models.ManyToManyField(
        'Genre',
        verbose_name='Жанр'
    )

    class Meta:
        ordering = ('-year',)
        verbose_name = 'Произведение'
        verbose_name_plural = 'Произведения'
        default_related_name = 'titles'

    def __str__(self):
        return self.name[:21]


class BaseModelReviw(models.Model):
    """Абстрактная модель для соблюдения DRY."""

    text = models.TextField(
        'Текст записи', max_length=500, help_text='Поле для новой записи'
    )
    pub_date = models.DateTimeField('Дата публикации', auto_now_add=True)

    class Meta:
        abstract = True


class Review(BaseModelReviw):
    """Модель для управления отзывами произведений."""

    title = models.ForeignKey(
        Title,
        on_delete=models.CASCADE,
        related_name='reviews',
        verbose_name='Произведение',
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='reviews',
        verbose_name='Автор',
    )
    score = models.IntegerField(
        verbose_name='Оценка',
        help_text='Ваша оценка данному произведению от 1 до 10 (целое число)',
        validators=(MinValueValidator(1), MaxValueValidator(10),))

    class Meta:
        verbose_name = 'Отзыв'
        verbose_name_plural = 'Отзывы'
        constraints = (
            models.UniqueConstraint(
                fields=['title', 'author'],
                name='reviews_unique',
            ),
        )

    def __str__(self):
        """Метод для возврата названия объекта."""
        return self.text[:LENGTH_STR]


class Comment(BaseModelReviw):
    """Модель для управления комментариями к отзывам."""

    review = models.ForeignKey(
        Review,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='Отзыв',
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='Автор',
    )

    class Meta:
        verbose_name = 'Комментарий'
        verbose_name_plural = 'Комментарии'

    def __str__(self):
        """Метод для возврата названия объекта."""
        return self.text[:LENGTH_STR]
