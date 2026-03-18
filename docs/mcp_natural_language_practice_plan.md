# MCP 자연어 질의 실습 계획

## 1. 목적

이 계획의 목적은 내부 provider 구현 자체보다, 사용자가 자연어로 질문했을 때 Codex가 적절한 MCP 도구를 호출하고 자연어로 답변하는 흐름을 만드는 것이다.

예시 목표 질의:

- `ANET의 최근 4분기 영업이익 변동을 알려줘.`
- `ANET의 최근 4분기 매출 성장률을 요약해줘.`
- `ANET의 최근 실적 발표에서 가이던스 관련 핵심 문장만 알려줘.`

핵심은 아래 세 단계를 자연스럽게 연결하는 것이다.

1. 질문 이해
2. 알맞은 MCP 도구 호출
3. 근거를 포함한 한국어 답변 생성

## 2. 설계 원칙

이 실습에서는 내부 데이터 공급자나 파서의 세부 구현을 전면에 두지 않는다.  
대신 모델이 자연어 질문을 처리하기 쉬운 도구 계약과 응답 구조를 우선한다.

원칙:

- 도구는 low-level API wrapper보다 intent-level 도구를 우선한다
- 한 질문에 필요한 tool call 수는 가능한 한 적게 유지한다
- 응답에는 숫자, 기간, 기준점, 출처를 함께 담는다
- 모델이 계산보다 해석에 집중할 수 있게 structured output을 먼저 준다
- 사용자는 provider 이름이 아니라 자연어 질문만 던져도 된다

## 3. 목표 사용자 경험

사용자는 아래처럼 묻는다.

```text
ANET의 최근 4분기 영업이익 변동을 알려줘.
```

시스템은 내부적으로 아래 흐름으로 처리한다.

1. 회사 식별
2. 필요한 재무 지표와 기간 결정
3. MCP 도구 호출
4. 결과 정리
5. 자연어 답변 생성

사용자가 최종적으로 받는 응답 예:

```text
ANET의 최근 4분기 영업이익은 전반적으로 증가 흐름을 보였습니다.

- 2025 Q1: ...
- 2025 Q2: ...
- 2025 Q3: ...
- 2025 Q4: ...

가장 큰 변동은 ...
출처: ...
```

## 4. V1 범위

V1에서는 아래 질문 유형만 우선 지원한다.

### 4.1 재무 지표 추세 질문

예:

- 최근 4분기 영업이익
- 최근 4분기 매출
- 최근 4분기 EPS
- 최근 4분기 FCF

### 4.2 최근 분기 비교 질문

예:

- 전분기 대비 무엇이 좋아졌는지
- 최근 분기와 직전 분기 영업이익 차이

### 4.3 최근 공시/실적 발표 근거 질문

예:

- 최근 실적 발표에서 가이던스 관련 문장
- 최근 10-Q에서 margin 관련 언급

V1에서 제외:

- 자유형 valuation
- 복잡한 peer 비교 분석
- 멀티회사 screening
- 투자 판단 자동화

## 5. 권장 MCP 도구 설계

이 실습 목적에 맞는 도구는 provider 중심보다 질문 중심이어야 한다.

### 5.1 Entity Resolve

도구명:

- `resolve_entity`

입력:

- `query`

출력:

- canonical identifier
- ticker
- exchange
- company name

용도:

- `ANET`, `Arista`, `Arista Networks` 같은 표현을 하나의 엔티티로 고정

### 5.2 Quarterly Metrics

도구명:

- `get_quarterly_metrics`

입력:

- `identifier`
- `metrics`
- `quarters`

출력:

- 분기별 지표 값
- 통화
- 단위
- period label
- source

용도:

- `영업이익`, `매출`, `EPS` 같은 질문에 직접 대응

### 5.3 Metric Trend

도구명:

- `get_metric_trend`

입력:

- `identifier`
- `metric`
- `quarters`

출력:

- 시계열 값
- q/q 변화
- y/y 변화 가능 시 함께 제공
- 증감 방향 요약용 구조화 값

용도:

- 모델이 직접 계산하지 않고 바로 해석하게 하기 위함

### 5.4 Source Evidence

도구명:

- `get_source_evidence`

입력:

- `identifier`
- `topic` 또는 `metric`
- `limit`

출력:

- 관련 문장
- document type
- filing date
- citation text
- uri

용도:

- “왜 그렇게 말할 수 있는지”를 답변에 붙이기 위함

### 5.5 Recent Filings

도구명:

- `get_recent_filings`

입력:

- `identifier`
- `doc_types`
- `limit`

출력:

- filing 목록
- 날짜
- 문서 유형
- uri

용도:

- 공시 기반 질문 대응

## 6. 자연어 처리 흐름

권장 처리 순서:

1. 질문에서 엔티티 후보 추출
2. 질문에서 의도 분류
3. 질문에서 metric, period, comparison type 추출
4. `resolve_entity` 호출
5. intent에 맞는 MCP tool 1~2개 호출
6. structured response를 바탕으로 한국어 요약 생성
7. 가능하면 출처 한 줄 포함

예:

질문:

```text
ANET의 최근 4분기 영업이익 변동을 알려줘.
```

내부 해석:

- entity: ANET
- intent: metric_trend
- metric: operating_income
- quarters: 4

권장 tool sequence:

1. `resolve_entity("ANET")`
2. `get_metric_trend(identifier=..., metric="operating_income", quarters=4)`
3. 필요 시 `get_source_evidence(identifier=..., metric="operating_income", limit=2)`

## 7. 질문 유형별 매핑

### 7.1 “최근 4분기 영업이익 변동”

- `resolve_entity`
- `get_metric_trend`

### 7.2 “최근 분기에 뭐가 좋아졌어?”

- `resolve_entity`
- `get_quarterly_metrics`
- 필요 시 `get_source_evidence`

### 7.3 “최근 실적발표에서 가이던스 관련 내용”

- `resolve_entity`
- `get_recent_filings`
- `get_source_evidence`

## 8. 응답 형식 가이드

최종 자연어 응답은 아래 구조를 권장한다.

1. 한 줄 요약
2. 핵심 숫자 bullet 3~5개
3. 변동 해석
4. 출처 요약

응답 규칙:

- 숫자는 period와 함께 제시
- 증가/감소는 기준점 명시
- 확실하지 않으면 `[UNKNOWN]`
- 추론이면 `Inference:` 태그 사용 가능

## 9. 구현 단계

### Step A. 질문 중심 MCP 도구 계약 정의

산출물:

- `docs/mcp_tool_contracts.md`
- `src/schemas/` 하위 request/response schema

### Step B. 엔티티 해석 + 지표 추세용 최소 도구 구현

우선 구현:

- `resolve_entity`
- `get_quarterly_metrics`
- `get_metric_trend`

### Step C. 근거 도구 구현

우선 구현:

- `get_source_evidence`
- `get_recent_filings`

### Step D. 자연어 오케스트레이션 레이어 구현

산출물:

- 질문 분류기
- metric alias 매핑
- tool selection 로직

### Step E. 프롬프트와 응답 템플릿 정리

산출물:

- 자연어 질의용 system prompt
- 답변 템플릿

### Step F. 예시 질의 평가셋 작성

산출물:

- `examples/nl_queries/`
- `evals/datasets/nl_questions.json`

## 10. 우선 metric alias 표준

질문에서 많이 나올 표현을 canonical metric으로 매핑한다.

예:

- `영업이익` -> `operating_income`
- `매출` -> `revenue`
- `순이익` -> `net_income`
- `EPS` -> `eps`
- `잉여현금흐름` -> `fcf`

## 11. V1 수용 기준

아래를 만족하면 V1 성공으로 본다.

- 자연어 질문 10개 이상에 대해 적절한 tool이 선택된다
- `ANET의 최근 4분기 영업이익 변동을 알려줘` 질문에 구조화된 trend 결과를 기반으로 답변한다
- 응답에 최소 1개 이상의 source/provenance 정보가 포함된다
- entity ambiguity가 있으면 임의 선택하지 않는다
- metric alias가 한국어 질문에서 정상 작동한다

## 12. 실패 기준

아래 중 하나라도 있으면 V1 실패다.

- 질문마다 low-level tool 여러 개를 무질서하게 호출함
- 모델이 raw 숫자를 직접 계산해 답변함
- period 없이 숫자만 나감
- source 없이 단정적 결론을 냄
- `영업이익` 같은 한국어 질의를 metric으로 해석하지 못함

## 13. 저장 대상

이 계획을 기준으로 다음 문서를 추가하는 것을 권장한다.

- `docs/mcp_tool_contracts.md`
- `docs/nl_query_examples.md`
- `docs/nl_orchestration_plan.md`

## 14. 다음 실행 항목

가장 먼저 할 일:

1. `resolve_entity`, `get_quarterly_metrics`, `get_metric_trend`의 contract 문서 작성
2. `operating_income`, `revenue`, `eps`, `fcf`의 alias 표준 정의
3. `ANET의 최근 4분기 영업이익 변동을 알려줘`를 통과시키는 최소 end-to-end 흐름 구현
