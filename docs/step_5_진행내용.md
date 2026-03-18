# Step 5. QA, 평가, 통제 프레임워크 구축

## 1. 목적

이 단계의 목적은 보고서 품질을 예쁘게 보이게 하는 것이 아니라, 실제 오류를 탐지하고 promotion을 통제하는 QA 체계를 구현하는 것이다.

## 2. 반드시 먼저 읽을 문서

1. `spec.md`
2. `config/qa_thresholds.yaml`
3. `config/output_paths.yaml`
4. `docs/playbooks/validate-sources.md`

## 3. 선행조건

- Step 4 완료
- `review_pack.md` 포함 run 결과 존재
- `source_map.json`과 `evidence_graph.jsonl` 생성 가능
- `config/qa_thresholds.yaml`의 필수 tolerance가 채워짐

## 4. 필수 범위

- QA rule registry
- source coverage check
- number reconcile check
- recency check
- unit/basis check
- output coherence check
- `qa_report.json` 및 `failure_report.md` 생성

## 5. 필수 파일 및 산출물

최소 코드 산출물:

- `src/qa/rule_registry.py`
- `src/qa/source_check.py`
- `src/qa/number_reconcile.py`
- `src/qa/recency_check.py`
- `src/qa/unit_basis_check.py`
- `src/qa/opinion_boundary_check.py`
- `src/qa/output_schema_check.py`
- `src/qa/cross_artifact_consistency_check.py`

필수 run 산출물:

- `runs/<run_id>/qa/qa_report.json`
- `runs/<run_id>/qa/failure_report.md`

필수 eval 자산:

- `evals/datasets/golden/`
- `evals/rubrics/`

## 6. QA 규칙

필수 검사:

- source map 존재 여부
- review pack 존재 여부
- KPI source coverage
- recency violation
- metric tolerance 초과 여부
- Markdown, JSON, evidence graph 일관성

모든 tolerance 기준은 `config/qa_thresholds.yaml`을 따른다.  
문서에 없는 임의 tolerance를 코드에서 새로 만들지 않는다.

## 7. number reconcile 규칙

최소 검사 대상:

- revenue
- gross_margin
- operating_margin
- eps
- fcf
- share_count
- net_cash_or_debt
- guidance_ranges

판정 규칙:

- tolerance 이내: pass
- tolerance 초과: conflict
- tolerance 미정: blocked

`blocked` 상태는 pass가 아니다.

## 8. 결과 판정 규칙

`qa_report.json`의 `status`는 아래 중 하나다.

- `pass`
- `warn`
- `fail`
- `blocked`

판정 원칙:

- strict mode는 `pass`만 promote 가능
- assisted mode는 `warn`까지 허용 가능하나 human review 승인 필요
- `blocked`는 tolerance 또는 필수 설정 미정 상태이므로 promote 금지

## 9. 실패 처리 규칙

- conflict를 발견하면 summary에서 숨기지 않는다
- failure report는 어느 단계에서 왜 실패했는지 남긴다
- QA 실패 run은 latest output을 갱신하지 않는다
- QA 재실행은 같은 run에 덮어쓰기 가능하지만 이전 판정 변경 이유를 기록한다

## 10. 구현 순서

1. `config/qa_thresholds.yaml` 값을 확인한다.
2. QA rule registry를 구현한다.
3. 필수 검사기를 구현한다.
4. `qa_report.json` 생성기를 구현한다.
5. `failure_report.md` 생성기를 구현한다.
6. golden dataset과 rubric 구조를 만든다.
7. 샘플 run으로 QA를 실행한다.

## 11. 구현 후 검증

- 모든 run에 pass/warn/fail/blocked 근거가 남는가
- tolerance 미정 상태를 blocked로 처리하는가
- source map 누락을 탐지하는가
- review pack 누락을 탐지하는가
- golden dataset 비교가 가능한가

목표 검증 파일:

- `tests/unit/test_qa_rules.py`
- `tests/integration/test_eval_gate.py`

예상 검증 명령:

```powershell
.\.venv311\Scripts\python.exe -m pytest tests\unit\test_qa_rules.py
.\.venv311\Scripts\python.exe -m pytest tests\integration\test_eval_gate.py
```

## 12. 완료 기준

- `qa_report.json` 생성
- `failure_report.md` 생성
- tolerance 기반 number reconcile 동작
- strict mode promotion gate 동작
- golden dataset 구조 생성

## 13. 실패 조건 및 주의사항

- tolerance가 비어 있는데 pass 판단을 내림
- QA를 Markdown에만 적용함
- conflict를 찾고도 summary에서 숨김
- review pack 없이 reviewer 판단을 기대함
- blocked 상태를 warn이나 pass로 취급함

## 14. 다음 단계 인계물

- QA registry
- golden dataset 초안
- 샘플 `qa_report.json`
- 샘플 `failure_report.md`
- failure taxonomy
