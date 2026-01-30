from __future__ import annotations

from infrastructure.CLI import ui


def test_clean_cell_removes_non_ascii_and_whitespace() -> None:
    assert ui._clean_cell("  hola\tmundo\n") == "hola mundo"
    assert ui._clean_cell("caf\u00e9") == "caf"


def test_truncate_behaviour() -> None:
    assert ui._truncate("abc", 5) == "abc"
    assert ui._truncate("abcdef", 3) == "abc"
    assert ui._truncate("abcdef", 5) == "ab..."


def test_fit_text_behaviour() -> None:
    assert ui._fit_text("hello", 10) == "hello"
    assert ui._fit_text("hello", 3) == "hel"
    assert ui._fit_text("hello", 0) == ""


def test_footer_line_formats_elapsed() -> None:
    line = ui._footer_line(80, elapsed="00:00:10")
    assert "T=00:00:10" in line.plain


def test_format_datetime_cell_handles_int_and_str() -> None:
    assert ui._format_datetime_cell("created_at", 0) == "1969-12-31 21:00:00"
    assert ui._format_datetime_cell("created_at", "not-a-ts") == "not-a-ts"
    assert ui._format_datetime_cell("other", 123) == "123"
