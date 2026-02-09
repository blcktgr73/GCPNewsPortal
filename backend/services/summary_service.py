from google.cloud import firestore
from models.summary_model import NewsSummary
from typing import List, Dict
from datetime import datetime
from services.google_news import get_google_news, summarize_with_gemini
from services.gemini_service import fetch_grounded_news

db = firestore.Client()

def save_summary(user_id: str, summary: NewsSummary):
    # ✅ 사용자 문서가 Firestore에 존재하도록 보장
    db.collection("users").document(user_id).set({}, merge=True)

    doc_ref = db.collection("users").document(user_id).collection("summaries").document()
    doc_ref.set(summary.dict())

def fetch_summaries_by_user(user_id: str, skip: int = 0, limit: int = 10) -> List[Dict]:
    summaries_ref = (
        db.collection("users")
        .document(user_id)
        .collection("summaries")
        .order_by("created_at", direction=firestore.Query.DESCENDING)
        .offset(skip)
        .limit(limit)
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

    # Grounding을 이용한 뉴스 수집 및 요약 (2-Phase)
    news_items = fetch_grounded_news(keyword)
    
    if not news_items:
        print(f"[WARN] {user_id} 뉴스 수집 실패 또는 결과 없음: {keyword}")
        return

    for item in news_items:
        title = item.get("title")
        url = item.get("url")
        summary = item.get("summary")
        
        # 추가 메타데이터
        published_at = item.get("published_at")
        source_name = item.get("source_name")

        if not title or not url:
            continue

        # 중복 여부 체크
        query = collection_ref.where("url", "==", url).limit(1).stream()
        exists = any(True for _ in query)

        if exists:
            print(f"[SKIP] {user_id} 이미 존재하는 URL: {url}")
            continue

        doc = {
            "title": title,
            "url": url,
            "summary": summary,
            "keyword": keyword,
            "published_at": published_at,
            "source_name": source_name,
            "created_at": datetime.utcnow().isoformat(),
            "summaryTokens": len(summary.split()) if summary else 0,
            "type": "grounding_v1"
        }
        collection_ref.add(doc)

        print(f"[SAVE] {user_id} 저장 완료: {title}")