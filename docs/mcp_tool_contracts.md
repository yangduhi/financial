# MCP Tool Contracts

## Scope

이 문서는 자연어 질의용 intent-level MCP tool contract를 정의한다.

## Tools

### `resolve_entity`

목적:

- 질의의 엔티티 표현을 canonical identifier로 고정

필수 입력:

- `query`
- `entity_type`
- `market_hint`
- `max_candidates`

필수 출력:

- `status`
- `selected`
- `candidates`
- `confidence`
- `source`

상태값:

- `RESOLVED`
- `AMBIGUOUS`
- `NOT_FOUND`

### `get_quarterly_metrics`

목적:

- 분기별 원값 조회

필수 입력:

- `identifier`
- `metrics`
- `quarter_count`
- `period_basis`
- `include_source`

필수 출력:

- `status`
- `identifier`
- `currency`
- `unit_map`
- `periods`

상태값:

- `OK`
- `PARTIAL`
- `NOT_FOUND`

### `get_metric_trend`

목적:

- q/q, y/y, summary flag를 포함한 trend 구조 제공

필수 입력:

- `identifier`
- `metric`
- `quarter_count`
- `include_qoq`
- `include_yoy`
- `include_summary_flags`

필수 출력:

- `status`
- `metric`
- `currency`
- `unit`
- `series`
- `trend_flags`
- `summary_stats`
- `sources`

상태값:

- `OK`
- `PARTIAL`
- `NOT_FOUND`

### `get_recent_filings`

목적:

- 최근 filing 또는 earnings 자료 후보 조회

필수 입력:

- `identifier`
- `doc_types`
- `limit`
- `sort`

필수 출력:

- `status`
- `items`

상태값:

- `OK`
- `PARTIAL`
- `NOT_FOUND`

### `get_source_evidence`

목적:

- 답변에 붙일 수 있는 근거 문장 추출

필수 입력:

- `identifier`
- `topic`
- `metric`
- `doc_type_hint`
- `limit`
- `max_chars_per_excerpt`

필수 출력:

- `status`
- `evidence`

상태값:

- `OK`
- `INSUFFICIENT_EVIDENCE`
- `NOT_FOUND`

## Cross-Tool Rules

- 숫자 출력에는 period와 source가 함께 있어야 한다
- ambiguity 시 임의 확정 금지
- metric 미해석 상태에서는 metric tool 호출 금지
- 질문당 tool budget은 기본 2~3회, 최대 4회
