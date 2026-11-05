import os

from app.dotenv import load_dotenv, parse_line


def test_parse_line():
    assert parse_line("A=1") == ("A", "1")
    assert parse_line('B="x y"') == ("B", "x y")
    assert parse_line("export C='z'") == ("C", "z")
    assert parse_line("D=val # note") == ("D", "val")
    assert parse_line("# comment") is None
    assert parse_line("") is None
    assert parse_line("novalue") is None


def test_load_does_not_override_and_first_file_wins(tmp_path, monkeypatch):
    monkeypatch.delenv("SKIP_DOTENV", raising=False)
    monkeypatch.setenv("ALREADY_SET", "real")
    monkeypatch.delenv("DOTENV_NEW", raising=False)
    monkeypatch.delenv("DOTENV_SHARED", raising=False)
    a, b = tmp_path / "a.env", tmp_path / "b.env"
    a.write_text("ALREADY_SET=file\nDOTENV_NEW=1\nDOTENV_SHARED=first\n")
    b.write_text("DOTENV_SHARED=second\n")
    keys = load_dotenv([a, b, tmp_path / "missing.env"])
    assert os.environ["ALREADY_SET"] == "real"
    assert os.environ["DOTENV_NEW"] == "1"
    assert os.environ["DOTENV_SHARED"] == "first"
    assert sorted(keys) == ["DOTENV_NEW", "DOTENV_SHARED"]
    for k in ("DOTENV_NEW", "DOTENV_SHARED"):
        monkeypatch.delenv(k, raising=False)


def test_skip_flag(tmp_path, monkeypatch):
    monkeypatch.setenv("SKIP_DOTENV", "1")
    f = tmp_path / ".env"
    f.write_text("DOTENV_SKIPPED=1\n")
    assert load_dotenv([f]) == []
    assert "DOTENV_SKIPPED" not in os.environ
