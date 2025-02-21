import requests
from bs4 import BeautifulSoup
import concurrent.futures
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from concurrent.futures import ThreadPoolExecutor
from selenium.webdriver.common.keys import Keys

from time import sleep
from tqdm import tqdm

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


def carrefour():
    # 設定家樂福線上商城的首頁 URL
    url = 'https://online.carrefour.com.tw/zh/homepage/'
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
                category = soup.select('div.crumbs a')[3].text.split('/')[1].strip()
            except (IndexError, AttributeError):
                category = "未知分類"

            print(f'商品: {title}, 價格: {price}, 分類: {category}')
            product_dict={'name': title,
                          'price': price,
                          'img_url': img_url,
                          'product_url': product_url,
                          'classification': category,
                          'store':'carrefour',
                          }            
            return product_dict
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

    category_links = get_category_links()[1:2]

    if category_links:
        all_products = []
        for category_url in category_links:
            print(f"正在爬取分類頁面: {category_url}")
            products = scrape_category_page(category_url)
            all_products.extend(products)
                
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
            link_list = [ a.get('href') for a in soup.select('ul#theMenu a.ng-star-inserted')]
            link_list = list(filter(lambda x: x != 'javascript:void(0)', link_list))
            return link_list
        return []  # 修正：避免返回 None
    def scrape_product_page(product_url):
        """爬取單個商品頁面的詳細資訊"""
        soup = get_soup(product_url)
        if not soup:
            return None

        try:
            title = soup.find('h1').text.strip()
            price = soup.find('span', class_='notranslate ng-star-inserted').text.strip()[1:]
            img_url = 'https://www.costco.com.tw' + soup.select_one('div.thumb img').get('src')

            # 抓取分類，如果找不到，則設定為 "未知分類"
            try:
                category = soup.select('div.breadcrumb-section a')[3].text.strip()
            except (IndexError, AttributeError):
                category = "未知分類"

            print(f'商品: {title}, 價格: {price}, 分類: {category}')
            product_dict={'name': title,
                          'price': price,
                          'img_url': img_url,
                          'product_url': product_url,
                          'classification': category,
                          'store':'costco',
                          }
            return product_dict
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
            product_links = set(a.get('href') for a in soup.select('div.product-name-container a'))
            print(f"發現 {len(product_links)} 件商品")

            # 使用多執行緒爬取所有商品詳情
            with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
                results = executor.map(scrape_product_page, product_links)

            # 收集有效的商品數據
            product_data.extend(filter(None, results))

            # 找下一頁的 URL
            try:
                next_page = soup.select('li.page-item a')[-1].get('href')
                category_url = next_page if next_page else None
            except (IndexError, AttributeError):
                category_url = None  # 沒有下一頁則停止

        return product_data

    def costco_all_product():
        category_links = get_category_links()[1:2]

        if category_links:
            all_products = []
            for category_url in category_links:
                print(f"正在爬取分類頁面: {category_url}")
                products = scrape_category_page(category_url)
                all_products.extend(products)
                
def savesafe():
    

    # === 爬取商品詳細資訊 ===
    def get_product_details(driver, product_url):
        """
        從指定的商品頁面抓取商品詳細資訊，包括標題、價格、圖片及分類，
        然後將這些資訊存入資料庫。

        :param driver: Selenium 的 WebDriver 物件，用來操作瀏覽器
        :param url: 商品的詳細頁面網址
        """
        driver.get(product_url)
        try:
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'h4.h2-responsive.product-name')))

            # ✅ 抓取標題
            try:
                title_element = driver.find_element(By.CSS_SELECTOR, 'h4.h2-responsive.product-name')
                title = title_element.text.strip()
                title = re.sub(r'\s*<span>.*?</span>\s*', '', title)  # 移除 <span> 內的內容
            except:
                title = None

            # ✅ 抓取價格
            try:
                price_element = driver.find_element(By.CSS_SELECTOR, 'span.SalePrice.text-danger')
                price = re.sub(r"[^\d.]", "", price_element.text.strip())  # 移除非數字字元
            except:
                price = None

            # ✅ 抓取主圖片
            try:
                main_img = driver.find_element(By.CSS_SELECTOR, 'div.clearfix a#cgo img#mainImg')
                img_url = main_img.get_attribute("src")
            except:
                img_url = None

            # ✅ 抓取分類 (麵包屑)
            try:
                breadcrumb = driver.find_element(By.CSS_SELECTOR, 'li.breadcrumb-item.active')
                category = breadcrumb.text.strip()
            except:
                category = "未分類"



            product_dict={'name': title,
                          'price': price,
                          'img_url': img_url,
                          'product_url': product_url,
                          'classification': category,
                          'store':'SaveSafe',
                          }         
        except Exception as e:
            print(f" 獲取 {product_url} 詳情時發生錯誤: {e}")
        return product_dict
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
    def savesafe_all_product():
        """
        主函數，設置資料庫並啟動爬蟲，抓取分類頁面的產品鏈接，
        並使用多線程並行處理每個分類頁面。
        """
        product_data = []
        

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
             results = executor.map(visit_link, linklist)
             
             # 收集有效的商品數據
             product_data.extend(filter(None, results))
             
        return product_data

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

carrefour()