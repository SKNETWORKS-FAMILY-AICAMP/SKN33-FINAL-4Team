# Swagger API 문서 사용법

서버 API 84개를 OpenAPI 3.0.3으로 정리했다. Swagger UI에서 기능별 요청 · 응답 · 오류 예시를 보고, 개발 서버에서는 직접 실행해 볼 수 있다.

## 실행하고 보기

프로젝트 루트에서 가상환경을 켠 뒤 서버를 실행한다. 처음 세팅은 [로컬 설치 가이드](LOCAL_SETUP.md)를 따른다.

```bash
python backend/manage.py runserver
```

| 주소 | 용도 |
|---|---|
| http://127.0.0.1:8000/api/docs/ | **전체 명세 84개**. 기능별 계약을 읽는 화면이며 실행 버튼은 없다 |
| http://127.0.0.1:8000/api/docs/runtime/ | **현재 서버 확인**. `Try it out → Execute`로 실제 요청을 보낸다. 저장 · 수정 · 삭제까지 실행된다 |
| http://127.0.0.1:8000/api/schema/ | 전체 명세 OpenAPI JSON |
| http://127.0.0.1:8000/api/schema/runtime/ | 현재 서버 확인용 OpenAPI JSON |

- 위 네 주소는 **`DJANGO_DEBUG=True`일 때만** 열린다. 운영(`False`)에서는 JSON 404 `not_found`로 답한다.
- Swagger UI 파일은 `drf-spectacular-sidecar` 패키지에서 제공하며 외부 CDN에 접근하지 않는다.
- 같은 명세 파일: [openapi.yaml](openapi/openapi.yaml) · [openapi.json](openapi/openapi.json) · 목록은 [api/README.md](api/README.md).

## 현재 서버 확인에서 테스트하는 순서

1. `GET /api/csrf/` 실행 → `csrftoken` 쿠키가 생긴다.
2. `POST /api/auth/signup/`(새 연습 계정) 또는 `POST /api/auth/login/` 실행 → 세션 쿠키가 생긴다. 이후 요청에 자동으로 붙는다.
3. `GET /api/auth/me/`로 로그인됐는지 확인한다.
4. 나머지 API를 실행한다. 주소에 `{id}`가 있는 API는 목록 API 응답에서 ID를 복사해 넣는다.
5. 끝나면 `POST /api/auth/logout/`.

- 실제 DB가 바뀌므로 연습용 계정으로 확인한다. 금융 연결 없이 확인하려면 시연 계정([로컬 설치 가이드](LOCAL_SETUP.md) 8단계)을 쓴다.
- 계좌 후보 · 연결 목록 · 거래 · 이전 대화는 **DB에 저장된 데이터만 읽는다**(CODEF를 새로 부르지 않음). 데이터가 없으면 빈 목록이나 404가 정상이다.
- 계좌 후보 · 계좌 선택은 금융 조회 동의(`POST /api/finance/consents/`)를 먼저 해야 한다. 없으면 403 `consent_required`.
- 새 연결 · 다시 불러오기는 CODEF를 호출하고, 결과는 `GET /api/tasks/{id}/`에서 본다.
- 챗봇 자유 대화(예산 조정 · 청년 정책)는 `CHAT_ENGINE=router` · `CHAT_LLM=live`와 실제 자료가 있어야 동작한다.

## 쿠키 · CSRF와 요청 규칙

- 인증은 Django 세션 쿠키 방식이다. JWT나 access token을 입력하지 않는다.
- 회원가입 · 로그인 · 로그아웃을 포함한 저장 요청은 `csrftoken` 쿠키와 `X-CSRFToken` 헤더가 필요하다. 현재 서버 확인 화면은 쿠키 값을 헤더에 자동으로 넣는다. 로그인한 주소와 같은 주소(localhost 또는 127.0.0.1)로 열어야 쿠키가 전달된다.
- 추천 · 예산 승인 · 조정안 승인은 `Idempotency-Key`가 필수이고, 그 밖의 생성 · 확정 요청 일부는 선택이다. 대상은 각 API의 파라미터에 표시된다.
- Swagger 요청은 같은 출처에만 보낸다. 인증 정보를 브라우저 저장소에 남기지 않고, 외부 검증 서버에 명세를 보내지 않는다.
- 필드 이름 · 금액 · ID · PATCH · 오류 응답 규칙은 [API 규칙](API_RULES.md)을 따른다. 명세의 예시는 모두 가상 값이다.

## 파일과 갱신 순서

| 파일 | 역할 |
|---|---|
| `docs/api/*.md`, `docs/API_RULES.md` | 기능별 명세와 공통 규칙 |
| `docs/openapi/parts/*.json` | 기능별 OpenAPI 원본 (요청 · 응답 스키마, 예시, 설명) |
| `backend/config/openapi.py` | 원본을 합치고 공통 정의 · 현재 서버 확인 화면을 구성한다 |
| `docs/openapi/openapi.json` · `openapi.yaml` | 합쳐서 생성한 전체 명세 (직접 고치지 않는다) |
| `backend/config/api_docs.py` | JSON 문서와 Swagger UI 제공 |

명세는 코드에서 자동 생성하지 않고 손으로 관리한다. API를 추가하거나 바꾸면 다음을 함께 고친다.

1. 기능별 Markdown 명세(`docs/api/*.md`)와 목록(`docs/api/README.md`의 '한눈에 보기' 표).
2. 해당 `docs/openapi/parts/*.json`의 필드 · 필수 여부 · 범위 · 오류 · 예시. 새 기능 묶음이면 `backend/config/openapi.py`의 `DOMAINS` · `TAGS`에도 추가한다.
3. 프로젝트 루트에서 다시 생성하고 검증한다.

```bash
python -m pip install -r requirements-docs.txt
python scripts/build_openapi.py --validate          # JSON · YAML 다시 생성 + 예시 검증
python scripts/build_openapi.py --check --validate  # 저장된 파일이 최신인지 확인 (CI와 같음)
```

생성 · 검증에는 데이터베이스가 필요 없다. 생성기는 목록 표와 OpenAPI의 API가 하나라도 다르면 멈춘다. `backend/config/tests/test_openapi.py`는 명세의 인증 · CSRF · 요청 번호 규칙과 예시를 검사한다.

## 참고

- [drf-spectacular 공식 문서](https://drf-spectacular.readthedocs.io/en/stable/readme.html)
- [Swagger UI 설정](https://swagger.io/docs/open-source-tools/swagger-ui/usage/configuration/)
