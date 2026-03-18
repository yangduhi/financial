# Metric Alias Standard

## Purpose

한국어 자연어 질의를 canonical metric으로 안정적으로 정규화하기 위한 alias 표준이다.

## Core Aliases

- `영업이익` -> `operating_income`
- `매출`, `매출액` -> `revenue`
- `순이익` -> `net_income`
- `EPS`, `주당순이익` -> `eps`
- `FCF`, `잉여현금흐름` -> `fcf`
- `영업이익률`, `영업마진` -> `operating_margin`
- `총이익률`, `gross margin` -> `gross_margin`

## Ambiguous Terms

아래 표현은 단독으로는 확정하지 않는다.

- `마진`
- `이익`
- `실적`

이 경우 상태를 `AMBIGUOUS_METRIC`으로 처리한다.

## Implementation Rules

- alias dictionary 우선
- 한국어 alias 우선 지원
- 대소문자 무시
- 띄어쓰기 변형 허용
