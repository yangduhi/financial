# Natural-Language Orchestration Plan

## Fixed Pipeline

1. Query normalization
2. Intent parsing
3. Entity resolution
4. Tool planning
5. Tool execution
6. Grounded answer generation

## Tool Budgets

- 단순 trend 질문: 2회
- evidence 질문: 3회
- ambiguity 해소 포함: 최대 4회

## Failure States

- `AMBIGUOUS_ENTITY`
- `AMBIGUOUS_METRIC`
- `NOT_FOUND`
- `INSUFFICIENT_EVIDENCE`
- `PLANNER_FAILURE`
