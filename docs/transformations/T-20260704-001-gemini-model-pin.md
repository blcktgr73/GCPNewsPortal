# Transformation: T-20260704-001 - Gemini Model Pin Update (3.1-flash-lite)

**Date**: 2026-07-04
**Status**: Completed
**Type**: Internal
**Issue**: [GCPNewsPortal #1](https://github.com/blcktgr73/GCPNewsPortal/issues/1)

## Intent
**Problem**:
- 실제 운영 요약 경로가 아직 `gemini-2.5-flash-lite`에 핀되어 있었다. 현재 작업 트랙은 Flash-Lite 타깃을 `gemini-3.1-flash-lite`로 통일 중.
- 모델명이 SDK 호출부와 raw REST URL에 리터럴로 박혀 있고, `backend`와 `news_summarizer` 두 곳에 중복되어 향후 드리프트 위험이 있었다.

**Solution**:
- 4개 생산 경로의 핀을 `gemini-3.1-flash-lite`로 교체.
- 각 모듈 상단에 `GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.1-flash-lite")` 기본 상수를 두어 파일당 핀을 1점화하고, 코드 수정 없이 env로 오버라이드 가능하게 함 (AC "defaults use"와 정합).
- raw REST URL은 f-string으로 `{GEMINI_MODEL}` 보간.

## Impact Analysis
- **Themes Affected**: News Consumption (Epic: News Summarization / US-006)
- **Structural Changes** (4 production paths):
    - `backend/services/gemini_service.py`: `GEMINI_MODEL` 상수 도입, SDK 모델 인자 참조.
    - `news_summarizer/services/gemini_service.py`: 동일 (중복 정렬 유지).
    - `backend/services/google_news.py`: `GEMINI_MODEL` 상수 + `API_URL` f-string 보간.
    - `news_summarizer/services/google_news.py`: 동일 (중복 정렬 유지).
- **Behavior / Cost Assumption Change**:
    - 요약 엔진이 `gemini-2.5-flash-lite` → `gemini-3.1-flash-lite`로 상향. 요약 품질·지연·토큰 단가 가정이 새 모델 기준으로 이동한다.
    - 기본값이 바뀌었으나 `GEMINI_MODEL` env로 구모델 롤백/핀 고정이 가능하다.

## Design Options (선택: B)
- **A. 리터럴 직접 교체** — 최소 diff, 그러나 핀이 호출부에 잔존해 드리프트 재발.
- **B. 모듈별 env-오버라이드 기본 상수 (선택)** — 파일당 핀 1점화 + env 오버라이드. "defaults use" AC와 정합, 패키지 독립성 유지.
- **C. 공용 config 단일 소스** — 최상의 단일 진리값이나 backend·news_summarizer copy-중복 구조상 공통 import 경로 확보가 취약.

## Verification (smoke)
- [x] 생산 경로에 `gemini-2.5-flash-lite` 잔여 없음 (grep).
- [x] 4개 파일 `py_compile` 통과.
- [x] AST 검증: 4개 파일 모두 기본 리터럴 `gemini-3.1-flash-lite`, REST 경로는 `{GEMINI_MODEL}:generateContent` 보간.
- [x] 동작 재현: `GEMINI_MODEL` 미설정 시 기본값, 설정 시 오버라이드가 모델명·URL에 반영됨.
- 주의: 이 환경엔 `bs4`/`google-generativeai` 미설치로 모듈 직접 import는 스킵, 동등 재현 smoke로 대체.
- [x] 라이브 확인(read-only ListModels, 실키): `gemini-3.1-flash-lite`가 `v1`/`v1beta` 모두에 존재. raw REST 경로가 쓰는 `/v1/models/...`에서 유효 → 핀 실제 작동 확인.
- 부수: 이번에 도입한 `GEMINI_MODEL` 오버라이드를 `backend/.env.example`, `news_summarizer/.env.example`에 문서화.

## Linked Acceptance Criteria (Issue #1)
- [x] production Gemini summarization defaults use `gemini-3.1-flash-lite`
- [x] raw REST `generateContent` endpoints and SDK model strings updated consistently
- [x] duplicated service paths (`backend`, `news_summarizer`) stay behaviorally aligned
- [x] at least one focused verification path passes (scripted smoke)
- [x] material behavior/cost assumption change documented (this file)
