import firebase_admin

# GCP 환경에서는 Application Default Credential 자동 사용
if not firebase_admin._apps:
    firebase_admin.initialize_app()