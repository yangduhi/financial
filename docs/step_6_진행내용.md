# Step 6. 운영, 확장, 배포 기준 확정

## 1. 목적

이 단계의 목적은 시스템을 구현 상태에서 운영 가능한 상태로 전환하는 것이다.  
여기서는 로컬 dry run, 실패 복구, 보안, 관측성, 확장 진입 조건을 문서와 규칙으로 고정한다.

## 2. 반드시 먼저 읽을 문서

1. `spec.md`
2. `docs/runbook.md`
3. `docs/recovery.md`
4. `config/runtime_defaults.yaml`
5. `config/output_paths.yaml`

## 3. 선행조건

- Step 5 완료
- 최소 3개 run 결과 존재
- failure taxonomy 존재
- `qa_report.json` 기반 promotion 규칙 검증 완료

## 4. 필수 범위

- 로컬 운영 runbook 고정
- failure recovery 절차 고정
- 보안 및 권한 운영 기준 문서화
- 품질/비용/성능 지표 고정
- V2, V3 진입 조건 고정

## 5. 필수 산출물

- `docs/runbook.md`
- `docs/recovery.md`
- `docs/security_governance.md`
- `docs/operations_metrics.md`
- `docs/expansion_criteria.md`

## 6. 로컬 운영 규칙

기본 흐름:

1. blocked decision 여부 확인
2. 입력 파일 준비
3. run 실행
4. `manifest.json` 확인
5. `qa_report.json` 확인
6. 필요 시 review pack 검토
7. `qa_passed` 또는 승인된 `warn`만 promote

## 7. 보안 및 거버넌스 규칙

- vendor credential은 secret store 또는 `.env`에서만 로드
- 민감 데이터는 prompt에 직접 넣지 않는다
- internal memory는 access control 승인 전 활성화하지 않는다
- run artifact에는 confidentiality tag를 남긴다
- audit 가능한 기록 없이 latest promote를 하지 않는다

## 8. 관측성 규칙

최소 추적 지표:

- run success rate
- average run time
- retrieval latency
- unresolved discrepancy rate
- manual correction frequency
- cost per run

각 지표의 정의와 계산식은 `docs/operations_metrics.md`에 기록한다.

## 9. 실패 복구 및 롤백 규칙

- latest output 오류 발견 시 promoted copy만 교체 또는 제거
- 원래 run artifact는 삭제하지 않는다
- 재실행은 새 `run_id`로 수행한다
- rollback 사실은 failure report에 남긴다

## 10. 확장 진입 조건

V2 Comparable / Valuation 자동화 진입 조건:

- Ticker-to-Report V1 성공률 안정화
- share count, FX, EV 관련 QA 안정화
- peer selection 기준 확정

V3 팀 표준 패키지 진입 조건:

- house style 문서화
- reviewer feedback 반복 패턴 정리
- 플레이북과 템플릿 재사용 가능

## 11. 구현 순서

1. `docs/runbook.md`를 최신화한다.
2. `docs/recovery.md`를 최신화한다.
3. `docs/security_governance.md`를 작성한다.
4. `docs/operations_metrics.md`를 작성한다.
5. `docs/expansion_criteria.md`를 작성한다.
6. promotion 및 rollback 규칙을 최종 확인한다.

## 12. 구현 후 검증

- 신규 참여자가 문서만 보고 dry run을 재현할 수 있는가
- failed run과 promoted output을 명확히 구분할 수 있는가
- 민감 데이터와 공개 데이터의 경계가 문서화되어 있는가
- rollback 절차가 문서만으로 실행 가능한가
- V2/V3 진입 조건이 모호하지 않은가

## 13. 완료 기준

- 운영 문서만으로 기본 실행과 복구가 가능하다
- promotion과 rollback 규칙이 고정되어 있다
- 보안 및 감사 규칙이 문서화되어 있다
- 품질/비용/성능 지표 정의가 있다
- 확장 조건이 문서화되어 있다

## 14. 실패 조건 및 주의사항

- 운영 문서 없이 개인 기억에 의존함
- rollback 절차가 없음
- latest output 갱신 규칙이 모호함
- 보안/감사 규칙보다 확장을 먼저 추진함
- metrics 정의 없이 성능/비용을 비교함
