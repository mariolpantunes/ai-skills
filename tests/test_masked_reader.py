import importlib.util
import os
import shutil
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HOME = Path(tempfile.mkdtemp())
(HOME / "private" / "in").mkdir(parents=True)
shutil.copy(ROOT / "tests/data/mail.txt", HOME / "private/in/Ana Ferreira - fatura.txt")
shutil.copy(ROOT / "tests/data/terms.txt", HOME / "private/terms.txt")
os.environ["AI_HOME"] = str(HOME)
spec = importlib.util.spec_from_file_location("masked_reader", ROOT / "plugins/privacy/mcp/masked_reader.py")
M = importlib.util.module_from_spec(spec)
spec.loader.exec_module(M)

RAW = ("501964843", "912 345 678", "ana.ferreira@acme.example", "4539 1488", "hunter2xyz", "Ana Ferreira", "Acme")


def test_names_and_text_are_masked():
    listing = M.list_documents()
    assert "NAME-1 - fatura.txt" in listing and "Ana" not in listing
    for out in (M.open_document("NAME-1 - fatura.txt"), M.read_pages("NAME-1 - fatura.txt"),
                M.search_document("NAME-1 - fatura.txt", "NIF")):
        assert not any(r in out for r in RAW), out
    assert "<NIF_1>" in M.read_pages("NAME-1 - fatura.txt")


def test_real_value_is_not_searchable_and_unknown_name_fails():
    assert M.search_document("NAME-1 - fatura.txt", "501964843") == "no match"
    try:
        M.read_pages("Ana Ferreira - fatura.txt")
        raise AssertionError("the original name must not work")
    except ValueError:
        pass


def test_no_tool_returns_values():
    assert {"list_documents", "open_document", "read_pages", "read_section", "search_document"} <= set(dir(M))
    assert not any("restore" in n or "unmask" in n for n in dir(M))


def test_search_all_ranks_pages_across_documents(tmp_path, monkeypatch):
    import importlib

    (tmp_path / "private" / "in").mkdir(parents=True)
    (tmp_path / "private" / "in" / "a.md").write_text("# Supplier Norte\n\nAverage delivery time: 96 hours. Price 4.25. Contact quality@norte.example", encoding="utf-8")
    (tmp_path / "private" / "in" / "b.md").write_text("# Supplier Sado\n\nAverage delivery time: 48 hours. Price 3.99. The incident was a delay in July.", encoding="utf-8")
    monkeypatch.setenv("AI_HOME", str(tmp_path))
    monkeypatch.delenv("MASK_READER_DIR", raising=False)
    import sys
    sys.path.insert(0, str(ROOT / "plugins/privacy/mcp"))
    mr = importlib.reload(importlib.import_module("masked_reader"))
    out = mr.search_all("delay in July")
    assert out.index("b.md") < out.index("--- ", 20) or "b.md" in out.splitlines()[1]
    assert "quality@norte.example" not in mr.search_all("contact norte")
