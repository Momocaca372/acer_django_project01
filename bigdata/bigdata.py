import numpy as np
import math
from collections import defaultdict, Counter
import sqlite3 as sql
import pathlib
import pandas as pd
import jieba
import re
import itertools
import nltk

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier


path = pathlib.Path(__file__).parent
conn = sql.connect(path / "db.sqlite3")
cur = conn.cursor()
# 讀取 product 表
df_product = pd.read_sql_query("SELECT id, category_id FROM product", conn)

# 讀取 product_detail 表
df_detail = pd.read_sql_query("SELECT id, name FROM product_detail", conn)

conn.close()
# 合併表，根據 `id` 欄位
df = pd.merge(df_product, df_detail, on="id", how="left")

# 中文分詞（使用 jieba），英文分詞（使用 nltk）
def tokenize(text):
    if any('\u4e00' <= char <= '\u9fff' for char in text):  # 檢查是否有中文
        return jieba.lcut(text)  # 中文用 jieba
    else:
        return nltk.word_tokenize(text)  # 英文用 nltk


df['tokens'] = df['name'].apply(tokenize)
# 定義正則表達式
pattern = re.compile(r"^(?:\d+[\W\d]*[a-zA-Z]{0,2}[\W\d]*|\W+)$") # 過濾純數字或純符號的 token

# 依 cat_id 分組，並將 tokens 展平為一維陣列
category_tokens = {
    cat: Counter(
        token for token in itertools.chain.from_iterable(tokens) if not pattern.match(token)
    )
    for cat, tokens in df.groupby("category_id")["tokens"]
}


# 統計每個 token 在不同類別內的分佈
token_distribution = defaultdict(list)

for cat, token_counts in category_tokens.items():
    for token, count in token_counts.items():
        token_distribution[token].append(count)

# 計算標準差 & 熵
def entropy(counts):
    total = sum(counts)
    probs = [count / total for count in counts]
    return -sum(p * math.log2(p) for p in probs if p > 0)

token_std = {token: np.std(counts) for token, counts in token_distribution.items()}
token_entropy = {token: entropy(counts) for token, counts in token_distribution.items()}

# 設定標準差 & 熵閾值
std_threshold = 5  # 標準差低於此值的 token 會調整權重
entropy_threshold = 0.9  # 熵高於此值的 token 會被刪除

# 調整 token 權重
adjusted_weights = {}
stop_words = set()

for token, counts in token_distribution.items():
    if token_entropy[token] > entropy_threshold:
        stop_words.add(token)  # 熵過高的 token 直接刪除
    elif token_std[token] < std_threshold:
        adjusted_weights[token] = [np.sqrt(w) for w in counts]  # 權重開根號
    else:
        adjusted_weights[token] = counts  # 保持原始權重

# 使用字典推導式過濾掉 stop_words 中的類別，並更新權重
filtered_category_tokens = {
    cat: {
        token: (count**0.5) if token not in stop_words else None  # 更新權重，stop_words 中的 token 刪除
        for token, count in tokens.items() if token not in stop_words  # 過濾掉 stop_words 中的 token
    }
    for cat, tokens in category_tokens.items()
    if cat not in stop_words  # 先過濾掉 stop_words 中的類別
}


# 轉換每個分類的 token 為單一字符串（文本），這樣可以用於詞頻向量化
documents = {
    cat: ' '.join(tokens.keys())  # 將每個類別的 token 轉換為單一的字符串
    for cat, tokens in category_tokens.items()
}

# 取得每個文檔的標籤，即每個文檔所屬的分類
labels = list(documents.keys())  # 類別名稱作為標籤
texts = list(documents.values())  # 每個類別的 token 作為文本

# 使用 TfidfVectorizer 將文本轉換為詞頻矩陣
vectorizer = TfidfVectorizer()
X = vectorizer.fit_transform(texts)

X = df['tokens'].apply(lambda x: ' '.join(x))
X = vectorizer.transform(X)
y = df['category_id']

#X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# 訓練模型
model = RandomForestClassifier(n_estimators=100)
#model = DecisionTreeClassifier()
model.fit(X, y)

# 評估模型
print( model.score(X,y))
