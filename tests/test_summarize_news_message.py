"""
Test: summarize_news Pub/Sub message handler.

Covers behavior of `news_summarizer.main.summarize_news`:

    - Valid base64-encoded JSON payload   -> processed normally
    - Malformed JSON                      -> raises (logged, not silent crash)
    - Empty payload                       -> raises ValueError
    - Missing required fields (user_id /  -> raises ValueError with clear msg
      keyword)

Style follows the existing tests under `tests/` (unittest + mock).
Heavy GCP modules (firestore) are stubbed via `sys.modules`.
"""

import base64
import json
import os
import sys
import types
import unittest
from unittest.mock import MagicMock, patch


# ---------------------------------------------------------------------------
# Stub `google.cloud.firestore` before importing the production module so
# that `summary_service.py`'s top-level `db = firestore.Client()` succeeds.
# ---------------------------------------------------------------------------
def _install_stub_firestore():
    google_mod = sys.modules.setdefault("google", types.ModuleType("google"))
    cloud_mod = sys.modules.setdefault("google.cloud", types.ModuleType("google.cloud"))
    google_mod.cloud = cloud_mod
    if "google.cloud.firestore" not in sys.modules:
        firestore_mod = types.ModuleType("google.cloud.firestore")

        class _Client:
            def collection(self, *_a, **_kw):
                return MagicMock()

        firestore_mod.Client = _Client
        sys.modules["google.cloud.firestore"] = firestore_mod
        cloud_mod.firestore = firestore_mod


_install_stub_firestore()

# Add news_summarizer onto sys.path so we can import its `main` and
# `services` packages. We import the function module under a UNIQUE name to
# avoid colliding with `trigger_function/main.py` (also named `main`) when
# multiple test files run in the same pytest session.
NEWS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "news_summarizer"))
if NEWS_DIR not in sys.path:
    sys.path.insert(0, NEWS_DIR)

import importlib.util as _ilu  # noqa: E402

_spec = _ilu.spec_from_file_location(
    "news_summarizer_main", os.path.join(NEWS_DIR, "main.py")
)
news_main = _ilu.module_from_spec(_spec)
sys.modules["news_summarizer_main"] = news_main
_spec.loader.exec_module(news_main)


def _event(payload_dict_or_bytes):
    """Build a Pub/Sub-style event dict accepted by `summarize_news`."""
    if isinstance(payload_dict_or_bytes, (dict, list)):
        raw = json.dumps(payload_dict_or_bytes).encode("utf-8")
    elif isinstance(payload_dict_or_bytes, str):
        raw = payload_dict_or_bytes.encode("utf-8")
    else:
        raw = payload_dict_or_bytes  # already bytes
    return {"data": base64.b64encode(raw)}


class TestSummarizeNewsMessage(unittest.TestCase):

    @patch("news_summarizer_main.summarize_and_store")
    def test_valid_payload_dispatches_to_summarize_and_store(self, mock_store):
        event = _event({"user_id": "user-1", "keyword": "Gemini"})
        news_main.summarize_news(event, context=None)
        mock_store.assert_called_once_with(user_id="user-1", keyword="Gemini")

    @patch("news_summarizer_main.summarize_and_store")
    def test_malformed_json_raises_json_decode_error(self, mock_store):
        # Invalid JSON inside an otherwise valid base64 envelope.
        event = _event("this is not json {{{")
        with self.assertRaises(json.JSONDecodeError):
            news_main.summarize_news(event, context=None)
        mock_store.assert_not_called()

    @patch("news_summarizer_main.summarize_and_store")
    def test_empty_payload_is_rejected(self, mock_store):
        event = _event({})  # base64-encoded "{}"
        with self.assertRaises(ValueError) as ctx:
            news_main.summarize_news(event, context=None)
        self.assertIn("Invalid message", str(ctx.exception))
        mock_store.assert_not_called()

    @patch("news_summarizer_main.summarize_and_store")
    def test_missing_user_id_is_rejected(self, mock_store):
        event = _event({"keyword": "Gemini"})
        with self.assertRaises(ValueError) as ctx:
            news_main.summarize_news(event, context=None)
        self.assertIn("Invalid message", str(ctx.exception))
        mock_store.assert_not_called()

    @patch("news_summarizer_main.summarize_and_store")
    def test_missing_keyword_is_rejected(self, mock_store):
        event = _event({"user_id": "user-1"})
        with self.assertRaises(ValueError) as ctx:
            news_main.summarize_news(event, context=None)
        self.assertIn("Invalid message", str(ctx.exception))
        mock_store.assert_not_called()

    @patch("news_summarizer_main.summarize_and_store")
    def test_non_base64_data_raises(self, mock_store):
        # Completely invalid base64 should raise — the function should not
        # silently swallow the error.
        bad_event = {"data": b"!!!not-base64!!!"}
        with self.assertRaises(Exception):
            news_main.summarize_news(bad_event, context=None)
        mock_store.assert_not_called()


if __name__ == "__main__":
    unittest.main()
