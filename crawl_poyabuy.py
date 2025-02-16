from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
poyabuy=webdriver.Chrome()
poyabuy.get("https://www.poyabuy.com.tw/v2/official/SalePageCategory/0?sortMode=Newest")
WebDriverWait(poyabuy, 20).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div.sc-bxgxFH')))
poyabuy.execute_script("window.scrollTo(0, document.body.scrollHeight);")
titles = poyabuy.find_elements(By.CSS_SELECTOR, 'div.sc-bxgxFH')
for title in titles:
    print(title.text)
poyabuy.quit()
    