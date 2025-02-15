import requests
from bs4 import BeautifulSoup
import sqlite3
import concurrent.futures
import os
import BIBIGOproject.Myproject.settings as settings

# 設置 headers，模擬瀏覽器行為，防止請求被拒絕
my_headers = {
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36"
}

# 設定家樂福線上商城的首頁 URL
url = 'https://online.carrefour.com.tw/zh/homepage/'

# 連接 SQLite 資料庫
conn = sqlite3.connect(os.path.join(settings.BASE_DIR,'db.sqlite3'))
cursor = conn.cursor()

# 建立資料表（如果不存在）
cursor.execute('''
    CREATE TABLE IF NOT EXISTS product_talbe (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        price TEXT,
        img_url TEXT,
        link TEXT,
        classification TEXT
        store TEXT
    )
''')
conn.commit()


def get_soup(url):
    """發送 GET 請求並回傳 BeautifulSoup 解析後的內容"""
    try:
        response = requests.get(url, headers=my_headers, timeout=10)
        if response.status_code == 200:
            return BeautifulSoup(response.text, 'html.parser')
    except requests.RequestException as e:
        print(f"請求失敗: {url}, 錯誤: {e}")
    return None


def get_category_links():
    """抓取所有商品分類的鏈接"""
    soup = get_soup(url)
    if soup:
        return ['https://online.carrefour.com.tw' + a.get('href') for a in soup.find_all('a', class_='category-panel-item')]
    return []  # 修正：避免返回 None


def scrape_product_page(product_url):
    """爬取單個商品頁面的詳細資訊"""
    soup = get_soup(product_url)
    if not soup:
        return None

    try:
        title = soup.select_one('div.title h1').text.strip()
        price = soup.find('span', class_='money').text.strip()
        img_url = 'https://online.carrefour.com.tw' + soup.select_one('div.preview-wrapper img').get('src')

        # 抓取分類，如果找不到，則設定為 "未知分類"
        try:
            classification = soup.select('div.crumbs a')[3].text.split('/')[1].strip()
        except (IndexError, AttributeError):
            classification = "未知分類"

        print(f'商品: {title}, 價格: {price}, 分類: {classification}')
        return {'name': title, 'price': price, 'img_url': img_url, 'link': product_url, 'classification': classification,'store':'carrefour'}
    except AttributeError:
        return None


def scrape_category_page(category_url):
    """爬取分類頁面內的所有商品"""
    product_data = []
    while category_url:
        soup = get_soup(category_url)
        if not soup:
            break

        # 找出商品的詳細頁面鏈接
        product_links = ['https://online.carrefour.com.tw' + a.get('href') for a in soup.select('div.box-img a')]
        print(f"發現 {len(product_links)} 件商品")

        # 使用多執行緒爬取所有商品詳情
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            results = executor.map(scrape_product_page, product_links)

        # 收集有效的商品數據
        product_data.extend(filter(None, results))

        # 找下一頁的 URL
        try:
            next_page = soup.select('div.pagenation a')[-2].get('onclick').split("'")[1]
            category_url = next_page if next_page else None
        except (IndexError, AttributeError):
            category_url = None  # 沒有下一頁則停止

    return product_data


def save_to_db(products):
    """將爬取到的商品資訊存入 SQLite 資料庫"""
    for product in products:
        cursor.execute('''
            INSERT INTO products (name, price, img_url, link, classification)
            VALUES (?, ?, ?, ?, ?)
        ''', (product['name'], product['price'], product['img_url'], product['link'], product['classification'],product['store']))
    conn.commit()
    print(f"成功存入 {len(products)} 筆資料")


if __name__ == '__main__':
    category_links = get_category_links()[1:2]

    if category_links:
        all_products = []
        for category_url in category_links:
            print(f"正在爬取分類頁面: {category_url}")
            products = scrape_category_page(category_url)
            all_products.extend(products)

        # 儲存數據到 SQLite
        if all_products:
            save_to_db(all_products)

    # 關閉資料庫連接
    conn.close()