import os
from typing import List, Dict
from google.cloud import firestore
from datetime import datetime
from services.google_news import get_google_news, summarize_with_gemini

import firebase_admin
from firebase_admin import credentials

# Firebase Admin SDK 초기화 (단 한 번만 수행)
if not firebase_admin._apps:
    #cred_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    #if not cred_path:
    #    raise EnvironmentError("GOOGLE_APPLICATION_CREDENTIALS 환경변수가 설정되지 않았습니다.")
    #cred = credentials.Certificate(cred_path)
    #firebase_admin.initialize_app(cred)
    firebase_admin.initialize_app()

db = firestore.Client()


def save_summary_to_firestore(title: str, url: str, summary: str, keyword: str, user_id: str = "system") -> None:
    """중복 URL이 없을 때만 Firestore에 저장"""

    # 컬렉션 경로
    collection_ref = db.collection("users").document(user_id).collection("summaries")

    # 중복 여부 체크
    query = collection_ref.where("url", "==", url).limit(1).stream()
    exists = any(True for _ in query)

    if exists:
        print(f"[SKIP] 이미 존재하는 URL: {url}")
        return

    # 저장
    doc_ref = collection_ref.document()
    doc_ref.set({
        "url": url,
        "title": title,
        "summary": summary,
        "createdAt": datetime.utcnow().isoformat() + "Z",
        "source": "Google",
        "category": "News",
        "keywords": [keyword],
        "user_id": user_id,
        "summaryTokens": len(summary.split())
    })
    print(f"[SAVE] 저장 완료: {title}")


def summarize_and_store(keyword: str, user_id: str = "system") -> List[Dict]:
    """특정 키워드로 뉴스 검색 후 요약하고 Firestore에 저장"""
    news_items = get_google_news(keyword)
    results = []

    for title, url in news_items:
        # content_to_summarize = f"{item['title']}\n{item.get('content', '')}"
        summary = summarize_with_gemini(title, url)
        save_summary_to_firestore(title, url, summary, keyword, user_id)
        results.append({
            "title": title,
            "summary": summary,
            "url": url
        })

    return results
