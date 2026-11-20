# 예산 설계 에이전트 (A/B)

처음 예산을 만들 때 생활비를 10개 소비 카테고리에 나눈다. 거래 이력이 넉넉하면 **B안(내 지난 소비 기준)**, 부족하면 **A안(비슷한 사람의 소비 비율 기준)**으로 계산한다. 돈 계산은 전부 서버가 하고, LLM은 켜져 있을 때 서버가 만든 선택지 중에서 고르기만 한다.

| 항목 | 내용 |
|---|---|
| 실행 시점 | 추천 예산 만들기 `POST /api/budgets/recommend/` (작업 번호 방식, 요청 안에서 계산 끝) |
| 켜는 법 | `BUDGET_DESIGN_ENABLED=true`. 끄면 기본 비율 엔진(`budgets.recommend`)을 쓴다. 응답 모양은 같다 |
| 입구 함수 | `budgets.design_service.recommend(user, snapshot, available_spare, today)` |
| 쓰는 모델 | 생활비 배분 CatBoost([ML 모델](../ML_MODELS.md#2-생활비-배분-catboost)) |
| 배분 대상 | 식비 · 교통 · 생활용품 · 패션 · 의료 · 뷰티 · 교육 · 문화. **주거·통신, 여행·숙박은 월 예산에서 빼고 0원** |
| API 문서 | [예산 API](../api/budgets.md#예산-ab-설계-budget_design_enabled) |

## 1. 흐름

```
지난 완료 3개월 거래 읽기 (수집 범위 + 거래 이력 검증)
  ↓
A/B 고르기 ── 조건 미달 → A안
  │             조건 충족 → B안
  ↓
CatBoost로 카테고리 비율 예측 (A·B 둘 다. B에서는 줄일 때 하한으로 씀)
  ↓
유지 목표 · 최소금액 · 잠금 · 시스템 하한 충돌 확인 ── 충돌 → 멈춤 (복구 대화로)
  ↓
A안 또는 B안 계산
  ↓
최종 금액 단위 정리 (만 원 우선, 필요할 때 5천 원 / 잠금은 원액)
  ↓
검수 (합계 + 남은 돈 = 생활비, 최소 · 잠금 · 하한 지킴) → 초안 저장
```

## 2. A/B 고르기

`scripts/budget_design/plan_selection.py`의 `select_plan`. 모델을 부르지 않는 고정 규칙이다.

| 조건 | 결과 |
|---|---|
| 지난 완료 3개월 모두 수집 완료(`coverage = complete`) | 하나라도 아니면 A |
| 3개월 모두 거래 이력 검증 통과(중복 · 취소 · 환불 = `verified`) | 하나라도 `unknown` · `unresolved`면 A |
| 카테고리별 3개월 결제 건수 중 가장 많은 것이 **11건 이상** | 10건 이하면 A |

- 건수는 분류된 소비 거래만 센다. 미분류 거래는 세지 않고, 미분류 비중만으로 B를 막지도 않는다.
- 이력 검증은 [거래 이력 검증](../finance_history_verifier.md)이 맡는다. 확인 못 한 달은 "소비 0건"이 아니라 "모름"으로 보고 A로 보낸다.

## 3. A안 — 비율 기준

1. CatBoost가 나이 · 성별 · 소득 · 차량 · 고정비 · 생활비로 10개 비율을 낸다. 생활비 × 비율 = 초안.
2. 사용자 최소금액을 먼저 채우고, 잠금은 그 금액 그대로 둔다. 교통은 시스템 하한(아래 표)을 지킨다.
3. **LLM 꺼짐(기본):** 여기까지가 결과다.
4. **LLM 켜짐:** 1~3순위 항목을 차례로 본다. 서버가 작은 · 중간 · 큰 증액안을 만들고 LLM은 하나를 고르거나 유지 · 종료한다.
   - 전체 이동 한도: (생활비 + 기타) × 20%
   - 재원 순서: 순위 미입력 항목 → 후순위 항목. 같은 그룹 안에서는 쇼핑 · 뷰티 · 문화를 먼저 줄인다
   - 순위를 매긴 항목은 재원으로 깎지 않는다
   - 실제로 깎이는 안이면 LLM이 한 번 더 검토한다. 실패 · 시간 초과(총 30초)면 부분 결과를 버리고 기본안으로 간다

## 4. B안 — 내 소비 기준

1. 카테고리별 출발액 = 지난 3개월 **일회성 제외 월평균**.
   - 일회성: 한 카테고리 결제가 10건 이상이면 금액 로그의 수정 Z점수 > 3.5인 결제. 3~9건이면 가장 큰 결제가 나머지 합보다 큰 경우. 패션 · 뷰티는 10건 이상일 때만 본다.
   - 같은 가게가 여러 달에 나오면 일회성으로 보지 않는다.
2. 출발액 합이 생활비보다 **적으면** 남은 돈은 그대로 `unallocated`(여윳돈)로 남긴다. 아무 항목에 얹지 않는다.
3. 합이 생활비보다 **많으면** 줄인다.
   - 순서: 순위 미입력 → 3순위 → 2순위 → 1순위. 같은 그룹 안에서는 최근 증가율 · 튀는 정도가 큰 항목부터
   - 하한: 최소금액, 잠금, 시스템 하한, 그리고 **ML 몫**(지난 소비가 ML 몫보다 많던 항목은 ML 몫 아래로 안 내려감)
4. 다 줄여도 모자라면 확인된 여윳돈에서 모자란 만큼만 가져온다(`spare_transfer`). 그래도 모자라면 `needs_upper_allocation_review`로 멈춘다.
5. 미분류 거래 보정: 미분류의 1순위 후보(ML 출처, 점수가 유효한 것만)로 분류했다고 가정하고 한 번 더 계산한다. 늘어난 만큼만 2번의 남은 돈 안에서 채운다. 다른 항목을 깎거나 여윳돈을 더 쓰지 않는다. 실제 거래 분류는 안 바뀐다.
6. **LLM 켜짐:** LLM이 다음 달 금액을 예측하되 출발액의 ±20% 안에서만 받는다. 범위를 벗어나거나 실패하면 위 규칙 계산으로 돌아간다.

## 5. 공통 규칙

**금액 단위** (`budgets/design_units.py`)
- 카테고리 금액은 만 원 단위가 기본이고, 최소 · 잠금 · 합계 때문에 필요할 때만 5천 원 단위를 쓴다.
- 잠금 금액은 원 단위 그대로 둔다.
- 단위를 맞추고 남은 돈은 `unallocated`로 여윳돈에 남긴다. 기타도 잠기지 않았으면 같은 단위를 쓴다.
- 단위와 보호 조건을 같이 지킬 수 없으면 성공 예산을 만들지 않는다.

**시스템 하한** (`budgets/design_reality.py`)

| 항목 | 하한 | 비고 |
|---|---|---|
| 교통 | 차 없음 6만 원 · 차 있음 10만 원 | 검증된 교통 이력이 있으면 그 금액(천 원 반올림)까지만 보호. 잠금이 우선 |
| 식비 | 없음 | 기준 미확정 |

**설명 문장** (`budgets/design_explain.py`)
- 카테고리마다 "왜 이 금액인지"를 서버가 만든다. 금액 변화의 원인 합이 실제 차이와 정확히 맞아야 한다.
- 1~3순위 항목이 지난 소비보다 30% 넘게 줄면(정확히 30%는 제외) 감액 안내를 붙인다. 이력이 없거나 잠긴 항목은 안내하지 않는다.

**멈추는 경우**

| 상태 | 언제 | 다음 |
|---|---|---|
| `needs_data` | 이력 읽기 실패, ML 실행 실패 | 다시 시도 안내 |
| `needs_policy` | 정책 설정 오류 | 운영 설정 확인 |
| `infeasible` | 최소금액 합이 생활비보다 큼, 잠금이 최소보다 작음 등 | 복구 대화 |
| `target_conflict` | 유지 목표가 잠금 · 최소 · 단위 · 생활비와 안 맞음 | 복구 대화 |
| `needs_upper_allocation_review` | 여윳돈을 보태도 생활비 부족, 단위 충돌 | 복구 대화 |

**복구 대화** (`design_handoff.py` · `design_recovery*.py`)
- 해결 가능한 충돌이면 추천 작업 결과에 `handoff={mode:"DESIGN_RECOVERY"}`만 붙인다. 예산은 만들지 않는다(`budgetId=null`).
- 예산 챗봇이 범위나 재원을 물어본다. 재원은 확인된 여윳돈을 먼저 쓰고, 저축 · 월 쿠션 여유분은 사용자가 고를 때만 쓴다.
- 서버가 A/B 계산을 다시 돌려 검수한 안만 보여 준다. 사용자가 승인하기 전에는 기존 예산 · 설정을 바꾸지 않는다.

**조정 에이전트로 넘기는 값** (`design_references.py`)
- 초안에 원래 ML 몫, 모델 정보, 검증된 교통 기준을 저장한다. 나중에 예산 조정이 이 값을 참고한다. 거래 · 가게 이름은 넣지 않는다.

## 6. 외부 LLM과 동의

- LLM은 `BUDGET_DESIGN_EXTERNAL_ENABLED=true` **그리고** 사용자의 예산 설계용 외부 전송 동의가 있을 때만 부른다. 둘 중 하나라도 없으면 규칙 계산만 한다.
- 이 동의는 예산 조정용 동의와 따로 받는다(`budgets/design_consent.py`).
- 모델은 `gpt-4o-mini`. LLM은 금액을 직접 쓰지 못하고 서버 선택지만 고른다. 서버가 매번 다시 검수한다.
- 실제 사용자 경로에서는 LangSmith 추적을 끈다. 합성 실험에서만 쓴다.

## 7. 설정과 파일

| 설정 | 기본 | 설명 |
|---|---|---|
| `BUDGET_DESIGN_ENABLED` | `false` | A/B 설계 켜기. 켜면 배포 때 `models/budget_allocation.joblib`가 있어야 한다 |
| `BUDGET_DESIGN_EXTERNAL_ENABLED` | `false` | 외부 LLM 허용 |
| `BUDGET_DESIGN_POLICY` | 내장 정책 `2026-11-12-a-ranked-protection` | JSON으로 덮어쓸 때만 |
| `BUDGET_INFERENCE_PYTHON` | `local_workspace/.venv-budget-inference/…/python` | CatBoost 추론 전용 Python. 배포 이미지는 `/opt/budget-inference/bin/python` |
| `BUDGET_MODEL_PATH` | 없음 | CatBoost 모델 파일 |
| `BUDGET_PRICE_REFERENCE_PATH` | 없음(꺼짐) | 지역 물가 참고 검토. 현재 쓰지 않음 |

| 위치 | 하는 일 |
|---|---|
| `backend/budgets/design_service.py` | 입구. 이력 읽기 → A/B 선택 → 계산 → 단위 정리 → 검수 |
| `backend/budgets/design_candidates.py` · `design_selection.py` | A안 계산, LLM 선택 |
| `scripts/budget_design/plan_b_*.py` | B안 이력 정리 · 계산 · 미분류 보정 · LLM 예측 |
| `scripts/budget_design/plan_selection.py` | A/B 선택 규칙 |
| `scripts/budget_design/inference.py` · `predict_worker.py` | CatBoost를 별도 프로세스로 실행 |
| `backend/budgets/design_units.py` · `design_explain.py` · `design_reality.py` | 금액 단위, 설명, 시스템 하한 |
| `backend/budgets/design_history.py` | 거래 이력 검증 연결 |
| `backend/budgets/design_handoff.py` · `design_recovery*.py` | 실패 → 복구 대화 |
| `scripts/budget_design/compare_window.py` | 합성 자료로 A/B를 비교해 보는 로컬 창 (Windows는 `A_B_예산비교_실행.cmd`) |

## 8. 실행 · 테스트

```bash
# CatBoost 추론 환경 확인 (합성 프로필, DB · LLM 없음)
python -m scripts.budget_design.inference

# A/B 계산 규칙 (저장소 루트)
python -m unittest discover -s tests/budget_design

# 서버 연결 (backend 폴더)
python manage.py test budgets.tests.test_design_service budgets.tests.test_design_candidates \
  budgets.tests.test_design_units budgets.tests.test_design_history budgets.tests.test_design_recovery
```

외부 LLM 경로 테스트(`test_design_service_llm`)는 HTTP 응답을 흉내 낸다. 실제 호출은 하지 않는다.

## 9. 한계

- A안은 "비슷한 사람의 평균 비율"이다. 이 사람에게 맞는 정답이 아니다.
- B안은 지난 소비를 기준으로 한다. 지난 소비가 많았다고 그만큼이 적정하다는 뜻은 아니다.
- 미분류 보정은 분류 후보가 맞다는 가정 위에서 돈다. 후보가 틀리면 보정도 틀린다. 합성 실험으로만 확인했다.
- 11건 · 20% · 30% · ±20% 같은 기준값은 팀 결정이다. 실사용자 자료로 다시 맞출 여지가 있다.
- 식비 시스템 하한, 지역 물가 검토는 아직 기준이 없어 꺼져 있다.
