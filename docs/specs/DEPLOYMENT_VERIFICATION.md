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
| `<sha>` | ✅ run#123 | ✅ live | ✅ | **Verified** | `<run URL>` |
| `<sha>` | ✅ | ❌ | — | **미완료** (인프라: quota) | `<로그 경로>` |
| `<sha>` | ❌ deploy-lane test | — | — | **미완료** (코드) → transformation | `<run URL>` |

- 상태: `Verified` / `In progress` / `미완료(Failed)`
- 미완료면 원인 triage(코드 → 구현/`transformation`, 인프라 → ops)를 함께 남긴다.
