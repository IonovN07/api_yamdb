# Текст для теста
сам текст
## Импорт данных
###  Импорт с путем по умолчанию:
```
  python manage.py import_db
```  
### Импорт с указанием кастомного пути:
```
  python manage.py import_db --path my_data/csv_files/
```
### Очистка данных перед импортом:
```
  python manage.py import_db --clear
```
### Комбинация параметров:
```
python manage.py import_db --path alternative_data/ --clear
```

