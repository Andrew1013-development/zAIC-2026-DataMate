"""Compact text profile of a business's tables; also the schema context later given to the LLM.

python -m src.profile  -> writes analysis/profiles/<split>__<business>.txt for every business.
"""
import sys
from pathlib import Path

from src.load import load_business


def profile(tables, samples=4):
    out = []
    for name, df in tables.items():
        out.append(f"## {name}  rows={len(df)}")
        for c in df.columns:
            vals = df[c][df[c] != ""]
            uniq = vals.unique()
            ex = " | ".join(v[:40] for v in uniq[:samples])
            out.append(f"- {c} (distinct={len(uniq)}, empty={len(df) - len(vals)}): {ex}")
    return "\n".join(out)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    dest = Path("analysis/profiles")
    dest.mkdir(parents=True, exist_ok=True)
    for split in ("train", "public_test"):
        for biz in sorted(Path(split, "data").iterdir()):
            text = (biz / "README.md").read_text(encoding="utf-8") + "\n\n" + profile(load_business(biz))
            (dest / f"{split}__{biz.name}.txt").write_text(text, encoding="utf-8")
            print(split, biz.name, "done", flush=True)
