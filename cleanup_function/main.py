"""
Cloud Function for cleaning up old news summaries.

This module implements an automated cleanup system for the GCP News Portal
application. It removes news summaries older than a configurable retention
period using a scheduled Cloud Function triggered by Pub/Sub.

Architecture:
    - Cloud Scheduler -> Pub/Sub Topic -> Cloud Function -> Firestore
    - Processes all users and deletes summaries based on created_at timestamp
    - Uses batch operations for efficient deletion (max 500 per batch)
    - Implements comprehensive logging and error handling

Author: Generated for GCP News Portal
Version: 1.0
Python: 3.11+
"""

import functions_framework
from google.cloud import firestore
from datetime import datetime, timedelta
import base64
import json
import logging
from typing import Dict, Any, Optional, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
DEFAULT_RETENTION_DAYS = 30
MIN_RETENTION_DAYS = 7
MAX_RETENTION_DAYS = 365
FIRESTORE_BATCH_LIMIT = 500


def parse_pubsub_message(cloud_event: Any) -> int:
    """
    Parse retention_days from Pub/Sub message data.

    Extracts and validates the retention period from the base64-encoded
    JSON payload in the Pub/Sub message. Falls back to default value
    if parsing fails or value is invalid.

    Args:
        cloud_event: Cloud event object containing Pub/Sub message data

    Returns:
        int: Validated retention days (7-365 range) or default value (30)

    Design Pattern:
        - Single Responsibility: Only handles message parsing
        - Defensive programming: Validates all inputs and provides fallback
    """
    retention_days = DEFAULT_RETENTION_DAYS

    try:
        # Check if message data exists
        if not cloud_event.data or "message" not in cloud_event.data:
            logger.info("No message data found, using default retention period")
            return retention_days

        # Decode base64 message data
        message_data = base64.b64decode(
            cloud_event.data["message"]["data"]
        ).decode('utf-8')

        # Parse JSON configuration
        config = json.loads(message_data)
        requested_days = config.get('retention_days')

        if requested_days is None:
            logger.info("No retention_days specified, using default")
            return retention_days

        # Validate retention period range
        if not isinstance(requested_days, int):
            logger.warning(
                f"retention_days must be integer, got {type(requested_days).__name__}. "
                f"Using default: {DEFAULT_RETENTION_DAYS}"
            )
            return retention_days

        if requested_days < MIN_RETENTION_DAYS:
            logger.warning(
                f"retention_days {requested_days} below minimum {MIN_RETENTION_DAYS}. "
                f"Using default: {DEFAULT_RETENTION_DAYS}"
            )
            return retention_days

        if requested_days > MAX_RETENTION_DAYS:
            logger.warning(
                f"retention_days {requested_days} exceeds maximum {MAX_RETENTION_DAYS}. "
                f"Using default: {DEFAULT_RETENTION_DAYS}"
            )
            return retention_days

        logger.info(f"Using retention period from message: {requested_days} days")
        return requested_days

    except json.JSONDecodeError as e:
        logger.warning(f"Failed to parse JSON message: {e}. Using default: {DEFAULT_RETENTION_DAYS}")
        return retention_days

    except Exception as e:
        logger.warning(f"Error parsing Pub/Sub message: {e}. Using default: {DEFAULT_RETENTION_DAYS}")
        return retention_days


def calculate_cutoff_date(retention_days: int) -> str:
    """
    Calculate the cutoff date for deletion in ISO 8601 format.

    Determines the timestamp before which all summaries should be deleted.
    Uses UTC timezone to ensure consistency across regions.

    Args:
        retention_days: Number of days to retain summaries

    Returns:
        str: ISO 8601 formatted cutoff date (e.g., "2025-10-02T18:00:00.000000")

    Design Pattern:
        - Single Responsibility: Only handles date calculation
        - Open/Closed: Easy to extend for different date calculation strategies
    """
    cutoff_datetime = datetime.utcnow() - timedelta(days=retention_days)
    cutoff_iso = cutoff_datetime.isoformat()

    logger.info(
        f"Calculated cutoff date: {cutoff_iso} "
        f"(retention: {retention_days} days from {datetime.utcnow().isoformat()})"
    )

    return cutoff_iso


def delete_old_summaries_for_user(
    db: firestore.Client,
    user_id: str,
    cutoff_date: str
) -> int:
    """
    Delete old summaries for a single user using batch operations.

    Queries and deletes all summaries created before the cutoff date for
    the specified user. Uses Firestore batch operations for efficiency,
    respecting the 500 document batch limit.

    Args:
        db: Initialized Firestore client
        user_id: User document ID
        cutoff_date: ISO 8601 formatted cutoff date

    Returns:
        int: Number of documents deleted for this user

    Raises:
        Exception: Propagates Firestore errors to caller for handling

    Design Pattern:
        - Single Responsibility: Handles deletion for one user only
        - Dependency Inversion: Depends on Firestore abstraction, not concrete implementation
        - Error handling: Allows caller to decide recovery strategy
    """
    total_deleted = 0

    try:
        # Query old summaries for this user
        old_summaries_query = (
            db.collection('users')
            .document(user_id)
            .collection('summaries')
            .where('created_at', '<', cutoff_date)
        )

        old_summaries = old_summaries_query.stream()

        # Initialize batch for deletions
        batch = db.batch()
        batch_count = 0

        for doc in old_summaries:
            batch.delete(doc.reference)
            batch_count += 1
            total_deleted += 1

            # Commit when batch reaches Firestore limit
            if batch_count >= FIRESTORE_BATCH_LIMIT:
                batch.commit()
                logger.info(
                    f"User {user_id}: Committed batch of {batch_count} deletions "
                    f"(total so far: {total_deleted})"
                )
                batch = db.batch()
                batch_count = 0

        # Commit remaining documents in final batch
        if batch_count > 0:
            batch.commit()
            logger.info(
                f"User {user_id}: Committed final batch of {batch_count} deletions"
            )

        if total_deleted > 0:
            logger.info(f"User {user_id}: Deleted {total_deleted} old summaries")
        else:
            logger.info(f"User {user_id}: No old summaries to delete")

        return total_deleted

    except Exception as e:
        logger.error(
            f"Error deleting summaries for user {user_id}: {e}",
            exc_info=True
        )
        raise


@functions_framework.cloud_event
def cleanup_old_summaries(cloud_event: Any) -> Dict[str, Any]:
    """
    Main Cloud Function entry point for cleaning up old news summaries.

    This function is triggered by Pub/Sub messages from Cloud Scheduler.
    It processes all users in the Firestore database and deletes summaries
    older than the configured retention period.

    Execution Flow:
        1. Parse configuration from Pub/Sub message
        2. Calculate cutoff date based on retention period
        3. Initialize Firestore client
        4. Iterate through all users
        5. For each user, delete old summaries using batch operations
        6. Log comprehensive execution summary
        7. Return structured result

    Args:
        cloud_event: Cloud event object from Pub/Sub trigger containing:
            - data.message.data: Base64-encoded JSON with optional retention_days

    Returns:
        Dict[str, Any]: Execution summary with the following structure:
            {
                'status': 'success' | 'error',
                'users_processed': int,
                'users_with_deletions': int,
                'total_deleted': int,
                'cutoff_date': str (ISO 8601),
                'retention_days': int,
                'error': str (only if status='error')
            }

    Error Handling Strategy:
        - Graceful degradation: Continue processing other users if one fails
        - Per-user errors logged as WARNING
        - Critical errors logged as ERROR and return error status
        - Idempotent: Safe to run multiple times without side effects

    Performance Characteristics:
        - Time Complexity: O(U + D) where U=users, D=documents to delete
        - Space Complexity: O(B) where B=batch size (500 max)
        - Target: <5 minutes for 100 users with 3000 total deletions

    Design Patterns:
        - Template Method: Defines cleanup algorithm structure
        - Strategy: Configurable retention period via Pub/Sub
        - Facade: Simplifies complex multi-step cleanup process
    """
    start_time = datetime.utcnow()
    logger.info("=" * 60)
    logger.info("Cleanup job started")
    logger.info(f"Execution timestamp: {start_time.isoformat()}")
    logger.info("=" * 60)

    try:
        # Step 1: Parse configuration from Pub/Sub message
        retention_days = parse_pubsub_message(cloud_event)

        # Step 2: Calculate cutoff date
        cutoff_date = calculate_cutoff_date(retention_days)

        # Step 3: Initialize Firestore client
        db = firestore.Client()
        logger.info("Firestore client initialized successfully")

        # Step 4: Initialize counters for execution summary
        total_deleted = 0
        users_processed = 0
        users_with_deletions = 0
        failed_users = []

        # Step 5: Query all users
        users_ref = db.collection('users')
        users = users_ref.stream()

        logger.info("Starting user processing iteration")

        # Step 6: Process each user
        for user_doc in users:
            user_id = user_doc.id
            users_processed += 1

            logger.info(f"Processing user {users_processed}: {user_id}")

            try:
                # Delete old summaries for this user
                deleted_count = delete_old_summaries_for_user(
                    db=db,
                    user_id=user_id,
                    cutoff_date=cutoff_date
                )

                total_deleted += deleted_count

                if deleted_count > 0:
                    users_with_deletions += 1

            except Exception as user_error:
                # Log error but continue processing other users
                failed_users.append(user_id)
                logger.warning(
                    f"Failed to process user {user_id}, continuing with others. "
                    f"Error: {user_error}"
                )
                continue

        # Step 7: Calculate execution duration
        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()

        # Step 8: Build execution summary
        result = {
            'status': 'success',
            'users_processed': users_processed,
            'users_with_deletions': users_with_deletions,
            'total_deleted': total_deleted,
            'cutoff_date': cutoff_date,
            'retention_days': retention_days,
            'execution_time_seconds': round(duration, 2),
            'timestamp': end_time.isoformat()
        }

        # Add partial failure information if applicable
        if failed_users:
            result['failed_users_count'] = len(failed_users)
            result['failed_users'] = failed_users[:10]  # Limit to first 10 for logging
            logger.warning(
                f"Completed with partial failures: {len(failed_users)} users failed"
            )

        # Step 9: Log comprehensive summary
        logger.info("=" * 60)
        logger.info("Cleanup job completed successfully")
        logger.info("=" * 60)
        logger.info(f"Execution Summary:")
        logger.info(f"  - Total users processed: {users_processed}")
        logger.info(f"  - Users with deletions: {users_with_deletions}")
        logger.info(f"  - Total documents deleted: {total_deleted}")
        logger.info(f"  - Cutoff date: {cutoff_date}")
        logger.info(f"  - Retention period: {retention_days} days")
        logger.info(f"  - Execution time: {duration:.2f} seconds")
        if failed_users:
            logger.info(f"  - Failed users: {len(failed_users)}")
        logger.info("=" * 60)

        return result

    except Exception as e:
        # Critical error - log and return error response
        error_msg = str(e)
        logger.error("=" * 60)
        logger.error("Cleanup job failed with critical error")
        logger.error("=" * 60)
        logger.error(f"Error: {error_msg}", exc_info=True)
        logger.error("=" * 60)

        return {
            'status': 'error',
            'error': error_msg,
            'error_type': type(e).__name__,
            'timestamp': datetime.utcnow().isoformat()
        }
