import pyrebase
import crawl_controler

"""爬取的商品資料，存成[{}]的格式，可以直接寫入Firebase"""

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

def fetch_existing_data(db):
    """預先讀取 Firebase 內的所有 store、category 和 product，減少 API 請求次數"""
    existing_data = {"store": {}, "category": {}, "product": {}}

    # 讀取店家資料
    store_data = db.child("store").get().val() or {}
    if isinstance(store_data, list):
        store_data = {str(i): v for i, v in enumerate(store_data) if v}
    existing_data["store"] = {v["name"]: k for k, v in store_data.items()}

    # 讀取分類資料
    category_data = db.child("category").get().val() or {}
    if isinstance(category_data, list):
        category_data = {str(i): v for i, v in enumerate(category_data) if v}
    existing_data["category"] = {v['name']: k for k, v in category_data.items()}

    # 讀取商品資料
    product_data = db.child("product_detail").get().val() or {}
    if isinstance(product_data, list):
        product_data = {str(i): v for i, v in enumerate(product_data) if v}
    existing_data["product"] = {v["product_url"]: k for k, v in product_data.items()}

    return existing_data

def save_to_firebase(products):
    """在本機比對是否有重複，再寫入Firebase"""
    db = get_firebase_connection()
    existing_data = fetch_existing_data(db)  # 預先讀取 Firebase 數據
    store_map = existing_data["store"]
    category_map = existing_data["category"]
    product_map = existing_data["product"]

    new_stores = {}
    new_categories = {}
    new_products = {}
    new_product_details = {}

    for product in products:
        store_name = product['store']
        category_name = product['category']
        product_name = product['name']
        price = product['price']
        img_url = product['img_url']
        product_url = product['product_url']

        # === 儲存店家資訊 ===
        store_id = store_map.get(store_name)
        if store_id is None:
            store_id = str(len(store_map) + 1)
            store_map[store_name] = store_id
            new_stores[store_id] = {"name": store_name}

        # === 儲存分類資訊 ===
        category_id = category_map.get(category_name)
        if category_id is None:
            category_id = str(len(category_map) + 1)
            category_map[category_name] = category_id
            new_categories[category_id] = {"name": category_name, "store_id": store_id}

        # === 儲存商品資訊 ===
        if product_url in product_map:
            continue  # 商品已存在，跳過

        product_id = str(len(product_map) + 1)
        product_map[product_url] = product_id
        new_products[product_id] = {"store_id": store_id, "category_id": category_id}
        new_product_details[product_id] = {
            "name": product_name,
            "price": price,
            "img_url": img_url,
            "product_url": product_url,
            "product_id": product_id,
        }

    # === 寫入 Firebase ===
    if new_stores:
        db.child("store").update(new_stores)
    if new_categories:
        db.child("category").update(new_categories)
    if new_products:
        db.child("product").update(new_products)
    if new_product_details:
        db.child("product_detail").update(new_product_details)

    print(f"新增 {len(new_stores)} 個店家, {len(new_categories)} 個分類, {len(new_products)} 個商品.")
    

if __name__ == '__main__':
    all_products = crawl_controler.Crawl.carrefour() + crawl_controler.Crawl.costco()
    save_to_firebase(all_products)