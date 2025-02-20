# 比價王

# 計畫
1. 爬蟲------
2. 確認SQL結構---
3. 首頁+網頁框架 
4. 改fire-base +Booststrap
5. 依照使用者推薦列表 ML
6. **AI 客服** 取代人工客服，能節省人工成本 可以快速回覆使用者需求 以及提供親切的問候!  
7.  人工客服(email收發)

1.爬蟲整合入SQL結構 4個檔案
Poyabuy - momo方
增加Firebase_form modle - momo方2/20
caffur - aaa吳 
costco - aaa吳 
修改為Firebase.py - aaa吳 2/18
savesave - GGP
2.網頁架構
3. 思考AI融入我們的專題--Jie
4. 前端網頁設計--Jie 2/18


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

### **優化後的設計**
#### **1. `store`（店家表）**
| 欄位名稱 | 資料型別  | 說明 |
|---------|--------|----|
| `id` (PK) | `SERIAL` | 店家 ID |
| `name` | `VARCHAR` | 店家名稱 |


---

#### **2. `category`（商品類別表）**
| 欄位名稱 | 資料型別 | 說明 |
|---------|------|----|
| `id` (PK) | `SERIAL` | 商品類別 ID |
| `store_id` (FK) | `INT` | 關聯店家（`store.id`） |
| `name` | `VARCHAR` | 商品類別名稱 |

---

#### **3. `product`（商品表）**
| 欄位名稱 | 資料型別 | 說明 |
|---------|------|----|
| `id` (PK) | `SERIAL` | 商品 ID |
| `store_id` (FK) | `INT` | 關聯店家（`store.id`） |
| `category_id` (FK) | `INT` | 關聯商品類別（`category.id`） |


---

#### **4. `product_detail`（商品詳細資訊表）**
| 欄位名稱 | 資料型別 | 說明 |
|---------|------|----|
| `id` (PK) | `SERIAL` | 詳細資訊 ID |
| `product_id` (FK) | `INT` | 關聯商品（`product.id`） |
| `name` | `VARCHAR` | 商品名稱 |
| `image_url` | `TEXT` | 商品圖檔url |
| `product_url` | `TEXT` | 下單url |
| `price` | `DECIMAL(10,2)` | 商品價格 |



