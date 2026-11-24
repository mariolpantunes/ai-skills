#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# ///
"""Write a Power BI Project (.pbip) from a clean CSV: a semantic model (TMDL) with one table
and three measures, and a one-page report (PBIR) with a card and a bar chart.

  make_pbip.py orders_clean.csv --out ./powerbi --name Orders [--csv-path C:\\data\\orders_clean.csv]

Open <out>\\<name>.pbip in Power BI Desktop (Windows), then click Refresh: a project has no data cache, so it opens empty.
The CSV path is a model parameter (CsvPath).
Needs a header row, one decimal point, ISO dates (2026-07-14).
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
import uuid
from pathlib import Path

S = "https://developer.microsoft.com/json-schemas/fabric/item"


def sniff(values: list[str]) -> str:
    v = [x for x in values if x != ""]
    if v and all(re.fullmatch(r"-?\d+", x) for x in v):
        return "int64"
    if v and all(re.fullmatch(r"-?\d+\.\d+", x) for x in v):
        return "double"
    if v and all(re.fullmatch(r"\d{4}-\d{2}-\d{2}", x) for x in v):
        return "dateTime"
    return "string"


def q(name: str) -> str:  # TMDL quoting
    return f"'{name}'" if re.search(r"[.=:' ]", name) else name


def write(p: Path, text: str) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8", newline="\n")


def wjson(p: Path, obj: dict) -> None:
    write(p, json.dumps(obj, indent=2) + "\n")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("csv", type=Path)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--name", default="Report")
    ap.add_argument("--table", default=None, help="table name (default: the file name)")
    ap.add_argument("--csv-path", default=None, help="path of the CSV on the Windows PC (default: the given path)")
    a = ap.parse_args()

    with a.csv.open(encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        print("empty CSV", file=sys.stderr)
        return 1
    cols = list(rows[0])
    kind = {c: sniff([r[c] for r in rows]) for c in cols}
    amount = next((c for c in cols if kind[c] == "double"), None)
    key = next((c for c in cols if kind[c] == "int64"), None)
    cat = next((c for c in cols if kind[c] == "string"), None)
    if not amount or not cat:
        print("need at least one decimal column and one text column", file=sys.stderr)
        return 1
    table = a.table or re.sub(r"\W+", "_", a.csv.stem)
    path = a.csv_path or str(a.csv.resolve())
    n, root = a.name, a.out
    sm, rp = root / f"{n}.SemanticModel", root / f"{n}.Report"

    # ---- project and semantic model
    wjson(root / f"{n}.pbip", {"version": "1.0", "artifacts": [{"report": {"path": f"{n}.Report"}}],
                               "settings": {"enableAutoRecovery": True}})
    write(root / ".gitignore", "**/.pbi/localSettings.json\n**/.pbi/cache.abf\n")
    wjson(sm / "definition.pbism", {"$schema": f"{S}/semanticModel/definitionProperties/1.0.0/schema.json", "version": "4.0", "settings": {}})
    d = sm / "definition"
    write(d / "database.tmdl", "database\n\tcompatibilityLevel: 1567\n")
    write(d / "model.tmdl", f"model Model\n\tculture: en-US\n\tdefaultPowerBIDataSourceVersion: powerBI_V3\n\nref table {q(table)}\n")
    esc = path.replace('"', '""')
    write(d / "expressions.tmdl", f'expression CsvPath = "{esc}" meta [IsParameterQuery=true, Type="Text", IsParameterQueryRequired=true]\n')
    mtype = {"int64": "Int64.Type", "double": "type number", "dateTime": "type date", "string": "type text"}
    typed = ", ".join(f'{{"{c}", {mtype[kind[c]]}}}' for c in cols)
    t = [f"table {q(table)}", f"\tlineageTag: {uuid.uuid4()}", ""]
    if amount:
        t += [f"\tmeasure 'Total EUR' = SUM({q(table)}[{amount}])", "\t\tformatString: #,##0.00", f"\t\tlineageTag: {uuid.uuid4()}", ""]
    if key:
        t += [f"\tmeasure 'Order count' = DISTINCTCOUNT({q(table)}[{key}])", "\t\tformatString: 0", f"\t\tlineageTag: {uuid.uuid4()}", ""]
        t += [f"\tmeasure 'Average order' = DIVIDE([Total EUR], [Order count])", "\t\tformatString: #,##0.00", f"\t\tlineageTag: {uuid.uuid4()}", ""]
    for c in cols:
        t += [f"\tcolumn {q(c)}", f"\t\tdataType: {kind[c]}", f"\t\tlineageTag: {uuid.uuid4()}",
              f"\t\tsummarizeBy: {'sum' if c == amount else 'none'}", f"\t\tsourceColumn: {c}", ""]
        if kind[c] == "dateTime":
            t.insert(-1, "\t\tformatString: yyyy-mm-dd")
    t += [f"\tpartition {q(table)} = m", "\t\tmode: import", "\t\tsource =", "\t\t\t\tlet",
          '\t\t\t\t\tSource = Csv.Document(File.Contents(CsvPath), [Delimiter=",", Columns=' + str(len(cols)) + ", Encoding=65001, QuoteStyle=QuoteStyle.Csv]),",
          "\t\t\t\t\tHeaders = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),",
          f'\t\t\t\t\tTyped = Table.TransformColumnTypes(Headers, {{{typed}}}, "en-US")', "\t\t\t\tin", "\t\t\t\t\tTyped", ""]
    write(d / "tables" / f"{table}.tmdl", "\n".join(t))

    # ---- report (PBIR): one page, a card and a bar chart
    wjson(rp / "definition.pbir", {"$schema": f"{S}/report/definitionProperties/2.0.0/schema.json", "version": "4.0",
                                   "datasetReference": {"byPath": {"path": f"../{n}.SemanticModel"}}})
    rd = rp / "definition"
    wjson(rd / "report.json", {"$schema": f"{S}/report/definition/report/3.0.0/schema.json",
                               "themeCollection": {}})
    wjson(rd / "version.json", {"$schema": f"{S}/report/definition/versionMetadata/1.0.0/schema.json", "version": "2.0.0"})
    page = "page1"
    wjson(rd / "pages" / "pages.json", {"$schema": f"{S}/report/definition/pagesMetadata/1.0.0/schema.json", "pageOrder": [page], "activePageName": page})
    wjson(rd / "pages" / page / "page.json", {"$schema": f"{S}/report/definition/page/2.0.0/schema.json", "name": page,
                                              "displayName": "Overview", "displayOption": "FitToPage", "height": 720, "width": 1280})

    def measure(name: str) -> dict:
        return {"field": {"Measure": {"Expression": {"SourceRef": {"Entity": table}}, "Property": name}}, "queryRef": f"{table}.{name}", "nativeQueryRef": name}

    def column(name: str) -> dict:
        return {"field": {"Column": {"Expression": {"SourceRef": {"Entity": table}}, "Property": name}}, "queryRef": f"{table}.{name}", "nativeQueryRef": name}

    def visual(name: str, x: int, y: int, w: int, h: int, vtype: str, state: dict) -> None:
        wjson(rd / "pages" / page / "visuals" / name / "visual.json", {
            "$schema": f"{S}/report/definition/visualContainer/2.0.0/schema.json", "name": name,
            "position": {"x": x, "y": y, "z": 0, "height": h, "width": w},
            "visual": {"visualType": vtype, "query": {"queryState": state}, "drillFilterOtherVisuals": True}})

    visual("card_total", 40, 30, 300, 130, "card", {"Values": {"projections": [measure("Total EUR")]}})
    visual("bar_by_category", 40, 190, 700, 460, "clusteredBarChart",
           {"Category": {"projections": [column(cat)]}, "Y": {"projections": [measure("Total EUR")]}})
    print(f"OK {root}\\{n}.pbip: table {table} ({len(rows)} rows), measures Total EUR / Order count / Average order, 2 visuals; CsvPath = {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
