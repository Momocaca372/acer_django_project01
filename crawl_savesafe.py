import time
import re
import sqlite3
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from concurrent.futures import ThreadPoolExecutor

# === 設置 SQLite 資料庫 ===
DB_NAME = "savesafe.db"

def setup_database():
    """
    初始化資料庫並創建所需的資料表。
    資料表包括 store, category, product 和 product_detail。
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # 建立 store 資料表 (存儲商店名稱)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS store (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE
    )""")

    # 建立 category 資料表 (存儲每個商店的分類)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS category (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        store_id INTEGER,
        name TEXT,
        FOREIGN KEY (store_id) REFERENCES store (id),
        UNIQUE (store_id, name)
    )""")

    # 建立 product 資料表 (存儲每個商店的商品)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS product (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        store_id INTEGER,
        category_id INTEGER,
        FOREIGN KEY (store_id) REFERENCES store (id),
        FOREIGN KEY (category_id) REFERENCES category (id)
    )""")

    # 建立 product_detail 資料表 (存儲商品詳細資訊)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS product_detail (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_id INTEGER,
        name TEXT,
        image_url TEXT,
        product_url TEXT,
        price DECIMAL(10,2),
        FOREIGN KEY (product_id) REFERENCES product (id),
        UNIQUE (product_id, product_url)
    )""")

    conn.commit()
    conn.close()

# === 插入資料到資料庫 ===
def insert_data(store_name, category_name, product_name, product_url, price, image_url):
    """
    插入商店、分類、商品及其詳細資訊到資料庫。
    確保資料表中有相應的商店、分類和商品，不會重複插入。

    :param store_name: 商店名稱
    :param category_name: 商品分類
    :param product_name: 商品名稱
    :param product_url: 商品網址
    :param price: 商品價格
    :param image_url: 商品圖片網址
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # 確保店家存在
    cursor.execute("INSERT OR IGNORE INTO store (name) VALUES (?)", (store_name,))
    cursor.execute("SELECT id FROM store WHERE name = ?", (store_name,))
    store_id = cursor.fetchone()[0]

    # 確保分類存在
    cursor.execute("INSERT OR IGNORE INTO category (store_id, name) VALUES (?, ?)", (store_id, category_name))
    cursor.execute("SELECT id FROM category WHERE store_id = ? AND name = ?", (store_id, category_name))
    category_id = cursor.fetchone()[0]

    # 確保商品存在
    cursor.execute("INSERT OR IGNORE INTO product (store_id, category_id) VALUES (?, ?)", (store_id, category_id))
    cursor.execute("SELECT id FROM product WHERE store_id = ? AND category_id = ?", (store_id, category_id))
    product_id = cursor.fetchone()[0]

    # 插入商品詳細資訊
    cursor.execute("""
    INSERT OR IGNORE INTO product_detail (product_id, name, image_url, product_url, price)
    VALUES (?, ?, ?, ?, ?)""", (product_id, product_name, image_url, product_url, price))

    conn.commit()
    conn.close()
    print(f"✅ {product_name} 已存入資料庫")

# === 設置 Selenium 爬取 ===
chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")

# === 爬取商品詳細資訊 ===
def get_product_details(driver, url):
    """
    從指定的商品頁面抓取商品詳細資訊，包括標題、價格、圖片及分類，
    然後將這些資訊存入資料庫。

    :param driver: Selenium 的 WebDriver 物件，用來操作瀏覽器
    :param url: 商品的詳細頁面網址
    """
    driver.get(url)
    try:
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'h4.h2-responsive.product-name')))

        # ✅ 抓取標題
        try:
            title_element = driver.find_element(By.CSS_SELECTOR, 'h4.h2-responsive.product-name')
            title = title_element.text.strip()
            title = re.sub(r'\s*<span>.*?</span>\s*', '', title)  # 移除 <span> 內的內容
        except:
            title = "無標題"

        # ✅ 抓取價格
        try:
            price_element = driver.find_element(By.CSS_SELECTOR, 'span.SalePrice.text-danger')
            price = re.sub(r"[^\d.]", "", price_element.text.strip())  # 移除非數字字元
        except:
            price = "0.00"

        # ✅ 抓取主圖片
        try:
            main_img = driver.find_element(By.CSS_SELECTOR, 'div.clearfix a#cgo img#mainImg')
            img_src = main_img.get_attribute("src")
        except:
            img_src = "無圖片"

        # ✅ 抓取分類 (麵包屑)
        try:
            breadcrumb = driver.find_element(By.CSS_SELECTOR, 'li.breadcrumb-item.active')
            category = breadcrumb.text.strip()
        except:
            category = "無分類"

        print(f"📌 標題: {title}")
        print(f"📂 分類: {category}")
        print(f"💰 價格: {price}")
        print(f"🖼 圖片: {img_src}")

        # ✅ 立即存入 SQLite
        insert_data("SaveSafe", category, title, url, price, img_src)

    except Exception as e:
        print(f"❌ 獲取 {url} 詳情時發生錯誤: {e}")

# === 訪問分類頁面 ===
def visit_link(url):
    """
    訪問一個分類頁面，並抓取頁面上的所有產品鏈接，然後逐一進入每個商品頁面進行資料爬取。

    :param url: 分類頁面的 URL
    """
    driver = webdriver.Chrome(options=chrome_options)
    try:
        driver.get(url)
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'ul.ThirdNavItemList.d-flex')))

        # ✅ 提取產品鏈接
        product_links = {p.get_attribute('href') for p in driver.find_elements(By.CSS_SELECTOR, 'div.card.hoverable a.text-center')}
        print(f"🔍 找到 {len(product_links)} 個產品")

        # ✅ 進入每個產品頁面，邊爬邊寫入資料庫
        for product_url in product_links:
            get_product_details(driver, product_url)

    finally:
        driver.quit()

# === 主函數 ===
def main():
    """
    主函數，設置資料庫並啟動爬蟲，抓取分類頁面的產品鏈接，
    並使用多線程並行處理每個分類頁面。
    """
    setup_database()  # 初始化資料庫

    driver = webdriver.Chrome(options=chrome_options)
    try:
        driver.get("https://www.savesafe.com.tw/")
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'ul.ThirdNavItemList.d-flex')))

        # ✅ 提取分類頁面鏈接
        linklist = {a.get_attribute('href') for a in driver.find_elements(By.CSS_SELECTOR, 'ul.ThirdNavItemList.d-flex li a')}
        print(f"🌍 找到 {len(linklist)} 個分類頁面")
    finally:
        driver.quit()

    # ✅ 多線程處理分類頁面
    with ThreadPoolExecutor(max_workers=5) as executor:
        executor.map(visit_link, linklist)

if __name__ == "__main__":
    main()
