# 거래 이력 검증

예산 B안을 쓰기 전에, 지난 3개월 소비 합계를 믿어도 되는지 확인한다. 달마다 **중복 · 취소 · 환불** 세 가지를 보고 각각 `verified` · `unknown` · `unresolved` 중 하나를 준다. 세 가지가 모두 `verified`인 달만 B안에 쓸 수 있다.

| 항목 | 내용 |
|---|---|
| 함수 | `finance.history_verifier.verify_transaction_history(user, month_ids, *, use_confirmed_salary=False)` |
| 예산 연결 | `budgets.design_history.verify_budget_history` → 위 함수를 `use_confirmed_salary=True`로 부른다 |
| 바꾸는 설정 | `BUDGET_HISTORY_VERIFIER` (기본 `verify_budget_history`) |
| 하는 일 | 읽기만 한다. DB 쓰기 · 잠금 · CODEF · ML 호출 없음. DB 읽기 2번 |
| 쓰는 곳 | [예산 설계 에이전트](agents/budget_design.md) A/B 고르기 |

```python
from finance.history_verifier import verify_transaction_history, transaction_history_report

verify_transaction_history(user, ["2026-08", "2026-09", "2026-10"])
# {"2026-08": {"duplicates": "verified", "cancellations": "verified", "refunds": "unknown"}, ...}

transaction_history_report(user, ["2026-08", "2026-09", "2026-10"])
# 같은 모양 + 항목마다 영향 상한과 이유 (아래 4절)
```

## 1. 입력 규칙

- 서로 다른 **완료된 달** `YYYY-MM`을 받는다. 이번 달 · 미래 · 중복 · 잘못된 형식은 `ValueError`. 오늘 기준은 `timezone.localdate()`.
- 어느 3개월을 볼지는 부르는 쪽이 정한다. 결과는 받은 순서대로 돌려준다.
- 수집 완료 여부(`coverage`)는 따로 본다. 이 함수는 "거래가 없으니 수집 완료"라고 판단하지 않는다.
- 환불이 다음 달에 들어와도 원래 달에 반영해야 하니, 그 사용자의 **저장된 전체 거래**와 연결을 읽는다.
- 동기화 · 후처리가 끝난 뒤에 부른다. 동기화 도중에 부르면 두 번의 읽기가 서로 다른 시점일 수 있다.

## 2. 상태

| 상태 | 뜻 |
|---|---|
| `verified` | 아래 검사를 모두 통과했다. 남은 문제가 있어도 소비 금액 영향이 0원이다 |
| `unknown` | 같은 구매인지, 원거래가 뭔지, 환불인지 근거가 부족해 영향을 확정하지 못했다 |
| `unresolved` | 저장된 연결 금액과 실제 소비 집계가 안 맞거나, 연결 구조가 모순된다 |

- 한 달 한 항목에 문제가 여러 개면 `unresolved` > `unknown` > `verified` 순으로 나쁜 쪽을 준다.
- DB 읽기 실패는 모든 달 · 항목이 `unknown`이다. 오류 원문은 내보내지 않는다.
- 영향이 작아도 봐주지 않는다. 1억 원 소비에 1원 환불이 안 맞아도 `unknown`이다. 허용 금액 · 비율은 정하지 않았다.

## 3. 무엇을 보나

비교 기준은 서비스 전체(홈 · 예산 사용액 · 소비 분석)와 같은 "쓴 돈"이다. 결제 − 서비스가 아는 취소 · 환불(취소 상태 · `CANCELLATION` 연결). 고정비 · 예산 밖 소비도 포함한다. 카테고리 · 미분류는 보지 않는다.

**중복**
- 소비 거래마다 원천 식별 키가 있어야 한다(수동 입력은 요청 키).
- 같은 원천에서 거래 지문(결제수단 · 일시 · 금액 · 이름 · 잔액)이 같거나, 같은 카드 · 날짜 · 승인번호가 또 있으면 중복 후보다. 반복 결제는 중복으로 단정하지 않는다.
- 같은 날 · 같은 금액 · 같은 이름의 카드 결제와 계좌 출금이 둘 다 소비로 남아 있으면 중복 후보다.
- `SAME_PURCHASE` 연결은 소유자 · 카드/계좌 조합 · 방향 · 금액 · 날짜 · 일대일을 본다. 계좌 쪽이 이미 `transfer`라 소비가 0이면 통과한다.

**취소 · 환불**
- 원승인에 반영된 카드 취소: 원천 키 · 승인번호 · 기관 취소 상태와 취소 금액이 맞아야 한다. 부분취소는 금액이 있어야 한다.
- 별도 `CANCELLATION` 연결: 방향 · 날짜 · 소유자 · 환불 재사용 · 순환 · 누적 취소액 초과를 본다. 원거래 순소비 = 원금 − 연결된 취소 합계여야 하고, 환불 행이 양수 소비로 남으면 안 된다.
- 자동 매칭(`suggested`) 연결도 금액은 대조한다. 금액이 안 맞으면 `unresolved`, 맞아도 원거래 확정 근거가 없으면 `unknown`.
- 원거래를 모르는 취소 · 환불은 그 달과 **그 이전 요청 달**을 모두 `unknown`으로 둔다.

**들어온 돈** (환불 항목)
- 월급 · 내 계좌 이체 · 친구 1/n · 판매 대금 같은 일반 입금은 어느 화면에서도 소비를 줄이지 않으므로 막지 않는다.
- 막는 경우는 셋뿐이다.
  - 전에 결제한 가게와 같은 이름(공백 무시)으로 들어온 입금. 예: 쿠팡 결제 뒤 쿠팡 입금
  - 들어온 돈이 소비로 집계되는 자료 이상
  - 사용자가 월급이라고 확인한 입금의 금액 · 날짜 · 적요 · 계좌가 확인 뒤 바뀐 경우 (`use_confirmed_salary=True`일 때만)
- 친구 1/n처럼 내 몫만 소비로 치고 싶으면 검증기가 아니라 거래 금액 수정(내 몫으로 고치기)으로 처리한다. 그러면 모든 화면과 B안에 같이 반영된다.

**처리 대기**
- 거래 저장 후처리의 연결 단계(`after_save_pending.link_basics`)가 남아 있으면 관련 달을 `unknown`으로 둔다. 카테고리 분류 실패는 상관없다.

## 4. 이유 코드

`transaction_history_report`는 항목마다 이렇게 준다. 거래 원문 · 계좌번호 · 가게 이름 · 거래 ID는 넣지 않는다.

```python
{"status": "unresolved", "impact_upper_bound": 3000,
 "reasons": [{"code": "cancellation_not_reflected", "impact_upper_bound": 3000}]}
```

| 코드 | 항목 | 상태 | 뜻 |
|---|---|---|---|
| `missing_identity` | 중복 | unknown | 원천 식별 키 없음 |
| `duplicate_fingerprint` · `duplicate_approval` | 중복 | unknown | 같은 지문 · 같은 승인번호 거래가 또 있음 |
| `unlinked_cross_source_purchase` | 중복 | unknown | 카드와 계좌에 같은 결제가 둘 다 소비로 남음 |
| `suggested_same_purchase` | 중복 | unknown | 같은 구매 연결이 추정뿐인데 소비를 숨김 |
| `same_purchase_net_mismatch` · `invalid_same_purchase` | 중복 | unresolved | 같은 구매 연결의 금액 · 구조가 안 맞음 |
| `cancellation_not_reflected` | 취소 · 환불 | unresolved | 연결된 취소액이 원거래 소비에 반영 안 됨 |
| `invalid_cancellation_link` | 취소 · 환불 | unresolved | 방향 · 날짜 · 누적액 등이 모순 |
| `suggested_cancellation_link` | 취소 · 환불 | unknown | 금액은 맞지만 자동 추정 연결뿐 |
| `hidden_original_refund` | 취소 · 환불 | unknown | 같은 구매로 숨긴 원거래의 환불 |
| `cancel_metadata_conflict` | 취소 · 환불 | unknown | 취소 플래그 · 금액 · 기관 상태가 서로 다름 |
| `unlinked_bank_cancellation` · `unlinked_card_cancellation` · `cancellation_origin_unknown` | 취소 · 환불 | unknown | 원거래를 못 찾은 취소 |
| `inflow_from_paid_merchant` | 환불 | unknown | 결제한 가게 이름으로 들어온 입금 |
| `inflow_counted_as_spending` | 환불 | unknown | 입금이 소비로 집계됨 |
| `changed_salary_evidence` | 환불 | unknown | 확인한 월급 입금이 확인 뒤 바뀜 |
| `link_processing_pending` | 전부 | unknown | 연결 후처리 대기 중 |
| `db_error` | 전부 | unknown | DB 읽기 실패 |

**영향 상한** (`impact_upper_bound`)
- 단위는 원. 근거가 부족해 상한을 못 정하면 `None`이고, 하나라도 `None`이면 그 항목 전체가 `None`이다.
- 같은 거래를 여러 이유가 가리키면 상한이 겹쳐 더해질 수 있다. 원거래를 모르는 입금은 가능한 과거 달마다 상한을 붙인다. 그래서 상한 합계를 실제 빠진 금액으로 읽으면 안 된다.

## 5. 예시

| 저장된 상황 | 중복 | 취소 | 환불 |
|---|---|---|---|
| 원승인 재조회로 10,000 → 7,000원 부분취소, 또는 0원 전액취소 | verified | verified | verified |
| 체크카드 결제 + 계좌 출금이 자동으로 같은 구매 연결, 소비 1번 | verified | verified | verified |
| 별도 카드 취소가 `suggested`로 연결됐는데 원승인 차감 없음 | verified | unresolved | unresolved |
| 별도 취소 차감액은 맞지만 연결이 `suggested`뿐 | verified | unknown | unknown |
| 월급 입금 + 카드 부분취소 + 체크카드 결제 | verified | verified | verified |

## 6. 한계

- DB에 저장된 거래만 본다. 기관이 안 보낸 거래, 이름 · 키 · 시간이 바뀐 중복, 앞으로 들어올 환불까지는 증명하지 않는다.
- `verified`라고 해서 거래나 합계를 고치지 않는다. 판정만 한다.
- 자동 취소 연결(`transfer_rules.link_cancellations` · `link_bank_cancellations`)은 `confirmed`로 올리지 않는다. 기관 원거래 참조 같은 확정 근거가 생기면 `unknown`을 더 줄일 수 있다.
- 결제한 가게 이름으로 들어온 입금은 환불이 아니어도 막힌다. 기관 입금 성격 코드나 사용자 확인이 생기면 줄일 수 있다.
- 전체 이력을 메모리로 읽는다. 이력이 아주 크면 성능을 따로 봐야 한다.

## 7. 테스트

```bash
cd backend
python manage.py test finance.tests.test_history_verifier finance.tests.test_transfer_rules \
  finance.tests.test_card_reviews finance.tests.test_card_sync budgets.tests.test_design_history
```

합성 거래로 입력 검사, 읽기 전용, 사용자 분리, 중복 후보, 같은 구매 연결, 부분 · 전액 취소, 미반영 연결, 달 경계 환불, 누적 초과, 월급 · 이자 · 내 계좌 이체를 본다. `HistoryPipelineTest`는 실제 저장 흐름(`normalize_approvals → card_review.save_transaction → transfer_rules.apply`)을 거친 결과로 확인한다.
