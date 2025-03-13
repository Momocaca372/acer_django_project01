import ssl
import requests
from requests.adapters import HTTPAdapter
from urllib3.poolmanager import PoolManager
from bs4 import BeautifulSoup
from selenium import webdriver
from tqdm import tqdm
import time 
import json

# 自定義的 SSL Adapter，降低安全等級以允許較小的 DH 金鑰
class SSLAdapter(HTTPAdapter):
    def init_poolmanager(self, connections, maxsize, block=False):
        # 創建一個默認的 SSL 上下文
        ctx = ssl.create_default_context()
        # 設置加密套件的安全等級為 1，允許較小的 DH 金鑰
        ctx.set_ciphers('DEFAULT:@SECLEVEL=0')
        # 初始化連線池管理器，並指定使用自定義的 SSL 上下文
        self.poolmanager = PoolManager(
            num_pools=connections, maxsize=maxsize, block=block, ssl_context=ctx
        )


#def saveself(driver_path=None):
base_url = 'https://www.savesafe.com.tw/'
headers = {
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36"
}

chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument('--headless')
chrome_options.add_argument("--headless")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--enable-unsafe-swiftshader")   




def get_titlelist(base_url=base_url):
    titlelist=[]
    driver = webdriver.Chrome(options=chrome_options)
    driver.get(base_url)
    driver.implicitly_wait(10)
    soup =BeautifulSoup(driver.page_source,"html.parser")
    driver.quit()
    titles = soup.select('ul.ThirdNavItemList>li>a')
    for title in titles:
        href = title.get('href')
        if href:
            titlelist.append(href)
    return titlelist

def get_category_items(nav_url):
    web_page = 1 
    product_list = []
    category=""
    try:
        while True:
            session = requests.Session()
            session.mount('https://', SSLAdapter())
            response = session.get(f"{base_url:s}{nav_url:s}&Pg={web_page:d}", headers=headers, timeout=10)  # 增加 timeout 避免卡住
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")
            breadcrumb_links = soup.select('li.breadcrumb-item a')
            if not breadcrumb_links:
                break
            category = breadcrumb_links[-1].get_text(strip=True)
    
            product_cards = soup.select('div.NewActivityItem')
            for card in product_cards:
                link_tag = card.select_one('a.text-center')
                product_url = link_tag.get('href')
                img_tag = link_tag.find('img', class_='card-img-top')
                image_url = img_tag['src']
    
                name_tag = card.select_one('p.ObjectName')
                name = name_tag.get_text(strip=True)
    
                price_tag = card.select_one('span.Price')
                price = price_tag.get_text(strip=True)
    
                product_list.append({
                    'name': name,
                    'price': price,
                    'img_url': image_url,
                    'product_url': product_url,
                    'category': category,
                    'store': 'savesafe'
                })
                web_page+=1
        session.close()
    except:
        print("伺服器守備")
        time.sleep(3)
        get_category_items(nav_url)
    #else:
        #category_n = category if category else nav_url
        #print(f"{category_n} :已抓取 {len(product_list)} 筆資料")
    return product_list

titlelist = get_titlelist()
seen = set()
product_list=[]  
for title in tqdm(titlelist):
    for item in get_category_items(title):
        if item["name"] not in seen:  # 檢查是否已存在
            seen.add(item["name"])  # 加入已見集合
            product_list.append(item)  # 加入結果列表
with open("product_save.json", "w", encoding="utf-8") as f:
    json.dump(product_list, f, indent=4, ensure_ascii=False)    

