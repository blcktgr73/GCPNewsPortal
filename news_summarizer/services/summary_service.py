from datetime import datetime
from google.cloud import firestore
from services.gemini_service import fetch_grounded_news

db = firestore.Client()

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
            "type": "grounding_v1" # 버전/타입 구분용
        }
        collection_ref.add(doc)

        print(f"[SAVE] {user_id} 저장 완료: {title}")
