"""docs/openapi/parts/*.json을 합친 OpenAPI 문서. DB나 Django 설정 없이 생성 가능."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PARTS = ROOT / "docs" / "openapi" / "parts"
DOMAINS = ("auth", "profile", "finance-connect", "cards", "loans", "transactions", "fixed", "savings", "home", "chat", "budgets", "salary", "cushion", "policies")
METHODS = {"get", "post", "put", "patch", "delete"}
CATEGORIES = ["FOOD", "HOUSING_TELECOM", "TRANSPORT_CAR", "HOUSEHOLD", "FASHION_SHOPPING", "MEDICAL_HEALTH", "BEAUTY", "EDUCATION", "CULTURE_LEISURE", "TRAVEL_LODGING", "ETC", "UNCLASSIFIED"]
TAGS = ["공통 · 인증", "내 정보", "금융 동의 · 연결", "카드", "대출", "거래", "고정지출", "정기 저축", "홈", "통합 챗봇", "예산", "쿠션", "청년 정책"]

# 모든 API가 구현·계약 검증을 마쳤다. 새 API를 명세만 먼저 추가할 때는 여기에 (method, path): "planned"를 넣는다.
NOT_IMPLEMENTED = {}
IDEMPOTENT_PATHS = {
    "/api/finance/consents/", "/api/finance/loans/", "/api/finance/loan-dues/{id}/payments/", "/api/finance/card-bills/{id}/payments/", "/api/chat/messages/",
    "/api/budgets/recommend/", "/api/budgets/{id}/approve/", "/api/budgets/proposals/{id}/approve/",
    "/api/budgets/salary-review/", "/api/budgets/salary/decisions/", "/api/budgets/salary/gap/",
    "/api/budgets/fixed/", "/api/budgets/fixed/confirm/", "/api/budgets/fixed/ignore/",
    "/api/budgets/savings/", "/api/budgets/savings/confirm/", "/api/budgets/savings/ignore/",
}


def _display(kind):
    return {
        "type": "object", "required": [kind + "Id", "displayName", "status"],
        "properties": {
            kind + "Id": {"type": "string", "format": "uuid"},
            "displayName": {"type": "string", "description": "서버가 만든 표시명. 번호는 끝 네 자리만 표시."},
            "status": {"type": "string", "enum": ["connected", "relogin", "disconnected"]},
        },
    }


def _base():
    return {
        "openapi": "3.0.3",
        "info": {
            "title": "머니쿠션 API 명세서", "version": "1.0.0",
            "description": (
                "머니쿠션 서버 API 전체 명세입니다. 직접 실행은 [현재 서버 확인](/api/docs/runtime/) 화면에서 합니다.\n\n"
                "공통 규칙(docs/API_RULES.md): 요청·응답은 camelCase, 금액은 원 단위 정수, ID는 UUID(청년 정책은 정책번호), "
                "날짜는 YYYY-MM-DD, 시각은 ISO 8601. 빈 값은 null이며 PATCH에서 생략한 칸은 그대로, null은 허용된 칸만 비웁니다. "
                "알 수 없는 요청 칸은 400입니다.\n\n"
                "인증은 Django 세션 쿠키입니다(JWT 없음). 변경 요청에는 X-CSRFToken, 생성·확정 요청에는 Idempotency-Key를 보냅니다. "
                "세션 없음은 403 not_authenticated, 주소의 없는·남의·잘못된 ID는 404, 본문의 부적합한 ID는 400입니다. "
                "오류의 fields는 입력 항목 오류일 때만 있습니다.\n\n"
                "예산 조정·청년 정책 자유 대화는 CHAT_ENGINE=router · CHAT_LLM=live 설정과 실제 자료가 있어야 동작합니다."
            ),
        },
        "servers": [{"url": "/", "description": "문서를 제공하는 동일 서버"}],
        "tags": [{"name": name} for name in TAGS],
        "security": [{"sessionAuth": []}],
        "paths": {},
        "components": {
            "securitySchemes": {"sessionAuth": {
                "type": "apiKey", "in": "cookie", "name": "sessionid",
                "description": "Django 로그인으로 발급되는 세션 쿠키. 브라우저가 동일 출처 요청에 자동 전송. Authorize에 JWT를 넣는 방식이 아닙니다.",
            }},
            "parameters": {
                "CsrfToken": {
                    "name": "X-CSRFToken", "in": "header", "required": True,
                    "description": "GET /api/csrf/로 받은 csrftoken 쿠키 값. 로그인 후 토큰이 바뀌면 최신 값을 사용합니다.",
                    "schema": {"type": "string"},
                },
                "IdempotencyKey": {
                    "name": "Idempotency-Key", "in": "header", "required": False,
                    "description": "화면에서 보내는 요청 번호(선택 헤더, 생략하면 중복 방지 보장 없음). 8~64자 영문·숫자·하이픈·밑줄, UUID도 가능. 같은 회원·번호·내용 재전송은 처음 응답, 내용이 다르면 409. 실패는 기록하지 않음. 폼을 다시 열거나 새 동작을 시작할 때 새 번호를 만듭니다.",
                    "schema": {"type": "string", "minLength": 8, "maxLength": 64, "pattern": "^[A-Za-z0-9_-]{8,64}$"},
                },
            },
            "schemas": {
                "Error": {
                    "type": "object", "required": ["error"],
                    "properties": {"error": {
                        "type": "object", "required": ["code", "message"],
                        "properties": {
                            "code": {"type": "string", "description": "invalid, parse_error, not_authenticated, permission_denied, not_found, method_not_allowed, idempotency_conflict, not_ready, expired, consent_required, relogin_required, provider_unavailable, server_error 등. 사용 가능한 코드는 각 API 참조."},
                            "message": {"type": "string"},
                            "fields": {"type": "object", "description": "입력 항목 오류일 때만 포함. 여러 칸의 조합 오류는 nonFieldErrors.", "additionalProperties": {"type": "array", "items": {"type": "string"}}},
                        },
                    }},
                },
                "AccountDisplay": _display("account"), "CardDisplay": _display("card"),
                "CategoryCode": {"type": "string", "enum": CATEGORIES},
                "SelectableCategoryCode": {"type": "string", "enum": CATEGORIES[:-1], "description": "사용자 선택에는 UNCLASSIFIED 제외. ETC는 선택 가능."},
            },
        },
    }


def operations(schema):
    for path, item in schema["paths"].items():
        for method, operation in item.items():
            if method in METHODS:
                yield path, method, operation


def build_contract():
    schema = _base()
    for domain in DOMAINS:
        part = json.loads((PARTS / f"{domain}.json").read_text(encoding="utf-8"))
        for path, item in part["paths"].items():
            target = schema["paths"].setdefault(path, {})
            if target.keys() & item.keys():
                raise ValueError(f"중복 API: {path}")
            target.update(item)
        for name, component in part.get("components", {}).get("schemas", {}).items():
            if name in schema["components"]["schemas"]:
                raise ValueError(f"중복 schema: {name}")
            schema["components"]["schemas"][name] = component
    for path, method, operation in operations(schema):
        state = NOT_IMPLEMENTED.get((method, path), "implemented")
        operation["x-implementation-status"] = state
        if state != "implemented":
            operation["summary"] = f"[미구현] {operation['summary']}"
        operation["description"] = f"{operation.get('description', '')}\n\n원본: `{operation['x-source']}`"
        if method in {"post", "put", "patch", "delete"}:
            params = operation.setdefault("parameters", [])
            if not any(p.get("name", "").lower() == "x-csrftoken" or p.get("$ref", "").endswith("/CsrfToken") for p in params):
                params.append({"$ref": "#/components/parameters/CsrfToken"})
            if "403" in operation["responses"] and "permission_denied" not in operation["responses"]["403"]["description"]:
                operation["responses"]["403"]["description"] += " CSRF 실패 시 permission_denied."
            if method == "post" and path in IDEMPOTENT_PATHS:
                if not any(p.get("name", "").lower() == "idempotency-key" or p.get("$ref", "").endswith("/IdempotencyKey") for p in params):
                    params.append({"$ref": "#/components/parameters/IdempotencyKey"})
    source_files = ["docs/API_RULES.md", "docs/api/README.md"] + [f"docs/api/{d}.md" for d in DOMAINS]
    # 체크아웃 줄바꿈(CRLF/LF)은 문서 내용 변경으로 보지 않는다.
    schema["x-source-sha256"] = {p: hashlib.sha256((ROOT / p).read_text(encoding="utf-8").encode("utf-8")).hexdigest() for p in source_files}
    return schema


def _sample_schema(value):
    """현 서버 목업 전용: 샘플의 모양을 설명하며 확정 계약으로 사용하지 않는다."""
    if value is None:
        return {"nullable": True, "description": "현재 샘플은 null. 정식 타입은 확정 명세 참조."}
    if isinstance(value, bool):
        return {"type": "boolean"}
    if isinstance(value, int):
        return {"type": "integer"}
    if isinstance(value, float):
        return {"type": "number"}
    if isinstance(value, str):
        return {"type": "string"}
    if isinstance(value, list):
        variants = []
        for item in value:
            item_schema = _sample_schema(item)
            if item_schema not in variants:
                variants.append(item_schema)
        return {"type": "array", "items": {} if not variants else variants[0] if len(variants) == 1 else {"anyOf": variants}}
    return {"type": "object", "properties": {k: _sample_schema(v) for k, v in value.items()}, "required": list(value)}


def _refs(value):
    """값 안의 모든 $ref 주소를 모은다 (실행 화면에 필요한 공통 정의만 남기기 위해)."""
    if isinstance(value, dict):
        found = {value["$ref"]} if isinstance(value.get("$ref"), str) else set()
        for item in value.values():
            found |= _refs(item)
        return found
    if isinstance(value, list):
        return set().union(*(_refs(item) for item in value)) if value else set()
    return set()


def _used_components(contract, paths):
    """실행 화면 경로가 쓰는 components 만 (참조의 참조까지) 복사한다."""
    used, todo = {}, list(_refs(paths))
    while todo:
        ref = todo.pop()
        if not ref.startswith("#/components/"):
            continue
        kind, name = ref.removeprefix("#/components/").split("/", 1)
        if name in used.setdefault(kind, {}):
            continue
        used[kind][name] = deepcopy(contract["components"][kind][name])
        todo.extend(_refs(used[kind][name]))
    return used


def build_runtime_schema():
    # 문서 생성은 DB나 CODEF를 호출하지 않는다.
    contract = build_contract()
    schema = deepcopy(contract)
    schema["paths"] = {}
    schema["security"] = []
    schema["info"]["title"] = "머니쿠션 — 현재 서버 확인"
    schema["info"]["description"] = (
        "현재 서버에서 구현된 API를 직접 실행하는 화면입니다. "
        "순서: ① GET /api/csrf/ → ② POST /api/auth/signup/ 또는 /api/auth/login/ → ③ 나머지 API. "
        "로그인하면 세션 쿠키가 저장되어 이후 요청에 자동으로 붙고, 저장 요청의 X-CSRFToken은 이 화면이 csrftoken 쿠키에서 자동으로 넣습니다. "
        "실제 DB가 바뀌므로 연습용 계정으로 확인하세요. 계좌 후보·거래·이전 대화는 DB에 저장된 데이터가 있어야 결과가 나옵니다(CODEF를 새로 부르지 않음). "
        "새 연결·다시 불러오기는 CODEF를 호출하고, 작업 확인에서 결과를 봅니다. 예산 조정은 router/live 설정과 실제 자료·정책이 필요합니다."
    )
    samples = {"/api/csrf/": {"ok": True}}
    for path, sample in samples.items():
        operation = deepcopy(contract["paths"][path]["get"])
        operation["operationId"] = "runtime_" + operation["operationId"]
        operation["security"] = []
        operation["parameters"] = []
        operation["description"] = "현재 구현의 실제 응답 구조입니다. CSRF 쿠키를 발급합니다."
        operation["responses"] = {"200": {"description": "현재 서버 응답", "content": {"application/json": {"schema": _sample_schema(sample), "example": sample}}}}
        schema["paths"][path] = {"get": operation}
    # 구현된 API는 확정 계약을 그대로 실행 대상으로 넣는다. CSRF 헤더는 화면이 자동으로 채운다.
    implemented = {}
    for path, method, operation in operations(contract):
        if path == "/api/csrf/" or operation["x-implementation-status"] != "implemented":
            continue
        operation = deepcopy(operation)
        operation["operationId"] = "runtime_" + operation["operationId"]
        operation["security"] = []
        operation["parameters"] = [p for p in operation.get("parameters", []) if not p.get("$ref", "").endswith("/CsrfToken")]
        implemented.setdefault(path, {})[method] = operation
        path_parameters = contract["paths"][path].get("parameters")
        if path_parameters:
            implemented[path]["parameters"] = deepcopy(path_parameters)
    schema["paths"].update(implemented)
    used_tags = {tag for item in schema["paths"].values() for m, op in item.items() if m in METHODS for tag in op.get("tags", [])}
    schema["tags"] = [t for t in schema["tags"] if t["name"] in used_tags]
    # 실행 화면은 별도 문서: 실행 대상이 쓰는 정의만 남기고 나머지 확정 계약 모델은 보여 주지 않는다.
    schema["components"] = _used_components(contract, implemented)
    return schema
