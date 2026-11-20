# 환경변수 설정 가이드

서버는 프로젝트 루트의 `.env`를 읽는다 (템플릿: [`.env.example`](../.env.example)). 처음 세팅한다면 OS별 단계 가이드 [`LOCAL_SETUP.md`](LOCAL_SETUP.md)부터 따라 한다.
화면(`frontend/`)은 환경변수 없이 동작한다.

| 항목 | 기준 |
|---|---|
| 읽는 곳 | `backend/config/settings.py` (`load_dotenv(BASE_DIR.parent / ".env")`, `BASE_DIR = backend/`) |
| 필수 값 검사 | 비어 있으면 서버를 켤 때 `ImproperlyConfigured`로 바로 알려 준다 |
| 기본 상태 | 필수 값만 채우면 챗봇은 가짜 해석(`CHAT_LLM=fake`), 예산 A/B 설계 · 외부 호출은 꺼진 상태로 켜진다 |

> 새 환경변수를 추가하면 **`.env.example`과 이 문서를 함께 갱신**한다. 값은 비워서 올린다.

---

## 1. 필수 값

| 변수 | 로컬 예시 | 설명 |
|---|---|---|
| `DJANGO_SECRET_KEY` | (생성한 값) | Django 서명 · 세션 키. `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"` |
| `POSTGRES_DB` | `money_cushion` | DB 이름 |
| `POSTGRES_USER` | `money_cushion` | DB 사용자 |
| `POSTGRES_PASSWORD` | (각자 설정) | DB 비밀번호 |
| `CONNECTED_ID_ENCRYPTION_KEY` | (생성한 값) | 회원별 CODEF 연결 ID 암호화 키 (32바이트). 바꾸면 저장된 연결을 못 읽는다 |
| `IDENTIFIER_HMAC_KEY` | (생성한 값) | 계좌 · 대출 · 카드 번호 중복 확인 키용 HMAC 키 (32바이트). **위 키와 다른 값**이어야 서버가 켜진다. 바꾸면 같은 계좌 · 카드가 새로 저장된다 |

32바이트 키 만들기 (두 번 실행해 서로 다른 값을 넣는다):

```bash
python -c "import secrets,base64;print(base64.urlsafe_b64encode(secrets.token_bytes(32)).decode())"
```

## 2. Django · DB 기본값

| 변수 | 기본값 | 설명 |
|---|---|---|
| `DJANGO_DEBUG` | `False` | 로컬은 `True`, 배포는 `False`. `.env`가 없는 서버에서 실수로 켜지지 않게 기본값이 `False`다 |
| `DJANGO_ALLOWED_HOSTS` | `localhost,127.0.0.1` | 접속 허용 호스트. 쉼표로 구분 |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | (비움) | HTTPS 배포 주소. 로컬은 비워 둔다 (DEBUG면 `localhost:5173`은 자동 허용) |
| `DJANGO_ADMIN_URL` | `admin/` | 관리자 화면 주소. 배포 때는 추측하기 어려운 값으로 바꾼다. `api`로 시작하면 서버가 켜지지 않는다 |
| `POSTGRES_HOST` | `localhost` | 배포 시 RDS 엔드포인트 |
| `POSTGRES_PORT` | `5432` | DB 포트 |
| `TASKS_INLINE` | `False` | `True`면 오래 걸리는 작업(금융 동기화 · 추천 등)을 백그라운드 스레드 대신 요청 안에서 끝까지 실행한다. 테스트 실행 때는 자동으로 켜진다 |

## 3. 기능별 선택 값

### 금융 조회 (CODEF)

| 변수 | 설명 |
|---|---|
| `CODEF_ENV` | `sandbox` · `demo` · `product` 중 하나. 비우면 `demo` |
| `CODEF_DEMO_ID` · `CODEF_DEMO_SECRET` | 데모 버전 client_id · client_secret (codef.io > MY > 키관리) |
| `CODEF_PUBLIC_KEY` | 금융사 비밀번호 RSA 암호화용 공개키 (전체를 한 줄로) |
| `CODEF_CONNECTED_ID` | 개발용 확인 명령(`codef_check`)이 쓰는 연결 ID. `python manage.py codef_connect`로 받는다. 서비스 화면의 연결은 회원별로 DB에 저장되므로 이 값과 무관하다 |
| `CODEF_CARD_NO` · `CODEF_CARD_PASSWORD` | `codef_card_check --card-auth` 명령 전용. 조회 때 카드 번호 · 비밀번호를 요구하는 카드사 확인용 |

### 통합 챗봇 · LLM

| 변수 | 값 | 설명 |
|---|---|---|
| `CHAT_ENGINE` | `legacy`(기본) · `router` | `router`에서 라우터가 소비 분석 · 예산 조정 · 청년 정책으로 연결한다 |
| `CHAT_LLM` | `fake`(기본) · `live` | `fake`는 정해 둔 해석만 하는 개발 · 테스트용(네트워크 없음). `live`는 실제 LLM |
| `OPENAI_API_KEY` · `LLM_MODEL` | `LLM_MODEL=gpt-6-luna` | `CHAT_LLM=live`면 둘 다 필요하다 (없으면 서버가 켜지지 않음). 예산 설계 외부 보정도 이 키를 쓴다 |
| `EMBEDDING_MODEL` | `text-embedding-3-small` | 청년 정책 검색용. **정책 데이터를 적재할 때 쓴 모델과 같아야** 한다 |
| `CHAT_EXPLAIN_PLAN` | `on` / 비움 | 원인 가설을 말한 설명 질문("배달 때문이야?")을 LLM 계획 · 답으로 확인한다 |
| `CHAT_AGENT` | `on` / 비움 | 소비 분석 첫 조회 뒤 필요할 때만 판단 1회 + 추가 조회 1회를 한다 |

청년 정책 추천은 `CHAT_ENGINE=router` · `CHAT_LLM=live` · `EMBEDDING_MODEL`에 더해 DB에 정책 데이터가 적재되어 있어야 한다. 정책 데이터는 저장소에 없으며 적재 방법은 [`agents/청년정책.md`](agents/청년정책.md)를 본다. 데이터가 없으면 정책 검색은 찾지 못했다는 안내로 응답하고, 소비 분석 · 예산 기능은 그대로 동작한다.

### 거래 분류

| 변수 | 설명 |
|---|---|
| `SPENDING_MODEL_PATH` | 거래 분류 SVM 모델 파일 경로. 비우면 `local_workspace/models/spending_classifier/...` 기본 위치. 모델 파일은 Git에 없다 ([`ML_MODELS.md`](ML_MODELS.md)) |
| `SPENDING_CONFLICTS_PATH` | 학습 데이터 라벨 충돌 목록(`label_conflicts.csv`) 경로. 비우면 기본 위치 |
| `KAKAO_REST_API_KEY` | 카카오 로컬 검색 (가게 이름으로 업종 찾기) |
| `NAVER_CLIENT_ID` · `NAVER_CLIENT_SECRET` | 네이버 지역 검색 (카카오 보완) |
| `TYPESAFE_API_KEY` · `JEV_MODEL` | 검색 결과로도 못 정한 거래를 Jev로 판단한다. 없으면 '확인 필요'로 남긴다 |

### 예산 설계 (A/B)

| 변수 | 기본값 | 설명 |
|---|---|---|
| `BUDGET_DESIGN_ENABLED` | `false` | `true`면 예산 A/B 설계를 쓴다. 끄면 임시 비율 추천 경로 |
| `BUDGET_DESIGN_EXTERNAL_ENABLED` | `false` | 외부 LLM 보정 허용. 사용자의 예산 설계 AI 동의가 별도로 필요하다. 끄면 새 동의 · 외부 호출을 모두 막고 기존 동의 철회만 허용한다 |
| `BUDGET_INFERENCE_PYTHON` | `local_workspace/.venv-budget-inference/...` | CatBoost 추론용 Python 실행 파일 ([추론 의존성](../scripts/budget_allocation/requirements-inference.txt)) |
| `BUDGET_MODEL_PATH` | (스크립트 기본 위치) | 예산 배분 모델 파일 경로. 추론 스크립트(`scripts/budget_design/`)가 읽는다 |
| `BUDGET_DESIGN_POLICY` | (코드 기본 정책) | 설계 정책을 JSON으로 덮어쓸 때만 넣는다 |

### 예산 조정

| 변수 | 설명 |
|---|---|
| `BUDGET_ADJUST_ALLOCATOR` | 선택. 같은 그룹 안의 감액 함수(dotted path). 기본은 `budgets.adjustment_core.calculation.proportional_group_reduction` (감액 가능액에 비례, 1만 원 우선 · 5천 원 보완). `(group, required, capacities)`를 받아 `{reductions, remaining}`을 돌려준다 |
| `BUDGET_ADJUST_REFERENCE_PROVIDER` | 선택. 최초 예산에 ML 참조가 없을 때 1회 보완하는 함수(dotted path). 비우면 `design_service.reference_from_initial_input`을 쓴다 |
| `BUDGET_PRICE_REFERENCE_PATH` | 선택. 가격 근거 검토용 스냅샷 JSON 경로. 아래 "가격 근거 예산 검토" 참고 |

실제 LLM 예산 조정은 `CHAT_ENGINE=router` · `CHAT_LLM=live`에 더해 사용자의 **예산 조정 AI 동의**가 필요하다 (예산 설계 AI 동의와 별개).

### 소비 분석 ML 비교

| 변수 | 설명 |
|---|---|
| `SPENDING_REFERENCE_ROOT` | 월 소비 비교 모델(모델 C) · 메타데이터 폴더. 비우면 `local_workspace/models/living_expense_prediction` |
| `BUDGET_INFERENCE_PYTHON` | 위 예산 설계와 같은 추론 환경을 쓴다 |

파일이나 추론 환경이 없으면 ML 비교만 건너뛰고 나머지 분석은 그대로 답한다.

### 시연 계정 · 배포

| 변수 | 쓰는 곳 |
|---|---|
| `DEMO_LOGIN_PASSWORD` | `python manage.py seed_persona <a·b·c> --apply` — 시연 계정 비밀번호. `.env`에 두지 않고 명령 실행 때만 넣는다 |
| `ALPHA_LOGIN_PASSWORD` | `python manage.py seed_alpha_home` — 알파 테스트 계정 비밀번호 |
| `RELEASE_TAG` | 배포 이미지 버전. 배포 서버의 상태 확인 주소가 이 값을 돌려준다 ([AWS 배포](AWS_DEPLOYMENT_GUIDE.md)) |

`spending_fixture/service_settings.py`가 읽는 `CHAT_TODAY` · `CHAT_LLM_LEDGER` · `CHAT_LLM_MAX_CALLS` · `FIXTURE_LIVE_LLM`, `chat/live_collab_check.py`가 읽는 `COLLAB_LIVE` · `COLLAB_LIVE_MAX_CALLS`는 합성 데이터 검증 전용이라 서비스 `.env`에는 넣지 않는다.

### 예산 조정 LangSmith 추적 (선택, 기본 꺼짐)

질문 원문과 예산 · 재정 정보가 LangSmith로 추가 전송되므로 개발 · 합성 검증 환경에서만 켠다. 먼저 `pip install -r backend/budgets/requirements-observability.txt`로 SDK를 설치하고 아래 값을 넣은 뒤 서버를 다시 켠다.

```dotenv
BUDGET_ADJUST_LANGSMITH=true
BUDGET_ADJUST_LANGSMITH_PROJECT=budget-adjustment
LANGSMITH_TRACING=true
LANGSMITH_API_KEY=<개인 LangSmith 키>
# LANGSMITH_ENDPOINT · LANGSMITH_WORKSPACE_ID 는 필요할 때만
```

- `BUDGET_ADJUST_LANGSMITH`와 `LANGSMITH_TRACING`이 **둘 다** `true`여야 기록한다.
- `budget-adjustment` 프로젝트의 `budget_adjustment` 실행에서 질문 · 최종 응답을, 하위 `budget_adjust*` 실행에서 프롬프트 · 대화 맥락 · 원본 출력 · 처리 시간을 본다. 라우터 · 소비 분석 호출은 추적하지 않는다.
- 은행 연결 · 예산 조정 AI 동의 검사는 추적보다 먼저 실행한다. 운영에서 켜기 전에는 LangSmith 전송 · 보관 범위에 대한 동의를 따로 확인해야 한다.
- 추적이 실패해도 LLM 호출을 반복하거나 조정 결과를 실패로 바꾸지 않는다. 끄려면 `BUDGET_ADJUST_LANGSMITH=false`로 바꾸고 다시 켠다.

### 가격 근거 예산 검토 (선택)

- `BUDGET_PRICE_REFERENCE_PATH`: 검증된 UTF-8 JSON 스냅샷의 서버 파일 경로. 기본값은 빈 값이며, 미설정 시 파일·지역 정보를 읽지 않고 기존 예산 계산을 유지한다. 실행 환경에 읽기 전용 파일로 제공하며 원자료·개인 PC 경로를 저장소에 넣지 않는다.
- `BUDGET_PRICE_PROFILE_PROVIDER`: **Django 설정의 callable** `(user) -> {"region_code": "12345", "item_groups": {"BEAUTY": "haircut"}}`. 환경변수 문자열만으로는 연결되지 않는다. 서버가 확인한 5자리 시군구 코드와 선택적인 세부품목 코드를 반환하도록 연결한다. 위치·이용 품목을 추측하지 않으며 제공자·지역이 없으면 검토를 생략한다.
- 실행 코드는 `budgets.price_reference`와 `budgets.price_review`에 있으며 개인 작업 폴더·수집기·추가 라이브러리가 필요하지 않다. 추천·조정은 동일한 검토 함수를 사용한다. 가격은 보조 근거이고 예산을 직접 변경하지 않는다.

스냅샷 v1의 최소 형식은 다음과 같다. 아래 금액·지역은 **형식 설명용 합성 값**이며 실제 판매가가 아니다.

```json
{
  "version": 1,
  "snapshot": "synthetic-example-v1",
  "regions": {"12345": "테스트 지역"},
  "references": [{
    "category": "BEAUTY",
    "item_group": "haircut",
    "unit": "1회",
    "reference_price": 35000,
    "scope": "local",
    "region_code": "12345",
    "sample_kind": "general",
    "tier": "everyday",
    "as_of": "2026-11-16"
  }]
}
```

`snapshot`은 자료가 바뀔 때 함께 바꾸는 비어 있지 않은 버전 식별자다. `category`는 확정된 10개 코드(`FOOD`, `HOUSING_TELECOM`, `TRANSPORT_CAR`, `HOUSEHOLD`, `FASHION_SHOPPING`, `MEDICAL_HEALTH`, `BEAUTY`, `EDUCATION`, `CULTURE_LEISURE`, `TRAVEL_LODGING`)만 허용한다. `reference_price`는 동일 품목·규격의 일반 판매가를 사전 검증·집계한 원 단위 양의 정수다. 실행 중에는 가격을 수집하거나 중앙값을 다시 만들지 않는다.

`scope`는 `local` 또는 `national`이며 전국 공통이면 `region_code`는 빈 문자열이다. 지역 가격은 `regions`에 등록된 코드만 쓴다. `as_of`는 미래가 아닌 ISO 날짜이며 검토 기준일로부터 180일 이내 자료만 사용한다. `tier`는 `everyday`/`premium` 중 하나이고 비교에는 `everyday`만 사용한다. 저가 선정 표본 등 `sample_kind`가 `general`이 아닌 자료는 제외한다. `unit`은 비어 있지 않은 문자열이며 직접 비교는 `1회·1개·1벌·1켤레·1권`만 허용한다. 증거·표본 수 등 추가 메타데이터는 유지할 수 있다.

잘못되거나 읽을 수 없는 파일은 `invalid_snapshot`, 지역 누락은 `needs_region`, 제공자 누락은 `needs_region_provider`, 스냅샷에 없는 지역은 `unknown_region`으로 검토를 생략한다. 유효한 파일이어도 가격 근거가 부족하면 `insufficient_price_data`이며 임의 가격으로 채우지 않는다. 기존 예산 검수·최소금액·잠금·승인은 그대로 적용한다.

기존 검토 규칙을 유지한다: 확인된 소비 이력이 있는 항목의 1회 기준가 미달·30% 이상 자동 감액을 재검토하며, 70% 유지액은 재검토 대안이지 가격에서 산출한 월별 필수 하한이 아니다. 사용자가 직접 지정한 항목·잠금·미사용 0원은 존중하고, 주거·통신과 여행·숙박에는 월별 구매 하한을 적용하지 않는다. 세부품목이 없으면 패션의 `basic_top`·미용의 `haircut`만 임시 기준으로 표시한다. `needs_reallocation`은 추가 재원 검토가 필요하다는 뜻이며 사용자 승인이나 기존 보호 조건을 건너뛰지 않는다.

---

## 4. 로컬 PostgreSQL 준비

**A. Docker (권장)** — [`LOCAL_SETUP.md`](LOCAL_SETUP.md) 4단계와 같다.

```bash
docker run --name money-cushion-db \
  -e POSTGRES_DB=money_cushion \
  -e POSTGRES_USER=money_cushion \
  -e POSTGRES_PASSWORD=<.env와 같은 비밀번호> \
  -p 5432:5432 -d pgvector/pgvector:pg17
```

> `pgvector/pgvector:pg17`은 PostgreSQL 17에 벡터 검색 확장(pgvector)이 들어 있는 이미지다. 청년 정책 검색이 쓰고, `finance` 0009 마이그레이션도 이 확장이 있어야 돈다. CI도 같은 이미지를 쓴다.

**B. 직접 설치 (macOS)**

```bash
brew install postgresql@17 pgvector
brew services start postgresql@17
psql postgres -c "CREATE USER money_cushion WITH PASSWORD '<비밀번호>' CREATEDB;"
psql postgres -c "CREATE DATABASE money_cushion OWNER money_cushion;"
psql template1 -c "CREATE EXTENSION IF NOT EXISTS vector;"
psql money_cushion -c "CREATE EXTENSION IF NOT EXISTS vector;"
```

> `CREATEDB` 권한과 `template1`의 확장은 Django 테스트가 새로 만드는 테스트 DB에 필요하다.

설치 확인 (`migrate` 후에 `installed_version`이 나오면 켜진 것):

```bash
docker exec money-cushion-db psql -U money_cushion -d money_cushion -c "SELECT name, installed_version FROM pg_available_extensions WHERE name='vector';"
```

| 에러 | 해결 |
|---|---|
| `could not open extension control file` | pgvector가 없다. A는 `pgvector/pgvector:pg17` 이미지로 다시 만들고, B는 `brew install pgvector` |
| `permission denied to create extension "vector"` | 관리자 계정으로 `CREATE EXTENSION vector;`를 한 번 실행한 뒤 다시 `migrate` |

---

## 5. 보안 규칙

- `.env`는 커밋하지 않는다 (`.gitignore`에 등록됨). `.env.example`에는 값을 비워서 올린다.
- 실제 키를 README · 이슈 · PR · 채팅방에 그대로 붙여넣지 않는다.
- 키가 커밋 · 노출되면 파일만 지우지 말고 **발급처에서 키를 즉시 재발급**한다.
- 같은 DB를 여러 사람이 쓰면 `CONNECTED_ID_ENCRYPTION_KEY` · `IDENTIFIER_HMAC_KEY`도 같은 값을 써야 저장된 연결 · 금융 데이터를 읽을 수 있다.
- 개발 · 시연에는 합성 데이터와 CODEF **데모 버전**(`CODEF_ENV=demo`)을 쓴다. 데모 버전은 하루 호출 수가 제한되므로 확인한 응답은 저장해 두고 개발한다. 실제 거래가 담긴 응답 파일은 커밋하지 않는다.
