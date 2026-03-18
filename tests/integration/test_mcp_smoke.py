from mcp.docs_gateway.server import list_tools as list_docs_tools
from mcp.market_data_gateway.server import list_tools as list_market_tools


def test_docs_gateway_lists_tools() -> None:
    assert len(list_docs_tools()) >= 3


def test_market_gateway_lists_tools() -> None:
    assert len(list_market_tools()) >= 3
