from src.orchestration.nl_tool_planner import plan_tools


def test_metric_trend_plan_is_minimal() -> None:
    plan = plan_tools(
        {
            "status": "OK",
            "intent": "metric_trend",
            "metric": "operating_income",
            "period": {"type": "recent_quarters", "value": 4},
        }
    )
    assert plan["status"] == "OK"
    assert plan["tools"] == ["resolve_entity", "get_metric_trend"]
    assert plan["tool_budget"] == 2
