"""تولید HTML بخش‌های گزارش (فارسی، RTL)."""

from __future__ import annotations

import html

from .normalize import to_fa_digits

SEV_CLASS = {"danger": "a-danger", "moderate": "a-moderate", "caution": "a-caution"}
BADGE_CLASS = {"danger": "b-danger", "moderate": "b-moderate", "caution": "b-caution"}


def e(s) -> str:
    return html.escape(str(s or ""))


def stats_html(analysis: dict, n_drugs: int) -> str:
    cells = [
        ("var(--txt)", to_fa_digits(n_drugs), "داروی بررسی‌شده"),
        ("var(--danger)", to_fa_digits(analysis["danger_count"]), "تداخل خطرناک"),
        ("var(--warn)", to_fa_digits(analysis["moderate_count"]), "تداخل متوسط"),
        ("var(--info)", to_fa_digits(len(analysis["foods"])), "هشدار غذایی"),
    ]
    inner = "".join(
        f'<div class="stat"><div class="n" style="color:{c}">{n}</div><div class="l">{l}</div></div>'
        for c, n, l in cells
    )
    return f'<div class="statgrid">{inner}</div>'


def alert_html(icon: str, title: str, body: str, severity: str, symptoms: str = "") -> str:
    sym = f'<div class="sym">علائم هشدار: {e(symptoms)}</div>' if symptoms else ""
    return (
        f'<div class="alert {SEV_CLASS[severity]}">'
        f'<div class="hd">{icon} {e(title)}</div>'
        f'<div class="bd">{e(body)}</div>{sym}</div>'
    )


def pairs_html(pairs: list) -> str:
    if not pairs:
        return (
            '<div class="alert a-caution"><div class="hd">✅ تداخل مهمی پیدا نشد</div>'
            '<div class="bd">بین داروهایی که وارد کردید، در بانک اطلاعاتی این برنامه '
            'تداخل ثبت‌شده‌ای نبود. این به معنی «قطعاً بی‌خطر» نیست؛ '
            'اگر داروی جدیدی اضافه می‌کنید با داروساز هم مشورت کنید.</div></div>'
        )
    out = []
    for p in pairs:
        out.append(
            alert_html(
                p["icon"],
                f'{p["a_fa"]} + {p["b_fa"]}  —  {p["severity_fa"]}',
                f'{p["why_fa"]}. {p["do_fa"]}',
                p["severity"],
                p.get("symptoms_fa", ""),
            )
        )
    return "".join(out)


def duplicates_html(dups: list) -> str:
    if not dups:
        return ""
    out = []
    for d in dups:
        names = " و ".join(d["members_fa"])
        out.append(
            alert_html(
                "🔁",
                f"داروی هم‌خانواده: {names}",
                "این داروها از یک خانواده هستند و اثرشان روی هم جمع می‌شود بدون اینکه "
                "فایده بیشتری بدهد. مطمئن شوید پزشک عمداً هر دو را خواسته است.",
                "moderate",
                "دوز مضاعف: عوارض بیشتر بدون سود درمانی",
            )
        )
    return "".join(out)


def foods_html(foods: list) -> str:
    if not foods:
        return '<div class="card"><div class="bd">هشدار غذایی خاصی برای این داروها ثبت نشده است.</div></div>'
    out = []
    for f in foods:
        drugs = "، ".join(f["drugs_fa"])
        out.append(
            alert_html(
                f["icon"],
                f'{f["food_fa"]}  —  {f["severity_fa"]}',
                f'مرتبط با: {drugs}. {f["why_fa"]}. {f["do_fa"]}',
                f["severity"],
            )
        )
    return "".join(out)


def schedule_table_html(rows: list) -> str:
    if not rows:
        return ""
    head = (
        "<tr><th>ساعت</th><th>نام دارو</th><th>نوبت</th>"
        "<th>ارتباط با غذا</th><th>نحوه مصرف</th></tr>"
    )
    body = []
    for r in rows:
        star = "" if r["matched"] else " ❓"
        body.append(
            f'<tr><td class="t">{to_fa_digits(r["time"])}</td>'
            f'<td class="n">{e(r["name_fa"])}{star}</td>'
            f'<td>{e(r["slot_fa"])}</td>'
            f'<td>{e(r["food_fa"])}</td>'
            f'<td>{e(r["how_fa"])}</td></tr>'
        )
    return f'<table class="tt">{head}{"".join(body)}</table>'


def conflicts_html(rows: list) -> str:
    seen, out = set(), []
    for r in rows:
        c = r.get("conflict_fa")
        if c and c not in seen:
            seen.add(c)
            out.append(alert_html("📌", "دستور کلی روی این دارو اعمال نشد", c, "moderate"))
    return "".join(out)


def spacing_html(tips: list) -> str:
    if not tips:
        return ""
    seen, out = set(), []
    for t in tips:
        k = (t["time"], t["pair_fa"])
        if k in seen:
            continue
        seen.add(k)
        out.append(
            alert_html(
                "⏱️",
                f'ساعت {to_fa_digits(t["time"])} — {t["pair_fa"]}',
                t["advice_fa"],
                t["severity"] if t["severity"] in SEV_CLASS else "moderate",
            )
        )
    return "".join(out)


def empty_stomach_html(conflicts: list) -> str:
    out = []
    for c in conflicts:
        out.append(
            alert_html(
                "⚠️",
                f'چند داروی ناشتا در ساعت {to_fa_digits(c["time"])}',
                f'{"، ".join(c["names_fa"])} هر دو ناشتا هستند و با هم جذب یکدیگر را کم می‌کنند. '
                "یکی را صبح ناشتا و دیگری را قبل خواب (۲ ساعت بعد از شام) بخورید.",
                "moderate",
            )
        )
    return "".join(out)


def missed_dose_html(guide: dict) -> str:
    gen = "".join(f"<li>{e(x)}</li>" for x in guide["general"])
    spec = "".join(f"<li>{e(x)}</li>" for x in guide["specific"])
    spec_block = (
        f'<div class="card"><h4>🎯 مخصوص داروهای شما</h4>'
        f'<div class="bd"><ul>{spec}</ul></div></div>' if spec else ""
    )
    return (
        f'<div class="card"><h4>📋 قاعده کلی دوز فراموش‌شده</h4>'
        f'<div class="bd"><ul>{gen}</ul></div></div>{spec_block}'
    )


def red_flags_html(flags: list) -> str:
    items = "".join(f"<li>{e(x)}</li>" for x in flags)
    return (
        '<div class="alert a-danger"><div class="hd">🚑 در این موارد فوری به پزشک '
        'یا اورژانس مراجعه کنید</div>'
        f'<div class="bd"><ul>{items}</ul></div></div>'
    )


def unmatched_html(items: list) -> str:
    miss = [i for i in items if not i.get("key")]
    if not miss:
        return ""
    chips = "".join(f'<div class="chip miss">{e(i["raw"])}</div>' for i in miss)
    return (
        f'<div class="card"><h4>❓ این موارد شناسایی نشدند</h4>'
        f'<div class="bd">این نام‌ها در بانک اطلاعاتی برنامه نبودند، پس تداخلشان بررسی نشد. '
        f'املا را چک کنید یا نام ژنریک (مثلاً «استامینوفن» به‌جای اسم برند) را وارد کنید.</div>'
        f'<div class="chips" style="margin-top:10px">{chips}</div></div>'
    )
