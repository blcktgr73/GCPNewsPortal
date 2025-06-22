import os
from dotenv import load_dotenv

import firebase_admin
from firebase_admin import auth, credentials

# .env 파일 로드
load_dotenv()

# 환경변수에서 파일 경로 읽기
cred_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
if not cred_path:
    raise ValueError("환경변수 'GOOGLE_APPLICATION_CREDENTIALS'가 설정되지 않았습니다.")

# Firebase 초기화
cred = credentials.Certificate(cred_path)
firebase_admin.initialize_app(cred)

# 사용자 인증 및 토큰 생성
user = auth.get_user_by_email("test@example.com")
custom_token = auth.create_custom_token(user.uid)
print(custom_token)
