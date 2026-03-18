# Build Report Playbook

## Purpose

단일 run의 입력 검증, source 수집, 구조화 산출물 생성, report 렌더링, QA까지의 흐름을 정의한다.

## Preconditions

- `spec.md`와 `config/*.yaml`을 읽었을 것
- `config/sources.yaml`의 필수 source 결정이 완료되었을 것
- `config/qa_thresholds.yaml`의 필수 tolerance 값이 채워졌을 것

## Required Inputs

- `runs/<run_id>/input.json`
- `config/report_types.yaml`
- `config/output_paths.yaml`

## Output Rule

- `runs/<run_id>/outputs/summary.md`
- `runs/<run_id>/outputs/kpi_summary.json`
- `runs/<run_id>/outputs/source_map.json`
- `runs/<run_id>/outputs/review_pack.md`

## Do Not

- `ticker` 단독 문자열만으로 entity를 확정하지 않는다
- structured output 없이 Markdown만 만들지 않는다
- QA pass 이전에 `data/outputs/latest/`를 갱신하지 않는다
