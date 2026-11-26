"""Automatic detection of personal data that has no fixed pattern: names, organisations, labelled ids.

Layers (all local, nothing leaves the PC):
  1. context rules: honorifics (Sr., Dra., Eng.), "Name <e-mail>", header fields (De:, Para:, Nome:),
     signatures after a closing phrase, labelled ids (NISS, SNS, passport, citizen card), birth dates;
  2. a Portuguese NER model (spaCy pt_core_news_sm) for PERSON and ORG; places only with AI_NER_LOC=1;
  3. aliases: the surname and first name of every full name found.
Everything found is returned as (kind, value); the caller writes it to private/terms.auto.txt so the
user can review it and later documents are masked the same way. Switch off with AI_AUTO=0.
"""
from __future__ import annotations

import os
import re

CAP = r"[A-ZÀ-ÝÇ][\wà-ÿç'’-]+"
LINK = r"(?:d[aeo]s?|e|von|van|de la)"
FULL = rf"{CAP}(?:\s+(?:{LINK}\s+)?{CAP}){{0,4}}"
HONOR = r"(?:Exmo\.?\s*\(?a?\)?\.?\s*Sr\.?\s*\(?a?\)?\.?|Sr\.?ª?|Sra\.?|Dr\.?ª?|Dra\.?|Eng\.?ª?|Engª|Prof\.?ª?|Profa?\.?|Arq\.?ª?|Dona|Mr\.?|Mrs\.?|Ms\.?|Dear|Caro|Cara|Ex\.?mo|Ex\.?ma)"
CLOSING = r"(?:cumprimentos|atenciosamente|com os melhores cumprimentos|melhores cumprimentos|obrigad[oa]|best regards|kind regards|regards|sincerely|cordialmente|abra[cç]o)"
LABELS = {  # label regex -> kind
    r"NISS|seguran[cç]a social": "NISS",
    r"SNS|utente|n[.ºo°]* de utente": "SNS",
    r"cart[aã]o de cidad[aã]o|\bCC\b|\bBI\b|identifica[cç][aã]o civil": "IDDOC",
    r"passaporte|passport": "IDDOC",
    r"NIPC|contribuinte|NIF|VAT": "NIF",
}
STOP = {"de", "do", "da", "dos", "das", "para", "cc", "bcc", "from", "to", "assunto", "subject", "re", "fw", "fwd", "cumprimentos", "atenciosamente", "obrigado", "obrigada", "regards", "nome", "name", "data", "date", "total", "exmo", "exma", "sr", "sra", "dr", "dra", "eng", "prof", "dear", "caro", "cara", "senhor", "senhora", "bom", "boa", "olá", "ola"}
COMMON = {w for w in """january february march april may june july august september october november december
janeiro fevereiro março marco abril maio junho julho agosto setembro outubro novembro dezembro monday tuesday wednesday thursday friday saturday sunday
segunda terça terca quarta quinta sexta sábado sabado domingo contact commercial quarterly report terms incidents invoices price unit average delivery time
total subject assunto dear hello olá bom boa best regards kind thanks obrigado relatório relatorio contrato escritório escritorio""".split()}
ID_LIKE = re.compile(r"\d|^[A-Z]{2,6}-")
_nlp = None
_nlp_failed = False


def _clean(name: str) -> str:
    words = [w for w in re.split(r"\s+", name.strip(" ,.;:-<>()\"'")) if w]
    while words and words[0].strip(".ªa").lower() in STOP:
        words.pop(0)
    return " ".join(words)


def _ner(text: str) -> list[tuple[str, str]]:
    global _nlp, _nlp_failed
    if _nlp_failed or os.environ.get("AI_NER", "1") == "0":
        return []
    if _nlp is None:
        try:
            import spacy

            _nlp = spacy.load("pt_core_news_sm", disable=["lemmatizer", "attribute_ruler"])
            _nlp.max_length = 2_000_000
        except Exception:  # model not installed: the rule layer still works
            _nlp_failed = True
            return []
    keep = {"PER": "NAME", "ORG": "ORG"}
    if os.environ.get("AI_NER_LOC") == "1":
        keep["LOC"] = "PLACE"
    out = []
    for e in _nlp(text).ents:
        kind = keep.get(e.label_)
        v = _clean(e.text)
        words = v.split()
        if not kind or len(v) < 4 or v.lower() in STOP or len(words) < 2 or ID_LIKE.search(v):
            continue  # single words and ids are too often wrong; honorific and signature rules cover single names
        if any(w.lower().strip(".,") in COMMON or w.lower().strip(".,") in STOP for w in words):
            continue
        if not all(re.match(CAP, w) or re.fullmatch(LINK, w) or w in {"&", "e"} for w in words):
            continue
        out.append((kind, v))
    return out


def detect(text: str) -> list[tuple[str, str]]:
    """Return (kind, value) pairs found in `text` (values appear in the text)."""
    t = re.sub(r"<[A-Z]+_\d+>", lambda m: " " * len(m.group()), text)  # tokens are already masked
    found: list[tuple[str, str]] = []
    for m in re.finditer(rf"\b{HONOR}\s+({FULL})", t):
        found.append(("NAME", _clean(m.group(1))))
    for m in re.finditer(rf"({FULL})\s*<[^>@\s]+@", t):
        found.append(("NAME", _clean(m.group(1))))
    for m in re.finditer(rf"(?im)^\s*(?:de|para|cc|bcc|from|to|nome|name|cliente|titular|requerente|assinado por|signed by)\s*:\s*({FULL})", t):
        found.append(("NAME", _clean(m.group(1))))
    for m in re.finditer(rf"(?is){CLOSING}[ ,.!]*\n+\s*({FULL})", t):
        found.append(("NAME", _clean(m.group(1))))
    for m in re.finditer(rf"\b({CAP}(?:\s+(?:&|e|{LINK})?\s*{CAP}){{0,4}}\s*,?\s+(?:Lda|S\.?\s?A|Unipessoal|Limitada|GmbH|Ltd|Inc|SGPS))\b\.?", t):
        found.append(("ORG", _clean(m.group(1))))
    for label, kind in LABELS.items():
        for m in re.finditer(rf"(?i)(?:{label})\b[^\n\d]{{0,25}}?((?=[A-Z0-9 -]*\d)[A-Z0-9][A-Z0-9 -]{{6,14}}[A-Z0-9])", t):
            found.append((kind, m.group(1).strip()))
    for m in re.finditer(r"(?i)(?:data de nascimento|nascid[oa] em|born on|date of birth|dob)\W{0,10}(\d{1,2}[/.-]\d{1,2}[/.-]\d{2,4}|\d{1,2} de \w+ de \d{4}|\d{4}-\d{2}-\d{2})", t):
        found.append(("DOB", m.group(1)))
    names = {v for k, v in found if k == "NAME" and " " in v}  # aliases only for names the context rules found (reliable)
    found += _ner(t)
    for full in names:  # aliases: first name and surname
        parts = [w for w in full.split() if re.match(CAP, w)]
        for w in (parts[0], parts[-1]) if parts else ():
            if len(w) >= 3 and w.lower() not in STOP:
                found.append(("NAME", w))
    seen, out = set(), []
    for k, v in found:
        if v and v.casefold() not in seen and v in text:
            seen.add(v.casefold())
            out.append((k, v))
    return out
