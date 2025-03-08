#!/usr/bin/env python
# -*- coding: utf-8 -*-

import ssl
import time
import requests
from urllib.parse import urlparse, parse_qs, urlencode, urljoin
from requests.adapters import HTTPAdapter
from urllib3.poolmanager import PoolManager
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By


class SSLAdapter(HTTPAdapter):
    """自訂 SSL 適配器，允許較舊的加密方式。"""
    def init_poolmanager(self, connections, maxsize, block=False):
        ctx = ssl.create_default_context()
        ctx.set_ciphers('DEFAULT:@SECLEVEL=1')
        self.poolmanager = PoolManager(num_pools=connections, maxsize=maxsize, block=block, ssl_context=ctx)


def savesafe(driver_path=None):
    url = 'https://www.savesafe.com.tw/'

    # 取得分類頁面 URL
    def get_urls(drv, url):
        drv.get(url)
        time.sleep(3)
        lst = []
        for a in drv.find_elements(By.CSS_SELECTOR, 'ul.ThirdNavItemList li a'):
            href = a.get_attribute('href')
            if href:
                lst.append(href)
        for a in drv.find_elements(By.CSS_SELECTOR, 'a.pl-3'):
            href = a.get_attribute('href')
            if href and 'ProductList?t_s_id=' in href:
                lst.append(urljoin(url, href))
        return list(set(lst))  # 去除重複

    # 修改 URL 加上分頁參數
    def add_page(u, p):
        parts = urlparse(u)
        qs = parse_qs(parts.query)
        qs["s"] = ["6"]
        qs["Pg"] = [str(p)]
        return f"{parts.scheme}://{parts.netloc}{parts.path}?{urlencode(qs, doseq=True)}"

    # 解析頁面資訊：取得目前頁碼與總頁數
    def get_page_info(soup):
        sp = soup.select_one('span.m-0.text-black-50')
        if not sp:
            return None, None
        try:
            tot = int(sp.get_text(strip=True).replace('/', '').strip())
        except ValueError:
            return None, None
        par = sp.find_parent('p')
        for item in par.contents:
            if isinstance(item, str) and item.strip().isdigit():
                return int(item.strip()), tot
        return None, None

    # 從商品卡片中提取資料，直接加入 items 列表
    def add_items(soup, url, cat):
        nonlocal items
        for card in soup.select('div.NewActivityItem'):
            a_tag = card.select_one('a.text-center')
            p_url = urljoin(url, a_tag.get('href')) if a_tag else ''
            img_tag = a_tag.find('img', class_='card-img-top') if a_tag else None
            img = urljoin(url, img_tag['src']) if img_tag and img_tag.get('src') else ''
            title = card.select_one('p.ObjectName').get_text(strip=True) if card.select_one('p.ObjectName') else ''
            price = card.select_one('span.Price').get_text(strip=True) if card.select_one('span.Price') else ''
            items.append({
                'name': title,
                'price': price,
                'img_url': img,
                'product_url': p_url,
                'category': cat,
                'store': 'savesafe'
            })

    opts = webdriver.ChromeOptions()
    opts.add_argument('--headless')
    serv = Service(driver_path) if driver_path else Service()
    drv = webdriver.Chrome(service=serv, options=opts)

    try:
        url_list = get_urls(drv, url)
    finally:
        drv.quit()

    print(f"共收集 {len(url_list)} 個分類頁面")

    session = requests.Session()
    session.mount('https://', SSLAdapter())
    headers = {
        "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                       "AppleWebKit/537.36 (KHTML, like Gecko) "
                       "Chrome/133.0.0.0 Safari/537.36")
    }
    items = []

    for u in url_list:
        print(f"開始抓取分類頁面：{u}")
        p = 1
        cat = '未知分類'
        while True:
            pu = add_page(u, p)
            print(f"抓取頁面：{pu}")
            try:
                r = session.get(pu, headers=headers, timeout=10)
                r.raise_for_status()
                soup = BeautifulSoup(r.text, "html.parser")
            except requests.RequestException as e:
                print(f"請求錯誤：{e}")
                break

            cur, tot = get_page_info(soup)
            if cur is None or tot is None:
                print("無法解析分頁資訊，停止翻頁")
                break
            print(f"分頁資訊：目前 {cur} / 總 {tot}")

            add_items(soup, url, cat)
            print(f"累計抓取 {len(items)} 筆資料")

            if cur >= tot:
                print(f"已到最後一頁（{cur}/{tot}）")
                break
            p += 1

    return items


# 直接呼叫 saveself()，即可使用
savesafe()
