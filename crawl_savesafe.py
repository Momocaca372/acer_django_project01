from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import re
from concurrent.futures import ThreadPoolExecutor

# 訪問每個鏈接的函數
def visit_link(url):
    driver = webdriver.Chrome()
    driver.get(url)
    
    # 等待菜單加載
    WebDriverWait(driver, 40).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'ul.ThirdNavItemList.d-flex')))
    
    # 提取鏈接
    linklist = list(filter(None, map(lambda link: link.get_attribute('href'), driver.find_elements(By.CSS_SELECTOR, 'ul.ThirdNavItemList.d-flex li a'))))
    print(f"Link list found on {url}: {len(linklist)}")

    # 訪問鏈接並處理每個頁面
    for a in linklist:
        driver.get(a)
        while True:
            WebDriverWait(driver, 40).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div.PaginationNumber p')))
            titles = driver.find_elements(By.CSS_SELECTOR, 'div.card-body p.ObjectName')
            page_info = driver.find_element(By.CSS_SELECTOR, 'div.PaginationNumber p')
            page_text = page_info.text
            match = re.search(r'(\d+)\s*/\s*(\d+)', page_text)
            if match:
                current_page = int(match.group(1))  # 當前頁
                total_pages = int(match.group(2))
            for title in titles:
                print(title.text)
            if current_page < total_pages:
                # 找到 "下一頁" 的 <a> 標籤
                WebDriverWait(driver, 40).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div.PaginationNumber a[href*="Pg="]')))
                nextlinks = driver.find_elements(By.CSS_SELECTOR, 'div.PaginationNumber a[href*="Pg="]')
                nextlink = nextlinks[-1]  # 取最後一個翻頁按鈕
                print(f"Next page URL: {nextlink.get_attribute('href')}")
                nextlink.click()  # 點擊 "下一頁"
                time.sleep(2)  # 等待頁面加載
            else:
                print("已經是最後一頁，停止翻頁。")
                break
    driver.quit()

# 主邏輯：獲取首頁鏈接並啟動多工
def main():
    # 設置 Chrome 驅動器
    driver = webdriver.Chrome()

    # 訪問網站
    driver.get("https://www.savesafe.com.tw/")

    # 增加等待時間並正確的 CSS 選擇器
    WebDriverWait(driver, 40).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'ul.ThirdNavItemList.d-flex')))

    # 查找所有的鏈接元素
    linklist = list(filter(None, map(lambda link: link.get_attribute('href'), driver.find_elements(By.CSS_SELECTOR, 'ul.ThirdNavItemList.d-flex li a'))))
    print("Link list found on the main page:", len(linklist))

    # 關閉瀏覽器
    driver.quit()

    # 使用 ThreadPoolExecutor 來並行處理每個鏈接
    with ThreadPoolExecutor(max_workers=15) as executor:
        executor.map(visit_link, linklist)

if __name__ == "__main__":
    main()
