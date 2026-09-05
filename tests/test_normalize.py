# -*- coding: utf-8 -*-
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest

from core.normalize import (
    load_drugs,
    parse_drug_lines,
    resolve_drug,
    strip_dose_noise,
    to_en_digits,
    to_fa_digits,
)


def test_digit_roundtrip():
    assert to_en_digits("۱۲۳۴۵") == "12345"
    assert to_fa_digits(2026) == "۲۰۲۶"
    assert to_fa_digits("08:30") == "۰۸:۳۰"


def test_strip_dose_noise():
    assert "500" not in strip_dose_noise("قرص متفورمین 500 mg")
    assert "قرص" not in strip_dose_noise("قرص متفورمین")


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("وارفارین", "warfarin"),
        ("قرص وارفارين", "warfarin"),          # عربی ی
        ("گلوکوفاژ", "metformin"),
        ("متفورمین ۵۰۰", "metformin"),
        ("بروفن 400", "ibuprofen"),
        ("لوزک", "omeprazole"),
        ("levothyroxin", "levothyroxine"),
        ("ciproflox", "ciprofloxacin"),
        ("کلسیم دی", "calcium-d"),
        ("آسپیرین 80", "aspirin"),
        ("پلاویکس", "clopidogrel"),
        ("سیمبیکورت", "budesonide-formoterol"),
        ("باکتریم", "trimethoprim-sulfamethoxazole"),
        ("قرص ال دی", "levonorgestrel-ethinylestradiol"),
    ],
)
def test_resolve_known(raw, expected):
    key, conf, _ = resolve_drug(raw)
    assert key == expected, f"{raw} -> {key} (conf={conf})"
    assert conf >= 0.86


def test_unknown_drug_returns_none():
    key, conf, cleaned = resolve_drug("قرص فرضی زوپلیکسانتین")
    assert key is None
    assert cleaned


def test_parse_multiline_and_dedupe():
    items = parse_drug_lines("وارفارین\nبروفن، امپرازول\n- وارفارین")
    keys = [i["key"] for i in items]
    assert keys == ["warfarin", "ibuprofen", "omeprazole"]


def test_every_drug_resolves_to_itself():
    """هر دارو باید با نام فارسی خودش پیدا شود (سلامت بانک داده)."""
    failures = []
    for key, rec in load_drugs().items():
        got, conf, _ = resolve_drug(rec["fa"])
        if got != key:
            failures.append((key, rec["fa"], got, conf))
    assert not failures, failures
