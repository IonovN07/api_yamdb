from django.contrib import admin

from reviews.models import Category, Genre, Title

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
    list_editable = ('category', 'genre')
    list_filter = ('category', 'genre')
    filter_horizontal = ('genre',)
    search_fields = ('name',)

class TitleInline(admin.StackedInline):
    model = Title
    extra = 0

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    inlines = (
        TitleInline,
    )
    list_display = ('name', 'slug')
    list_display_links = ('name',)

@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    inlines = (
        TitleInline,
    )
    list_display = ('name', 'slug')
    list_display_links = ('name',)


admin.site.empty_value_display = 'Не задано'