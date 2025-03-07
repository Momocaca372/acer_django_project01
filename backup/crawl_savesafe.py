import ssl
import requests
from requests.adapters import HTTPAdapter
from urllib3.poolmanager import PoolManager
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
import time

# 自定義的 SSL Adapter，降低安全等級以允許較小的 DH 金鑰
class SSLAdapter(HTTPAdapter):
    def init_poolmanager(self, connections, maxsize, block=False):
        # 創建一個默認的 SSL 上下文
        ctx = ssl.create_default_context()
        # 設置加密套件的安全等級為 1，允許較小的 DH 金鑰
        ctx.set_ciphers('DEFAULT:@SECLEVEL=1')
        # 初始化連線池管理器，並指定使用自定義的 SSL 上下文
        self.poolmanager = PoolManager(
            num_pools=connections, maxsize=maxsize, block=block, ssl_context=ctx
        )

def saveself(driver_path=None):
    base_url = 'https://www.savesafe.com.tw/'
    titlelist = []
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    driver_service = Service(driver_path) if driver_path else Service()
    driver = webdriver.Chrome(service=driver_service, options=options)
    
    session = requests.Session()
    session.mount('https://', SSLAdapter())

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/133.0.0.0 Safari/537.36"
    }

    try:
        driver.get(base_url)
        time.sleep(3)
        titles = driver.find_elements(By.CSS_SELECTOR, 'ul.ThirdNavItemList li a')
        for title in titles:
            href = title.get_attribute('href')
            if href:
                titlelist.append(href)
    finally:
        driver.quit()

    all_products = []
    for nav_url in titlelist:
        print(f"開始抓取分類頁面：{nav_url}")
        url = nav_url
        while url:
            try:
                response = session.get(url, headers=headers, timeout=10)  # 增加 timeout 避免卡住
                response.raise_for_status()
                soup = BeautifulSoup(response.text, "html.parser")

                breadcrumb_links = soup.select('li.breadcrumb-item a')
                category = breadcrumb_links[-1].get_text(strip=True) if breadcrumb_links else '未知分類'

                product_cards = soup.select('div.NewActivityItem')
                for card in product_cards:
                    link_tag = card.select_one('a.text-center')
                    if link_tag:
                        product_url = link_tag.get('href')
                        img_tag = link_tag.find('img', class_='card-img-top')
                        image_url = img_tag['src'] if img_tag and img_tag.has_attr('src') else ''
                    else:
                        product_url = ''
                        image_url = ''

                    name_tag = card.select_one('p.ObjectName')
                    name = name_tag.get_text(strip=True) if name_tag else ''

                    price_tag = card.select_one('span.Price')
                    price = price_tag.get_text(strip=True) if price_tag else ''

                    all_products.append({
                        'name': name,
                        'price': price,
                        'img_url': image_url,
                        'product_url': product_url if product_url else '',
                        'category': category,
                        'store': 'savesafe'
                    })

                    if len(all_products) % 10 == 0:
                        print(f"已抓取 {len(all_products)} 筆資料")

                next_page_tag = soup.select_one('a.page-link[aria-label="Next"]')
                if next_page_tag and 'href' in next_page_tag.attrs:
                    url = base_url + next_page_tag['href']
                else:
                    break

            except requests.exceptions.RequestException as e:
                print(f"請求錯誤（{url}）：{e}")
                break

    return all_products



# 只需直接呼叫 saveself() 即可運行
saveself()  # 不需要再指定變數來儲存返回值
