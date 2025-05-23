from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone

LENGTH_STR: int = 15
MIN_RATING: int = 1
MAX_RATING: int = 10

USER = 'user'
MODERATOR = 'moderator'
ADMIN = 'admin'
ROLE_CHOICES = [
    (USER, 'user'),
    (MODERATOR, 'moderator'),
    (ADMIN, 'admin')
]

ROLE_MAX_LENGTH = max(len(role) for role, _ in ROLE_CHOICES)


def current_year():
    return timezone.now().year


class User(AbstractUser):
    username = models.CharField(
        verbose_name="Имя пользователя",
        max_length=settings.USERNAME_MAX_LENGTH,
        unique=True,
    )
    email = models.EmailField(
        verbose_name="Почта",
        max_length=settings.EMAIL_MAX_LENGTH,
        unique=True,
    )
    first_name = models.CharField(
        verbose_name="Имя",
        max_length=settings.NAME_MAX_LENGTH,
        blank=True,
    )
    last_name = models.CharField(
        verbose_name="Фамилия",
        max_length=settings.NAME_MAX_LENGTH,
        blank=True,
    )
    bio = models.TextField(
        verbose_name="Биография",
        blank=True,
    )
    role = models.CharField(
        verbose_name="Роль",
        max_length=ROLE_MAX_LENGTH,
        choices=ROLE_CHOICES,
        default=USER,
    )
    confirmation_code = models.CharField(
        max_length=settings.CONFIRMATION_CODE_LENGTH,
        blank=True,
    )

    @property
    def is_admin(self):
        return self.role == ADMIN or self.is_staff or self.is_superuser

    @property
    def is_moderator(self):
        return self.role == MODERATOR

    def clean(self):
        if self.username == settings.RESERVED_NAME:
            raise ValidationError({
                'username': f'Имя "{settings.RESERVED_NAME}" не разрешено.'
            })


class BaseModel(models.Model):
    """Базовый класс для моделей с общими свойствами."""

    name = models.CharField(
        max_length=256,
        verbose_name='Название',
        help_text=''
    )
    slug = models.SlugField(unique=True, verbose_name='Слаг')

    class Meta:
        abstract = True

    def __str__(self):
        return self.name[:LENGTH_STR]


class Category(BaseModel):
    """Данная модель описывает таблицу с категориями произведений."""

    class Meta:
        ordering = ('name',)
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'

    help_text = 'Название категории, не более 256 символов'


class Genre(BaseModel):
    """Данная модель описывает таблицу с жанрами произведений."""

    class Meta:
        ordering = ('name',)
        verbose_name = 'Жанр'
        verbose_name_plural = 'Жанры'

    help_text = 'Название жанра, не более 256 символов'


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
        category_name = (
            self.category.name[:LENGTH_STR]
            if self.category
            else 'Категории нет'
        )
        return f'{self.name[::LENGTH_STR]} {self.year} {category_name}'


class BaseContentModel(models.Model):
    '''Абстрактная модель с общими полями.'''

    text = models.TextField(
        'Текст записи',
        max_length=256,
        help_text='Поле для новой записи'
    )
    pub_date = models.DateTimeField(
        'Дата публикации',
        auto_now_add=True
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='%(class)ss',  # Автоматическое создание related_name
        verbose_name='Автор',
    )

    class Meta:
        abstract = True
        ordering = ('-pub_date',)
        # Добавляем default_related_name для всех ForeignKey в дочерних классах
        default_related_name = '%(class)ss'

    def __str__(self):
        '''Метод для возврата сокращенного текста объекта.'''
        return self.text[:LENGTH_STR]


class Review(BaseContentModel):
    '''Модель для управления отзывами произведений.'''

    title = models.ForeignKey(
        Title,
        on_delete=models.CASCADE,
        verbose_name='Произведение',
    )
    score = models.IntegerField(
        verbose_name='Оценка',
        help_text=f'Ваша оценка данному произведению от {MIN_RATING}'
                  f'до {MAX_RATING} (целое число)',
        validators=(MinValueValidator(MIN_RATING),
                    MaxValueValidator(MAX_RATING),)
    )

    class Meta(BaseContentModel.Meta):
        verbose_name = 'Отзыв'
        verbose_name_plural = 'Отзывы'
        # related_name будет автоматически 'reviews' из default_related_name
        constraints = (
            models.UniqueConstraint(
                fields=['title', 'author'],
                name='reviews_unique',
            ),
        )


class Comment(BaseContentModel):
    '''Модель для управления комментариями к отзывам.'''

    review = models.ForeignKey(
        Review,
        on_delete=models.CASCADE,
        verbose_name='Отзыв',  # related_name теперь определяется в Meta
    )

    class Meta(BaseContentModel.Meta):
        verbose_name = 'Комментарий'
        verbose_name_plural = 'Комментарии'
