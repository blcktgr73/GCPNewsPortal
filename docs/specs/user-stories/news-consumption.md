# Theme: News Consumption

## Overview
Users consume personalized news summaries based on keywords they define.

## State
- **User Keywords**: List of strings (e.g., ["Politics", "Technology"]).
- **News Summaries**: List of summary objects (Title, Body, Source, Created At).

## Actions
- `addKeyword(keyword)`: Subscribes user to a new keyword.
- `removeKeyword(keywordId)`: Unsubscribes user from a keyword.
- `fetchSummaries()`: Retrieves latest summaries.
- `listKeywords()`: Retrieves subscribed keywords.
- `normalizeTitle(title)`: 응답 처리 시 제목을 표시용으로 정규화(길이 제한 + 중간 생략). 저장 데이터는 불변.

## Operational Principle
- Users subscribe to keywords -> System triggers fetch -> System stores summaries (원본 제목 보존) -> **조회 API가 표시용 제목을 정규화하여 반환** -> Users view summaries.

## Invariants
- 요약의 **원본 제목은 저장 시 변형되지 않는다**(비파괴). 정규화는 응답 계층에서만 일어난다.
- 조회 API가 반환하는 표시 제목은 최대 길이 이내이며, 초과 시 앞 일부 + 중간 생략(…) + 뒤 일부로 헤드라인과 출처를 보존한다.
- 요약 문서 스키마는 `grounding_v1`(title, url, summary, keyword, published_at, source_name, created_at, summaryTokens, type)을 따른다.

## User Stories
### Epic: News Summarization
- [x] US-001: As a user, I want to add keywords to receive personalized news summaries.
- [x] US-002: As a user, I want to view a list of my subscribed keywords.
- [x] US-003: As a user, I want to delete keywords I am no longer interested in.
- [x] US-004: As a user, I want to view my news summaries.
- [x] US-005: As a user, I want to browse paginated summaries for efficiency.
- [x] US-006: As a user, I want the system to automatically summarize news for my keywords.
- [x] US-007: As a user, I want long/messy summary titles shown truncated with a middle ellipsis, so I don't see the bloated raw "headline - source" title in full. `[T-20260704-002]`
  - [x] AC-007-1 (원본 보존): 원본 제목(RSS 제목)은 Firestore에 그대로 저장되며 저장 시 절단하지 않는다(비파괴).
  - [x] AC-007-2 (응답 정규화): summaries 조회 API 응답은 표시용 정규화 제목을 제공한다. 길이 ≤ L 이면 원본 그대로, 초과 시 `앞 head … 뒤 tail` 형태로 중간 생략.
  - [x] AC-007-3 (경계 보존): "헤드라인 - 출처" 형태에서 앞(헤드라인 시작)과 뒤(출처)를 보존한다. CJK 문자 경계에서 안전하게 절단(문자 중간 깨짐 없음).
  - [x] AC-007-4 (단일 적용점): 정규화는 백엔드 조회 API 응답 계층 1곳에 적용한다(현재 유일 소비 경로; 프론트 제거됨).
  - [x] AC-007-5 (범위): 표시 제목 정규화에 한정. 본문 요약 품질 검증(환각·혼합언어 등)은 이 스토리 범위 외.

> 검증: `tests/test_title_truncate.py` (12 통과) + `backend/app/text_utils.py`, `main.py` 응답 적용. Transformation: `[T-20260704-002]`.

> 튜닝 파라미터(구현 시 확정): 최대 길이 L, head/tail 비율, 생략 기호(`…`).
> Follow-up 후보(범위 외): ① 제목을 LLM echo 대신 RSS에서 결정적으로 취해 저장(오류원·토큰 절감), ② 본문 요약 품질 검증(구 US-007 heavy안).
