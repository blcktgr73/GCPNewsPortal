# Transformation: T-20260704-002 - 표시 제목 중간 생략 정규화 (US-007)

**Date**: 2026-07-04
**Status**: Completed
**Type**: User-facing (표시 계층)
**Story**: US-007 (News Consumption)

## Intent
**Problem**:
- 저장된 요약의 `title`이 RSS 제목을 LLM이 echo한 값이라 "헤드라인 - 출처" 형태로 길고, 꼬리에 출처가 붙어 지저분하게 노출됨(스크린샷의 "… - Market Iss", "… - Chouzetsu").
- 제목 표시를 규율하는 계약이 없었음.

**Solution**:
- 원본 제목은 저장에서 그대로 보존(비파괴). **조회 API 응답 계층에서만** 표시용으로 정규화.
- 길이 초과 시 앞 head + 중간 생략(`…`) + 뒤 tail 로 헤드라인·출처를 함께 보존. 문자(code point) 단위 슬라이스로 CJK 안전.

## Impact Analysis
- **Themes Affected**: News Consumption (US-007)
- **Structural Changes**:
    - `backend/app/text_utils.py` (신규): 순수 유틸 `truncate_middle`, 응답 헬퍼 `with_display_titles`. 외부 의존 없음.
    - `backend/app/main.py`: `/summaries`, `/summaries/paginated` 응답에 `with_display_titles` 적용(단일 적용점).
    - `tests/test_title_truncate.py` (신규): 12 테스트.
- **비파괴**: Firestore 저장 데이터·스키마 변경 없음. 응답 dict 만 정규화.

## Design (선택 근거)
- 대안 중 "저장 시 절단" 대신 **"원본 저장 + 응답 계층 정규화"** 선택 — 원본 보존(가역), 소비 경로가 백엔드 API 1곳뿐이라 단일 적용점으로 충분.
- 무거운 품질 파이프라인(LLM-judge/본문 fetch/저장 차단, 구 US-007 heavy안)은 과하다고 판단해 **대체**. 본문 요약 품질 검증은 범위 외 follow-up으로 남김.

## Verification
- [x] `python -m unittest tests.test_title_truncate` → 12/12 통과.
- [x] `py_compile` backend/app/main.py, text_utils.py.
- [x] AC-007-2/3 은 테스트로 직접 증명(길이 ≤ L, `…` 포함, 헤드라인·출처 보존, CJK 무손상). AC-007-1/4/5 는 코드로 증명(저장 미변경, 응답 1곳 적용, 표시 한정).
- 주의: FastAPI 실앱 E2E 는 로컬에 fastapi/firebase 미설치로 스킵(유틸+응답헬퍼 단위 검증으로 대체). 배포 후 인증 토큰 확보 시 `/summaries` 실호출 스모크 가능.

## Follow-ups (범위 외)
1. 제목을 LLM echo 대신 RSS 에서 결정적으로 취득해 저장(오류원·토큰 절감).
2. 본문 요약 품질 검증(구 US-007 heavy안) — 필요 시 별도 카드.
3. 튜닝: 최대 길이 L(기본 60), head/tail 비율, 생략 기호.
