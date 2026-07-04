"""Test: US-007 표시 제목 정규화 (`app.text_utils`).

Covers the acceptance criteria:
  - AC-007-2 길이 ≤ L 원본 그대로, 초과 시 앞 head … 뒤 tail 중간 생략, 결과 ≤ L
  - AC-007-3 "헤드라인 - 출처" 앞/뒤 보존, CJK 문자 경계 안전
  - with_display_titles 는 응답 dict 만 정규화(원본 필드 보존, 결측/빈 처리)

Style follows existing tests under `tests/` (unittest).
`app.text_utils` 는 외부 의존이 없어 firestore/firebase stub 없이 import 된다.
"""

import os
import sys
import unittest

BACKEND_DIR = os.path.join(os.path.dirname(__file__), "..", "backend")
sys.path.insert(0, os.path.abspath(BACKEND_DIR))

from app.text_utils import truncate_middle, with_display_titles  # noqa: E402


class TestTruncateMiddle(unittest.TestCase):
    def test_short_title_unchanged(self):
        self.assertEqual(truncate_middle("짧은 제목", max_len=60), "짧은 제목")

    def test_exactly_max_len_unchanged(self):
        text = "a" * 60
        self.assertEqual(truncate_middle(text, max_len=60), text)

    def test_none_passthrough(self):
        self.assertIsNone(truncate_middle(None))

    def test_whitespace_trimmed(self):
        self.assertEqual(truncate_middle("  hi  ", max_len=60), "hi")

    def test_long_title_gets_ellipsis_and_fits(self):
        text = (
            "USD pair of 40-year lows, why it matters and how it "
            "could shake US stocks and treasury bonds - Market Issues"
        )
        out = truncate_middle(text, max_len=60)
        self.assertIn("…", out)
        self.assertLessEqual(len(out), 60)

    def test_headline_and_source_preserved(self):
        # "헤드라인 - 출처" 형태: 앞(헤드라인 시작)과 뒤(출처)가 남아야 한다.
        text = "강달러 약세로 엔화 환율이 10년 만에 최저치를 기록했다는 장문의 헤드라인 - Chouzetsu"
        out = truncate_middle(text, max_len=40)
        self.assertLessEqual(len(out), 40)
        self.assertIn("…", out)
        self.assertTrue(out.startswith("강달러"))
        self.assertTrue(out.rstrip().endswith("Chouzetsu"))

    def test_cjk_no_broken_characters(self):
        # code point 슬라이스라 어떤 위치에서 잘라도 온전한 문자만 남는다.
        text = "円" * 200
        out = truncate_middle(text, max_len=50)
        self.assertLessEqual(len(out), 50)
        # 생략 기호/공백을 제외하면 온전한 '円' 문자만 남는다 (깨진 문자 없음)
        leftover = set(out) - {"円", " ", "…"}
        self.assertEqual(leftover, set())

    def test_custom_ellipsis_and_ratio(self):
        text = "x" * 100
        out = truncate_middle(text, max_len=20, ellipsis="...", tail_ratio=0.5)
        self.assertIn("...", out)
        self.assertLessEqual(len(out), 20)


class TestWithDisplayTitles(unittest.TestCase):
    def test_normalizes_title_only(self):
        long_title = "제목 " + "가" * 100 + " - 출처"
        results = [{"title": long_title, "url": "http://x", "summary": "본문"}]
        out = with_display_titles(results, max_len=30)
        self.assertLessEqual(len(out[0]["title"]), 30)
        self.assertIn("…", out[0]["title"])
        # 다른 필드는 보존
        self.assertEqual(out[0]["url"], "http://x")
        self.assertEqual(out[0]["summary"], "본문")

    def test_short_title_kept(self):
        results = [{"title": "짧다", "url": "u"}]
        out = with_display_titles(results, max_len=60)
        self.assertEqual(out[0]["title"], "짧다")

    def test_missing_or_none_title_ignored(self):
        results = [{"url": "u"}, {"title": None, "url": "v"}]
        out = with_display_titles(results, max_len=60)
        self.assertNotIn("title", out[0])
        self.assertIsNone(out[1]["title"])

    def test_empty_and_none_results(self):
        self.assertEqual(with_display_titles([]), [])
        self.assertIsNone(with_display_titles(None))


if __name__ == "__main__":
    unittest.main()
