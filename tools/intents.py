"""Group train questions into rough intent clusters (dev analysis): python -m tools.intents > analysis/intents.txt"""
import collections
import json
import re
import sys

from src.normalize import norm_q


def mask(q):
    q = re.sub(r"\b\d{1,2}/\d{1,2}/\d{4}\b", "D", q)
    q = re.sub(r"\b\d{1,2}[/-]\d{4}\b|\b\d{4}-\d{2}\b", "M", q)
    q = re.sub(r"\b20\d\d\b", "Y", q)
    return re.sub(r"\b\d[\d.,]*\b", "N", q)


def cluster(items, thr=0.6):
    reps = []  # (token set, members)
    for it in items:
        toks = set(it["m"].split())
        best = max(reps, key=lambda r: len(toks & r[0]) / len(toks | r[0]), default=None)
        if best and len(toks & best[0]) / len(toks | best[0]) >= thr:
            best[1].append(it)
        else:
            reps.append((toks, [it]))
    return sorted((r[1] for r in reps), key=len, reverse=True)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    ans = {d["id"]: d for d in map(json.loads, open("train/answers.jsonl", encoding="utf-8"))}
    items = []
    for d in map(json.loads, open("train/questions.jsonl", encoding="utf-8")):
        items.append({**d, "m": mask(norm_q(d["question"])), "type": ans[d["id"]]["type"]})
    groups = cluster(sorted(items, key=lambda x: len(x["m"])))
    print(f"{len(items)} questions -> {len(groups)} clusters\n")
    for g in groups:
        types = collections.Counter(x["type"] for x in g).most_common()
        print(f"[{len(g)}] {types}  e.g. {g[0]['m']!r}")
        for x in g[:3]:
            print("     ", x["question"])

# Coarse families, first match wins: used only to rank what to build first.
FAMILIES = [
    ("price_change_effect", r"tang gia|len gia"),
    ("cancel_rate", r"huy.*(%|ti le|phan tram)|(%|ti le|phan tram).*huy"),
    ("cancel_count", r"huy"),
    ("debt", r"\bno\b|thieu tien|mua chiu"),
    ("import", r"nhap"),
    ("inventory_batch", r"ton kho|trong kho|cuoi ngay.*con may|het han|\blo\b.*han"),
    ("profit", r"\bloi\b|\blai\b|loi nhuan"),
    ("unit_price_on_day", r"gia ban|don gia"),
    ("best_day_or_month", r"ngay nao|thang nao"),
    ("pharma_rx_ingredient", r"hoat chat|ke don|bac si"),
    ("delivery", r"giao hang|dot"),
    ("ranking_topk", r"\btop\b|liet ke|nhat|best"),
    ("group_share_or_sales", r"\bnhom\b|ti trong"),
    ("shift", r"ca sang|ca chieu"),
    ("customer_counts", r"khach"),
    ("avg_order_value", r"trung binh|binh quan"),
    ("order_count", r"\bdon\b|bill"),
    ("revenue_or_units", r"doanh thu|revenue|tien|ban ra|ban duoc"),
]


def family(m):
    return next((name for name, rx in FAMILIES if re.search(rx, m)), "other")


if __name__ == "__main__":
    fam = collections.defaultdict(list)
    for x in items:
        fam[family(x["m"])].append(x)
    print("\n\n=== families ===")
    for name, xs in sorted(fam.items(), key=lambda kv: -len(kv[1])):
        cmp = sum(bool(re.search(r"%|so voi|tang hay giam|hon hay kem|chenh", x["m"])) for x in xs)
        print(f"{name:24s} {len(xs):5d}  compare={cmp:4d}  {collections.Counter(x['type'] for x in xs).most_common()}")
    for x in fam["other"][:15]:
        print("  other:", x["question"])
