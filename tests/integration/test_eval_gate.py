from src.qa.source_check import validate_source_map_present


def test_source_map_is_required_for_eval_gate() -> None:
    assert validate_source_map_present(True) is True
