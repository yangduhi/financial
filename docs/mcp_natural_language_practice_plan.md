# MCP 자연어 질의 실습 계획 v2.2

## 1. 목표

본 실습의 1차 목표는 내부 provider 구현 자체가 아니라, 사용자가 자연어로 질문했을 때 시스템이 다음 흐름을 안정적으로 수행하도록 만드는 것이다.

1. 질문을 구조화한다
2. 적절한 MCP 도구를 최소 횟수로 호출한다
3. 숫자, 기간, 기준점, 출처를 포함한 한국어 답변을 생성한다

V1의 성공 기준은 단순 데모가 아니라, 제한된 범위에서 재현 가능한 질의-도구-근거-응답 파이프라인을 만드는 것이다.

대표 목표 질의:

- `ANET의 최근 4분기 영업이익 변동을 알려줘.`
- `ANET의 최근 4분기 매출 성장률을 요약해줘.`
- `ANET의 최근 실적 발표에서 가이던스 관련 핵심 문장만 알려줘.`

## 2. 비목표

V1에서는 아래를 의도적으로 제외한다.

- 자유형 valuation 생성
- peer 비교 자동화
- 멀티티커 screening
- buy/sell 추천 자동화
- 장문의 투자 리포트 자동 작성
- 비정형 웹 전역 검색 기반 사실 합성

이유:

- V1의 병목은 분석 깊이가 아니라 질문 해석 정확도와 근거 정합성이다.

## 3. 설계 원칙

### 3.1 질문 중심 설계

도구는 provider 중심이 아니라 질문 의도 중심으로 설계한다.

### 3.2 최소 도구 호출

일반 질의는 2회, 복합 질의는 3회, 애매성 해소가 필요한 경우만 4회까지 허용한다.

### 3.3 구조화 우선, 서술 후행

모델이 raw data를 임의 계산하지 않도록, 계산된 structured output을 먼저 제공한다.

### 3.4 근거 우선

숫자 주장에는 period와 source가 따라가야 하며, 정성 해석에는 filing 또는 earnings-call 근거 문장을 붙인다.

### 3.5 애매하면 멈춤

엔티티, metric, period가 불명확하면 임의 확정하지 않는다.  
`AMBIGUOUS`, `NOT_FOUND`, `INSUFFICIENT_EVIDENCE` 상태를 명시적으로 사용한다.

### 3.6 한국어 질의 1급 지원

한국어 alias, 분기 표현, 비교 표현을 초기부터 canonical form으로 정규화한다.

### 3.7 레포 구조 일관성 유지

새 구현은 현재 레포 구조를 따른다.

- `src/orchestration/` 사용
- `config/`에 alias/period/entity 규칙 저장
- `docs/`에 contract와 가이드 저장
- `evals/`에 질문셋과 golden expectation 저장

`src/orchestrator/` 같은 신규 축은 만들지 않는다.

## 4. 지원 질의 범위

### 4.1 V1 지원

#### A. 분기 재무 지표 추세

- 최근 4분기 매출
- 최근 4분기 영업이익
- 최근 4분기 EPS
- 최근 4분기 FCF

#### B. 최근 분기 비교

- 최근 분기와 직전 분기 비교
- 전분기 대비 무엇이 개선되었는지
- 특정 metric의 q/q 변화

#### C. 최근 공시/실적발표 근거 추출

- 최근 실적 발표에서 가이던스 관련 문장
- 최근 10-Q에서 margin 관련 언급
- 최근 filing에서 capex 관련 근거

### 4.2 V1.5 후보

- TTM 계산
- y/y와 q/q 동시 해석
- metric 2개 이상 동시 비교
- 최근 2개 filing cross-reference

## 5. 목표 사용자 경험

사용자 입력:

```text
ANET의 최근 4분기 영업이익 변동을 알려줘.
```

시스템 내부 목표 상태:

```json
{
  "entity": {
    "raw": "ANET",
    "resolved_identifier": "anet_us_equity",
    "ticker": "ANET",
    "company_name": "Arista Networks, Inc."
  },
  "intent": "metric_trend",
  "metric": "operating_income",
  "period": {
    "type": "recent_quarters",
    "value": 4
  },
  "comparison": "sequential_trend",
  "response_mode": "summary_with_evidence"
}
```

최종 사용자 응답 예시:

```text
ANET의 최근 4분기 영업이익은 전반적으로 증가 흐름이었고, 최근 분기에서 개선 폭이 가장 컸습니다.

- 2025Q1: ...
- 2025Q2: ...
- 2025Q3: ...
- 2025Q4: ...

직전 분기 대비 증감률은 ...
회사가 최근 실적 자료에서 언급한 근거는 ...
출처: 2025-xx-xx earnings release / 10-Q
```

## 6. 핵심 아키텍처

V1 오케스트레이션은 아래 6단계로 고정한다.

1. Query Normalization
2. Intent Parsing
3. Entity Resolution
4. Tool Planning
5. Tool Execution
6. Grounded Answer Generation

자유형 chain orchestration은 V1에서 금지한다.

## 7. 자연어 해석 규칙

### 7.1 엔티티 해석

입력 표현:

- `ANET`
- `Arista`
- `Arista Networks`

출력:

- canonical identifier
- ticker
- exchange
- company_name
- ambiguity status
- confidence score

규칙:

- ticker exact match 우선
- company_name exact/alias match 차순위
- 다수 후보면 임의 선택 금지
- confidence threshold 미만이면 `AMBIGUOUS`

### 7.2 metric 해석

예시 alias:

- `영업이익` -> `operating_income`
- `매출` -> `revenue`
- `순이익` -> `net_income`
- `주당순이익`, `EPS` -> `eps`
- `잉여현금흐름`, `FCF` -> `fcf`
- `마진`, `영업이익률` -> `operating_margin`
- `총이익률`, `gross margin` -> `gross_margin`

규칙:

- alias dictionary 기반 1차 매핑
- 다의어면 intent와 결합해 해석
- `margin` 단독은 `AMBIGUOUS`
- metric 미해석 시 tool call 금지

### 7.3 기간 해석

예시 표현:

- `최근 4분기` -> `recent_quarters=4`
- `최근 분기` -> `recent_quarters=1`
- `전분기 대비` -> `comparison=qoq`
- `최근 실적 발표` -> 최근 earnings document 1건
- `최근 10-Q` -> 최근 10-Q 1건

규칙:

- V1에서는 상대기간 우선 지원
- `최근`은 filing date 또는 earnings date 기준으로 해석
- 회계분기 기준을 기본값으로 사용
- calendar quarter와 fiscal quarter 혼합 금지

## 8. MCP 도구 설계 v2

### 8.1 `resolve_entity`

목적:

- 질문의 회사 표현을 canonical entity로 고정

입력:

```json
{
  "query": "ANET",
  "entity_type": "public_company",
  "market_hint": "US",
  "max_candidates": 5
}
```

출력:

```json
{
  "status": "RESOLVED",
  "selected": {
    "identifier": "anet_us_equity",
    "ticker": "ANET",
    "exchange": "NYSE",
    "company_name": "Arista Networks, Inc."
  },
  "candidates": [],
  "confidence": 0.99,
  "source": "entity_master_v1"
}
```

상태값:

- `RESOLVED`
- `AMBIGUOUS`
- `NOT_FOUND`

추가 필드:

- `resolution_method`
- `matched_alias`

### 8.2 `get_quarterly_metrics`

목적:

- 분기별 재무 지표 원값 조회

입력:

```json
{
  "identifier": "anet_us_equity",
  "metrics": ["revenue", "operating_income", "eps"],
  "quarter_count": 4,
  "period_basis": "fiscal_reported",
  "include_source": true
}
```

출력:

```json
{
  "status": "OK",
  "identifier": "anet_us_equity",
  "currency": "USD",
  "unit_map": {
    "revenue": "USD_million",
    "operating_income": "USD_million",
    "eps": "USD_per_share"
  },
  "periods": [
    {
      "period_label": "2025Q1",
      "fiscal_year": 2025,
      "fiscal_quarter": 1,
      "values": {
        "revenue": 0.0,
        "operating_income": 0.0,
        "eps": 0.0
      },
      "source": {
        "doc_type": "10-Q",
        "filing_date": "2025-05-00",
        "uri": "..."
      }
    }
  ]
}
```

필수 규칙:

- 단위와 통화를 metric별로 명시
- `period_label`은 정렬 가능 문자열
- source는 period별로 존재
- 데이터 누락 시 null 허용, 단 상태코드/메시지 필요

### 8.3 `get_metric_trend`

목적:

- 모델이 직접 숫자를 계산하지 않도록 trend 해석용 구조 제공

입력:

```json
{
  "identifier": "anet_us_equity",
  "metric": "operating_income",
  "quarter_count": 4,
  "include_qoq": true,
  "include_yoy": true,
  "include_summary_flags": true
}
```

출력:

```json
{
  "status": "OK",
  "metric": "operating_income",
  "currency": "USD",
  "unit": "USD_million",
  "series": [
    {
      "period_label": "2025Q1",
      "value": 0.0,
      "qoq_change_pct": null,
      "yoy_change_pct": 0.0
    }
  ],
  "trend_flags": {
    "overall_direction": "UP",
    "volatility": "LOW",
    "largest_move_period": "2025Q4",
    "latest_qoq_direction": "UP"
  },
  "summary_stats": {
    "latest_value": 0.0,
    "first_value": 0.0,
    "net_change_pct": 0.0
  },
  "sources": [
    {
      "doc_type": "10-Q",
      "filing_date": "2025-05-00",
      "uri": "..."
    }
  ]
}
```

주의:

- 이 도구는 원값 조회와 파생 계산을 담당
- LLM은 받은 값을 설명만 함
- q/q 기준점이 없는 첫 분기는 `null`

### 8.4 `get_recent_filings`

목적:

- 최근 filing 또는 earnings 자료 후보를 안정적으로 조회

입력:

```json
{
  "identifier": "anet_us_equity",
  "doc_types": ["10-Q", "10-K", "earnings_release", "earnings_call_transcript"],
  "limit": 5,
  "sort": "filing_date_desc"
}
```

출력:

```json
{
  "status": "OK",
  "items": [
    {
      "doc_id": "doc_001",
      "doc_type": "earnings_release",
      "title": "...",
      "filing_date": "2026-02-00",
      "period_label": "2025Q4",
      "uri": "..."
    }
  ]
}
```

### 8.5 `get_source_evidence`

목적:

- 답변에 붙일 수 있는 근거 문장을 topic 또는 metric 기준으로 추출

입력:

```json
{
  "identifier": "anet_us_equity",
  "topic": "guidance",
  "metric": null,
  "doc_type_hint": ["earnings_release", "earnings_call_transcript", "10-Q"],
  "limit": 3,
  "max_chars_per_excerpt": 400
}
```

출력:

```json
{
  "status": "OK",
  "evidence": [
    {
      "excerpt": "...",
      "topic": "guidance",
      "document_type": "earnings_release",
      "filing_date": "2026-02-00",
      "period_label": "2025Q4",
      "citation_text": "2025Q4 earnings release",
      "uri": "..."
    }
  ]
}
```

규칙:

- excerpt는 짧게 제한
- 답변용 `citation_text` 포함
- relevance score 추가 허용

## 9. 오케스트레이션 정책

### 9.1 기본 정책

#### A. Metric trend 질문

예: `최근 4분기 영업이익 변동`

1. `resolve_entity`
2. `get_metric_trend`
3. 필요 시 `get_source_evidence`

#### B. Metric compare 질문

예: `최근 분기와 직전 분기 매출 비교`

1. `resolve_entity`
2. `get_quarterly_metrics`
3. 필요 시 `get_source_evidence`

#### C. Filing evidence 질문

예: `최근 실적 발표에서 가이던스 관련 문장`

1. `resolve_entity`
2. `get_recent_filings`
3. `get_source_evidence`

### 9.2 tool budget

- 단순 질문: 최대 2회
- 증거 포함 질문: 최대 3회
- 애매성 해소 포함: 최대 4회
- 이를 초과하면 planner failure로 기록

### 9.3 tool selection rule

- metric trend가 명확하면 `get_metric_trend` 우선
- 원값 여러 개 비교가 필요하면 `get_quarterly_metrics`
- 근거 문장이 요구되면 `get_source_evidence` 필수
- filing 유형이 명시되면 `get_recent_filings` 선행

## 10. 답변 생성 규칙

최종 응답은 반드시 아래 순서를 따른다.

1. 한 줄 결론
2. 핵심 수치
3. 해석
4. 근거/출처
5. 불확실성 명시

예시 포맷:

```text
요약:
ANET의 최근 4분기 영업이익은 전반적으로 증가 흐름이었습니다.

핵심 수치:
- 2025Q1: ...
- 2025Q2: ...
- 2025Q3: ...
- 2025Q4: ...
- 최근 분기 q/q: ...%

해석:
- 가장 큰 증가는 ... 구간에서 발생했습니다.
- 변동성은 ... 수준입니다.

근거:
- 2025Q4 earnings release
- 2025Q3 10-Q

제한:
- 일부 지표는 filing 기준 시점과 비GAAP/GAAP 정의 차이가 있을 수 있습니다.
```

생성 규칙:

- 숫자는 period 없이 쓰지 않는다
- 증가/감소는 기준점 없이 쓰지 않는다
- 근거 없는 해석 금지
- evidence가 없으면 “근거 문장 미확보” 명시
- 계산이 tool output에 없으면 LLM 임의 계산 금지

## 11. 애매성 및 오류 처리

### 11.1 엔티티 애매성

응답 예:

```json
{
  "status": "AMBIGUOUS_ENTITY",
  "candidates": []
}
```

정책:

- 임의 선택 금지
- 후보 2~5개 반환
- 사용자 재질문 유도 또는 safe failure

### 11.2 metric 애매성

예:

- `마진`
- `이익`
- `실적`

정책:

- default mapping 금지
- canonical metric 미확정 시 clarification state

### 11.3 evidence 부족

예:

- 가이던스 문장 요청인데 transcript 없음

정책:

- 수치 답변과 근거 문장 답변 분리
- `INSUFFICIENT_EVIDENCE` 반환 가능
- “현재 확보된 최근 문서 기준” 문구 명시

### 11.4 기간 불명확

정책:

- 최근 실적 = 가장 최근 reported quarter 1건
- 최근 4분기 = 가장 최근 reported fiscal quarters 4개

## 12. 데이터 정합성 규칙

필수 정합성 규칙:

- fiscal period 기준 통일
- GAAP vs non-GAAP 혼용 금지
- metric definition registry 유지
- source 문서 유형과 값 provenance 연결
- period ordering deterministic
- currency/unit metadata 항상 포함

추천 필드:

- `metric_definition_version`
- `accounting_basis`
- `restated_flag`
- `data_quality_flag`

## 13. 파일 구조 권장안

현재 레포 구조를 기준으로 아래처럼 저장한다.

```text
docs/
  mcp_natural_language_practice_plan.md
  mcp_tool_contracts.md
  nl_orchestration_plan.md
  nl_query_examples.md
  metric_alias_standard.md
  ambiguity_policy.md
  answer_style_guide.md

config/
  metric_aliases.yaml
  doc_type_aliases.yaml
  period_rules.yaml
  entity_rules.yaml

src/
  orchestration/
    nl_query_normalizer.py
    nl_intent_parser.py
    nl_tool_planner.py
    nl_answer_generator.py
    nl_ambiguity_handler.py
    trend_service.py
  schemas/
    resolve_entity.request.schema.json
    resolve_entity.response.schema.json
    get_quarterly_metrics.request.schema.json
    get_quarterly_metrics.response.schema.json
    get_metric_trend.request.schema.json
    get_metric_trend.response.schema.json
    get_recent_filings.request.schema.json
    get_recent_filings.response.schema.json
    get_source_evidence.request.schema.json
    get_source_evidence.response.schema.json

evals/
  datasets/
    nl_questions_v1.json
  golden/
    expected_tool_plans.json
    expected_answer_traits.json
  reports/
    eval_report_v1.md

runs/
  <run_id>/
    logs/
      tool_traces/
      failed_cases/
```

## 14. 구현 단계 재구성

### Step 0. 범위 고정

산출물:

- `docs/v1_scope.md`

해야 할 일:

- 지원 질의 유형 3개 고정
- metric 6개 이하로 고정
- filing type 4개 이하로 고정

완료 기준:

- 범위 문서 승인 전 구현 금지

### Step 1. Canonical vocabulary 정의

산출물:

- `docs/metric_alias_standard.md`
- `config/metric_aliases.yaml`
- `config/period_rules.yaml`

해야 할 일:

- 한국어/영어 alias 정의
- period parser rule 정의
- comparison intent 정의

완료 기준:

- 20개 샘플 문장 파싱 성공률 90% 이상

### Step 2. MCP tool contract 문서화

산출물:

- `docs/mcp_tool_contracts.md`
- `src/schemas/*.json`

해야 할 일:

- 5개 도구 request/response schema 확정
- 상태코드 정의
- nullable field 정책 정의

완료 기준:

- schema validation 통과
- 각 tool 예시 request/response 3세트 작성

### Step 3. 최소 provider adapter 구현

산출물:

- `src/orchestration/` 하위 adapter/selector 또는 기존 gateway wrapper

해야 할 일:

- entity lookup
- quarterly financial fetch
- recent filings fetch
- evidence snippet extraction

완료 기준:

- ANET 기준 샘플 값 retrieval 성공
- source uri 반환 성공

### Step 4. Trend computation layer 구현

산출물:

- `src/orchestration/trend_service.py`

해야 할 일:

- q/q
- y/y
- latest/latest-1 comparison
- summary flag 계산

완료 기준:

- raw metric 대비 계산 결과 검증
- null/결측 규칙 검증

### Step 5. Query orchestration 구현

산출물:

- `src/orchestration/nl_query_normalizer.py`
- `src/orchestration/nl_intent_parser.py`
- `src/orchestration/nl_tool_planner.py`

해야 할 일:

- 질문 -> canonical intent/metric/period/entity 분해
- tool sequence 결정
- tool budget enforcement

완료 기준:

- 평가 질문 10개 중 8개 이상에서 예상 tool plan과 일치

### Step 6. Grounded answer generator 구현

산출물:

- `src/orchestration/nl_answer_generator.py`
- `docs/answer_style_guide.md`

해야 할 일:

- 숫자/기간/근거 결합 템플릿
- 부족한 evidence 처리
- uncertainty 문구 표준화

완료 기준:

- hallucinated source 0건
- period 없는 숫자 출력 0건

### Step 7. Eval set 구축

산출물:

- `evals/datasets/nl_questions_v1.json`
- `evals/golden/expected_tool_plans.json`
- `evals/golden/expected_answer_traits.json`

질문 분포:

- metric trend 5개
- compare 5개
- evidence 5개
- ambiguous 3개
- failure case 2개

완료 기준:

- 최소 20문항 확보

### Step 8. Trace/logging 구현

산출물:

- `runs/<run_id>/logs/tool_traces/`
- `runs/<run_id>/logs/failed_cases/`

로그 필수 항목:

- raw query
- normalized query
- parsed intent
- selected tools
- tool args
- tool outputs summary
- answer draft
- final failure reason

완료 기준:

- 실패 케이스 재현 가능

### Step 9. V1 acceptance test

테스트 질문 예시:

- `ANET의 최근 4분기 영업이익 변동을 알려줘.`
- `ANET의 최근 분기 매출은 직전 분기보다 얼마나 늘었어?`
- `ANET의 최근 실적 발표에서 가이던스 관련 핵심 문장만 보여줘.`
- `Arista의 최근 10-Q에서 gross margin 관련 언급을 알려줘.`
- `ANET의 최근 4분기 EPS 추세를 요약해줘.`

완료 기준:

- 아래 수용 기준 충족

## 15. 수용 기준

기능 수용 기준:

- 자연어 질문 20개 이상에서 pipeline이 끝까지 동작
- entity resolution 성공률 90% 이상
- metric alias 해석 성공률 90% 이상
- expected tool plan 일치율 80% 이상
- 답변 내 숫자-period 연결 정확도 100%
- hallucinated source 0건
- ambiguous entity 임의 선택 0건

품질 수용 기준:

- 단순 trend 질문 평균 tool call 수 2.5 이하
- evidence 질문 평균 tool call 수 3.5 이하
- 답변 길이 5~12문장 범위 유지
- 응답에 최소 1개 provenance 포함

## 16. 실패 기준

아래 중 하나라도 발생하면 V1 실패다.

- 모델이 raw 숫자를 자체 계산해 핵심 결론 생성
- source 없는 단정적 결론 생성
- fiscal/calendar period 혼용
- 애매한 metric 임의 확정
- evidence 요청에 unrelated excerpt 사용
- 질문 하나에 5개 이상 low-level tool 호출
- 실패했는데 trace가 남지 않음

## 17. 대표 질의별 기대 tool plan

### 17.1 `ANET의 최근 4분기 영업이익 변동을 알려줘.`

1. `resolve_entity`
2. `get_metric_trend`
3. optional `get_source_evidence`

### 17.2 `ANET의 최근 분기에 뭐가 좋아졌어?`

1. `resolve_entity`
2. `get_quarterly_metrics`
3. `get_source_evidence`

내부 재해석 규칙:

- 기본 비교 집합: revenue, operating_income, eps, fcf
- 개선 기준: latest quarter vs prior quarter

### 17.3 `ANET의 최근 실적 발표에서 가이던스 관련 핵심 문장만 알려줘.`

1. `resolve_entity`
2. `get_recent_filings`
3. `get_source_evidence`

우선순위:

- earnings release
- earnings call transcript
- 10-Q fallback

## 18. Codex 실행 지시문 템플릿

```text
목표:
MCP 기반 자연어 질의 시스템 V1을 구현하라.
사용자는 한국어 자연어로 미국 상장사의 최근 분기 실적/공시를 질문하고,
시스템은 질문을 구조화한 뒤 적절한 MCP tool을 최소 횟수로 호출하여
숫자, 기간, 기준점, 출처를 포함한 한국어 답변을 생성해야 한다.

우선 지원 범위:
1) 최근 4분기 metric trend
2) 최근 분기 vs 직전 분기 비교
3) 최근 filing/earnings evidence 추출

반드시 구현할 MCP 도구:
- resolve_entity
- get_quarterly_metrics
- get_metric_trend
- get_recent_filings
- get_source_evidence

핵심 제약:
- low-level provider 도구를 오케스트레이터에서 직접 조합하지 말 것
- intent-level tool contract를 우선 구현할 것
- 숫자에는 period와 source를 반드시 포함할 것
- entity/metric ambiguity 시 임의 추정 금지
- 답변 생성 시 tool output에 없는 숫자를 모델이 임의 계산하지 말 것
- 일반 질문의 tool call 수는 2~3회 내로 제한할 것

필수 산출물:
- docs/mcp_tool_contracts.md
- docs/nl_orchestration_plan.md
- docs/metric_alias_standard.md
- src/schemas/*.json
- src/orchestration/*
- evals/datasets/nl_questions_v1.json
- evals/reports/eval_report_v1.md

필수 로그:
- raw query
- normalized query
- parsed intent
- selected tool plan
- tool args
- tool outputs summary
- final answer
- failure reason

수용 기준:
- 평가 질문 20개 이상
- entity resolution 성공률 90% 이상
- metric alias 해석 성공률 90% 이상
- expected tool plan 일치율 80% 이상
- hallucinated source 0건
- ambiguous entity 임의 선택 0건
```

## 19. 원안 대비 핵심 강화 포인트

이번 최종안에서 특히 강화한 항목:

1. 도구 설명을 schema 수준으로 내림
2. `최근`, `전분기`, `실적발표` 해석 규칙 명시
3. `AMBIGUOUS / NOT_FOUND / INSUFFICIENT_EVIDENCE` 상태 도입
4. tool budget 명시
5. LLM 임의 계산 금지 강화
6. trace/logging을 필수 산출물로 승격
7. 평가셋과 expected tool plan을 함께 정의
8. 현재 레포 구조에 맞게 파일 경로를 조정

## 20. 신뢰도와 한계

- 신뢰도: 높음
- 이유: 이 문서는 최신 수치보다 설계/운영 구조를 정의하는 문서이며, 현재 레포의 MCP 구조와도 정합적이다

한계:

- provider 세부 구현은 실제 source 품질과 스키마에 따라 조정될 수 있다
- `get_source_evidence`와 `get_metric_trend`의 내부 계산은 추후 데이터 정합성 정책에 따라 변할 수 있다

## 21. 다음 실행 항목

가장 먼저 할 일:

1. `docs/mcp_tool_contracts.md` 작성
2. `docs/metric_alias_standard.md` 작성
3. `config/metric_aliases.yaml`, `config/period_rules.yaml` 추가
4. `resolve_entity`, `get_quarterly_metrics`, `get_metric_trend` contract와 최소 구현 시작
