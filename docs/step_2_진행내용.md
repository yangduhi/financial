# Step 2. MCP 계층 및 데이터 접근 평면 구축

## 1. 목적

이 단계의 목적은 문서와 시장 데이터에 접근하는 MCP 계층을 설계하고 구현하는 것이다.  
핵심은 source를 많이 붙이는 것이 아니라, 모호성, entitlement, provenance, 오류 처리를 통제 가능한 계약으로 고정하는 데 있다.

## 2. 반드시 먼저 읽을 문서

1. `spec.md`
2. `config/sources.yaml`
3. `config/output_paths.yaml`
4. `docs/playbooks/validate-sources.md`

## 3. 선행조건

아래 조건을 모두 만족해야 Step 2 live 구현을 시작할 수 있다.

- Step 1 완료
- `config/sources.yaml`의 `docs_primary`가 `decision_status: decided`
- `config/sources.yaml`의 `market_primary`가 `decision_status: decided`
- 필수 source가 `enabled: true`
- 인증 환경변수 이름이 `config/sources.yaml`에 기록됨

위 조건을 만족하지 못하면 허용 범위는 contract scaffold와 테스트 뼈대 작성까지다.  
live vendor 호출 구현은 시작하지 않는다.

## 4. 이번 단계의 핵심 범위

필수 범위:

- `docs_gateway`
- `market_data_gateway`
- 공통 contract layer
- provenance 구조
- 인증, 권한, 캐시, 재시도 정책
- smoke test와 contract test

선택 범위:

- `research_memory_gateway` 설계 문서

## 5. 필수 파일 및 산출물

Step 2 완료 시점의 최소 산출물:

- `mcp/common/contracts.py`
- `mcp/common/errors.py`
- `mcp/common/provenance.py`
- `mcp/docs_gateway/server.py`
- `mcp/market_data_gateway/server.py`
- `tests/contracts/test_mcp_contracts.py`
- `tests/integration/test_mcp_smoke.py`
- `examples/mcp/docs_gateway.search_documents.response.json`
- `examples/mcp/market_data_gateway.get_price_snapshot.response.json`

## 6. 설계 원칙

### 6.1 Narrow servers

문서 검색과 숫자 조회를 같은 tool로 섞지 않는다.

### 6.2 Strict schemas

모든 tool 입력/출력은 명시적 schema를 가진다.

### 6.3 Full provenance

모든 응답은 최소 아래 필드를 포함한다.

- `source_id`
- `source_type`
- `source_system`
- `retrieved_at`
- `as_of_datetime`
- `license_scope`
- `confidence`
- `content_hash`

### 6.4 Fail loud on ambiguity

entity ambiguity, ticker ambiguity, version ambiguity가 있으면 임의 선택하지 않는다.

## 7. tool 계약

### 7.1 docs_gateway 최소 tool

- `search_documents`
- `fetch_document`
- `extract_sections`
- `get_latest_primary_sources`
- `build_citation_bundle`

### 7.2 market_data_gateway 최소 tool

- `get_price_snapshot`
- `get_price_history`
- `get_fundamentals`
- `get_share_count`
- `get_fx_rate`
- `get_peer_set`

### 7.3 응답 필수 필드

문서 응답:

- `document_id`
- `document_type`
- `issuer`
- `published_at`
- `fiscal_period`
- `uri`

시장 데이터 응답:

- `as_of_datetime`
- `currency`
- `unit`
- `share_basis`
- `vendor`
- `market_session`

## 8. 재시도, 예외, 권한 규칙

- 재시도는 429와 일시적 5xx에만 적용
- 재시도 횟수와 backoff 정책은 코드와 문서에 함께 기록
- source entitlement가 불명확하면 요청을 실패 처리
- stale cache를 최신 응답처럼 반환하지 않는다
- raw secret은 model context에 전달하지 않는다

## 9. 실패 처리 및 재개 규칙

- source 호출 실패는 구조화된 error envelope로 반환한다
- partial failure가 발생하면 성공/실패 source를 함께 기록한다
- sample response는 live 성공 케이스만 저장한다
- unresolved ambiguity는 cache hit이 있더라도 실패 처리한다

## 10. 구현 순서

1. `config/sources.yaml`의 필수 source decision 상태를 확인한다.
2. 공통 contract layer를 구현한다.
3. `docs_gateway` server와 schema를 구현한다.
4. `market_data_gateway` server와 schema를 구현한다.
5. provenance 및 error envelope를 연결한다.
6. smoke test와 contract test를 작성한다.
7. sample response를 `examples/mcp/`에 저장한다.

## 11. 구현 후 검증

아래를 검증한다.

- 각 서버가 최소 3개 이상의 tool을 제공하는가
- 모든 응답에 provenance 필드가 있는가
- `as_of_datetime`, `currency`, `unit`, `share_basis` 누락이 없는가
- ambiguity가 명시적으로 실패하는가
- `tests/contracts/test_mcp_contracts.py`가 통과하는가
- `tests/integration/test_mcp_smoke.py`가 통과하는가

예상 검증 명령:

```powershell
.\.venv311\Scripts\python.exe -m pytest tests\contracts\test_mcp_contracts.py
.\.venv311\Scripts\python.exe -m pytest tests\integration\test_mcp_smoke.py
```

## 12. 완료 기준

아래 조건을 모두 만족하면 Step 2 완료다.

- docs와 market data 접근이 분리된 contract로 동작한다
- sample response가 실제 필드 구조를 보여 준다
- 재시도와 예외 규칙이 문서와 코드에 일치한다
- Step 3가 이 응답을 canonical pipeline 입력으로 사용할 수 있다

## 13. 실패 조건 및 주의사항

- source decision이 비어 있는데 live 구현을 진행함
- 문서와 숫자를 같은 tool 응답으로 섞음
- provenance 없는 텍스트 또는 숫자를 반환함
- ambiguity를 임의 선택으로 처리함
- smoke test 없이 완료 처리함

## 14. 다음 단계 인계물

- `examples/mcp/` sample responses
- contract test 결과
- smoke test 결과
- provenance 필드 정의
- source entitlement와 auth 환경변수 정의 결과
