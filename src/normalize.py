"""Question normalizer: accent-free lowercase ASCII, Telex typos decoded, teencode expanded.

Used for intent matching only; entity names are matched against the data separately (with diacritics).
"""
import re
import unicodedata

_TELEX = re.compile(r"dd|aw|aa|ee|oo|ow|uw|w")

# teencode / abbreviations seen in train questions -> canonical accent-free words
_ABBR = {
    "dthu": "doanh thu", "dt": "doanh thu", "bnhiu": "bao nhieu", "bnhieu": "bao nhieu", "bn": "bao nhieu",
    "nhiu": "nhieu", "bao nhiu": "bao nhieu", "hnay": "hom nay", "hqua": "hom qua", "bua qua": "hom qua",
    "bua nay": "hom nay", "dc": "duoc", "ko": "khong", "hok": "khong", "sp": "san pham",
    "trc": "truoc", "nhut": "nhat", "ni": "nay", "chu": "nay", "th": "thang", "t": "thang",
    "kh": "khach hang", "vs": "voi", "sl": "so luong", "tb": "trung binh", "nv": "nhan vien",
}
_FILLER = {"z", "vay", "ha", "a", "nhi", "nhe", "ta", "the", "do", "ah", "nha", "oi", "ne", "e", "thanks", "giup", "gium", "dum"}


def strip_accents(s):
    s = unicodedata.normalize("NFD", s.replace("đ", "d").replace("Đ", "D"))
    return "".join(ch for ch in s if unicodedata.category(ch) != "Mn")


def _untelex(w):
    """'dduwowcj' -> 'duoc', 'toongr' -> 'tong', 'naof' -> 'nao' (unconverted Telex typing)."""
    if not w.isalpha() or len(w) < 3:
        return w
    if w[-1] in "sfrxj" and w[-2] not in "sfrxj":  # Vietnamese words never end in a tone key
        w = w[:-1]
    return _TELEX.sub(lambda m: m.group(0)[0] if m.group(0) != "w" else "", w)


def norm_q(text):
    s = strip_accents(text.lower())
    s = re.sub(r"(?<=[a-z])(?=\d)|(?<=\d)(?=[a-z])", " ", s)  # th7 -> th 7, 5tr -> 5 tr
    s = re.sub(r"[^a-z0-9/%.,\-\s]", " ", s)
    words = [_untelex(w) for w in s.split()]
    s = " " + " ".join(words) + " "
    for k in sorted(_ABBR, key=len, reverse=True):
        s = s.replace(f" {k} ", f" {_ABBR[k]} ")
    return " ".join(w for w in s.split() if w not in _FILLER)


if __name__ == "__main__":
    assert norm_q("bữa qua toongr cộng bán dduwowcj bnhiu lon") == "hom qua tong cong ban duoc bao nhieu lon", norm_q("bữa qua toongr cộng bán dduwowcj bnhiu lon")
    assert norm_q("dthu ngày naof cao nhất trong tháng 7 nawm 2026 z") == "doanh thu ngay nao cao nhat trong thang 7 nam 2026"
    assert norm_q("Th7/2026 mat hang nao ban chay nhat the?") == "thang 7/2026 mat hang nao ban chay nhat"
    print("ok")
