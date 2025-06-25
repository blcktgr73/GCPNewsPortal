from google.cloud import pubsub_v1
from utils.keywords_service import fetch_all_user_keywords
from flask import jsonify
import json
import functions_framework

publisher = pubsub_v1.PublisherClient()
topic_path = publisher.topic_path("gcpnewsportal", "worker-news-summary")

@functions_framework.http
def trigger_news_summary(request):
    print(f"[🔍] trigger_news_summary")
    try:
        user_keywords_list = fetch_all_user_keywords()

        for entry in user_keywords_list:
            user_id = entry["user_id"]
            for keyword in entry["keywords"]:
                print(f"[🔍] publish topic {user_id} {keyword}")
                payload = {
                    "user_id": user_id,
                    "keyword": keyword
                }
                publisher.publish(topic_path, json.dumps(payload).encode("utf-8"))

        return jsonify({"status": "triggered", "users": len(user_keywords_list)})
    except Exception as e:
        print("Error occurred:", str(e))
        return jsonify({"status": "error", "message": str(e)}), 500
