# Skill: acp-claude

> dispatched(GitHub webhook 트리거) 코딩 작업을 **Claude Code(ACP)** 에 위임해 실행한다.
> OpenClaw = 지휘·중계, Claude Code(ACP) = 실행기. **OpenClaw 전용 스킬** (`.codex`/`.claude` 어댑터 없음 —
> Claude 런타임은 자기가 실행기라 무의미, Codex 는 대상 아님).
> 판단 기준·트리거/승인 규약은 palab-platform 을 참조한다 (여기 복제하지 않는다).
> spec: palab-platform `docs/operations/event-driven-trigger-design.md` (트리거·승인 경계).

## 언제 실행

- `dispatch:<봇>` 라벨로 깨어난 **코딩/구현/변경** 작업. 조회·요약만이면 대상 아님(직접 처리).

## 입력

- dispatched 카드: 이슈 title / 본문 / AC / `html_url`. 대상 repo(+브랜치).
- **전제**: OpenClaw 에 `gh` 가 인증돼 있어야 한다(repo 준비용). 작업 repo 는 acp 워크스페이스 아래
  **`prj/<repo>`** 에 둔다 (예: `/root/.openclaw/workspace-claude/prj/<repo>`).

## 절차

1. **대상 repo 준비** — 작업 경로는 `<워크스페이스>/prj/<repo>`.
   - 없으면 `gh repo clone <owner>/<repo> <워크스페이스>/prj/<repo>`
   - 있으면 `git -C <경로> fetch --prune` 후 기본 브랜치를 최신화.
   - 작업은 **새 브랜치**에서 한다(카드 번호 기반 권장, 예: `feat/<issue-number>-<slug>`).
2. **작업을 실행 프롬프트로 정리** — 무엇을 / AC(완료 기준) / 제약(건드리지 말 것) / 기대 산출물,
   그리고 **1의 repo 경로와 브랜치**. 카드 본문·AC 를 근거로 범위를 한정한다.
3. **Claude Code(ACP) 에 위임** — 프롬프트에 **`acp claude 사용해서 진행해줘`** 를 포함해
   1의 repo 디렉터리에서 실제 코딩·변경·검증을 수행하게 한다.
4. **결과 회수·보고** — 변경 요약 + AC 대비 검증 결과 + 남은 위험/다음 액션을 카드/스레드에
   사람이 읽게 정리한다. 위임 응답을 그대로 붙여넣지 않는다.

## 출력

- 변경 요약(파일/커밋) + AC 대비 pass/fail + kanban/카드 갱신 후보.
- 위임 실패·범위 이탈 시: 무엇이 막혔는지 + 사람 확인 요청.

## 가드레일

- OpenClaw = 지휘·중계, **Claude Code(ACP) = 실행기.** 역할을 섞지 않는다.
- 위임 프롬프트에 카드 링크·AC·제약을 명시해 acp claude 가 범위를 벗어나지 않게 한다.
- 배포·시크릿·외부·비가역은 승인 경계를 따른다(gated 카드는 라우터가 이미 보류 + 실행 중 위험 행위 승인).
- 위임이 실패/불명확하면 **사람에게 보고하고 임의 진행하지 않는다.**
- 기존 클론의 워킹트리가 더럽거나(이전 작업 잔재) 충돌하면 **`reset --hard`·강제 정리 금지** —
  상태를 보고하고 사람 판단을 받는다(비가역 손실 방지).
- clone/최신화는 `gh`/`git` 로 하되, 대상 repo 외 경로는 건드리지 않는다.
