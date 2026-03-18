from mcp.macro_data_gateway.server import list_tools as list_macro_tools


def test_macro_gateway_lists_tools() -> None:
    assert len(list_macro_tools()) >= 3
