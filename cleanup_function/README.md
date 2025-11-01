# Cleanup Function - Automated News Summary Cleanup

This Cloud Function automatically deletes old news summaries from Firestore based on a configurable retention period. It is designed to run on a scheduled basis using Cloud Scheduler and Pub/Sub.

## Overview

- **Purpose**: Remove news summaries older than a configurable retention period (default: 30 days)
- **Trigger**: Cloud Scheduler via Pub/Sub (scheduled monthly on the 1st at 3 AM KST)
- **Runtime**: Python 3.11 on Cloud Functions Gen 2
- **Region**: asia-northeast3 (Seoul)

## 🚀 Quick Start

### Already Deployed? (After running deploy script)

**⚠️ IMPORTANT: Create Firestore Index First**

The function requires a Firestore composite index to work. Create it now:

**Option 1: Automatic (Easiest)**
```bash
# Trigger the function (it will fail but show index creation link)
gcloud scheduler jobs run cleanup-old-news-job --location=asia-northeast3

# Wait 30 seconds
sleep 30

# Check logs for index creation URL
gcloud logging read "resource.type=cloud_function resource.labels.function_name=cleanup-old-news" --limit=100 --freshness=5m
```

Look for a URL like: `https://console.firebase.google.com/project/.../firestore/indexes?create_composite=...`

**Option 2: Manual**
1. Go to: https://console.cloud.google.com/firestore/indexes
2. Click "Create Index"
3. Settings:
   - Collection ID: `summaries`
   - Query scope: `Collection group`
   - Field: `created_at` (Ascending)
4. Wait 5-10 minutes for index to build

**Then test:**
```bash
gcloud scheduler jobs run cleanup-old-news-job --location=asia-northeast3
# Wait 30 seconds, then check logs
gcloud functions logs read cleanup-old-news --region=asia-northeast3 --gen2 --limit=50
```

## Architecture

```
Cloud Scheduler (cron: 0 3 1 * *)
    |
    v
Pub/Sub Topic (cleanup-old-news-topic)
    |
    v
Cloud Function (cleanup-old-news)
    |
    v
Firestore (users/{uid}/summaries/{doc_id})
```

## Files

- `main.py` - Cloud Function implementation with cleanup logic
- `requirements.txt` - Python dependencies
- `.gcloudignore` - Files to exclude from deployment
- `test_local.py` - Local testing utilities
- `README.md` - This documentation

## Key Features

### Clean Code Architecture

The implementation follows SOLID principles and clean code practices:

1. **Single Responsibility Principle**: Each function has one clear purpose
   - `parse_pubsub_message()` - Only parses and validates messages
   - `calculate_cutoff_date()` - Only calculates dates
   - `delete_old_summaries_for_user()` - Only handles user-specific deletion
   - `cleanup_old_summaries()` - Orchestrates the cleanup workflow

2. **Dependency Inversion**: Functions depend on abstractions (Firestore client) not concrete implementations

3. **Error Handling**: Comprehensive error handling with graceful degradation
   - Per-user failures don't stop processing other users
   - Invalid configurations fall back to safe defaults
   - All errors logged with appropriate severity levels

4. **Comprehensive Logging**: Structured logging at INFO, WARNING, and ERROR levels

### Configuration

- **Default Retention**: 30 days
- **Min Retention**: 7 days
- **Max Retention**: 365 days
- **Batch Size**: 500 documents (Firestore limit)

### Performance

- **Target**: <5 minutes for 100 users
- **Timeout**: 540 seconds (9 minutes)
- **Memory**: 256 MB (configurable)

## Deployment

### Prerequisites

1. GCP project with billing enabled
2. APIs enabled:
   - Cloud Functions API
   - Cloud Scheduler API
   - Cloud Pub/Sub API
   - Cloud Firestore API

3. Service account with `roles/datastore.user` role

### Step 1: Create Pub/Sub Topic

```bash
gcloud pubsub topics create cleanup-old-news-topic \
  --project=YOUR_PROJECT_ID
```

### Step 2: Deploy Cloud Function

```bash
cd cleanup_function

gcloud functions deploy cleanup-old-news \
  --gen2 \
  --runtime=python311 \
  --region=asia-northeast3 \
  --source=. \
  --entry-point=cleanup_old_summaries \
  --trigger-topic=cleanup-old-news-topic \
  --memory=256MB \
  --timeout=540s \
  --set-env-vars GOOGLE_CLOUD_PROJECT=YOUR_PROJECT_ID
```

### Step 3: Create Cloud Scheduler Job

```bash
gcloud scheduler jobs create pubsub cleanup-old-news-job \
  --location=asia-northeast3 \
  --schedule="0 3 1 * *" \
  --time-zone="Asia/Seoul" \
  --topic=cleanup-old-news-topic \
  --message-body='{"retention_days": 30}'
```

## Testing

### Local Testing

1. Install dependencies:
```bash
pip install -r requirements.txt
pip install functions-framework
```

2. Set environment variables:
```bash
export GOOGLE_APPLICATION_CREDENTIALS="path/to/service-account-key.json"
export GOOGLE_CLOUD_PROJECT="your-project-id"
```

3. Run tests:
```bash
# Unit tests only (no Firestore access required)
python test_local.py unit

# Safe integration test (no data deletion)
python test_local.py safe

# Full integration test (may delete data!)
python test_local.py full
```

### Manual Trigger (After Deployment)

```bash
# Trigger via Scheduler
gcloud scheduler jobs run cleanup-old-news-job \
  --location=asia-northeast3

# Or trigger via Pub/Sub directly
gcloud pubsub topics publish cleanup-old-news-topic \
  --message='{"retention_days": 30}'
```

### View Logs

```bash
gcloud functions logs read cleanup-old-news \
  --region=asia-northeast3 \
  --gen2 \
  --limit=50
```

## Configuration Management

### Change Retention Period

```bash
gcloud scheduler jobs update pubsub cleanup-old-news-job \
  --location=asia-northeast3 \
  --message-body='{"retention_days": 60}'
```

### Change Schedule

```bash
# Change to weekly execution (every Sunday at 3 AM)
gcloud scheduler jobs update pubsub cleanup-old-news-job \
  --location=asia-northeast3 \
  --schedule="0 3 * * 0"
```

### Update Function Resources

```bash
gcloud functions deploy cleanup-old-news \
  --gen2 \
  --region=asia-northeast3 \
  --memory=512MB \
  --timeout=600s
```

## Monitoring

### Cloud Logging Queries

**View successful executions:**
```
resource.type="cloud_function"
resource.labels.function_name="cleanup-old-news"
jsonPayload.message=~"Cleanup job completed"
```

**View errors:**
```
resource.type="cloud_function"
resource.labels.function_name="cleanup-old-news"
severity>=ERROR
```

**View deletion statistics:**
```
resource.type="cloud_function"
resource.labels.function_name="cleanup-old-news"
jsonPayload.message=~"total_deleted"
```

### Expected Output

Successful execution produces logs like:
```
INFO: ============================================================
INFO: Cleanup job started
INFO: Execution timestamp: 2025-11-01T18:00:00.000000
INFO: ============================================================
INFO: Using retention period from message: 30 days
INFO: Calculated cutoff date: 2025-10-02T18:00:00.000000 (retention: 30 days)
INFO: Firestore client initialized successfully
INFO: Processing user 1: user123
INFO: User user123: Deleted 42 old summaries
INFO: ============================================================
INFO: Cleanup job completed successfully
INFO: ============================================================
INFO: Execution Summary:
INFO:   - Total users processed: 10
INFO:   - Users with deletions: 8
INFO:   - Total documents deleted: 245
INFO:   - Cutoff date: 2025-10-02T18:00:00.000000
INFO:   - Retention period: 30 days
INFO:   - Execution time: 42.50 seconds
INFO: ============================================================
```

## Troubleshooting

### Function Not Executing

1. Check Scheduler job status:
```bash
gcloud scheduler jobs describe cleanup-old-news-job \
  --location=asia-northeast3
```

2. Check Pub/Sub topic exists:
```bash
gcloud pubsub topics list
```

3. Check function deployment:
```bash
gcloud functions describe cleanup-old-news \
  --region=asia-northeast3 \
  --gen2
```

### Permission Errors

Grant Firestore permissions to the function's service account:

```bash
# Get service account
gcloud functions describe cleanup-old-news \
  --region=asia-northeast3 \
  --gen2 \
  --format="value(serviceConfig.serviceAccountEmail)"

# Grant permissions
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
  --member="serviceAccount:SERVICE_ACCOUNT_EMAIL" \
  --role="roles/datastore.user"
```

### Timeout Issues

If the function times out:

1. Increase timeout:
```bash
gcloud functions deploy cleanup-old-news \
  --gen2 \
  --region=asia-northeast3 \
  --timeout=600s
```

2. Increase memory:
```bash
gcloud functions deploy cleanup-old-news \
  --gen2 \
  --region=asia-northeast3 \
  --memory=512MB
```

## Rollback

To remove all cleanup infrastructure:

```bash
# Delete Cloud Function
gcloud functions delete cleanup-old-news \
  --region=asia-northeast3 \
  --gen2

# Delete Scheduler Job
gcloud scheduler jobs delete cleanup-old-news-job \
  --location=asia-northeast3

# Delete Pub/Sub Topic
gcloud pubsub topics delete cleanup-old-news-topic
```

## Cost Estimation

For 100 users with monthly execution:

| Service | Monthly Cost |
|---------|--------------|
| Cloud Scheduler | $0.10 |
| Pub/Sub | ~$0.00 (free tier) |
| Cloud Functions | ~$0.00 (free tier) |
| Firestore Operations | ~$0.01 |
| **Total** | **~$0.11/month** |

## Related Documentation

### In cleanup_function/docs/
- [QA Test Report](./docs/QA_TEST_REPORT.md) - Comprehensive QA testing results
- [QA Summary](./docs/QA_SUMMARY.md) - Quick QA overview
- [Implementation Summary](./docs/IMPLEMENTATION_SUMMARY.md) - Technical implementation details

### In .docs/ (project root)
- [Implementation Guide](../.docs/cleanup-implementation-guide.md) - Step-by-step deployment guide
- [Product Specification](../.docs/cleanup-product-specification.md) - Complete product spec
- [Technical Design](../.docs/cleanup-technical-design.md) - Detailed technical design
- [Architecture Overview](../.docs/cleanup-automation-overview.md) - System overview

## Support

For issues or questions:
1. Check logs using `gcloud functions logs read`
2. Review this troubleshooting section
3. Consult the implementation guide
4. Contact GCP Support if needed
