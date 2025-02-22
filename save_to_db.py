import sqlite3
import os
import BIBIGOproject.Myproject.settings as settings
import crawl_controler

# 連接 SQLite 資料庫
def get_db_connection():
    conn = sqlite3.connect(os.path.join(settings.BASE_DIR,'db.sqlite3'))
    cursor = conn.cursor()
    return conn,cursor


def create_table():
    conn,cursor = get_db_connection()
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

def save_to_db(products):
    """將爬取到的商品資訊存入 SQLite 資料庫"""
    conn = get_db_connection()
    cursor = conn.cursor()

    # 儲存店家資訊（如果店家不存在，則新增）
    for product in products:
        store_name = product['store']
        cursor.execute('SELECT id FROM store WHERE name = ?', (store_name,))
        store_id = cursor.fetchone()
        if store_id is None:
            cursor.execute('INSERT INTO store (name) VALUES (?)', (store_name,))
            store_id = cursor.lastrowid
        else:
            store_id = store_id[0]

    # 儲存商品類別
        category_name = product['category']
        cursor.execute('SELECT id FROM category WHERE name = ? AND store_id = ?', (category_name, store_id))
        category_id = cursor.fetchone()
        if category_id is None:
            cursor.execute('INSERT INTO category (store_id, name) VALUES (?, ?)', (store_id, category_name))
            category_id = cursor.lastrowid
        else:
            category_id = category_id[0]

    # 儲存商品
        cursor.execute('''
            INSERT INTO product (store_id, category_id) 
            VALUES (?, ?)
        ''', (store_id, category_id))
        product_id = cursor.lastrowid

    # 儲存商品詳細資訊
        cursor.execute('''
            INSERT INTO product_detail (product_id, name, price, image_url, product_url)
            VALUES (?, ?, ?, ?, ?)
        ''', (product_id, product['name'], product['price'], product['img_url'], product['product_url']))

    conn.commit()
    conn.close()
    print(f"成功存入 {len(products)} 筆資料")
    
if __name__ == '__main__':

    all_products = crawl_controler.carrefour
    save_to_db(all_products)