# Security Governance

## Rules

- credential은 문서에 쓰지 않는다
- `.env` 또는 secret store 외 저장 금지
- internal memory source는 access control 승인 전 비활성 상태 유지
- audit log 없는 외부 배포 금지

## Review Triggers

- 새 vendor 추가
- internal memory 활성화
- 외부 connector 또는 원격 MCP 도입
