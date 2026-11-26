import importlib.util
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "plugins/privacy/skills/mask-sensitive/scripts"
sys.path.insert(0, str(SCRIPTS))
import normalize  # noqa: E402
import pii_auto  # noqa: E402
import sensitive as S  # noqa: E402

pytest.importorskip("spacy")
REAL = ["Marta Lopes Cardoso", "Rui Pinto", "João Miguel Ferreira", "Silva & Filhos", "Paulo Mendes", "Ana Costa",
        "12/03/1980", "12345678901", "marta.cardoso@exemplo.example"]


def letter():
    return (ROOT / "tests/data/letter.txt").read_text(encoding="utf-8")


def test_names_found_without_a_word_list(tmp_path):
    out, n = S.mask_text(letter(), S.Vault(tmp_path / "map.json"), [])
    for raw in REAL:
        assert raw not in out, raw
    assert n["NAME"] >= 5 and n["DOB"] == 1 and n["NISS"] == 1 and n["ORG"] >= 1


def test_aliases_and_learning_are_stable(tmp_path):
    v = S.Vault(tmp_path / "map.json")
    S.mask_text(letter(), v, [])
    v.save()
    out, _ = S.mask_text("Falei com o Pinto e com a Costa ontem.", S.Vault(tmp_path / "map.json"), [])  # a later document
    assert "Pinto" not in out and "Costa" not in out
    assert "NAME: Rui Pinto" in (tmp_path / "terms.auto.txt").read_text(encoding="utf-8")


def test_ordinary_text_is_not_masked(tmp_path):
    t = "O relatório mostra que as vendas subiram 12 por cento em março e que o prazo termina na sexta."
    assert S.mask_text(t, S.Vault(tmp_path / "map.json"), [])[0] == t


def test_normalize_text():
    raw = "Relatório ﬁnal\nda ex-\nploração continua\nna próxima página.\n\n- item\n- outro\n"
    out = normalize.clean(raw)
    assert "final" in out and "exploração" in out and "continua na próxima página." in out and "- item\n- outro" in out


def test_pdf_is_normalised_and_masked(tmp_path):
    pymupdf = pytest.importorskip("pymupdf")
    doc = pymupdf.open()
    for i in range(4):
        page = doc.new_page()
        page.insert_text((72, 40), "ACME Lda - Relatorio interno", fontsize=9)  # header on every page
        page.insert_text((72, 800), f"Pagina {i + 1} de 4", fontsize=9)  # footer
        page.insert_text((72, 120), f"Seccao {i + 1}", fontsize=16)
        page.insert_text((72, 150), "Contacto: Rui Pinto, NIF 501964843, rui.pinto@exemplo.example", fontsize=11)
    pdf = tmp_path / "r.pdf"
    doc.save(pdf)
    text = S.read_text(pdf)
    assert "Relatorio interno" not in text and "Pagina 2 de 4" not in text and "Seccao 3" in text
    out, n = S.mask_text(text, S.Vault(tmp_path / "map.json"), [])
    assert "501964843" not in out and "rui.pinto@" not in out and n["NIF"] == 4 and n["EMAIL"] == 4


def test_restore_gives_back_values(tmp_path):
    v = S.Vault(tmp_path / "map.json")
    out, _ = S.mask_text(letter(), v, [])
    v.save()
    f = tmp_path / "summary.md"
    f.write_text("Resumo: " + out.splitlines()[0], encoding="utf-8")
    import argparse
    S.cmd_restore(argparse.Namespace(file=f, out=tmp_path / "back.md", map=tmp_path / "map.json", docx=True))
    assert "Marta Lopes Cardoso" in (tmp_path / "back.md").read_text(encoding="utf-8") and (tmp_path / "back.docx").is_file()
