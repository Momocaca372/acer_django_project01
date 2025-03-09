import math
import sqlite3 as sql
import pathlib
import pandas as pd
import jieba
import re
import itertools
import nltk
import joblib

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier

path = pathlib.Path(__file__).parent
conn = sql.connect(path / "db.sqlite3")
cur = conn.cursor()
# 讀取 product 表
df_product = pd.read_sql_query("SELECT id,store_id ,category_id FROM product", conn)

# 讀取 product_detail 表
df_detail = pd.read_sql_query("SELECT product_id, name FROM product_detail", conn)
df_detail.columns = ['id',"name"]
conn.close()
# 合併表，根據 `id` 欄位
df = pd.merge(df_product, df_detail, on="id", how="left")
df1 = df.loc[df['store_id']==1]


# 定義需要刪除的單位
units = ["g","kg", "克拉","毫升", "K", "尺", "呎","組","公升", "入","包入","入組","公分","袋入"
         "斤","公斤", "公克", "g", "ml", "L", "盒", "包", "瓶", "顆", "件"]
units_pattern = r"\b\d+\s*(" + "|".join(units) + r")\b"  # 建立正則表達式

def clean_product_name(text):
    text = text.lower()  # 轉小寫
    text = re.sub(units_pattern, "", text)  # 刪除開頭數字+單位
    text = re.sub(r"[^a-zA-Z0-9\u4e00-\u9fff\s]", "", text)  # 移除所有特殊符號
    text = re.sub(r"\s+", " ", text).strip()  # 移除多餘空格
    return text
df1.name = df1.name.apply(lambda x:clean_product_name(x)) 


# 中文分詞（使用 jieba），英文分詞（使用 nltk）
def tokenize(text):
    if any('\u4e00' <= char <= '\u9fff' for char in text):  # 檢查是否有中文
        return jieba.lcut(text)  # 中文用 jieba
    else:
        return nltk.word_tokenize(text)  # 英文用 nltk

df1['tokens'] = df1['name'].apply(tokenize)
# 定義正則表達式(12, @2,60ml,50mlx6)
pattern = re.compile(r"^(?:\d+|\W+|\d+[a-zA-Z]+|\d+\W*\d*[a-zA-Z]*)$") 

# 依 category_id 分組，並將 tokens 展平成一維陣列
category_tokens = {
    cat: [
        token for token in itertools.chain.from_iterable(token_lists) 
        if not pattern.match(token)
    ]
    for cat, token_lists in df1.groupby("category_id")["tokens"]
}


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
        token_entropy[token] = calculate_entropy(token, category_tokens)
    
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

# 計算每個 token 的熵
token_entropy = calculate_token_entropy(category_tokens)

# 設置熵閾值並創建 stop words 集合
stop_words = create_stop_words(token_entropy, threshold=0.5)

# 過濾掉 stop words
filtered_category_tokens = filter_stop_words(category_tokens, stop_words)
include_words = ["貓", "狗", "犬", "糧","寵物","喵","汪"]

# 針對 [250:576] 範圍內的數據進行篩選，其他部分保持不變
filtered_category_tokens[5] = filtered_category_tokens[5][:780]
# 只對 [250:576] 區間進行篩選
filtered_category_tokens[5][250:576] = list(map(
    lambda x: x if any(word in x for word in include_words) else None,
    filtered_category_tokens[5][250:576]
))

# 移除 None
filtered_category_tokens[5] = list(filter(None, filtered_category_tokens[5]))
print("filtered_category_tokens Done")
# 轉換每個分類的 token 為單一字符串（文本），這樣可以用於詞頻向量化
documents = {
    cat: ' '.join(token for token in tokens)  # 將每個類別的 token 轉換為單一的字符串
    for cat, tokens in category_tokens.items()
}

# 取得每個文檔的標籤，即每個文檔所屬的分類
labels = list(documents.keys())  # 類別名稱作為標籤
texts = list(documents.values())  # 每個類別的 token 作為文本

print("vectorizer Done")
# 讓 Vectorizer 按照商品名稱（單獨處理每篇文章）
vectorizer = TfidfVectorizer(
    stop_words=['a', 'an', 'the', 'of', 'on', '的', '是', '了', '和', '入','kirkland'],
    ngram_range=(1, 2)  # 同時學習單字和詞組，提高泛化能力
)
X = vectorizer.fit_transform(texts)

X = df1['tokens'].apply(lambda x: ' '.join(x))
X = vectorizer.transform(X)
y = df1['category_id']

#X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
print("model builing")
# 訓練模型
model = RandomForestClassifier(n_estimators=100)
model.fit(X, y)
print(model.score(X, y))


def data_classify(model,vectorizer,name):
    name = clean_product_name(name)
    name = ' '.join(tokenize(name))
    print(name)
    X = vectorizer.transform([name])
    print(X)
    print(model.predict(X))



# 假設你的 GMM 模型是 gmm
joblib.dump(model, "RFC_model.pkl")  # 儲存為 pkl 檔案
joblib.dump(vectorizer, "tfidf_vectorizer.pkl") # 儲存為 pkl 檔案
