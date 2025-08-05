# amazon_scraper
Скрипт призначений для скрапінга даних з сайту www.amazon.com.  
Написаний на Python з використанням бібліотеки Selenium. Для зберігання результатів використовується база даних SQLite.

## Встановлення та запуск
1. Клонуйте репозиторій та перейдіть до директорії проєкта:
    ```
    git clone https://github.com/AlTisl/amazon_scraper.git
    cd amazon_scraper
    ```
2. Створіть віртуальне оточення:
    ```
    python -m venv venv
    source venv/bin/activate  # для Linux/Mac
    venv\Scripts\activate     # для Windows
    ```
3. Встановіть необхідні залежності з файлу requirements.txt:
    ```
    pip install -r requirements.txt
    ```
4. Запустіть виконання скрипта командою:
   ```
   python main.py --query <ключові слова> --pages <кількість сторінок пошуку> --db <файл бази даних>
   ```
   Вказані параметри є опціональними. За замовчуванням використовуються наступні значення:
   ```
   query: 'laptop'
   pages: 5
   db: 'amazon.db'
