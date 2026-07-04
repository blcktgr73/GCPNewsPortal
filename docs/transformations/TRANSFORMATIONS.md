# Transformation Log

| ID | Title | Date | Status | Description | User Stories |
|---|---|---|---|---|---|
| T-20231024-001 | Initial Code Review & Docs | 2023-10-24 | Completed | Initial codebase review and documentation generation based on CLAUDE.md principles. | N/A |
| T-20260209-001 | Gemini Grounding Integration | 2026-02-09 | Completed | Replaced deprecated Google News scraping with Gemini 1.5 Flash + Grounding (Google Search) for reliable 2-phase news summarization. | US-006 |
| T-20260704-001 | Gemini Model Pin Update (3.1-flash-lite) | 2026-07-04 | Completed | Updated production summarization model pin `gemini-2.5-flash-lite` → `gemini-3.1-flash-lite` across 4 paths (SDK + raw REST, backend + news_summarizer) via env-overridable `GEMINI_MODEL` default. Issue #1. | US-006 |
| T-20260704-002 | 표시 제목 중간 생략 정규화 | 2026-07-04 | Completed | 조회 API 응답 계층에서 요약 제목을 길이 제한 + 중간 생략(앞 … 뒤)으로 정규화(원본 저장 보존, 비파괴). `backend/app/text_utils.py` + main.py 2개 라우트. 12 단위테스트. | US-007 |
