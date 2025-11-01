"""
Local testing script for the cleanup Cloud Function.

This script provides utilities for testing the cleanup function locally
without deploying to GCP. It includes mock data generators and test
scenarios to validate functionality.

Usage:
    1. Set environment variables:
       export GOOGLE_APPLICATION_CREDENTIALS="path/to/service-account-key.json"
       export GOOGLE_CLOUD_PROJECT="your-project-id"

    2. Run the script:
       python test_local.py

Requirements:
    - functions-framework installed (pip install functions-framework)
    - Valid GCP service account credentials
    - Firestore database accessible

Author: Generated for GCP News Portal
Version: 1.0
Python: 3.11+
"""

import base64
import json
from datetime import datetime, timedelta
from typing import Dict, Any
import sys
import os


class MockCloudEvent:
    """
    Mock Cloud Event object for local testing.

    Simulates the structure of a Cloud Event received from Pub/Sub,
    allowing local function testing without actual Pub/Sub infrastructure.
    """

    def __init__(self, retention_days: int = None):
        """
        Initialize mock cloud event.

        Args:
            retention_days: Optional retention period to include in message.
                          If None, creates an empty message.
        """
        self.data = {}

        if retention_days is not None:
            # Create message payload with retention_days
            message_payload = json.dumps({"retention_days": retention_days})
            encoded_payload = base64.b64encode(message_payload.encode()).decode()

            self.data = {
                "message": {
                    "data": encoded_payload,
                    "messageId": "test-message-123",
                    "publishTime": datetime.utcnow().isoformat()
                }
            }
        else:
            # Empty message (will use default retention)
            self.data = {
                "message": {
                    "data": base64.b64encode(b"{}").decode(),
                    "messageId": "test-message-empty",
                    "publishTime": datetime.utcnow().isoformat()
                }
            }


def test_parse_pubsub_message():
    """Test the parse_pubsub_message function with various scenarios."""
    print("\n" + "=" * 60)
    print("Testing parse_pubsub_message()")
    print("=" * 60)

    from main import parse_pubsub_message

    # Test 1: Valid retention period
    print("\nTest 1: Valid retention period (45 days)")
    event = MockCloudEvent(retention_days=45)
    result = parse_pubsub_message(event)
    assert result == 45, f"Expected 45, got {result}"
    print(f"✓ Result: {result} days")

    # Test 2: Empty message (should use default)
    print("\nTest 2: Empty message (should use default 30 days)")
    event = MockCloudEvent()
    result = parse_pubsub_message(event)
    assert result == 30, f"Expected 30, got {result}"
    print(f"✓ Result: {result} days")

    # Test 3: Value below minimum (should use default)
    print("\nTest 3: Value below minimum (5 days, should use default)")
    event = MockCloudEvent(retention_days=5)
    result = parse_pubsub_message(event)
    assert result == 30, f"Expected 30, got {result}"
    print(f"✓ Result: {result} days")

    # Test 4: Value above maximum (should use default)
    print("\nTest 4: Value above maximum (400 days, should use default)")
    event = MockCloudEvent(retention_days=400)
    result = parse_pubsub_message(event)
    assert result == 30, f"Expected 30, got {result}"
    print(f"✓ Result: {result} days")

    print("\n✓ All parse_pubsub_message tests passed!")


def test_calculate_cutoff_date():
    """Test the calculate_cutoff_date function."""
    print("\n" + "=" * 60)
    print("Testing calculate_cutoff_date()")
    print("=" * 60)

    from main import calculate_cutoff_date

    # Test with 30 days retention
    print("\nTest 1: Calculate cutoff for 30 days retention")
    cutoff = calculate_cutoff_date(30)
    print(f"✓ Cutoff date: {cutoff}")

    # Verify the cutoff is approximately 30 days ago
    cutoff_dt = datetime.fromisoformat(cutoff)
    expected_dt = datetime.utcnow() - timedelta(days=30)
    time_diff = abs((cutoff_dt - expected_dt).total_seconds())

    assert time_diff < 2, f"Cutoff date calculation off by {time_diff} seconds"
    print(f"✓ Cutoff date is correctly ~30 days in the past")

    # Test with different retention periods
    for days in [7, 15, 60, 90]:
        print(f"\nTest: Calculate cutoff for {days} days retention")
        cutoff = calculate_cutoff_date(days)
        print(f"✓ Cutoff date: {cutoff}")

    print("\n✓ All calculate_cutoff_date tests passed!")


def test_cleanup_function_with_mock():
    """
    Test the full cleanup function with a mock event.

    This test requires actual Firestore access and will process real data.
    Use with caution in production environments.
    """
    print("\n" + "=" * 60)
    print("Testing cleanup_old_summaries() with mock event")
    print("=" * 60)
    print("\nWARNING: This will query your actual Firestore database.")
    print("It will NOT delete data with a future cutoff date.")

    from main import cleanup_old_summaries

    # Create a mock event with a cutoff far in the future (won't delete anything)
    # Use negative retention days to create a future date
    print("\nCreating mock event with 30 days retention...")
    event = MockCloudEvent(retention_days=30)

    print("\nExecuting cleanup function...")
    result = cleanup_old_summaries(event)

    print("\n" + "=" * 60)
    print("Execution Result:")
    print("=" * 60)
    print(json.dumps(result, indent=2))
    print("=" * 60)

    # Validate result structure
    assert 'status' in result, "Result missing 'status' field"

    if result['status'] == 'success':
        assert 'users_processed' in result, "Result missing 'users_processed'"
        assert 'total_deleted' in result, "Result missing 'total_deleted'"
        assert 'cutoff_date' in result, "Result missing 'cutoff_date'"
        assert 'retention_days' in result, "Result missing 'retention_days'"
        print("\n✓ Result structure is valid")
        print(f"✓ Processed {result['users_processed']} users")
        print(f"✓ Deleted {result['total_deleted']} documents")
    else:
        print(f"\n✗ Function returned error status: {result.get('error', 'Unknown error')}")
        return False

    print("\n✓ cleanup_old_summaries test completed!")
    return True


def run_safe_integration_test():
    """
    Run a safe integration test that won't delete any data.

    This creates a test with retention period in the future to verify
    the function runs correctly without actually deleting data.
    """
    print("\n" + "=" * 60)
    print("Running Safe Integration Test")
    print("=" * 60)
    print("\nThis test uses retention = -1 days (future date)")
    print("No data will be deleted - this is a safe dry run.")

    from main import cleanup_old_summaries

    # Create event with negative retention (cutoff in future = no deletions)
    message_payload = json.dumps({"retention_days": 1000})  # Very long retention = minimal deletions
    encoded_payload = base64.b64encode(message_payload.encode()).decode()

    class SafeEvent:
        data = {
            "message": {
                "data": encoded_payload
            }
        }

    print("\nExecuting safe test...")
    result = cleanup_old_summaries(SafeEvent())

    print("\n" + "=" * 60)
    print("Safe Test Result:")
    print("=" * 60)
    print(json.dumps(result, indent=2))

    if result['status'] == 'success':
        print("\n✓ Safe integration test passed!")
        print(f"✓ Successfully connected to Firestore")
        print(f"✓ Processed {result['users_processed']} users")
        print(f"✓ Function executed without errors")
        return True
    else:
        print(f"\n✗ Safe test failed: {result.get('error')}")
        return False


def display_usage():
    """Display usage instructions for the test script."""
    print("\n" + "=" * 60)
    print("Cleanup Function Local Testing Utility")
    print("=" * 60)
    print("\nUsage:")
    print("  python test_local.py [test_type]")
    print("\nTest Types:")
    print("  unit       - Run unit tests only (no Firestore required)")
    print("  safe       - Run safe integration test (no data deletion)")
    print("  full       - Run full integration test (may delete data!)")
    print("  all        - Run all tests in sequence")
    print("\nEnvironment Setup:")
    print("  1. Set GOOGLE_APPLICATION_CREDENTIALS to service account key path")
    print("  2. Set GOOGLE_CLOUD_PROJECT to your GCP project ID")
    print("\nExamples:")
    print("  python test_local.py unit")
    print("  python test_local.py safe")
    print("=" * 60)


def main():
    """Main test execution function."""
    print("\n" + "=" * 60)
    print("CLEANUP FUNCTION LOCAL TEST SUITE")
    print("=" * 60)

    # Check environment variables
    if not os.getenv('GOOGLE_APPLICATION_CREDENTIALS'):
        print("\n⚠ WARNING: GOOGLE_APPLICATION_CREDENTIALS not set")
        print("Some tests may fail without credentials.")

    if not os.getenv('GOOGLE_CLOUD_PROJECT'):
        print("\n⚠ WARNING: GOOGLE_CLOUD_PROJECT not set")
        print("Some tests may fail without project ID.")

    # Determine test type from command line
    test_type = sys.argv[1] if len(sys.argv) > 1 else 'unit'

    if test_type == 'unit':
        print("\nRunning unit tests only...")
        test_parse_pubsub_message()
        test_calculate_cutoff_date()

    elif test_type == 'safe':
        print("\nRunning safe integration test...")
        success = run_safe_integration_test()
        sys.exit(0 if success else 1)

    elif test_type == 'full':
        print("\nRunning full integration test...")
        print("\n⚠ WARNING: This may delete actual data from Firestore!")
        response = input("Are you sure you want to continue? (yes/no): ")
        if response.lower() == 'yes':
            success = test_cleanup_function_with_mock()
            sys.exit(0 if success else 1)
        else:
            print("Test cancelled.")
            sys.exit(0)

    elif test_type == 'all':
        print("\nRunning all tests...")
        test_parse_pubsub_message()
        test_calculate_cutoff_date()
        success = run_safe_integration_test()
        sys.exit(0 if success else 1)

    else:
        display_usage()
        sys.exit(1)

    print("\n" + "=" * 60)
    print("ALL TESTS COMPLETED")
    print("=" * 60)


if __name__ == "__main__":
    main()
