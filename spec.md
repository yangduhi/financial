# Specification

## 1. Objective

단일 티커 기준의 금융 리서치 보고서 생성 파이프라인을 구축한다.  
핵심 결과물은 출처 추적이 가능한 구조화 산출물과 사람이 읽을 수 있는 요약 문서다.

## 2. In Scope

- 레포 부트스트랩과 개발 표준 수립
- MCP 기반 문서/시장 데이터 접근 계층
- canonical 데이터 파이프라인
- 단일 티커 기준 report workflow
- QA, evaluation, promotion gate
- 운영 및 확장 기준 문서화

## 3. Out of Scope

- 실시간 매매 집행
- 멀티테넌트 SaaS
- 원격 배포 자동화
- vendor 선택을 문서 없이 임의 결정하는 작업

## 4. Document Precedence

문서 충돌 시 우선순위는 아래와 같다.

1. `spec.md`
2. `config/*.yaml`
3. `plan.md`
4. `tasks.md`
5. `docs/step_*_진행내용.md`
6. `docs/archive/*`

## 5. Environment Contract

- workspace root: `D:\vscode\Financial`
- Python interpreter: `.\.venv311\Scripts\python.exe`
- default shell examples: PowerShell
- Git SHA가 없는 경우 `workspace_revision = "nogit"`로 기록

## 6. Source Contract

모든 외부/내부 데이터 소스 계약은 `config/sources.yaml`에 기록한다.

필수 조건:

- 문서 조회용 source 1개 이상
- 시장 데이터 조회용 source 1개 이상
- 각 source에 `purpose`, `auth_required`, `auth_envs`, `license_scope`, `decision_status` 존재

차단 조건:

- `decision_status != "decided"` 인 필수 source 존재
- `enabled != true` 인 필수 source 존재
- `auth_required = true` 인 source에서 `auth_envs`가 비어 있음
- `auth_required = true` 인 source의 실제 환경변수가 런타임에서 비어 있음

## 7. Input Contract

입력은 JSON 파일로 저장하며 기본 경로는 `runs/<run_id>/input.json`이다.

최소 입력 필드:

- `identifier`
- `report_type`
- `as_of_date`
- `strict_mode`

`identifier` 구조:

```json
{
  "type": "ticker_exchange",
  "value": "ANET",
  "exchange": "NYSE"
}
```

허용 `identifier.type`:

- `ticker_exchange`
- `cik`
- `figi`

`ticker` 단독 문자열은 허용하지 않는다.  
거래소 또는 동등한 전역 식별자를 반드시 제공한다.

허용 `report_type` 값은 `config/report_types.yaml`의 key만 사용한다.

## 8. Output Contract

정확한 경로 규칙은 `config/output_paths.yaml`을 따른다.

필수 산출물:

- `runs/<run_id>/input.json`
- `runs/<run_id>/manifest.json`
- `runs/<run_id>/outputs/summary.md`
- `runs/<run_id>/outputs/kpi_summary.json`
- `runs/<run_id>/outputs/source_map.json`
- `runs/<run_id>/outputs/review_pack.md`
- `runs/<run_id>/qa/qa_report.json`
- `runs/<run_id>/evidence/evidence_graph.jsonl`

필수 원칙:

- 모든 산출물은 먼저 `runs/<run_id>/` 아래 생성
- `data/outputs/latest/`는 promoted copy만 저장
- 실패한 run은 latest copy를 갱신하지 않음

## 9. Run Status Contract

`manifest.json`의 `status`는 아래 중 하나여야 한다.

- `created`
- `ingesting`
- `parsed`
- `normalized`
- `derived`
- `reported`
- `qa_passed`
- `qa_failed`
- `failed`

중간 단계 실패 시:

- 이후 단계는 실행하지 않는다
- 이미 생성된 `runs/<run_id>/` 산출물은 보존한다
- `data/outputs/latest/`는 갱신하지 않는다

## 10. QA Contract

QA 정책은 `config/qa_thresholds.yaml`을 따른다.

필수 조건:

- source map 존재
- review pack 존재
- 핵심 metric tolerance 설정 존재
- recency check, source coverage check, number reconcile check 실행

`config/qa_thresholds.yaml`에 필수 값이 없으면 QA pass 판정을 내리지 않는다.

## 11. Human Review Contract

아래 항목이 하나라도 존재하면 review pack 검토가 필수다.

- unresolved discrepancy
- `[UNKNOWN]` 항목
- low confidence claim
- valuation implication
- investment opinion

## 12. Failure Handling

재시도와 복구 규칙:

- 네트워크 재시도는 source fetch 단계에서만 적용
- 파싱/정규화/QA 실패는 자동 재시도하지 않음
- 실패 원인은 `runs/<run_id>/qa/qa_report.json` 또는 `runs/<run_id>/manifest.json`에 기록
- 같은 입력으로 재실행 시 새 `run_id`를 사용하되 `retries_of` 필드를 manifest에 기록

## 13. Unresolved User Decisions

현재 문서가 실행 가능하려면 아래 항목이 반드시 채워져야 한다.

- `SEC_API_USER_AGENT` 환경변수 설정
- internal research memory 사용 여부 결정
