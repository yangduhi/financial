# NL Query MCP STDIO Usage

## Purpose

이 문서는 자연어 질의용 MCP gateway를 stdio transport로 실행하는 방법을 정리한다.

## Entry Point

- launcher: `scripts/run_nl_query_gateway.py`
- direct module: `mcp/nl_query_gateway/stdio_server.py`

## Local Run

PowerShell:

```powershell
.\.venv311\Scripts\python.exe .\scripts\run_nl_query_gateway.py
```

또는:

```powershell
.\.venv311\Scripts\python.exe -m mcp.nl_query_gateway.stdio_server
```

## Expected Protocol

이 서버는 stdio JSON-RPC 형태의 최소 MCP 흐름을 처리한다.

- `initialize`
- `tools/list`
- `tools/call`
- `ping`

## Exposed Tools

- `resolve_entity`
- `get_quarterly_metrics`
- `get_metric_trend`
- `get_recent_filings`
- `get_source_evidence`
- `answer_query`

## Example MCP Client Config

예시:

```json
{
  "mcpServers": {
    "financial-nl-query": {
      "command": "D:\\vscode\\Financial\\.venv311\\Scripts\\python.exe",
      "args": ["D:\\vscode\\Financial\\scripts\\run_nl_query_gateway.py"]
    }
  }
}
```

## Example Tool Call

질문 하나를 end-to-end로 실행:

```json
{
  "name": "answer_query",
  "arguments": {
    "question": "ANET의 최근 4분기 영업이익 변동을 알려줘.",
    "persist": true
  }
}
```

## Persisted Outputs

`persist: true`일 때 생성:

- `runs/<run_id>/input.json`
- `runs/<run_id>/manifest.json`
- `runs/<run_id>/outputs/source_map.json`
- `runs/<run_id>/qa/qa_report.json`
- `runs/<run_id>/logs/tool_traces/trace.json`

## Logging Rule

stdio transport이므로 stdout에는 MCP 메시지만 써야 한다.  
추가 로그는 파일 또는 artifact 경로로 남긴다.
