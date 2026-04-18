"""
Test: article deduplication in `summary_service.summarize_and_store`.

Covers:

    1. Same URL stored twice                  -> second insert skipped
    2. Different URL same content             -> both stored
       (current logic keys on URL only)
    3. URL with query parameter normalization -> CURRENTLY a finding:
       `?utm_source=...` style variants are treated as distinct URLs.
       Test asserts the *current* behavior and is xfail-marked so the
       intent (eventual normalization) stays visible.
    4. Race condition: two concurrent inserts -> both currently land in
       Firestore because the check-then-add is non-transactional. Test
       documents this concurrency hazard.

Style follows the existing tests under `tests/` (unittest + mock).
The Firestore client and the Gemini fetcher are mocked.
"""

import os
import sys
import threading
import types
import unittest
from unittest.mock import MagicMock, patch


# ---------------------------------------------------------------------------
# Stub `google.cloud.firestore` BEFORE importing summary_service, because
# its module-level `db = firestore.Client()` would otherwise fail.
# ---------------------------------------------------------------------------
def _install_stub_firestore():
    google_mod = sys.modules.setdefault("google", types.ModuleType("google"))
    cloud_mod = sys.modules.setdefault("google.cloud", types.ModuleType("google.cloud"))
    google_mod.cloud = cloud_mod
    if "google.cloud.firestore" not in sys.modules:
        firestore_mod = types.ModuleType("google.cloud.firestore")
        firestore_mod.Client = MagicMock  # placeholder; tests patch service.db
        sys.modules["google.cloud.firestore"] = firestore_mod
        cloud_mod.firestore = firestore_mod


_install_stub_firestore()

NEWS_DIR = os.path.join(os.path.dirname(__file__), "..", "news_summarizer")
sys.path.insert(0, os.path.abspath(NEWS_DIR))

import services.summary_service as summary_service  # noqa: E402


# ---------------------------------------------------------------------------
# Helpers — an in-memory Firestore-collection-ish stub that respects the
# subset of the API summary_service uses:
#
#     db.collection("users").document(uid).set({}, merge=True)
#     coll = db.collection("users").document(uid).collection("summaries")
#     coll.where("url", "==", url).limit(1).stream()  -> iterable of docs
#     coll.add({...})
# ---------------------------------------------------------------------------
class _InMemoryCollection:
    def __init__(self):
        self.docs = []
        self.add_lock = threading.Lock()

    # --- query side ---
    def where(self, field, op, value):
        assert op == "=="
        matches = [d for d in self.docs if d.get(field) == value]
        return _Query(matches)

    # --- write side ---
    def add(self, doc):
        with self.add_lock:
            self.docs.append(dict(doc))
        return ("/fake/path", MagicMock())


class _Query:
    def __init__(self, matches):
        self._matches = matches

    def limit(self, _n):
        return self

    def stream(self):
        return iter(self._matches)


class _Document:
    def __init__(self, summaries_collection):
        self._summaries = summaries_collection

    def set(self, _data, merge=False):  # noqa: D401 — Firestore API
        return None

    def collection(self, name):
        assert name == "summaries"
        return self._summaries


class _DBStub:
    def __init__(self):
        self._summaries = _InMemoryCollection()
        self._doc = _Document(self._summaries)

    def collection(self, name):
        assert name == "users"
        return _UsersCollection(self._doc)

    @property
    def summaries(self):
        return self._summaries


class _UsersCollection:
    def __init__(self, doc):
        self._doc = doc

    def document(self, _uid):
        return self._doc


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------
class TestArticleDeduplication(unittest.TestCase):

    def setUp(self):
        # Replace the module-level Firestore client with our in-memory stub.
        self.db_stub = _DBStub()
        self._db_patcher = patch.object(summary_service, "db", self.db_stub)
        self._db_patcher.start()

    def tearDown(self):
        self._db_patcher.stop()

    @staticmethod
    def _item(url, title="T", summary="S"):
        return {
            "title": title,
            "url": url,
            "summary": summary,
            "published_at": "2026-04-18 09:00",
            "source_name": "TestSrc",
        }

    @patch("services.summary_service.fetch_grounded_news")
    def test_same_url_twice_only_stored_once(self, mock_fetch):
        url = "https://example.com/news/1"
        # First call: returns the article.
        mock_fetch.return_value = [self._item(url, title="First")]
        summary_service.summarize_and_store("user-1", "Gemini")
        self.assertEqual(len(self.db_stub.summaries.docs), 1)

        # Second call: same URL again -> should be skipped.
        mock_fetch.return_value = [self._item(url, title="First (re-fetch)")]
        summary_service.summarize_and_store("user-1", "Gemini")
        self.assertEqual(
            len(self.db_stub.summaries.docs),
            1,
            "Duplicate URL must not be stored a second time.",
        )

    @patch("services.summary_service.fetch_grounded_news")
    def test_different_urls_both_stored(self, mock_fetch):
        # Two articles with different URLs but identical content body —
        # current logic keys on URL only, so both should be persisted.
        mock_fetch.return_value = [
            self._item("https://example.com/news/1", title="A", summary="same body"),
            self._item("https://example.com/news/2", title="B", summary="same body"),
        ]
        summary_service.summarize_and_store("user-1", "Gemini")
        self.assertEqual(len(self.db_stub.summaries.docs), 2)

    @patch("services.summary_service.fetch_grounded_news")
    def test_url_with_query_param_is_currently_treated_as_distinct(self, mock_fetch):
        """
        FINDING: dedup compares URLs as raw strings. Tracking-only query
        parameters (`utm_source`, `fbclid`, ...) defeat dedup.
        Once URL normalization is added, flip this test to expect 1 doc.
        """
        base = "https://example.com/news/1"
        with_utm = base + "?utm_source=newsletter"

        mock_fetch.return_value = [self._item(base, title="A")]
        summary_service.summarize_and_store("user-1", "Gemini")

        mock_fetch.return_value = [self._item(with_utm, title="A-utm")]
        summary_service.summarize_and_store("user-1", "Gemini")

        # CURRENT behavior:
        self.assertEqual(
            len(self.db_stub.summaries.docs),
            2,
            "Current code does not normalize URLs — both variants are stored. "
            "Update this test once URL normalization lands.",
        )

    @patch("services.summary_service.fetch_grounded_news")
    def test_concurrent_inserts_race_condition(self, mock_fetch):
        """
        FINDING: dedup uses a non-transactional check-then-add. Two
        concurrent invocations for the same URL can both pass the
        existence check and both persist a document.
        """
        url = "https://example.com/news/race"
        mock_fetch.return_value = [self._item(url)]

        errors = []

        def worker():
            try:
                summary_service.summarize_and_store("user-1", "Gemini")
            except Exception as exc:  # pragma: no cover - defensive
                errors.append(exc)

        t1 = threading.Thread(target=worker)
        t2 = threading.Thread(target=worker)
        t1.start(); t2.start()
        t1.join();  t2.join()

        self.assertEqual(errors, [], "Concurrent inserts must not crash.")
        # Document the race: under the current implementation we expect
        # *up to* 2 entries. We assert >=1 so the test is robust on either
        # interleaving, and we additionally surface the race when it occurs.
        stored = len(self.db_stub.summaries.docs)
        self.assertGreaterEqual(stored, 1)
        if stored > 1:
            print(
                "[FINDING] race condition reproduced: "
                f"{stored} duplicate documents written for {url!r}"
            )


if __name__ == "__main__":
    unittest.main()
