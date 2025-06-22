from firebase_admin import firestore
from models.summary_model import NewsSummary
from typing import List, Dict

db = firestore.client()

def save_summary(user_id: str, summary: NewsSummary):
    doc_ref = db.collection("users").document(user_id).collection("summaries").document()
    doc_ref.set(summary.dict())

def fetch_summaries_by_user(user_id: str) -> List[Dict]:
    summaries_ref = (
        db.collection("users")
        .document(user_id)
        .collection("summaries")
        .order_by("createdAt", direction=firestore.Query.DESCENDING)
    )
    docs = summaries_ref.stream()

    results = []
    for doc in docs:
        data = doc.to_dict()
        data["id"] = doc.id
        results.append(data)

    return results