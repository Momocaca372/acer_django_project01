import sqlite3
import os
import BIBIGOproject.Myproject.settings as settings

# 連接 SQLite 資料庫
conn = sqlite3.connect(os.path.join(settings.BASE_DIR,'db.sqlite3'))
cursor = conn.cursor()

cursor.execute('''CREATE TABLE IF NOT EXISTS store (
    id   INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL)'''
    )

cursor.execute('''CREATE TABLE IF NOT EXISTS category (
    id       INTEGER PRIMARY KEY AUTOINCREMENT,
    store_id INTEGER NOT NULL,
    name     TEXT NOT NULL,
    FOREIGN KEY (store_id) REFERENCES store(id) ON DELETE CASCADE)'''
    )

cursor.execute('''CREATE TABLE IF NOT EXISTS product (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    store_id    INTEGER NOT NULL,
    category_id INTEGER NOT NULL,
    name        TEXT NOT NULL,
    FOREIGN KEY (store_id) REFERENCES store(id) ON DELETE CASCADE,
    FOREIGN KEY (category_id) REFERENCES category(id) ON DELETE CASCADE)'''
    )

cursor.execute('''CREATE TABLE IF NOT EXISTS product_detail (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL,
    description TEXT,
    price      DECIMAL(10,2) NOT NULL,
    stock      INTEGER NOT NULL,
    FOREIGN KEY (product_id) REFERENCES product(id) ON DELETE CASCADE)'''
    )