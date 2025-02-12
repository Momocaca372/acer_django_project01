from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import re
# 設置 Chrome 驅動器
savesafe = webdriver.Chrome()

# 儲存所有鏈接
linklist = []

# 訪問網站
savesafe.get("https://www.savesafe.com.tw/")

# 增加等待時間並正確的 CSS 選擇器
WebDriverWait(savesafe, 40).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'ul.ThirdNavItemList.d-flex')))

# 查找所有的鏈接元素，這裏假設你希望提取的是菜單中的鏈接
links = savesafe.find_elements(By.CSS_SELECTOR, 'ul.ThirdNavItemList.d-flex li a')  # li > a
# 從每個鏈接元素中提取 href 屬性
for link in links:
    href1 = link.get_attribute('href')
    if href1:  # 確保 href 屬性不為 None
        linklist.append(href1)

# 關閉瀏覽器
savesafe.quit()

for a in linklist:
    savesafe = webdriver.Chrome()
    savesafe.get(a)
    while True:
        titles = savesafe.find_elements(By.CSS_SELECTOR, 'div.card-body p.ObjectName')
        page_info = savesafe.find_element(By.CSS_SELECTOR, 'div.PaginationNumber p')
        page_text = page_info.text
        match = re.search(r'(\d+)\s*/\s*(\d+)', page_text)
        if match:
            current_page = int(match.group(1))  # 當前頁
            total_pages = int(match.group(2))
        for title in titles:
            print(title.text)
        if current_page < total_pages:
            # 找到 "下一頁" 的 <a> 標籤
            nextlinks = savesafe.find_elements(By.CSS_SELECTOR, 'div.PaginationNumber a[href*="Pg="]')
            nextlink = nextlinks[-1]  # 取最後一個翻頁按鈕
            print(f"Next page URL: {nextlink.get_attribute('href')}")
            nextlink.click()  # 點擊 "下一頁"
            time.sleep(5)  # 等待5秒鐘讓頁面加載
        else:
            print("已經是最後一頁，停止翻頁。")
            break
    savesafe.quit()