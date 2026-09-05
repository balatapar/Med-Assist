# -*- coding: utf-8 -*-
"""اعتبارسنجی .ics با کتابخانه مستقل icalendar (پارس واقعی، نه بررسی رشته‌ای)."""
import sys
from datetime import date, time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
from icalendar import Calendar

from core.ics import REPEAT_OPTIONS, build_ics, ics_bytes, parse_hhmm


def _one(**kw):
    ev = {"name": "متفورمین", "start_date": date(2026, 9, 6), "start_time": "08:30",
          "repeat": "daily", "note": "بعد از صبحانه"}
    ev.update(kw)
    return [ev]


def test_parses_with_icalendar_library():
    cal = Calendar.from_ical(build_ics(_one()))
    events = [c for c in cal.walk("VEVENT")]
    assert len(events) == 1
    assert "متفورمین" in str(events[0]["SUMMARY"])


def test_crlf_and_structure():
    text = build_ics(_one())
    assert text.startswith("BEGIN:VCALENDAR\r\n")
    assert text.rstrip().endswith("END:VCALENDAR")
    assert "\r\n" in text
    for bare in ("\nBEGIN:VEVENT",):
        assert text.count(bare) == text.count("\r\nBEGIN:VEVENT")


def test_valarm_present_and_trigger_format():
    cal = Calendar.from_ical(build_ics(_one(), alarm_minutes=15))
    alarms = [c for c in cal.walk("VALARM")]
    assert len(alarms) == 1
    assert str(alarms[0]["ACTION"]) == "DISPLAY"
    assert alarms[0]["TRIGGER"].dt.total_seconds() == -15 * 60


def test_zero_alarm_triggers_at_event_time():
    cal = Calendar.from_ical(build_ics(_one(), alarm_minutes=0))
    trig = [c for c in cal.walk("VALARM")][0]["TRIGGER"]
    assert trig.dt.total_seconds() == 0


def test_every_72h_rrule():
    cal = Calendar.from_ical(build_ics(_one(repeat="every_72h")))
    rr = [c for c in cal.walk("VEVENT")][0]["RRULE"]
    assert rr["FREQ"] == ["DAILY"]
    assert rr["INTERVAL"] == [3]


def test_weekly_and_monthly_rrule():
    for rep, freq in [("weekly", "WEEKLY"), ("monthly", "MONTHLY"),
                      ("every_3_months", "MONTHLY"), ("every_8h", "HOURLY")]:
        cal = Calendar.from_ical(build_ics(_one(repeat=rep)))
        assert [c for c in cal.walk("VEVENT")][0]["RRULE"]["FREQ"] == [freq]


def test_once_has_no_rrule():
    cal = Calendar.from_ical(build_ics(_one(repeat="once")))
    assert "RRULE" not in [c for c in cal.walk("VEVENT")][0]


def test_count_and_until():
    cal = Calendar.from_ical(build_ics(_one(count=10)))
    assert [c for c in cal.walk("VEVENT")][0]["RRULE"]["COUNT"] == [10]
    cal2 = Calendar.from_ical(build_ics(_one(until=date(2026, 12, 31))))
    assert [c for c in cal2.walk("VEVENT")][0]["RRULE"]["UNTIL"]


def test_dtstart_carries_tehran_tz_and_correct_clock():
    cal = Calendar.from_ical(build_ics(_one(start_time="21:45")))
    ev = [c for c in cal.walk("VEVENT")][0]
    assert ev["DTSTART"].params["TZID"] == "Asia/Tehran"
    dt = ev["DTSTART"].dt
    assert (dt.hour, dt.minute) == (21, 45)
    assert (dt.year, dt.month, dt.day) == (2026, 9, 6)


def test_dtend_after_dtstart():
    cal = Calendar.from_ical(build_ics(_one(), duration_minutes=10))
    ev = [c for c in cal.walk("VEVENT")][0]
    assert ev["DTEND"].dt > ev["DTSTART"].dt


def test_multiple_events_unique_uids():
    evs = _one() + _one(name="لووتیروکسین", start_time="07:00")
    cal = Calendar.from_ical(build_ics(evs))
    uids = [str(c["UID"]) for c in cal.walk("VEVENT")]
    assert len(uids) == 2 and len(set(uids)) == 2


def test_special_chars_escaped_and_recovered():
    cal = Calendar.from_ical(build_ics(_one(note="نکته؛ مهم, با آب زیاد")))
    desc = str([c for c in cal.walk("VEVENT")][0]["DESCRIPTION"])
    assert "؛" in desc and "," in desc


def test_long_persian_summary_folds_and_survives_roundtrip():
    long_name = "کپسول " + "آموکسی‌سیلین کلاوولانیک اسید " * 5
    text = build_ics(_one(name=long_name))
    assert all(len(l.encode()) <= 75 for l in text.split("\r\n") if l)
    cal = Calendar.from_ical(text)
    assert long_name.strip() in str([c for c in cal.walk("VEVENT")][0]["SUMMARY"])


def test_bytes_has_bom():
    assert ics_bytes(_one()).startswith(b"\xef\xbb\xbf")


def test_all_repeat_options_valid():
    for key in REPEAT_OPTIONS:
        cal = Calendar.from_ical(build_ics(_one(repeat=key)))
        assert len([c for c in cal.walk("VEVENT")]) == 1


def test_bad_input_raises():
    with pytest.raises(ValueError):
        build_ics([])
    with pytest.raises(ValueError):
        build_ics(_one(repeat="every_5_seconds"))
    with pytest.raises(ValueError):
        parse_hhmm("99:99")


def test_parse_hhmm_variants():
    assert parse_hhmm("8:05") == time(8, 5)
    assert parse_hhmm("۰۹:۳۰".translate({ord(a): ord(b) for a, b in zip("۰۱۲۳۴۵۶۷۸۹", "0123456789")})) == time(9, 30)
    assert parse_hhmm(time(7, 0)) == time(7, 0)
