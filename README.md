# YaMDb API — отзывы пользователей на произведения

## Описание:

Проект **YaMDb** собирает отзывы пользователей на **произведения**. Сами произведения в YaMDb не хранятся, 
здесь нельзя посмотреть фильм или послушать музыку.

Произведения делятся на **категории**, такие как «Книги», «Фильмы», «Музыка». Например, в категории 
«Книги» могут быть произведения «Винни-Пух и все-все-все» и «Марсианские хроники», а в категории 
«Музыка» — песня «Давеча» группы «Жуки» и вторая сюита Баха. Список категорий может быть расширен 
(например, можно добавить категорию «Изобразительное искусство» или «Ювелирка»). 

Произведению может быть присвоен **жанр** из списка предустановленных (например, «Сказка», «Рок» или 
«Артхаус»). 

Добавлять произведения, категории и жанры может только администратор.

Благодарные или возмущённые пользователи оставляют к произведениям текстовые **отзывы** и ставят 
произведению оценку в диапазоне от одного до десяти (целое число); из пользовательских оценок 
формируется усреднённая оценка произведения — **рейтинг** (целое число). На одно произведение 
пользователь может оставить только один отзыв.
Пользователи могут оставлять **комментарии** к отзывам.
Добавлять отзывы, комментарии и ставить оценки могут только аутентифицированные пользователи.

## Технологии:

![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)
![Django](https://img.shields.io/badge/django-%23092E20.svg?style=for-the-badge&logo=django&logoColor=white)
![DjangoREST](https://img.shields.io/badge/DJANGO-REST-ff1709?style=for-the-badge&logo=django&logoColor=white&color=ff1709&labelColor=gray)
![JWT](https://img.shields.io/badge/JWT-black?style=for-the-badge&logo=JSON%20web%20tokens)
![SQLite](https://img.shields.io/badge/sqlite-%2307405e.svg?style=for-the-badge&logo=sqlite&logoColor=white)
![Git](https://img.shields.io/badge/git-%23F05033.svg?style=for-the-badge&logo=git&logoColor=white)

## Установка:

Клонируйте репозиторий и перейдите в папку проекта:

```bash
git clone https://github.com/IonovN07/api_yamdb.git
cd api_yamdb
```

Создайте и активируйте виртуальное окружение:

```bash
python3 -m venv venv
source venv/bin/activate
```

Установите зависимости:

```bash
python3 -m pip install --upgrade pip
pip install -r requirements.txt
```

Выполните миграции:

```bash
python3 manage.py migrate
```

Загрузите данные (по желанию):

```bash
python3 manage.py base_import
```

Запустите сервер:

```bash
python3 manage.py runserver
```

## Документация:

Документация доступна по адресу:

```bash
http://127.0.0.1:8000/redoc/
```

## Импорт данных:

###  Импорт с путем по умолчанию:

```bash
  python manage.py import_db
```  

### Импорт с указанием кастомного пути:

```bash
  python manage.py import_db --path my_data/csv_files/
```

### Очистка данных перед импортом:

```bash
  python manage.py import_db --clear
```

### Комбинация параметров:

```bash
python manage.py import_db --path alternative_data/ --clear
```

## Тестирование: 

```bash
pytest
```

#### Коллекция запросов для Postman:
В директории **postman_collection** сохранена коллекция 
запросов для отладки и проверки работы текущей версии 
API для проекта YaMDB.

Подробная инструкция по работе с коллекцией находится в файле 
**/postman_collection/README.md**.

## Примеры запросов

Регистрация нового пользователя:
```code
POST http://127.0.0.1:8000/api/v1/auth/signup/

{
    "email": "user@example.com",
    "username": "^w\\Z"
}
```

Получение JWT-токена:
```code
POST http://127.0.0.1:8000/api/v1/auth/token/

{
"username": "^w\\Z",
"confirmation_code": "string"
}
```

Регистрация нового пользователя:
```code
GET http://127.0.0.1:8000/api/v1/users/

{
    "count": 0,
    "next": "string",
    "previous": "string",
    "results": [
        {}
    ]
}
```

Добавление пользователя:
```code
POST http://127.0.0.1:8000/api/v1/users/

{
    "username": "^w\\Z",
    "email": "user@example.com",
    "first_name": "string",
    "last_name": "string",
    "bio": "string",
    "role": "user"
}
```

## Авторы проекта:

- **Никита Ионов** — Team Lead, Модели, View, Эндпойнты
- **Андрей Рязанов** — Отзывы, Комментарии, Рейтинг, Импорт базы данных  
- **Максим Симченко** — Управление пользователями
