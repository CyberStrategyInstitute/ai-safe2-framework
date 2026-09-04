"""Regression tests for scanner quality and bounded execution."""

from pathlib import Path

from scanner.scanner import StaticScanner


def test_function_declaration_is_not_treated_as_model_load(tmp_path: Path) -> None:
    (tmp_path / "models.py").write_text(
        "def load_model(name: str):\n    return name\n", encoding="utf-8"
    )

    result = StaticScanner().scan_project(str(tmp_path))

    assert not any(v.control_id == "A2.3" for v in result.violations)


def test_markdown_and_generated_environments_are_skipped(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("eval(user_input)\n", encoding="utf-8")
    generated = tmp_path / ".uv-cache"
    generated.mkdir()
    (generated / "unsafe.py").write_text("eval(user_input)\n", encoding="utf-8")

    result = StaticScanner().scan_project(str(tmp_path))

    assert result.meta["scanned_files"] == 0
    assert result.violations == []


def test_scan_stops_at_configured_file_limit(tmp_path: Path) -> None:
    for index in range(3):
        (tmp_path / f"module_{index}.py").write_text("value = 1\n", encoding="utf-8")

    result = StaticScanner(max_files=2).scan_project(str(tmp_path))

    assert result.meta["scanned_files"] == 2
    assert result.meta["scan_truncated"] is True
    assert result.meta["max_files"] == 2
