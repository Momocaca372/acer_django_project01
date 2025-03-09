import sqlite3
import pathlib
import json
# 連接 SQLite 資料庫
# 此函式返回 SQLite 連線 (conn) 和游標 (cursor)
def get_db_connection():
    base_path = pathlib.Path(__file__).parent  # 獲取當前腳本所在目錄
    db_path = base_path / "BIBIGOproject" 
    conn = sqlite3.connect(db_path / "db.sqlite3")  # 連接 SQLite 資料庫
    cursor = conn.cursor()
    return conn, cursor

# 將爬取到的商品資訊存入 SQLite 資料庫
# 若商品網址已存在則不新增
def save_to_db(products):
    # 取得資料庫連接和游標
    conn, cursor = get_db_connection()

    for product in products:
        store_name = product['store']
        # 查找店家是否已存在
        cursor.execute('SELECT id FROM myapp_store WHERE name = ?', (store_name,))
        store_id = cursor.fetchone()
        if store_id is None:
            # 若店家不存在，則新增店家（不需要指定 id，資料庫會自動遞增）
            cursor.execute('INSERT INTO myapp_store (name) VALUES (?)', (store_name,))
            store_id = cursor.lastrowid  # 取得插入後的自動生成 id
        else:
            store_id = store_id[0]

        category_name = product['category']
        # 查找商品類別是否已存在
        cursor.execute('SELECT id FROM myapp_category WHERE name = ?', (category_name,))
        category_id = cursor.fetchone()
        if category_id is None:
            # 若類別不存在，則新增類別
            cursor.execute('INSERT INTO myapp_category (store_id, name) VALUES (?, ?)', (store_id, category_name))
            category_id = cursor.lastrowid
        else:
            category_id = category_id[0]

        # 檢查商品網址是否已存在，若已存在則跳過
        cursor.execute('SELECT id FROM myapp_product WHERE product_url = ?', (product['product_url'],))
        if cursor.fetchone() is not None:
            continue  # 若網址已存在，跳過這筆資料

        # 儲存商品詳細資訊到 product_detail 表
        cursor.execute(''' 
            INSERT INTO myapp_product (store_id, category_id, name, price, img_url, product_url) 
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            store_id, 
            category_id, 
            product['name'], 
            product['price'], 
            product['img_url'], 
            product['product_url']
        ))

    # 提交所有變更並關閉連線
    conn.commit()
    conn.close()
    print(f"成功存入 {len(products)} 筆資料（不包含重複網址商品）")


# 主程式
if __name__ == '__main__':
    with open('product.json', 'r', encoding='utf-8') as file:
       all_products = json.load(file) 
    save_to_db(all_products)  # 將商品存入資料庫