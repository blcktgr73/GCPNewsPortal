# GCPNewsPortal — Agent / Coding Guide

> 이 프로젝트에서 사람(Codex/Claude/OpenClaw)과 bot 이 공통으로 따르는 규약의 정본(canonical).
> `AGENTS.md` 를 기준으로 하고, `CLAUDE.md` 는 기존 확장 가이드를 유지한다.
>
> cross-project 표준은 palab-platform 을 source-of-truth 로 참조한다.

## 스택 / 구조

- Backend: FastAPI (`backend/`)
- Batch / summarization: Cloud Functions (`news_summarizer/`, `trigger_function/`, `cleanup_function/`)
- Frontend: Expo / React Native (`frontend/`)
- Infra target: GCP Cloud Run, Cloud Functions, Firestore, Scheduler, Pub/Sub

## 작업 규약

- branch/tag/PR: palab-platform [git-workflow](https://github.com/blcktgr73/palab-platform/blob/main/policies/git-workflow.md)
- 전체 흐름(아이디어→릴리즈, 채널·dispatch·핸드오프·실패 복구 규약): palab-platform [delivery-lifecycle](https://github.com/blcktgr73/palab-platform/blob/main/docs/operations/delivery-lifecycle.md) 를 정본으로 따른다. 조율은 GitHub 이슈+`dispatch:` 라벨, Discord 는 깨우기 전송·사람요약만.
- 착수/추적: `PALab Ops Kanban` 카드 또는 이 repo issue (`Owner`/`Type`/`Blocker` 필수)
- 이 repo 는 deploy 대상이다. **`push 성공` ≠ `배포 완료`**
- Dev 검증은 `verify-ac`, 실서비스 반영 확인은 `deployment-verify` 로 분리한다.
- 한국어 문서·리포트·커밋은 palab-platform [ko-writing-style](https://github.com/blcktgr73/palab-platform/blob/main/policies/ko-writing-style.md) 을 따른다.

## 보안 경계

- 비밀은 커밋하지 않는다 (`.env*`, GCP key, Firebase credential)
- `frontend/` 같은 클라이언트 번들에 비밀을 넣지 않는다
- GCP 서비스 계정, Firestore 데이터, Pub/Sub trigger 권한 변경은 승인 경계를 유지한다

## bot 자율 실행 시

- 외부 발신·배포·권한 변경·secret 변경·결제는 승인 경계를 유지한다
- 모르는 것은 추정하지 말고 "확인 필요"로 남긴다
- 중요한 결정은 issue/PR/doc 중 하나로 승격한다

## Spec 추적 (Transformation-Centered Development)

이 repo 는 이미 자체 문서 구조를 사용한다. bootstrap 은 그 구조를 보존한 채 접합한다.

- PRD: `docs/specs/PRD.md`
- User Story Map: `docs/specs/user-stories/index.md`
- Theme/Story 상세: `docs/specs/user-stories/*.md`
- Verification evidence: `docs/guides/VERIFICATION.md`
- Transformation Log: `docs/transformations/TRANSFORMATIONS.md`
- 템플릿: `docs/templates/{THEME,USER_STORY,TRANSFORMATION}_TEMPLATE.md`

요구사항은 Theme(Concept) > Epic > Story > AC 흐름으로 다루고, 변경은 작은 Transformation(`T-YYYYMMDD-###`) 단위로 만든다.
기준: palab-platform [transformation-centered-development](https://github.com/blcktgr73/palab-platform/blob/main/docs/operations/transformation-centered-development.md), [user-story-verification-governance](https://github.com/blcktgr73/palab-platform/blob/main/docs/operations/user-story-verification-governance.md).

## Skills

표준/반복 절차는 `ops/skills/*.md` 에 둔다.

- `ops/skills/story-authoring.md`
- `ops/skills/transformation.md`
- `ops/skills/verify-ac.md`
- `ops/skills/deployment-verify.md`
- `ops/skills/security-baseline.md`
- `ops/skills/kanban-sweep.md`
- `ops/skills/acp-claude.md` — **(OpenClaw 코딩 봇)** dispatched(webhook 트리거) **코딩** 작업은 직접 코딩하지 말고 이 절차대로 Claude Code(ACP)에 위임한다 (`acp claude 사용해서 진행해줘`). 조회·요약만이면 직접 처리.
- `ops/skills/change-closeout.md` — **(OpenClaw 전용)** 변경(문서·정책·코드)을 브랜치→PR→머지→main 반영 확인까지 태운다. **머지는 사람 승인 경계**(봇 자동 머지 금지). PR 만 만들고 멈추는 것 방지.
> **dispatched 실행**: `dispatch:<봇>` 로 깨어난 **코딩** 작업이면, OpenClaw 는 직접 코딩하지 말고 `acp-claude` 절차대로 **Claude Code(ACP)에 위임**한다 (프롬프트에 `acp claude 사용해서 진행해줘`). 라우터가 코딩 route 에 이 문구를 이미 붙여 보낼 수도 있다(중복 무해). 조회·요약만이면 직접 처리.
> **dispatched 마무리**: 커밋만 남기고 끝내지 않는다. **push → PR 생성(`Refs #N` + 남은 항목) → 카드에 PR 링크 댓글 → 카드에 `awaiting-review` 라벨**까지가 한 건이다. `awaiting-review` 가 라우터의 **완료→리뷰 핸드오프**를 발화해 요청자(Neo)를 재기동한다(design §5). **봇이 스스로 카드를 닫지 않는다** — 완료 판정·카드 닫기는 Neo 가 verify-ac 후 `github-project-closeout` 계약대로 한다. 여기서 멈춘 카드는 라우터의 정체(dead-letter) 감지에 잡힌다.
> **단, 코디네이터(Neo)가 자기 카드(`dispatch:neo`)를 끝내면 `awaiting-review` 를 붙이지 않고 직접 닫는다(#42).** 핸드오프는 worker→코디네이터 전용이라, Neo 가 자기에게 넘기면 무한 self-loop 가 된다(라우터도 이 경우를 `self-handoff` 로 막지만, 원천은 여기서 막는다).
- `ops/skills/issue-intake.md` — **(Neo·Kusanagi 전용)** 새로 드러난 할 일을 GitHub issue 로 등록하고, 필요하면 `dispatch:<봇>` 라벨로 다른 봇에게 넘긴다. 다른 봇에게 업무를 넘길 때는 카드를 먼저 만든다.

흐름:
`story-authoring` → `transformation` → `verify-ac`

런타임 어댑터:

- Claude Code → `.claude/skills/<name>/SKILL.md`
- Codex / OpenClaw → `.codex/skills/<name>/SKILL.md`

## 반복 작업 (cron)

- 정기 작업은 cron 이 skill/command 를 호출하는 구조를 따른다
- 절차는 skill 에, 스케줄은 각 bot 런타임 cron 에 둔다

## 프로젝트 고유 규칙

- 구현 전 `docs/guidelines/WORKFLOW.md` 와 `docs/guidelines/CODING_STANDARDS.md` 를 확인한다
- 배포/운영 확인은 기존 `docs/guides/VERIFICATION.md` 와 새 `docs/specs/DEPLOYMENT_VERIFICATION.md` 를 함께 본다
