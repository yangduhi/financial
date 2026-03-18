# Step 3. Canonical 데이터 파이프라인 및 Evidence Graph 구축

## 1. 목적

이 단계의 목적은 Step 2의 외부 응답을 재현 가능한 내부 계산 자산으로 변환하는 것이다.  
핵심은 텍스트를 많이 모으는 것이 아니라, 숫자와 서술을 같은 canonical schema와 run manifest 아래에서 관리하는 데 있다.

## 2. 반드시 먼저 읽을 문서

1. `spec.md`
2. `config/output_paths.yaml`
3. `docs/step_2_진행내용.md`

## 3. 선행조건

- Step 2 완료
- sample MCP responses 존재
- provenance와 citation 필드 정의 완료
- `src/`, `data/`, `runs/` 구조 준비 완료

## 4. 이번 단계의 핵심 범위

필수 범위:

- `raw -> parsed -> normalized -> derived` 흐름 확정
- canonical schema 구현
- run manifest 구조 구현
- evidence graph 저장 형식 정의
- deterministic calculation 기본 경로 구현

## 5. 필수 파일 및 산출물

최소 코드 산출물:

- `src/schemas/source_document.py`
- `src/schemas/metric_observation.py`
- `src/schemas/narrative_claim.py`
- `src/schemas/run_manifest.py`

필수 run 산출물:

- `runs/<run_id>/manifest.json`
- `runs/<run_id>/artifacts/raw/`
- `runs/<run_id>/artifacts/parsed/`
- `runs/<run_id>/artifacts/normalized/`
- `runs/<run_id>/artifacts/derived/`
- `runs/<run_id>/evidence/evidence_graph.jsonl`

## 6. 저장 규칙

저장 포맷은 아래를 기본값으로 사용한다.

- raw: JSON
- parsed: JSONL
- normalized: Parquet
- derived: Parquet
- manifest: JSON
- evidence graph: JSONL

각 산출물은 `config/output_paths.yaml`의 경로 규칙을 따른다.

## 7. schema 규칙

반드시 별도 schema로 정의할 모델:

- `SourceDocument`
- `MetricObservation`
- `NarrativeClaim`
- `RunManifest`

`RunManifest` 필수 필드:

- `run_id`
- `workspace_revision`
- `status`
- `identifier`
- `report_type`
- `started_at`
- `completed_at`
- `schema_version`
- `retries_of`

## 8. 파싱 및 정규화 규칙

- 파서 종류와 버전을 결과에 기록한다
- 통화, 단위, period, share basis를 항상 보존한다
- canonical metric 이름과 원문 라벨을 함께 저장한다
- company-stated 값과 computed 값을 구분한다

## 9. evidence graph 규칙

노드 최소 종류:

- document
- section
- table
- metric_observation
- claim
- output_artifact

엣지 최소 종류:

- `supported_by`
- `derived_from`
- `conflicts_with`
- `rendered_into`

`동등한 연결 구조` 같은 표현은 허용하지 않는다.  
필수 산출물은 `runs/<run_id>/evidence/evidence_graph.jsonl`로 고정한다.

## 10. 재실행, 재개, 실패 처리 규칙

- 각 단계는 idempotent해야 한다
- 실패한 run은 삭제하지 않고 `status`만 갱신한다
- 재실행은 새 `run_id`를 사용한다
- 재실행 manifest는 `retries_of`로 이전 run을 참조한다
- Step 3은 `data/outputs/latest/`를 절대 갱신하지 않는다

## 11. 구현 순서

1. schema 파일을 구현한다.
2. raw/parsed/normalized/derived 저장 경로를 고정한다.
3. 문서 파서와 표 추출 흐름을 구현한다.
4. 정규화 로직을 구현한다.
5. evidence graph writer를 구현한다.
6. deterministic analysis 뼈대를 구현한다.
7. 최소 1개 run으로 dry run을 수행한다.

## 12. 구현 후 검증

아래를 확인한다.

- 하나의 run에서 raw부터 derived까지 산출물이 모두 남는가
- 핵심 수치가 source document와 연결되는가
- currency, unit, period 정보가 보존되는가
- 같은 입력 재실행 시 결과가 재현되는가
- evidence graph가 실제 file로 생성되는가

목표 검증 파일:

- `tests/unit/test_normalize_metrics.py`
- `tests/integration/test_pipeline_dry_run.py`

예상 검증 명령:

```powershell
.\.venv311\Scripts\python.exe -m pytest tests\unit\test_normalize_metrics.py
.\.venv311\Scripts\python.exe -m pytest tests\integration\test_pipeline_dry_run.py
```

## 13. 완료 기준

- canonical schema 구현 완료
- `manifest.json`과 `evidence_graph.jsonl` 생성 확인
- raw/parsed/normalized/derived artifact 생성 확인
- deterministic calculation 결과 추적 가능
- Step 4가 이 결과를 직접 입력으로 사용할 수 있음

## 14. 실패 조건 및 주의사항

- 구조화 metric 없이 텍스트만 저장함
- period, currency, unit 없는 숫자를 저장함
- evidence graph file이 생성되지 않음
- failed run을 성공 run처럼 promote함
- 계산 근거를 manifest 또는 evidence에 남기지 않음

## 15. 다음 단계 인계물

- 샘플 `manifest.json`
- 샘플 `evidence_graph.jsonl`
- normalized metric set
- deterministic KPI 계산 결과
