# Recovery Rules

## Failure Categories

- source_configuration_failure
- network_fetch_failure
- parse_failure
- normalization_failure
- reconciliation_failure
- qa_failure

## Recovery Policy

- network fetch 실패만 자동 재시도한다
- parse/normalize/qa 실패는 자동 재시도하지 않는다
- 실패 시 `runs/<run_id>/manifest.json`에 최종 status를 기록한다
- 실패 run은 `data/outputs/latest/`를 갱신하지 않는다
- 재실행 시 새 `run_id`를 사용하고 `retries_of` 필드로 연결한다

## Rollback Policy

- promoted latest output이 잘못된 것으로 확인되면 latest copy만 교체 또는 제거한다
- 원래 run artifact는 삭제하지 않는다
- rollback 사실은 새 failure report에 기록한다
