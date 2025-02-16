import requests
from bs4 import BeautifulSoup
import csv
import concurrent.futures

# 設置 headers，模擬瀏覽器行為，防止請求被拒絕
my_headers = {
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36"
}

# 設定家樂福線上商城的首頁 URL
url = 'https://online.carrefour.com.tw/zh/homepage/'

# CSV 檔案名稱
csv_filename = 'carrefour.csv'


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
    return []


def scrape_product_page(product_url):
    """爬取單個商品頁面的詳細資訊"""
    soup = get_soup(product_url)
    if not soup:
        return None

    try:
        title = soup.select_one('div.title h1').text.strip()
        price = soup.find('span', class_='money').text.strip()
        img_url = 'https://online.carrefour.com.tw' + soup.select_one('div.preview-wrapper img').get('src')
        print(title,price)
        return {'name': title, 'money': price, 'img': img_url, 'link': product_url}
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
        print(f"類別數: {len(product_links):d}")
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


def main():
    """主執行函式，負責控制爬取流程並將結果寫入 CSV"""
    category_links = get_category_links()

    # 開啟 CSV 檔案
    with open(csv_filename, 'w', encoding='utf-8', newline='') as file:
        fieldnames = ['name', 'money', 'img', 'link']
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()

        # 使用 ThreadPoolExecutor 並發抓取分類頁面
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            results = executor.map(scrape_category_page, category_links)
        
        # 寫入所有商品數據
        for product_list in results:
            for product in product_list:
                writer.writerow(product)

        print("爬取完成，數據已寫入", csv_filename)


if __name__ == '__main__':
    main()
