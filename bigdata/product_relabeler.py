import pandas as pd
import joblib
import re
import jieba
import nltk
from scipy.stats import mode  # 用於計算眾數
import pyrebase

def split_and_upload_data(db, data):
    max_chunk_size = 100000  # 根據需要調整大小，假設每次寫入最大 100,000 字元
    chunk = {}

    for key, value in data.items():
        chunk[key] = value
        if len(str(chunk)) >= max_chunk_size:
            # 上傳一部分資料
            ref = db.child("/")  # 更新你希望的路徑
            ref.update(chunk)
            print(f"資料塊已上傳：{len(str(chunk))}")
            chunk = {}  # 重置 chunk 變數，開始下一批

    # 確保最後一個小塊也能寫入
    if chunk:
        ref = db.child("/")  # 更新你希望的路徑
        ref.update(chunk)
        print(f"最後的資料塊已上傳：{len(str(chunk))}")

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

def download_data_from_firebase():
    """下載資料並轉換為 DataFrame"""
    db = get_firebase_connection()
    ref = db.child("/product_detail")  # 假設資料儲存在 /product_detail 路徑下
    data = ref.get()  # 取得資料

    if data.val():  # 確認資料存在
        rows = data.val()
        # 轉換為 DataFrame
        df = pd.json_normalize(rows)
        return df
    else:
        print("資料不存在")
        return None
    
# **資料清理函數**
def clean_product_name(text):
    units = ["g", "kg", "克拉", "毫升", "K", "尺", "呎", "組", "公升", "入", "包入", "公分", "斤", "公斤", "公克", "ml", "L", "盒", "包", "瓶", "顆", "件"]
    units_pattern = r"\b\d+\s*(" + "|".join(units) + r")\b"
    text = text.lower()
    text = re.sub(units_pattern, "", text)
    text = re.sub(r"[^a-zA-Z0-9\u4e00-\u9fff\s]", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text

def tokenize(text):
    if any('\u4e00' <= char <= '\u9fff' for char in text):
        return " ".join(jieba.lcut(text))
    else:
        return " ".join(nltk.word_tokenize(text))

def product_relabeler(df):
    df.dropna(inplace=True)
    df = df[["product_id", "name"]]
    
    # 讀取模型 & 向量器
    model = joblib.load("RFC_model.pkl")
    vectorizer = joblib.load("tfidf_vectorizer.pkl")
    
    
    
    # **用 apply 加速資料清理**
    df["cleaned_name"] = df["name"].apply(clean_product_name)
    df["tokenized_name"] = df["cleaned_name"].apply(tokenize)
    
    # **批量轉換成向量**
    X = vectorizer.transform(df["tokenized_name"])  
    
    # **批量預測**
    df["predicted_category"] = model.predict(X)
    
    # **計算連續 10 筆的眾數**
    window_size = 10  # 取最近10筆資料
    df["smoothed_category"] = (
        df["predicted_category"]
        .rolling(window=window_size, min_periods=1)
        .apply(lambda x: mode(x)[0], raw=True)
        .fillna(1)
    )
    
    # **轉成 JSON 格式**
    result_dict = {"product_relabel": dict(zip(df["product_id"], df["smoothed_category"].astype(int)))}
    return result_dict
    
    
def save_to_firebase(result_dict):

    # 取得 Firebase 連線
    db = get_firebase_connection()
    ref = db.child("/") 
    # 取得目前資料庫中的內容
    data = ref.get()

    if data.val() and 'product_relabel' in data.val():
        # 移除 'product_relabel' 欄位
        updated_data = data.val()
        del updated_data['product_relabel']

        # 更新資料
        updated_data.update(result_dict)

        # 將資料上傳到 Firebase
        split_and_upload_data(db, updated_data)
        print("資料已成功更新")
    else:
        split_and_upload_data(db, result_dict)
        print("資料已成功新增")
if __name__=="__main__":
    df = download_data_from_firebase()
    result_dict = product_relabeler(df)
    save_to_firebase(result_dict)
    