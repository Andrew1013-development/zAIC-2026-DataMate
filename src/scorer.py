"""Local copy of the DataMate scoring rules (problem statement/evaluation.md).

Usage: python -m src.scorer <submission.jsonl> <answers.jsonl>
"""
import json
import re
import sys
import unicodedata


def norm(s):
    s = unicodedata.normalize("NFC", str(s)).lower()
    s = re.sub(r"[^\w\s]|_", " ", s)  # \w keeps letters+digits (incl. Vietnamese); "_" is not a letter
    return " ".join(s.split())


def is_num(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool)


def num_eq(p, r):
    return is_num(p) and abs(p - r) < 1e-6


def name_eq(p, r, aliases=()):
    return isinstance(p, str) and norm(p) in {norm(r), *map(norm, aliases)}


def cell_eq(p, r, aliases=()):
    return num_eq(p, r) if is_num(r) else name_eq(p, r, aliases)


def table_eq(p, r, row_aliases):
    if not (isinstance(p, dict) and isinstance(p.get("columns"), list) and isinstance(p.get("rows"), list)):
        return False
    pc, rc = [norm(c) for c in p["columns"]], [norm(c) for c in r["columns"]]
    if len(pc) != len(rc):
        return False
    order = [pc.index(c) for c in rc] if sorted(pc) == sorted(rc) else list(range(len(rc)))
    prows = [[row[i] for i in order] for row in p["rows"] if isinstance(row, list) and len(row) == len(rc)]
    if len(prows) != len(p["rows"]) or len(prows) != len(r["rows"]):
        return False
    unused = list(range(len(prows)))
    for k, rrow in enumerate(r["rows"]):
        al = row_aliases[k] if k < len(row_aliases) else []
        hit = next((j for j in unused if all(cell_eq(prows[j][c], rrow[c], al if c == 0 else ()) for c in range(len(rc)))), None)
        if hit is None:
            return False
        unused.remove(hit)
    return True


def score(pred, ref):
    """+1 correct, 0 abstain/missing, -1 wrong."""
    if pred is None or pred.get("type") in (None, "abstain"):
        return 0
    t = pred["type"]
    if t != ref["type"]:
        return -1
    if t == "unanswerable":
        return 1
    p, r, al = pred.get("answer"), ref["answer"], ref.get("alias") or []
    if t == "number":
        ok = num_eq(p, r)
    elif t == "percent":
        ok = is_num(p) and round(p, 2) == round(r, 2)
    elif t == "string":
        ok = name_eq(p, r, al)
    elif t in ("date", "boolean"):
        ok = type(p) is type(r) and p == r
    elif t == "list":
        ok = isinstance(p, list) and len(p) == len(r) and all(
            cell_eq(x, y, al[i] if i < len(al) else ()) for i, (x, y) in enumerate(zip(p, r)))
    elif t == "table":
        ok = table_eq(p, r, al)
    else:
        ok = False
    return 1 if ok else -1


def read_jsonl(path):
    with open(path, encoding="utf-8") as f:
        return {d["id"]: d for d in map(json.loads, f) if d}


def evaluate(preds, refs):
    s = [score(preds.get(i), r) for i, r in refs.items()]
    n = len(s)
    return {"PA": sum(s) / n, "correct": s.count(1), "wrong": s.count(-1), "abstain": s.count(0), "n": n}


def _selfcheck():
    ref = {"type": "string", "answer": "Sting dâu 330ml", "alias": ["SP0042"]}
    assert score({"type": "string", "answer": "STING DÂU, 330ml!"}, ref) == 1
    assert score({"type": "string", "answer": "sp0042"}, ref) == 1
    assert score({"type": "string", "answer": "Sting dầu 330ml"}, ref) == -1  # diacritics matter
    assert score({"type": "number", "answer": "4820000"}, {"type": "number", "answer": 4820000}) == -1
    assert score({"type": "percent", "answer": -12.449999}, {"type": "percent", "answer": -12.45}) == 1
    assert score({"type": "boolean", "answer": 1}, {"type": "boolean", "answer": True}) == -1
    assert score({"type": "list", "answer": ["b", "a"]}, {"type": "list", "answer": ["a", "b"]}) == -1
    t = {"type": "table", "answer": {"columns": ["khach_hang", "so_tien_no"], "rows": [["An", 5], ["Bình", 3]]},
         "alias": [["KH01"], ["KH02"]]}
    assert score({"type": "table", "answer": {"columns": ["so_tien_no", "khach_hang"], "rows": [[3, "kh02"], [5, "An"]]}}, t) == 1
    assert score({"type": "table", "answer": {"columns": ["a", "b"], "rows": [["An", 5], ["Bình", 4]]}}, t) == -1
    assert score({"type": "unanswerable"}, {"type": "number", "answer": 1}) == -1
    assert score({"type": "abstain"}, {"type": "number", "answer": 1}) == 0


if __name__ == "__main__":
    _selfcheck()
    if len(sys.argv) == 3:
        print(json.dumps(evaluate(read_jsonl(sys.argv[1]), read_jsonl(sys.argv[2]))))
