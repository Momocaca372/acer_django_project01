import requests
from bs4 import BeautifulSoup
import csv

# 設置 headers，這裡用來模擬瀏覽器行為，防止請求被拒絕
my_headers = {"user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36"}
session = requests.Session()

# 設定 URL
url = 'https://online.carrefour.com.tw/zh/homepage/'
def crawl():
    # 發送 GET 請求來抓取首頁
    r = requests.get(url, headers=my_headers)
    
    # 如果請求成功（狀態碼 200），開始解析資料
    if r.status_code == 200:
        soup = BeautifulSoup(r.text, 'html.parser')
    
        # 找到所有分類的鏈接，這些鏈接指向不同的商品分類頁
        titles = soup.find_all('a', attrs={'class': 'category-panel-item'})
    
        # 打開 CSV 文件來存儲抓取的數據
        with open('carrefour.csv', 'w', encoding='utf-8', newline='') as file:
            # 設定 CSV 文件的欄位名稱
            fieldnames = ['name', 'money', 'img', 'link']
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            
            # 寫入 CSV 的表頭
            writer.writeheader()
    
            # 遍歷每一個分類的鏈接
            for title in titles:
                # 生成每個分類的具體頁面 URL
                url2 = 'https://online.carrefour.com.tw/' + title.get('href')
    
                # 開始抓取分類頁的商品
                while True:
                    r2 = requests.get(url2, headers=my_headers)
                    
                    # 如果請求成功，解析該頁面的內容
                    if r2.status_code == 200:
                        soup2 = BeautifulSoup(r2.text, 'html.parser')
                        
                        # 找到商品圖片所在的鏈接
                        links = soup2.select('div.box-img a')
    
                        # 獲取下一頁的 URL，便於分頁抓取
                        nexturl = soup2.select('div.pagenation a')[-2].get('onclick').split("'")[1]
                        url2 = nexturl  # 更新為下一頁的 URL
    
                        # 遍歷每一個商品鏈接
                        for link in links:
                            # 生成商品頁面的 URL
                            item_url = 'https://online.carrefour.com.tw/' + link.get('href')
                            r3 = requests.get(item_url, headers=my_headers)
    
                            # 如果請求成功，抓取該商品頁面
                            if r3.status_code == 200:
                                soup3 = BeautifulSoup(r3.text, 'html.parser')
                                
                                # 找到商品名稱
                                titles2 = soup3.select('div.title h1')
                                
                                # 找到商品價格
                                moneys = soup3.find_all('span', class_='money')
                                
                                # 找到商品圖片的網址
                                imgs = soup3.select('div.preview-wrapper img')
    
                                # 逐一抓取商品的名稱、價格、圖片鏈接和商品頁面的鏈接，並寫入 CSV
                                for title2, money, img in zip(titles2, moneys, imgs):
                                    # 清理抓取到的文字資料，去除多餘空白
                                    title_text = title2.text.strip()
                                    money_text = money.text.strip()
                                    
                                    # 處理圖片鏈接和商品頁面鏈接
                                    img_url = 'https://online.carrefour.com.tw' + img.get('src')
                                    link_url = 'https://online.carrefour.com.tw' + link.get('href')
    
                                    # 寫入抓取的資料到 CSV 文件
                                    writer.writerow({'name': title_text, 'money': money_text, 'img': img_url, 'link': link_url})
    
                                    # 打印結果方便檢查
                                    print(title_text)
                                    print("價格: " + money_text)
                                    print(img_url)
                                    print(link_url)
                                    print("---------------分隔-----------------")
