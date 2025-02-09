# 比價王
1. 使用者註冊功能
2. mail驗證
3. 非使用者有瀏覽功能及<-session
4. 要有下單時才跳出註冊通知
5. 基本的session+cookies
6. Mariadb+非使用者使用sessionID+使用者使用註冊表
7. 查詢暫存列表...cookie
8. (額外)推薦熱門商品
9. (額外)已GOOGLE FB MAC登入
10. (額外)default推薦關注列表


# 首頁
* 熱門商品
* 查詢列表
* 右上角有 登入 註冊 關注頁面

# 下單
* redierct到目標網址

## 分頁
* 主頁 index.html
* 註冊頁 register.html
* 登入頁面 login.html
* 商品頁面 product.html
* 分類頁面 cat.html /hot /elec /food
* 關注頁面 care.html

## 爬蟲
* 家樂福
* 大買家
* costco
* 寶雅

## 資料庫分頁
|Table Name|columns|
|-|-|
|user_table| ID 名稱 密碼 EMAIL 年齡 性別 關注列表 關注類別
|care_table| 關注類別 產品列表
|cat_table| cat_id name 
|product_table| product_id product_shop
|shop_table|shop_id product link logo



# AI回覆
```
這是一個很完整的設計需求，針對您所提出的功能與架構，我會進一步給出專案設計的建議與檔案結構，並指出可能需要進一步考慮的功能。

### 功能設計及建議

1. **使用者註冊功能**：
   - 實現 Django 的內建用戶模型（`django.contrib.auth.models.User`），也可以根據需要擴展用戶模型來儲存額外的用戶資訊（如地址、訂單歷史等）。
   - 使用郵件驗證（透過 `django-allauth` 或自定義驗證邏輯），在用戶註冊後發送驗證郵件。
   - 使用者註冊後會自動登入。

2. **非使用者有瀏覽功能及 session**：
   - 非註冊用戶會使用 `Session` 儲存他們的訪問記錄，並可查看商品，不能進行結帳。
   - 使用 Django 的 `Session` 框架來記錄非註冊用戶的臨時資料，例如查看過的商品。

3. **下單時才跳出註冊通知**：
   - 使用 Session 檢查是否為登錄狀態，如果未登入，用戶在下單時會跳出註冊提示。
   - 可以在結帳過程中引導用戶完成註冊。

4. **基本的 session + cookies**：
   - 使用 Django 內建的 `Session` 與 `Cookie` 管理，將一些簡單資料儲存於 cookie 例如查看的商品或當前分類等。

5. **MariaDB + 非使用者使用 sessionID + 使用者使用註冊表**：
   - 使用 Django ORM 管理 MariaDB 資料庫，對於未註冊用戶，使用 `SessionID` 儲存會話資料；對於已註冊用戶，透過其用戶模型進行操作。

6. **查詢暫存列表（cookie）**：
   - 使用 cookie 儲存非註冊用戶查看過的商品清單，這樣即便關閉瀏覽器也能保持他們的查詢歷史。

7. **推薦熱門商品**：
   - 可以基於用戶的瀏覽記錄、點擊量等資料進行推薦（可以使用基於內容或協同過濾的算法來實現）。

8. **已 Google, FB, Apple 登入**：
   - 使用 `django-allauth` 來實現 Google、Facebook 和 Apple 登入，提供第三方認證支持。

9. **郵件驗證**：
   - 利用 `django.core.mail` 發送註冊時的驗證郵件，並在用戶點擊驗證鏈接後激活帳戶。

### 預期功能的檔案結構與專案架構

以下是一個簡單的 Django 專案檔案結構建議：


比價王/
├──比價王/
│   ├── settings.py        # 設定檔案，包含資料庫設置、第三方服務配置
│   ├── urls.py            # 主要 URL 路由
│   ├── wsgi.py            # WSGI 設定
│   ├── asgi.py            # ASGI 設定（如果需要異步處理）
├──app/
│   ├── migrations/        # 資料庫遷移檔案
│   ├── models.py          # 用戶、商品、訂單等資料模型
│   ├── views.py           # 控制邏輯
│   ├── urls.py            # 應用內部的路由設定
│   ├── forms.py           # 註冊、登入等表單處理
│   ├── templates/
│   │   ├── index.html     # 主頁
│   │   ├── register.html  # 註冊頁
│   │   ├── login.html     # 登入頁
│   │   ├── product.html   # 商品頁
│   │   ├── cat.html       # 分類頁
│   │   ├── care.html      # 關注頁面
│   ├── static/
│   │   ├── css/
│   │   ├── js/
│   │   ├── images/
│   ├── views/
│   │   ├── homepage_views.py # 主頁邏輯
│   │   ├── auth_views.py    # 註冊、登入等認證邏輯
│   │   ├── product_views.py # 商品頁邏輯
│   │   ├── order_views.py   # 訂單邏輯
│   ├── tests.py           # 測試
├──crawler/                # 爬蟲
│   ├── carrefour.py        # 家樂福爬蟲
│   ├── costco.py           # Costco 爬蟲
│   ├── hypermarket.py      # 大買家爬蟲
│   ├── poya.py             # 寶雅爬蟲
│   ├── utils.py            # 爬蟲工具函數
├──manage.py               # Django 執行管理命令
└──requirements.txt        # 需要的外部庫（`django`, `requests`, `django-allauth`, `pandas`, `mysqlclient`, `beautifulsoup4`等）
```

### 更進一步的建議功能

1. **資料庫優化**：
   - 根據業務邏輯，考慮對查詢頻繁的資料建立索引，如商品名稱、分類等。
   - 考慮為熱門商品推薦系統建立額外的資料表來儲存商品的評分、點擊次數等。

2. **訂單管理**：
   - 建立訂單模型，包含商品、數量、總價、狀態等，並且與使用者進行關聯。

3. **商品分類和篩選功能**：
   - 提供多種篩選商品的方式，根據價格、品牌、評分等篩選商品，並提供多層級的商品分類（如電子、食品、家居等）。

4. **支付整合**：
   - 如果需要，可以進一步整合支付接口（例如：Stripe、PayPal）來完成在線支付功能。

5. **網站性能與安全**：
   - 設置對網站的性能優化（如靜態檔案、圖片壓縮）以及安全措施（如防範跨站請求偽造（CSRF）、跨站腳本攻擊（XSS）等）。

6. **管理後台**：
   - 使用 Django 自帶的管理界面來管理商品、訂單、用戶等。

### 爬蟲部分

爬蟲部分可以使用 `requests`、`BeautifulSoup` 和 `Selenium` 來進行數據抓取。根據網站的反爬蟲機制，可能需要加入代理或使用 headless 瀏覽器。

這樣設計應該能夠滿足您的基本需求，並且具有良好的擴展性。您可以根據具體情況進一步優化。
```
###DeBug_mode
1. admin page 預設帳號密碼administrator:administrator 歡迎大家新增自己的使用者
2. Login預設帳密 111:111
3. 使用先到127.0.0.1:8000/ 會自動跳轉到登入畫面
