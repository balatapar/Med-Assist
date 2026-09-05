"""تولید فایل استاندارد iCalendar (.ics) برای یادآور دارو.

خروجی شامل VEVENT با RRULE و VALARM است تا تقویم گوشی زنگ بزند.
پیاده‌سازی دستی (بدون وابستگی) + اعتبارسنجی با کتابخانه icalendar در تست.
"""

from __future__ import annotations

import hashlib
import re
from datetime import UTC, date, datetime, time, timedelta

PRODID = "-//Daroyar//Persian Medication Reminder//FA"

# فاصله تکرار: کلید انگلیسی (قرارداد داده) -> برچسب فارسی + RRULE
REPEAT_OPTIONS = {
    "daily": {"fa": "هر روز", "rrule": "FREQ=DAILY;INTERVAL=1"},
    "twice_daily": {"fa": "روزی دو بار (هر ۱۲ ساعت)", "rrule": "FREQ=HOURLY;INTERVAL=12"},
    "every_8h": {"fa": "هر ۸ ساعت (روزی ۳ بار)", "rrule": "FREQ=HOURLY;INTERVAL=8"},
    "every_48h": {"fa": "هر ۴۸ ساعت (دو روز یک‌بار)", "rrule": "FREQ=DAILY;INTERVAL=2"},
    "every_72h": {"fa": "هر ۷۲ ساعت (سه روز یک‌بار)", "rrule": "FREQ=DAILY;INTERVAL=3"},
    "weekly": {"fa": "هفتگی", "rrule": "FREQ=WEEKLY;INTERVAL=1"},
    "biweekly": {"fa": "هر دو هفته", "rrule": "FREQ=WEEKLY;INTERVAL=2"},
    "monthly": {"fa": "ماهانه", "rrule": "FREQ=MONTHLY;INTERVAL=1"},
    "every_3_months": {"fa": "هر ۳ ماه", "rrule": "FREQ=MONTHLY;INTERVAL=3"},
    "once": {"fa": "فقط یک بار", "rrule": None},
}


def _esc(text: str) -> str:
    """گریز کاراکترهای ویژه بر اساس RFC 5545 بخش ۳.۳.۱۱."""
    s = str(text or "")
    s = s.replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,")
    s = s.replace("\r\n", "\\n").replace("\n", "\\n").replace("\r", "\\n")
    return s


def _fold(line: str) -> str:
    """تاکردن خطوط بلندتر از ۷۵ اوکتت (RFC 5545 بخش ۳.۱)."""
    raw = line.encode("utf-8")
    if len(raw) <= 75:
        return line
    out, buf, size = [], bytearray(), 0
    for ch in line:
        b = ch.encode("utf-8")
        limit = 75 if not out else 74  # خطوط ادامه یک فاصله ابتدایی دارند
        if size + len(b) > limit:
            out.append(buf.decode("utf-8"))
            buf, size = bytearray(), 0
        buf.extend(b)
        size += len(b)
    if buf:
        out.append(buf.decode("utf-8"))
    return "\r\n ".join(out)


def _dt_local(d: date, t: time) -> str:
    return datetime(d.year, d.month, d.day, t.hour, t.minute, 0).strftime("%Y%m%dT%H%M%S")


def _utc_stamp() -> str:
    return datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")


def _uid(seed: str) -> str:
    h = hashlib.sha1(seed.encode("utf-8")).hexdigest()[:20]
    return f"{h}@daroyar.local"


def parse_hhmm(value) -> time:
    """'08:30' یا time -> time"""
    if isinstance(value, time):
        return value
    s = str(value).strip()
    m = re.match(r"^(\d{1,2})\s*[:.]?\s*(\d{2})?$", s)
    if not m:
        raise ValueError(f"invalid time: {value!r}")
    h = int(m.group(1))
    mi = int(m.group(2) or 0)
    if not (0 <= h <= 23 and 0 <= mi <= 59):
        raise ValueError(f"time out of range: {value!r}")
    return time(h, mi)


def build_ics(
    events: list,
    calendar_name: str = "یادآور دارو",
    alarm_minutes: int = 0,
    duration_minutes: int = 10,
    timezone_id: str = "Asia/Tehran",
) -> str:
    """events: [{name, start_date(date), start_time('HH:MM'|time), repeat(key),
                count(int|None), until(date|None), note(str)}]

    خروجی: متن کامل .ics با VEVENT + VALARM
    """
    if not events:
        raise ValueError("no events")

    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        f"PRODID:{PRODID}",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        f"X-WR-CALNAME:{_esc(calendar_name)}",
        f"X-WR-TIMEZONE:{timezone_id}",
    ]
    stamp = _utc_stamp()

    for i, ev in enumerate(events):
        name = str(ev.get("name") or "دارو").strip()
        d = ev.get("start_date") or date.today()
        if isinstance(d, datetime):
            d = d.date()
        t = parse_hhmm(ev.get("start_time") or "08:00")
        repeat = ev.get("repeat") or "daily"
        if repeat not in REPEAT_OPTIONS:
            raise ValueError(f"unknown repeat: {repeat}")
        rrule = REPEAT_OPTIONS[repeat]["rrule"]
        dtstart = _dt_local(d, t)
        end_dt = datetime(d.year, d.month, d.day, t.hour, t.minute) + timedelta(
            minutes=max(1, int(duration_minutes))
        )

        lines.append("BEGIN:VEVENT")
        lines.append(f"UID:{_uid(f'{name}|{dtstart}|{repeat}|{i}')}")
        lines.append(f"DTSTAMP:{stamp}")
        lines.append(f"DTSTART;TZID={timezone_id}:{dtstart}")
        lines.append(f"DTEND;TZID={timezone_id}:{end_dt.strftime('%Y%m%dT%H%M%S')}")
        lines.append(f"SUMMARY:{_esc('💊 ' + name)}")

        desc = ev.get("note") or f"زمان مصرف {name}"
        extra = REPEAT_OPTIONS[repeat]["fa"]
        lines.append(f"DESCRIPTION:{_esc(desc + ' — ' + extra)}")

        if rrule:
            parts = [rrule]
            count = ev.get("count")
            until = ev.get("until")
            if count:
                parts.append(f"COUNT={int(count)}")
            elif until:
                if isinstance(until, datetime):
                    until = until.date()
                parts.append(f"UNTIL={until.strftime('%Y%m%d')}T235900Z")
            lines.append("RRULE:" + ";".join(parts))

        lines.append("STATUS:CONFIRMED")
        lines.append("TRANSP:TRANSPARENT")
        lines.append("CATEGORIES:HEALTH,MEDICATION")
        lines.append("BEGIN:VALARM")
        m = max(0, int(alarm_minutes))
        lines.append(f"TRIGGER:-PT{m}M" if m else "TRIGGER:PT0M")
        lines.append("ACTION:DISPLAY")
        lines.append(f"DESCRIPTION:{_esc('یادآور مصرف ' + name)}")
        lines.append("END:VALARM")
        lines.append("END:VEVENT")

    lines.append("END:VCALENDAR")
    return "\r\n".join(_fold(x) for x in lines) + "\r\n"


def ics_bytes(*args, **kwargs) -> bytes:
    """خروجی بایت با BOM تا نام فارسی در اوت‌لوک هم درست بخواند."""
    return b"\xef\xbb\xbf" + build_ics(*args, **kwargs).encode("utf-8")
