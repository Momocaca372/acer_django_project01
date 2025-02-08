import requests  # 匯入 requests 庫來處理 HTTP 請求
from bs4 import BeautifulSoup  # 匯入 BeautifulSoup 來解析 HTML 內容

# 定義自訂的 headers，模擬瀏覽器請求
my_headers = {"user-agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36"}

# 建立一個會話，保持在多次請求之間的狀態
session = requests.Session()

def Carrefour(n):
    """
    這個函數用來搜尋並抓取 Carrefour 網站上的商品資訊，包括商品名稱、品牌、價格和圖片。

    參數:
    n (str): 用戶輸入的查詢關鍵字，例如商品名稱，這會用來在 Carrefour 網站上進行搜尋。

    過程:
    1. 發送 HTTP 請求到 Carrefour 搜尋頁面，取得商品資料。
    2. 解析網頁內容，提取商品標題、品牌、價格和圖片等資訊。
    3. 支援分頁，持續抓取下一頁的商品資訊。
    """
    
    # 設定 Carrefour 搜尋頁面的基本 URL，並加上查詢字串
    url = "https://online.carrefour.com.tw/zh/search/?q="+n
    
    # 無窮迴圈來翻頁獲取更多的結果
    while True:
        # 發送 HTTP GET 請求到該 URL
        r = session.get(url, headers=my_headers)
        
        # 如果請求成功 (HTTP 狀態碼 200)
        if r.status_code == 200:
            # 使用 BeautifulSoup 解析頁面的 HTML 內容
            soup = BeautifulSoup(r.text, 'html.parser')
            
            # 使用 CSS 選擇器查找所有商品的標題
            titles = soup.select('div.desc-operation-wrapper a')
            
            # 使用 CSS 選擇器查找所有商品的連結
            links = soup.select('div.commodity-desc a')
            
            # 使用 CSS 選擇器查找所有商品的圖片
            imgs = soup.select('div.box-img a img')
            
            # 透過選擇分頁中的倒數第二個「下一頁」按鈕，獲得下一頁的 URL
            nexturl = soup.select('div.pagenation a')[-2].get('onclick').split("'")[1]
            
            # 更新 URL 為下一頁的 URL，繼續進行下一輪循環
            url = nexturl
            
            # 透過 zip() 將標題、連結、圖片集合在一起，同時遍歷
            for title, link, img in zip(titles, links, imgs):
                # 輸出商品的圖片連結
                print("圖片連結: "+img.get('src'))
                print("-----------分隔線-----------")
                
                # 構建商品詳細頁的 URL
                url2 = "https://online.carrefour.com.tw/" + link.get('href')
                
                # 發送 GET 請求到商品詳細頁
                r2 = session.get(url2, headers=my_headers)
                
                try:
                    # 如果商品詳細頁加載成功 (狀態碼 200)
                    if r2.status_code == 200:
                        # 解析商品詳細頁
                        soup2 = BeautifulSoup(r2.text, 'html.parser')
                        
                        # 提取商品的標題
                        titles2 = soup2.find_all('h1')
                        
                        # 提取商品的品牌名稱
                        brands = soup2.select('div.hot a')
                        
                        # 提取商品的價格
                        moneys = soup2.find_all('span', class_='current-money')
                        
                        # 同時遍歷商品標題、品牌和價格
                        for title2, brand, money in zip(titles2, brands, moneys):
                            # 輸出商品的標題、品牌和價格
                            print(title2.text)
                            print(brand.text)
                            print("價格:" + money.text[2:])
                except:
                    # 如果發生錯誤（例如找不到商品詳情頁），則跳出迴圈
                    break

# 提示用戶輸入查詢的商品名稱
n = input("查詢:") 

# 呼叫 Carrefour 函式並傳入用戶的查詢名稱
Carrefour(n)
