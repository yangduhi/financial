# Validate Sources Playbook

## Purpose

source 선택, 최신성, citation 연결, ambiguity 처리 규칙을 검증한다.

## Minimum Checks

- primary source 우선순위 적용 여부
- identifier ambiguity 발생 시 fail loud 여부
- source map 연결 여부
- recency violation 여부
- license_scope 기록 여부

## Failure Rule

아래 중 하나라도 있으면 pass 처리하지 않는다.

- source map 누락
- 최신 문서보다 오래된 문서가 우선 선택됨
- primary source 부족
- source entitlement가 불명확함
