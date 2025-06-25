from google.cloud import firestore
from datetime import datetime

db = firestore.Client()

def add_keyword(user_id: str, keyword: str) -> str:
    # ✅ 상위 user 문서가 없다면 빈 문서라도 생성 (merge=True)
    db.collection("users").document(user_id).set({}, merge=True)
    
    keyword_ref = db.collection("users").document(user_id).collection("keywords")
    existing = keyword_ref.where("keyword", "==", keyword).limit(1).stream()
    if any(existing):
        raise ValueError("Keyword already exists")

    doc_ref = keyword_ref.document()
    doc_ref.set({
        "keyword": keyword,
        "created_at": datetime.utcnow().isoformat()
    })
    return doc_ref.id

def get_keywords(user_id: str):
    docs = db.collection("users").document(user_id).collection("keywords").stream()
    return [
        {"id": doc.id, **doc.to_dict()} for doc in docs
    ]

def delete_keyword(user_id: str, keyword_id: str):
    ref = db.collection("users").document(user_id).collection("keywords").document(keyword_id)
    if not ref.get().exists:
        raise ValueError("Keyword not found")
    ref.delete()

