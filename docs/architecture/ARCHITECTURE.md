# System Architecture

## Overview
GCP News Portal is a serverless application built on Google Cloud Platform. It consists of a backend API for user interactions, and background workers for news processing and system maintenance.

## Components

### 1. User API (@backend)
- **Technology**: Python, FastAPI.
- **Function**: Handles user authentication (Firebase), keyword management, and summary retrieval.
- **Deployment**: Likely Cloud Run.

### 2. News Summarizer Worker (@news_summarizer)
- **Technology**: Python, Cloud Functions (Gen 2).
- **Function**: Processes a single (User, Keyword) tuple. Fetches news, summarizes it using AI, and stores it in Firestore.
- **Trigger**: Pub/Sub topic `gcpnewsportal/worker-news-summary`.

### 3. Trigger Function (@trigger_function)
- **Technology**: Python, Cloud Functions.
- **Function**: Periodically fetches all user keywords and publishes tasks to the `worker-news-summary` topic.
- **Trigger**: Cloud Scheduler (HTTP trigger).

### 4. Cleanup Function (@cleanup_function)
- **Technology**: Python, Cloud Functions.
- **Function**: Periodically deletes old summaries based on retention policy.
- **Trigger**: Pub/Sub topic (likely triggered by Cloud Scheduler).

## Data Store
- **Firestore**: Stores Users, Keywords (sub-collection), and Summaries (sub-collection).

## Data Flow
1. **User Action**: User adds keyword via App -> API -> Firestore.
2. **Scheduled Trigger**: Cloud Scheduler -> Trigger Function -> Fetch Keywords -> Pub/Sub (1 message per keyword).
3. **Processing**: Pub/Sub -> News Summarizer -> External News API -> AI Summarization -> Firestore.
4. **Consumption**: User opens App -> API -> Firestore (Query Summaries) -> App.
5. **Maintenance**: Cloud Scheduler -> Cleanup Function -> Firestore (Batch Delete).
