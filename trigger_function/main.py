import base64
import json
import requests  # Worker Function이 HTTP로 구성된 경우

def trigger_news_summary(event, context):
    """
    Pub/Sub 메시지를 수신하여 Worker Function 호출
    """
    if 'data' not in event:
        print("No data found in event")
        return

    # 1. 메시지 디코딩
    payload = base64.b64decode(event['data']).decode('utf-8')
    data = json.loads(payload)

    user_id = data.get("user_id", "system")
    keywords = data.get("keywords", [])
    print(f"user_id: {user_id}, keywords:{keywords}")

    if not keywords or not user_id:
        print("Missing user_id or keywords")
        return

    # 2. Worker Function 호출
    worker_url = "https://asia-northeast3-gcpnewsportal.cloudfunctions.net/summarize_news"  # 실제 배포된 URL로 교체
    #worker_url = "http://localhost:8080"
    headers = {"Content-Type": "application/json"}

    for keyword in keywords:
        body = {"user_id": user_id, "keyword": keyword}
        try:
            response = requests.post(worker_url, json=body, headers=headers)
            print(f"Worker response: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"Failed to call worker: {str(e)}")
