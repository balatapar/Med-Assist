"""موتور بررسی تداخل دارو-دارو و دارو-غذا."""

from __future__ import annotations

import json
from functools import lru_cache
from itertools import combinations
from pathlib import Path

from .normalize import load_drugs

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

SEVERITY_ORDER = {"danger": 3, "moderate": 2, "caution": 1}
SEVERITY_FA = {
    "danger": "خطرناک",
    "moderate": "متوسط",
    "caution": "نیازمند احتیاط",
}
SEVERITY_ICON = {"danger": "🛑", "moderate": "⚠️", "caution": "ℹ️"}


@lru_cache(maxsize=1)
def _pair_index() -> dict:
    with open(DATA_DIR / "interactions.json", encoding="utf-8") as f:
        pairs = json.load(f)["pairs"]
    idx = {}
    for p in pairs:
        idx[tuple(sorted((p["a"], p["b"])))] = p
    return idx


@lru_cache(maxsize=1)
def load_foods() -> dict:
    with open(DATA_DIR / "food_interactions.json", encoding="utf-8") as f:
        return json.load(f)


def fa_name(key: str) -> str:
    rec = load_drugs().get(key)
    return rec["fa"] if rec else key


def check_pairs(keys: list) -> list:
    """جفت‌های تداخل‌دار بین داروهای کاربر، مرتب از خطرناک به کم‌خطر."""
    found = []
    idx = _pair_index()
    uniq = list(dict.fromkeys(k for k in keys if k))
    for a, b in combinations(uniq, 2):
        hit = idx.get(tuple(sorted((a, b))))
        if hit:
            found.append(
                {
                    "a": a,
                    "b": b,
                    "a_fa": fa_name(a),
                    "b_fa": fa_name(b),
                    "severity": hit["severity"],
                    "severity_fa": SEVERITY_FA[hit["severity"]],
                    "icon": SEVERITY_ICON[hit["severity"]],
                    "why_fa": hit["why_fa"],
                    "do_fa": hit["do_fa"],
                    "symptoms_fa": hit.get("symptoms_fa", ""),
                }
            )
    found.sort(key=lambda x: (-SEVERITY_ORDER[x["severity"]], x["a_fa"]))
    return found


def check_duplicate_class(keys: list) -> list:
    """هشدار داروهای هم‌خانواده (خطر دوز مضاعف)."""
    drugs = load_drugs()
    by_class = {}
    for k in dict.fromkeys(keys):
        rec = drugs.get(k)
        if not rec:
            continue
        by_class.setdefault(rec["class"], []).append(k)
    out = []
    ignore = {"supplement", "inhaler"}
    for cls, members in by_class.items():
        if len(members) > 1 and cls not in ignore:
            out.append(
                {
                    "class": cls,
                    "members": members,
                    "members_fa": [fa_name(m) for m in members],
                }
            )
    return out


def check_foods(keys: list) -> list:
    """گروه‌های غذایی مرتبط با داروهای کاربر."""
    keyset = {k for k in keys if k}
    out = []
    for gid, g in load_foods().items():
        hits = [k for k in g["drugs"] if k in keyset]
        if hits:
            out.append(
                {
                    "id": gid,
                    "food_fa": g["fa"],
                    "severity": g["severity"],
                    "severity_fa": SEVERITY_FA[g["severity"]],
                    "icon": SEVERITY_ICON[g["severity"]],
                    "why_fa": g["why_fa"],
                    "do_fa": g["do_fa"],
                    "drugs_fa": [fa_name(k) for k in hits],
                }
            )
    out.sort(key=lambda x: -SEVERITY_ORDER[x["severity"]])
    return out


RED_FLAGS_FA = [
    "تنگی نفس، ورم لب و زبان یا کهیر گسترده (واکنش حساسیتی) — اورژانس",
    "درد قفسه سینه، تپش قلب شدید یا غش کردن",
    "مدفوع سیاه و قیری، استفراغ خونی یا ادرار قرمز",
    "زردی چشم و پوست، ادرار پررنگ همراه با تهوع مداوم",
    "بثورات پوستی جدید همراه تب و تاول، خصوصاً با لاموتریژین یا آنتی‌بیوتیک",
    "درد و ضعف شدید عضلانی با ادرار قهوه‌ای (خصوصاً با استاتین‌ها)",
    "گیجی، حرف زدن نامفهوم، خواب‌آلودگی غیرعادی یا تنفس کند",
    "تشنج، لرزش شدید همراه تب و تعریق",
    "کاهش شدید حجم ادرار یا ورم سریع پاها",
]


def analyze(keys: list) -> dict:
    pairs = check_pairs(keys)
    return {
        "pairs": pairs,
        "duplicates": check_duplicate_class(keys),
        "foods": check_foods(keys),
        "danger_count": sum(1 for p in pairs if p["severity"] == "danger"),
        "moderate_count": sum(1 for p in pairs if p["severity"] == "moderate"),
        "caution_count": sum(1 for p in pairs if p["severity"] == "caution"),
        "red_flags": RED_FLAGS_FA,
    }
