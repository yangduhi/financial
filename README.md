# Financial Research Workbench

## Authority

이 워크스페이스의 실행 기준 문서는 아래 순서로 읽는다.

1. `README.md`
2. `spec.md`
3. `plan.md`
4. `tasks.md`
5. `docs/step_1_진행내용.md`
6. `docs/step_2_진행내용.md`
7. `docs/step_3_진행내용.md`
8. `docs/step_4_진행내용.md`
9. `docs/step_5_진행내용.md`
10. `docs/step_6_진행내용.md`

`docs/archive/` 아래 문서는 참고용 보관본이며 실행 기준이 아니다.

## Goal

목표는 단일 티커 기준의 금융 리서치 보고서 생성 파이프라인을 구축하는 것이다.  
핵심은 그럴듯한 텍스트 생성이 아니라, 출처 추적이 가능한 수치와 서술을 안전하게 생성하고 검증하는 것이다.

## Current Workspace

- workspace root: `D:\vscode\Financial`
- default Python interpreter: `.\.venv311\Scripts\python.exe`
- repository status: Git 저장소가 아닐 수 있으므로 `workspace_revision`은 Git SHA가 없으면 `nogit`로 기록한다

## Hard Stops

아래 중 하나라도 만족하면 live implementation을 시작하지 않는다.

- `config/sources.yaml`의 필수 소스에 `decision_status: decided`가 아닌 항목이 있음
- `config/sources.yaml`의 필수 소스가 `enabled: true`가 아님
- `config/qa_thresholds.yaml`의 필수 tolerance 값이 `null`임
- Step 1 필수 산출물인 `AGENTS.md` 또는 `.codex/config.toml`이 없음
- 입력 파일이 `spec.md`의 입력 계약을 만족하지 않음

이 경우 허용되는 작업은 문서 정리, contract scaffold 작성, 테스트 뼈대 작성까지다.  
실제 live vendor 연동과 QA pass 판정은 보류한다.

## Required Registries

아래 파일은 사용자 결정사항과 실행 기준의 단일 저장소다.

- `config/sources.yaml`
- `config/report_types.yaml`
- `config/runtime_defaults.yaml`
- `config/qa_thresholds.yaml`
- `config/output_paths.yaml`

사용자 지정 변수나 운영 규칙을 새로 만들 때는 위 파일 중 하나에 먼저 기록하고 문서와 구현이 이를 참조해야 한다.

## Output Rule

모든 실행 산출물은 `runs/<run_id>/` 아래에 먼저 생성한다.  
`data/outputs/latest/`는 QA를 통과한 결과만 복사한다.  
실패한 run은 `data/outputs/latest/`를 갱신하지 않는다.

## Start Order For Codex

1. `spec.md`에서 목표, 범위, 계약을 확인한다.
2. `config/*.yaml`에서 사용자 결정사항과 출력 규칙을 읽는다.
3. `plan.md`에서 선행조건과 단계 의존성을 확인한다.
4. `tasks.md`에서 현재 작업 항목과 blocked decision을 확인한다.
5. 해당 단계의 `docs/step_X_진행내용.md`를 읽고 구현한다.
