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
from collections import Counter

from gensim.models import Word2Vec
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier
from scipy.stats import mode
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
include_cat={
    #食品
    85:[*range(1,22),],                     
    #3C
    86:[27,30,33,34,35,36],                 
    #家電
    87:[22,23,24,25,26,27,28,29,31,32,61,62],        
    #保健美容
    88:[38,40,*range(95,103),119],                             
    #日用
    89:[37,39,43,44,45,46,48,57,58,59,79,80,109,111],     
    #時尚
    90:[73,74,75,76,77,81,82,83,84,108],                                
    #家具
    91:[*range(61,71),116,118],                             
    #飾品
    92:[72,106],                             
    #戶外
    93:[47,49,50,51,52,55,56,112,114,117],
    #辦公
    94:[53,113,],
    }
def get_category_tokens(df,pattern=pattern,include_cat=include_cat):
    df1 = df.loc[df.store_name=="costco"]
    category_tokens = {
        cat: [
            token for token in itertools.chain.from_iterable(token_lists) 
            if not pattern.match(token)
        ]
        for cat, token_lists in df1.groupby("category_id")["tokens"]
    }

    
    # 依據 include_cat 更新 category_tokens
    for i in range(min(category_tokens.keys()), max(category_tokens.keys()) + 1):
       if i in include_cat:
           for sub_cat in include_cat[i]:
               # 取得子類別的 tokens 列表並過濾
               tokens_list = df.loc[df.category_id == sub_cat, "tokens"].sum()
               try:
                   filtered_tokens = [token for token in tokens_list if not pattern.match(token)]
                   # 更新主類別的 token
                   category_tokens[i].extend(filtered_tokens)
               except:
                   pass
               
               
   
   # 篩選掉只出現一次的 token
    all_tokens = list(itertools.chain.from_iterable(category_tokens.values()))  # 平展所有 tokens
    token_counts = Counter(all_tokens)  # 計算每個 token 的頻次

    # 過濾掉頻次為 1 的 token 並轉為set
    for i in category_tokens:
       category_tokens[i] = list(set([token for token in category_tokens[i] if token_counts[token] > 1]))
   
    return category_tokens

def extract_features(category_tokens):
    # 計算每個 token 的熵
    token_entropy = calculate_token_entropy(category_tokens)
    
    # 設置熵閾值並創建 stop words 集合
    stop_words = create_stop_words(token_entropy, threshold=0.1)
    
    # 過濾掉 stop words
    filtered_category_tokens = filter_stop_words(category_tokens, stop_words)
    
    print("filtered_category_tokens Done")
    # 轉換每個分類的 token 為單一字符串（文本），這樣可以用於詞頻向量化
    return {
        cat: ' '.join(token for token in tokens)  # 將每個類別的 token 轉換為單一的字符串
        for cat, tokens in filtered_category_tokens.items()
    }

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

def model_create():
    conn = sql.connect(path / SQL_path)
    query = """SELECT p.id, p.name, p.category_id, s.name AS store_name, c.name AS category
    FROM myapp_product AS p
    JOIN myapp_category AS c ON p.category_id = c.id
    JOIN myapp_store AS s ON c.store_id = s.id;
    """
    
    df_product = pd.read_sql_query(query, conn)
    conn.close()

    df_product = data_preprocessing(df_product)
    category_tokens = get_category_tokens(df_product)       # 依 category_id 分組，並將 tokens 展平成一維陣列
    documents = extract_features(category_tokens)
    
    # 取得每個文檔的標籤，即每個文檔所屬的分類
    #labels = list(documents.keys())  # 類別名稱作為標籤
    #print(labels)
    texts = list(documents.values())  # 每個類別的 token 作為文本
    print("vectorizer Done")
    
    # 讓 Vectorizer 按照商品名稱（單獨處理每篇文章）
    vectorizer = TfidfVectorizer(
        max_df=0.4,           # 移除在 40% 以上文件中出現的詞
        ngram_range=(1,2)     # 允許 unigram 和 bigram
    )

    
    X = vectorizer.fit_transform(texts)
    
    df_product['tokens'] = df_product['tokens'].apply(lambda x: ' '.join(x))
    df_product['category_id'] = df_product['category_id'].apply(
        lambda x: next((k for k, v in include_cat.items() if x in v), None)
        )    
    df_product.dropna(subset ='category_id' ,inplace=True)
    X = df_product['tokens'] 
    y=df_product['category_id']
    #vectorizer = Word2Vec(sentences=df_product['tokens'].tolist(), vector_size=100, window=5, min_count=1, workers=4)
    
    #給預測及推薦功能使用
    W_vectorizer = Word2Vec(sentences=list(documents.values()), vector_size=100, window=5, min_count=1, workers=4)
    joblib.dump(W_vectorizer, path / "bigdata/Word2Vec.pkl")
    X = vectorizer.transform(X)
    
    #X = np.vstack( df_product['tokens'].apply(lambda x : get_sentence_vector(vectorizer,x)))
    
    
    

    model = RandomForestClassifier(n_estimators=200, class_weight='balanced')
    print("model build Done")
    
    
    # 訓練模型
    model.fit(X, y)
    print(model.score(X, y)) #印出解釋力
    joblib.dump(model, path / "bigdata/RFC_model.pkl")  # 儲存為 pkl 檔案
    joblib.dump(vectorizer, path / "bigdata/tfidf_vectorizer.pkl") # 儲存為 pkl 檔案
    print("模組及向量表已暫存")
    return model,vectorizer

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
    df_product["vector"] = df_product["tokenized_name"].apply(lambda words: get_sentence_vector(model, words))
    
    # **轉換成 numpy 陣列**
    product_vectors = np.stack(df_product["vector"])  # 直接轉成 numpy 陣列
    similarities = cosine_similarity(vector.reshape(1, -1), product_vectors)[0]

    # **排序並回傳前 N 個最相似的商品**
    df_product["similarity"] = similarities
    top_products = df_product.sort_values(by="similarity", ascending=False).head(top_n)

    return top_products[["id","name", "similarity"]]  # 回傳商品名稱與相似度

def most_similar_filter(search_product,top_n=5):
    df_product = joblib.load(path / "bigdata/df_product.pkl")  # 讀取 DataFrame
    vectorizer = joblib.load(path / "bigdata/Word2Vec.pkl")  # 讀取 Word2Vec 模型

    # **處理輸入商品名稱**
    cleaned_search = clean_product_name(search_product)  # 文字清理
    tokenize_search = tokenize(cleaned_search)  # 斷詞
    print(tokenize_search)
    vector = get_sentence_vector(vectorizer, tokenize_search) # **使用 get_sentence_vector 取得向量**
    
    similar_products = find_similar_products(vectorizer,vector, df_product,top_n=5)
    return similar_products

    
def recommand_list_generator(top_n=50):
    df_product = joblib.load(path / "bigdata/df_product.pkl")  # 讀取商品 DataFrame
    model = Word2Vec.load(path / "bigdata/Word2Vec.pkl")  # 讀取 Word2Vec 模型

    conn = sql.connect(path / SQL_path)
    query = "SELECT user_id, product_id FROM myapp_followedproduct"
    df_follow = pd.read_sql_query(query, conn)

    # 加載商品向量
    df_product["vector"] = df_product["tokenized_name"].apply(lambda words: get_sentence_vector(model, words))

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
    if input("是否要使用生成推薦列表? y/n").upper() =="Y":
        recommand_list_generator()
        print("推薦列表已生成")
    elif input("是否要使用單一相關列表? y/n").upper() =="Y":
        similar_products = most_similar_filter(input("輸入商品名稱"),5)
        print(similar_products)
    elif input("是否要使用舊數據? y/n").upper() =="Y":
        model = joblib.load(path /"bigdata/RFC_model.pkl") #讀取模型
        vectorizer = joblib.load(path /"bigdata/tfidf_vectorizer.pkl") #讀取向量器
    else:
        model,vectorizer = model_create()
    if input("是否要使用舊dataframe? y/n").upper() =="Y": 
        df_product = joblib.load(path /"bigdata/df_product.pkl") ##讀取Dataframe
    else:
        conn = sql.connect(path / SQL_path)
        query = """
        SELECT id, name, category_id
        FROM myapp_product """
        
        df_product = pd.read_sql_query(query, conn)
        conn.close()
        
        # **預處理商品名稱**
        df_product = data_preprocessing(df_product)
        X = vectorizer.transform(df_product["tokens"].apply(lambda x: " ".join(x)))  
        #X = np.vstack( df_product['tokens'].apply(lambda x : get_sentence_vector(vectorizer,x)))
        print("資料向量化完成 預測模型中")
        # **批量預測**
        df_product["predicted_category"] = model.predict(X)
        
        df_product["category_id"] = df_product["category_id"].astype(int)
        df_product["predicted_category"] = df_product["predicted_category"].astype(int)
# =============================================================================
#         # 按 category_id 分組，對每組內的 predicted_category 計算眾數
#         df_product["predicted_category"] = (
#             df_product.groupby("category_id")["predicted_category"]
#             .transform(lambda x: mode(x)[0] if len(x) > 0 else 85))  # 取眾數
# =============================================================================
        
        joblib.dump(df_product, path / "bigdata/df_product.pkl") # 儲存為 pkl 檔案
    
    
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
    
    
    
    