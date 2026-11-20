# 머니쿠션 API 명세

서버 API 전체 목록과 공통 코드다. API 하나하나의 보내는 값 · 받는 값 · 실패는 아래 표의 기능별 문서와 Swagger에 있다.

| 문서 | 내용 |
|---|---|
| [API 규칙](../API_RULES.md) | 응답 · 에러 모양, 인증 · CSRF, 요청 번호, 수정 요청(PATCH) 규칙 |
| [Swagger 사용법](../SWAGGER.md) | Django 실행 후 `http://127.0.0.1:8000/api/docs/` (명세) · `/api/docs/runtime/` (직접 실행) |
| [OpenAPI](../openapi/openapi.yaml) | 이 목록과 같은 84개 API의 기계용 명세 (`docs/openapi/parts/*.json`에서 생성) |
| [통합 챗봇](chat.md) | 라우터 · 소비 분석 · 예산 조정 · 청년 정책 에이전트가 채팅 API로 주고받는 모양 |

## 1. 한눈에 보기 — 84개

| # | 기능 | 주소 | 로그인 | 문서 |
|---|---|---|---|---|
| | **공통 · 인증** | | | |
| 1 | 로그인 | `POST /api/auth/login/` | 필요 없음 | [auth.md](auth.md) |
| 2 | 로그아웃 | `POST /api/auth/logout/` | 필요 없음 | [auth.md](auth.md) |
| 3 | 내 계정 확인 | `GET /api/auth/me/` | 필요 | [auth.md](auth.md) |
| 4 | 회원 탈퇴와 전체 데이터 삭제 | `DELETE /api/auth/me/` | 필요 | [auth.md](auth.md) |
| 5 | 회원가입 | `POST /api/auth/signup/` | 필요 없음 | [auth.md](auth.md) |
| 6 | 동의 문서 원문 보기 | `GET /api/consent-documents/` | 필요 없음 | [auth.md](auth.md) |
| 7 | 저장 전 보안값 준비 | `GET /api/csrf/` | 필요 없음 | [auth.md](auth.md) |
| 8 | 마이페이지 실제 요약 | `GET /api/my/` | 필요 | [auth.md](auth.md) |
| | **내 정보** | | | |
| 9 | 내 정보 보기 | `GET /api/profile/` | 필요 | [profile.md](profile.md) |
| 10 | 내 정보 저장 | `PUT /api/profile/` | 필요 | [profile.md](profile.md) |
| | **금융 동의 · 연결** | | | |
| 11 | 계좌 후보 보기 | `GET /api/finance/connect/accounts/` | 필요 | [finance-connect.md](finance-connect.md) |
| 12 | 계좌 선택 저장 | `PUT /api/finance/connect/accounts/` | 필요 | [finance-connect.md](finance-connect.md) |
| 13 | 연결 목록 보기 | `GET /api/finance/connections/` | 필요 | [finance-connect.md](finance-connect.md) |
| 14 | 금융기관 인증 · 새 연결 | `POST /api/finance/connections/` | 필요 | [finance-connect.md](finance-connect.md) |
| 15 | 연결 해제 | `DELETE /api/finance/connections/{connectionId}/` | 필요 | [finance-connect.md](finance-connect.md) |
| 16 | 금융 조회 동의 상태 | `GET /api/finance/consents/` | 필요 | [finance-connect.md](finance-connect.md) |
| 17 | 금융 조회 동의 저장 | `POST /api/finance/consents/` | 필요 | [finance-connect.md](finance-connect.md) |
| 18 | 동의 철회와 해당 범위 데이터 삭제 | `DELETE /api/finance/consents/{scope}/` | 필요 | [finance-connect.md](finance-connect.md) |
| 19 | 금융 정보 다시 불러오기 | `POST /api/finance/sync/` | 필요 | [finance-connect.md](finance-connect.md) |
| | **카드** | | | |
| 20 | 카드 청구서 보기 | `GET /api/finance/card-bills/{id}/` | 필요 | [cards.md](cards.md) |
| 21 | 카드 청구서 납부 확인 저장 | `PUT /api/finance/card-bills/{id}/payment-check/` | 필요 | [cards.md](cards.md) |
| 22 | 카드 청구서 납부 확인 취소 | `DELETE /api/finance/card-bills/{id}/payment-check/` | 필요 | [cards.md](cards.md) |
| 23 | 카드 청구서 납부 거래 보기 | `GET /api/finance/card-bills/{id}/payments/` | 필요 | [cards.md](cards.md) |
| 24 | 카드 청구서 납부 거래 연결 | `POST /api/finance/card-bills/{id}/payments/` | 필요 | [cards.md](cards.md) |
| 25 | 카드 청구서 납부 거래 연결 취소 | `DELETE /api/finance/card-bills/{id}/payments/{transactionId}/` | 필요 | [cards.md](cards.md) |
| 26 | 결제 카드 확인이 필요한 승인 조회 | `GET /api/finance/card-reviews/` | 필요 | [cards.md](cards.md) |
| 27 | 승인 한 건의 결제 카드 확인 | `PUT /api/finance/card-reviews/{id}/` | 필요 | [cards.md](cards.md) |
| 28 | 카드 후보 보기 | `GET /api/finance/connect/cards/` | 필요 | [cards.md](cards.md) |
| 29 | 카드 선택 저장 | `PUT /api/finance/connect/cards/` | 필요 | [cards.md](cards.md) |
| | **대출** | | | |
| 30 | 대출 납부 거래 후보 보기 | `GET /api/finance/loan-dues/{id}/payments/` | 필요 | [loans.md](loans.md) |
| 31 | 대출 납부 거래 연결 · 정정 | `POST /api/finance/loan-dues/{id}/payments/` | 필요 | [loans.md](loans.md) |
| 32 | 대출 납부 거래 연결 취소 | `DELETE /api/finance/loan-dues/{id}/payments/{transactionId}/` | 필요 | [loans.md](loans.md) |
| 33 | 대출 정보 보기 | `GET /api/finance/loans/` | 필요 | [loans.md](loans.md) |
| 34 | 대출 직접 등록 | `POST /api/finance/loans/` | 필요 | [loans.md](loans.md) |
| 35 | 대출 정보 보완 | `PATCH /api/finance/loans/{id}/` | 필요 | [loans.md](loans.md) |
| 36 | 대출 전체 완납 처리 (직접 등록) | `POST /api/finance/loans/{id}/payoff/` | 필요 | [loans.md](loans.md) |
| 37 | 대출 전체 완납 되돌리기 | `POST /api/finance/loans/{id}/payoff/cancel/` | 필요 | [loans.md](loans.md) |
| | **거래** | | | |
| 38 | 거래 목록 보기 | `GET /api/finance/transactions/` | 필요 | [transactions.md](transactions.md) |
| 39 | 거래 한 건 보기 | `GET /api/finance/transactions/{id}/` | 필요 | [transactions.md](transactions.md) |
| 40 | 거래 분류 수정 | `PATCH /api/finance/transactions/{id}/` | 필요 | [transactions.md](transactions.md) |
| | **고정지출** | | | |
| 41 | 고정지출 목록 보기 | `GET /api/budgets/fixed/` | 필요 | [fixed.md](fixed.md) |
| 42 | 고정지출 직접 추가 | `POST /api/budgets/fixed/` | 필요 | [fixed.md](fixed.md) |
| 43 | 고정지출 후보 확정 | `POST /api/budgets/fixed/confirm/` | 필요 | [fixed.md](fixed.md) |
| 44 | 고정지출 후보 무시 | `POST /api/budgets/fixed/ignore/` | 필요 | [fixed.md](fixed.md) |
| 45 | 고정지출 수정 | `PATCH /api/budgets/fixed/{id}/` | 필요 | [fixed.md](fixed.md) |
| 46 | 고정지출 중지 | `DELETE /api/budgets/fixed/{id}/` | 필요 | [fixed.md](fixed.md) |
| | **정기 저축** | | | |
| 47 | 정기 저축 목록 보기 | `GET /api/budgets/savings/` | 필요 | [savings.md](savings.md) |
| 48 | 정기 저축 직접 추가 | `POST /api/budgets/savings/` | 필요 | [savings.md](savings.md) |
| 49 | 정기 저축 후보 확정 | `POST /api/budgets/savings/confirm/` | 필요 | [savings.md](savings.md) |
| 50 | 정기 저축 후보 무시 | `POST /api/budgets/savings/ignore/` | 필요 | [savings.md](savings.md) |
| 51 | 정기 저축 수정 | `PATCH /api/budgets/savings/{id}/` | 필요 | [savings.md](savings.md) |
| 52 | 정기 저축 중지 | `DELETE /api/budgets/savings/{id}/` | 필요 | [savings.md](savings.md) |
| | **홈** | | | |
| 53 | 홈 화면 보기 | `GET /api/home/` | 필요 | [home.md](home.md) |
| | **통합 챗봇** | | | |
| 54 | 이전 대화 보기 | `GET /api/chat/conversations/{id}/` | 필요 | [chat.md](chat.md) |
| 55 | 챗봇 기능 버튼 보기 | `GET /api/chat/messages/` | 필요 | [chat.md](chat.md) |
| 56 | 챗봇에 메시지 보내기 | `POST /api/chat/messages/` | 필요 | [chat.md](chat.md) |
| 57 | 오래 걸리는 작업 진행 확인 | `GET /api/tasks/{id}/` | 필요 | [chat.md](chat.md) |
| | **예산** | | | |
| 58 | 카테고리 예산 보기 | `GET /api/budgets/` | 필요 | [budgets.md](budgets.md) |
| 59 | 예산 조정 AI 외부 전송 동의 보기 | `GET /api/budgets/adjustment-ai-consent/` | 필요 | [budgets.md](budgets.md) |
| 60 | 예산 조정 AI 외부 전송 동의 저장 | `PUT /api/budgets/adjustment-ai-consent/` | 필요 | [budgets.md](budgets.md) |
| 61 | 예산 조정 AI 외부 전송 동의 철회 | `DELETE /api/budgets/adjustment-ai-consent/` | 필요 | [budgets.md](budgets.md) |
| 62 | 예산 AI 외부 전송 동의 보기 | `GET /api/budgets/ai-consent/` | 필요 | [budgets.md](budgets.md) |
| 63 | 예산 AI 외부 전송 동의 저장 | `PUT /api/budgets/ai-consent/` | 필요 | [budgets.md](budgets.md) |
| 64 | 예산 AI 외부 전송 동의 철회 | `DELETE /api/budgets/ai-consent/` | 필요 | [budgets.md](budgets.md) |
| 65 | 예산 조정안 현재 카드 보기 | `GET /api/budgets/proposals/{id}/` | 필요 | [budgets.md](budgets.md) |
| 66 | 월중 예산 조정안 승인 | `POST /api/budgets/proposals/{id}/approve/` | 필요 | [budgets.md](budgets.md) |
| 67 | 지킬 돈 보기 | `GET /api/budgets/protect/` | 필요 | [budgets.md](budgets.md) |
| 68 | 지킬 돈 저장 | `PUT /api/budgets/protect/` | 필요 | [budgets.md](budgets.md) |
| 69 | 추천 예산 만들기 | `POST /api/budgets/recommend/` | 필요 | [budgets.md](budgets.md) |
| 70 | 월급 증가분과 보관한 예산 요청 검토 | `GET /api/budgets/salary-review/` | 필요 | [budgets.md](budgets.md) |
| 71 | 저축 비율 확인 후 월급 증가분 재배분 미리보기 | `POST /api/budgets/salary-review/` | 필요 | [budgets.md](budgets.md) |
| 72 | 월급·급여일 조회 | `GET /api/budgets/salary/` | 필요 | [salary.md](salary.md) |
| 73 | 월급·급여일 저장 | `PUT /api/budgets/salary/` | 필요 | [salary.md](salary.md) |
| 74 | 월급 맞아요 · 아니에요 · 판단 지우기 | `POST /api/budgets/salary/decisions/` | 필요 | [salary.md](salary.md) |
| 75 | 월급 확인할 입금 보기 | `GET /api/budgets/salary/deposits/` | 필요 | [salary.md](salary.md) |
| 76 | 월급 차이 안내에 답하기 | `POST /api/budgets/salary/gap/` | 필요 | [salary.md](salary.md) |
| 77 | 월급 자동 인식 끄기 | `DELETE /api/budgets/salary/pattern/` | 필요 | [salary.md](salary.md) |
| 78 | 예산 승인 | `POST /api/budgets/{id}/approve/` | 필요 | [budgets.md](budgets.md) |
| | **쿠션** | | | |
| 79 | 머니쿠션 보기 | `GET /api/budgets/cushion/` | 필요 | [cushion.md](cushion.md) |
| 80 | 머니쿠션 목표 금액 바꾸기 | `PATCH /api/budgets/cushion/` | 필요 | [cushion.md](cushion.md) |
| | **청년 정책** | | | |
| 81 | 사는 지역 목록 | `GET /api/policies/regions/` | 필요 | [policies.md](policies.md) |
| 82 | 저장한 정책 목록 | `GET /api/policies/saved/` | 필요 | [policies.md](policies.md) |
| 83 | 정책 저장 | `PUT /api/policies/{policyNo}/saved/` | 필요 | [policies.md](policies.md) |
| 84 | 정책 저장 취소 | `DELETE /api/policies/{policyNo}/saved/` | 필요 | [policies.md](policies.md) |

- 로그인은 Django 세션 쿠키다. 저장 · 수정 · 삭제 요청에는 `X-CSRFToken` 헤더가 필요하다 ([API 규칙](../API_RULES.md)).
- 생성 · 확정 요청 일부는 `Idempotency-Key`(요청 번호)를 받는다. 대상 API는 Swagger의 각 API 파라미터에 표시된다.
- 오래 걸리는 작업(금융 조회 · 예산 추천 · 조정)은 `202` + `taskId`를 돌려주고, 결과는 작업 확인 API(`/api/tasks/{id}/`)로 확인한다.

## 2. 공통 코드 — API 값 = DB 값

| 어디 | 코드 | 뜻 |
|---|---|---|
| 카테고리 | `FOOD` · `HOUSING_TELECOM` · `TRANSPORT_CAR` · `HOUSEHOLD` · `FASHION_SHOPPING` · `MEDICAL_HEALTH` · `BEAUTY` · `EDUCATION` · `CULTURE_LEISURE` · `TRAVEL_LODGING` · `ETC` · `UNCLASSIFIED` | 10개 + 기타 + 확인 필요. 응답에는 `categoryName`을 같이 준다. `HOUSING_TELECOM` · `TRAVEL_LODGING`은 예산 밖 지출 |
| 계좌 · 카드 · 연결 `status` | `connected` · `relogin` · `disconnected` | 연결됨 / 다시 로그인 필요 / 연결 해제 |
| 거래 방향 `direction` | `in` · `out` | 입금 / 출금 |
| 거래 유형 `transactionType` | `spending` · `transfer` · `own_transfer` · `card_payment` · `saving` · `loan_repayment` · `income` · `not_spending` | 소비 / 이체 / 내 계좌끼리 / 카드값 / 저축 / 대출 상환 / 입금 / 소비 아님(회사 경비 등) |
| 분류 상태 `classifyState` | `needs_review` · `suggested` · `confirmed` | 확인 필요 / 자동 분류 / 사용자 확정 |
| 분류 출처 `classifiedBy` | `user` · `rule` · `ml` · `llm` | 사용자 / 규칙 · 사전 / ML / LLM |
| 재원 `funding` | `living` · `fixed` | 생활비 / 고정비(생활비 사용액에서 빠짐) |
| 취소 `cancel.state` | `none` · `partial` · `full` | 없음 / 부분 취소 / 전체 취소 |
| 고정지출 · 정기 저축 `status` | `suggested` · `confirmed` · `stopped` · `ignored` | 후보 / 확정 / 중지 / 무시 (목록에는 앞의 둘만) |
| 고정지출 · 정기 저축 `sourceType` | `detected` · `manual` | 거래에서 감지 / 직접 추가 |
| 납부 상태 `paymentState` | `unpaid` · `partial` · `paid` · `needs_review` | 미납 / 일부 / 냄 / 미납 확인 필요 |
| 월급 상태 `salaryState` | `received` · `needs_check` · `waiting` · `unknown` | 받음 / 확인 필요 / 아직 / 실수령액 미등록 |
| 급여 판단 `decision` | `confirmed` · `auto` · `rejected` · `recheck` | 사용자 확인 / 자동 인정 / 아님 / 다시 확인 필요 |
| 대출 `status` · `origin` | `repaying` · `repaid` / `provider` · `manual` | 상환 중 · 완료 / 기관 조회 · 직접 등록 |
| 동의 범위 `productScope` | `bank` · `card` · `loan` | 은행(필수) / 카드 · 대출(선택) |
| 메시지 `role` · `contentType` | `user` · `bot` / `text` · `card` | 보낸 사람 / 내용 종류 |
| 작업 `status` | `queued` · `running` · `succeeded` · `failed` · `canceled` | 대기 / 실행 중 / 성공 / 실패 / 취소 |
| 정책 신청 상태 `applyState` | `open` · `always` · `upcoming` · `unknown` · `closed` | 신청 중 / 상시 / 신청 예정 / 기간 확인 필요 / 마감 |
| 에러 `code` | `invalid` · `parse_error` · `not_authenticated` · `permission_denied` · `not_found` · `method_not_allowed` · `idempotency_conflict` · `consent_required` · `relogin_required` · `provider_unavailable` · `not_ready` · `expired` · `server_error` | [API 규칙](../API_RULES.md)의 에러 표 |

## 3. 화면 → API

| 화면 | 쓰는 API 묶음 |
|---|---|
| 회원가입 · 로그인 · 마이 | 공통 · 인증, 내 정보 |
| 금융 연결 (동의 → 계좌 → 카드 → 대출) | 금융 동의 · 연결, 카드, 대출 |
| 첫 설정 (내 정보 → 월급 → 고정지출 → 저축 → 지킬 돈 → 추천 예산) | 내 정보, 예산(월급 · 지킬 돈 · 추천 · 승인), 고정지출, 정기 저축 |
| 홈 | 홈, 예산(월급 확인 · 차이 안내), 카드(청구서 납부 확인), 대출(납부) |
| 거래 | 거래, 카드(결제 카드 확인) |
| 예산 | 예산 |
| 쿠션 | 쿠션 |
| 챗봇 (소비 분석 · 예산 조정 · 청년 정책) | 통합 챗봇, 청년 정책 |
| 마이 > 연결 관리 · 고정지출 · 정기 저축 · 저장한 정책 · 동의 관리 | 금융 동의 · 연결, 고정지출, 정기 저축, 청년 정책, 공통 · 인증 |
