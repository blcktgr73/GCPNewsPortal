# Product Specification: Automated News Cleanup System

## Document Information

**Product Name**: Automated News Data Cleanup System
**Version**: 1.0
**Date**: 2025-11-01
**Product Owner**: [To be assigned]
**Technical Lead**: [To be assigned]
**Status**: Draft for Review

---

## Executive Summary

This document defines the product specification for implementing an automated cleanup system that removes old news summaries from the GCP News Portal application. The system will run as a scheduled background job using GCP Cloud Functions to maintain data hygiene and optimize storage costs without impacting user experience.

**Key Objectives**:
- Automatically delete news summaries older than 30 days (configurable)
- Execute monthly on a scheduled basis (1st day of month at 3 AM KST)
- Process all users transparently without service disruption
- Maintain data quality and system performance

---

## 1. Product Vision & Business Context

### 1.1 Vision Statement

Create a reliable, cost-effective automated data lifecycle management system that maintains optimal database size and query performance by removing outdated news summaries while preserving data integrity and user trust.

### 1.2 Business Drivers

**Primary Drivers**:
- **Cost Optimization**: Reduce Firestore storage and read operation costs by maintaining only relevant data
- **Performance**: Improve query response times by limiting dataset size
- **Data Management**: Establish systematic data retention policies
- **Scalability**: Enable the platform to scale to thousands of users without degrading performance

**Supporting Drivers**:
- **Compliance**: Prepare infrastructure for potential data retention regulations
- **User Experience**: Faster data retrieval through smaller result sets
- **Operational Excellence**: Reduce manual database maintenance overhead

### 1.3 Success Metrics

| Metric | Target | Measurement Method |
|--------|--------|-------------------|
| **Data Retention Compliance** | 100% of summaries > 30 days deleted | Monthly audit query |
| **System Reliability** | 99.5% successful monthly executions | Cloud Function execution logs |
| **Zero User Impact** | 0 user-reported issues related to cleanup | Support ticket tracking |
| **Cost Reduction** | 15-30% reduction in Firestore costs | GCP billing reports (3-month trend) |
| **Performance Improvement** | <10% improvement in /summaries endpoint response time | API monitoring (p95 latency) |
| **Execution Time** | Cleanup completes within 5 minutes (for 100 users) | Cloud Function duration metrics |

---

## 2. User Stories & Acceptance Criteria

### Epic: Automated Data Lifecycle Management

#### Story 2.1: Scheduled Data Cleanup Execution

**As a** system administrator
**I want** the cleanup system to run automatically on a schedule
**So that** I don't need to manually manage old data

**Acceptance Criteria**:
- [ ] Cloud Scheduler job triggers on 1st day of each month at 3:00 AM KST
- [ ] Pub/Sub message successfully delivered to cleanup function
- [ ] Function executes within scheduled time window (3:00-3:15 AM)
- [ ] Execution completes within timeout period (9 minutes)
- [ ] Scheduler status shows "success" after execution
- [ ] No manual intervention required for normal operation

**Priority**: P0 (Must Have)
**Effort**: Medium (5 story points)

---

#### Story 2.2: Old Summary Deletion

**As a** data steward
**I want** summaries older than 30 days to be automatically deleted
**So that** only relevant news data is retained

**Acceptance Criteria**:
- [ ] All summaries with `created_at < (current_date - 30 days)` are deleted
- [ ] Deletion applies to all users in the system
- [ ] Only summaries are deleted (user documents remain intact)
- [ ] Firestore batch operations used for efficient deletion (max 500 per batch)
- [ ] Deletion is permanent (no soft delete)
- [ ] Query uses proper Firestore index on `created_at` field

**Priority**: P0 (Must Have)
**Effort**: Medium (5 story points)

**Technical Notes**:
- Use `datetime.utcnow() - timedelta(days=30)` for cutoff calculation
- Use ISO 8601 format comparison: `created_at < cutoff_iso`
- Firestore query: `where('created_at', '<', cutoff_iso)`

---

#### Story 2.3: Configurable Retention Period

**As a** system administrator
**I want** to configure the retention period via Pub/Sub message
**So that** I can adjust data retention without redeploying code

**Acceptance Criteria**:
- [ ] Retention period configurable via Pub/Sub message JSON: `{"retention_days": N}`
- [ ] Default value of 30 days used if no configuration provided
- [ ] Valid range: 7 to 365 days
- [ ] Configuration parsed from base64-encoded Pub/Sub data
- [ ] Invalid configurations logged and default used
- [ ] Cloud Scheduler job message body editable via gcloud command

**Priority**: P1 (Should Have)
**Effort**: Small (2 story points)

---

#### Story 2.4: Comprehensive Logging

**As a** DevOps engineer
**I want** detailed logs of cleanup operations
**So that** I can monitor and audit system behavior

**Acceptance Criteria**:
- [ ] Log cleanup job start with timestamp
- [ ] Log retention period and cutoff date
- [ ] Log each user processed with user_id
- [ ] Log deletion count per user
- [ ] Log total deletions across all users
- [ ] Log completion status (success/failure)
- [ ] Log any errors with stack traces
- [ ] All logs visible in Cloud Logging within 1 minute
- [ ] Logs retained for 30 days minimum

**Log Levels**:
- INFO: Normal operations, start/end, summary statistics
- WARNING: Parsing errors, missing fields
- ERROR: Firestore failures, timeout issues

**Priority**: P0 (Must Have)
**Effort**: Small (2 story points)

---

#### Story 2.5: Error Handling & Recovery

**As a** reliability engineer
**I want** the system to handle errors gracefully
**So that** partial failures don't corrupt data or stop processing

**Acceptance Criteria**:
- [ ] Function continues processing remaining users if one user fails
- [ ] Firestore transient errors trigger automatic retry (up to 3 attempts)
- [ ] Timeout errors logged with details of last processed user
- [ ] Function returns structured error response with error type and message
- [ ] Partial success scenarios logged clearly (e.g., "90/100 users processed")
- [ ] No data corruption occurs during error scenarios
- [ ] Next scheduled run attempts cleanup again (idempotent operation)

**Priority**: P0 (Must Have)
**Effort**: Medium (3 story points)

---

#### Story 2.6: Manual Trigger Capability

**As a** system administrator
**I want** to manually trigger cleanup on-demand
**So that** I can perform cleanup outside the schedule if needed

**Acceptance Criteria**:
- [ ] Cleanup triggerable via `gcloud scheduler jobs run` command
- [ ] Cleanup triggerable via `gcloud pubsub topics publish` command
- [ ] Manual trigger accepts custom retention_days parameter
- [ ] Manual trigger logged distinctly from scheduled runs
- [ ] Multiple concurrent executions prevented (Pub/Sub deduplication)
- [ ] Manual trigger completes within same timeout as scheduled runs

**Priority**: P1 (Should Have)
**Effort**: Small (1 story point)

---

#### Story 2.7: Monitoring & Alerting

**As a** DevOps engineer
**I want** alerts when cleanup fails
**So that** I can respond to issues quickly

**Acceptance Criteria**:
- [ ] Alert triggered if cleanup execution fails
- [ ] Alert triggered if execution exceeds expected duration (>8 minutes)
- [ ] Alert includes error details and affected time window
- [ ] Alert sent via configured notification channel (email/Slack)
- [ ] Cloud Logging queries available for common debugging scenarios
- [ ] Cloud Monitoring dashboard shows cleanup metrics

**Priority**: P2 (Nice to Have)
**Effort**: Medium (3 story points)

---

## 3. Functional Requirements

### 3.1 Core Functionality

**FR-001: Scheduled Execution**
- Cloud Scheduler job triggers Pub/Sub topic monthly (cron: `0 3 1 * *`)
- Timezone: Asia/Seoul (KST)
- Pub/Sub topic: `cleanup-old-news-topic`
- Message format: JSON with optional `retention_days` parameter

**FR-002: Data Deletion Logic**
- Query all user documents from `users` collection
- For each user, query subcollection `summaries` where `created_at < cutoff_date`
- Delete matching documents using Firestore batch operations
- Batch size limit: 500 documents per commit
- Cutoff date calculation: `UTC_NOW - retention_days`

**FR-003: Configuration Management**
- Default retention period: 30 days
- Configurable via Pub/Sub message: `{"retention_days": <integer>}`
- Valid range: 7-365 days
- Configuration validation with fallback to default

**FR-004: Logging & Telemetry**
- Log level: INFO for normal operations, ERROR for failures
- Required log fields:
  - Execution timestamp
  - Retention period used
  - Cutoff date (ISO 8601)
  - Users processed count
  - Users with deletions count
  - Total documents deleted
  - Execution duration
  - Error messages (if any)

**FR-005: Error Handling**
- Graceful degradation: continue processing on per-user failures
- Automatic retry on Firestore transient errors
- Timeout handling: 540 seconds (9 minutes)
- Return structured response with status and metrics

### 3.2 Data Model

**Firestore Structure**:
```
users/{user_id}/summaries/{summary_id}
  - title: string
  - url: string
  - summary: string
  - keyword: string
  - created_at: string (ISO 8601, e.g., "2025-10-15T12:30:00.000000")
  - summaryTokens: number
```

**Deletion Query**:
```python
db.collection('users')
  .document(user_id)
  .collection('summaries')
  .where('created_at', '<', cutoff_iso)
  .stream()
```

**Index Requirement**:
- Collection: `summaries`
- Field: `created_at` (Ascending)
- Scope: Collection group (applies to all users)

### 3.3 Integration Points

| System | Integration Type | Purpose |
|--------|-----------------|---------|
| Cloud Scheduler | Trigger | Initiates cleanup job monthly |
| Pub/Sub | Message Queue | Decouples scheduler from function |
| Cloud Functions | Execution | Runs cleanup logic |
| Firestore | Database | Queries and deletes old summaries |
| Cloud Logging | Observability | Stores execution logs |
| Cloud Monitoring | Alerting | Monitors execution health |

---

## 4. Non-Functional Requirements

### 4.1 Performance

**NFR-001: Execution Time**
- Target: Complete within 5 minutes for 100 users
- Maximum: 9 minutes (hard timeout)
- Scalability: Linear time complexity O(n) where n = total documents

**NFR-002: Resource Utilization**
- Memory allocation: 256 MB (expandable to 512 MB if needed)
- CPU: 1 vCPU (Cloud Functions default)
- Network: Minimal (Firestore API calls only)

**NFR-003: Query Performance**
- Firestore composite index required on `created_at` field
- Index creation time: <24 hours (automatic)
- Query response time: <100ms per user (with index)

### 4.2 Reliability

**NFR-004: Availability**
- Target: 99.5% successful monthly executions (11/12 months successful)
- Recovery: Automatic retry on transient failures
- Idempotency: Safe to run multiple times without side effects

**NFR-005: Data Integrity**
- No data corruption during cleanup
- Atomic batch operations (all-or-nothing per batch)
- User documents never deleted
- Only `summaries` subcollection affected

**NFR-006: Fault Tolerance**
- Single user failure does not stop processing other users
- Partial completion acceptable (logged and reported)
- Next execution attempts remaining deletions

### 4.3 Security

**NFR-007: Authentication**
- Cloud Functions authenticated via GCP IAM
- Service account-based execution
- No public HTTP endpoint

**NFR-008: Authorization**
- Function service account requires `roles/datastore.user` role
- Principle of least privilege
- Scoped to project Firestore database

**NFR-009: Audit Trail**
- All deletions logged to Cloud Logging
- Logs retained for 30 days minimum
- Immutable log records (no deletion possible)

### 4.4 Maintainability

**NFR-010: Code Quality**
- Python 3.11 runtime
- Type hints for function signatures
- Docstrings for public functions
- Error handling with specific exception types

**NFR-011: Deployment**
- Infrastructure-as-Code: gcloud CLI commands documented
- Repeatable deployment process
- Version-controlled source code
- Rollback capability (function versioning)

**NFR-012: Observability**
- Structured logging (JSON format)
- Key metrics exposed in logs (parseable)
- Cloud Logging queries documented
- Monitoring dashboard templates provided

### 4.5 Scalability

**NFR-013: User Growth**
- Support 1,000 users without timeout (within 9 minutes)
- Batch processing prevents memory overflow
- Horizontal scaling via multiple function instances (if needed)

**NFR-014: Data Volume**
- Support up to 100,000 summaries per user (theoretical limit)
- Firestore batch size: 500 documents (optimal)
- Memory-efficient iteration (streaming queries)

### 4.6 Cost Efficiency

**NFR-015: Resource Optimization**
- Execution time minimized via batch operations
- Memory allocation: 256 MB (increase only if necessary)
- Monthly execution only (not daily)
- Cold start acceptable (non-latency-sensitive)

**NFR-016: Firestore Optimization**
- Use indexed queries only
- Minimize read operations (query filters on server)
- Batch deletes reduce write operation count

---

## 5. Edge Cases & Error Scenarios

### 5.1 Data Edge Cases

**EC-001: Missing `created_at` Field**
- **Scenario**: Summary document lacks `created_at` field
- **Behavior**: Document skipped (not deleted)
- **Logging**: WARNING log with document ID
- **Mitigation**: Data validation on summary creation (separate story)

**EC-002: Invalid `created_at` Format**
- **Scenario**: `created_at` is not ISO 8601 format
- **Behavior**: Query may not match (depends on format)
- **Logging**: WARNING if parsing fails
- **Mitigation**: Strict validation on write path

**EC-003: Future `created_at` Date**
- **Scenario**: Document has `created_at` in the future (clock skew)
- **Behavior**: Document not deleted (correct behavior)
- **Logging**: No special logging (expected case)
- **Mitigation**: None required

**EC-004: Empty Summaries Collection**
- **Scenario**: User has no summaries
- **Behavior**: No deletions, processing continues
- **Logging**: INFO log "User {user_id}: no old summaries"
- **Mitigation**: None required (normal case)

**EC-005: No Users Exist**
- **Scenario**: `users` collection is empty
- **Behavior**: Function completes successfully with 0 deletions
- **Logging**: INFO log "No users found"
- **Mitigation**: None required

### 5.2 System Edge Cases

**EC-006: Function Timeout**
- **Scenario**: Processing exceeds 9-minute timeout
- **Behavior**: Function terminated by runtime
- **Logging**: ERROR log with last processed user
- **Recovery**: Next scheduled run processes remaining data
- **Mitigation**: Increase timeout or implement pagination

**EC-007: Firestore Rate Limit**
- **Scenario**: Deletion rate exceeds Firestore quotas
- **Behavior**: Firestore returns 429 error
- **Logging**: ERROR log with retry information
- **Recovery**: Automatic retry with exponential backoff
- **Mitigation**: Firestore quotas typically sufficient for monthly runs

**EC-008: Pub/Sub Message Duplication**
- **Scenario**: Pub/Sub delivers message multiple times
- **Behavior**: Multiple function executions
- **Impact**: Idempotent operation (no harm, extra cost)
- **Mitigation**: Pub/Sub message deduplication (best effort)

**EC-009: Scheduler Job Failure**
- **Scenario**: Cloud Scheduler fails to publish message
- **Behavior**: Cleanup does not run
- **Logging**: Scheduler logs show failure
- **Recovery**: Manual trigger or wait for next month
- **Mitigation**: Monitoring alert configured

**EC-010: Service Account Permission Denied**
- **Scenario**: Function lacks Firestore permissions
- **Behavior**: Function fails immediately
- **Logging**: ERROR log with permission error
- **Recovery**: Grant `roles/datastore.user` to service account
- **Mitigation**: Permission validation during deployment

### 5.3 Configuration Edge Cases

**EC-011: Invalid Retention Days (Too Low)**
- **Scenario**: `retention_days < 7`
- **Behavior**: Use default value (30 days)
- **Logging**: WARNING log with provided value
- **Mitigation**: Configuration validation

**EC-012: Invalid Retention Days (Too High)**
- **Scenario**: `retention_days > 365`
- **Behavior**: Use default value (30 days)
- **Logging**: WARNING log with provided value
- **Mitigation**: Configuration validation

**EC-013: Malformed JSON Message**
- **Scenario**: Pub/Sub message is not valid JSON
- **Behavior**: Use default value (30 days)
- **Logging**: WARNING log with parse error
- **Mitigation**: JSON validation on message creation

**EC-014: Empty Pub/Sub Message**
- **Scenario**: Pub/Sub message has no data
- **Behavior**: Use default value (30 days)
- **Logging**: INFO log "Using default retention"
- **Mitigation**: None required (expected case)

### 5.4 Concurrency Edge Cases

**EC-015: Multiple Manual Triggers**
- **Scenario**: Admin triggers cleanup multiple times simultaneously
- **Behavior**: Multiple function instances execute
- **Impact**: Idempotent (safe but wasteful)
- **Logging**: Multiple execution logs with timestamps
- **Mitigation**: Documentation warning against concurrent execution

**EC-016: Cleanup During User Activity**
- **Scenario**: User creates summary while cleanup runs
- **Behavior**: New summary not deleted (created_at is recent)
- **Impact**: No user impact
- **Mitigation**: None required (correct behavior)

---

## 6. Scope & Boundaries

### 6.1 In Scope

- Automated deletion of news summaries older than configurable retention period
- Scheduled monthly execution via Cloud Scheduler
- Processing all users in the Firestore `users` collection
- Comprehensive logging of cleanup operations
- Error handling and graceful degradation
- Manual trigger capability for on-demand cleanup
- Configuration via Pub/Sub message
- Deployment documentation and scripts

### 6.2 Out of Scope

**Phase 1 (Current Release)**:
- User notification of deleted summaries (no user-facing feature)
- Soft delete or archival (permanent deletion only)
- Cleanup of other collections (keywords, user metadata, etc.)
- Per-user retention policies (global policy only)
- Backup before deletion
- Web UI for configuration management
- Real-time cleanup (scheduled only, not continuous)
- Cleanup of duplicate summaries (separate feature)
- Analytics on deleted data

**Future Considerations**:
- User-configurable retention preferences (per-user settings)
- Soft delete with recovery window (30-day trash)
- Automated backup before deletion
- Analytics dashboard showing deletion trends
- Cloud Storage archival of old summaries before deletion
- More granular scheduling (weekly, daily options)
- Cleanup of orphaned data (keywords without summaries)

### 6.3 Dependencies

**External Dependencies**:
- GCP Cloud Functions Gen 2 availability in `asia-northeast3`
- GCP Cloud Scheduler availability in `asia-northeast3`
- GCP Pub/Sub service
- Firestore database operational
- Service account with appropriate IAM roles

**Internal Dependencies**:
- Existing Firestore schema (no schema changes required)
- `created_at` field present in all summary documents (assumed)
- User documents exist in `users` collection

**Assumptions**:
- All summaries have `created_at` field in ISO 8601 format
- System clock synchronized (UTC timezone)
- Firestore composite index can be created (no quota limits)
- Monthly execution sufficient for data hygiene
- No legal requirement to retain data beyond 30 days

---

## 7. Technical Architecture

### 7.1 Component Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                     GCP Project                             │
│                                                             │
│  ┌────────────────┐      ┌─────────────────┐              │
│  │ Cloud Scheduler│─────▶│  Pub/Sub Topic  │              │
│  │ cleanup-old-   │      │ cleanup-old-    │              │
│  │ news-job       │      │ news-topic      │              │
│  │                │      │                 │              │
│  │ Schedule:      │      │ Message:        │              │
│  │ 0 3 1 * *      │      │ {retention_days}│              │
│  └────────────────┘      └────────┬────────┘              │
│                                   │                        │
│                                   ▼                        │
│                          ┌─────────────────┐              │
│                          │ Cloud Function  │              │
│                          │ cleanup-old-    │              │
│                          │ summaries       │              │
│                          │                 │              │
│                          │ Runtime: Py 3.11│              │
│                          │ Memory: 256MB   │              │
│                          │ Timeout: 540s   │              │
│                          └────────┬────────┘              │
│                                   │                        │
│                                   ▼                        │
│                          ┌─────────────────┐              │
│                          │   Firestore DB  │              │
│                          │                 │              │
│                          │ users/{uid}/    │              │
│                          │   summaries/    │              │
│                          │     {doc_id}    │              │
│                          └─────────────────┘              │
│                                                             │
│  ┌────────────────┐      ┌─────────────────┐              │
│  │ Cloud Logging  │◀─────│ Cloud Monitoring│              │
│  │                │      │                 │              │
│  │ Logs retention:│      │ Alerts:         │              │
│  │ 30 days        │      │ - Execution fail│              │
│  └────────────────┘      │ - Timeout       │              │
│                          └─────────────────┘              │
└─────────────────────────────────────────────────────────────┘
```

### 7.2 Execution Flow

```
1. Cloud Scheduler triggers at scheduled time (1st of month, 3 AM KST)
   ↓
2. Pub/Sub message published to cleanup-old-news-topic
   Message: {"retention_days": 30}
   ↓
3. Cloud Function instance started (cold or warm start)
   ↓
4. Function parses Pub/Sub message
   - Extract retention_days (default: 30)
   - Calculate cutoff_date = UTC_NOW - retention_days
   ↓
5. Initialize Firestore client
   ↓
6. Query all users from 'users' collection
   ↓
7. For each user:
   7.1 Query summaries where created_at < cutoff_date
   7.2 Batch delete (max 500 per batch)
   7.3 Commit batch
   7.4 Log deletion count
   ↓
8. Log final summary:
   - Total users processed
   - Total documents deleted
   - Execution duration
   ↓
9. Return success response
   ↓
10. Cloud Logging stores all logs
    ↓
11. Cloud Monitoring evaluates alerts
```

### 7.3 Data Flow

```
Input:
  - Pub/Sub message: {"retention_days": 30}
  - Current UTC timestamp: 2025-11-01T18:00:00Z (3 AM KST)

Processing:
  - Cutoff date: 2025-10-02T18:00:00Z
  - Firestore query: created_at < "2025-10-02T18:00:00.000000"

Output:
  - Deleted documents from Firestore
  - Log entries in Cloud Logging:
    {
      "status": "success",
      "users_processed": 10,
      "users_with_deletions": 8,
      "total_deleted": 245,
      "cutoff_date": "2025-10-02T18:00:00.000000",
      "retention_days": 30,
      "duration_seconds": 42.5
    }
```

### 7.4 Error Handling Flow

```
Error Type: Firestore Permission Denied
  ↓
Function catches exception
  ↓
Log ERROR with details
  ↓
Return error response
  ↓
Cloud Monitoring triggers alert
  ↓
Admin receives notification

Error Type: User Processing Failure
  ↓
Function catches exception
  ↓
Log WARNING with user_id
  ↓
Continue to next user
  ↓
Final response includes partial success status

Error Type: Timeout (9 minutes exceeded)
  ↓
Cloud Functions runtime terminates execution
  ↓
Log shows last processed user
  ↓
Cloud Monitoring triggers timeout alert
  ↓
Next scheduled run processes remaining users
```

---

## 8. Implementation Considerations

### 8.1 Deployment Prerequisites

- [ ] GCP project with billing enabled
- [ ] Cloud Functions API enabled
- [ ] Cloud Scheduler API enabled
- [ ] Pub/Sub API enabled
- [ ] Firestore database created (already exists)
- [ ] Service account with `roles/datastore.user`
- [ ] gcloud CLI installed and authenticated

### 8.2 Infrastructure as Code

**Required GCP Resources**:
1. Pub/Sub Topic: `cleanup-old-news-topic`
2. Cloud Function: `cleanup-old-news` (Gen 2, Python 3.11)
3. Cloud Scheduler Job: `cleanup-old-news-job`
4. Firestore Composite Index: `summaries.created_at`

**Deployment Commands** (documented in implementation guide):
```bash
# Create Pub/Sub topic
gcloud pubsub topics create cleanup-old-news-topic

# Deploy Cloud Function
gcloud functions deploy cleanup-old-news --gen2 ...

# Create Scheduler job
gcloud scheduler jobs create pubsub cleanup-old-news-job ...
```

### 8.3 Testing Strategy

**Unit Testing** (Local):
- Test cutoff date calculation logic
- Test Pub/Sub message parsing
- Test batch deletion logic (mocked Firestore)
- Test error handling paths

**Integration Testing** (GCP Test Project):
- Test with sample Firestore data
- Test manual Pub/Sub trigger
- Test timeout scenarios (large dataset)
- Test concurrent execution behavior

**User Acceptance Testing**:
- Verify correct summaries deleted (age-based)
- Verify recent summaries retained
- Verify user documents not affected
- Verify logs contain expected information

**Monitoring Testing**:
- Trigger alerts manually
- Verify alert delivery
- Verify log queries return expected results

### 8.4 Rollout Plan

**Phase 1: Development & Testing** (Week 1)
- Create `cleanup_function` directory
- Implement `main.py` with cleanup logic
- Write unit tests
- Test locally with Functions Framework

**Phase 2: Staging Deployment** (Week 2)
- Deploy to GCP test project
- Create test data in Firestore
- Run manual triggers
- Verify logs and metrics
- Test error scenarios

**Phase 3: Production Deployment** (Week 3)
- Deploy to production project
- Create Scheduler job (initially disabled)
- Run first manual cleanup during maintenance window
- Monitor execution
- Enable scheduled execution

**Phase 4: Monitoring & Optimization** (Week 4)
- Configure Cloud Monitoring alerts
- Create log-based metrics
- Document operational runbooks
- Train operations team

### 8.5 Rollback Strategy

**Rollback Trigger Conditions**:
- Function deletes incorrect data
- Function causes service disruption
- Function exceeds timeout repeatedly
- Critical error in production

**Rollback Procedure**:
1. Disable Cloud Scheduler job immediately
2. Delete Cloud Function (stops further executions)
3. Review logs to identify affected users
4. Assess data loss impact
5. Communicate with stakeholders
6. Plan recovery strategy (if possible)

**Prevention**:
- No rollback of deleted data (permanent deletion)
- Testing in staging environment mandatory
- Incremental rollout with monitoring
- Manual verification after first production run

---

## 9. Operational Procedures

### 9.1 Monitoring Checklist

**Daily** (Automated):
- Cloud Monitoring alerts configured and active

**Monthly** (After Scheduled Run):
- [ ] Verify cleanup job executed successfully
- [ ] Review Cloud Logging for execution summary
- [ ] Check deletion count is reasonable (not 0, not excessive)
- [ ] Verify execution time within acceptable range (<5 minutes)
- [ ] Check for any ERROR logs
- [ ] Validate no user-reported issues

**Quarterly**:
- [ ] Review Firestore storage trends
- [ ] Analyze cost reduction from cleanup
- [ ] Review retention policy effectiveness
- [ ] Assess need for retention period adjustment

### 9.2 Common Operational Tasks

**Task: Manual Cleanup Execution**
```bash
# Run cleanup immediately
gcloud scheduler jobs run cleanup-old-news-job --location=asia-northeast3

# Verify execution
gcloud functions logs read cleanup-old-news --region=asia-northeast3 --limit=50
```

**Task: Change Retention Period**
```bash
# Update to 60 days
gcloud scheduler jobs update pubsub cleanup-old-news-job \
  --location=asia-northeast3 \
  --message-body='{"retention_days": 60}'
```

**Task: Debug Execution Failure**
```bash
# View recent logs
gcloud functions logs read cleanup-old-news \
  --region=asia-northeast3 \
  --gen2 \
  --limit=100

# Check function status
gcloud functions describe cleanup-old-news \
  --region=asia-northeast3 \
  --gen2
```

**Task: Temporarily Disable Cleanup**
```bash
# Pause scheduler job
gcloud scheduler jobs pause cleanup-old-news-job --location=asia-northeast3

# Resume scheduler job
gcloud scheduler jobs resume cleanup-old-news-job --location=asia-northeast3
```

### 9.3 Incident Response

**Scenario: Cleanup Deleted Too Much Data**
1. Immediately disable scheduler job
2. Gather logs and identify cutoff date used
3. Determine if configuration error or code bug
4. Assess data loss impact (summaries older than 30 days expected to be deleted)
5. Communicate to stakeholders if user data impacted
6. Implement fix and test thoroughly before re-enabling

**Scenario: Cleanup Failed to Run**
1. Check Cloud Scheduler job status
2. Check Pub/Sub topic exists and is accessible
3. Check Cloud Function deployment status
4. Review Cloud Logging for error messages
5. Trigger manual cleanup if urgent
6. Fix underlying issue (permissions, quota, etc.)

**Scenario: Timeout on Every Execution**
1. Review log to find last processed user
2. Calculate total users and estimate time required
3. If data volume exceeds capacity:
   - Increase function timeout (max 60 minutes for Gen 2)
   - Increase memory allocation (256 MB → 512 MB)
   - Consider pagination strategy (split into multiple runs)
4. Re-deploy with updated configuration
5. Monitor next execution

---

## 10. Cost Estimation

### 10.1 GCP Service Costs (Monthly)

**Assumptions**:
- 100 users
- 10 summaries per user per month
- Average 30 old summaries deleted per user per month
- 1 scheduled execution per month
- Execution time: 3 minutes
- Function memory: 256 MB

| Service | Usage | Unit Cost | Monthly Cost |
|---------|-------|-----------|--------------|
| **Cloud Scheduler** | 1 job | $0.10/job/month | **$0.10** |
| **Pub/Sub** | 1 message/month | $0.40/1M messages | **$0.00** |
| **Cloud Functions (Gen 2)** | 1 invocation, 3 min, 256MB | $0.00001215/GB-sec | **$0.00** |
| **Firestore Reads** | 100 user docs + 3,000 summary queries | $0.06/100K reads | **$0.00** |
| **Firestore Deletes** | 3,000 deletes | $0.18/100K writes | **$0.01** |
| **Cloud Logging** | ~100 KB logs | $0.50/GB ingestion | **$0.00** |
| **Cloud Monitoring** | 1 time series | Free tier | **$0.00** |
| | | **Total:** | **$0.11/month** |

**Notes**:
- Most services fall within GCP free tier
- Cloud Scheduler is the only significant recurring cost
- Scaling to 1,000 users: ~$0.15/month (minimal increase)
- Firestore read/write costs negligible due to free tier (50K reads/day, 20K writes/day)

### 10.2 Cost-Benefit Analysis

**Direct Cost Savings**:
- Firestore storage reduction: ~30-50% (varies by user activity)
- For 100 users with 1,000 docs each at 2KB: 2 MB saved
- Storage cost saved: ~$0.0004/month (minimal at small scale)
- **At scale** (10,000 users): $0.04/month saved in storage

**Indirect Benefits**:
- Improved query performance (faster API responses)
- Reduced Firestore read costs (smaller result sets)
- Better user experience (faster load times)
- Reduced operational overhead (no manual cleanup)

**Break-Even Analysis**:
- Monthly cost: $0.11
- Immediate value: Operational efficiency, performance
- Financial ROI: Positive at scale (>5,000 users)
- **Primary ROI**: Non-financial (performance, maintainability)

---

## 11. Risk Assessment & Mitigation

### 11.1 Technical Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| **Function timeout with large user base** | Medium | High | Increase timeout to 60 min; implement pagination |
| **Firestore rate limit exceeded** | Low | Medium | Batch operations; exponential backoff |
| **Service account permission issues** | Low | High | Pre-deployment permission validation; documentation |
| **Index creation failure** | Low | Medium | Manual index creation; monitoring |
| **Data deletion bug (wrong data deleted)** | Low | Critical | Thorough testing; staging environment; manual first run |
| **Concurrent execution issues** | Low | Low | Pub/Sub deduplication; documentation warning |

### 11.2 Operational Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| **Misconfiguration of retention period** | Medium | Medium | Validation logic; default fallback; change review process |
| **Cleanup not executed (scheduler failure)** | Low | Low | Monitoring alerts; monthly verification checklist |
| **Unnoticed execution failures** | Medium | Medium | Alerting on failure; monthly review checklist |
| **Loss of debugging capability (insufficient logs)** | Low | Medium | Comprehensive logging strategy; log retention policy |

### 11.3 Business Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| **User complaints about missing old summaries** | Low | Low | Clear data retention policy; user education (if needed) |
| **Regulatory compliance issues (data retention)** | Low | High | Configurable retention period; legal review |
| **Unexpected cost increase at scale** | Low | Low | Cost monitoring; free tier coverage; budget alerts |

---

## 12. Acceptance Testing Scenarios

### 12.1 Functional Tests

**Test Case FT-001: Scheduled Execution**
- **Given**: Scheduler job configured for 1st of month at 3 AM KST
- **When**: Date/time reaches scheduled time
- **Then**: Cloud Function executes within 15 minutes of scheduled time
- **Verify**: Cloud Logging shows execution start log

**Test Case FT-002: Data Deletion - Old Summaries**
- **Given**: User has 10 summaries created 35 days ago
- **When**: Cleanup function executes with 30-day retention
- **Then**: All 10 summaries are deleted
- **Verify**: Firestore query returns 0 results for that user's old summaries

**Test Case FT-003: Data Retention - Recent Summaries**
- **Given**: User has 5 summaries created 25 days ago
- **When**: Cleanup function executes with 30-day retention
- **Then**: All 5 summaries are retained
- **Verify**: Firestore query returns 5 results for that user's summaries

**Test Case FT-004: User Document Preservation**
- **Given**: User document exists with summaries subcollection
- **When**: Cleanup function deletes all summaries
- **Then**: User document still exists (not deleted)
- **Verify**: `db.collection('users').document(user_id).get()` returns document

**Test Case FT-005: Multiple Users**
- **Given**: 10 users with varying numbers of old summaries
- **When**: Cleanup function executes
- **Then**: Each user's old summaries deleted independently
- **Verify**: Log shows correct deletion count per user

**Test Case FT-006: Custom Retention Period**
- **Given**: Pub/Sub message contains `{"retention_days": 60}`
- **When**: Cleanup function executes
- **Then**: Only summaries older than 60 days are deleted
- **Verify**: Log shows `"retention_days": 60`

### 12.2 Non-Functional Tests

**Test Case NFT-001: Performance - 100 Users**
- **Given**: 100 users with 30 old summaries each (3,000 total documents)
- **When**: Cleanup function executes
- **Then**: Execution completes within 5 minutes
- **Verify**: Cloud Functions execution duration metric

**Test Case NFT-002: Error Handling - Single User Failure**
- **Given**: One user's Firestore path is corrupted
- **When**: Cleanup function encounters error on that user
- **Then**: Processing continues for remaining users
- **Verify**: Logs show WARNING for failed user, SUCCESS for others

**Test Case NFT-003: Logging Completeness**
- **Given**: Cleanup function executes successfully
- **When**: Reviewing Cloud Logging
- **Then**: All required log fields present (users_processed, total_deleted, cutoff_date, etc.)
- **Verify**: Log parsing script extracts all fields successfully

**Test Case NFT-004: Idempotency**
- **Given**: Cleanup function executed once
- **When**: Same function executed again immediately
- **Then**: Second execution deletes 0 documents (no duplicates)
- **Verify**: Log shows `"total_deleted": 0`

### 12.3 Edge Case Tests

**Test Case ECT-001: No Users Exist**
- **Given**: Firestore `users` collection is empty
- **When**: Cleanup function executes
- **Then**: Function completes successfully with 0 deletions
- **Verify**: Log shows `"users_processed": 0, "total_deleted": 0`

**Test Case ECT-002: User with No Summaries**
- **Given**: User document exists but has empty `summaries` subcollection
- **When**: Cleanup function processes this user
- **Then**: No errors, 0 deletions for that user
- **Verify**: Log shows user processed with 0 deletions

**Test Case ECT-003: Invalid Retention Days**
- **Given**: Pub/Sub message contains `{"retention_days": 5}` (too low)
- **When**: Cleanup function parses configuration
- **Then**: Default value (30 days) is used
- **Verify**: Log shows WARNING and `"retention_days": 30`

**Test Case ECT-004: Malformed Pub/Sub Message**
- **Given**: Pub/Sub message contains invalid JSON
- **When**: Cleanup function attempts to parse message
- **Then**: Default configuration used, function executes normally
- **Verify**: Log shows WARNING about parsing failure

---

## 13. Definition of Done

A feature is considered "Done" when all of the following criteria are met:

### 13.1 Code Completeness
- [ ] All user stories implemented and acceptance criteria met
- [ ] Code reviewed and approved by technical lead
- [ ] Python code follows PEP 8 style guidelines
- [ ] Type hints present for all function signatures
- [ ] Docstrings present for all public functions
- [ ] Error handling implemented for all identified edge cases
- [ ] No critical or high-severity code analysis warnings

### 13.2 Testing
- [ ] Unit tests written for core logic (>80% code coverage)
- [ ] Integration tests executed in staging environment
- [ ] All functional acceptance test cases passed
- [ ] All non-functional acceptance test cases passed
- [ ] Edge case scenarios tested and validated
- [ ] Performance benchmarks met (5-minute execution for 100 users)
- [ ] Manual smoke testing completed in production

### 13.3 Deployment
- [ ] Cloud Function deployed to production
- [ ] Pub/Sub topic created and configured
- [ ] Cloud Scheduler job created and validated
- [ ] Firestore composite index created and built
- [ ] Service account permissions granted and verified
- [ ] Infrastructure documented (gcloud commands in implementation guide)
- [ ] Rollback procedure tested in staging

### 13.4 Documentation
- [ ] Implementation guide completed and reviewed
- [ ] Operational runbook created (monitoring, troubleshooting)
- [ ] Deployment commands documented
- [ ] Configuration change procedures documented
- [ ] Code comments present for complex logic
- [ ] Architecture diagrams created and reviewed

### 13.5 Monitoring & Observability
- [ ] Cloud Logging queries documented
- [ ] Log retention policy configured (30 days minimum)
- [ ] Cloud Monitoring alerts configured (execution failure, timeout)
- [ ] Alert notification channels configured and tested
- [ ] Dashboard created with key metrics
- [ ] Logging verified to contain all required fields

### 13.6 Operational Readiness
- [ ] First production execution monitored manually
- [ ] Operations team trained on monitoring procedures
- [ ] Incident response procedures documented
- [ ] Manual trigger procedure tested
- [ ] Disable/enable procedure tested
- [ ] Logs reviewed and validated for first production run

### 13.7 Stakeholder Acceptance
- [ ] Product Owner approval
- [ ] Technical Lead approval
- [ ] DevOps team sign-off
- [ ] Security review completed (if required)
- [ ] Cost estimation reviewed and approved

---

## 14. Open Questions & Decisions

### 14.1 Resolved Decisions

| Decision | Options Considered | Decision Made | Rationale | Date |
|----------|-------------------|---------------|-----------|------|
| **Implementation Approach** | Cloud Function vs Backend API | Cloud Function | Cost efficiency, independence, existing pattern | 2025-11-01 |
| **Execution Frequency** | Daily, Weekly, Monthly | Monthly | Data freshness not critical, cost optimization | 2025-11-01 |
| **Retention Period** | 14, 30, 60, 90 days | 30 days (configurable) | Balance between relevance and storage | 2025-11-01 |
| **Deletion Type** | Soft delete vs Hard delete | Hard delete (permanent) | Simplicity, storage savings, no recovery requirement | 2025-11-01 |
| **Execution Time** | Various times | 3 AM KST | Low user activity period | 2025-11-01 |

### 14.2 Open Questions

| Question | Options | Impact | Decision Owner | Target Date |
|----------|---------|--------|----------------|-------------|
| Should we notify users before deleting their data? | Yes/No | Low (old data only) | Product Owner | Before deployment |
| Should we archive data to Cloud Storage before deletion? | Yes/No | Medium (cost, complexity) | Technical Lead | Sprint 2 planning |
| Should we implement per-user retention preferences? | Yes/No | High (complexity) | Product Owner | Roadmap Q2 2026 |
| Should we create a recovery mechanism (soft delete)? | Yes/No | Medium (complexity, cost) | Product Owner | Roadmap Q2 2026 |

### 14.3 Assumptions to Validate

- [ ] All existing summaries have `created_at` field (data audit required)
- [ ] 30-day retention is legally compliant (legal review if needed)
- [ ] Monthly cleanup frequency is sufficient (monitor data growth)
- [ ] No user complaints expected about missing old data (user research)
- [ ] Firestore performance adequate for query at scale (load testing)

---

## 15. Future Enhancements (Post-MVP)

### 15.1 Short-Term Enhancements (Q1 2026)

**Enhancement 1: Archive Before Delete**
- Archive old summaries to Cloud Storage before deletion
- Enable data recovery if needed
- Use for analytics on deleted data
- Estimated effort: 5 story points

**Enhancement 2: User-Visible Retention Policy**
- Display retention policy in app settings
- Show user how many summaries will be retained
- Provide transparency about data lifecycle
- Estimated effort: 3 story points

**Enhancement 3: Advanced Monitoring Dashboard**
- Create Looker Studio dashboard with cleanup trends
- Track deletion patterns over time
- Monitor storage savings
- Estimated effort: 2 story points

### 15.2 Medium-Term Enhancements (Q2 2026)

**Enhancement 4: Per-User Retention Preferences**
- Allow users to configure retention period (7-90 days)
- Store preferences in user document
- Cleanup function respects per-user settings
- Estimated effort: 8 story points

**Enhancement 5: Soft Delete with Recovery**
- Add `deleted_at` field instead of hard delete
- Implement 30-day recovery window
- Create user-facing "Trash" feature
- Permanent delete after recovery window
- Estimated effort: 13 story points

**Enhancement 6: Duplicate Summary Cleanup**
- Detect and remove duplicate summaries (same URL)
- Run during cleanup execution
- Log duplicate removal separately
- Estimated effort: 5 story points

### 15.3 Long-Term Enhancements (2026+)

**Enhancement 7: Intelligent Retention**
- ML-based retention using user engagement signals
- Keep frequently accessed summaries longer
- Delete rarely viewed summaries sooner
- Estimated effort: 21 story points

**Enhancement 8: Multi-Collection Cleanup**
- Extend cleanup to other collections (keywords, user metadata)
- Identify and remove orphaned data
- Comprehensive data lifecycle management
- Estimated effort: 13 story points

---

## 16. Glossary

| Term | Definition |
|------|------------|
| **Cleanup Function** | The Cloud Function that executes the deletion logic |
| **Cutoff Date** | The calculated date before which all summaries are deleted (UTC_NOW - retention_days) |
| **Retention Period** | Number of days to retain summaries before deletion (default: 30 days) |
| **Summary** | A news article summary document stored in Firestore |
| **Batch Operation** | Firestore operation that groups multiple writes/deletes into a single atomic transaction (max 500 operations) |
| **Cold Start** | Initial startup time for a Cloud Function instance (not cached) |
| **Warm Start** | Fast startup time for a Cloud Function instance (cached from previous execution) |
| **Idempotent** | An operation that produces the same result whether executed once or multiple times |
| **ISO 8601** | International standard for date/time format (e.g., "2025-10-15T12:30:00.000000") |
| **Cloud Scheduler Job** | A cron-based task scheduler in GCP that triggers events on a schedule |
| **Pub/Sub Topic** | A message queue in GCP that decouples event producers from consumers |
| **Service Account** | A GCP identity used by applications (not human users) for authentication |
| **Firestore Composite Index** | A database index on multiple fields or single field in a subcollection to enable fast queries |

---

## 17. Appendix

### 17.1 Related Documents

- **Implementation Guide**: `c:\Projects\GCPNewsPortal\.docs\cleanup-implementation-guide.md`
- **Architecture Overview**: `c:\Projects\GCPNewsPortal\.docs\cleanup-automation-overview.md`
- **Implementation Comparison**: `c:\Projects\GCPNewsPortal\.docs\cleanup-implementation-comparison.md`
- **Main Project README**: `c:\Projects\GCPNewsPortal\README.md`

### 17.2 Reference Architecture

**Existing Cloud Functions Pattern**:
- `news_summarizer/main.py` - Similar pattern for Pub/Sub-triggered function
- `trigger_function/main.py` - Existing scheduler integration

**Firestore Schema**:
```
users/{user_id}
  - (user metadata fields)
  summaries/{summary_id}
    - title: string
    - url: string
    - summary: string
    - keyword: string
    - created_at: string (ISO 8601)
    - summaryTokens: number
  keywords/{keyword_id}
    - keyword: string
    - created_at: timestamp
```

### 17.3 Compliance & Legal Considerations

**Data Retention**:
- No specific legal requirement for news summary retention identified
- 30-day retention considered reasonable for news content
- Users implicitly consent via service usage (no explicit data retention agreement)

**GDPR/Privacy**:
- Summaries do not contain personal data (news content only)
- User ID association for organization purposes only
- No special privacy considerations beyond standard practices

**Recommendations**:
- Document data retention policy in Terms of Service (future)
- Provide transparency to users about data lifecycle (future)
- Consult legal team before launching to EU users (if applicable)

### 17.4 Contact Information

**Product Team**:
- Product Owner: [To be assigned]
- Technical Lead: [To be assigned]
- DevOps Engineer: [To be assigned]

**Escalation Path**:
1. DevOps Engineer (operational issues)
2. Technical Lead (technical decisions)
3. Product Owner (business decisions)

---

## Document Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-11-01 | Claude AI | Initial draft based on implementation guide |

---

**Document Status**: Draft for Review
**Next Review Date**: [To be scheduled]
**Approval Required From**: Product Owner, Technical Lead, DevOps Team

---

*This product specification is a living document and will be updated as requirements evolve and implementation progresses.*
