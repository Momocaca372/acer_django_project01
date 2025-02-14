from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# 啟動 Chrome 瀏覽器
costoc = webdriver.Chrome()

# 初始化一個空的列表來儲存抓取到的鏈接
linklist = []

# 進入成本網站的首頁
costoc.get("https://www.costco.com.tw/")

# 等待頁面中的特定元素出現，最多等 20 秒
WebDriverWait(costoc, 20).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'a.show-sub-menu')))

# 提取頁面中所有符合條件的鏈接
links = costoc.find_elements(By.CSS_SELECTOR, 'a.show-sub-menu.hidden-xs.hidden-sm.ng-star-inserted')

# 迭代每個鏈接並提取其 href 屬性
for link in links:
    href1 = link.get_attribute('href')
    linklist.append(href1)

# 關閉瀏覽器
costoc.quit()

# 初始化第二個空的列表來儲存進一步抓取的鏈接
linklist2 = []

# 迭代每個從首頁抓取到的鏈接
n = 0
for a in linklist:
    # 啟動一個新的 Chrome 瀏覽器進入每個鏈接
    costoc1 = webdriver.Chrome()
    costoc1.get(a)

    # 提取該頁面中的所有圖片鏈接
    links2 = costoc1.find_elements(By.CSS_SELECTOR, 'a.thumb')

    # 提取該頁面的“下一頁”鏈接
    nextlinks = costoc1.find_elements(By.CSS_SELECTOR, 'a.page-link-next')

    # 迭代圖片鏈接和下一頁鏈接的組合
    for link2, b in zip(links2, nextlinks):
        # 提取圖片鏈接的 href 屬性
        href2 = link2.get_attribute('href')

        # 提取下一頁鏈接的 href 屬性
        nexthref = b.get_attribute('href')

        # 啟動一個新的瀏覽器，進入下一頁鏈接
        costoc2 = webdriver.Chrome()
        costoc2.get(nexthref)

        # 儲存圖片鏈接到 linklist2 中
        linklist2.append(href2)

        # 關閉瀏覽器
        costoc2.quit()

    # 關閉 costoc1 瀏覽器
    costoc1.quit()

# 程式執行結束後，linklist2 會包含抓取到的所有圖片鏈接
