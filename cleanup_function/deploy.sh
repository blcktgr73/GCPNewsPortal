#!/bin/bash

# Deployment script for cleanup Cloud Function
# This script automates the deployment of the cleanup function to GCP

set -e  # Exit on error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ID="${GOOGLE_CLOUD_PROJECT:-}"
REGION="asia-northeast3"
FUNCTION_NAME="cleanup-old-news"
TOPIC_NAME="cleanup-old-news-topic"
SCHEDULER_JOB_NAME="cleanup-old-news-job"
RETENTION_DAYS="30"

echo "============================================================"
echo "Cleanup Function Deployment Script"
echo "============================================================"

# Check if project ID is set
if [ -z "$PROJECT_ID" ]; then
    echo -e "${RED}Error: GOOGLE_CLOUD_PROJECT environment variable not set${NC}"
    echo "Please set it with: export GOOGLE_CLOUD_PROJECT=your-project-id"
    exit 1
fi

echo -e "${GREEN}Using GCP Project: $PROJECT_ID${NC}"
echo -e "${GREEN}Using Region: $REGION${NC}"
echo ""

# Function to check if command succeeded
check_status() {
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ $1${NC}"
    else
        echo -e "${RED}✗ $1 failed${NC}"
        exit 1
    fi
}

# Step 1: Create Pub/Sub Topic
echo "============================================================"
echo "Step 1: Creating Pub/Sub Topic"
echo "============================================================"

# Check if topic already exists
if gcloud pubsub topics describe $TOPIC_NAME --project=$PROJECT_ID &>/dev/null; then
    echo -e "${YELLOW}Topic $TOPIC_NAME already exists, skipping creation${NC}"
else
    gcloud pubsub topics create $TOPIC_NAME \
        --project=$PROJECT_ID
    check_status "Created Pub/Sub topic: $TOPIC_NAME"
fi

echo ""

# Step 2: Deploy Cloud Function
echo "============================================================"
echo "Step 2: Deploying Cloud Function"
echo "============================================================"

gcloud functions deploy $FUNCTION_NAME \
    --gen2 \
    --runtime=python311 \
    --region=$REGION \
    --source=. \
    --entry-point=cleanup_old_summaries \
    --trigger-topic=$TOPIC_NAME \
    --memory=256MB \
    --timeout=540s \
    --set-env-vars GOOGLE_CLOUD_PROJECT=$PROJECT_ID \
    --project=$PROJECT_ID

check_status "Deployed Cloud Function: $FUNCTION_NAME"

echo ""

# Step 3: Create Cloud Scheduler Job
echo "============================================================"
echo "Step 3: Creating Cloud Scheduler Job"
echo "============================================================"

# Check if scheduler job already exists
if gcloud scheduler jobs describe $SCHEDULER_JOB_NAME --location=$REGION --project=$PROJECT_ID &>/dev/null; then
    echo -e "${YELLOW}Scheduler job $SCHEDULER_JOB_NAME already exists${NC}"
    read -p "Do you want to update it? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        gcloud scheduler jobs update pubsub $SCHEDULER_JOB_NAME \
            --location=$REGION \
            --schedule="0 3 1 * *" \
            --time-zone="Asia/Seoul" \
            --topic=$TOPIC_NAME \
            --message-body="{\"retention_days\": $RETENTION_DAYS}" \
            --project=$PROJECT_ID
        check_status "Updated Cloud Scheduler job: $SCHEDULER_JOB_NAME"
    else
        echo "Skipping scheduler job update"
    fi
else
    gcloud scheduler jobs create pubsub $SCHEDULER_JOB_NAME \
        --location=$REGION \
        --schedule="0 3 1 * *" \
        --time-zone="Asia/Seoul" \
        --topic=$TOPIC_NAME \
        --message-body="{\"retention_days\": $RETENTION_DAYS}" \
        --project=$PROJECT_ID
    check_status "Created Cloud Scheduler job: $SCHEDULER_JOB_NAME"
fi

echo ""

# Step 4: Grant Permissions
echo "============================================================"
echo "Step 4: Verifying Permissions"
echo "============================================================"

# Get service account email
SERVICE_ACCOUNT=$(gcloud functions describe $FUNCTION_NAME \
    --region=$REGION \
    --gen2 \
    --project=$PROJECT_ID \
    --format="value(serviceConfig.serviceAccountEmail)")

echo -e "${GREEN}Function service account: $SERVICE_ACCOUNT${NC}"

# Check if service account has necessary permissions
echo "Verifying Firestore permissions..."
gcloud projects get-iam-policy $PROJECT_ID \
    --flatten="bindings[].members" \
    --filter="bindings.members:serviceAccount:$SERVICE_ACCOUNT AND bindings.role:roles/datastore.user" \
    --format="value(bindings.role)" &>/dev/null

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Service account has Firestore permissions${NC}"
else
    echo -e "${YELLOW}Warning: Service account may not have Firestore permissions${NC}"
    read -p "Do you want to grant roles/datastore.user now? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        gcloud projects add-iam-policy-binding $PROJECT_ID \
            --member="serviceAccount:$SERVICE_ACCOUNT" \
            --role="roles/datastore.user"
        check_status "Granted Firestore permissions"
    fi
fi

echo ""

# Step 5: Summary
echo "============================================================"
echo "Deployment Complete!"
echo "============================================================"
echo ""
echo "Resources created/updated:"
echo "  - Pub/Sub Topic: $TOPIC_NAME"
echo "  - Cloud Function: $FUNCTION_NAME"
echo "  - Scheduler Job: $SCHEDULER_JOB_NAME"
echo ""
echo "Configuration:"
echo "  - Region: $REGION"
echo "  - Schedule: 1st of month at 3 AM KST (0 3 1 * *)"
echo "  - Retention Period: $RETENTION_DAYS days"
echo "  - Memory: 256MB"
echo "  - Timeout: 540s (9 minutes)"
echo ""
echo "Next steps:"
echo "  1. Test the function manually:"
echo "     gcloud scheduler jobs run $SCHEDULER_JOB_NAME --location=$REGION"
echo ""
echo "  2. View logs:"
echo "     gcloud functions logs read $FUNCTION_NAME --region=$REGION --gen2 --limit=50"
echo ""
echo "  3. Monitor execution:"
echo "     Check Cloud Logging console for detailed logs"
echo ""
echo "============================================================"
