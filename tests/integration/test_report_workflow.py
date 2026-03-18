from src.qa.output_schema_check import has_required_output_files


def test_required_output_files_are_enforced() -> None:
    files_present = {"summary.md", "kpi_summary.json", "source_map.json", "review_pack.md"}
    assert has_required_output_files(files_present)
