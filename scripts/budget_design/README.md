# 예산 설계 A/B — 계산 코드와 로컬 도구

서비스의 예산 설계 계산 코드와, 합성 자료로 A/B를 비교해 보는 로컬 도구가 있다. 계산 규칙은 [예산 설계 에이전트](../../docs/agents/budget_design.md)에 정리돼 있다.

모든 도구는 합성 자료만 쓴다. 실제 개인정보·거래 내역은 넣지 않는다.

## 파일

| 파일 | 하는 일 |
|---|---|
| `plan_selection.py` | A/B 고르기 (3개월 · 카테고리 최대 건수 11건 이상이면 B) |
| `plan_b_history.py` | 3개월 거래 정리, 일회성 지출 찾기 |
| `plan_b_budget.py` | B안 계산 (출발액 → 감액 → 여윳돈 충당) |
| `plan_b_candidates.py` | 미분류 거래를 1순위 후보로 가정한 재계산 |
| `plan_b_forecast.py` | B안 LLM 예측 (출발액 ±20% 안에서만) |
| `plan_b_adjustments.py` · `plan_b_llm.py` | B안 조정 도구 · LLM 검토 (실험용) |
| `inference.py` · `predict_worker.py` | CatBoost를 별도 Python 프로세스로 실행 (서버도 이걸 씀) |
| `compare_plans.py` · `compare_window.py` | 합성 사용자로 A/B 비교 (명령줄 · 창) |
| `simulator.py` · `run_*.py` | 직접 값을 바꿔 돌려 보는 실험 스크립트 |

서버 쪽 입구는 `backend/budgets/design_service.py`다.

## 준비

CatBoost 모델은 Git에 없다. 담당자에게 받은 `budget_allocation.joblib`를 두고, 전용 Python 환경을 만든 뒤 두 경로를 **절대 경로**로 지정한다.

```sh
# 저장소 루트에서
python3.12 -m venv /opt/budget-runtime
/opt/budget-runtime/bin/pip install -r scripts/budget_allocation/requirements-inference.txt

export BUDGET_INFERENCE_PYTHON=/opt/budget-runtime/bin/python
export BUDGET_MODEL_PATH=/opt/budget-model/budget_allocation.joblib
```

Windows는 `Scripts/python.exe`를 쓴다. 다른 OS에서 만든 가상환경 폴더를 복사해 쓰지 않는다.

## 실행

```sh
# 1. CatBoost 추론 확인 — 합성 프로필 1개, DB · LLM 없음
python -m scripts.budget_design.inference
#    성공: status=ready, 종료 코드 0 / 실패: 오류 종류만 출력, 종료 코드 2

# 2. A/B 비교 (명령줄)
python scripts/budget_design/compare_plans.py --case shortfall   # shortfall · surplus · medical
python scripts/budget_design/compare_plans.py --auto             # 자동 선택된 안만

# 3. A/B 비교 (창)
python scripts/budget_design/compare_window.py
```

- 창을 쓰려면 Tk가 되는 Python이 필요하다. Windows는 `A_B_예산비교_실행.cmd`로 열 수 있다.
- `--llm`을 붙이면 실제 OpenAI를 부른다(비용 발생). `OPENAI_API_KEY`, `LLM_MODEL`이 필요하다.
- LangSmith 추적을 보려면 `backend/budgets/requirements-observability.txt`를 설치하고 `LANGSMITH_TRACING` · `LANGSMITH_API_KEY` · `LANGSMITH_PROJECT`를 설정한다. 실제 사용자 경로에서는 항상 꺼져 있다.

## 테스트

```sh
# 저장소 루트 — 계산 규칙 (모의 ML · LLM, 외부 호출 없음)
python -m unittest discover -s tests/budget_design

# backend 폴더 — 서버 연결
python manage.py test budgets.tests.test_design_service budgets.tests.test_design_candidates \
  budgets.tests.test_design_selection budgets.tests.test_design_units budgets.tests.test_design_history
```

- `test_budget_inference.py`의 실제 모델 검사 3개는 모델 · 추론 환경이 없으면 건너뛴다.
- 창 관련 검사는 Tk · 화면이 없으면 건너뛴다.
- `test_design_service_llm`은 HTTP 응답을 흉내 내서 실제 LLM을 부르지 않는다.
