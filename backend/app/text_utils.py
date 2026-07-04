"""표시용 텍스트 정규화 유틸 (US-007).

순수 함수 — 외부 의존 없음. 저장 데이터는 건드리지 않고 응답 계층에서만 쓴다.
"""

_DEFAULT_MAX_LEN = 60
_ELLIPSIS = " … "


def truncate_middle(text, max_len=_DEFAULT_MAX_LEN, ellipsis=_ELLIPSIS, tail_ratio=0.35):
    """길이 초과 시 앞 head + 중간 생략 + 뒤 tail 로 제목을 정규화한다.

    - "헤드라인 - 출처" 형태에서 앞(주제)과 뒤(출처)를 보존한다.
    - 문자(code point) 단위 슬라이스라 CJK 문자 중간이 깨지지 않는다.
    - text 가 None 이면 그대로, max_len 이하면 trim 만 하여 반환한다.
    - 결과 길이는 항상 max_len 이하다.
    """
    if text is None:
        return text
    text = text.strip()
    if len(text) <= max_len:
        return text
    budget = max_len - len(ellipsis)
    if budget <= 0:
        return text[:max_len]
    tail_len = max(1, int(budget * tail_ratio))
    head_len = max(1, budget - tail_len)
    head = text[:head_len].rstrip()
    tail = text[-tail_len:].lstrip()
    return f"{head}{ellipsis}{tail}"


def with_display_titles(results, max_len=_DEFAULT_MAX_LEN):
    """조회 결과 리스트의 title 을 표시용으로 정규화한다(응답 계층 전용).

    응답 dict 만 정규화하며 저장 데이터/원본은 변경하지 않는다.
    """
    if not results:
        return results
    for item in results:
        if isinstance(item, dict) and item.get("title") is not None:
            item["title"] = truncate_middle(item["title"], max_len)
    return results
