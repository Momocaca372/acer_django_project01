import pathlib
import pandas as pd
import jieba
import re
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
SQL_path = "db.sqlite3"  
config = {
"apiKey": "AIzaSyAb1S6EP5v3np68_R6JQc6JPrlx6UHuEuE",
"authDomain": "djangofirebase-949f7.firebaseapp.com",
"databaseURL": "https://djangofirebase-949f7-default-rtdb.firebaseio.com",
"projectId": "djangofirebase-949f7",
"storageBucket": "djangofirebase-949f7.firebasestorage.app",
"messagingSenderId": "925644337298",
"appId": "1:925644337298:web:e2769661ba39282dbe364b",
}
path = pathlib.Path(__file__).parent.parent.parent




def clean_product_name(text):
    """清理商品名稱

    Args:
        text (String): 商品名稱

    Returns:
        String: 回傳清理後的商品名稱
    """
    # 定義需要刪除的單位
    units = ["g","kg", "克拉","毫升", "K", "尺", "呎","組","公升", "入","包入","入組","公分","袋入"
             "斤","公斤", "公克", "g", "ml", "L", "盒", "包", "瓶", "顆", "件"]
    units_pattern = r"\b\d+\s*(" + "|".join(units) + r")\b"  # 建立正則表達式
    text = text.lower()  # 轉小寫
    text = re.sub(units_pattern, "", text)  # 刪除開頭數字+單位
    text = re.sub(r"[^a-zA-Z0-9\u4e00-\u9fff\s]", "", text)  # 移除所有特殊符號
    text = re.sub(r"\s+", " ", text).strip()  # 移除多餘空格
    return text

def tokenize(text):
    """
    中文分詞（使用 jieba），英文分詞（使用 nltk）

    Args:
        text (String): 輸入字串

    Returns:
        String: 回傳斷詞後的字串 
    """
    
    
    if any('\u4e00' <= char <= '\u9fff' for char in text):  # 檢查是否有中文
        return jieba.lcut(text)  # 中文用 jieba
    else:
        return nltk.word_tokenize(text)  # 英文用 nltk 

def data_preprocessing(df_product):
    """資料前處理

    Args:
        df_product (DataFrame): 商品資料

    Returns:
        df_product (DataFrame): 處理後商品資料
    """
    def filter_tokens(tokens, regex):
        return [token for token in tokens if not regex.match(token)]

    # 定義需要刪除的字元
    pattern = re.compile(r"^(?:\d+|\W+|\d+[a-zA-Z]+|\d+\W*\d*[a-zA-Z]*|\s+)$")
    # Token過濾表
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

    # 商品名稱清理與斷詞
    df_product.name = df_product.name.apply(lambda x:clean_product_name(x)) 
    df_product['tokens'] = df_product['name'].apply(tokenize)
    
    # 應用過濾條件
    df_product['tokens'] = df_product['tokens'].apply(lambda x: filter_tokens(x, pattern))
    df_product['tokens'] = df_product['tokens'].apply(
        lambda tokens: [token for token in tokens if token not in filter_all]
    )
    return df_product

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

def create_Word2Vec():
    """
    創建 word2vec向量器與全站商品向量DataFrame
    """
    # 連接資料庫，讀取商品資料
    conn = sql.connect(path / SQL_path)
    query = """
    SELECT id,name
    FROM myapp_product """
    
    df_product = pd.read_sql_query(query, conn)
    conn.close()
    # 資料前處理
    df_product = data_preprocessing(df_product)
    # 創建 Word2Vec 模型
    W_vectorizer = Word2Vec(sentences=list(df_product.tokens),
                            vector_size=100, window=5, min_count=1, workers=4)
    W_vectorizer.save( str(path / "static/Word2Vec.pkl"))    
    # 儲存商品 DataFrame
    joblib.dump(df_product, path / "static/df_product.pkl")

def most_similar_filter(search_product,top_n=5,df_product=None,vectorizer=None):
    """
    Parameters
    ----------
    search_product: 查詢商品名稱
    top_n : int, optional
        DESCRIPTION. The default is 5.
    df_product: DataFrame 
    vectorizer: vectorizer
    Returns top_n 個物件
    -------

    """
    if df_product is None or vectorizer is None:
        df_product = joblib.load(path / "static/df_product.pkl")  # 讀取 DataFrame
        vectorizer = Word2Vec.load( str(path / "static/Word2Vec.pkl"))  # 讀取 Word2Vec 模型

    # **處理輸入商品名稱**
    cleaned_search = clean_product_name(search_product)  # 文字清理
    tokenize_search = tokenize(cleaned_search)  # 斷詞
    print(tokenize_search)
    vector = get_sentence_vector(vectorizer, tokenize_search) # **使用 get_sentence_vector 取得向量**
    
    similar_products = find_similar_products(vectorizer,vector, df_product,top_n=top_n)
    return similar_products
    
def recommand_list_generator(top_n=50,df_product=None,vectorizer=None):
    '''

    Parameters
    ----------
    top_n : TYPE, optional
        DESCRIPTION. The default is 50.

    為每個使用者推薦 top_n 個物件
    -------
    None.

    '''
    if df_product is None or vectorizer is None:
        df_product = joblib.load(path / "static/df_product.pkl")  # 讀取商品 DataFrame
        vectorizer = Word2Vec.load( str(path / "static/Word2Vec.pkl"))  # 讀取 Word2Vec 模型

    conn = sql.connect(path / SQL_path)
    query = "SELECT user_id, product_id FROM myapp_followedproduct"
    df_follow = pd.read_sql_query(query, conn)

    # 加載商品向量
    df_product["vector"] = df_product["tokens"].apply(lambda words: get_sentence_vector(vectorizer, words))

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
        cursor.execute("DROP TABLE IF EXISTS myapp_recommand_list")  # 先刪除舊的表
        cursor.execute("""
            CREATE TABLE myapp_recommand_list (
                user_id INTEGER,
                product_id INTEGER
            )
        """)
        cursor.executemany("INSERT INTO myapp_recommand_list (user_id, product_id) VALUES (?, ?)",
                           recommand_data)
        conn.commit()
    conn.close()
    
if __name__ == "__main__":
   pass

    
    
    

    