"""تبدیل نام فارسی/برند دارو به نام ژنریک استاندارد (canonical key).

قواعد:
- کلیدهای دیکشنری‌ها انگلیسی می‌مانند (قرارداد داده).
- ورودی کاربر می‌تواند فارسی، فینگلیش یا انگلیسی باشد.
"""

from __future__ import annotations

import json
import re
import unicodedata
from difflib import SequenceMatcher
from functools import lru_cache
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

_AR_TO_FA = {
    "\u064a": "\u06cc",  # ARABIC YEH -> FARSI YEH
    "\u0649": "\u06cc",  # ALEF MAKSURA -> FARSI YEH
    "\u0643": "\u06a9",  # ARABIC KAF -> KEHEH
    "\u0629": "\u0647",  # TEH MARBUTA -> HEH
    "\u0623": "\u0627",
    "\u0625": "\u0627",
    "\u0622": "\u0627",
    "\u0624": "\u0648",
    "\u0626": "\u06cc",
}
# اعراب، تشدید، کشیده، نیم‌فاصله و کاراکترهای کنترلی نامرئی
_STRIP_CHARS = "".join(
    [
        "\u064b", "\u064c", "\u064d", "\u064e", "\u064f", "\u0650",
        "\u0651", "\u0652", "\u0653", "\u0654", "\u0655", "\u0670",
        "\u0640",              # tatweel
        "\u200b", "\u200c", "\u200d", "\u200e", "\u200f", "\ufeff",
    ]
)

FA_DIGITS = "\u06f0\u06f1\u06f2\u06f3\u06f4\u06f5\u06f6\u06f7\u06f8\u06f9"
AR_DIGITS = "\u0660\u0661\u0662\u0663\u0664\u0665\u0666\u0667\u0668\u0669"
_DIGIT_MAP = {ord(c): str(i) for i, c in enumerate(FA_DIGITS)}
_DIGIT_MAP.update({ord(c): str(i) for i, c in enumerate(AR_DIGITS)})


def to_en_digits(text: str) -> str:
    """۱۲۳ -> 123"""
    return str(text).translate(_DIGIT_MAP)


def to_fa_digits(text) -> str:
    """123 -> ۱۲۳ (برای نمایش به کاربر)"""
    out = []
    for ch in str(text):
        out.append(FA_DIGITS[int(ch)] if ch.isdigit() and ch.isascii() else ch)
    return "".join(out)


def normalize_text(raw: str) -> str:
    """یکسان‌سازی متن فارسی/عربی/لاتین برای مقایسه."""
    if raw is None:
        return ""
    s = unicodedata.normalize("NFKC", str(raw))
    s = s.translate(_DIGIT_MAP)
    for a, b in _AR_TO_FA.items():
        s = s.replace(a, b)
    s = s.translate({ord(c): None for c in _STRIP_CHARS})
    s = s.replace("\u2010", "-").replace("\u2011", "-").replace("\u2013", "-")
    s = s.lower()
    s = re.sub(r"[^0-9a-z\u0621-\u06cc\s\-/]+", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


# واحدها و صورت‌های دارویی که باید از نام حذف شوند تا نام خالص بماند
_DOSE_NOISE = [
    r"\b\d+(\.\d+)?\s*(mg|mcg|ug|g|ml|iu|units?|%)\b",
    r"\b\d+(\.\d+)?\s*(\u0645\u06cc\u0644\u06cc\u200c?\u06af\u0631\u0645|\u0645\u06cc\u0644\u06cc\u200c?\u06af\u0631|\u06af\u0631\u0645|\u0645\u06cc\u0644\u06cc\u200c?\u0644\u06cc\u062a\u0631|\u0648\u0627\u062d\u062f)\b",
    r"\b(tab|tabs?|tablet|cap|caps?|capsule|syrup|susp|suspension|amp|ampoule|inj|injection|drop|drops|spray|cream|ointment|gel|patch|sachet|effervescent|er|xr|sr|cr|la|hfa|md|odt)\b",
    r"\b(\u0642\u0631\u0635|\u0642\u0631\u0635\u0647\u0627|\u06a9\u067e\u0633\u0648\u0644|\u0634\u0631\u0628\u062a|\u0627\u0645\u067e\u0648\u0644|\u0622\u0645\u067e\u0648\u0644|\u0642\u0637\u0631\u0647|\u0627\u0633\u067e\u0631\u06cc|\u067e\u0645\u0627\u062f|\u06a9\u0631\u0645|\u0698\u0644|\u0633\u0627\u0634\u0647|\u062c\u0648\u0634\u0627\u0646|\u0648\u06cc\u0627\u0644)\b",
]


def strip_dose_noise(text: str) -> str:
    s = normalize_text(text)
    for pat in _DOSE_NOISE:
        s = re.sub(pat, " ", s)
    return re.sub(r"\s+", " ", s).strip()


@lru_cache(maxsize=1)
def load_drugs() -> dict:
    with open(DATA_DIR / "drugs.json", encoding="utf-8") as f:
        return json.load(f)


@lru_cache(maxsize=1)
def _alias_index() -> dict:
    """map: normalized alias -> canonical generic key"""
    idx = {}
    for key, rec in load_drugs().items():
        aliases = [key, rec.get("fa", ""), rec.get("en", "")]
        aliases += rec.get("aliases", [])
        aliases += rec.get("brands_fa", [])
        for a in aliases:
            n = normalize_text(a)
            if n:
                idx.setdefault(n, key)
                idx.setdefault(n.replace(" ", ""), key)
    return idx


def _similar(a: str, b: str) -> float:
    return SequenceMatcher(None, a, b).ratio()


def resolve_drug(raw_name: str, cutoff: float = 0.86):
    """نام خام -> (canonical_key | None, confidence, cleaned_name)

    مرحله‌ای: تطابق دقیق، بدون فاصله، زیررشته، سپس شباهت فازی.
    """
    cleaned = strip_dose_noise(raw_name)
    if not cleaned:
        return None, 0.0, ""
    idx = _alias_index()

    if cleaned in idx:
        return idx[cleaned], 1.0, cleaned
    squashed = cleaned.replace(" ", "")
    if squashed in idx:
        return idx[squashed], 1.0, cleaned

    # زیررشته: «قرص متفورمین ۵۰۰ صبح» -> metformin
    best_sub = None
    for alias, key in idx.items():
        if len(alias) >= 4 and alias in cleaned:
            if best_sub is None or len(alias) > len(best_sub[0]):
                best_sub = (alias, key)
    if best_sub:
        return best_sub[1], 0.95, cleaned

    # پیشوند: «ciproflox» -> ciprofloxacin
    best_pre = None
    for alias, key in idx.items():
        if len(cleaned) >= 5 and alias.startswith(cleaned):
            if best_pre is None or len(alias) < len(best_pre[0]):
                best_pre = (alias, key)
    if best_pre:
        return best_pre[1], 0.92, cleaned

    # فازی روی توکن‌ها و کل رشته
    best = (None, 0.0)
    tokens = [t for t in cleaned.split() if len(t) >= 4] + [cleaned]
    for alias, key in idx.items():
        if len(alias) < 4:
            continue
        for t in tokens:
            r = _similar(t, alias)
            if r > best[1]:
                best = (key, r)
    if best[1] >= cutoff:
        return best[0], round(best[1], 3), cleaned
    return None, round(best[1], 3), cleaned


def parse_drug_lines(text: str) -> list:
    """متن چندخطی کاربر -> لیست دیکشنری {raw, key, confidence, cleaned}"""
    items = []
    seen = set()
    raw_lines = re.split(r"[\n\r\u060c;\+]+|(?<=\S)\s*,\s*", str(text or ""))
    for line in raw_lines:
        line = line.strip(" \t-\u2022*\u2013.")
        if not line:
            continue
        key, conf, cleaned = resolve_drug(line)
        dedupe_on = key or cleaned
        if dedupe_on in seen:
            continue
        seen.add(dedupe_on)
        items.append({"raw": line, "key": key, "confidence": conf, "cleaned": cleaned})
    return items
