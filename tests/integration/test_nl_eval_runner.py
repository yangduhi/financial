from src.orchestration.nl_eval_runner import run_dataset


def test_run_dataset_generates_verification() -> None:
    summary = run_dataset()
    assert summary["total"] >= 1
    assert summary["passed"] >= 1
