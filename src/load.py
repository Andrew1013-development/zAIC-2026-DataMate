"""Read every table of one business folder into string DataFrames, keyed "file" or "file::sheet".

Values stay raw strings (money like "19tr990", Excel serial dates, ...); parsing happens later.
"""
import sqlite3
from pathlib import Path

import pandas as pd


def _promote_header(raw):
    """Use the first row with the most filled cells (within the top 20) as header; drops title/blank rows above it."""
    raw = raw.fillna("").astype(str).apply(lambda c: c.str.strip())
    filled = (raw.head(20) != "").sum(axis=1)
    if filled.empty:
        return raw
    h = int(filled.idxmax())
    cols = [c or f"col{i}" for i, c in enumerate(raw.iloc[h])]
    df = raw.iloc[h + 1:].set_axis(cols, axis=1)
    df = df.loc[:, [not (c.startswith("col") and (df[c] == "").all()) for c in cols]]  # drop unnamed empty columns
    return df[(df != "").any(axis=1)].reset_index(drop=True)


def load_business(folder):
    tables = {}
    for p in sorted(Path(folder).iterdir()):
        ext = p.suffix.lower()
        if ext == ".csv":
            raw = pd.read_csv(p, encoding="utf-8-sig", dtype=str, keep_default_na=False, header=None)
            tables[p.name] = _promote_header(raw)
        elif ext in (".xlsx", ".xls"):
            for sheet, raw in pd.read_excel(p, sheet_name=None, engine="calamine", dtype=str, header=None).items():
                tables[f"{p.name}::{sheet}"] = _promote_header(raw)
        elif ext in (".sqlite", ".db"):
            with sqlite3.connect(f"file:{p}?mode=ro", uri=True) as con:  # /data is mounted read-only
                names = [r[0] for r in con.execute("select name from sqlite_master where type='table'")]
                for t in names:
                    tables[f"{p.name}::{t}"] = pd.read_sql_query(f'select * from "{t}"', con).fillna("").astype(str)
    return tables


if __name__ == "__main__":
    raw = pd.DataFrame([["TITLE", "", ""], ["", "", ""], ["a", "b", ""], ["1", "2", ""], ["", "", ""]])
    df = _promote_header(raw)
    assert list(df.columns) == ["a", "b"] and df.values.tolist() == [["1", "2"]], df
    print("ok")
