import sqlite3
import os
import BIBIGOproject.Myproject.settings as settings


# 連接 SQLite 資料庫
def get_db_connection():
    conn = sqlite3.connect(os.path.join(settings.BASE_DIR,'db.sqlite3'))
    cursor = conn.cursor()
    return conn,cursor

def create_table(conn,cursor):
    # 建立 store 表（店家表）
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS store (
        id   INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL
    )
    ''')

    # 建立 category 表（商品類別表）
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS category (
        id       INTEGER PRIMARY KEY AUTOINCREMENT,
        store_id INTEGER NOT NULL,
        name     TEXT NOT NULL,
        FOREIGN KEY (store_id) REFERENCES store(id) ON DELETE CASCADE
    )
    ''')

    # 建立 product 表（商品表）
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS product (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        store_id    INTEGER NOT NULL,
        category_id INTEGER NOT NULL,
        FOREIGN KEY (store_id) REFERENCES store(id) ON DELETE CASCADE,
        FOREIGN KEY (category_id) REFERENCES category(id) ON DELETE CASCADE
    )
    ''')

    # 建立 product_detail 表（商品詳細資訊表）
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS product_detail (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        product_id  INTEGER NOT NULL,
        name        TEXT NOT NULL,
        price       DECIMAL(10,2) NOT NULL,
        image_url   TEXT,
        product_url TEXT,
        FOREIGN KEY (product_id) REFERENCES product(id) ON DELETE CASCADE
    )
    ''')

    # 提交變更並關閉連線
    conn.commit()
    conn.close()