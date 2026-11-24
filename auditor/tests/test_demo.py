from pathlib import Path

from ..demo import main

EXAMPLES = Path(__file__).resolve().parents[2] / "examples"


def test_demo_with_errors_finds_income_mismatch(capsys):
    assert main([str(EXAMPLES / "with_errors"), "--no-llm"]) == 0
    out = capsys.readouterr().out
    assert "income_mismatch" in out and "📐 Regla" in out


def test_demo_clean_has_no_findings(capsys):
    assert main([str(EXAMPLES / "clean"), "--no-llm"]) == 0
    assert "Sin discrepancias" in capsys.readouterr().out


def test_demo_missing_files(tmp_path, capsys):
    assert main([str(tmp_path), "--no-llm"]) == 1
