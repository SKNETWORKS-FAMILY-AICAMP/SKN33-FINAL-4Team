# 거래 API 명세

> 공통 규칙은 [API_RULES.md](../API_RULES.md), 전체 목록은 [README.md](README.md)를 따른다.

**카테고리 코드 (1번, DB `category.category_code`와 같음)**

| 코드 | 화면 이름 | 코드 | 화면 이름 |
|---|---|---|---|
| `FOOD` | 식비 | `BEAUTY` | 뷰티·미용 |
| `HOUSING_TELECOM` | 주거·통신 | `EDUCATION` | 교육 |
| `TRANSPORT_CAR` | 교통·차량 | `CULTURE_LEISURE` | 문화·여가 |
| `HOUSEHOLD` | 생활용품 | `TRAVEL_LODGING` | 여행·숙박 |
| `FASHION_SHOPPING` | 패션·쇼핑 | `ETC` | 기타 |
| `MEDICAL_HEALTH` | 의료·건강 | `UNCLASSIFIED` | 확인 필요 (고를 수 없음) |

저축 · 투자 · 대출 상환 · 카드값은 카테고리가 아니다.

**공통으로 쓰는 값**

| 값 | 모양 | 뜻 |
|---|---|---|
| 카테고리 | `"category": "FOOD"`, `"categoryName": "식비"` | 키는 `category`, 값은 위 코드. 응답에는 `categoryName`도 준다. 확인 필요 거래는 `"UNCLASSIFIED"` / `"확인 필요"` |
| 분류 상태 `classifyState` | `confirmed` · `suggested` · `needs_review` | 사용자가 확정 / 규칙·ML이 정함 / 확인 필요(미분류). DB `confirmation_state`와 같음. `category = UNCLASSIFIED`이면 항상 `needs_review` |
| 결제 수단 `paymentAccount` · `paymentCard` | `{ "accountId", "displayName", "status" }` · `{ "cardId", "displayName", "status" }` 또는 `null` | `API_RULES.md` '계좌 · 카드 표시'와 같음. 카드 승인 거래는 `paymentCard`만, 계좌 거래는 `paymentAccount`만 채우고 다른 쪽은 `null`. `status`: `connected` · `relogin`(다시 연결 필요) · `disconnected`. `displayName`은 서버가 만든다 |
| 취소 `cancel` | `{ "state": "partial", "amount": 12000 }` | `state`: `none` · `partial` · `full`, `amount`: 취소된 금액(없으면 0) |
| 돈의 출처 `funding` | `living` · `fixed` | 생활비에서 쓴 돈 / 고정비로 연결된 돈(★8, `spending_allocation.funding_bucket`). `fixed`면 생활비 카테고리 사용액에서 빠진다 |

---

## 거래 목록 보기

| 칸 | 내용 |
|---|---|
| 어떤 기능 | 하단 탭 [거래]를 열 때, [필터] 팝업에서 카테고리 · 거래 유형 · 계좌 · 카드를 고를 때 (카테고리 칩 줄을 팝업으로) |
| 어디로 | `GET /api/finance/transactions/` |
| 로그인 필요 | O |

**보내는 값 (주소 뒤 `?` 조건, 모두 선택)**

| 이름 | 타입 | 필수 | 범위·설명 | 예시 |
|---|---|---|---|---|
| `category` | 문자 | X | 카테고리 코드(`UNCLASSIFIED` = 확인 필요만). 없으면 전체. **쉼표로 여러 개**(그중 하나면 나옴). 모르는 코드가 하나라도 있으면 400 | `FOOD,CULTURE_LEISURE` |
| `accountId` | UUID | X | 이 계좌의 거래만. 쉼표로 여러 개. `cardId`와 같이 보내면 **둘 중 하나** | `27d3…` |
| `cardId` | UUID | X | 이 카드의 거래만. 쉼표로 여러 개 | `38e7…` |
| `transactionType` | 문자 | X | 거래 유형만: `spending` 소비 · `income` 입금 · `transfer` 이체(남에게 보낸 이체 + 내 계좌 이체 줄). 쉼표로 여러 개(그중 하나면 나옴). `category`와 같이 보내면 둘 다 만족(카테고리는 소비에만 있음). 모르는 값이면 400 | `income,transfer` |
| `from` | 날짜 | X | 시작일(포함). 없으면 **이번 달 1일**(달력월). 단 `category=UNCLASSIFIED` **하나만** 보내면 기본값 없음(**전체 기간**). 다른 카테고리와 같이 보내면 이번 달 | `2026-10-01` |
| `to` | 날짜 | X | 종료일(포함). 없으면 **오늘** | `2026-10-31` |

```
GET /api/finance/transactions/?category=FOOD&from=2026-10-01&to=2026-10-31
```

> **기간은 달력월 기준이다 (급여 주기 아님).** 거래 화면 제목이 '10월'처럼 달을 보여 주기 때문이다. 홈의 예산·남은 생활비는 **급여 주기** 기준이다. 급여 주기는 **설정한 월급날에 바뀐다**(★14, home.md). 그래서 같은 날 두 화면의 기간과 금액이 다를 수 있다. 홈처럼 이번 주기로 보고 싶으면 `from`·`to`에 주기 시작일·오늘을 보내고, 이때 `period.basis`는 `custom`이 된다.

**받는 값 (200)** — 최신 거래가 먼저(거래일 → 거래 시각 순, 시각이 없으면 같은 날의 맨 뒤). 날짜별 묶음과 날짜 합계는 화면에서 만든다.

| 이름 | 타입 | 뜻 |
|---|---|---|
| `period` | 객체 | 실제로 조회한 기간 `{ "from", "to", "basis" }` |
| `period.basis` | 문자 | `month`(달력월, 기본) · `custom`(`from`·`to`를 보낸 경우) · `all`(`category=UNCLASSIFIED`에 기간을 안 보낸 경우 — 전체 기간, 이때 `period.from`은 가장 오래된 확인 필요 거래일, 없으면 `null`) |
| `summary.spentTotal` | 정수 | **이번 응답 `items` 중 소비 거래(`transactionType: spending`)의 소계**(원) = `netAmount` 합. 입금 · 이체는 넣지 않는다. `category`를 걸면 그 카테고리만의 합 |
| `summary.needsReviewCount` | 정수 | **이번 응답 `items` 중** '확인 필요' 거래 수 |
| `items` | 목록 | 거래 (평평한 목록, 날짜로 묶지 않음) |
| `items[].transactionId` | UUID | 거래 번호 |
| `items[].occurredOn` | 날짜 | 거래일 |
| `items[].occurredTime` | 시각 문자 / null | 거래 시각 `"14:32"` (기관이 주지 않으면 `null`) |
| `items[].direction` | 문자 | `out`(출금) · `in`(입금). DB 코드와 같음 |
| `items[].transactionType` | 문자 | 목록에 나오는 값: `spending`(소비) · `income`(입금) · `transfer`(남에게 보낸 이체) · `not_spending`(사용자가 '소비가 아니에요'로 뺀 소비, 11/13 — 카테고리 · 분류 상태 · `funding`은 `null`, `transactionType` 필터 `spending`에는 안 나옴). DB 코드와 같음 |
| `items[].merchantName` | 문자 | 표시 이름. 카드 = 가맹점명, 계좌 = 적요 |
| `items[].amount` | 정수 | 원거래 금액(원, 0 이상) |
| `items[].cancel` | 객체 | 취소 정보(위 공통 값) |
| `items[].netAmount` | 정수 | 실제 소비 금액 = `amount` − 취소액 (전체 취소면 0) |
| `items[].category` | 문자 / null | 카테고리 코드. 입금 · 이체는 `null` |
| `items[].categoryName` | 문자 / null | 카테고리 화면 이름. 입금 · 이체는 `null` |
| `items[].classifyState` | 문자 / null | 분류 상태. 입금 · 이체는 `null` |
| `items[].paymentCard` | 객체 / null | 결제한 카드 `{ cardId, displayName, status }` |
| `items[].paymentAccount` | 객체 / null | 거래한 계좌 `{ accountId, displayName, status }` |
| `items[].funding` | 문자 / null | `living` · `fixed` (위 공통 값). 입금 · 이체는 `null` |
| `items[].fixedExpenseId` | UUID / null | 이 거래가 연결된 고정지출(★8·13). 없으면 `null` |
| `items[].isSalary` | 불린 | 인정된 월급 입금인지. 사용자가 확인했거나 확인한 기준과 같은 패턴이라 자동 인정된 입금만 `true` — 홈과 같은 저장 근거(`salary_decision`). 판단 없는 후보 · 거절 · 취소 · 내 계좌 이체로 바뀐 거래는 `false`. R12 전 자동 추정은 저장된 판단이 아니라서 `false`로 보인다. 거래 한 건 보기에도 같은 값 |
| `items[].salaryReview` | 문자 또는 `null` | `isSalary`의 근거. `confirmed` 사용자 확인 · `auto` 자동 인정 · 아니면 `null`. 화면 "월급 · 자동 인식" |

> **`summary`는 필터가 걸린 목록의 소계일 뿐이다.** 홈의 '남은 생활비'·'이번 주기 사용액', 예산 화면의 카테고리 사용액과는 **다른 값**이다. 그 값들은 급여 주기 기준이고, 고정비(`funding: fixed`)를 빼는 등 예산 규칙이 들어간 계산이라 이 숫자를 가져다 쓰지 않는다. 이 소계에는 `funding: fixed` 거래도 들어 있다. '확인 필요' 칩과 홈 알림에 붙일 건수는 아래 H-03 기준(기간 없이 전체)이다.

```json
{
  "period": { "from": "2026-10-01", "to": "2026-10-11", "basis": "month" },
  "summary": { "spentTotal": 24800, "needsReviewCount": 1 },
  "items": [
    { "transactionId": "4c0f…", "occurredOn": "2026-10-11", "occurredTime": "18:40", "merchantName": "무신사 스토어", "amount": 89000,
      "cancel": { "state": "full", "amount": 89000 }, "netAmount": 0,
      "category": "FASHION_SHOPPING", "categoryName": "패션·쇼핑", "classifyState": "suggested",
      "paymentCard": { "cardId": "77ab…", "displayName": "신한 Mr.Life · ****5678", "status": "connected" }, "paymentAccount": null,
      "funding": "living", "fixedExpenseId": null, "isSalary": false, "direction": "out", "transactionType": "spending" },
    { "transactionId": "e2a1…", "occurredOn": "2026-10-11", "occurredTime": "12:10", "merchantName": "김밥천국 역삼점", "amount": 18000,
      "cancel": { "state": "none", "amount": 0 }, "netAmount": 18000,
      "category": "FOOD", "categoryName": "식비", "classifyState": "suggested",
      "paymentCard": { "cardId": "1c90…", "displayName": "신한 Deep Dream · ****1234", "status": "connected" }, "paymentAccount": null,
      "funding": "living", "fixedExpenseId": null, "isSalary": false, "direction": "out", "transactionType": "spending" },
    { "transactionId": "9d3b…", "occurredOn": "2026-10-09", "occurredTime": "08:02", "merchantName": "GS25 역삼점", "amount": 6800,
      "cancel": { "state": "none", "amount": 0 }, "netAmount": 6800,
      "category": "UNCLASSIFIED", "categoryName": "확인 필요", "classifyState": "needs_review",
      "paymentCard": { "cardId": "1c90…", "displayName": "신한 Deep Dream · ****1234", "status": "connected" }, "paymentAccount": null,
      "funding": "living", "fixedExpenseId": null, "isSalary": false, "direction": "out", "transactionType": "spending" },
    { "transactionId": "5b7e…", "occurredOn": "2026-10-08", "occurredTime": "19:20", "merchantName": "이하늘", "amount": 30000,
      "cancel": { "state": "none", "amount": 0 }, "netAmount": 30000,
      "category": null, "categoryName": null, "classifyState": null,
      "paymentCard": null, "paymentAccount": { "accountId": "c91d…", "displayName": "국민 급여통장 · ****5678", "status": "connected" },
      "funding": null, "fixedExpenseId": null, "isSalary": false, "direction": "out", "transactionType": "transfer" },
    { "transactionId": "0a42…", "occurredOn": "2026-10-01", "occurredTime": null, "merchantName": "급여", "amount": 2600000,
      "cancel": { "state": "none", "amount": 0 }, "netAmount": 2600000,
      "category": null, "categoryName": null, "classifyState": null,
      "paymentCard": null, "paymentAccount": { "accountId": "c91d…", "displayName": "국민 급여통장 · ****5678", "status": "connected" },
      "funding": null, "fixedExpenseId": null, "isSalary": true, "direction": "in", "transactionType": "income" }
  ]
}
```

- 기간 안에 거래가 없으면 `items: []`, `spentTotal: 0` (200).

**목록에 넣는 거래**

- **소비 거래**(`spending`)와 함께 **입금**(`income`, 월급 등)과 **남에게 보낸 이체**(`transfer`)도 보여 준다.
- 입금 · 이체는 `category: null`이고 **소비 합계(`spentTotal`) · 카테고리 칩 · `needsReviewCount`에 들어가지 않는다.** 카테고리를 걸어 조회하면 나오지 않는다.
- 내 계좌끼리 이체(`own_transfer`) · 저축(`saving`) · 대출 상환(`loan_repayment`) · 카드값(`card_payment`)은 넣지 않는다.
  - **예외**: 이 기능이 자동 분류했거나(`ownTransferReview: auto`) 사용자가 확인한(`confirmed`) 내 계좌 이체는 **출금 쪽 한 줄만** 넣는다. 그 뒤 정기 저축으로 처리돼 `saving`이 된 출금도 넣는다. 되돌릴 수 있게 하려는 것이고 소비 합계에는 들어가지 않는다.
- 각 줄에 `ownTransferReview`(아래 '거래 한 건 보기' 표)를 같이 준다.
  - **예전 기록**: 11/5 전 규칙이 판단 표시 없이 `own_transfer`로 바꾸고 입금과 이은(`OWN_TRANSFER` 연결) 은행 출금은 DB를 고치지 않고 `ownTransferReview: auto`로 읽어 목록에 넣는다 → 사용자가 [맞아요] · [연결 해제]로 확인 · 정정한다(처음 고를 때 표시를 남김). 연결 없는 `own_transfer` · 표시 없는 `saving`은 넣지 않는다. 점검: `python manage.py own_transfer_legacy_check [--ids]` (읽기 전용).
- 적요에 카드사 이름만 있는 출금은 `card_payment`가 아니라 `transfer`(카드값 후보)로 목록에 남는다. 청구서에 연결될 때 카드값이 된다 (cards.md '11/06 추가').
- 고정지출로 연결된 거래(월세 출금, 넷플릭스 카드 결제 등)는 **목록에 넣고** `funding: fixed`로 표시한다. 화면은 '고정' 배지 등으로 구분할 수 있다.

**같은 구매가 두 번 들어올 때 (중복 집계 방지)**

체크카드 결제 1만 원은 **카드 승인**과 **계좌 출금**으로 두 번 들어올 수 있다. DB는 둘을 `transaction_link`(`relation_type = SAME_PURCHASE`)로 잇는다.

- **대표 소비 = 카드 승인 거래.** 가맹점명이 있어서 분류할 수 있기 때문이다.
- `SAME_PURCHASE`로 이어진 **계좌 출금 쪽은 목록에서 빼고**, `summary`와 챗봇 소비 집계에서도 뺀다. 같은 구매는 한 번만 센다.
- 아직 연결되지 않은 계좌 출금은 그대로 보이고 합계에 들어간다. 연결이 확인되면 사라진다.
- 신용카드 **대금 납부**(계좌 → 카드사)는 카드값이라 소비 목록·합계에 넣지 않는다(이미 카드 승인으로 셌음).

**정해진 것**

- 목록 모양은 `{ items, period, summary }`다.

**실패하면**

| 상황 | 상태 | `code` | 화면 안내 |
|---|---|---|---|
| 모르는 카테고리 코드 | 400 | `invalid` | (개발 중 버그) `fields.category` |
| 날짜 형식이 틀리거나 `from`이 `to`보다 늦음 | 400 | `invalid` | "기간을 다시 골라 주세요." (`fields.from`) |
| `accountId` · `cardId`가 UUID 형식이 아니거나 · 없거나 · 남의 것 | 400 | `invalid` | "선택할 수 없는 계좌 · 카드예요." (`fields.accountId` · `fields.cardId`) |
| 로그인 안 함 | 403 | `not_authenticated` | 로그인 화면으로 |

**홈 '확인할 거래 수' = 확인 필요 거래 전체 개수, 최신순**

| 조건 | 내용 |
|---|---|
| 대상 거래 | 목록의 **소비 거래**(`transactionType: spending`)만. 입금 · 이체 · 카드값 · `SAME_PURCHASE` 계좌 출금 제외 |
| 분류 | `category = UNCLASSIFIED` (`classifyState: needs_review`) |
| 기간 | **제한 없음 (전체 기간).** 지난 주기 · 지난달에 처리 못 한 거래도 사라지지 않고 남는다 |
| 정렬 | **최신순** (거래일 → 거래 시각) |
| 같은 숫자를 목록에서 보려면 | `GET /api/finance/transactions/?category=UNCLASSIFIED` (기간 안 보냄)의 `summary.needsReviewCount` = 홈 숫자 |

- 홈의 [확인할 거래 N건 ›]과 거래 화면의 '확인 필요' 칩은 모두 위 요청을 쓴다. 그래야 숫자와 목록이 같다.
- `category=UNCLASSIFIED`에 기간을 안 보내면 전체 기간(`period.basis: all`), 기간을 보내면 그 기간만(`custom`). 다른 카테고리 · 전체 보기의 기본 기간은 그대로 달력월이다.

- 거래 유형만 보려면 `transactionType`(소비 · 입금 · 이체 등)을 쓴다. 입금 중 월급은 '월급' 표시로 구분한다

---

## 거래 한 건 보기

| 칸 | 내용 |
|---|---|
| 어떤 기능 | 거래 목록에서 거래 하나를 눌러 상세 화면(또는 '확인 필요' 카드)을 열 때 |
| 어디로 | `GET /api/finance/transactions/<uuid:transaction_id>/` |
| 로그인 필요 | O |

**보내는 값** — 없음 (주소의 ID = `transactionId`)

**받는 값 (200)** — 목록의 한 줄(위 `items[]`)에 아래 칸을 더한다

| 이름 | 타입 | 뜻 |
|---|---|---|
| `direction` | 문자 | `out`(출금) · `in`(입금). DB 코드와 같음 |
| `transactionType` | 문자 | 거래 유형. DB 코드와 같음. `transfer`(남에게 보낸 이체)면 화면에 **[소비로 분류하기]** 를 보여 준다 |
| `installmentMonths` | 정수 / null | 할부 개월(일시불 0, 계좌 거래 `null`) |
| `suggestion` | 객체 / null | 서비스가 제안한 분류. 사용자가 이미 확정했으면 `null` |
| `suggestion.candidates` | 목록 | 후보 카테고리, 확신도 높은 순 `[{ "category", "categoryName" }]` |
| `suggestion.reason` | 문자 / null | 확인 필요 이유(사용자에게 보여 줄 문장) |
| `classifiedBy` | 문자 / null | 분류 출처: `user` · `rule` · `ml` · `llm`. DB `classification_source`와 같음 |
| `wasTransfer` | 불린 | 원래 이체였다가 소비로 바뀐 거래인지. `true`면 화면이 [이체로 되돌리기](`category: null`)를 보여 준다. 고정지출에 연결된 거래는 `true`여도 되돌리기가 400 |
| `ownTransferReview` | 문자 / null | 내 계좌 이체 판단. `transfer` · `own_transfer` · `saving` 출금만, 그 밖은 `null`. `suggested` = 출금 적요가 가입 이름(`nickname`)과 같아 **추정**(유형은 `transfer` 그대로, 화면 [맞아요]/[아니에요]) · `auto` = 규칙이 내 다른 계좌의 입금과 묶어 **자동 분류**(`own_transfer`, 그 뒤 저축 처리되면 `saving`. 확실한 식별이 아니라 규칙 추정 — [맞아요]/[연결 해제]. 기준은 아래 '내 계좌 이체 자동 분류') · `confirmed` = 사용자가 [맞아요](`own_transfer`, [확인 취소]) · `rejected` = 사용자가 [아니에요] · 확인 취소 · 연결 해제(`transfer`). `field_states` 원값은 내보내지 않는다 |
| `ownTransferRecheck` | 불린 | `auto`인데 나중에 들어온 거래로 상대 후보가 여럿이 됐지만, 저축 · 납부 · 고정지출 근거라 자동으로 풀지 않은 연결이면 `true`. 화면은 "다시 확인해 주세요"를 보여 주고 같은 상세에서 [맞아요]/[연결 해제]로 정정한다 |
| `canApplyToFuture` | 불린 | 화면에 "앞으로 이 가게 거래도 이 카테고리로" 체크박스를 보여 줄지. 소비 거래이고 페이 충전이 아니면 `true`. 다품목 가맹점도 `true`다. 이체는 `false`(받는 사람은 기억하지 않음, W) |
| `updatedAt` | 시각 | 마지막 수정 시각 |

```json
{
  "transactionId": "9d3b…", "occurredOn": "2026-10-09", "occurredTime": "08:02", "merchantName": "쿠팡", "amount": 6800,
  "cancel": { "state": "none", "amount": 0 }, "netAmount": 6800,
  "category": "UNCLASSIFIED", "categoryName": "확인 필요", "classifyState": "needs_review",
  "paymentCard": { "cardId": "1c90…", "displayName": "신한 Deep Dream · ****1234", "status": "connected" }, "paymentAccount": null,
  "funding": "living", "fixedExpenseId": null,
  "direction": "out", "transactionType": "spending", "installmentMonths": 0,
  "suggestion": {
    "candidates": [ { "category": "FOOD", "categoryName": "식비" }, { "category": "HOUSEHOLD", "categoryName": "생활용품" } ],
    "reason": "여러 종류의 물건을 파는 곳이라 무엇을 샀는지 골라 주세요."
  },
  "classifiedBy": null,
  "canApplyToFuture": true,
  "wasTransfer": false,
  "isSalary": false,
  "updatedAt": "2026-10-09T08:05:00+09:00"
}
```

**실패하면**

| 상황 | 상태 | `code` | 화면 안내 |
|---|---|---|---|
| 없는 거래 · 남의 거래 · **목록에 안 나오는 거래**(★3: `SAME_PURCHASE`로 빠진 계좌 출금, 카드값 등) | 404 | `not_found` | "거래를 찾을 수 없어요." |
| 로그인 안 함 | 403 | `not_authenticated` | 로그인 화면으로 |

**정해진 것**

- 후보의 확신도 숫자(`confidence`)는 화면에 보내지 않는다.
- 카드 승인번호 · 거래 후 잔액 등 원천 상세는 보여 주지 않는다.

---

## 거래 분류 수정

| 칸 | 내용 |
|---|---|
| 어떤 기능 | 거래 상세 또는 '확인 필요' 카드에서 카테고리를 고르고 [저장]할 때, 이체 상세에서 [소비로 분류하기]를 할 때 |
| 어디로 | `PATCH /api/finance/transactions/<uuid:transaction_id>/` |
| 로그인 필요 | O |

**보내는 값** — 보낼 수 있는 칸은 아래 네 개뿐이다. `category`(+ `applyToFuture`) · `ownTransfer` · `notSpending` 중 하나만 보낸다.

| 이름 | 타입 | 필수 | 범위·설명 | 예시 |
|---|---|---|---|---|
| `category` | 문자 / null | O | 10개 카테고리 + `ETC`(기타) 중 하나. `UNCLASSIFIED`는 보낼 수 없음. `null`은 **원래 이체였던 거래를 다시 이체로 돌릴 때만** | `"FOOD"` |
| `ownTransfer` | 불린 | X | 내 계좌 이체 확인. 다른 칸과 같이 보내면 400. 아래 '내 계좌 이체 확인' | `true` |
| `notSpending` | 불린 | X | '소비가 아니에요'. 다른 칸과 같이 보내면 400. 아래 '소비가 아니에요' | `true` |
| `applyToFuture` | 불린 | X (기본 `false`) | `true`면 **같은 가맹점의 다음 새 거래**와 **이미 '확인 필요'로 남아 있는 같은 가맹점 거래**도 이 카테고리로 자동 분류. `canApplyToFuture: false`인 거래에 `true`를 보내도 400을 내지 않고 재사용하지 않는다 | `true` |

```json
{ "category": "FOOD", "applyToFuture": true }
```

- 금액·날짜·가맹점명·`classifyState`·`funding` 등 표에 없는 칸을 보내면 **400 "이 칸은 보낼 수 없어요."**
- 이미 같은 카테고리로 확정된 거래에 같은 값을 다시 보내면 **성공(200)** 으로 같은 결과를 돌려준다(0번 '같은 요청 두 번').
- 저장하면 이 거래는 사용자 확정(`classifyState: confirmed`, `classifiedBy: user`)이 된다.
- **같은 가맹점의 다음 거래에 쓰기**: `applyToFuture: true`로 저장했을 때만, 이후 같은 가맹점의 새 거래가 이 카테고리를 먼저 쓴다(`finance/merchant_rules.py`의 `remembered_category()`, 출처 `rule`).
    - 이름이 같아도 카드사 업종이 분명히 다르면 다른 가게로 보고 재사용하지 않는다.
    - **이미 '확인 필요'로 남아 있는 같은 가맹점 거래도 저장할 때 함께 분류한다.** 새 거래가 기억으로 분류될 때와 같게 출처 `rule`, 상태 `suggested`. 사용자가 이미 고른 거래 · 자동 분류된 거래 · 업종이 다른 같은 이름 가게는 그대로 둔다 (`merchant_rules.same_store_pending()`).
    - 기준은 같은 가맹점에서 사용자가 고른 거래 중 **가장 최근 거래**(거래일 순, 같은 날이면 마지막 수정 순)다. 그 거래가 `applyToFuture: true`일 때만 재사용하고, 아니면 재사용하지 않는다. 사용자가 선택을 바꾸면 마지막 선택을 따른다.
    - 새 칸 없이 그 거래의 `field_states.apply_to_future = true`로 남긴다. API 응답에는 내보내지 않는다.
    - 10/30 이전에 확정한 거래는 이 표시가 없어서 재사용되지 않는다.
- **단, 페이 충전은 기억하지 않는다** (`applyToFuture`를 보내도 같음). 다품목 가맹점은 `applyToFuture: true`일 때만 기억한다. 체크하지 않으면 백화점·종합 온라인몰은 **다음 거래가 다시 `UNCLASSIFIED`** 로 들어오고, 편의점·슈퍼마켓·대형마트는 식비, 다이소는 생활용품으로 자동 분류된다.
- 고정지출로 연결된 거래(`funding: fixed`)도 카테고리는 바꿀 수 있다. 돈의 출처(고정비)는 그대로다.
- **고정지출에 연결된 이체**: 월세를 집주인에게 계좌이체로 내는 경우처럼, 남에게 보낸 이체(`transfer`)가 확정된 고정지출의 납부 예정과 **금액 · 날짜(±3일)로 연결되면** 소비로 본다.
    - `transactionType` `transfer` → `spending`, 카테고리는 **그 고정지출의 카테고리**, `funding: fixed`('고정' 표시). 생활비 사용액엔 안 들어가고 소비 분석엔 `fixedAmount`로 들어간다.
    - 연결을 풀면 다시 `transfer`(카테고리 · `funding` 비움).
    - 연결은 매칭 입구 6번 `match_payment_dues`가 한다. 사용자가 PATCH로 카테고리를 바꿔도 연결은 그대로다.
    - 고정지출에 연결된 이체에 `category: null`을 보내면 400 — 고정지출 연결을 먼저 풀어야 이체로 돌아간다.
- **이체를 소비로 바꾸기**: 남에게 보낸 이체(`transfer`)에 카테고리를 보내면 `transactionType`이 `spending`이 되고 소비 합계 · 예산에 들어간다(`classifyState: confirmed`, `classifiedBy: user`).
    - `category: null`을 보내면 다시 `transfer`로 돌아간다. **원래 이체였던 거래만** 된다. 원래 소비였던 거래에 `null`을 보내면 400.
    - 이체의 **받는 사람은 기억하지 않는다.** 같은 사람에게 다음에 보낸 이체는 다시 `transfer`로 들어온다(`remembered_category()`를 쓰지 않음).
- 입금(`income`) 거래는 카테고리를 고를 수 없다 → 400 (아래 실패 표).
- **'원래 이체였던 거래' 표시**: 새 칸 없이 거래의 `field_states.original_transaction_type = "transfer"`로 남긴다. 사용자가 소비로 바꾼 이체 · 고정지출 근거로 연결되어 소비가 된 이체 모두. `category: null`로 되돌릴 수 있는지, 연결을 풀 때 무엇으로 돌릴지 이 값으로 판단한다. 원값은 내보내지 않고, 거래 한 건 보기에 `wasTransfer`(불린)만 준다.
- **소비가 아니에요** — `{"notSpending": true | false}`. 회사 경비로 돌려받는 돈 · 친구 대신 낸 돈처럼 내가 쓴 돈이 아닌 소비를 뺀다.
    - `true`: 소비(`spending`) → `not_spending`. 예산 사용액 · 홈 · 소비 분석 · 챗봇은 `spending`만 세서 모두 빠진다. 거래 목록(전체)에는 남는다. '확인 필요' 수에서도 빠진다.
    - `false`: `not_spending` → `spending`. 카테고리 · 분류 상태는 바꾸지 않고 두었으므로 원래대로 돌아온다(확인 필요였으면 다시 확인 필요).
    - 400: 소비가 아닌 거래(입금 · 이체 · 내 계좌 이체 등)에 `true`, 소비 아님이 아닌 거래에 `false`(이미 소비면 200), 전액 취소 거래, 고정지출에 연결된 소비("고정지출에 연결된 거래예요. 고정지출 연결을 먼저 풀어 주세요."). `not_spending` 거래에 `category`를 보내면 400 "소비로 되돌린 뒤 카테고리를 고를 수 있어요."
    - 이미 원하는 상태면 200. 잠금: 회원 → 거래. DB: `financial_transaction.transaction_type`에 `not_spending` 추가 (DB_MODELS.md).
    - 카드 첫 청구서 선차감은 '예산에 이미 잡힌 소비'만 빼므로, 소비 아님으로 뺀 카드 사용은 청구서 미리 떼기에 남는다(실제로 카드값으로 나가는 돈).
- **내 계좌 이체 확인** — `{"ownTransfer": true | false}`
    - `true` [맞아요]: `suggested` · `rejected`인 `transfer` → **이 출금만** `own_transfer`(`confirmed`). 같은 금액 입금 등 다른 거래로 넓히지 않는다. `auto`면 연결 · 유형(`own_transfer` · `saving`)은 그대로 두고 `confirmed`로만 바꾼다.
    - `false` [아니에요] · 확인 취소 · 연결 해제: → `transfer`(`rejected`). 규칙이 이은 입금이 있으면 연결(`OWN_TRANSFER`)을 지우고 입금을 `income`으로 되돌린 뒤 입금에도 `rejected`를 남겨 다시 잇지 않는다. 거절해도 **소비로 바꾸지 않는다** — 소비로 넣으려면 [소비로 분류하기].
    - **저축으로 처리된 출금(`saving`)** 에 `false`: 그 출금을 정기 저축의 근거 이체(`evidence`)에서 빼고 `transfer`로 되돌린다. 저축 자체(상태 · 금액 · 다른 근거)는 그대로이고, 저축 화면의 '근거 이체 수'가 하나 줄어든다. 이 출금은 이후 저축 자동 처리(`match_savings`)에서도 빠진다. 고정지출 근거이기도 하면 400 "고정지출 근거로 쓰인 거래예요. 고정지출 화면에서 먼저 정리해 주세요." 저축 화면에는 거래 한 건을 빼는 기능이 없어서 정정은 거래 상세에서만 한다.
    - 바꿀 수 있는 거래 (잠근 뒤 다시 읽은 **지금 상태** 기준): `suggested` · `rejected`인 `transfer`(사용자 확정 아님), `auto` · `confirmed`인 `own_transfer` · `saving` 은행 출금. 판단 표시가 남아 있어도 지금 유형이 소비 등이면(사용자가 [소비로 분류하기]를 함) `true` · `false` 모두 400 — 오래된 화면의 요청이나 동시 요청이 사용자 분류를 덮지 않는다. 취소 거래 · 납부(카드값 · 대출 · 고정지출 회차)에 붙은 출금 · 고정비로 충당된 출금도 400. 이미 원하는 상태면 200.
    - 사용자 판단은 재수집 · 저장 뒤 처리 · 이름 변경으로 덮어쓰지 않는다. 저장은 `field_states.own_transfer_review`.
    - `own_transfer` · `saving` 거래에 `category`를 보내면 400 — 확인을 먼저 취소한다.
    - 잠금: 회원 → 거래 (저장 뒤 처리와 같은 순서).
- **내 계좌 이체 자동 분류 (최종 기준, `finance/transfer_rules.py`)** — 거래 저장 뒤 1단계 `link_basics`
    - **양쪽 거래가 다 있으면 `auto`**: 같은 회원의 서로 다른 계좌 · 출금 ↔ 입금 · 같은 금액 · 시각 차이 **5분 이내**(5분 포함, 날짜와 시각을 합쳐 비교해 자정 넘김도 봄) · **양쪽 대표 적요가 모두 가입 이름**(공백 · 대소문자 정리 후 전체 일치) · 양쪽에서 맞는 상대가 **각각 하나뿐**(상대 거래의 유형과 상관없이 셈). 양쪽 거래와 연결(`OWN_TRANSFER`)을 한 트랜잭션에서 바꾼다.
    - 하지 않는 경우: 시각 없음 · 가입 이름이 비었음 · 적요끼리만 같음("이체" 등) · 부분 일치 · 후보가 여럿 · 취소 · 사용자 확정 · 납부 · 같은 구매 · 이미 이은 거래 · 사용자 판단(`confirmed` · `rejected`)이 있는 거래.
    - **상대 거래가 없거나 모호하면 `suggested`**: 출금 적요가 가입 이름이면 일반 이체(`transfer`) 그대로 추정만 남긴다. 상대 입금이 나중에 들어와 조건을 다 맞추면 `auto`로 올린다.
    - **늦게 온 거래로 다시 보기**: 새 거래가 기존 `auto` 연결의 후보가 되면 그 연결을 다시 본다. 여전히 양쪽 유일이면 둔다. 모호해졌으면 연결을 지우고 출금은 `transfer`(이름이 같으면 `suggested`), 입금은 `income`으로 되돌린다 — 다른 후보에 갈아 붙이지 않는다. 그래서 한꺼번에 받든 나눠 받든 결과가 같다. 사용자가 확인한 연결(`confirmed`)은 그대로. 저축으로 바뀌었거나 저축 · 고정지출 근거 · 납부에 붙은 연결은 풀지 않고 `ownTransferRecheck: true`로 표시한다(정정은 거래 상세).
    - CODEF 은행 거래에는 상대 계좌번호나 양쪽 송금을 잇는 식별값이 없어서(적요 1~4칸뿐) 이 규칙은 **추정**이다. `source_key`는 쓰지 않는다.
- 이 요청은 같은 값을 두 번 보내도 결과가 같아서 요청 번호(`Idempotency-Key`)를 쓰지 않는다(★4: 새로 만들기 · 승인 요청만).

**받는 값 (200)** — 바뀐 거래 한 건(`GET /api/finance/transactions/<id>/`와 같은 모양)

```json
{
  "transactionId": "9d3b…", "merchantName": "GS25 역삼점",
  "category": "FOOD", "categoryName": "식비", "classifyState": "confirmed", "classifiedBy": "user",
  "suggestion": null, "updatedAt": "2026-10-22T09:12:00+09:00", "…": "…"
}
```

**실패하면**

| 상황 | 상태 | `code` | 화면 안내 |
|---|---|---|---|
| `category`가 없음, 모르는 코드, `UNCLASSIFIED`, 원래 소비였던 거래에 `null` | 400 | `invalid` | "카테고리를 다시 골라 주세요." (`fields.category`) |
| 입금(`income`) 거래에 카테고리를 보냄 | 400 | `invalid` | "이 거래는 카테고리를 고를 수 없어요." (`fields.category`) |
| 내 계좌 이체(`own_transfer`) · 저축(`saving`)에 카테고리를 보냄 | 400 | `invalid` | "내 계좌 이체 확인을 먼저 취소해 주세요." (`fields.category`) |
| `ownTransfer`를 바꿀 수 없는 거래 (판단 없음 · 지금 소비 등 다른 유형 · 입금 · 취소 · 납부 연결 · 고정비 충당) | 400 | `invalid` | "내 계좌 이체로 확인할 수 없는 거래예요." (`fields.ownTransfer`) |
| `ownTransfer`를 다른 칸과 같이 보냄 · 불린이 아님 | 400 | `invalid` | `fields.ownTransfer` |
| 표에 없는 칸을 보냄 | 400 | `invalid` | `fields.<그 칸>: ["이 칸은 보낼 수 없어요."]` |
| 없는 거래 · 남의 거래 · 목록에 안 나오는 거래 | 404 | `not_found` | "거래를 찾을 수 없어요." |
| 로그인 안 함 | 403 | `not_authenticated` | 로그인 화면으로 |
| 저장 보안값(CSRF) 없음 | 403 | `permission_denied` | "다시 시도해 주세요." |

**정해진 것**

- 같은 가맹점의 이미 있는 거래를 **한꺼번에 바꾸지 않는다** (새 거래에만 반영, `sameMerchantUpdatedCount` 없음).
- 확정한 분류를 '확인 필요'로 **되돌리는 기능은 없다.** (다른 카테고리로 다시 고르는 것은 됨)
- 백화점 · 종합 온라인몰 등 다품목 가맹점은 **사용자에게 물어본다.** 편의점 · 마트는 **식비**, 다이소는 **생활용품**으로 자동 분류한다. 사용자가 "앞으로도 적용"을 고른 가게는 그 선택이 먼저다.
- 같은 가맹점 재사용은 사용자가 "앞으로도 적용"(`applyToFuture`)을 고른 경우에만.

---
