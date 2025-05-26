from django.contrib import admin
from django.urls import reverse
from django.utils.http import urlencode
from django.utils.safestring import mark_safe

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
    list_filter = ('score', 'pub_date')
    search_fields = ('title__name', 'author__username', 'text__startswith')
    raw_id_fields = ('title', 'author')

    @admin.display(description='Произведение')
    @mark_safe
    def title_link(self, review):
        url = reverse('admin:reviews_title_change', args=[review.title.id])
        return f'<a href="{url}">{review.title.name}</a>'

    @admin.display(description='Автор')
    @mark_safe
    def author_link(self, review):
        url = reverse('admin:reviews_user_change', args=[review.author.id])
        return f'<a href="{url}">{review.author.username}</a>'

    @admin.display(description='Текст (превью)')
    def text_preview(self, review):
        return review.text[:MAX_LENGTH_DISPLAY_TEXT]

    @admin.display(description='Комментарии')
    @mark_safe
    def comments_link(self, review):
        count = review.comments.count()
        url = (
            reverse('admin:reviews_comment_changelist')
            + '?'
            + urlencode({'review__id': f'{review.id}'})
        )
        return f'<a href="{url}">{count} комментариев</a>'


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
    list_filter = ('review', 'pub_date', 'author')
    search_fields = ('review__text__startswith', 'author__username')
    raw_id_fields = ('review', 'author')

    @admin.display(description='Отзыв')
    @mark_safe
    def review_link(self, comment):
        url = reverse('admin:reviews_review_change', args=[comment.review.id])
        return f'<a href="{url}">Отзыв #{comment.review.id}</a>'

    @admin.display(description='Автор')
    @mark_safe
    def author_link(self, comment):
        url = reverse('admin:reviews_user_change', args=[comment.author.id])
        return f'<a href="{url}">{comment.author.username}</a>'

    @admin.display(description='Текст (превью)')
    def text_preview(self, comment):
        return comment.text[:MAX_LENGTH_DISPLAY_TEXT]


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
