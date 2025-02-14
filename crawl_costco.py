from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
costoc=webdriver.Chrome()
linklist = []
costoc.get("https://www.costco.com.tw/")
WebDriverWait(costoc, 20).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'a.show-sub-menu')))
links=costoc.find_elements(By.CSS_SELECTOR, 'a.show-sub-menu.hidden-xs.hidden-sm.ng-star-inserted')
for link in links:
    href1 = link.get_attribute('href')
    linklist.append(href1)
costoc.quit()
linklist2 = []
n = 0
for a in linklist:
    costoc1=webdriver.Chrome()
    costoc1.get(a)
    links2=costoc1.find_elements(By.CSS_SELECTOR, 'a.thumb')
    nextlinks = costoc1.find_elements(By.CSS_SELECTOR, 'a.page-link-next')
    for link2,b in zip(links2,nextlinks):
        href2 = link2.get_attribute('href')
        nexthref = b.get_attribute('href')
        costoc2=webdriver.Chrome()
        costoc2.get(nexthref)
        linklist2.append(href2)
        costoc2.quit()
    costoc1.quit()
    