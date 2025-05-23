from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from django.utils.http import urlencode

from reviews.models import Category, Comment, Genre, Review, Title, User

MAX_LENGTH_DISPLAY_TEXT = 50


@admin.register(Title)
class TitleAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'category',
        'name',
        'year',
        'description'
    )
    list_display_links = ('name',)
    list_editable = ('category',)
    list_filter = ('category', 'genre')
    filter_horizontal = ('genre',)
    search_fields = ('name',)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    list_display_links = ('name',)


@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    list_display_links = ('name',)


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'title_link',
        'author_link',
        'score',
        'pub_date',
        'text_preview',
        'comments_link',
    )
    list_display_links = ('title_link',)
    list_filter = ('title', 'author', 'score', 'pub_date')
    search_fields = ('title__name', 'author__username', 'text')
    raw_id_fields = ('title', 'author')

    def title_link(self, obj):
        url = reverse('admin:reviews_title_change', args=[obj.title.id])
        return format_html('<a href="{}">{}</a>', url, obj.title.name)
    title_link.short_description = 'Произведение'

    def author_link(self, obj):
        url = reverse('admin:reviews_user_change', args=[obj.author.id])
        return format_html('<a href="{}">{}</a>', url, obj.author.username)
    author_link.short_description = 'Автор'

    def text_preview(self, obj):
        return (
            obj.text[:MAX_LENGTH_DISPLAY_TEXT] + '...'
            if len(obj.text) > MAX_LENGTH_DISPLAY_TEXT
            else obj.text
        )
    text_preview.short_description = 'Текст (превью)'

    def comments_link(self, obj):
        count = obj.comments.count()
        url = (
            reverse('admin:reviews_comment_changelist')
            + '?'
            + urlencode({'review__id': f'{obj.id}'})
        )
        return format_html('<a href="{}">{} комментариев</a>', url, count)
    comments_link.short_description = 'Комментарии'


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'review_link',
        'author_link',
        'pub_date',
        'text_preview',
    )
    list_display_links = ('review_link',)
    list_filter = ('review', 'author', 'pub_date')
    search_fields = ('review__text', 'author__username', 'text')
    raw_id_fields = ('review', 'author')

    def review_link(self, obj):
        url = reverse('admin:reviews_review_change', args=[obj.review.id])
        return format_html('<a href="{}">Отзыв #{}</a>', url, obj.review.id)
    review_link.short_description = 'Отзыв'

    def author_link(self, obj):
        url = reverse('admin:reviews_user_change', args=[obj.author.id])
        return format_html('<a href="{}">{}</a>', url, obj.author.username)
    author_link.short_description = 'Автор'

    def text_preview(self, obj):
        return (
            obj.text[:MAX_LENGTH_DISPLAY_TEXT] + '...'
            if len(obj.text) > MAX_LENGTH_DISPLAY_TEXT
            else obj.text
        )
    text_preview.short_description = 'Текст (превью)'


admin.site.empty_value_display = 'Не задано'

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    fields = ("username", "email", "first_name", "last_name", "bio", "role")
    list_display = (
        "username",
        "email",
        "first_name",
        "last_name",
        "bio",
        "role",
    )
    list_editable = ("role",)
