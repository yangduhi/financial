# Execution Plan

## 1. Phase Order

1. Step 1: 개발 기반 및 레포 표준 확정
2. Step 2: MCP 계층 및 데이터 접근 평면 구축
3. Step 3: canonical 데이터 파이프라인 및 evidence graph 구축
4. Step 4: Ticker-to-Report V1 워크플로 구축
5. Step 5: QA, 평가, 통제 프레임워크 구축
6. Step 6: 운영, 확장, 배포 기준 확정

후행 단계는 선행 단계의 완료 기준을 만족하기 전까지 시작하지 않는다.

## 2. Dependency Rules

- Step 2는 Step 1 산출물과 `config/sources.yaml` 결정사항이 있어야 시작 가능
- Step 3는 Step 2의 contract와 sample response가 있어야 시작 가능
- Step 4는 Step 3의 canonical schema, manifest, evidence 구조가 있어야 시작 가능
- Step 5는 Step 4의 review pack 포함 end-to-end run이 있어야 시작 가능
- Step 6는 Step 5의 QA 결과와 failure taxonomy가 있어야 시작 가능

## 3. Stop Rules

아래 상황에서는 다음 단계를 진행하지 않는다.

- 필수 산출물 경로와 형식이 확정되지 않음
- 필수 config 값이 `null` 또는 `required_user_decision` 상태임
- 완료 기준이 테스트나 샘플 산출물로 검증되지 않음
- 실패 처리 규칙이 없는 상태로 다음 단계를 시작함

## 4. Promotion Rule

- 단계 결과물은 해당 단계의 완료 기준을 만족할 때만 다음 단계 입력으로 사용
- Step 4 이후에는 `qa_passed` 결과만 `data/outputs/latest/`로 promote

## 5. Recommended Working Order

1. `tasks.md`에서 blocked decision 확인
2. blocked decision 해소 또는 문서에 명시
3. 현재 단계 구현
4. 단계별 검증 실행
5. 산출물 경로와 manifest 상태 기록
6. 다음 단계 인계물 준비
