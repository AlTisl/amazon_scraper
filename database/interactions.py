from os import path
from sqlite3 import connect, Row
from typing import Any

def db_create_table(db_name: str) -> None:
    with connect(path.join('.', db_name)) as con:
        con.execute('''
            CREATE TABLE IF NOT EXISTS products (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                title           TEXT NOT NULL,
                url             TEXT NOT NULL UNIQUE,
                rating          REAL CHECK(rating IS NULL OR rating BETWEEN 0 AND 5),
                reviews         INTEGER CHECK(reviews IS NULL OR reviews >= 0),
                current_price   INTEGER CHECK(current_price IS NULL OR current_price >= 0),
                base_price      INTEGER CHECK(base_price IS NULL OR base_price >= 0),
                delivery        INTEGER NOT NULL DEFAULT 0 CHECK (delivery = 0 OR delivery = 1)
            )
        ''')
    con.close()

def db_insert(db_name: str, data: list[dict[str, Any]]) -> None:
    
    with connect(path.join('.', db_name)) as con:
        con.executemany('''
            INSERT INTO products(title, url, rating, reviews, current_price, base_price, delivery)
            VALUES(:title, :url, :rating, :reviews, :current_price, :original_price, :delivery_available)
''', data)
    con.close()

def db_select_all(db_name: str) -> list[dict[str, Any]]:
    with connect(path.join('.', db_name)) as con:
        con.row_factory = Row
        row = con.execute('''
                    SELECT title, url, rating, reviews,
                          CAST(current_price AS REAL)/100 AS current_price,
                          CAST(base_price AS REAL)/100 AS base_price,
                          (CASE delivery
                                WHEN 1 THEN 'Yes'
                                ELSE 'No'
                           END) AS delivery
                    FROM products
                    ''').fetchall()
    con.close()
    return row

def db_truncate_table(db_name: str) -> None:
    with connect(path.join('.', db_name)) as con:
        con.execute('DROP TABLE IF EXISTS products')
    con.close()
    db_create_table(db_name)

# Розрахунок середньої ціни товарів з рейтингом більшим за 4
def db_average_price(db_name: str) -> float:
    with connect(path.join('.', db_name)) as con:
        result = con.execute('''
                    SELECT AVG(CAST(current_price AS REAL)/100) AS avg_price
                    FROM products
                    ''').fetchone()
    con.close()
    return result[0]

# Визначення товару з найбільшим дисконтом
def db_max_discount(db_name: str) -> dict[str, Any]:
    with connect(path.join('.', db_name)) as con:
        con.row_factory = Row
        result = con.execute('''
                    SELECT title, url, rating, reviews,
                           CAST(current_price AS REAL)/100 AS current_price,
                           CAST(base_price AS REAL)/100 AS base_price,
                           (CASE delivery
                                WHEN 1 THEN 'Yes'
                                ELSE 'No'
                           END) AS delivery
                    FROM products
                    WHERE current_price IS NOT NULL AND base_price IS NOT NULL
                    ORDER BY (base_price - current_price) DESC
                    LIMIT 1
                    ''').fetchone()
    con.close()
    return result

# Три товари з найкращим співвідношенням рейтингу та ціни
def db_top_three(db_name: str) -> list[dict[str, Any]]:
    with connect(path.join('.', db_name)) as con:
        con.row_factory = Row
        result = con.execute('''
                    SELECT title, url, rating, reviews,
                           CAST(current_price AS REAL)/100 AS current_price,
                           CAST(base_price AS REAL)/100 AS base_price,
                           (CASE delivery
                                WHEN 1 THEN 'Yes'
                                ELSE 'No'
                           END) AS delivery
                    FROM products
                    WHERE current_price IS NOT NULL AND rating IS NOT NULL
                    ORDER BY (rating / current_price) DESC
                    LIMIT 3
                    ''').fetchall()
    con.close()
    return result
