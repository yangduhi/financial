# Runbook

## Local Dry Run

1. `README.md`, `spec.md`, `config/*.yaml`을 읽는다.
2. `config/sources.yaml`와 `config/qa_thresholds.yaml`의 blocked decision이 없는지 확인한다.
3. `examples/report_input.example.json`을 기반으로 실제 입력 파일을 만든다.
4. `run_id`를 생성하고 `runs/<run_id>/input.json`에 저장한다.
5. 해당 단계 문서에 따라 구현 또는 실행한다.
6. 결과는 `runs/<run_id>/` 아래에서만 검토한다.
7. `manifest.json`과 `qa_report.json`이 `qa_passed`일 때만 latest copy를 갱신한다.

## Escalation

아래 상황에서는 구현보다 먼저 문서 또는 config를 갱신한다.

- source vendor가 확정되지 않음
- tolerance가 비어 있음
- output path 규칙이 모호함
- report_type이 `config/report_types.yaml`에 없음
