import pyrebase
import crawl_controler
import concurrent.futures

def get_firebase_connection():
    """建立與 Firebase 的連線"""
    config = {
        "apiKey": "<your-api-key>",
        "authDomain": "<your-auth-domain>",
        "databaseURL": "<your-database-url>",
        "projectId": "<your-project-id>",
        "storageBucket": "<your-storage-bucket>",
        "messagingSenderId": "<your-messaging-sender-id>",
        "appId": "<your-app-id>",
    }
    firebase = pyrebase.initialize_app(config)  # 初始化 Firebase
    return firebase.database()  # 回傳資料庫物件

def fetch_existing_data(db):
    """預先讀取 Firebase 內的 store、category 和 product，減少 API 請求次數"""
    existing_data = {"store": {}, "category": {}, "product": {}}

    # 讀取店家資料，建立字典 {店家名稱: 店家ID}
    store_data = db.child("store").get().val() or {}
    if isinstance(store_data, list):
        store_data = {str(i): v for i, v in enumerate(store_data) if v}
    existing_data["store"] = {v["name"]: k for k, v in store_data.items()}

    # 讀取分類資料，建立字典 {分類名稱: 分類ID}
    category_data = db.child("category").get().val() or {}
    if isinstance(category_data, list):
        category_data = {str(i): v for i, v in enumerate(category_data) if v}
    existing_data["category"] = {v['name']: k for k, v in category_data.items()}

    # 讀取商品資料，建立字典 {商品 URL: 商品ID}，避免重複新增
    product_data = db.child("product_detail").get().val() or {}
    if isinstance(product_data, list):
        product_data = {str(i): v for i, v in enumerate(product_data) if v}
    existing_data["product"] = {v["product_url"]: k for k, v in product_data.items()}

    return existing_data

def batch_save(db, products):
    """批量寫入 Firebase，減少 API 請求次數"""
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

    # === 批量寫入 Firebase ===
    if new_stores:
        db.child("store").update(new_stores)
    if new_categories:
        db.child("category").update(new_categories)
    if new_products:
        db.child("product").update(new_products)
    if new_product_details:
        db.child("product_detail").update(new_product_details)

    print(f"批量新增 {len(new_stores)} 個店家, {len(new_categories)} 個分類, {len(new_products)} 個商品.")

def save_to_firebase(products):
    """使用多執行緒加速寫入 Firebase"""
    db = get_firebase_connection()

    # 分批處理，每批 5000 筆，避免 API 請求過大
    batch_size = 5000
    product_batches = [products[i:i + batch_size] for i in range(0, len(products), batch_size)]

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        executor.map(lambda batch: batch_save(db, batch), product_batches)

if __name__ == '__main__':
    all_products = crawl_controler.carrefour()  # 爬取 Carrefour 產品資料
    save_to_firebase(all_products)