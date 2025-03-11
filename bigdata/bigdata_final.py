import math
import pathlib
import pandas as pd
import jieba
import re
import itertools
import nltk
import joblib
import sqlite3 as sql
import numpy as np

from gensim.models import Word2Vec
from sklearn.metrics.pairwise import cosine_similarity


"""
使用方法: 直接執行可更新模駔，再來生成relabel_table
    most_similar_filter(str,n=int) 輸入文字會回傳一張數量n的表
    recommand_list_generator 會直接生成myapp_recommand_list供人使用
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

# 定義正則表達式(12, @2,60ml,50mlx6)
pattern = re.compile(r"^(?:\d+|\W+|\d+[a-zA-Z]+|\d+\W*\d*[a-zA-Z]*|\s+)$")



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


def data_preprocessing(df_product):
    filter_all =set(["x","kirkland","適用","件裝","尋找","入組",
                     "signature","精選濾","精選","配方","毫克","口味","均衡",
                     "加強","one","a","day","漢方","海洋","組合","科克","蘭",
                     "美國","特調","漢方","亮妍","超薄","個","基礎","伊布","包組",
                     "雙二入","超抗","不沾深","show","f21","爆汁方","全新",
                     "心情","oo","超輕薄","雙舒壓","環炫亮","銳利","涼拌",
                     "兩雙股","類比數","冰絲涼","藕荷色","課程","出貨款","平價幸",
                     "平價","x100","mm10","退貨","入門學","潔淨亮","48mmx35mx6",
                     "英尺","港式","24v15a","創世神","件套","超耐熱","奢華繽紛",
                     "盛開","夜間","正式","20pcx4","附匙","薄霧","精工"," ",
                     '每包', '約', '306', '克'
                     ])

    df_product.name = df_product.name.apply(lambda x:clean_product_name(x)) 
    df_product['tokens'] = df_product['name'].apply(tokenize)
    # 應用過濾條件
    df_product['tokens'] = df_product['tokens'].apply(
        lambda tokens: [token for token in tokens if token not in filter_all]
    )

    return df_product

def create_Word2Vec():
    conn = sql.connect(path / SQL_path)
    query = """
    SELECT id,name
    FROM myapp_product """
    
    df_product = pd.read_sql_query(query, conn)
    conn.close()
    df_product = data_preprocessing(df_product)
    #給預測及推薦功能使用
    W_vectorizer = Word2Vec(sentences=list(df_product.tokens), vector_size=100, window=5, min_count=1, workers=4)
    W_vectorizer.save( str(path / "bigdata/Word2Vec.pkl"))    
    joblib.dump(df_product, path / "bigdata/df_product.pkl")


def get_sentence_vector(model, words=""):
    """取得句子的平均詞向量"""
    word_vectors = [model.wv[word] for word in words if word in model.wv]  
    if len(word_vectors) == 0:
        return np.zeros(model.vector_size)  # 若沒有詞向量，回傳零向量
    return np.mean(word_vectors, axis=0)  # 取平均向量

def find_similar_products(model, vector, df_product, top_n=5):
    """
    使用 Word2Vec + Cosine Similarity 找出最相似的商品
    model: Word2Vec 模型
    vector: 搜尋詞的向量
    df_product: 包含商品名稱與向量的 DataFrame
    top_n: 取前 N 個最相似的商品
    """
    # **確保 df_product["vector"] 內的向量正確**
    df_product["vector"] = df_product["tokens"].apply(lambda words: get_sentence_vector(model, words))
    
    # **轉換成 numpy 陣列**
    product_vectors = np.stack(df_product["vector"])  # 直接轉成 numpy 陣列
    similarities = cosine_similarity(vector.reshape(1, -1), product_vectors)[0]

    # **排序並回傳前 N 個最相似的商品**
    df_product["similarity"] = similarities
    top_products = df_product.sort_values(by="similarity", ascending=False).head(top_n)

    return top_products[["id","name", "similarity"]]  # 回傳商品名稱與相似度

def most_similar_filter(search_product,top_n=5):
    """
    Parameters
    ----------
    search_product: 查詢商品名稱
    top_n : TYPE, optional
        DESCRIPTION. The default is 5.

    Returns top_n 個物件
    -------

    """
    df_product = joblib.load(path / "bigdata/df_product.pkl")  # 讀取 DataFrame
    vectorizer = Word2Vec.load( str(path / "bigdata/Word2Vec.pkl"))  # 讀取 Word2Vec 模型

    # **處理輸入商品名稱**
    cleaned_search = clean_product_name(search_product)  # 文字清理
    tokenize_search = tokenize(cleaned_search)  # 斷詞
    #print(tokenize_search)
    vector = get_sentence_vector(vectorizer, tokenize_search) # **使用 get_sentence_vector 取得向量**
    
    similar_products = find_similar_products(vectorizer,vector, df_product,top_n=top_n)
    return similar_products

    
def recommand_list_generator(top_n=50):
    '''

    Parameters
    ----------
    top_n : TYPE, optional
        DESCRIPTION. The default is 50.

    為每個使用者推薦 top_n 個物件
    -------
    None.

    '''
    df_product = joblib.load(path / "bigdata/df_product.pkl")  # 讀取商品 DataFrame
    model = Word2Vec.load( str(path / "bigdata/Word2Vec.pkl"))  # 讀取 Word2Vec 模型

    conn = sql.connect(path / SQL_path)
    query = "SELECT user_id, product_id FROM myapp_followedproduct"
    df_follow = pd.read_sql_query(query, conn)

    # 加載商品向量
    df_product["vector"] = df_product["tokens"].apply(lambda words: get_sentence_vector(model, words))

    # **準備寫入 SQL**
    recommand_data = []

    for user, user_products in df_follow.groupby("user_id"):
        user_vectors = df_product[df_product["id"].isin(user_products["product_id"])]["vector"].tolist()

        if not user_vectors:
            continue  # 如果該用戶沒有有效的商品向量，則跳過

        user_profile_vector = np.mean(user_vectors, axis=0)  # 用戶的個人向量（取平均）
        product_vectors = np.stack(df_product["vector"].tolist())  # 轉換為 2D 陣列
        
        similarities = cosine_similarity(user_profile_vector.reshape(1, -1), product_vectors)[0]

        df_product["similarity"] = similarities
        top_products = df_product.sort_values(by="similarity", ascending=False).head(top_n)

        for product_id in top_products["id"]:
            recommand_data.append((user, product_id))
        
    # **將推薦結果存入 SQLite**
    with conn:
        cursor = conn.cursor()
        cursor.execute("DROP TABLE IF EXISTS recommand_list")  # 先刪除舊的表
        cursor.execute("""
            CREATE TABLE myapp_recommand_list (
                user_id INTEGER,
                product_id INTEGER
            )
        """)
        cursor.executemany("INSERT INTO myapp_recommand_list (user_id, product_id) VALUES (?, ?)", recommand_data)
    
    conn.close()
    
if __name__ == "__main__":
    if input("是否要初始化模組? y/n").upper() =="Y":
        create_Word2Vec()
    elif input("是否要使用生成推薦列表? y/n").upper() =="Y":
        recommand_list_generator()
        print("推薦列表已生成")
    elif input("是否要使用單一相關列表? y/n").upper() =="Y":
        similar_products = most_similar_filter(input("輸入商品名稱"),5)
        print(similar_products)
    
    
    
    