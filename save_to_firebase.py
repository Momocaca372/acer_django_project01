import pyrebase  # 用於連接 Firebase
import crawl_carrefour  # Carrefour 爬蟲模組
import crawl_costco  # Costco 爬蟲模組

def get_firebase_connection():
    """建立與 Firebase 的連線"""
    config = {
        "apiKey": "AIzaSyAb1S6EP5v3np68_R6JQc6JPrlx6UHuEuE",
        "authDomain": "djangofirebase-949f7.firebaseapp.com",
        "databaseURL": "https://djangofirebase-949f7-default-rtdb.firebaseio.com",
        "projectId": "djangofirebase-949f7",
        "storageBucket": "djangofirebase-949f7.firebasestorage.app",
        "messagingSenderId": "925644337298",
        "appId": "1:925644337298:web:e2769661ba39282dbe364b",
    }
    firebase = pyrebase.initialize_app(config)  # 初始化 Firebase
    return firebase.database()  # 回傳資料庫物件

def save_to_firebase(products):
    """將爬取到的商品資訊存入 Firebase 資料庫"""
    db = get_firebase_connection()  # 取得 Firebase 連線

    for product in products:
        store_name = product['store']  # 店家名稱
        category_name = product['category']  # 商品分類
        product_name = product['name']  # 商品名稱
        price = product['price']  # 商品價格
        img_url = product['img_url']  # 商品圖片連結
        product_url = product['product_url']  # 商品頁面連結

        # === 儲存店家資訊 ===
        store_data = db.child("store").get()
        existing_stores = store_data.val() or {}  # 取得現有店家資料

        if isinstance(existing_stores, list):
            existing_stores = {str(i): v for i, v in enumerate(existing_stores) if v}

        # 查找店家是否已存在
        existing_store_id = next((sid for sid, store in existing_stores.items() if store.get("name") == store_name), None)

        if existing_store_id is None:
            store_id = str(max(map(int, existing_stores.keys()), default=0) + 1)
            db.child("store").child(store_id).set({"name": store_name})  # 新增店家
            print(f"新增店家: {store_name} (ID: {store_id})")
        else:
            store_id = existing_store_id  # 店家已存在，使用現有 ID

        # === 儲存商品類別 ===
        category_data = db.child("category").get()
        existing_categories = category_data.val() or {}

        if isinstance(existing_categories, list):
            existing_categories = {str(i): v for i, v in enumerate(existing_categories) if v}

        # 查找分類是否已存在
        existing_category_id = next((cid for cid, category in existing_categories.items() if category.get("name") == category_name), None)

        if existing_category_id is None:
            category_id = str(max(map(int, existing_categories.keys()), default=0) + 1)
            db.child("category").child(category_id).set({"name": category_name, "store_id": store_id})  # 新增分類
        else:
            category_id = existing_category_id  # 分類已存在，使用現有 ID

        # === 儲存商品資訊 ===
        product_data = db.child("product").get()
        existing_products = product_data.val() or {}

        if isinstance(existing_products, list):
            existing_products = {str(i): v for i, v in enumerate(existing_products) if v}

        # 檢查商品是否已存在
        existing_product_id = next((pid for pid, prod in existing_products.items() if prod.get("name") == product_name), None)

        if existing_product_id is None:
            product_id = str(max(map(int, existing_products.keys()), default=0) + 1)
            db.child("product").child(product_id).set({"store_id": store_id, "category_id": category_id})  # 儲存基本資訊
            db.child("product_detail").child(product_id).set({  # 儲存詳細資訊
                "name": product_name,
                "price": price,
                "img_url": img_url,
                "product_url": product_url,
                "product_id": product_id,
            })
            print(f"新增商品: {product_name} (ID: {product_id})")
        else:
            print(f"商品 {product_name} 已存在，跳過新增！")

if __name__ == '__main__':
    # Carrefour & Costco 類別頁面爬取範圍
    carrefour_category_links = crawl_carrefour.get_category_links()[6:7]
    costco_category_links = crawl_costco.get_category_links()[1:2]
    all_products = []  # 儲存所有爬取的商品
    
    # 爬取 Carrefour 資料
    if carrefour_category_links:
        for category_url in carrefour_category_links:
            print(f"正在爬取分類頁面: {category_url}")
            products = crawl_carrefour.scrape_category_page(category_url)  # 爬取該分類頁面
            all_products.extend(products)
    
    # 爬取 Costco 資料
    if costco_category_links:
        for category_url in costco_category_links:
            print(f"正在爬取分類頁面: {category_url}")
            products = crawl_costco.scrape_category_page(category_url)  # 爬取該分類頁面
            all_products.extend(products)
    
    # 儲存爬取的商品資訊到 Firebase
    if all_products:
        save_to_firebase(all_products)
