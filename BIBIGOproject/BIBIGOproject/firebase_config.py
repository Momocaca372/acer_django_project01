import pyrebase
import firebase_admin
from firebase_admin import credentials
import os

# Pyrebase 配置（用於客戶端功能，例如電子郵件/密碼登入）
config = {
    "apiKey": "AIzaSyAb1S6EP5v3np68_R6jQc6JPrlx6UHuEuE",
    "authDomain": "djangofirebase-949f7.firebaseapp.com",
    "databaseURL": "https://djangofirebase-949f7-default-rtdb.firebaseio.com",
    "projectId": "djangofirebase-949f7",
    "storageBucket": "djangofirebase-949f7.firebasestorage.app",
    "messagingSenderId": "925644337298",
    "appId": "1:925644337298:web:e2769661ba39282dbe364b",
}
firebase = pyrebase.initialize_app(config)  # 初始化 Pyrebase
db = firebase.database()  # 回傳資料庫物件
pyrebase_auth = firebase.auth()  # 回傳認證物件

# Firebase Admin 配置（用於後端管理功能，例如驗證 ID Token）
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
cred_path = os.path.join(BASE_DIR, "service_account", "djangofirebase-949f7-firebase-adminsdk-fbsvc-f8d620bc57.json")

# 初始化 Firebase Admin（只執行一次）
if not firebase_admin._apps:  # 檢查是否已初始化，避免重複
    cred = credentials.Certificate(cred_path)
    firebase_admin.initialize_app(cred)
