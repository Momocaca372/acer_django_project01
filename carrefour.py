import requests
from bs4 import BeautifulSoup
my_headers = {"user-agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36"}
session = requests.Session()

def Carrefour(n):
    url = "https://online.carrefour.com.tw/zh/search/?q="+n
    while True:
        r = session.get(url,headers = my_headers)
        if r.status_code == 200:
            soup = BeautifulSoup(r.text,'html.parser')
            titles = soup.select('div.desc-operation-wrapper a')
            links = soup.select('div.commodity-desc a')
            imgs = soup.select('div.box-img a img')
            nexturl = soup.select('div.pagenation a')[-2].get('onclick').split("'")[1]
            url = nexturl
            for title,link,img in zip(titles,links,imgs):
                # print(title.text)
                # print("https://online.carrefour.com.tw/"+link.get('href'))
                print("圖片連結: "+img.get('src'))
                print("-----------分隔線-----------")
                url2 = "https://online.carrefour.com.tw/"+link.get('href')
                r2 = session.get(url2,headers = my_headers)
                try:
                    if r2.status_code == 200:
                        soup2 = BeautifulSoup(r2.text,'html.parser')
                        titles2 = soup2.find_all('h1')
                        brands = soup2.select('div.hot a')
                        moneys = soup2.find_all('span',class_='current-money')
                        for title2,brand,money in zip(titles2,brands,moneys):
                            print(title2.text)
                            print(brand.text)
                            print("價格:"+money.text[2:])
                except:
                    break
                
n = input("查詢:") 
Carrefour(n)
