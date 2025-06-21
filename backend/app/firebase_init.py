import os
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials

# .env 경로 설정
#load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

# Firebase Admin 초기화
#cred_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
#cred = credentials.Certificate(cred_path)
#firebase_admin.initialize_app(cred)

# GCP 환경에서는 Application Default Credential 자동 사용
if not firebase_admin._apps:
    firebase_admin.initialize_app()