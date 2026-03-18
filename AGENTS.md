# AGENTS.md

## Purpose

이 레포는 금융 리서치 보고서 생성을 위한 workbench다.  
에이전트는 텍스트 품질보다 수치 정확성, 출처 추적성, 재현 가능성을 우선한다.

## Required Reading Order

작업 전 아래 문서를 먼저 읽는다.

1. `README.md`
2. `spec.md`
3. `plan.md`
4. `tasks.md`
5. `config/*.yaml`
6. 필요한 경우 `docs/step_*_진행내용.md`

`docs/archive/`는 참고용 보관본이며 실행 기준이 아니다.

## Core Rules

- 출처 없는 숫자를 쓰지 않는다.
- 사실, 추론, 의견을 명시적으로 구분한다.
- 서술은 짧고 기관형 메모 톤으로 작성한다.
- 모호한 entity 매칭은 임의 선택하지 않고 실패 처리한다.
- 불일치 수치를 조용히 덮지 않는다.
- 검증할 수 없는 항목은 `[UNKNOWN]`으로 표시한다.
- 구조화 산출물 없이 Markdown만 먼저 만들지 않는다.
- deterministic 계산을 LLM 추정으로 대체하지 않는다.

## Point-in-Time Rules

모든 수치와 claim은 가능한 범위에서 아래 메타데이터와 연결한다.

- `as_of_date`
- `as_of_datetime`
- `fiscal_period`
- `currency`
- `unit_basis`
- `share_basis`

## Input Rules

- `ticker` 단독 문자열은 허용하지 않는다.
- 입력은 `spec.md`의 `identifier` 계약을 따른다.
- `report_type`은 `config/report_types.yaml`의 정의만 사용한다.
- `house_style` 기본값은 `concise_evidence_first`로 간주한다.

## Output Rules

- 모든 실행 산출물은 먼저 `runs/<run_id>/` 아래 생성한다.
- `data/outputs/latest/`는 `qa_passed` 또는 승인된 `warn` 결과만 갱신한다.
- 실패 run은 latest output을 갱신하지 않는다.
- 필수 출력은 최소 `summary.md`, `kpi_summary.json`, `source_map.json`, `review_pack.md`, `qa_report.json`, `manifest.json`, `evidence_graph.jsonl`이다.
- review pack에는 unresolved discrepancy, unknown, low confidence claim을 반드시 포함한다.

## Blocked Decision Rules

아래 중 하나라도 비어 있으면 live 구현을 시작하지 않는다.

- `config/sources.yaml`의 필수 source가 미결정 상태
- `config/sources.yaml`에서 `auth_required: true` 인 source의 환경변수 미설정
- `config/qa_thresholds.yaml`의 필수 tolerance 미설정

이 경우 허용되는 작업은 스캐폴드, contract, 테스트 골격, 문서 정리까지다.

## Security Rules

- credential은 `.env` 또는 secret store에서만 로드한다.
- prompt나 문서에 실제 비밀값을 쓰지 않는다.
- internal memory는 access control 승인 전 활성화하지 않는다.
- 라이선스 범위가 불명확한 source는 사용하지 않는다.

## Review Gate

아래 항목이 있으면 사람이 review pack을 확인해야 한다.

- unresolved discrepancy
- `[UNKNOWN]`
- low confidence claim
- valuation implication
- investment opinion
- public source 한계로 confidence가 낮아진 항목
