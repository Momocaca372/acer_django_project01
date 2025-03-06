import math
import pathlib
import pandas as pd
import jieba
import re
import itertools
import nltk
import joblib
import pyrebase

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics.pairwise import cosine_similarity

class CreateModel():
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
    
    def __init__(self):
        #Firebase 設定值
        self.config = {
        "apiKey": "AIzaSyAb1S6EP5v3np68_R6JQc6JPrlx6UHuEuE",
        "authDomain": "djangofirebase-949f7.firebaseapp.com",
        "databaseURL": "https://djangofirebase-949f7-default-rtdb.firebaseio.com",
        "projectId": "djangofirebase-949f7",
        "storageBucket": "djangofirebase-949f7.firebasestorage.app",
        "messagingSenderId": "925644337298",
        "appId": "1:925644337298:web:e2769661ba39282dbe364b",
    }
        self.path = pathlib.Path(__file__).parent
        self.db = self.get_firebase_connection() #取得資料庫物件
        # 定義正則表達式(12, @2,60ml,50mlx6)
        self.pattern =re.compile(r"^(?:\d+|\W+|\d+[a-zA-Z]+|\d+\W*\d*[a-zA-Z]*)$") 
        self.model = RandomForestClassifier(n_estimators=100)
        self.vectorizer = TfidfVectorizer()
        self.df1 = self.load_data()
        self.df1.name = self.df1.name.apply(lambda x:self.clean_product_name(x)) 
        self.df1['tokens'] = self.df1['name'].apply(self.tokenize)
        self.category_tokens = self.get_category_tokens()        # 依 category_id 分組，並將 tokens 展平成一維陣列
        self.documents = self.extract_features()
        self.X = None
        self.y = None
        
    def get_firebase_connection(self):
        """建立與 Firebase 的連線"""
        firebase = pyrebase.initialize_app(self.config)  # 初始化 Firebase
        return firebase.database()  # 回傳資料庫物件
    
    def load_data(self):
        # 讀取 product 表
        ref = self.db.child("/product") 
        data = ref.get()  # 取得資料
        df_product = pd.json_normalize(data.val())
        ref = self.db.child("/product_detail") 
        data = ref.get()  # 取得資料
        # 讀取 product_detail 表
        df_detail = pd.json_normalize(data.val())
        df_detail = df_detail["name"]
        # 合併表，根據 `id` 欄位
        df = pd.concat([df_product, df_detail],axis=1 )
        df1 = df.loc[df['store_id']=='2']
        print("取得Dataframe Done")
        return df1
        
    def train_model(self):   
        # 取得每個文檔的標籤，即每個文檔所屬的分類
        labels = list(self.documents.keys())  # 類別名稱作為標籤
        print(labels)
        texts = list(self.documents.values())  # 每個類別的 token 作為文本
        print("vectorizer Done")
        # 讓 Vectorizer 按照商品名稱（單獨處理每篇文章）
        self.vectorizer = TfidfVectorizer(
            stop_words=['a', 'an', 'the', 'of', 'on', '的', '是', '了', '和', '入','kirkland'],
            ngram_range=(1, 2)  # 同時學習單字和詞組，提高泛化能力
        )
        self.X = self.vectorizer.fit_transform(texts)
        
        self.X = self.df1['tokens'].apply(lambda x: ' '.join(x))
        self.X = self.vectorizer.transform(self.X)
        self.y = self.df1['category_id']
        
        #X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        print("model build Done")
        return 
        
    def predict(self):
        # 訓練模型
        self.model.fit(self.X, self.y)
        print(self.model.score(self.X, self.y)) #印出解釋力
        joblib.dump(self.model, self.path / "RFC_model.pkl")  # 儲存為 pkl 檔案
        joblib.dump(self.vectorizer, self.path / "tfidf_vectorizer.pkl") # 儲存為 pkl 檔案
        return
    
    def get_category_tokens(self):
        return {
            cat: [
                token for token in itertools.chain.from_iterable(token_lists) 
                if not self.pattern.match(token)
            ]
            for cat, token_lists in self.df1.groupby("category_id")["tokens"]
        }
        
    def extract_features(self):
        # 計算每個 token 的熵
        token_entropy = self.calculate_token_entropy(self.category_tokens)
        
        # 設置熵閾值並創建 stop words 集合
        stop_words = self.create_stop_words(token_entropy, threshold=0.5)
        
        # 過濾掉 stop words
        filtered_category_tokens = self.filter_stop_words(self.category_tokens, stop_words)
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
        return {
            cat: ' '.join(token for token in tokens)  # 將每個類別的 token 轉換為單一的字符串
            for cat, tokens in self.category_tokens.items()
        }
    
    # 計算熵的函數
    def calculate_entropy(self,token, category_tokens):
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
    def calculate_token_entropy(self,category_tokens):
        token_entropy = {}
        all_tokens = set(itertools.chain.from_iterable(itertools.chain.from_iterable(category_tokens.values())))
        
        for token in all_tokens:
           token_entropy[token] =  self.calculate_entropy(token, category_tokens)
        
        return token_entropy
    
    # 設置熵的閾值來識別 stop words
    def create_stop_words(self,token_entropy, threshold=1.0):
        return {token for token, entropy in token_entropy.items() if entropy > threshold}
    
    # 去除 stop words
    def filter_stop_words(self,category_tokens, stop_words):
        filtered_category_tokens = {
            cat: [token for token in tokens if token not in stop_words]
            for cat, tokens in category_tokens.items()
        }
        return filtered_category_tokens
        
    def clean_product_name(self,text):
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
    def tokenize(self,text):
        if any('\u4e00' <= char <= '\u9fff' for char in text):  # 檢查是否有中文
            return jieba.lcut(text)  # 中文用 jieba
        else:
            return nltk.word_tokenize(text)  # 英文用 nltk
       
    def data_classify(self,model,vectorizer,name):
        name = self.clean_product_name(name)
        name = ' '.join(self.tokenize(name))
        print(name)
        X = vectorizer.transform([name])
        print(X)
        print(model.predict(X))
    

class ProductRlabeler():
    def __init__(self):
        '''
        save_to_firebase()
        recommand_list_genetor()
        '''
        self.table_path = "/product_detail"# 資料儲存路徑
        # Firebase 設定
        self.config = CreateModel().config
        self.max_chunk_size = 100000 # 根據需要調整大小，每次寫入最大 100,000 字元
        self.db = self.get_firebase_connection() #取得資料庫物件
        self.df = self.download_data_from_firebase() #取得資料
        self.model = joblib.load("bigdata/RFC_model.pkl") #讀取模型
        self.vectorizer = joblib.load("bigdata/tfidf_vectorizer.pkl") #讀取向量器
        self.result_dict = self.product_relabeler() #執行預測
        # 預先讀取商品詳細資料
        ref = self.db.child("/product_detail")
        data = ref.get()
        df = pd.json_normalize(data.val())
        
        # **預處理商品名稱**
        df["cleaned_name"] = df["name"].apply(CreateModel.clean_product_name)
        df["tokenized_name"] = df["cleaned_name"].apply(CreateModel.tokenize)
        
        # **批量轉換成向量**
        self.product_vectors = self.vectorizer.fit_transform(df["tokenized_name"])
        self.df_products = df  # 存商品資料以供查詢
        
    def get_firebase_connection(self):
        """建立與 Firebase 的連線"""
        print("建立與 Firebase 的連線")
        return CreateModel.get_firebase_connection()
    
    def split_and_upload_data(self,db, data):
        chunk = {}
        for key, value in data.items():
            chunk[key] = value
            if len(str(chunk)) >= self.max_chunk_size :
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
        return

    def download_data_from_firebase(self):
        """下載資料並轉換為 DataFrame"""
        ref = self.db.child(self.table_path)  
        data = ref.get()  # 取得資料

        if data.val():  # 確認資料存在
            rows = data.val()
            # 轉換為 DataFrame
            df = pd.json_normalize(rows)
            return df
        else:
            print("資料不存在")
            return None
    def product_relabeler(self):
        self.df.dropna(inplace=True)
        df = self.df[["product_id", "name"]]
        
        # 讀取模型 & 向量器
        model = self.model
        vectorizer = self.vectorizer
        
        
        
        # **用 apply 加速資料清理**
        df["cleaned_name"] = df["name"].apply(CreateModel.clean_product_name)
        df["tokenized_name"] = df["cleaned_name"].apply(CreateModel.tokenize)
        
        # **批量轉換成向量**
        X = vectorizer.transform(df["tokenized_name"])  
        print("資料向量化完成 預測模型中")
        # **批量預測**
        df["predicted_category"] = model.predict(X)
        
        # **計算連續 10 筆的眾數**
        window_size = 10  # 取最近10筆資料
        df["smoothed_category"] = (
            df["predicted_category"]
            .rolling(window=window_size, min_periods=1)
            .apply(lambda x: model(x)[0], raw=True)
            .fillna(1)
        )
        
        # **轉成 JSON 格式**
        result_dict = {"product_relabel": dict(zip(df["product_id"], df["smoothed_category"].astype(int)))}
        return result_dict
    
    def save_to_firebase(self):

        ref = self.db.child("/") 
        # 取得目前資料庫中的內容
        data = ref.get()
        if data.val() and 'product_relabel' in data.val():
            # 移除 'product_relabel' 欄位
            updated_data = data.val()
            del updated_data['product_relabel']

            # 更新資料
            updated_data.update(self.result_dict)

            # 將資料上傳到 Firebase
            self.split_and_upload_data(self.db, updated_data)
            print("資料已成功更新")
        else:
            self.split_and_upload_data(self.db, self.result_dict)
            print("資料已成功新增")
    
    def recommand_list_genetor(self,user_input,user_id):
        try:
            vectorizer = self.vectorizer
            ref = self.db.child("/care/"+user_id) 
            data = ref.get()  # 取得資料
            df_product = pd.json_normalize(data.val())
        except:
            print("找不到資料使用dummy預測")
            df_product = pd.DataFrame([["",""]],columns=[])
        
        # **用 apply 加速資料清理**
        df_product["cleaned_name"] = df_product["name"].apply(CreateModel.clean_product_name)
        df_product["tokenized_name"] = df_product["cleaned_name"].apply(CreateModel.tokenize)
        
        # **批量轉換成向量**
        user_vector = vectorizer.transform(df_product["tokenized_name"])    

        
        similarity_scores = cosine_similarity(user_vector, self.product_vectors)
        df_product['similarity'] = similarity_scores[0]
        top_products = df_product.sort_values(by='similarity', ascending=False).head(50)
        # **建立推薦結果的 JSON 結構**
        recommend_data = [row["id"]for _, row in top_products.iterrows()]
        
       
        # **存入 Firebase `/recommend/{user_id}`**
        self.db.child("recommend").child(user_id).set(recommend_data)
        
        print(f"✅ 已成功儲存推薦結果至 /recommend/{user_id}")
        return top_products[['id', 'name', 'similarity']]
    
if __name__=="__main__":
    # model = CreateModel()
    # model.train_model()
    # model.predict()
    ProductRlabeler()
