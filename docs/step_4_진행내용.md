# Step 4. Ticker-to-Report V1 워크플로 구축

## 1. 목적

이 단계의 목적은 단일 티커 기준의 end-to-end report workflow를 구현하는 것이다.  
이 단계부터는 구조화 산출물, review pack, QA gate, latest promotion 규칙이 실제로 연결되어야 한다.

## 2. 반드시 먼저 읽을 문서

1. `spec.md`
2. `config/report_types.yaml`
3. `config/runtime_defaults.yaml`
4. `config/output_paths.yaml`
5. `examples/report_input.example.json`

## 3. 선행조건

- Step 3 완료
- canonical schema와 manifest가 동작함
- evidence graph file 생성 가능
- 허용 `report_type`가 `config/report_types.yaml`에 정의됨

## 4. 입력 계약

최소 입력:

- `identifier`
- `report_type`
- `as_of_date`
- `strict_mode`

`identifier`는 `spec.md`의 object 구조만 허용한다.  
`ticker` 단독 문자열은 허용하지 않는다.

허용 `report_type`는 `config/report_types.yaml`에 정의된 값만 사용한다.

## 5. 필수 산출물

모든 필수 산출물은 `runs/<run_id>/` 아래 생성한다.

- `runs/<run_id>/input.json`
- `runs/<run_id>/manifest.json`
- `runs/<run_id>/outputs/summary.md`
- `runs/<run_id>/outputs/kpi_summary.json`
- `runs/<run_id>/outputs/source_map.json`
- `runs/<run_id>/outputs/review_pack.md`
- `runs/<run_id>/qa/qa_report.json`
- `runs/<run_id>/evidence/evidence_graph.jsonl`

`review_pack.md`는 권장이 아니라 필수다.

## 6. 실행 플로우

1. 입력 검증 및 `run_id` 생성
2. entity resolve
3. primary source 수집
4. KPI 및 narrative claim 추출
5. 숫자 정규화 및 reconciliation
6. structured outputs 생성
7. `summary.md` 렌더링
8. `review_pack.md` 생성
9. QA 실행
10. `qa_passed`일 때만 latest copy promote

## 7. strict_mode와 assisted_mode 규칙

Strict mode:

- primary source 2개 미만이면 실패
- unresolved discrepancy가 있으면 실패
- source map이 없으면 실패
- review pack이 없으면 실패

Assisted mode:

- 일부 누락은 허용하되 `qa_report.json`에 경고를 남긴다
- latest promotion은 사람 검토 승인 전 금지

`strict_mode` 기본값은 `config/runtime_defaults.yaml`을 따른다.

## 8. 리포트 구조 규칙

`summary.md` 필수 섹션:

- Executive summary
- Key KPIs
- What improved
- What deteriorated
- Guidance and management commentary
- Customer or end-market commentary
- Risks and unknowns
- Source notes

표현 규칙:

- 사실은 단정문
- 추론은 `Inference:`
- 의견은 `Opinion:`
- 검증 불가 항목은 `[UNKNOWN]`

## 9. source map 및 review pack 규칙

`source_map.json` 최소 필드:

- `claims`
- `metrics`
- `documents`
- `artifacts`

`review_pack.md` 최소 포함 항목:

- run summary
- key metric table
- unresolved discrepancy 목록
- unknown 목록
- low confidence claim 목록

## 10. 실패 처리 및 promotion 규칙

- `qa_passed`가 아니면 `data/outputs/latest/`를 갱신하지 않는다
- strict mode 실패는 `manifest.status = "qa_failed"` 또는 `failed`로 기록한다
- 출력 file은 남겨도 되지만 promoted output으로 취급하지 않는다
- 재실행 시 새 `run_id` 사용

## 11. 구현 순서

1. 입력 loader와 validator 구현
2. `run_id` 생성 규칙을 `config/output_paths.yaml`에 맞춘다
3. structured outputs 생성기를 구현
4. Markdown renderer를 구현
5. review pack generator를 구현
6. QA 연동
7. latest promotion gate 구현

## 12. 구현 후 검증

- latest primary source 2개 이상을 실제로 사용했는가
- KPI 10개 이상이 source map에 연결되는가
- `review_pack.md`가 항상 생성되는가
- `summary.md`와 `kpi_summary.json`이 모순되지 않는가
- `qa_passed` 전에는 latest copy가 갱신되지 않는가

목표 검증 파일:

- `tests/integration/test_report_workflow.py`

예상 검증 명령:

```powershell
.\.venv311\Scripts\python.exe -m pytest tests\integration\test_report_workflow.py
```

## 13. 완료 기준

- end-to-end run 성공
- 필수 출력 8종 생성
- review pack 필수 생성
- strict mode gate 동작
- latest promotion 규칙 동작

## 14. 실패 조건 및 주의사항

- `ticker` 단독 문자열로 entity를 확정함
- structured output 없이 Markdown만 생성함
- review pack 없이 완료 처리함
- `qa_passed` 이전 결과를 latest로 복사함
- 추정 숫자를 공식 수치처럼 서술함

## 15. 다음 단계 인계물

- 최소 3개 run 결과
- `summary.md`, `kpi_summary.json`, `source_map.json`, `review_pack.md`
- strict mode 실패 사례
- 자주 발생한 discrepancy 패턴
