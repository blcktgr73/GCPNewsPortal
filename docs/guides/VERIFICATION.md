
# 🛠️ GCPNewsPortal Verification Guide

This document outlines the steps to verify the deployment and functionality of the **GCPNewsPortal** services, specifically the **News Summarizer** (Cloud Functions) and **Backend API** (Cloud Run).

## 1. Prerequisites

Ensure you have the following installed and configured:
- **Google Cloud SDK (`gcloud`)**: Authenticated and set to project `gcpnewsportal`.
- **Python 3.11+**: Environment set up.
- **`google-cloud-pubsub`**: Installed (`pip install google-cloud-pubsub`).

## 2. Check Deployment Status

### Cloud Functions (`summarize_news`)
Verify the function is active and serving traffic.

```bash
gcloud functions describe summarize_news --region asia-northeast3 --format="value(state)"
# Expected Output: ACTIVE
```

### Cloud Run (`news-backend`)
Verify the backend service is running and get the Service URL.

```bash
gcloud run services describe news-backend --region asia-northeast3 --format="value(status.url)"
# Expected Output: https://news-backend-1069077238668.asia-northeast3.run.app
```

## 3. Verify News Summarization Flow (End-to-End)

The news summarization process is triggered by a Pub/Sub message. Follow these steps to simulate a trigger and verify the result.

### Step 1: Trigger the Process (Publish Message)

Run the provided Python script to send a test message to the `worker-news-summary` topic.

```bash
# Ensure dependencies are installed
pip install google-cloud-pubsub python-dotenv

# Run the trigger script
python tools/trigger_news_summary.py
```
> **Note:** If you encounter `DefaultCredentialsError`, ensure `tools/.env` has the correct absolute path for `GOOGLE_APPLICATION_CREDENTIALS`.

**Alternative (using gcloud CLI directly):**
```bash
gcloud pubsub topics publish worker-news-summary --message="{\"user_id\":\"manual_verify\",\"keyword\":\"Google Gemini\"}"
```

### Step 2: Validate via Logs (Wait ~30s)

After triggering, wait about 15-30 seconds for Gemini to process the request, then check the logs.

```bash
gcloud functions logs read summarize_news --region asia-northeast3 --limit 20
```

**What to look for:**
- `[Phase 1] Fetching RSS for: Google Gemini` (News Discovery)
- `[Phase 2] Analyzing ... articles with Gemini...` (Gemini Processing)
- `[SAVE] manual_verify 저장 완료` (Success! Saved to Firestore)

If you see the `[SAVE]` log, the entire pipeline is working correctly.

## 4. Troubleshooting

- **`403 Forbidden` / `DefaultCredentialsError`**: Check service account permissions and `GOOGLE_APPLICATION_CREDENTIALS` path.
- **`JSONDecodeError`**: The Pub/Sub message payload must be valid JSON.
- **`[Gemini Error]`**: Check if `GEMINI_API_KEY` is valid and the API quota is not exceeded.
- **No Logs**: Ensure you are looking at the correct region (`asia-northeast3`) and the function execution has started.

---
*Last Updated: 2026-02-10*
