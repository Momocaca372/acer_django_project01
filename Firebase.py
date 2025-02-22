import pyrebase

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