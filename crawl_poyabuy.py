import os
import sqlite3
import json
from time import sleep
from selenium.webdriver import Chrome
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup as bs

import BIBIGOproject.Myproject.settings as settings
import databaseCreate
from tqdm import tqdm 
# 宣告參數
url = "https://www.poyabuy.com.tw/v2/official/SalePageCategory/0?sortMode=Newest"
poya_base_url = 'https://www.poyabuy.com.tw'

def connect_sqlite():
    """連接 SQLite，並返回 conn & cursor"""
    conn = sqlite3.connect(os.path.join(settings.BASE_DIR, 'db.sqlite3'))
    cursor = conn.cursor()
    return conn, cursor

def get_category_index():
    """爬取類別列表，並存入 `category` 資料表（如果分類不存在則新增）"""
    
    driver = Chrome()
    driver.get(url)
    driver.implicitly_wait(10)

    # 取得所有分類按鈕的名稱
    category_buttons = driver.find_elements(By.CLASS_NAME, "sc-kZCGdI.jmFZfR")
    category_names = []
            
        
        
    for btn in tqdm(category_buttons[9:]):  # 從 index=9 開始抓取
        category_names.append(btn.text)
        if btn.text == "男士保養":  # 碰到 "男士保養" 停止
            break

    driver.quit()  # 關閉瀏覽器

    print(f"發現 {len(category_names)} 個分類: {category_names}")

    # 存入 SQLite，避免重複插入
    conn, cursor = connect_sqlite()
    
    category_id_map = {}  # 用來存分類名稱對應的 ID
    store_id = cursor.execute("SELECT id FROM store WHERE name = ?", ('poyabuy',)).fetchone()
    
    for name in tqdm(category_names):
        
        # 先檢查分類是否已存在
        cursor.execute("SELECT id FROM category WHERE name = ?", (name,))
        result = cursor.fetchone()
        
        if result:
            category_id_map[name] = result[0]  # 取得已存在的 category_id
        else:
            # 不存在則新增分類
            print(store_id[0], name)
            cursor.execute("INSERT INTO category (store_id, name) VALUES (?, ?)", (store_id[0], name))
            category_id_map[name] = cursor.lastrowid  # 取得剛插入的 category_id

    conn.commit()
    conn.close()

    return range(9, 9 + len(category_names)), category_id_map  # 回傳分類索引與 ID 對應表

def fetch_category_url(index, category_id_map):
    """滾動到底部，爬取商品資訊，並存入 `product_detail` 和 `productl`"""
    
    driver = Chrome()
    wait = WebDriverWait(driver, 10, poll_frequency=0.5)
    driver.get(url)
    driver.implicitly_wait(10)
    sleep(3)
    # 點擊分類按鈕
    for _ in range(50):
        try:
            category_buttons = driver.find_elements(By.CLASS_NAME, "sc-kZCGdI.jmFZfR")

            category_buttons[index].click()
            break
        except:
            category_buttons[0].send_keys(Keys.ARROW_DOWN)
    try:        
        wait.until(EC.url_changes(driver.current_url))  # 等待 URL 變更
    except:
        pass
    # 獲取分類名稱
    category_name = driver.find_element(By.CLASS_NAME, "sc-jdiFFc.ihCGgx").text
    print(f"開始爬取分類: {category_name}")

    # 確保分類存在於 `category` 表
    category_id = category_id_map.get(category_name)
    if not category_id:
        print(f"警告：分類 {category_name} 不存在於資料庫，跳過該分類")
        driver.quit()
        return

    # 滾動到最底部，確保所有商品都載入
    last_height = driver.execute_script("return document.body.scrollHeight")
    while True:
        driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.END)
        sleep(2)  # 等待新內容載入
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break  # 如果頁面高度不再變化，代表已經載入完畢
        last_height = new_height

    #  取得完整 HTML，然後用 bs4 解析
    soup = bs(driver.page_source, "html.parser")

    # 爬取商品資訊
    products = soup.find_all("li", class_="column-grid-container__column")
    product_list = []
    
    for product in tqdm(products):
        try:
            #  檢查是否包含 mask 層（如果有就跳過）
            mask = product.find("div", class_="sc-hfiVbt hGbyjb")
            if mask:
                continue
            
            #  使用 `bs4` 解析商品資訊
            product_name = product.find("div", class_="sc-bxgxFH xMesR").text.strip()
            product_price = product.find("div", class_="sc-jEjhTi djfehP").text.replace("$", "").strip()
            product_image_url = product.find("img")["src"]
            product_url = product.find("a")["href"]
    
            product_list.append((product_name, product_price, product_image_url, product_url))
    
        except Exception as e:
            print(f"爬取商品時發生錯誤: {e}")

    # 存入 SQLite
    conn, cursor = connect_sqlite()

    # 插入商品資訊到 `product_detail`，但先檢查 product_url 是否已存在
    for product_name, product_price, product_image_url, product_url in tqdm(product_list):
        cursor.execute("SELECT id FROM product_detail WHERE product_url = ?", (product_url,))
        existing_product = cursor.fetchone()

        if not existing_product:  # 如果資料庫沒有這個 product_url，則新增
            # 插入關聯到 `productl`
            cursor.execute("""
                INSERT INTO product (store_id, category_id, id)
                VALUES (?, ?, ?)
            """, (1, category_id, None))
            
            # 取得剛剛插入的 `product_id`
            product_id = cursor.lastrowid
            
            cursor.execute("""
                INSERT INTO product_detail (product_id, name, price, image_url, product_url)
                VALUES (?, ?, ?, ?, ?)
            """, (product_id, product_name, product_price, product_image_url, product_url))

            



    conn.commit()
    conn.close()
    driver.quit()

if __name__ == '__main__':
    # 取得所有分類，存入 category 表，並獲取分類 ID 對應表
    poya_index, category_id_map = get_category_index()
    

    for i in poya_index:
      fetch_category_url(i, category_id_map)
