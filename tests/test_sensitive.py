import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("sensitive", ROOT / "plugins/privacy/skills/mask-sensitive/scripts/sensitive.py")
S = importlib.util.module_from_spec(spec)
spec.loader.exec_module(S)


def masked(text, terms=()):
    v = S.Vault(Path("/nonexistent/map.json"))
    return S.mask_text(text, v, [("NAME", t) for t in terms])


def test_validators():
    assert S.nif_ok("501964843") and not S.nif_ok("501964844")
    assert S.iban_ok("PT50 0002 0123 1234 5678 9015 4") and not S.iban_ok("PT50 0002 0123 1234 5678 9015 5")
    assert S.luhn_ok("4539 1488 0343 6467") and not S.luhn_ok("4539 1488 0343 6468")


def test_types_found_and_values_gone():
    text = (ROOT / "tests/data/mail.txt").read_text(encoding="utf-8")
    out, n = masked(text, ["Ana Ferreira"])
    for kind in ("IBAN", "NIF", "PHONE", "EMAIL", "CARD", "PLATE", "POSTAL", "SECRET", "ADDRESS", "NAME"):
        assert n[kind] >= 1, kind
    for raw in ("501964843", "912 345 678", "ana.ferreira@acme.example", "4539", "hunter2xyz", "12-AB-34", "3800-123", "Ana Ferreira"):
        assert raw not in out, raw


def test_not_overmasked():
    out, n = masked("Total 1.234,50 EUR em 2026-07-14, ref 2026/114, 12 itens, 123456788")
    assert out == "Total 1.234,50 EUR em 2026-07-14, ref 2026/114, 12 itens, 123456788" and not n


def test_stable_tokens_and_restore(tmp_path):
    v = S.Vault(tmp_path / "m.json")
    a, _ = S.mask_text("mail a@x.pt e outra vez A@X.PT", v, [])
    assert a == "mail <EMAIL_1> e outra vez <EMAIL_1>"
    v.save()
    assert json.loads((tmp_path / "m.json").read_text())["<EMAIL_1>"] == "a@x.pt"
