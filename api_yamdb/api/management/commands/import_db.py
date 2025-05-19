import csv
import os
from datetime import datetime

from django.core.management.base import BaseCommand
from django.db import transaction

from reviews.models import (
    Category, Genre, Title, TitleGenre, Review, Comment
)
from users.models import User


class Command(BaseCommand):
    """Команда для импорта данных из CSV файлов в базу данных."""

    help = 'Загрузка данных из csv'
    DEFAULT_CSV_PATH = 'static/data/'

    def add_arguments(self, parser):
        """Определение аргументов команды."""

        parser.add_argument(
            '--path',
            type=str,
            default=self.DEFAULT_CSV_PATH,
            help=f'Путь к файлам csv (default: "{self.DEFAULT_CSV_PATH}")'
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Очистить базу перед импортом'
        )

    def handle(self, *args, **options):
        """Основной метод выполнения команды."""

        self.csv_path = options['path']

        if not os.path.exists(self.csv_path):
            self.stdout.write(
                self.style.ERROR(
                    f'Каталог "{self.csv_path}" не существует!')
            )
            return

        self.stdout.write(
            self.style.SUCCESS(
                f'Старт импорта из "{self.csv_path}"...')
        )

        try:
            with transaction.atomic():
                if options['clear']:
                    self.clear_data()

                self.import_users()
                self.import_categories()
                self.import_genres()
                self.import_titles()
                self.import_genre_title()
                self.import_reviews()
                self.import_comments()

            self.stdout.write(
                self.style.SUCCESS('Данные успешно загружены!')
            )
        except Exception as e:
            self.stdout.write(self.style.ERROR(
                f'При попытке импорта произошла ошибка: {str(e)}'))

    def clear_data(self):
        """Очистка существующих данных перед импортом."""

        self.stdout.write(self.style.WARNING('Очистка базы...'))
        Comment.objects.all().delete()
        Review.objects.all().delete()
        TitleGenre.objects.all().delete()
        Title.objects.all().delete()
        Genre.objects.all().delete()
        Category.objects.all().delete()
        User.objects.filter(is_superuser=False).delete()
        self.stdout.write(self.style.SUCCESS('База очищена!'))

    def get_csv_path(self, filename):
        """Возвращает полный путь к CSV-файлу."""

        return os.path.join(self.csv_path, filename)

    def import_users(self):
        """Импорт пользователей из CSV."""

        with open(self.get_csv_path('users.csv'),
                  mode='r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                User.objects.get_or_create(
                    id=row['id'],
                    defaults={
                        'username': row['username'],
                        'email': row['email'],
                        'role': row['role'],
                        'bio': row['bio'] if row['bio'] else "",
                    }
                )
        self.stdout.write(self.style.SUCCESS('Пользователи успешно загружены'))

    def import_categories(self):
        """Импорт категорий из CSV."""

        with open(self.get_csv_path('category.csv'),
                  mode='r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                Category.objects.get_or_create(
                    id=row['id'],
                    defaults={
                        'name': row['name'],
                        'slug': row['slug'],
                    }
                )
        self.stdout.write(self.style.SUCCESS(
            'Категории успешно загружены'))

    def import_genres(self):
        """Импорт жанров из CSV."""

        with open(self.get_csv_path('genre.csv'),
                  mode='r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                Genre.objects.get_or_create(
                    id=row['id'],
                    defaults={
                        'name': row['name'],
                        'slug': row['slug'],
                    }
                )
        self.stdout.write(self.style.SUCCESS('Жанры успешно загружены'))

    def import_titles(self):
        """Импорт произведений из CSV."""

        with open(self.get_csv_path('titles.csv'),
                  mode='r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                category = Category.objects.get(id=row['category'])
                Title.objects.get_or_create(
                    id=row['id'],
                    defaults={
                        'name': row['name'],
                        'year': row['year'],
                        'category': category,
                        'description': '',
                    }
                )
        self.stdout.write(self.style.SUCCESS('Произведения успешно загружены'))

    def import_genre_title(self):
        """Импорт связей жанров и произведений из CSV."""

        with open(self.get_csv_path('genre_title.csv'),
                  mode='r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                title = Title.objects.get(id=row['title_id'])
                genre = Genre.objects.get(id=row['genre_id'])
                TitleGenre.objects.get_or_create(
                    id=row['id'],
                    defaults={
                        'title': title,
                        'genre': genre,
                    }
                )
        self.stdout.write(
            self.style.SUCCESS('Связи жанр - произведение успешно загружены')
        )

    def import_reviews(self):
        """Импорт отзывов из CSV."""

        with open(self.get_csv_path('review.csv'),
                  mode='r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                title = Title.objects.get(id=row['title_id'])
                author = User.objects.get(id=row['author'])
                pub_date = datetime.strptime(
                    row['pub_date'], '%Y-%m-%dT%H:%M:%S.%fZ'
                )

                Review.objects.get_or_create(
                    id=row['id'],
                    defaults={
                        'title': title,
                        'text': row['text'],
                        'author': author,
                        'score': row['score'],
                        'pub_date': pub_date,
                    }
                )
        self.stdout.write(self.style.SUCCESS('Отзывы успешно загружены'))

    def import_comments(self):
        """Импорт комментариев из CSV."""

        with open(self.get_csv_path('comments.csv'),
                  mode='r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                review = Review.objects.get(id=row['review_id'])
                author = User.objects.get(id=row['author'])
                pub_date = datetime.strptime(
                    row['pub_date'], '%Y-%m-%dT%H:%M:%S.%fZ'
                )

                Comment.objects.get_or_create(
                    id=row['id'],
                    defaults={
                        'review': review,
                        'text': row['text'],
                        'author': author,
                        'pub_date': pub_date,
                    }
                )
        self.stdout.write(self.style.SUCCESS('Комментарии успешно загружены'))
