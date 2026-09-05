"""ساخت جدول زمانی مصرف از داروها + دستور پزشک."""

from __future__ import annotations

import re
from datetime import datetime, timedelta

from .interactions import fa_name
from .normalize import load_drugs, normalize_text, to_en_digits, to_fa_digits

# ساعت پیش‌فرض هر نوبت (قابل تغییر از رابط کاربری)
DEFAULT_CLOCK = {
    "morning": "08:00",
    "noon": "13:30",
    "evening": "18:00",
    "night": "20:30",
    "bedtime": "22:30",
    "any": "12:00",
}
SLOT_FA = {
    "morning": "صبح",
    "noon": "ظهر",
    "evening": "عصر",
    "night": "شب",
    "bedtime": "قبل خواب",
    "any": "هر زمان",
}
SLOT_ORDER = ["morning", "noon", "evening", "night", "bedtime", "any"]

FOOD_FA = {
    "empty": "ناشتا (معده خالی)",
    "before": "۳۰ دقیقه قبل غذا",
    "with": "همراه غذا",
    "after": "بعد از غذا",
    "any": "با یا بدون غذا",
}

# چند بار در روز -> کدام نوبت‌ها
FREQ_SLOTS = {
    1: ["morning"],
    2: ["morning", "night"],
    3: ["morning", "noon", "night"],
    4: ["morning", "noon", "evening", "bedtime"],
}

_FA_WORD_NUM = {
    "یک": 1, "یکبار": 1, "روزی یک": 1,
    "دو": 2, "دوبار": 2,
    "سه": 3, "سه‌بار": 3, "سه بار": 3,
    "چهار": 4, "چهاربار": 4,
}


def parse_doctor_order(order_text: str) -> dict:
    """دستور پزشک به فارسی/انگلیسی -> اصلاح‌کننده‌های زمان و غذا.

    مثال‌ها: «روزی ۳ بار بعد غذا»، «هر ۸ ساعت»، «شب‌ها ناشتا»، «BD»، «q12h»
    """
    t = normalize_text(to_en_digits(order_text or ""))
    out = {"freq": None, "slots": [], "food": None, "every_hours": None, "raw": order_text or ""}
    if not t:
        return out

    m = re.search(r"(?:هر|every|q)\s*(\d+)\s*(?:ساعت|h|hr|hours?)", t)
    if m:
        h = int(m.group(1))
        out["every_hours"] = h
        if h >= 1:
            out["freq"] = max(1, min(4, round(24 / h))) if h <= 24 else 1

    m = re.search(r"(\d+)\s*(?:بار|times?|x)\b", t)
    if m:
        out["freq"] = max(1, min(4, int(m.group(1))))
    else:
        for w, n in _FA_WORD_NUM.items():
            if f"روزی {w}" in t or f"{w} بار" in t:
                out["freq"] = n
                break

    for pat, n in [(r"\bod\b|\bdaily\b|\bqd\b", 1), (r"\bbd\b|\bbid\b", 2),
                   (r"\btds\b|\btid\b", 3), (r"\bqds\b|\bqid\b", 4)]:
        if re.search(pat, t):
            out["freq"] = n
            break

    if re.search(r"ناشتا|معده خالی|empty", t):
        out["food"] = "empty"
    elif re.search(r"قبل\s*(از)?\s*(غذا|صبحانه|ناهار|شام)|before (meal|food)|ac\b", t):
        out["food"] = "before"
    elif re.search(r"بعد\s*(از)?\s*(غذا|صبحانه|ناهار|شام)|after (meal|food)|pc\b", t):
        out["food"] = "after"
    elif re.search(r"همراه\s*(با)?\s*غذا|با غذا|with (meal|food)", t):
        out["food"] = "with"

    for slot, words in [
        ("morning", r"صبح|صبحانه|morning|am\b"),
        ("noon", r"ظهر|ناهار|noon|midday"),
        ("evening", r"عصر|عصرها|afternoon|evening"),
        ("night", r"شب|شام|night|pm\b"),
        ("bedtime", r"قبل خواب|هنگام خواب|موقع خواب|bedtime|nocte|hs\b"),
    ]:
        if re.search(words, t):
            out["slots"].append(slot)
    return out


# داروهایی که قاعده غذایی‌شان حیاتی است و دستور کلی نباید بازنویسی‌اش کند
STRICT_FOOD_CLASSES = {"thyroid", "bisphosphonate", "ppi", "anti-tb"}


def _is_strict_food(rec: dict) -> bool:
    return rec["food"] == "empty" or rec["class"] in STRICT_FOOD_CLASSES


def build_schedule(items: list, order_text: str = "", clock: dict = None) -> list:
    """items: خروجی parse_drug_lines (هر آیتم می‌تواند کلید order خودش را داشته باشد).

    order_text دستور کلی است و فقط روی داروهایی اعمال می‌شود که دستور اختصاصی ندارند.
    قاعده غذایی داروهای حساس (ناشتا، تیروئید، محافظ معده، آلندرونات) هرگز با
    دستور کلی بازنویسی نمی‌شود؛ به‌جایش یک هشدار در ردیف ثبت می‌شود.
    """
    clock = {**DEFAULT_CLOCK, **(clock or {})}
    global_order = parse_doctor_order(order_text)
    drugs = load_drugs()
    rows = []
    for it in items:
        key = it.get("key")
        rec = drugs.get(key) if key else None
        name_fa = rec["fa"] if rec else (it.get("raw") or it.get("cleaned") or "—")

        own_text = (it.get("order") or "").strip()
        order = parse_doctor_order(own_text) if own_text else global_order
        is_own = bool(own_text)

        if rec:
            slots = list(rec["timing"])
            food = rec["food"]
            note = rec["note_fa"]
            strict = _is_strict_food(rec)
        else:
            slots, food, note, strict = ["morning"], "any", "این دارو در بانک اطلاعاتی نبود؛ طبق نسخه پزشک عمل کنید", False

        conflict = ""
        # زمان‌بندی: دستور پزشک مقدم است
        if order["slots"]:
            slots = order["slots"]
        elif order["freq"]:
            slots = FREQ_SLOTS.get(order["freq"], slots)

        # غذا: دستور اختصاصی همیشه، دستور کلی فقط اگر دارو حساس نباشد
        if order["food"]:
            if is_own or not strict:
                food = order["food"]
            else:
                conflict = (
                    f"دستور کلی «{FOOD_FA[order['food']]}» برای این دارو اعمال نشد؛ "
                    f"{name_fa} باید {FOOD_FA[food]} خورده شود. اگر پزشک خلاف این گفته، "
                    "حرف پزشک را اجرا کنید."
                )

        for slot in slots:
            rows.append(
                {
                    "key": key,
                    "name_fa": name_fa,
                    "raw": it.get("raw", ""),
                    "slot": slot,
                    "slot_fa": SLOT_FA[slot],
                    "time": clock.get(slot, "12:00"),
                    "food": food,
                    "food_fa": FOOD_FA[food],
                    "how_fa": note,
                    "matched": bool(rec),
                    "order_source": "اختصاصی" if is_own else ("کلی" if (global_order["slots"] or global_order["freq"] or global_order["food"]) else "پیش‌فرض دارو"),
                    "conflict_fa": conflict,
                    "every_hours": order.get("every_hours"),
                }
            )
    rows.sort(key=lambda r: (r["time"], r["name_fa"]))
    return rows


def spacing_advice(rows: list) -> list:
    """هشدار داروهایی که در یک نوبت افتاده‌اند ولی باید فاصله بگیرند."""
    from .interactions import _pair_index

    idx = _pair_index()
    by_time = {}
    for r in rows:
        by_time.setdefault(r["time"], []).append(r)
    tips = []
    for t, group in sorted(by_time.items()):
        keys = [g["key"] for g in group if g["key"]]
        for i in range(len(keys)):
            for j in range(i + 1, len(keys)):
                hit = idx.get(tuple(sorted((keys[i], keys[j]))))
                if hit and ("فاصله" in hit["do_fa"] or "ساعت" in hit["do_fa"]):
                    tips.append(
                        {
                            "time": t,
                            "pair_fa": f"{fa_name(keys[i])} و {fa_name(keys[j])}",
                            "advice_fa": hit["do_fa"],
                            "severity": hit["severity"],
                        }
                    )
    return tips


def empty_stomach_conflicts(rows: list) -> list:
    """چند داروی ناشتا در یک ساعت = تداخل جذب."""
    groups = {}
    for r in rows:
        if r["food"] == "empty":
            groups.setdefault(r["time"], []).append(r["name_fa"])
    return [
        {"time": t, "names_fa": names}
        for t, names in sorted(groups.items())
        if len(names) > 1
    ]


MISSED_DOSE_FA = {
    "general": [
        "اگر یادتان افتاد و تا نوبت بعدی خیلی مانده: همان موقع بخورید.",
        "اگر نزدیک نوبت بعدی است: دوز فراموش‌شده را رد کنید و نوبت بعد را سر وقت بخورید.",
        "هرگز دو دوز را با هم نخورید تا جبران شود.",
        "اگر بیش از یک نوبت پشت‌سرهم فراموش شد، با پزشک یا داروساز تماس بگیرید.",
    ],
    "rules": [
        {"match": ["anticoagulant"], "text": "وارفارین و ضدانعقادها: دوز جامانده را دو برابر نکنید. اگر همان روز یادتان افتاد بخورید، اگر روز بعد شد آن نوبت را رد کنید و در دفترچه یادداشت کنید تا به پزشک بگویید."},
        {"match": ["contraceptive"], "text": "قرص ضدبارداری: اگر کمتر از ۱۲ ساعت گذشته همان موقع بخورید. بیشتر از ۱۲ ساعت، قرص را بخورید ولی ۷ روز از روش کمکی (کاندوم) استفاده کنید."},
        {"match": ["antibiotic", "anti-tb"], "text": "آنتی‌بیوتیک: هرچه زودتر بخورید و بقیه دوره را با همان فاصله ادامه دهید. دوره را نصفه رها نکنید، حتی اگر خوب شدید."},
        {"match": ["thyroid"], "text": "لووتیروکسین: اگر همان روز یادتان افتاد ناشتا بخورید؛ اگر روز بعد شد، برخی پزشکان اجازه می‌دهند دو قرص یکجا خورده شود — این را فقط با تأیید پزشک خودتان انجام دهید."},
        {"match": ["anticonvulsant"], "text": "داروی تشنج: هر چه سریع‌تر بخورید. فراموشی مکرر می‌تواند تشنج را برگرداند؛ یادآور تنظیم کنید."},
        {"match": ["antidiabetic"], "text": "داروی قند: اگر وعده غذایی مربوطه گذشته، دوز را رد کنید (خطر افت قند). قند خون را چک کنید."},
        {"match": ["bisphosphonate"], "text": "آلندرونات هفتگی: اگر روز مقرر فراموش شد، صبح روز بعد ناشتا بخورید و بعد به روز همیشگی هفته برگردید. دو قرص در یک روز نخورید."},
        {"match": ["dmard"], "text": "متوترکسات هفتگی: اگر ۱ تا ۲ روز گذشته همان دوز را بخورید؛ بیشتر از آن با پزشک تماس بگیرید. هرگز دو دوز هفتگی را جمع نکنید."},
        {"match": ["corticosteroid"], "text": "کورتون: دوز صبح را همان روز بخورید. خودسرانه قطع نکنید چون افت فشار و ضعف شدید می‌دهد."},
        {"match": ["benzodiazepine", "hypnotic"], "text": "آرام‌بخش و خواب‌آور: اگر شب فراموش شد و صبح شده، آن نوبت را رد کنید تا روز بعد گیج و خواب‌آلود نباشید."},
    ],
}


def missed_dose_guide(keys: list) -> dict:
    drugs = load_drugs()
    classes = {drugs[k]["class"] for k in keys if k in drugs}
    specific = [
        r["text"] for r in MISSED_DOSE_FA["rules"] if classes & set(r["match"])
    ]
    return {"general": MISSED_DOSE_FA["general"], "specific": specific}
