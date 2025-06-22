import base64
import json
from main import trigger_news_summary  # trigger 함수 import

class MockContext:
    def __init__(self):
        self.event_id = '123456'
        self.timestamp = '2023-01-01T00:00:00.000Z'

# 테스트 데이터 생성
def create_pubsub_event(data_dict):
    data_str = json.dumps(data_dict)
    data_bytes = data_str.encode("utf-8")
    base64_bytes = base64.b64encode(data_bytes)
    return {
        "data": base64_bytes.decode("utf-8")
    }

# 실행
if __name__ == "__main__":
    # 테스트 키워드 목록
    user_id = "user123"
    keywords = ["디플레이션", "부동산", "전세가", "KOSPI"]

    print(f"[TEST] Triggering user_id = {user_id}, keywords: {keywords}")
    event = create_pubsub_event({"user_id": user_id, "keywords": keywords})
    trigger_news_summary(event, MockContext())
    print("Event Triggered")
