#!/usr/bin/env bash

# Non-interactive, idempotent deployment for GitHub Actions.
set -euo pipefail

PROJECT_ID="${GOOGLE_CLOUD_PROJECT:?GOOGLE_CLOUD_PROJECT is required}"
REGION="${REGION:-asia-northeast3}"
FUNCTION_NAME="cleanup-old-news"
TOPIC_NAME="cleanup-old-news-topic"
SCHEDULER_JOB_NAME="cleanup-old-news-job"

if ! gcloud pubsub topics describe "$TOPIC_NAME" --project="$PROJECT_ID" >/dev/null 2>&1; then
  gcloud pubsub topics create "$TOPIC_NAME" --project="$PROJECT_ID" --quiet
fi

gcloud functions deploy "$FUNCTION_NAME" \
  --gen2 \
  --runtime=python311 \
  --region="$REGION" \
  --source="cleanup_function" \
  --entry-point=cleanup_old_summaries \
  --trigger-topic="$TOPIC_NAME" \
  --memory=256MB \
  --timeout=540s \
  --set-env-vars="GOOGLE_CLOUD_PROJECT=$PROJECT_ID" \
  --project="$PROJECT_ID" \
  --quiet

SCHEDULER_ARGS=(
  --location="$REGION"
  --schedule="0 3 1 * *"
  --time-zone="Asia/Seoul"
  --topic="projects/$PROJECT_ID/topics/$TOPIC_NAME"
  --message-body='{"retention_days":30}'
  --project="$PROJECT_ID"
  --quiet
)

if gcloud scheduler jobs describe "$SCHEDULER_JOB_NAME" \
  --location="$REGION" --project="$PROJECT_ID" >/dev/null 2>&1; then
  gcloud scheduler jobs update pubsub "$SCHEDULER_JOB_NAME" "${SCHEDULER_ARGS[@]}"
else
  gcloud scheduler jobs create pubsub "$SCHEDULER_JOB_NAME" "${SCHEDULER_ARGS[@]}"
fi
