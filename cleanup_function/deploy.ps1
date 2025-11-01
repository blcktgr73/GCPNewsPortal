# Deployment script for cleanup Cloud Function (PowerShell)
# This script automates the deployment of the cleanup function to GCP

param(
    [string]$ProjectId = $env:GOOGLE_CLOUD_PROJECT,
    [string]$Region = "asia-northeast3",
    [int]$RetentionDays = 30
)

# Configuration
$FunctionName = "cleanup-old-news"
$TopicName = "cleanup-old-news-topic"
$SchedulerJobName = "cleanup-old-news-job"

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Cleanup Function Deployment Script" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

# Check if project ID is set
if ([string]::IsNullOrEmpty($ProjectId)) {
    Write-Host "Error: Project ID not provided" -ForegroundColor Red
    Write-Host "Please provide it via -ProjectId parameter or set GOOGLE_CLOUD_PROJECT environment variable" -ForegroundColor Red
    exit 1
}

Write-Host "Using GCP Project: $ProjectId" -ForegroundColor Green
Write-Host "Using Region: $Region" -ForegroundColor Green
Write-Host ""

# Step 1: Create Pub/Sub Topic
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Step 1: Creating Pub/Sub Topic" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

$topicExists = gcloud pubsub topics describe $TopicName --project=$ProjectId 2>$null
if ($LASTEXITCODE -eq 0) {
    Write-Host "Topic $TopicName already exists, skipping creation" -ForegroundColor Yellow
} else {
    gcloud pubsub topics create $TopicName --project=$ProjectId
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Created Pub/Sub topic: $TopicName" -ForegroundColor Green
    } else {
        Write-Host "✗ Failed to create Pub/Sub topic" -ForegroundColor Red
        exit 1
    }
}

Write-Host ""

# Step 2: Deploy Cloud Function
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Step 2: Deploying Cloud Function" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

gcloud functions deploy $FunctionName `
    --gen2 `
    --runtime=python311 `
    --region=$Region `
    --source=. `
    --entry-point=cleanup_old_summaries `
    --trigger-topic=$TopicName `
    --memory=256MB `
    --timeout=540s `
    --set-env-vars GOOGLE_CLOUD_PROJECT=$ProjectId `
    --project=$ProjectId

if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Deployed Cloud Function: $FunctionName" -ForegroundColor Green
} else {
    Write-Host "✗ Failed to deploy Cloud Function" -ForegroundColor Red
    exit 1
}

Write-Host ""

# Step 3: Create Cloud Scheduler Job
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Step 3: Creating Cloud Scheduler Job" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

$schedulerExists = gcloud scheduler jobs describe $SchedulerJobName --location=$Region --project=$ProjectId 2>$null
if ($LASTEXITCODE -eq 0) {
    Write-Host "Scheduler job $SchedulerJobName already exists" -ForegroundColor Yellow
    $response = Read-Host "Do you want to update it? (y/n)"
    if ($response -eq "y" -or $response -eq "Y") {
        gcloud scheduler jobs update pubsub $SchedulerJobName `
            --location=$Region `
            --schedule="0 3 1 * *" `
            --time-zone="Asia/Seoul" `
            --topic=$TopicName `
            --message-body="{`"retention_days`": $RetentionDays}" `
            --project=$ProjectId

        if ($LASTEXITCODE -eq 0) {
            Write-Host "✓ Updated Cloud Scheduler job: $SchedulerJobName" -ForegroundColor Green
        } else {
            Write-Host "✗ Failed to update Scheduler job" -ForegroundColor Red
        }
    } else {
        Write-Host "Skipping scheduler job update" -ForegroundColor Yellow
    }
} else {
    gcloud scheduler jobs create pubsub $SchedulerJobName `
        --location=$Region `
        --schedule="0 3 1 * *" `
        --time-zone="Asia/Seoul" `
        --topic=$TopicName `
        --message-body="{`"retention_days`": $RetentionDays}" `
        --project=$ProjectId

    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Created Cloud Scheduler job: $SchedulerJobName" -ForegroundColor Green
    } else {
        Write-Host "✗ Failed to create Scheduler job" -ForegroundColor Red
        exit 1
    }
}

Write-Host ""

# Step 4: Verify Permissions
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Step 4: Verifying Permissions" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

$ServiceAccount = gcloud functions describe $FunctionName `
    --region=$Region `
    --gen2 `
    --project=$ProjectId `
    --format="value(serviceConfig.serviceAccountEmail)"

Write-Host "Function service account: $ServiceAccount" -ForegroundColor Green

Write-Host "Verifying Firestore permissions..."
$hasPermission = gcloud projects get-iam-policy $ProjectId `
    --flatten="bindings[].members" `
    --filter="bindings.members:serviceAccount:$ServiceAccount AND bindings.role:roles/datastore.user" `
    --format="value(bindings.role)" 2>$null

if ($LASTEXITCODE -eq 0 -and ![string]::IsNullOrEmpty($hasPermission)) {
    Write-Host "✓ Service account has Firestore permissions" -ForegroundColor Green
} else {
    Write-Host "Warning: Service account may not have Firestore permissions" -ForegroundColor Yellow
    $response = Read-Host "Do you want to grant roles/datastore.user now? (y/n)"
    if ($response -eq "y" -or $response -eq "Y") {
        gcloud projects add-iam-policy-binding $ProjectId `
            --member="serviceAccount:$ServiceAccount" `
            --role="roles/datastore.user"

        if ($LASTEXITCODE -eq 0) {
            Write-Host "✓ Granted Firestore permissions" -ForegroundColor Green
        } else {
            Write-Host "✗ Failed to grant permissions" -ForegroundColor Red
        }
    }
}

Write-Host ""

# Step 5: Summary
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Deployment Complete!" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Resources created/updated:" -ForegroundColor White
Write-Host "  - Pub/Sub Topic: $TopicName" -ForegroundColor White
Write-Host "  - Cloud Function: $FunctionName" -ForegroundColor White
Write-Host "  - Scheduler Job: $SchedulerJobName" -ForegroundColor White
Write-Host ""
Write-Host "Configuration:" -ForegroundColor White
Write-Host "  - Region: $Region" -ForegroundColor White
Write-Host "  - Schedule: 1st of month at 3 AM KST (0 3 1 * *)" -ForegroundColor White
Write-Host "  - Retention Period: $RetentionDays days" -ForegroundColor White
Write-Host "  - Memory: 256MB" -ForegroundColor White
Write-Host "  - Timeout: 540s (9 minutes)" -ForegroundColor White
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  1. Test the function manually:" -ForegroundColor White
Write-Host "     gcloud scheduler jobs run $SchedulerJobName --location=$Region" -ForegroundColor Cyan
Write-Host ""
Write-Host "  2. View logs:" -ForegroundColor White
Write-Host "     gcloud functions logs read $FunctionName --region=$Region --gen2 --limit=50" -ForegroundColor Cyan
Write-Host ""
Write-Host "  3. Monitor execution:" -ForegroundColor White
Write-Host "     Check Cloud Logging console for detailed logs" -ForegroundColor White
Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
