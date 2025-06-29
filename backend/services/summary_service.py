from google.cloud import firestore
from models.summary_model import NewsSummary
from typing import List, Dict
from datetime import datetime
from services.google_news import get_google_news, summarize_with_gemini

db = firestore.Client()

def save_summary(user_id: str, summary: NewsSummary):
    # ✅ 사용자 문서가 Firestore에 존재하도록 보장
    db.collection("users").document(user_id).set({}, merge=True)

    doc_ref = db.collection("users").document(user_id).collection("summaries").document()
    doc_ref.set(summary.dict())

def fetch_summaries_by_user(user_id: str) -> List[Dict]:
    summaries_ref = (
        db.collection("users")
        .document(user_id)
        .collection("summaries")
        .order_by("created_at", direction=firestore.Query.DESCENDING)
    )
    docs = summaries_ref.stream()

    results = []
    for doc in docs:
        print(f"doc.id: {doc.id}, fields: {doc.to_dict()}")
        data = doc.to_dict()
        data["id"] = doc.id
        results.append(data)

    return results

def summarize_and_store(user_id: str, keyword: str):
    print(f"[🔍] Summary 요청: {user_id=}, {keyword=}")
    
    # ✅ 사용자 문서가 Firestore에 존재하도록 보장
    db.collection("users").document(user_id).set({}, merge=True)

    # 컬렉션 경로
    collection_ref = db.collection("users").document(user_id).collection("summaries")

    news_list = get_google_news(keyword)
    for title, url in news_list:
        # 중복 여부 체크
        query = collection_ref.where("url", "==", url).limit(1).stream()
        exists = any(True for _ in query)

        if exists:
            print(f"[SKIP] {user_id} 이미 존재하는 URL: {url}")
            continue

        summary = summarize_with_gemini(title, url)
        doc = {
            "title": title,
            "url": url,
            "summary": summary,
            "keyword": keyword,
            "created_at": datetime.utcnow().isoformat(),
            "summaryTokens": len(summary.split())
        }
        collection_ref.add(doc)

        print(f"[SAVE] {user_id} 저장 완료: {title}")