from sqlite3 import connect, Row
from typing import Any

def db_create_table(db_name: str):
    with connect('.\\' + db_name) as con:
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

def db_insert(db_name: str, data: list[dict[str, Any]]):
    
    with connect('.\\' + db_name) as con:
        con.executemany('''
            INSERT INTO products(title, url, rating, reviews, current_price, base_price, delivery)
            VALUES(:title, :url, :rating, :reviews, :current_price, :original_price, :delivery_available)
''', data)
    con.close()

def db_select_all(db_name: str) -> list[dict[str, Any]]:
    with connect('.\\' + db_name) as con:
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

def db_truncate_table(db_name: str):
    with connect('.\\' + db_name) as con:
        con.execute('DROP TABLE IF EXISTS products')
    con.close()
    db_create_table(db_name)