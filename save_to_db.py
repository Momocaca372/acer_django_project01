import sqlite3
import crawl_controler
import pathlib

# 連接 SQLite 資料庫
# 此函式返回 SQLite 連線 (conn) 和游標 (cursor)
def get_db_connection():
    base_path = pathlib.Path(__file__).parent  # 獲取當前腳本所在目錄
    db_path = base_path / "bigdata" 
    conn = sqlite3.connect(db_path / "db.sqlite3")  # 連接 SQLite 資料庫
    cursor = conn.cursor()
    return conn, cursor

# 建立資料表
# 若資料表不存在，則建立 store、category、product、product_detail

def create_table():
    conn, cursor = get_db_connection()
    
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

# 將爬取到的商品資訊存入 SQLite 資料庫
# 若商品網址已存在則不新增
def save_to_db(products):
    conn, cursor = get_db_connection()

    for product in products:
        store_name = product['store']
        # 查找店家是否已存在
        cursor.execute('SELECT id FROM store WHERE name = ?', (store_name,))
        store_id = cursor.fetchone()
        if store_id is None:
            # 若店家不存在，則新增店家
            cursor.execute('INSERT INTO store (name) VALUES (?)', (store_name,))
            store_id = cursor.lastrowid
        else:
            store_id = store_id[0]

        category_name = product['category']
        # 查找商品類別是否已存在
        cursor.execute('SELECT id FROM category WHERE name = ?', (category_name,))
        category_id = cursor.fetchone()
        if category_id is None:
            # 若類別不存在，則新增類別
            cursor.execute('INSERT INTO category (store_id, name) VALUES (?, ?)', (store_id, category_name))
            category_id = cursor.lastrowid
        else:
            category_id = category_id[0]

        # 檢查商品網址是否已存在，若已存在則跳過
        cursor.execute('SELECT id FROM product_detail WHERE product_url = ?', (product['product_url'],))
        if cursor.fetchone() is not None:
            continue

        # 儲存商品到 product 表
        cursor.execute('''
            INSERT INTO product (store_id, category_id) 
            VALUES (?, ?)
        ''', (store_id, category_id))
        product_id = cursor.lastrowid

        # 儲存商品詳細資訊到 product_detail 表
        cursor.execute('''
            INSERT INTO product_detail (product_id, name, price, image_url, product_url)
            VALUES (?, ?, ?, ?, ?)
        ''', (product_id, product['name'], product['price'], product['img_url'], product['product_url']))

    # 提交變更並關閉連線
    conn.commit()
    conn.close()
    print(f"成功存入 {len(products)} 筆資料（不包含重複網址商品）")

# 主程式
if __name__ == '__main__':
    # all_products = crawl_controler.Crawl.carrefour()
    create_table()
    all_products = crawl_controler.Crawl.costco()  # 從爬蟲控制器獲取商品資料
    save_to_db(all_products)  # 將商品存入資料庫