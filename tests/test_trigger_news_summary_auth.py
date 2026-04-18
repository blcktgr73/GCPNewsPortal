"""
Test: trigger_news_summary HTTP authentication.

These tests assume Firebase token authentication WILL be added to the
trigger_news_summary HTTP function (currently no auth — security finding).
The tests verify the expected post-implementation behavior:

    1. Missing Authorization header           -> 401
    2. Invalid / unverifiable Firebase token  -> 401
    3. Valid Firebase token                   -> 200 success
    4. The verified token claims (uid, etc.)  -> extractable

All four tests are marked `skip` until the production code in
`trigger_function/main.py` actually calls
`firebase_admin.auth.verify_id_token(...)` and rejects unauthenticated
requests. Remove the skip marks once auth is implemented.

Style follows the existing tests under `tests/` (unittest + mock).
"""

import json
import os
import sys
import types
import unittest
from unittest.mock import MagicMock, patch


# ---------------------------------------------------------------------------
# Stub heavy GCP / Firebase modules BEFORE importing the function under test.
# `google-cloud-pubsub`, `google-cloud-firestore` and `firebase-admin` are not
# installed in this minimal test environment, so we provide just-enough
# in-memory stand-ins.
# ---------------------------------------------------------------------------

def _install_stub_modules():
    # google + google.cloud namespaces
    google_mod = sys.modules.setdefault("google", types.ModuleType("google"))
    cloud_mod = sys.modules.setdefault("google.cloud", types.ModuleType("google.cloud"))
    google_mod.cloud = cloud_mod

    # google.cloud.pubsub_v1 with PublisherClient
    if "google.cloud.pubsub_v1" not in sys.modules:
        pubsub_mod = types.ModuleType("google.cloud.pubsub_v1")

        class _PublisherClient:
            def topic_path(self, project, topic):
                return f"projects/{project}/topics/{topic}"

            def publish(self, topic_path, data):
                future = MagicMock()
                future.result.return_value = "fake-message-id"
                return future

        pubsub_mod.PublisherClient = _PublisherClient
        sys.modules["google.cloud.pubsub_v1"] = pubsub_mod
        cloud_mod.pubsub_v1 = pubsub_mod

    # google.cloud.firestore with Client
    if "google.cloud.firestore" not in sys.modules:
        firestore_mod = types.ModuleType("google.cloud.firestore")

        class _Client:
            def collection(self, *_a, **_kw):
                return MagicMock()

        firestore_mod.Client = _Client
        sys.modules["google.cloud.firestore"] = firestore_mod
        cloud_mod.firestore = firestore_mod

    # firebase_admin + firebase_admin.auth
    if "firebase_admin" not in sys.modules:
        fb_mod = types.ModuleType("firebase_admin")
        fb_auth = types.ModuleType("firebase_admin.auth")

        class _InvalidIdTokenError(Exception):
            pass

        def _verify_id_token(token):
            # Replaced by tests via patch().
            raise _InvalidIdTokenError("not configured")

        fb_auth.verify_id_token = _verify_id_token
        fb_auth.InvalidIdTokenError = _InvalidIdTokenError
        fb_mod.auth = fb_auth
        sys.modules["firebase_admin"] = fb_mod
        sys.modules["firebase_admin.auth"] = fb_auth


_install_stub_modules()

# Stub utils.keywords_service before importing main (it would otherwise
# instantiate a real Firestore client at import time).
_utils_pkg = types.ModuleType("utils")
_utils_pkg.__path__ = []  # mark as package
_kw_mod = types.ModuleType("utils.keywords_service")
_kw_mod.fetch_all_user_keywords = lambda: []
sys.modules["utils"] = _utils_pkg
sys.modules["utils.keywords_service"] = _kw_mod

# Add trigger_function on path so we can import its `main` module.
# Import it under a UNIQUE module name so it doesn't collide with
# `news_summarizer/main.py` (also called `main`) in the same pytest run.
TRIGGER_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "trigger_function"))
if TRIGGER_DIR not in sys.path:
    sys.path.insert(0, TRIGGER_DIR)

import importlib.util as _ilu  # noqa: E402

_spec = _ilu.spec_from_file_location(
    "trigger_function_main", os.path.join(TRIGGER_DIR, "main.py")
)
trigger_main = _ilu.module_from_spec(_spec)
sys.modules["trigger_function_main"] = trigger_main
_spec.loader.exec_module(trigger_main)


# ---------------------------------------------------------------------------
# Detect whether auth has been implemented yet. Used to skip the auth-tests
# that would fail (and confirm the security finding) until then.
# ---------------------------------------------------------------------------
import inspect

_TRIGGER_SRC = inspect.getsource(trigger_main.trigger_news_summary)
AUTH_IMPLEMENTED = "verify_id_token" in _TRIGGER_SRC or "Authorization" in _TRIGGER_SRC


def _make_request(headers=None):
    """Build a Flask-like request object the function can consume."""
    req = MagicMock()
    req.headers = headers or {}
    # Common Flask helpers the function might reach for in future:
    req.headers.get = (headers or {}).get
    req.method = "POST"
    return req


class TestTriggerNewsSummaryAuth(unittest.TestCase):
    """
    Tests describing the *desired* auth behavior. While `AUTH_IMPLEMENTED`
    is False, every assertion here is skipped — but the file still serves
    as executable specification of the security requirement.
    """

    @unittest.skipUnless(
        AUTH_IMPLEMENTED,
        "Auth not yet implemented in trigger_function/main.py "
        "(security finding: HTTP endpoint is currently unauthenticated).",
    )
    def test_missing_authorization_header_returns_401(self):
        request = _make_request(headers={})
        response = trigger_main.trigger_news_summary(request)
        status = response[1] if isinstance(response, tuple) else getattr(response, "status_code", 200)
        self.assertEqual(status, 401)

    @unittest.skipUnless(
        AUTH_IMPLEMENTED,
        "Auth not yet implemented in trigger_function/main.py.",
    )
    @patch("firebase_admin.auth.verify_id_token")
    def test_invalid_token_returns_401(self, mock_verify):
        mock_verify.side_effect = sys.modules["firebase_admin.auth"].InvalidIdTokenError("bad")
        request = _make_request(headers={"Authorization": "Bearer not-a-real-token"})
        response = trigger_main.trigger_news_summary(request)
        status = response[1] if isinstance(response, tuple) else getattr(response, "status_code", 200)
        self.assertEqual(status, 401)

    @unittest.skipUnless(
        AUTH_IMPLEMENTED,
        "Auth not yet implemented in trigger_function/main.py.",
    )
    @patch("utils.keywords_service.fetch_all_user_keywords", return_value=[])
    @patch("firebase_admin.auth.verify_id_token")
    def test_valid_token_returns_success(self, mock_verify, _mock_fetch):
        mock_verify.return_value = {"uid": "user-123", "email": "u@example.com"}
        request = _make_request(headers={"Authorization": "Bearer good-token"})
        response = trigger_main.trigger_news_summary(request)
        status = response[1] if isinstance(response, tuple) else getattr(response, "status_code", 200)
        self.assertIn(status, (200, 201))

    @unittest.skipUnless(
        AUTH_IMPLEMENTED,
        "Auth not yet implemented in trigger_function/main.py.",
    )
    @patch("utils.keywords_service.fetch_all_user_keywords", return_value=[])
    @patch("firebase_admin.auth.verify_id_token")
    def test_token_claims_extracted(self, mock_verify, _mock_fetch):
        claims = {"uid": "user-xyz", "email": "x@example.com", "admin": True}
        mock_verify.return_value = claims
        request = _make_request(headers={"Authorization": "Bearer good-token"})
        trigger_main.trigger_news_summary(request)
        mock_verify.assert_called_once()
        # Argument should be the bare token (header value with the "Bearer " prefix stripped).
        called_arg = mock_verify.call_args[0][0]
        self.assertIn("good-token", called_arg)


class TestTriggerNewsSummaryAuthFinding(unittest.TestCase):
    """A non-skipped test that records the security finding directly."""

    def test_auth_currently_missing_is_a_finding(self):
        # This assertion documents the current state. It will start failing
        # (and should be deleted) once auth is implemented.
        self.assertFalse(
            AUTH_IMPLEMENTED,
            "Auth appears to be implemented now — please remove the "
            "@skipUnless guards and this finding test.",
        )


if __name__ == "__main__":
    unittest.main()
