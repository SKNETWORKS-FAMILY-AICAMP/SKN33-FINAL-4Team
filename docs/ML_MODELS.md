# ML 모델

서비스에서 쓰는 모델은 3개다. 모델 파일과 학습 자료는 Git에 없다. 코드는 `scripts/`에, 공유 가능한 집계 지표는 `reports/ml_models/`에 있다.

| 모델 | 하는 일 | 서비스에서 쓰는 곳 | 모델 파일 · 설정 |
|---|---|---|---|
| 거래 분류 SVM | 가게 이름 → 10개 소비 카테고리 | [거래 분류 에이전트](agents/거래분류.md) ④단계 | `spending_category_svm.joblib` · `SPENDING_MODEL_PATH` |
| 생활비 배분 CatBoost | 프로필 + 생활비 → 10개 카테고리 비율 | [예산 설계 에이전트](agents/budget_design.md) A안 · B안 하한 | `budget_allocation.joblib` · `BUDGET_MODEL_PATH` |
| 월 소비 참고 모델 C | 프로필 → 11개 카테고리 월 소비 금액 | 소비 분석의 소비 유형 보조 문장 · 월 소비 비교 | `models/original/C/` · `SPENDING_REFERENCE_ROOT` |

- 모델 파일은 담당자에게 받아 로컬 경로에 둔다. 배포 서버는 `/opt/moneycushion/models`를 `/models`로 읽기 전용 연결한다.
- joblib은 믿을 수 있는 곳에서 받은 파일만 연다. 받은 파일은 SHA256을 확인한다.
- CatBoost와 모델 C는 웹 서버와 패키지 버전이 달라서 **별도 Python**(`BUDGET_INFERENCE_PYTHON`)으로 실행한다. 배포 이미지는 `/opt/budget-inference/bin/python`을 미리 만들어 둔다.
- 모델 파일이 없으면: SVM은 분류 단계가 실패로 기록되고 다음 동기화 때 다시 시도한다. CatBoost는 A/B 추천이 `needs_data`로 멈춘다. 모델 C는 그 문장 · 비교만 빠진다. 배포 스크립트는 SVM 파일과 (A/B를 켰을 때) CatBoost 파일이 없으면 배포를 멈춘다.

## 환경과 테스트

저장소 루트에서 실행한다. Python 3.12. 두 모델의 pandas 버전이 달라 가상환경을 나눈다.

```bash
# SVM
python -m venv .venv-ml
.venv-ml/bin/python -m pip install -r scripts/spending_classifier/requirements.txt
.venv-ml/bin/python -m unittest discover -s tests/ml_models -p 'test_spending*.py' -v

# CatBoost (추론만 하면 requirements-inference.txt만 필요)
python -m venv .venv-budget
.venv-budget/bin/python -m pip install -r scripts/budget_allocation/requirements.txt
.venv-budget/bin/python -m pip install -r scripts/budget_allocation/requirements-inference.txt
.venv-budget/bin/python -m unittest discover -s tests/ml_models -p 'test_allocation*.py' -v
```

Windows는 `.venv-ml/Scripts/python.exe`처럼 바꿔 쓴다. 테스트는 합성 자료와 임시 폴더만 쓰고 재학습은 하지 않는다.

## 1. 거래 분류 SVM

| 항목 | 내용 |
|---|---|
| 모델 | `M2_C1_exclude_brands` (정책 `20261026_books_content_beoltoon_v1`) |
| 방식 | 상호명 정리 → 문자 TF-IDF(char_wb, 1~3글자) → LinearSVC(C=1, balanced) → 5-fold sigmoid 보정 |
| 학습 | 상가 · 통신판매 상호 1,166,171개 (여러 업종 브랜드 후보는 뺌) |
| 출력 | 식비 · 주거·통신 · 교통·차량 · 생활용품 · 패션·쇼핑 · 의료·건강 · 뷰티·미용 · 교육 · 문화·여가 · 여행·숙박. `기타` · `미분류`는 정답에 없다 |
| 서비스 기준 | 확신도 0.85 이상이면 자동 분류. 미만이면 후보 3개를 남기고 검색 단계로 넘긴다 |
| SHA256 | `35cb19686b4ee73dcef9c3512f974ef22b7e18e7052e500a320c83f590d802d5` |

**성능** (`reports/ml_models/spending_classifier.json`)

| 평가 | 정확도 | Macro-F1 |
|---|---|---|
| 검증셋 145,830개 | 85.82% | 0.8234 |
| 실거래 189건 | 87.30% | 0.4581 (10개 고정) |

실거래 정답은 사람 독립 검수 전의 임시 라벨이다.

**상호명 정리**: NFKC · 소문자, 법인 표기 · 공백 · 기호 정리. 괄호 안 내용과 지점명은 남긴다.

**추론**

```bash
.venv-ml/bin/python -m scripts.spending_classifier.predict --model <svm 경로> --names '새봄동물병원' '새봄운전학원'
```

코드에서는 `joblib.load`로 한 번 읽은 묶음을 `scripts.spending_classifier.predict.predict(bundle, names)`에 넘긴다. 정리된 상호, 카테고리, 확신도, 전체 확률이 나온다. 빈 이름은 `UNCLASSIFIED`다.

**다시 학습할 때** (`local_workspace/` 아래 자료 필요)

| 파일 | 필요한 열 |
|---|---|
| `data/store_labels/v3.2_20261020/stores_ml_training.csv` | 상호명, 소비카테고리, 학습대상여부, (정책 보정용) 상권업종소분류명 |
| `data/ml_training_candidates/mail_order_training_candidates_v3_20261020.csv` | 상호, 라벨, 학습사용, (정책 보정용) 인터넷도메인 |
| `data/store_labels/multi_category_brand_candidates.csv` | 브랜드명, 검색키_정규식 |

```bash
P=.venv-ml/bin/python
D=local_workspace/data/spending_classifier
$P -m scripts.spending_classifier.prepare_data --output $D/prepared/shared_baseline
$P -m scripts.spending_classifier.train_eval --data $D/prepared/shared_baseline
$P -m scripts.spending_classifier.correct_policy_data --base $D/prepared/shared_baseline \
   --evaluation $D/evaluation/transaction_labels_v1.csv --output $D/prepared/shared_content_policy
$P -m scripts.spending_classifier.retrain_policy_svm --data $D/prepared/shared_content_policy
```

| 단계 | 하는 일 |
|---|---|
| `prepare_data` | 80% 다수결 라벨, 이름 중복 정리, 그룹 단위 80:10:10 분할 |
| `train_eval` | 후보 비교 → 전체 train 재학습 → 테스트 평가. `--phase compare / fit-final / evaluate`로 나눠 돌릴 수 있다 |
| `correct_policy_data` | 콘텐츠 플랫폼 · 벌툰 업종 보정. 동명 상호는 따로 근거를 본다 |
| `retrain_policy_svm` | 보정 자료 해시 확인 후 SVM만 재학습 |
| `evaluate_csv` | 거래 라벨 CSV로 평가. `--model --input --prepared --output` 모두 지정. 결과에 거래명이 들어가니 로컬에만 둔다 |

문구 업종을 생활용품으로 보정한 재학습 모델(`compare_stationery_policy`로 비교)도 있다. 별도 파일이고 서비스 모델은 바꾸지 않았다.

## 2. 생활비 배분 CatBoost

| 항목 | 내용 |
|---|---|
| 모델 | `catboost_shallow` (`20261026T074827Z_53769d64`) |
| 설정 | depth 4, iterations 200, learning_rate 0.05, MultiRMSE, seed 42 |
| 학습 | 가계동향조사 20~34세 1인 근로자 가구, 2019~2024년 7,936행. 조사 가중치 × 반감기 2년 시간 가중치 |
| 선택 | 2022 · 2023 · 2024 시간순 교차검증, 33개 후보 중 비율 MAE가 가장 낮은 모델 |
| 출력 | 10개 카테고리 비율(합 1). 음수는 0으로 자르고, 모두 0이면 학습 평균 비율로 바꾼다 |

**입력**

| 입력 | 의미 |
|---|---|
| `age` | 20~34세 |
| `sex` | 0=남, 1=여 |
| `disposable_income` | 소득 − 비소비지출 (원, 양수). 모델 안에서 로그 변환 |
| `has_vehicle` | 0=없음, 1=있음 |
| `fixed_expense_amount` | 월세 · 수도 · 관리비 · 연료 · 통신 고정비 |
| `living_budget_amount` | 고정비를 뺀 생활비 (양수) |

**성능** (`reports/ml_models/budget_allocation.json`): 비율 MAE — 교차검증 5.3250%p, 2025년 5.3173%p, 2026년 5.3073%p. 2025 · 2026은 이전에 본 사후 평가 자료다.

**서비스 연결**: 예산 설계가 `scripts/budget_design/inference.py`의 `predict_ml`로 부른다. 금액은 표준입력으로 넘기고, 별도 Python 프로세스(`predict_worker.py`)가 모델을 읽어 비율을 돌려준다.

```bash
# 합성 프로필로 추론 환경 확인
python -m scripts.budget_design.inference

# 모델 단독 실행
.venv-budget/bin/python -m scripts.budget_allocation.predict_allocation --model <모델 경로> \
  --age 27 --sex 0 --disposable-income 3000000 --has-vehicle 1 \
  --fixed-expense-amount 700000 --living-budget-amount 1200000
```

**다시 학습할 때**: `local_workspace/data/household_budget/`에 `household_single_20_34_2019_2025.csv`, `household_single_20_34_2026_holdout.csv`, `category_mapping_v2.csv`, `processing_records.json`이 필요하다.

```bash
.venv-budget/bin/python -m scripts.budget_allocation.compare_allocation_models --output local_workspace/reports/budget_prediction/shared_allocation_comparison
.venv-budget/bin/python -m scripts.budget_allocation.train_allocation --output local_workspace/models/budget_allocation/catboost_shallow
```

저장 후 다시 읽어 같은 예측이 나와야 최종 파일이 만들어진다.

## 3. 월 소비 참고 모델 C

| 항목 | 내용 |
|---|---|
| 모델 | `v13_model_c` · CatBoost 금액 모델 (depth 6, iterations 85, MultiRMSE) |
| 입력 | 나이, 성별, 소득, 차량 대수, 고정비 |
| 출력 | 11개 카테고리(기타 포함) 월 소비 금액 + 카테고리별 평가 MAE |
| 대상 | 20~34세 1인 가구만. 대상 밖이면 부르지 않는다 |
| 코드 | `backend/spending_analysis/benchmark.py` → `scripts/living_expense_prediction/predict_reference.py` |

**필요한 파일** (`SPENDING_REFERENCE_ROOT` 아래, 기본 `local_workspace/models/living_expense_prediction`)

- `models/original/C/model.cbm`
- `models/original/C/metadata.json`
- `reports/tables/observed_metrics.json`

세 파일의 SHA256이 코드에 적힌 값과 다르면 실행하지 않는다. 하나라도 없으면 경고를 한 번 남기고 이 기능만 끈다.

**서비스에서 쓰는 곳** (자세한 규칙은 [챗봇 API](api/chat.md)의 소비 습관 절)

- 소비 유형 카드의 보조 문장 한 줄 "비슷한 조건을 반영한 모델 예상보다 높은 편이에요". 실제 ≥ 예상 × 1.3이고 차이가 기준 금액 1%와 MAE 중 큰 값 이상일 때만. 유형 판정 자체에는 안 쓴다.
- 월 소비 비교. 완전히 수집된 완료 달만 모델 예측과 비교한다. 월 중간 누계와는 비교하지 않는다. MAE보다 작은 차이는 강조하지 않는다.

모델 예측은 또래 평균이나 권장 한도가 아니다. 공개 집계 지표 파일(`reports/ml_models/`)에는 모델 C 평가가 들어 있지 않다.

## 4. 한계

- SVM은 이름만 본다. 같은 이름에 다른 업종이 섞인 가게, 상호처럼 안 생긴 이름은 서비스가 SVM 앞뒤에서 따로 거른다.
- CatBoost는 "생활비 총액이 정해졌을 때 어떻게 나누나"를 배운 모델이다. 생활비가 얼마여야 하는지, 줄인 예산이 적절한지는 말해 주지 않는다.
- 통계 분류 단위 때문에 일부 세부 항목이 옆 카테고리에 들어간다. 2024년 차량 보유 결측을 0으로 처리했고, 반복 조사 가구가 서로 독립이 아닐 수 있다.

## 5. 파일 보관

- 작업 자료 · 모델 · 평가 출력은 `local_workspace/`에 둔다. Git에서 빠져 있는지 `git check-ignore local_workspace/`로 확인한다.
- 원본 · 정제 CSV, 행별 라벨 · 예측, 노트북 출력, 가상환경은 커밋하지 않는다.
