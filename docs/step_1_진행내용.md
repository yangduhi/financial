# Step 1. 개발 기반 및 레포 표준 확정

## 1. 목적

이 단계의 목적은 현재 작업공간 `D:\vscode\Financial`를 실행 가능한 Financial Research Workbench 레포 기준으로 고정하는 것이다.  
이 단계가 끝나면 이후 Step 2~6이 참조할 문서 우선순위, 디렉터리 구조, 설정 registry, 품질 명령, 보안 규칙이 모두 정리되어 있어야 한다.

## 2. 반드시 먼저 읽을 문서

Step 1을 시작하기 전에 아래 문서를 순서대로 읽는다.

1. `README.md`
2. `spec.md`
3. `plan.md`
4. `tasks.md`
5. `config/*.yaml`

`docs/archive/` 아래 문서는 참고용이며 Step 1 구현 기준으로 사용하지 않는다.

## 3. 선행조건

아래 항목을 모두 만족해야 Step 1을 시작할 수 있다.

- 작업 루트가 `D:\vscode\Financial`로 고정되어 있을 것
- `.venv311` 가상환경이 실행 가능할 것
- root 문서 `README.md`, `spec.md`, `plan.md`, `tasks.md`가 존재할 것
- `config/` 아래 registry 파일이 존재할 것

## 4. 이번 단계의 핵심 범위

필수 범위:

- authoritative 문서 구조 고정
- 레포 표준 디렉터리 구조 생성
- `AGENTS.md` 생성
- `.codex/config.toml` 생성
- `.codex/prompts/` 구조 생성
- `pyproject.toml`, `.env.example`, `.gitignore` 생성
- 테스트, 평가, run 저장 위치 분리

이번 단계에서 하지 않는 일:

- live MCP 연동
- 실제 vendor 데이터 파싱
- 실제 report 생성 로직 구현

## 5. 표준 구조

Step 1 완료 시점의 표준 구조는 아래와 같다.

```text
D:\vscode\Financial
├─ README.md
├─ spec.md
├─ plan.md
├─ tasks.md
├─ AGENTS.md
├─ .codex/
│  ├─ config.toml
│  └─ prompts/
│     ├─ analyst_system.md
│     ├─ earnings_review.md
│     ├─ initiation_note.md
│     └─ valuation_memo.md
├─ config/
│  ├─ sources.yaml
│  ├─ report_types.yaml
│  ├─ runtime_defaults.yaml
│  ├─ qa_thresholds.yaml
│  └─ output_paths.yaml
├─ docs/
│  ├─ step_1_진행내용.md
│  ├─ ...
│  ├─ playbooks/
│  │  ├─ build-report.md
│  │  ├─ refresh-comps.md
│  │  └─ validate-sources.md
│  ├─ runbook.md
│  ├─ recovery.md
│  └─ archive/
├─ examples/
│  ├─ report_input.example.json
│  ├─ expected_manifest.example.json
│  ├─ expected_source_map.example.json
│  └─ review_pack.example.md
├─ mcp/
│  ├─ common/
│  ├─ docs_gateway/
│  ├─ market_data_gateway/
│  └─ research_memory_gateway/
├─ src/
│  ├─ ingest/
│  ├─ parse/
│  ├─ normalize/
│  ├─ analysis/
│  ├─ report/
│  ├─ qa/
│  ├─ schemas/
│  └─ orchestration/
├─ templates/
│  ├─ reports/
│  ├─ xlsx/
│  └─ pptx/
├─ tests/
│  ├─ unit/
│  ├─ integration/
│  ├─ contracts/
│  ├─ fixtures/
│  └─ golden/
├─ evals/
│  ├─ datasets/
│  ├─ rubrics/
│  └─ reports/
├─ data/
│  ├─ raw/
│  ├─ parsed/
│  ├─ normalized/
│  ├─ derived/
│  └─ outputs/
├─ runs/
└─ .venv311/
```

## 6. 설계 원칙

### 6.1 Evidence-first

핵심 문장과 숫자는 출처와 연결되어야 한다.

### 6.2 Point-in-time safe

`as_of_date`, `as_of_datetime`, `fiscal_period`, `currency`, `unit_basis`, `share_basis`를 항상 보존한다.

### 6.3 Contract-first

문서 출력보다 구조화 데이터와 schema 검증이 먼저다.

### 6.4 Deterministic before agentic

정규화, 계산, reconciliation은 코드로 고정한다.

### 6.5 Human-review gating

투자의견과 valuation 해석은 사람 검토 없이 promote하지 않는다.

## 7. 필수 산출물

Step 1 완료 시점의 필수 산출물은 아래와 같다.

- `AGENTS.md`
- `.codex/config.toml`
- `.codex/prompts/`
- `pyproject.toml`
- `.env.example`
- `.gitignore`
- `mcp/common/`
- `src/`
- `tests/`
- `evals/`
- `data/`
- `runs/`

이미 존재하는 문서:

- `README.md`
- `spec.md`
- `plan.md`
- `tasks.md`
- `config/*.yaml`
- `docs/playbooks/*.md`
- `docs/runbook.md`
- `docs/recovery.md`

## 8. 구현 순서

1. Python 인터프리터와 workspace root를 확인한다.
2. 표준 디렉터리 구조를 생성한다.
3. `AGENTS.md`를 작성한다.
4. `.codex/config.toml`과 `.codex/prompts/`를 작성한다.
5. `pyproject.toml`, `.env.example`, `.gitignore`를 작성한다.
6. `tests/`, `evals/`, `data/`, `runs/` 기본 구조를 만든다.
7. lint, type-check, test 명령을 `pyproject.toml` 또는 문서에 고정한다.

## 9. 구현 후 검증

아래 명령이 정상 동작해야 한다.

```powershell
.\.venv311\Scripts\python.exe --version
Test-Path .\README.md
Test-Path .\spec.md
Test-Path .\plan.md
Test-Path .\tasks.md
Test-Path .\config\sources.yaml
Test-Path .\AGENTS.md
Test-Path .\.codex\config.toml
```

체크리스트:

- nested repo를 새로 만들지 않았는가
- archived 초안이 실행 경로에 다시 나타나지 않았는가
- root 문서와 config registry가 구현 경로보다 먼저 존재하는가
- `.env.example`에 실제 비밀값이 없는가

## 10. 완료 기준

아래 조건을 모두 만족하면 Step 1 완료다.

- Step 2가 바로 사용할 문서와 registry가 모두 존재한다
- `AGENTS.md`와 `.codex/config.toml`이 존재한다
- 테스트, 평가, 데이터, run 위치가 분리되어 있다
- output path는 `config/output_paths.yaml` 기준으로 해석 가능하다

## 11. 실패 조건 및 예외

아래 중 하나라도 있으면 Step 1은 미완료다.

- `AGENTS.md` 없음
- `.codex/config.toml` 없음
- root 문서와 단계 문서가 서로 다른 구조를 지시함
- `.env.example`에 실제 비밀값 기록
- `data`, `runs`, `src`를 혼합 저장

## 12. 다음 단계 인계물

Step 2로 넘기기 전에 아래를 준비한다.

- Step 1 산출물 전체
- `config/sources.yaml` 검토 결과
- `config/output_paths.yaml` 경로 규칙 확인 결과
- `.codex/prompts/` 초기 파일
