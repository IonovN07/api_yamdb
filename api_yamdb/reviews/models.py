from django.db import models


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
        # Возможно необходима валидация на уровне модели
    )
    description = models.TextField(blank=True, verbose_name='Описание')
    category = models.ForeignKey(
        'Category',
        on_delete=models.SET_NULL,
        null=True,
        verbose_name='Категория',
    )
    genres = models.ManyToManyField(
        'Genre',
        through='TitleGenre',
        verbose_name='Жанр'
    )

    class Meta:
        ordering = ('-year',)
        verbose_name = 'Произведение'
        verbose_name_plural = 'Произведения'
        default_related_name = 'titles'

    def __str__(self):
        return self.name


class TitleGenre(models.Model):

    title = models.ForeignKey(Title, on_delete=models.CASCADE,)
    genre = models.ForeignKey(Genre, on_delete=models.CASCADE,)

    def __str__(self):
        return f'{self.title},{self.genre}'