# Cloud Function vs Backend API 구현 방식 비교

## 📋 개요

오래된 뉴스 데이터 정리 기능을 구현하는 두 가지 방식을 비교합니다.

## 🏗️ 아키텍처 비교

### 방식 1: Cloud Function + Cloud Scheduler (선택됨 ✅)

```
┌─────────────────────┐
│ Cloud Scheduler     │ ← 매월 1일 03:00 KST
│ (Cron Job)          │
└──────────┬──────────┘
           │ trigger
           ▼
┌─────────────────────┐
│ Pub/Sub Topic       │
│ cleanup-old-news    │
└──────────┬──────────┘
           │ event
           ▼
┌─────────────────────┐
│ Cloud Function      │ ← 독립 실행
│ Gen 2 Python        │
└──────────┬──────────┘
           │ batch delete
           ▼
┌─────────────────────┐
│ Firestore           │
│ All Users' Data     │
└─────────────────────┘
```

### 방식 2: Backend API + Cloud Scheduler

```
┌─────────────────────┐
│ Cloud Scheduler     │ ← 매월 1일 03:00 KST
│ (HTTP Job)          │
└──────────┬──────────┘
           │ HTTP POST
           ▼
┌─────────────────────┐
│ Cloud Run           │ ← 기존 Backend
│ (Backend API)       │
│ /admin/cleanup      │
└──────────┬──────────┘
           │ batch delete
           ▼
┌─────────────────────┐
│ Firestore           │
│ All Users' Data     │
└─────────────────────┘
```

## 💰 비용 비교

### Cloud Function 방식

| 항목 | 사양 | 비용 |
|------|------|------|
| **함수 실행** | 월 1회, 30초 소요 | 무료 (Free tier 범위 내) |
| **메모리** | 256MB | 무료 |
| **Pub/Sub** | 메시지 1개/월 | 무료 (Free tier 범위 내) |
| **Scheduler** | Job 1개 | 월 $0.10 |
| **총 예상 비용** | - | **월 $0.10** |

**Free Tier:**
- Cloud Functions: 월 2백만 호출 무료
- Pub/Sub: 월 10GB 무료
- Cloud Scheduler: 3개 job까지 무료 (프로젝트당)

### Backend API 방식

| 항목 | 사양 | 비용 |
|------|------|------|
| **Cloud Run** | 항상 실행 (최소 1 인스턴스) | 월 $5-10 (기존) |
| **추가 컴퓨팅** | 정리 작업 실행 | 추가 비용 미미 |
| **Scheduler** | HTTP Job 1개 | 무료 (3개 이내) |
| **총 예상 비용** | - | **월 $5-10 (기존 비용에 포함)** |

### 비용 분석

**Cloud Function 승리!** 🏆

- **독립 비용**: Cloud Function은 순수하게 정리 작업만의 비용
- **Cloud Run**: 이미 실행 중이므로 추가 비용 거의 없음
- **하지만**: Cloud Function이 더 명확하고 관리하기 쉬움

## ⚡ 성능 비교

### Cloud Function

| 항목 | 설명 |
|------|------|
| **Cold Start** | 5-10초 (월 1회 실행이므로 매번 발생) |
| **실행 시간** | 사용자 100명 기준 30-60초 |
| **메모리** | 256MB (필요 시 512MB로 증설 가능) |
| **타임아웃** | 최대 60분 (충분함) |
| **동시성** | 1개 인스턴스로 충분 |

### Backend API

| 항목 | 설명 |
|------|------|
| **Cold Start** | 없음 (이미 실행 중) |
| **실행 시간** | 사용자 100명 기준 30-60초 |
| **메모리** | 512MB (기존 설정) |
| **타임아웃** | 최대 60분 |
| **동시성** | 기존 요청과 공유 (리소스 경합 가능) |

### 성능 분석

**무승부** (큰 차이 없음)
- 월 1회 실행: Cold Start 5-10초는 허용 범위
- 배치 작업: 두 방식 모두 동일한 Firestore API 사용
- Backend는 이미 실행 중이지만, 정리 작업 중 다른 요청 처리 가능

## 🔧 구현 및 유지보수

### Cloud Function

| 장점 | 단점 |
|------|------|
| ✅ 독립적인 코드베이스 | ❌ 별도 배포 파이프라인 필요 |
| ✅ Backend 코드 수정 불필요 | ❌ 코드베이스 분산 |
| ✅ 실패 시 Backend에 영향 없음 | ❌ 의존성 관리 별도 |
| ✅ 버전 관리 독립적 | ❌ 테스트 환경 별도 구성 |
| ✅ 롤백 용이 | |

**배포 명령어:**
```bash
gcloud functions deploy cleanup-old-news \
  --gen2 \
  --runtime=python311 \
  --region=asia-northeast3 \
  --source=./cleanup_function \
  --entry-point=cleanup_old_summaries \
  --trigger-topic=cleanup-old-news-topic
```

### Backend API

| 장점 | 단점 |
|------|------|
| ✅ 단일 코드베이스 | ❌ Backend 코드 복잡도 증가 |
| ✅ 공통 의존성 활용 | ❌ Backend 배포 시 함께 배포됨 |
| ✅ 로컬 테스트 용이 | ❌ 실패 시 Backend 영향 가능 |
| ✅ 기존 인프라 활용 | ❌ API 엔드포인트 보안 관리 필요 |
| ✅ HTTP로 수동 실행 가능 | |

**API 엔드포인트:**
```python
@app.post("/admin/cleanup-old-news")
def cleanup_endpoint(retention_days: int = 30):
    # 구현 코드
    pass
```

### 유지보수 분석

**상황에 따라 다름**
- **Cloud Function**: 독립성으로 안정성 ↑, 관리 포인트 ↑
- **Backend API**: 통합 관리 편함, 복잡도 ↑

## 🔒 보안 비교

### Cloud Function

| 보안 요소 | 설명 |
|----------|------|
| **인증** | Pub/Sub 기반, 외부 접근 불가 |
| **권한** | IAM으로 자동 관리 |
| **노출** | 인터넷에 노출 안 됨 |
| **키 관리** | 불필요 |

**보안 설정:**
```bash
# IAM 자동 설정, 추가 설정 불필요
```

### Backend API

| 보안 요소 | 설명 |
|----------|------|
| **인증** | API Key 또는 JWT 필요 |
| **권한** | 별도 Admin 권한 체크 필요 |
| **노출** | HTTPS 엔드포인트 (인터넷 노출) |
| **키 관리** | Admin API Key 관리 필요 |

**보안 설정:**
```python
@app.post("/admin/cleanup-old-news")
def cleanup_endpoint(x_admin_key: str = Header(None)):
    if x_admin_key != os.getenv("ADMIN_API_KEY"):
        raise HTTPException(status_code=403)
```

### 보안 분석

**Cloud Function 승리!** 🔒
- 외부 노출 없음
- API Key 관리 불필요
- IAM 기반 자동 보안

## 🚀 확장성 비교

### Cloud Function

| 시나리오 | 대응 방법 |
|---------|----------|
| 사용자 1,000명 | 메모리 512MB로 증설 |
| 사용자 10,000명 | 타임아웃 10분으로 증가 |
| 처리 시간 오래 걸림 | 배치 크기 조정 |

**확장 명령어:**
```bash
gcloud functions deploy cleanup-old-news \
  --memory=512MB \
  --timeout=600s
```

### Backend API

| 시나리오 | 대응 방법 |
|---------|----------|
| 사용자 1,000명 | 기존 인스턴스로 처리 가능 |
| 사용자 10,000명 | 타임아웃 설정 필요 |
| 처리 시간 오래 걸림 | 다른 요청과 리소스 경합 |

### 확장성 분석

**Cloud Function 승리!** 📈
- 독립 실행으로 리소스 보장
- 필요 시 메모리/타임아웃 자유롭게 조정
- Backend 영향 없음

## 🧪 테스트 및 디버깅

### Cloud Function

**로컬 테스트:**
```bash
# Functions Framework 사용
functions-framework --target=cleanup_old_summaries --debug
```

**디버깅:**
- Cloud Logging에서 실시간 로그 확인
- 로컬에서 독립 테스트 가능

### Backend API

**로컬 테스트:**
```bash
# FastAPI 서버 실행
uvicorn main:app --reload

# API 호출
curl -X POST http://localhost:8000/admin/cleanup-old-news \
  -H "X-Admin-Key: test-key"
```

**디버깅:**
- 기존 Backend 로깅 시스템 활용
- 다른 API와 통합 테스트 가능

### 테스트 분석

**Backend API 승리!** 🧪
- 로컬 개발 환경 이미 구축됨
- 기존 테스트 도구 활용

## 📊 종합 비교표

| 항목 | Cloud Function | Backend API | 승자 |
|------|----------------|-------------|------|
| **비용** | $0.10/월 | $0 (기존 포함) | 🏆 Function |
| **성능** | Cold Start 있음 | 즉시 실행 | 무승부 |
| **구현 난이도** | 새 프로젝트 생성 | 코드 추가만 | API |
| **유지보수** | 독립 관리 | 통합 관리 | 상황 따라 |
| **보안** | IAM 자동 | API Key 필요 | 🏆 Function |
| **확장성** | 독립 리소스 | 공유 리소스 | 🏆 Function |
| **테스트** | 별도 환경 | 기존 환경 | API |
| **안정성** | Backend 독립 | Backend 의존 | 🏆 Function |

## 🎯 최종 결론

### Cloud Function 방식 선택 ✅

**주요 선택 이유:**

1. **비용 효율성**
   - 실행 시간만 과금 (월 1회)
   - 명확한 비용 추적

2. **안정성**
   - Backend 서비스와 완전 독립
   - 실패해도 사용자 서비스에 영향 없음

3. **보안**
   - 외부 노출 없음
   - API Key 관리 불필요

4. **아키텍처 일관성**
   - 기존 news_summarizer도 Cloud Function 사용
   - 동일한 패턴으로 유지보수 용이

5. **확장성**
   - 필요 시 독립적으로 리소스 조정
   - Backend에 영향 없이 개선 가능

### Backend API가 더 나은 경우

다음 상황에서는 Backend API가 더 적합할 수 있습니다:

- ❌ 정리 작업을 자주 실행해야 하는 경우 (일 단위 이상)
- ❌ 관리자 대시보드에서 수동 실행이 중요한 경우
- ❌ 정리 로직을 자주 변경해야 하는 경우
- ❌ Backend 코드와 긴밀하게 통합해야 하는 경우

**하지만 현재 요구사항 (월 1회 자동 실행)에는 Cloud Function이 최적입니다.**

## 📚 다음 단계

구현을 진행하려면 [구현 가이드](./cleanup-implementation-guide.md)를 참조하세요.
