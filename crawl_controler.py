import requests
from bs4 import BeautifulSoup
import concurrent.futures
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from concurrent.futures import ThreadPoolExecutor
from selenium.webdriver.common.keys import Keys
import ssl
from urllib3.poolmanager import PoolManager
from requests.adapters import HTTPAdapter
from time import sleep
import time
from tqdm import tqdm
from selenium.webdriver.chrome.service import Service
import re
# 設置 headers，模擬瀏覽器行為，防止請求被拒絕
my_headers = {
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36"
}
chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--enable-unsafe-swiftshader")
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

def carrefour():
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
            category_links = ['https://online.carrefour.com.tw' + a.get('href') for a in soup.find_all('a', class_='category-panel-label')][9:]
            return category_links
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
    
    """抓取所有分類的商品，使用併發來加速"""
    category_urls = get_category_links()
    all_products = []

    # 使用 ThreadPoolExecutor 來並行抓取各個分類頁面
    with concurrent.futures.ThreadPoolExecutor() as executor:
        results = executor.map(scrape_category_page, category_urls)
        for result in results:
            all_products.extend(result)

    return all_products

def costco():  
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
            link_list = [a.get('href') for a in soup.select('ul#theMenu a.ng-star-inserted')]
            link_list = list(filter(lambda x: x != 'javascript:void(0)', link_list))  # 過濾掉無效鏈接
            return link_list[25:-55]
        return []  # 若請求失敗或無分類則返回空列表

    def scrape_category_page(category_url):
        """抓取某一分類頁面的所有商品"""
        all_products = []
        page = 0
        while True:
            paginated_url = category_url if page == 0 else f"{category_url}?page={page}"
            print(paginated_url)
            soup = get_soup(paginated_url)
            if not soup:
                break
            
            # 提取分類名稱
            try:
                category = soup.find('h1',class_='category-title').text.strip()
            except (IndexError, AttributeError):
                category = "未知分類"    
            
            # 提取商品信息
            products = soup.find_all('a',class_='lister-name js-lister-name')
            prices = soup.select('div.product-price span.notranslate')
            img_urls = soup.select('div.product-image img')
            
            for product, price, img_url in zip(products, prices, img_urls):
                title = product.text
                product_url = product.get('href').replace('https://www.costco.com.tw', '')
                # try:
                price = price.text.split('$')[1].strip()
                # except IndexError:
                #     price = "未知價格"
                img_url = img_url.get('src').replace('https://www.costco.com.tw', '')
            
                all_products.append({
                    'name': title,
                    'price': price,
                    'img_url': img_url,
                    'product_url': product_url,
                    'category': category,
                    'store': 'costco'
                })
            
                print(title, product_url, price, category)
                
                # 如果該頁面沒有更多商品則停止
            if len(products) < 48:
                break
            
            page += 1
        return all_products


    """抓取所有分類的商品，使用併發來加速"""
    category_urls = get_category_links()
    all_products = []

    # 使用 ThreadPoolExecutor 來並行抓取各個分類頁面
    with concurrent.futures.ThreadPoolExecutor() as executor:
        results = executor.map(scrape_category_page, category_urls)
        for result in results:
            all_products.extend(result)

    return all_products

def saveself(driver_path=None):
    """
    使用 Selenium 獲取導航列中的所有鏈接並抓取商品資料
    :param driver_path: 若需要指定 ChromeDriver 路徑，則提供此參數，預設為 None，會自動尋找
    :return: 返回抓取到的所有商品資料列表，包含商品名稱、價格、圖片和商品連結等資訊
    """
    base_url = 'https://www.savesafe.com.tw/'  # 設定默認網站的 URL
    titlelist = []  # 用於存儲從導航列中抓取的所有分類頁面鏈接
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')  # 無頭模式，避免彈出瀏覽器視窗，適合於自動化抓取
    driver_service = Service(driver_path) if driver_path else Service()  # 判斷是否有傳入 driver 路徑
    driver = webdriver.Chrome(service=driver_service, options=options)  # 使用 WebDriver 打開瀏覽器

    # 使用自定義 SSLAdapter 的 requests Session
    session = requests.Session()  # 創建一個新的 session 用於發送 HTTP 請求
    session.mount('https://', SSLAdapter())  # 設置自定義的 SSLAdapter 來處理 HTTPS 請求
    
    # 定義 headers 來模擬瀏覽器行為，防止被網站識別為機器人
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/133.0.0.0 Safari/537.36"
    }

    try:
        # 使用 Selenium 獲取網站首頁並抓取導航列中的所有鏈接
        driver.get(base_url)
        time.sleep(3)  # 等待頁面完全加載，確保導航列的鏈接已經渲染完成
        titles = driver.find_elements(By.CSS_SELECTOR, 'ul.ThirdNavItemList li a')  # 找到導航列中的所有鏈接
        for title in titles:
            href = title.get_attribute('href')  # 獲取每個鏈接的 href 屬性
            if href:
                titlelist.append(href)  # 如果 href 存在，將其加入 titlelist
    finally:
        driver.quit()  # 無論成功與否，結束後關閉 WebDriver，釋放資源

    # 遍歷所有導航頁面鏈接，抓取每個分類頁中的商品資料
    all_products = []  # 用於存儲所有商品資料的列表
    for nav_url in titlelist:
        print(f"開始抓取分類頁面：{nav_url}")  # 輸出目前正在抓取的分類頁面 URL
        url = nav_url
        while url:
            try:
                # 發送 GET 請求來抓取頁面的內容，並設置 headers 來模擬真實瀏覽器行為
                response = session.get(url, headers=headers)
                response.raise_for_status()  # 如果狀態碼不是 200，則引發異常
                soup = BeautifulSoup(response.text, "html.parser")  # 用 BeautifulSoup 解析 HTML 內容
                
                # 從麵包屑導航中獲取分類名稱
                breadcrumb_links = soup.select('li.breadcrumb-item a')  # 解析麵包屑導航中的所有分類
                category = breadcrumb_links[-1].get_text(strip=True) if breadcrumb_links else '未知分類'  # 取得最後一個分類作為當前頁面的分類名稱
                
                # 找到所有商品區塊
                product_cards = soup.select('div.NewActivityItem')
                for card in product_cards:
                    # 取得商品的連結與圖片連結
                    link_tag = card.select_one('a.text-center')  # 找到每個商品的連結
                    if link_tag:
                        product_url = link_tag.get('href')  # 獲取商品的詳細頁面 URL
                        
                        # 確保圖片連結存在並獲取圖片 URL
                        img_tag = link_tag.find('img', class_='card-img-top')  # 尋找商品圖片
                        image_url = img_tag['src'] if img_tag and img_tag.has_attr('src') else ''  # 如果有圖片，則取其 src 屬性
                    else:
                        product_url = ''
                        image_url = ''
                    
                    # 取得商品名稱
                    name_tag = card.select_one('p.ObjectName')  # 找到商品名稱的標籤
                    name = name_tag.get_text(strip=True) if name_tag else ''  # 提取商品名稱文本
                    
                    # 取得商品價格
                    price_tag = card.select_one('span.Price')  # 找到商品價格的標籤
                    price = price_tag.get_text(strip=True) if price_tag else ''  # 提取商品價格文本
                    
                    # 將抓取的商品資訊添加到 all_products 列表中
                    all_products.append({
                        'name': name,  # 商品名稱
                        'price': price,  # 商品價格
                        'img_url': image_url,  # 商品圖片的 URL
                        'product_url': product_url if product_url else '',  # 商品詳細頁面的 URL
                        'category': category,  # 商品所屬分類
                        'store': 'savesafe'  # 店鋪名稱（固定為 'savesafe'）
                    })
                    print(name, product_url, price, category, image_url)  # 輸出商品的基本資訊
                
                # 檢查是否有下一頁的連結
                next_page_tag = soup.select_one('a.page-link[aria-label="Next"]')  # 查找 "下一頁" 按鈕
                if next_page_tag and 'href' in next_page_tag.attrs:  # 如果下一頁按鈕存在，則獲取下一頁的鏈接
                    url = base_url + next_page_tag['href']  # 組合出完整的 URL
                else:
                    break  # 如果沒有下一頁，則跳出循環，停止抓取

            except requests.exceptions.RequestException as e:  # 捕捉任何 HTTP 請求錯誤
                print(f"請求錯誤（{url}）：{e}")  # 輸出錯誤訊息
                break  # 出現錯誤後跳出循環
    
    return all_products  # 返回所有抓取的商品資料，形式為列表字典


def poyabuy():
    # 宣告參數
    url = "https://www.poyabuy.com.tw/v2/official/SalePageCategory/0?sortMode=Newest"
    poya_base_url = 'https://www.poyabuy.com.tw'

    def get_category_index():
        """爬取類別列表，並存入 `category` 資料表（如果分類不存在則新增）"""
        
        driver = webdriver.Chrome(options=chrome_options)
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

        category_names_map = {}  # 用來存分類名稱對應的 ID
        for index,item in enumerate(category_names):
            category_names_map[index] = item
        
        return category_names_map  # 回傳分類索引與 ID 對應表

    def fetch_category_url(index,category):
        
        """滾動到底部，爬取商品資訊，並存入 `product_detail` 和 `productl`"""
        
        driver = webdriver.Chrome(options=chrome_options)
        wait = WebDriverWait(driver, 10, poll_frequency=0.5)
        driver.get(url)
        driver.implicitly_wait(10)
        sleep(3)
        # 點擊分類按鈕
        for _ in range(50):
            try:
                category_buttons = driver.find_elements(By.CLASS_NAME, "sc-kZCGdI.jmFZfR")

                category_buttons[index+9].click()
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
        soup = BeautifulSoup(driver.page_source, "html.parser")

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
                product_dict={'name': product_name,
                          'price': product_price,
                          'img_url': product_image_url,
                          'product_url': product_url,
                          'classification': category,
                          'store':'carrefour',
                          }      
            except Exception as e:
                print(f"爬取商品時發生錯誤: {e}")
                print( product_name, product_price, product_image_url, product_url)   
        driver.quit()
        return product_dict


    # 取得所有分類，存入 category 表，並獲取分類 ID 對應表
    categorys = get_category_index()
    
    product_data=[]
    
 # ✅ 多線程處理分類頁面
    with ThreadPoolExecutor(max_workers=5) as executor:

            results = executor.map(fetch_category_url, categorys.keys(), categorys.values())   
            product_data.extend(filter(None, results))
             
    return product_data
