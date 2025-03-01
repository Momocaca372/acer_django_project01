import requests
from bs4 import BeautifulSoup
import concurrent.futures

"""只爬取家樂福的商品資料，並存成[{}]的格式"""

# 設置 headers 模擬瀏覽器行為，防止被封鎖
my_headers = {
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36"
}

# 家樂福的首頁 URL
url = 'https://online.carrefour.com.tw/zh/homepage/'

def get_soup(url):
    """發送 GET 請求並返回解析後的 BeautifulSoup 對象"""
    try:
        response = requests.get(url, headers=my_headers, timeout=10)
        if response.status_code == 200:
            return BeautifulSoup(response.text, 'html.parser')
    except requests.RequestException as e:
        print(f"請求失敗: {url}, 錯誤: {e}")
    return None

def get_category_links():
    """獲取所有商品分類的鏈接"""
    soup = get_soup(url)
    if soup:
        # 提取所有分類的鏈接
        category_links = ['https://online.carrefour.com.tw' + a.get('href') for a in soup.find_all('a', class_='category-panel-label')]
        return category_links[9:]
    return []

def scrape_category_page(category_url):
    """抓取某一分類頁面的所有商品"""
    all_products = []
    page = 0
    while True:
        paginated_url = f"{category_url}?start={page * 24}"
        soup = get_soup(paginated_url)
        if not soup:
            break

        # 提取分類名稱
        try:
            category = soup.select('div.crumbs a')[-1].text.split('/')[1].strip()
        except (IndexError, AttributeError):
            category = "未知分類"

        # 提取商品信息
        products = soup.select('div.desc-operation-wrapper a')
        prices = soup.find_all('div', class_='current-price')
        img_urls = soup.select('div.box-img img')

        for product, price, img_url in zip(products, prices, img_urls):
            title = product.text
            product_url = product.get('href')
            price = price.text.split('$')[1].strip()
            img_url = img_url.get('src')[31:]

            all_products.append({
                'name': title,
                'price': price,
                'img_url': img_url,
                'product_url': product_url,
                'category': category,
                'store': 'carrefour'
            })

            print(title, product_url, price, category)
        
        # 如果該頁面沒有更多商品則停止
        if len(products) < 24:
            break

        page += 1

    return all_products

def scrape_all_products():
    """抓取所有分類的商品，使用併發來加速"""
    category_urls = get_category_links()
    all_products = []

    # 使用 ThreadPoolExecutor 來並行抓取各個分類頁面
    with concurrent.futures.ThreadPoolExecutor() as executor:
        results = executor.map(scrape_category_page, category_urls)
        for result in results:
            all_products.extend(result)

    return all_products

# 執行爬蟲並打印結果
if __name__ == "__main__":
    products = scrape_all_products()
    print(f"總共抓取了 {len(products)} 個商品")