# Tasks

## Done

- [x] DOC-001 Authoritative document order defined in `README.md`
- [x] DOC-002 `spec.md`, `plan.md`, `tasks.md` created
- [x] DOC-003 Decision registries under `config/` created
- [x] DOC-004 Example input and output files created under `examples/`
- [x] DOC-005 Legacy root step documents removed from execution path

## Blocked Decisions

- [x] DEC-001 Choose actual document vendor and update `config/sources.yaml`
- [x] DEC-002 Choose actual market data vendor and update `config/sources.yaml`
- [x] DEC-003 Set required QA tolerances in `config/qa_thresholds.yaml`
- [x] DEC-004 Confirm house style default in `config/runtime_defaults.yaml`

## Pending Implementation

- [x] STEP1-001 Create `AGENTS.md`
- [x] STEP1-002 Create `.codex/config.toml`
- [x] STEP1-003 Create `.codex/prompts/`
- [x] STEP1-004 Create repo scaffold from `docs/step_1_진행내용.md`
- [x] STEP2-001 Implement MCP common contract layer scaffold
- [x] STEP2-002 Implement `docs_gateway`
- [x] STEP2-003 Implement `market_data_gateway`
- [x] STEP2-004 Add smoke and contract tests scaffold
- [x] STEP2-005 Connect Finnhub fallback and verification path
- [x] STEP2-006 Add FRED macro gateway scaffold
- [x] STEP2-007 Document provider field mapping
- [x] STEP3-001 Implement canonical schemas
- [ ] STEP3-002 Implement raw/parsed/normalized/derived storage flow
- [ ] STEP3-003 Implement evidence graph output
- [ ] STEP4-001 Implement input loader and run manifest creation
- [ ] STEP4-002 Implement report renderer and source map generator
- [ ] STEP4-003 Make `review_pack.md` mandatory output
- [ ] STEP5-001 Implement QA registry and checks
- [ ] STEP5-002 Implement `qa_report.json` generation
- [ ] STEP6-001 Finalize runbook and recovery procedure

## MCP Practice Track

- [x] MCPP-000 Write `docs/v1_scope.md`
- [x] MCPP-001 Write `docs/mcp_tool_contracts.md`
- [x] MCPP-002 Write `docs/metric_alias_standard.md`
- [x] MCPP-003 Add `config/metric_aliases.yaml`
- [x] MCPP-004 Add `config/period_rules.yaml`
- [x] MCPP-005 Implement `resolve_entity`
- [x] MCPP-006 Implement `get_quarterly_metrics`
- [x] MCPP-007 Implement `get_metric_trend`
- [x] MCPP-008 Implement `get_recent_filings`
- [x] MCPP-009 Implement `get_source_evidence`
- [x] MCPP-010 Implement `src/orchestration/nl_query_normalizer.py`
- [x] MCPP-011 Implement `src/orchestration/nl_intent_parser.py`
- [x] MCPP-012 Implement `src/orchestration/nl_tool_planner.py`
- [x] MCPP-013 Implement `src/orchestration/nl_answer_generator.py`
- [ ] MCPP-014 Add natural-language query evaluation set
- [ ] MCPP-015 Add tool trace and failure logging

## Execution Rule

Blocked decisions must be resolved before live data integration or QA promotion work begins.
