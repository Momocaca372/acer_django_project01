import pyrebase


config = {
    "apiKey": "AIzaSyAb1S6EP5v3np68_R6jQc6JPrlx6UHuEuE",
    "authDomain": "djangofirebase-949f7.firebaseapp.com",
    "databaseURL": "https://djangofirebase-949f7-default-rtdb.firebaseio.com",
    "projectId": "djangofirebase-949f7",
    "storageBucket": "djangofirebase-949f7.firebasestorage.app",
    "messagingSenderId": "925644337298",
    "appId": "1:925644337298:web:e2769661ba39282dbe364b",
}

firebase = pyrebase.initialize_app(config)
db = firebase.database()