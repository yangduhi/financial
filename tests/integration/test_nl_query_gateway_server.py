from mcp.nl_query_gateway.stdio_server import handle_request


def test_mcp_gateway_lists_tools() -> None:
    response = handle_request({"jsonrpc": "2.0", "id": 1, "method": "tools/list"})
    assert response is not None
    tools = response["result"]["tools"]
    names = {tool["name"] for tool in tools}
    assert "answer_query" in names
    assert "get_metric_trend" in names


def test_mcp_gateway_calls_answer_query() -> None:
    response = handle_request(
        {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {
                "name": "answer_query",
                "arguments": {
                    "question": "ANET의 최근 4분기 영업이익 변동을 알려줘.",
                    "persist": False,
                },
            },
        }
    )
    assert response is not None
    assert response["result"]["isError"] is False
