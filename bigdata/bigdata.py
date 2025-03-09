import math
import pathlib
import pandas as pd
import jieba
import re
import itertools
import nltk
import joblib
import sqlite3 as sql

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier
from scipy.stats import mode
#from sklearn.metrics.pairwise import cosine_similarity


"""
用於創建模型的類別

train_model: 訓練模型
predict: 預測

內部說明:
    get_category_tokens: 取得分類的 tokens
    extract_features: 提取特徵
    load_data: 讀取資料
    clean_product_name: 清理商品名稱
    tokenize: 分詞
    calculate_entropy: 計算熵
    calculate_token_entropy: 計算 token 熵
    create_stop_words: 創建 stop words
    filter_stop_words: 過濾 stop words

"""
#Firebase 設定值
SQL_path = "BIBIGOproject/db.sqlite3"  
config = {
"apiKey": "AIzaSyAb1S6EP5v3np68_R6JQc6JPrlx6UHuEuE",
"authDomain": "djangofirebase-949f7.firebaseapp.com",
"databaseURL": "https://djangofirebase-949f7-default-rtdb.firebaseio.com",
"projectId": "djangofirebase-949f7",
"storageBucket": "djangofirebase-949f7.firebasestorage.app",
"messagingSenderId": "925644337298",
"appId": "1:925644337298:web:e2769661ba39282dbe364b",
}
path = pathlib.Path(__file__).parent.parent

pattern =re.compile(r"^(?:\d+|\W+|\d+[a-zA-Z]+|\d+\W*\d*[a-zA-Z]*)$")# 定義正則表達式(12, @2,60ml,50mlx6)


# 計算熵的函數
def calculate_entropy(token, category_tokens):
    # 計算 token 在每個 category 中出現的頻率
    category_counts = {cat: 0 for cat in category_tokens}
    
    for cat, tokens in category_tokens.items():
        category_counts[cat] = tokens.count(token)
    
        # 計算 token 在各類別中出現的概率
    total_count = sum(category_counts.values())
    
    # 確保總和大於 0，否則設為 0
    if total_count > 0:
        probabilities = [count / total_count for count in category_counts.values()]
    else:
        probabilities = [0 for _ in category_counts.values()]
    # 計算熵
    entropy = -sum(p * math.log2(p) for p in probabilities if p > 0)
    return entropy

# 計算每個 token 的熵
def calculate_token_entropy(category_tokens):
    token_entropy = {}
    all_tokens = set(itertools.chain.from_iterable(itertools.chain.from_iterable(category_tokens.values())))
    
    for token in all_tokens:
       token_entropy[token] =  calculate_entropy(token, category_tokens)
    
    return token_entropy

# 設置熵的閾值來識別 stop words
def create_stop_words(token_entropy, threshold=1.0):
    return {token for token, entropy in token_entropy.items() if entropy > threshold}

# 去除 stop words
def filter_stop_words(category_tokens, stop_words):
    filtered_category_tokens = {
        cat: [token for token in tokens if token not in stop_words]
        for cat, tokens in category_tokens.items()
    }
    return filtered_category_tokens

def clean_product_name(text):
    # 定義需要刪除的單位
    units = ["g","kg", "克拉","毫升", "K", "尺", "呎","組","公升", "入","包入","入組","公分","袋入"
             "斤","公斤", "公克", "g", "ml", "L", "盒", "包", "瓶", "顆", "件"]
    units_pattern = r"\b\d+\s*(" + "|".join(units) + r")\b"  # 建立正則表達式
    text = text.lower()  # 轉小寫
    text = re.sub(units_pattern, "", text)  # 刪除開頭數字+單位
    text = re.sub(r"[^a-zA-Z0-9\u4e00-\u9fff\s]", "", text)  # 移除所有特殊符號
    text = re.sub(r"\s+", " ", text).strip()  # 移除多餘空格
    return text

# 中文分詞（使用 jieba），英文分詞（使用 nltk）
def tokenize(text):
    if any('\u4e00' <= char <= '\u9fff' for char in text):  # 檢查是否有中文
        return jieba.lcut(text)  # 中文用 jieba
    else:
        return nltk.word_tokenize(text)  # 英文用 nltk 

def get_category_tokens(df):
    return {
        cat: [
            token for token in itertools.chain.from_iterable(token_lists) 
            if not pattern.match(token)
        ]
        for cat, token_lists in df.groupby("category_id")["tokens"]
    }
    

def extract_features(category_tokens):
    # 計算每個 token 的熵
    token_entropy = calculate_token_entropy(category_tokens)
    
    # 設置熵閾值並創建 stop words 集合
    stop_words = create_stop_words(token_entropy, threshold=0.5)
    
    # 過濾掉 stop words
    filtered_category_tokens = filter_stop_words(category_tokens, stop_words)
    include_words = ["貓", "狗", "犬", "糧","寵物","喵","汪","毛小孩"]
    baby_index = str(min(map(int, filtered_category_tokens.keys()))+5)
    # 針對 [250:576] 範圍內的數據進行篩選，其他部分保持不變
    filtered_category_tokens[baby_index] = filtered_category_tokens[baby_index][:780]
    # 只對 [250:576] 區間進行篩選
    filtered_category_tokens[baby_index][250:576] = list(map(
        lambda x: x if any(word in x for word in include_words) else None,
        filtered_category_tokens[baby_index][250:576]
    ))
    
    # 移除 None
    filtered_category_tokens[baby_index] = list(filter(None, filtered_category_tokens[baby_index]))
    print("filtered_category_tokens Done")
    # 轉換每個分類的 token 為單一字符串（文本），這樣可以用於詞頻向量化
    return {
        cat: ' '.join(token for token in tokens)  # 將每個類別的 token 轉換為單一的字符串
        for cat, tokens in category_tokens.items()
    }

def model_create():
    conn = sql.connect(path / SQL_path)
    query = """
    SELECT p.id, p.name, p.category_id
    FROM myapp_product AS p
    JOIN myapp_category AS c ON p.category_id = c.id
    JOIN myapp_store AS s ON c.store_id = s.id
    WHERE s.name = 'costco';
    """
    
    df_product = pd.read_sql_query(query, conn)
    conn.close()
    df_product.name = df_product.name.apply(lambda x:clean_product_name(x)) 
    df_product['tokens'] = df_product['name'].apply(tokenize)
    category_tokens = get_category_tokens(df_product)        # 依 category_id 分組，並將 tokens 展平成一維陣列
    documents = extract_features(category_tokens)
    
        
    
    
    # 取得每個文檔的標籤，即每個文檔所屬的分類
    labels = list(documents.keys())  # 類別名稱作為標籤
    print(labels)
    texts = list(documents.values())  # 每個類別的 token 作為文本
    print("vectorizer Done")
    # 讓 Vectorizer 按照商品名稱（單獨處理每篇文章）
    vectorizer = TfidfVectorizer(
        stop_words=['a', 'an', 'the', 'of', 'on', '的', '是', '了', '和', '入','kirkland'],
        ngram_range=(1, 2)  # 同時學習單字和詞組，提高泛化能力
    )
    X = vectorizer.fit_transform(texts)
    
    X = df_product['tokens'].apply(lambda x: ' '.join(x))
    X = vectorizer.transform(X)
    y = df_product['category_id']
    
    model = RandomForestClassifier(n_estimators=200)
    print("model build Done")
    
    
    # 訓練模型
    model.fit(X, y)
    print(model.score(X, y)) #印出解釋力
    joblib.dump(model, path / "bigdata/RFC_model.pkl")  # 儲存為 pkl 檔案
    joblib.dump(vectorizer, path / "bigdata/tfidf_vectorizer.pkl") # 儲存為 pkl 檔案
    print("模組及向量表已暫存")
    return model,vectorizer

if input("是否要使用舊數據? y/n").upper() =="Y":
    model = joblib.load(path /"bigdata/RFC_model.pkl") #讀取模型
    vectorizer = joblib.load(path /"bigdata/tfidf_vectorizer.pkl") #讀取向量器
else:
    model,vectorizer = model_create()

conn = sql.connect(path / SQL_path)
query = """
SELECT id, name, category_id
FROM myapp_product """

df_product = pd.read_sql_query(query, conn)
conn.close()

# **預處理商品名稱**
df_product["cleaned_name"] = df_product["name"].apply(clean_product_name)
df_product["tokenized_name"] = df_product["cleaned_name"].apply(tokenize)
X = vectorizer.transform(df_product["tokenized_name"].apply(lambda x: " ".join(x)))  
print("資料向量化完成 預測模型中")
# **批量預測**
df_product["predicted_category"] = model.predict(X)

df_product["category_id"] = df_product["category_id"].astype(int)
df_product["predicted_category"] = df_product["predicted_category"].astype(int)
# 按 category_id 分組，對每組內的 predicted_category 計算眾數
df_product["predicted_category"] = (
    df_product.groupby("category_id")["predicted_category"]
    .transform(lambda x: mode(x)[0] if len(x) > 0 else 85)  # 取眾數
)



conn = sql.connect(path / SQL_path)
cursor = conn.cursor()
# SQL UPDATE 語法
query = """
UPDATE myapp_product 
SET value = ? 
WHERE id = ?
"""

# 將 DataFrame 轉換為列表
data = list(zip(df_product["predicted_category"], df_product["id"]))

# 批量更新資料（避免 for 迴圈）
cursor.executemany(query, data)

# 提交變更 & 關閉
conn.commit()
conn.close()



    

    
# =============================================================================
# def recommand_list_genetor(user_input,user_id):
#     try:
#         vectorizer = vectorizer
#         ref = db.child("/care/"+user_id) 
#         data = ref.get()  # 取得資料
#         df_product = pd.json_normalize(data.val())
#     except:
#         print("找不到資料使用dummy預測")
#         df_product = pd.DataFrame([["",""]],columns=[])
#     
#     # **用 apply 加速資料清理**
#     df_product["cleaned_name"] = df_product["name"].apply(CreateModel.clean_product_name)
#     df_product["tokenized_name"] = df_product["cleaned_name"].apply(CreateModel.tokenize)
#     
#     # **批量轉換成向量**
#     user_vector = vectorizer.transform(df_product["tokenized_name"])    
# 
#     
#     similarity_scores = cosine_similarity(user_vector, product_vectors)
#     df_product['similarity'] = similarity_scores[0]
#     top_products = df_product.sort_values(by='similarity', ascending=False).head(50)
#     # **建立推薦結果的 JSON 結構**
#     recommend_data = [row["id"]for _ , row in top_products.iterrows()]
#     
#    
#     # **存入 Firebase `/recommend/{user_id}`**
#     db.child("recommend").child(user_id).set(recommend_data)
#     
#     print(f"✅ 已成功儲存推薦結果至 /recommend/{user_id}")
#     return top_products[['id', 'name', 'similarity']]
#     
# 
# =============================================================================
