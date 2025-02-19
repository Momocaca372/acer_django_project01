import pyrebase
import crawl_carrefour

def get_firebase_connection():
    config = {
        "apiKey": "AIzaSyAb1S6EP5v3np68_R6jQc6JPrlx6UHuEuE",
        "authDomain": "djangofirebase-949f7.firebaseapp.com",
        "databaseURL": "https://djangofirebase-949f7-default-rtdb.firebaseio.com",
        "projectId": "djangofirebase-949f7",
        "storageBucket": "djangofirebase-949f7.firebasestorage.app",
        "messagingSenderId": "925644337298",
        "appId": "1:925644337298:web:e2769661ba39282dbe364b",
    }
    firebase = pyrebase.initialize_app(config)
    return firebase.database()


def save_to_firebase(products):
    """將爬取到的商品資訊存入 Firebase 資料庫"""
    db = get_firebase_connection()

    for product in products:
        store_name = product['store']
        category_name = product['category']
        product_name = product['name']
        price = product['price']
        img_url = product['img_url']
        product_url = product['product_url']

        # === 儲存店家資訊 ===
        store_data = db.child("store").get()
        existing_stores = store_data.val() or {}

        # 確保 existing_stores 是字典格式
        if isinstance(existing_stores, list):
            existing_stores = {str(i): v for i, v in enumerate(existing_stores) if v}

        # 查找店家 ID
        existing_store_id = next((sid for sid, store in existing_stores.items() if store.get("name") == store_name), None)

        if existing_store_id is None:
            # 新增店家
            store_id = str(max(map(int, existing_stores.keys()), default=0) + 1)
            db.child("store").child(store_id).set({"name": store_name})
            print(f"新增店家: {store_name} (ID: {store_id})")
        else:
            store_id = existing_store_id
            print(f"店家 {store_name} 已存在，ID: {store_id}")

        # === 儲存商品類別 ===
        category_data = db.child("category").get()
        existing_categories = category_data.val() or {}

        # 確保 existing_categories 是字典格式
        if isinstance(existing_categories, list):
            existing_categories = {str(i): v for i, v in enumerate(existing_categories) if v}

        # 查找分類 ID
        existing_category_id = next((cid for cid, category in existing_categories.items() if category.get("name") == category_name), None)

        if existing_category_id is None:
            # 新增分類
            category_id = str(max(map(int, existing_categories.keys()), default=0) + 1)
            db.child("category").child(category_id).set({"name": category_name, "store_id": store_id})
            print(f"新增分類: {category_name} (ID: {category_id})")
        else:
            category_id = existing_category_id
            print(f"分類 {category_name} 已存在，ID: {category_id}")

        # === 儲存商品 ===
        product_data = db.child("product").get()
        existing_products = product_data.val() or {}

        # 確保 existing_products 是字典格式
        if isinstance(existing_products, list):
            existing_products = {str(i): v for i, v in enumerate(existing_products) if v}

        # 檢查商品是否已存在
        existing_product_id = next((pid for pid, prod in existing_products.items() if prod.get("name") == product_name), None)

        if existing_product_id is None:
            # 新增商品
            product_id = str(max(map(int, existing_products.keys()), default=0) + 1)
            db.child("product").child(product_id).set({
                "name": product_name,
                "price": price,
                "img_url": img_url,
                "product_url": product_url,
                "store_id": store_id,
                "category_id": category_id,
            })
            print(f"新增商品: {product_name} (ID: {product_id})")
        else:
            print(f"商品 {product_name} 已存在，跳過新增！")
            
if __name__ == '__main__':
    category_links = carrefour.get_category_links()[6:7]

    if category_links:
        all_products = []
        for category_url in category_links:
            print(f"正在爬取分類頁面: {category_url}")
            products = carrefour.scrape_category_page(category_url)
            all_products.extend(products)
            
        if all_products :
            save_to_firebase(all_products)    