
import os
import json
import time
from google.cloud import pubsub_v1
from dotenv import load_dotenv

# Load environment variables
load_dotenv("./tools/.env")

# Configuration
PROJECT_ID = "gcpnewsportal"
TOPIC_ID = "worker-news-summary"

def publish_message(user_id, keyword):
    publisher = pubsub_v1.PublisherClient()
    topic_path = publisher.topic_path(PROJECT_ID, TOPIC_ID)

    data = {
        "user_id": user_id,
        "keyword": keyword
    }
    
    # Data must be a bytestring
    data_str = json.dumps(data)
    data_bytes = data_str.encode("utf-8")

    print(f"Publishing message to {topic_path}...")
    print(f"Data: {data_str}")

    try:
        publish_future = publisher.publish(topic_path, data_bytes)
        # Wait for the publish to complete
        message_id = publish_future.result()
        print(f"✅ Message published successfully! Message ID: {message_id}")
        return True
    except Exception as e:
        print(f"❌ Failed to publish message: {e}")
        return False

if __name__ == "__main__":
    # Test Data
    USER_ID = "test_user_manual"
    KEYWORD = "Google Gemini"
    
    print("--- Triggering News Summary ---")
    if publish_message(USER_ID, KEYWORD):
        print("\nNow check the Cloud Function logs with:")
        print(f"gcloud functions logs read summarize_news --region asia-northeast3 --limit 20")
