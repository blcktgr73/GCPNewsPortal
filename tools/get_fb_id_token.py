import os
from dotenv import load_dotenv
import pyrebase

# .env 파일 로드
load_dotenv()

# Firebase 설정 정보
firebase_config = {
    "apiKey": os.getenv("FIREBASE_API_KEY"),
    "authDomain": os.getenv("FIREBASE_AUTH_DOMAIN"),
    "databaseURL": os.getenv("FIREBASE_DATABASE_URL"),
    "projectId": os.getenv("FIREBASE_PROJECT_ID"),
    "storageBucket": os.getenv("FIREBASE_STORAGE_BUCKET"),
    "messagingSenderId": os.getenv("FIREBASE_MESSAGING_SENDER_ID"),
    "appId": os.getenv("FIREBASE_APP_ID"),
    "measurementId": os.getenv("FIREBASE_MEASUREMENT_ID"),
}

firebase = pyrebase.initialize_app(firebase_config)
auth = firebase.auth()

# 로그인 정보
email = os.getenv("FIREBASE_EMAIL")
password = os.getenv("FIREBASE_PASSWORD")
user = auth.sign_in_with_email_and_password(email, password)

# 토큰 출력
id_token = user["idToken"]
print("Your Firebase ID Token:\n", id_token)
