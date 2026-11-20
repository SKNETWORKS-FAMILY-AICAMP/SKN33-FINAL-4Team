# 프론트엔드(React) 가이드

화면은 **React**(`frontend/`)가 그리고, 데이터는 **Django API**(`backend/`)가 준다.
처음 설정(Python · Docker · `.env`)은 [`LOCAL_SETUP.md`](LOCAL_SETUP.md), API 규칙은 [`API_RULES.md`](API_RULES.md)를 본다.

```
브라우저 ── http://localhost:5173 ──▶ React (Vite 개발 서버)
                                      │  fetch('/api/home/')
                                      ▼  Vite 프록시
                                 Django (127.0.0.1:8000) ──▶ PostgreSQL
```

배포에서는 Caddy가 화면 파일과 `/api/` 요청을 나눠 보낸다 ([AWS 배포](AWS_DEPLOYMENT_GUIDE.md)). 화면 코드는 두 환경에서 같다.

| 항목 | 기준 |
|---|---|
| Node.js | 22.22 이상 (React Router 8 요구) |
| 라이브러리 | React 19 · React Router · lucide-react (아이콘) |
| 도구 | Vite (개발 서버 · 빌드) · oxlint (검사) · Vitest + jsdom (화면 테스트) |

---

## 1. 처음 설정 · 실행

### 1-1. Node.js 설치 (처음 한 번)

| | Windows | macOS |
|---|---|---|
| 설치 | nodejs.org → **22 LTS** 설치 파일 (npm 같이 설치됨) | `brew install node@22` |
| 확인 | `node -v` → **v22.x** · `npm -v` | 같음 |

> 설치 후에는 **터미널을 새로 열어야** `node` 명령이 잡힌다.

### 1-2. 패키지 설치 (처음 한 번 + `package-lock.json`이 바뀌었을 때)

```bash
cd frontend
npm ci
```

`frontend/node_modules/` 폴더가 생기면 성공이다. 이 폴더는 Git에 올라가지 않는다.

### 1-3. 실행 — 터미널 2개

| 터미널 | 할 일 | 명령 |
|---|---|---|
| 1 (가상환경 켜고) | Django API 서버 | `cd backend` → `python manage.py runserver` |
| 2 | React 화면 | `cd frontend` → `npm run dev` |

브라우저에서 **http://localhost:5173**을 연다. 로그인하지 않은 상태면 화면에 '로그인이 필요해요' 안내와 [로그인하기] 버튼이 나온다. 금융 연결 없이 화면을 보려면 [`LOCAL_SETUP.md`](LOCAL_SETUP.md) 8단계의 시연 계정으로 로그인한다. 코드를 저장하면 화면이 바로 바뀐다.

> 서비스는 모바일 웹 화면이다. 크롬 개발자 도구(F12)에서 휴대폰 모양 아이콘을 누르고 기기(예: iPhone)를 고르면 실제 크기로 볼 수 있다. 확대 비율은 100%(`Ctrl/Cmd + 0`)로 맞춘다.

> 다른 포트의 Django에 붙이려면 `API_PROXY_TARGET=http://127.0.0.1:8001 npm run dev`처럼 대상을 바꾼다 (기본 8000).

---

## 2. 폴더 구조

```
frontend/
├── index.html              # 시작 페이지 (글꼴 · 제목)
├── vite.config.js          # /api 요청을 Django(8000)로 넘기는 프록시
├── vitest.config.js        # 화면 테스트 설정 (src/**/*.test.jsx)
├── public/mascots/kushong/ # 캐릭터 쿠숑이 이미지 (포즈별 SVG)
└── src/
    ├── main.jsx            # 앱 시작점 (CSS · 주소 장치 · 팝업 장치 연결)
    ├── App.jsx             # 주소 → 화면 연결 (ROUTES)
    ├── routes.js           # 화면 주소 목록 (PATHS)
    ├── pages/              # 화면 28개 (HomePage.jsx …)
    ├── popups/             # 팝업 (Popup 틀 · PopupProvider · 각 팝업)
    ├── components/         # 공통 부품 (Layout · Header · TabBar · TabHero · Icon …)
    ├── utils/              # 도우미 (api.js · money.js · categories.js · toast.js …)
    └── styles/             # 디자인 CSS
```

테스트 파일(`*.test.jsx` · `*.test.js`)은 대상 파일 바로 옆에 둔다 (예: `pages/HomePage.jsx` ↔ `pages/HomePage.test.jsx`).

| 부품 (`components/`) | 하는 일 |
|---|---|
| `Layout` | 모든 화면의 틀. 상단 바, 본문, 아래 버튼, 팝업 자리, 하단 탭 |
| `TabHero` | 탭 화면 맨 위 색 띠. 문장 제목 + 쿠숑이. 바로 뒤의 `.mc-tabsheet`(흰 시트)가 띠 위로 겹친다 |
| `Mascot` | 쿠숑이 그리기. `<Mascot mood="saver" />` (포즈 이름은 `MASCOT_MOODS`) |
| `Icon` | `<Icon name="CreditCard" />`처럼 이름으로 아이콘 그리기 |
| `ApiStatus` | 불러오는 중 · 오류 안내 카드 (5번 참고) |
| `MoneyInput` · `DayInput` | 금액 · 날짜 입력칸 |
| `HelpTip` | 물음표 아이콘을 누르면 열리는 설명 |
| `StepBar` | 첫 설정 흐름의 "6단계 중 N단계" 막대 |
| `ChatReply` · `BudgetAdjustment` | 챗봇 답변 · 예산 조정 카드 |

| 도우미 (`utils/`) | 하는 일 |
|---|---|
| `api.js` | `useApi`(읽기) · `apiSend`(저장) — 5번 참고 |
| `money.js` | `won(420000)` → `420,000원` · `comma(420000)` → `420,000` |
| `categories.js` | **소비 카테고리 목록 · 아이콘. 카테고리가 필요하면 꼭 여기서만 가져다 쓴다** (`SPEND_CATS` 10개 · `ETC` 기타 · `PENDING` 확인 필요 · `OUT_OF_BUDGET` 예산 밖 주거·통신/여행·숙박 · `BUDGET_CATS` 예산 칸이 있는 카테고리). 화면에 카테고리 이름을 직접 적지 않는다 |
| `toast.js` | `toast('저장했어요')` — 화면 위에 2초 동안 뜨는 안내 |
| `usePicked.js` | 여러 개 고르기 (6번 참고) |
| `days.js` | 날짜 목록 · 급여 주기 계산 |
| `mockSpending.js` | 화면 테스트용 예시 소비 데이터 |

| CSS (`styles/`) | 쓰임 |
|---|---|
| `app.css` | 프로토타입 원본 디자인. **되도록 고치지 않는다** |
| `shell.css` | 모바일 웹 보정 · 덧붙이는 규칙 |
| `tabs.css` | 탭 화면 디자인 (탭마다 띠 색: 홈 파랑 · 거래 흰색 · 예산 라임 · 쿠션 남색 · 챗봇 연파랑) |
| `chat.css` · `policies.css` | 챗봇 화면 · 정책 카드 전용 (해당 화면에서만 불러옴) |

---

## 3. 화면 하나 추가하기 (3단계)

**① `src/routes.js`에 주소 추가**
```js
export const PATHS = {
  // ...
  report: '/report',
}
```

**② `src/pages/ReportPage.jsx` 만들기**
```jsx
import Layout from '../components/Layout.jsx'

export default function ReportPage() {
  return (
    <Layout title="소비 분석" showBack>
      <div className="mc-card">내용</div>
    </Layout>
  )
}
```

**③ `src/App.jsx`의 `ROUTES`에 한 줄 추가**
```jsx
import ReportPage from './pages/ReportPage.jsx'
// ...
[PATHS.report, ReportPage],
```

### `Layout`에 넣을 수 있는 값

| 값 | 뜻 | 예 |
|---|---|---|
| `title` | 상단 제목 | `"카테고리 예산"` |
| `showBack` · `backTo` | 뒤로 가기 버튼 · 앞 화면 기록이 없을 때 갈 곳 | `showBack backTo={PATHS.my}` |
| `activeTab` | 탭 화면이면 켜진 탭. 넣으면 하단 탭과 마이 아이콘이 생기고 탭 색이 적용된다 | `"home"` · `"txs"` · `"budget"` · `"fund"` · `"assistant"` |
| `foot` | 화면 맨 아래 고정 버튼 | `foot={<button className="mc-primary">다음</button>}` |
| `headAction` | 오른쪽 위에 둘 버튼 (홈의 알림 종) | `headAction={<button>…</button>}` |
| `bare` | 상단 바 없이 (로그인 화면) | `bare` |
| `overlay` | 화면 전체를 덮는 안내 (쿠숑이 가이드 투어). 있으면 뒤 화면을 잠근다 | `overlay={<GuideTour … />}` |

### 다른 화면으로 가기
```jsx
import { useNavigate } from 'react-router'
import { PATHS } from '../routes.js'

const navigate = useNavigate()
<button onClick={() => navigate(PATHS.budget)}>예산 보기</button>
```

---

## 4. 팝업

```jsx
import { usePopup } from '../popups/context.js'
import NoticePopup from '../popups/NoticePopup.jsx'

const { openPopup, closePopup } = usePopup()
<button onClick={() => openPopup(<NoticePopup />)}>알림</button>
```

새 팝업은 `Popup` 틀 안에 내용만 넣는다. 배경 누르기, `닫기 ×`, Esc로 닫는 건 틀이 처리한다.
```jsx
import Popup from './Popup.jsx'

export default function HelloPopup({ name }) {        // 값은 props 로 받기
  return (
    <Popup>                                            {/* 큰 시트는 <Popup sub>, 확인 창은 <Popup dialog> */}
      <h2>안녕 {name}</h2>
    </Popup>
  )
}
```
팝업 안에서 다른 팝업을 열면 갈아끼워진다. 다른 화면으로 가면 팝업은 저절로 닫힌다. 팝업이 떠 있는 동안 뒤 화면은 누를 수 없다.

---

## 5. 데이터 (Django API)

```jsx
import { useApi, apiSend } from '../utils/api.js'
import ApiStatus from '../components/ApiStatus.jsx'

// 읽기
const { data, error, reload } = useApi('/api/home/')
if (!data) return <Layout title="홈"><ApiStatus error={error} onRetry={reload} /></Layout>   // 불러오는 중 · 실패

// 저장 (POST · PATCH · DELETE) — 보안 토큰(CSRF)은 자동으로 붙는다
try {
  await apiSend('/api/budgets/fixed/', 'POST', { name: '월세', amount: 700000 })
} catch (err) {
  toast(err.message)     // err.fields = 칸별 에러
}
```

- 주소가 바뀌면(필터 이동) 새 결과가 올 때까지 `data`가 `null`이다. 늦게 온 이전 응답 · 취소된 응답은 버린다.
- 같은 목록을 다시 받을 때는 주소에 `?v=` 같은 숫자를 붙이지 말고 `reload()`를 쓴다. 받는 동안 `data`는 그대로이고 `refreshing`이 `true`다. 실패하면 기본은 `data`가 `null`이 되어 오류 카드가 뜬다.
- 실패해도 지난 목록을 남기고 싶으면 `useApi(path, { keepData: true })`. 이때는 `data`가 있어도 `error`를 꼭 화면에 보여 준다 (예: 거래 내역).
- `<ApiStatus error={error} onRetry={reload} />`는 오류 종류(로그인 필요 · 동의 필요 · 권한 · 404 · 409 · 429 · 일시 실패)에 맞는 안내를 보여 준다. `onRetry`를 생략하면 [다시 시도]가 페이지를 새로고침한다.
- 키 이름은 **camelCase**(`livingUsed`)다. Django가 바꿔서 보낸다.
- 돈은 **원 단위 정수**다. 화면에는 `won(420000)` → `420,000원`으로 보여 준다.
- 요청 · 응답 모양은 [기능별 API 명세](api/README.md)와 개발 서버의 Swagger(`http://127.0.0.1:8000/api/docs/`)를 본다.

### 예산 조정 챗봇 연결

- 추천 작업이 `DESIGN_RECOVERY` 전달 정보와 원 작업 ID를 반환하면 통합 챗봇을 자동으로 열고 `budgetContext: {mode: 'DESIGN_RECOVERY', sourceTaskId}`를 보냅니다. 첫 응답이 유실되면 같은 요청 번호로 확인하며, 대화가 연결된 뒤 새로고침하면 대화 ID로 조회합니다.
- 조정을 취소하면 추천 화면에서 다시 추천받거나 같은 조정 대화를 열 수 있습니다. 만료된 연결은 새 추천을 안내합니다. 검수된 안을 직접 승인하면 ‘반영된 예산 보기’에서 카테고리 예산을 확인할 수 있습니다.
- 추천 예산과 카테고리 예산의 조정 버튼은 통합 챗봇으로 이동하며 첫 메시지에 `budgetContext: {baseBudgetId, mode}`를 보냅니다. 추천 초안은 `INITIAL_ADJUSTMENT`, 승인 예산은 `NORMAL_ADJUSTMENT`입니다. 기준 예산의 소유권·상태는 서버가 다시 검사합니다.
- `ChatReply`는 서버의 `content.budgetAdjustment`가 있으면 `BudgetAdjustment`로 질문·비교·변경안을 표시합니다. 비교 카드의 ‘예산 변화 보기’는 화면에서만 펼칩니다. ‘이 안 선택’은 기존 메시지 선택지의 `{value, turn}`을 그대로 전송합니다.
- 확정 팝업은 변경 내역과 ‘다음 달에도 이 금액 유지’를 보여 줍니다. 초기 체크 상태·유지할 항목은 서버가 준 값입니다. 초안 조정은 `/api/budgets/<proposalId>/approve/`, 월중 조정은 `/api/budgets/proposals/<proposalId>/approve/`에 `{keepForNextCycle}`과 요청 키를 보냅니다.
- 확정 응답이 유실되면 본문과 요청 키를 보존해 같은 요청으로 확인합니다. 확인 전에는 체크 변경·다른 메시지 전송을 막고, 팝업을 닫아도 다시 확인할 수 있습니다. 대화·조정안 ID, 승인 경로·키와 유지 여부만 `sessionStorage`에 남기며 예산 금액은 저장하지 않습니다. 새로고침 시에는 본인 대화에서 조회한 실제 카드 ID·모드·상태와 맞는 기록만 복원합니다. 저장·만료 확인 또는 명시적인 거절 시 기록을 지웁니다. 입력 오류는 선택을 고쳐 새 키로 보내고, `409 expired`는 새 조정을 안내합니다.
- 금액은 원 단위 정수 그대로 표시합니다. 기본 1만 원·필요 시 5천 원 계산, 최소 보장액·잠금액 보호는 서버가 맡습니다. 잠금액과 미배정 여윳돈 잔액을 화면에서 반올림하지 않습니다.

---

## 6. 상태 (눌러서 바뀌는 것)

| 쓰임 | 코드 |
|---|---|
| 하나만 고르기 | `const [dir, setDir] = useState(null)` → `aria-pressed={dir === name}` · `onClick={() => setDir(name)}` |
| 여러 개 고르기 | `const banks = usePicked(['신한'])` → `banks.has(x)` · `banks.toggle(x)` · `banks.list` |
| 입력칸 | `const [pw, setPw] = useState('')` → `value={pw} onChange={(e) => setPw(e.target.value)}` |

> 버튼이 "눌린 모양"인지는 디자인 CSS가 `aria-pressed="true"`를 보고 정한다.

---

## 7. 디자인 · JSX 규칙

- 새 화면 · 수정은 **기존 화면의 스타일을 그대로 따른다.** 비슷한 기존 화면을 열어 같은 클래스를 쓰고, 새 규칙이 필요하면 `app.css` 대신 `shell.css`(탭 화면은 `tabs.css`)에 덧붙인다.
- 클래스 이름은 `mc-`로 시작한다 (`mc-card`, `mc-primary`, `mc-row`, `mc-muted` …).
- 탭 화면은 `<TabHero>` 띠 + `.mc-tabsheet` 흰 시트 구성을 쓴다 (예: `pages/HomePage.jsx`).

| HTML | JSX (React) |
|---|---|
| `class="mc-card"` | `className="mc-card"` |
| `for="birth"` | `htmlFor="birth"` |
| `style="width:40%"` | `style={{ width: '40%' }}` |
| `<br>` · `<input>` | `<br />` · `<input />` (꼭 닫기) |
| 조건부 표시 | `{조건 && <div>…</div>}` |
| 반복 | `{목록.map((x) => <div key={x.id}>…</div>)}` (`key` 필수) |
| `maxlength` · `inputmode` | `maxLength` · `inputMode` |

### 아이콘
- `<Icon name="Wallet" />` 이름은 [lucide.dev/icons](https://lucide.dev/icons)에서 찾는다 (`credit-card` → `CreditCard`).
- 새 아이콘은 `components/Icon.jsx` 위쪽 **두 군데(import · ICONS)**에 이름을 추가해야 나온다. 안 넣으면 동그라미가 그려진다.

---

## 8. 검사 · 테스트 · 빌드

```bash
npm run lint     # oxlint, 경고 0개
npm test         # node --test (utils/*.test.js) + Vitest (src/**/*.test.jsx)
npm run build    # 에러 없이 끝나기
```

CI도 PR · `main` 변경 때 같은 세 명령을 실행한다 ([`ci-cd.yml`](../.github/workflows/ci-cd.yml)).

| 올린다 | 안 올린다 |
|---|---|
| `src/` · `public/` · `package.json` · `package-lock.json` | `node_modules/` · `dist/` (`.gitignore`에 있음) |

> 새 패키지를 넣었으면 `package.json`과 `package-lock.json`을 **같이** 커밋한다.
> `npm` 명령은 **꼭 `frontend` 폴더 안에서** 실행한다. 밖에서 하면 엉뚱한 곳에 `package.json`이 생긴다.

---

## 9. 자주 나는 에러

| 에러 | 원인 | 해결 |
|---|---|---|
| `npm: command not found` / `'npm'은(는) … 아닙니다` | Node.js 미설치 · 터미널을 새로 열지 않음 | 1-1 설치 후 터미널 새로 열기 |
| (Windows) `npm.ps1 파일을 로드할 수 없습니다` | PowerShell 실행 정책 | `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` 한 번 실행 |
| `Failed to resolve import "react-router"` | 패키지 설치 안 함 | `frontend`에서 `npm ci` |
| 오류 카드가 뜨고 데이터가 안 나옴 | Django 서버 꺼짐 | 터미널 1에서 `python manage.py runserver` |
| '로그인이 필요해요' 안내가 뜸 | 로그인하지 않았거나 세션 만료 | [로그인하기]로 다시 로그인 (시연 계정은 `LOCAL_SETUP.md` 8단계) |
| `Port 5173 is in use` | 개발 서버가 이미 켜져 있음 | 켜진 창을 쓰거나 `Ctrl+C`로 끄고 다시 |
| 아이콘이 동그라미로 나옴 | `Icon.jsx` 목록에 없는 이름 | 7. 아이콘 참고 |
| 저장 시 `CSRF Failed` | `fetch`를 직접 씀 | `apiSend` 사용 |
| 화면이 하얗게 비어 있음 | 코드 에러 | F12 → Console의 빨간 글씨 확인 |
