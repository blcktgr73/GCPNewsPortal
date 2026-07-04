# GCPNewsPortal Deployment Verification

> **server / auto-deploy repo 전용.** `VERIFICATION.md`(코드/테스트, Dev 축)와 **분리**된 배포 확인.
> owner: Tachikoma. `deployment-verify` 스킬이 갱신한다.
> 기준: palab-platform [deployment-verification](https://github.com/blcktgr73/palab-platform/blob/main/docs/operations/deployment-verification.md)

## 판정 규칙

- `Verification Status 완료` ≠ `배포 완료`. **push 성공 ≠ 서비스 배포 성공.**
- Dev 검증(`verify-ac`) 완료 **후에만** 이 단계로.
- GitHub Actions **실패** → 배포 확인으로 넘기지 않음.
- Actions **성공 + prod deploy 실패** → 미완료.
- **인프라 원인 실패는 재구현이 아니라 ops 조치로 분기.**

## Deployment Ledger

| 릴리즈 / commit | Actions (+deploy test) | prod deploy | smoke | 상태 | 증거 / 로그 |
|---|---|---|---|---|---|
| `538c3c7` (gemini-3.1-flash-lite 핀 + 상수화) | ✅ Deploy run#28700488307 (deploy-backend/summarizer/trigger 3 job) + CI Unit Tests ✅ | ✅ live — Cloud Run `news-backend` + CF `summarize_news`/`trigger_news_summary`, asia-northeast3 | ✅ `GET /` 200 `{"message":"API is running"}`, `/docs` 200 | **Verified** | [run](https://github.com/blcktgr73/GCPNewsPortal/actions/runs/28700488307) |

> 참고 형식: `✅ live` / `❌`(인프라 원인 → ops 분기) / `❌ deploy-lane test`(코드 원인 → `transformation`).
> 모델 반영 근거: 배포 소스가 538c3c7 checkout(평문 상수 `gemini-3.1-flash-lite`) + deploy-backend job 성공. 모델명 유효성은 사전 라이브 ListModels(v1)로 확인(T-20260704-001). 실제 요약 호출까지의 deep E2E는 Firebase 인증 토큰·Gemini 비용이 필요해 shallow smoke로 대체.

- 상태: `Verified` / `In progress` / `미완료(Failed)`
- 미완료면 원인 triage(코드 → 구현/`transformation`, 인프라 → ops)를 함께 남긴다.
