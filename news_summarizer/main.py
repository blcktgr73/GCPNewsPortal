import base64
import json
from services.summary_service import summarize_and_store

def summarize_news(event, context):
    message = base64.b64decode(event['data']).decode('utf-8')
    payload = json.loads(message)

    user_id = payload.get("user_id")
    keyword = payload.get("keyword")

    if not user_id or not keyword:
        raise ValueError("Invalid message")

    print(f"received {user_id} {keyword}")
    summarize_and_store(user_id=user_id, keyword=keyword)
