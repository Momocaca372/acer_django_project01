import requests
from bs4 import BeautifulSoup
import concurrent.futures
"""這隻程式碼只擷取好事多所有商品的函數"""

# 設置 headers，模擬瀏覽器行為，防止請求被拒絕
my_headers = {
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36"
}

# 設定好事多線上商城的首頁 URL
url = 'https://www.costco.com.tw/'

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
        link_list = [a.get('href') for a in soup.select('ul#theMenu > li > ul > li > a.ng-star-inserted')]
        link_list = list(filter(lambda x: x != 'javascript:void(0)' and x != 'https://www.costco.com.tw/Televisions-Appliances/c/395', link_list))  # 過濾掉無效鏈接
        return link_list[20:88] 
    return []  # 若請求失敗或無分類則返回空列表
a = get_category_links()
# def scrape_category_page(category_url):
#     """抓取某一分類頁面的所有商品"""
#     all_products = []
#     page = 0
#     while True:
#         paginated_url = category_url if page == 0 else f"{category_url}?page={page}"
#         print(paginated_url)
#         soup = get_soup(paginated_url)
#         if not soup:
#             break
        
#         # 提取分類名稱
#         try:
#             category = soup.select('div.breadcrumb-section a')[-2].text.strip()
#         except (IndexError, AttributeError):
#             category = "未知分類"    
        
#         # 提取商品信息
#         products = soup.find_all('a',class_='lister-name js-lister-name')
#         prices = soup.select('div.product-price span.notranslate')
#         img_urls = soup.select('div.product-image > a > sip-primary-image > sip-media > picture > img')
        
#         for product, price, img_url in zip(products, prices, img_urls):
#             title = product.text
#             product_url = product.get('href').replace('https://www.costco.com.tw', '')
#             # try:
#             price = price.text.split('$')[1].strip()
#             # except IndexError:
#             #     price = "未知價格"
#             img_url = img_url.get('src').replace('https://www.costco.com.tw', '')
        
#             all_products.append({
#                 'name': title,
#                 'price': price,
#                 'img_url': img_url,
#                 'product_url': product_url,
#                 'category': category,
#                 'store': 'costco'
#             })
        
#             print(title, price, category)
            
#             # 如果該頁面沒有更多商品則停止
#         if len(products) < 48:
#             break
        
#         page += 1
#     return all_products

# def scrape_all_products():
#     """抓取所有分類的商品，使用併發來加速"""
#     category_urls = get_category_links()
#     all_products = []

#     # 使用 ThreadPoolExecutor 來並行抓取各個分類頁面
#     with concurrent.futures.ThreadPoolExecutor() as executor:
#         results = executor.map(scrape_category_page, category_urls)
#         for result in results:
#             all_products.extend(result)

#     return all_products

# # 執行爬蟲並打印結果
# if __name__ == "__main__":
#     products = scrape_all_products()
#     print(f"總共抓取了 {len(products)} 個商品")