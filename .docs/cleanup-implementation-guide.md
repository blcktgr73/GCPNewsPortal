# 오래된 뉴스 데이터 정리 - 구현 가이드

## 📋 개요

이 문서는 Cloud Function을 사용한 오래된 뉴스 데이터 자동 정리 시스템의 구현 방법을 단계별로 설명합니다.

## 🎯 구현 목표

- **보관 기간**: 30일
- **정리 주기**: 매월 1일 새벽 3시 (KST)
- **대상**: 모든 사용자의 summaries 데이터
- **방식**: Cloud Function + Cloud Scheduler + Pub/Sub

## 📁 프로젝트 구조

```
GCPNewsPortal/
├── backend/
├── news_summarizer/
├── cleanup_function/          # ← 새로 생성
│   ├── main.py               # Cloud Function 코드
│   ├── requirements.txt      # 의존성
│   └── .gcloudignore        # 배포 제외 파일
└── docs/
    └── cleanup-implementation-guide.md
```

## 🚀 구현 단계

### Step 1: cleanup_function 디렉토리 생성

```bash
# 프로젝트 루트에서
mkdir cleanup_function
cd cleanup_function
```

### Step 2: main.py 작성

`cleanup_function/main.py` 파일을 생성하고 다음 코드를 작성합니다:

```python
"""
Cloud Function for cleaning up old news summaries
Triggered by Pub/Sub message from Cloud Scheduler
"""

import functions_framework
from google.cloud import firestore
from datetime import datetime, timedelta
import base64
import json
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@functions_framework.cloud_event
def cleanup_old_summaries(cloud_event):
    """
    30일 이상 된 뉴스 요약을 삭제하는 Cloud Function

    Args:
        cloud_event: Pub/Sub 이벤트 객체

    Returns:
        dict: 처리 결과 (사용자 수, 삭제된 문서 수, 기준 날짜)
    """

    try:
        logger.info("=== Cleanup job started ===")

        # Firestore 클라이언트 초기화
        db = firestore.Client()

        # 보관 기간 설정 (기본값: 30일)
        retention_days = 30

        # Pub/Sub 메시지에서 설정값 읽기 (선택사항)
        if cloud_event.data and "message" in cloud_event.data:
            try:
                message_data = base64.b64decode(
                    cloud_event.data["message"]["data"]
                ).decode()
                config = json.loads(message_data)
                retention_days = config.get('retention_days', 30)
                logger.info(f"Retention days from message: {retention_days}")
            except Exception as e:
                logger.warning(f"Failed to parse message data, using default: {e}")

        # 삭제 기준 날짜 계산
        cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
        cutoff_iso = cutoff_date.isoformat()

        logger.info(f"Cutoff date: {cutoff_iso} (retention: {retention_days} days)")

        total_deleted = 0
        users_processed = 0
        users_with_deletions = 0

        # 모든 사용자 순회
        users_ref = db.collection('users')
        users = users_ref.stream()

        for user_doc in users:
            user_id = user_doc.id
            users_processed += 1

            logger.info(f"Processing user: {user_id}")

            # 해당 사용자의 오래된 summaries 조회
            old_summaries = (
                db.collection('users')
                .document(user_id)
                .collection('summaries')
                .where('created_at', '<', cutoff_iso)
                .stream()
            )

            # 배치 삭제 (Firestore 배치는 최대 500개 제한)
            batch = db.batch()
            batch_count = 0
            user_deleted = 0

            for doc in old_summaries:
                batch.delete(doc.reference)
                batch_count += 1
                user_deleted += 1

                # 500개마다 커밋
                if batch_count >= 500:
                    batch.commit()
                    total_deleted += batch_count
                    logger.info(f"Batch committed: {batch_count} documents")
                    batch = db.batch()
                    batch_count = 0

            # 남은 문서 커밋
            if batch_count > 0:
                batch.commit()
                total_deleted += batch_count
                logger.info(f"Final batch committed: {batch_count} documents")

            if user_deleted > 0:
                users_with_deletions += 1
                logger.info(f"User {user_id}: deleted {user_deleted} old summaries")

        # 결과 로깅
        result = {
            'status': 'success',
            'users_processed': users_processed,
            'users_with_deletions': users_with_deletions,
            'total_deleted': total_deleted,
            'cutoff_date': cutoff_iso,
            'retention_days': retention_days
        }

        logger.info(f"=== Cleanup job completed ===")
        logger.info(f"Summary: {result}")

        return result

    except Exception as e:
        logger.error(f"Error during cleanup: {str(e)}", exc_info=True)
        return {
            'status': 'error',
            'error': str(e)
        }
```

### Step 3: requirements.txt 작성

`cleanup_function/requirements.txt` 파일을 생성합니다:

```txt
functions-framework==3.*
google-cloud-firestore==2.*
```

### Step 4: .gcloudignore 작성

`cleanup_function/.gcloudignore` 파일을 생성합니다:

```
.gcloudignore
.git
.gitignore
__pycache__/
*.pyc
*.pyo
*.pyd
.pytest_cache/
.coverage
htmlcov/
venv/
```

### Step 5: GCP 리소스 생성

#### 5-1. Pub/Sub Topic 생성

```bash
gcloud pubsub topics create cleanup-old-news-topic \
  --project=YOUR_PROJECT_ID
```

**확인:**
```bash
gcloud pubsub topics list
```

#### 5-2. Cloud Function 배포

```bash
# cleanup_function 디렉토리에서 실행
cd cleanup_function

gcloud functions deploy cleanup-old-news \
  --gen2 \
  --runtime=python311 \
  --region=asia-northeast3 \
  --source=. \
  --entry-point=cleanup_old_summaries \
  --trigger-topic=cleanup-old-news-topic \
  --memory=256MB \
  --timeout=540s \
  --set-env-vars GOOGLE_CLOUD_PROJECT=YOUR_PROJECT_ID
```

**파라미터 설명:**
- `--gen2`: Cloud Functions 2세대 사용
- `--runtime=python311`: Python 3.11 런타임
- `--region=asia-northeast3`: 서울 리전
- `--source=.`: 현재 디렉토리의 코드 배포
- `--entry-point=cleanup_old_summaries`: 실행할 함수 이름
- `--trigger-topic`: Pub/Sub 트리거 설정
- `--memory=256MB`: 메모리 할당 (필요시 512MB로 증설)
- `--timeout=540s`: 타임아웃 9분 (최대 처리 시간)

**배포 확인:**
```bash
gcloud functions describe cleanup-old-news \
  --region=asia-northeast3 \
  --gen2
```

#### 5-3. Cloud Scheduler Job 생성

```bash
gcloud scheduler jobs create pubsub cleanup-old-news-job \
  --location=asia-northeast3 \
  --schedule="0 3 1 * *" \
  --time-zone="Asia/Seoul" \
  --topic=cleanup-old-news-topic \
  --message-body='{"retention_days": 30}'
```

**파라미터 설명:**
- `--schedule="0 3 1 * *"`: 매월 1일 새벽 3시 실행 (Cron 표현식)
- `--time-zone="Asia/Seoul"`: 한국 시간 기준
- `--topic`: 발행할 Pub/Sub Topic
- `--message-body`: Function에 전달할 설정 (JSON)

**스케줄 표현식 예시:**
```
0 3 1 * *      → 매월 1일 03:00
0 3 1,15 * *   → 매월 1일, 15일 03:00
0 3 * * 0      → 매주 일요일 03:00
0 3 * * *      → 매일 03:00
```

**Job 확인:**
```bash
gcloud scheduler jobs list --location=asia-northeast3
```

## 🧪 테스트

### 로컬 테스트 (Functions Framework)

```bash
# cleanup_function 디렉토리에서
pip install -r requirements.txt
pip install functions-framework

# 환경 변수 설정
export GOOGLE_APPLICATION_CREDENTIALS="path/to/your/service-account-key.json"
export GOOGLE_CLOUD_PROJECT="your-project-id"

# 로컬 실행
functions-framework --target=cleanup_old_summaries --debug
```

**테스트 메시지 발행:**
```bash
# 다른 터미널에서
curl -X POST http://localhost:8080 \
  -H "Content-Type: application/json" \
  -d '{
    "data": {
      "message": {
        "data": "'$(echo -n '{"retention_days": 30}' | base64)'"
      }
    }
  }'
```

### 배포 후 수동 테스트

```bash
# Scheduler Job 즉시 실행
gcloud scheduler jobs run cleanup-old-news-job \
  --location=asia-northeast3
```

**또는 Pub/Sub로 직접 메시지 발행:**
```bash
gcloud pubsub topics publish cleanup-old-news-topic \
  --message='{"retention_days": 30}'
```

### 로그 확인

```bash
# Cloud Function 로그 실시간 보기
gcloud functions logs read cleanup-old-news \
  --region=asia-northeast3 \
  --gen2 \
  --limit=50
```

**또는 Cloud Console에서:**
1. GCP Console → Logging → Logs Explorer
2. 쿼리 입력:
```
resource.type="cloud_function"
resource.labels.function_name="cleanup-old-news"
severity>=INFO
```

## 📊 모니터링

### Cloud Logging 쿼리 예시

**성공적인 실행 확인:**
```
resource.type="cloud_function"
resource.labels.function_name="cleanup-old-news"
jsonPayload.message=~"Cleanup job completed"
```

**에러 확인:**
```
resource.type="cloud_function"
resource.labels.function_name="cleanup-old-news"
severity>=ERROR
```

**삭제된 문서 수 확인:**
```
resource.type="cloud_function"
resource.labels.function_name="cleanup-old-news"
jsonPayload.message=~"total_deleted"
```

### 알림 설정 (선택사항)

실행 실패 시 이메일 알림을 받으려면:

1. **Alerting Policy 생성**
   - GCP Console → Monitoring → Alerting
   - Create Policy

2. **조건 설정**
   - Resource Type: Cloud Function
   - Metric: executions/count
   - Filter: status != "ok"

3. **알림 채널 설정**
   - Email 등록

## 🔧 설정 변경

### 보관 기간 변경

```bash
# 60일로 변경
gcloud scheduler jobs update pubsub cleanup-old-news-job \
  --location=asia-northeast3 \
  --message-body='{"retention_days": 60}'
```

### 실행 주기 변경

```bash
# 매주 실행으로 변경 (일요일 03:00)
gcloud scheduler jobs update pubsub cleanup-old-news-job \
  --location=asia-northeast3 \
  --schedule="0 3 * * 0"
```

### 메모리/타임아웃 변경

```bash
gcloud functions deploy cleanup-old-news \
  --gen2 \
  --region=asia-northeast3 \
  --memory=512MB \
  --timeout=600s \
  --update-env-vars GOOGLE_CLOUD_PROJECT=YOUR_PROJECT_ID
```

## 🐛 트러블슈팅

### 문제: Function이 실행되지 않음

**확인 사항:**
1. Scheduler Job이 활성화되어 있는지 확인
   ```bash
   gcloud scheduler jobs describe cleanup-old-news-job \
     --location=asia-northeast3
   ```

2. Pub/Sub Topic이 존재하는지 확인
   ```bash
   gcloud pubsub topics list
   ```

3. Function이 배포되어 있는지 확인
   ```bash
   gcloud functions list --gen2 --region=asia-northeast3
   ```

### 문제: 권한 에러 (Permission Denied)

**해결 방법:**
Cloud Function의 Service Account에 Firestore 권한 부여

```bash
# Function의 Service Account 확인
gcloud functions describe cleanup-old-news \
  --region=asia-northeast3 \
  --gen2 \
  --format="value(serviceConfig.serviceAccountEmail)"

# Firestore 권한 부여
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
  --member="serviceAccount:SERVICE_ACCOUNT_EMAIL" \
  --role="roles/datastore.user"
```

### 문제: 타임아웃 발생

**해결 방법:**
타임아웃 시간 증가 또는 배치 크기 조정

```bash
# 타임아웃을 10분으로 증가
gcloud functions deploy cleanup-old-news \
  --gen2 \
  --region=asia-northeast3 \
  --timeout=600s
```

### 문제: created_at 필드가 없는 문서

**해결 방법:**
main.py에서 필드 존재 여부 확인 로직 추가

```python
# 기존 쿼리 대신
for doc in summaries_ref.stream():
    data = doc.to_dict()
    if 'created_at' not in data:
        logger.warning(f"Document {doc.id} has no created_at field, skipping")
        continue

    created_at = data['created_at']
    if created_at < cutoff_iso:
        batch.delete(doc.reference)
```

## 💡 최적화 팁

### 1. 인덱스 생성

Firestore에서 `created_at` 필드에 인덱스를 생성하면 쿼리 성능이 향상됩니다.

**자동 생성:**
- 첫 실행 시 자동으로 생성 요청 메시지가 로그에 표시됨
- 링크를 클릭하여 인덱스 생성

**수동 생성:**
1. GCP Console → Firestore → Indexes
2. Create Index
   - Collection: summaries
   - Field: created_at (Ascending)

### 2. 배치 크기 조정

사용자 수가 매우 많은 경우:

```python
# 배치 크기를 500 → 100으로 줄여 메모리 절약
if batch_count >= 100:
    batch.commit()
    batch = db.batch()
    batch_count = 0
```

### 3. 병렬 처리 (고급)

사용자가 1,000명 이상인 경우, 병렬 처리 고려:
- Cloud Tasks로 사용자별 작업 분산
- 여러 Function 인스턴스가 동시에 처리

## 📈 예상 비용

### 사용자 100명 기준

| 항목 | 사양 | 월간 비용 |
|------|------|----------|
| Cloud Function | 1회 실행, 30초, 256MB | $0.00 (무료) |
| Pub/Sub | 메시지 1개 | $0.00 (무료) |
| Cloud Scheduler | Job 1개 | $0.10 |
| Firestore 읽기 | ~100 documents | $0.00 (무료) |
| Firestore 삭제 | ~1,000 documents | $0.00 (무료) |
| **총 비용** | | **$0.10/월** |

**참고:**
- Cloud Functions 무료 할당량: 월 2백만 호출
- Firestore 무료 할당량: 일 50,000 읽기, 20,000 쓰기

## ✅ 체크리스트

배포 전 확인사항:

- [ ] `cleanup_function/` 디렉토리 생성
- [ ] `main.py` 작성 완료
- [ ] `requirements.txt` 작성 완료
- [ ] `.gcloudignore` 작성 완료
- [ ] GCP 프로젝트 ID 확인
- [ ] Pub/Sub Topic 생성
- [ ] Cloud Function 배포 성공
- [ ] Cloud Scheduler Job 생성
- [ ] 수동 테스트 실행 및 로그 확인
- [ ] 알림 설정 (선택사항)

## 📚 관련 문서

- [개요 문서](./cleanup-automation-overview.md)
- [구현 방식 비교](./cleanup-implementation-comparison.md)
- [Cloud Functions 공식 문서](https://cloud.google.com/functions/docs)
- [Cloud Scheduler 공식 문서](https://cloud.google.com/scheduler/docs)

## 🔄 롤백 방법

문제가 발생한 경우:

```bash
# Cloud Function 삭제
gcloud functions delete cleanup-old-news \
  --region=asia-northeast3 \
  --gen2

# Scheduler Job 삭제
gcloud scheduler jobs delete cleanup-old-news-job \
  --location=asia-northeast3

# Pub/Sub Topic 삭제
gcloud pubsub topics delete cleanup-old-news-topic
```

## 📞 지원

문제가 발생하면:
1. 로그 확인 (`gcloud functions logs read`)
2. 트러블슈팅 섹션 참조
3. GCP Support 문의
