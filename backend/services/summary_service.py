from firebase_admin import firestore
from models.summary_model import NewsSummary

db = firestore.client()

def save_summary(user_id: str, summary: NewsSummary):
    doc_ref = db.collection("users").document(user_id).collection("summaries").document()
    doc_ref.set(summary.dict())

def get_summaries(user_id: str):
    docs = db.collection("users").document(user_id).collection("summaries")\
        .order_by("createdAt", direction=firestore.Query.DESCENDING).stream()
    return [doc.to_dict() for doc in docs]
