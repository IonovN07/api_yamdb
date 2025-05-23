import csv
import os
import sqlite3
from datetime import datetime

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    '''Команда для импорта данных из CSV файлов напрямую в SQLite.'''

    help = 'Загрузка данных из csv в SQLite'
    DEFAULT_CSV_PATH = 'static/data/'
    DB_PATH = 'db.sqlite3'

    def add_arguments(self, parser):
        parser.add_argument(
            '--path',
            type=str,
            default=self.DEFAULT_CSV_PATH,
            help=f'Путь к файлам csv (default: \'{self.DEFAULT_CSV_PATH}\')'
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Очистить базу перед импортом'
        )

    def handle(self, *args, **options):
        self.csv_path = options['path']

        if not os.path.exists(self.csv_path):
            self.stdout.write(
                self.style.ERROR(f'Каталог \'{self.csv_path}\' не существует!')
            )
            return

        self.stdout.write(
            self.style.SUCCESS(f'Старт импорта из \'{self.csv_path}\'...')
        )

        try:
            conn = sqlite3.connect(self.DB_PATH)
            cursor = conn.cursor()

            if options['clear']:
                self.clear_data(cursor)

            self.import_users(cursor)
            self.import_categories(cursor)
            self.import_genres(cursor)
            self.import_titles(cursor)
            self.import_genre_title(cursor)
            self.import_reviews(cursor)
            self.import_comments(cursor)

            conn.commit()
            self.stdout.write(
                self.style.SUCCESS('Данные успешно загружены!')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Ошибка импорта: {str(e)}')
            )
        finally:
            conn.close()

    def clear_data(self, cursor):
        '''Очистка существующих данных перед импортом.'''
        self.stdout.write(self.style.WARNING('Очистка базы...'))
        tables = [
            'reviews_comment',
            'reviews_review',
            'reviews_title_genre',
            'reviews_title',
            'reviews_genre',
            'reviews_category',
        ]
        for table in tables:
            cursor.execute(f'DELETE FROM {table};')
        cursor.execute(
            'DELETE FROM reviews_user WHERE is_superuser = 0;'
        )
        self.stdout.write(
            self.style.SUCCESS('База очищена!')
        )

    def get_csv_path(self, filename):
        return os.path.join(self.csv_path, filename)

    def import_users(self, cursor):
        with open(
            self.get_csv_path('users.csv'),
            mode='r',
            encoding='utf-8'
        ) as file:
            reader = csv.DictReader(file)
            for row in reader:
                cursor.execute(
                    '''
                    INSERT OR IGNORE INTO reviews_user (
                        id, password, last_login, is_superuser, username,
                        first_name, last_name, email, is_staff, is_active,
                        date_joined, role, bio
                    ) VALUES (?, \'\', NULL, 0, ?, \'\', ?, ?, 0, 1, ?, ?, ?)
                    ''',
                    (
                        row['id'],
                        row['username'],
                        row['email'],
                        row['email'],
                        datetime.now().isoformat(),
                        row.get('role', 'user'),
                        row.get('bio', ''),
                    )
                )
        self.stdout.write(
            self.style.SUCCESS('Пользователи загружены')
        )

    def import_categories(self, cursor):
        with open(
            self.get_csv_path('category.csv'),
            mode='r',
            encoding='utf-8'
        ) as file:
            reader = csv.DictReader(file)
            for row in reader:
                cursor.execute(
                    '''
                    INSERT OR IGNORE INTO reviews_category
                    (id, name, slug) VALUES (?, ?, ?)
                    ''',
                    (row['id'], row['name'], row['slug'])
                )
        self.stdout.write(
            self.style.SUCCESS('Категории загружены')
        )

    def import_genres(self, cursor):
        with open(
            self.get_csv_path('genre.csv'),
            mode='r',
            encoding='utf-8'
        ) as file:
            reader = csv.DictReader(file)
            for row in reader:
                cursor.execute(
                    '''
                    INSERT OR IGNORE INTO reviews_genre
                    (id, name, slug) VALUES (?, ?, ?)
                    ''',
                    (row['id'], row['name'], row['slug'])
                )
        self.stdout.write(
            self.style.SUCCESS('Жанры загружены')
        )

    def import_titles(self, cursor):
        with open(
            self.get_csv_path('titles.csv'),
            mode='r',
            encoding='utf-8'
        ) as file:
            reader = csv.DictReader(file)
            for row in reader:
                cursor.execute(
                    '''
                    INSERT OR IGNORE INTO reviews_title (
                        id, name, year, category_id, description
                    ) VALUES (?, ?, ?, ?, ?)
                    ''',
                    (row['id'], row['name'], row['year'], row['category'], '')
                )
        self.stdout.write(
            self.style.SUCCESS('Произведения загружены')
        )

    def import_genre_title(self, cursor):
        with open(
            self.get_csv_path('genre_title.csv'),
            mode='r',
            encoding='utf-8'
        ) as file:
            reader = csv.DictReader(file)
            for row in reader:
                cursor.execute(
                    '''
                    INSERT OR IGNORE INTO reviews_title_genre (
                        id, title_id, genre_id
                    ) VALUES (?, ?, ?)
                    ''',
                    (row['id'], row['title_id'], row['genre_id'])
                )
        self.stdout.write(
            self.style.SUCCESS('Связи жанр-произведение загружены')
        )

    def import_reviews(self, cursor):
        with open(
            self.get_csv_path('review.csv'),
            mode='r',
            encoding='utf-8'
        ) as file:
            reader = csv.DictReader(file)
            for row in reader:
                pub_date = datetime.strptime(
                    row['pub_date'], '%Y-%m-%dT%H:%M:%S.%fZ'
                ).isoformat()
                cursor.execute(
                    '''
                    INSERT OR IGNORE INTO reviews_review (
                        id, title_id, text, author_id, score, pub_date
                    ) VALUES (?, ?, ?, ?, ?, ?)
                    ''',
                    (
                        row['id'],
                        row['title_id'],
                        row['text'],
                        row['author'],
                        row['score'],
                        pub_date
                    )
                )
        self.stdout.write(
            self.style.SUCCESS('Отзывы загружены')
        )

    def import_comments(self, cursor):
        with open(
            self.get_csv_path('comments.csv'),
            mode='r',
            encoding='utf-8'
        ) as file:
            reader = csv.DictReader(file)
            for row in reader:
                pub_date = datetime.strptime(
                    row['pub_date'], '%Y-%m-%dT%H:%M:%S.%fZ'
                ).isoformat()
                cursor.execute(
                    '''
                    INSERT OR IGNORE INTO reviews_comment (
                        id, review_id, text, author_id, pub_date
                    ) VALUES (?, ?, ?, ?, ?)
                    ''',
                    (
                        row['id'],
                        row['review_id'],
                        row['text'],
                        row['author'],
                        pub_date
                    )
                )
        self.stdout.write(
            self.style.SUCCESS('Комментарии загружены')
        )
