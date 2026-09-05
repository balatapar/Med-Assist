# -*- coding: utf-8 -*-
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.interactions import (
    SEVERITY_FA,
    analyze,
    check_duplicate_class,
    check_foods,
    check_pairs,
    load_foods,
)
from core.normalize import load_drugs


def test_warfarin_nsaid_is_danger():
    hits = check_pairs(["warfarin", "ibuprofen"])
    assert len(hits) == 1
    assert hits[0]["severity"] == "danger"
    assert hits[0]["symptoms_fa"]


def test_pair_order_does_not_matter():
    a = check_pairs(["ibuprofen", "warfarin"])
    b = check_pairs(["warfarin", "ibuprofen"])
    assert a[0]["severity"] == b[0]["severity"]


def test_no_self_pair():
    assert check_pairs(["warfarin", "warfarin"]) == []


def test_sorted_danger_first():
    hits = check_pairs(["warfarin", "ibuprofen", "levothyroxine", "calcium-d"])
    sev = [h["severity"] for h in hits]
    assert sev[0] == "danger"
    assert sev == sorted(sev, key=lambda s: {"danger": 0, "moderate": 1, "caution": 2}[s])


def test_duplicate_class_detects_two_nsaids():
    dup = check_duplicate_class(["ibuprofen", "naproxen"])
    assert dup and dup[0]["class"] == "nsaid"
    assert len(dup[0]["members_fa"]) == 2


def test_supplements_not_flagged_as_duplicates():
    assert check_duplicate_class(["vitamin-d", "omega-3", "zinc"]) == []


def test_grapefruit_is_danger_for_statin():
    foods = check_foods(["atorvastatin"])
    ids = {f["id"]: f for f in foods}
    assert "grapefruit" in ids
    assert ids["grapefruit"]["severity"] == "danger"


def test_dairy_flagged_for_ciprofloxacin():
    ids = {f["id"] for f in check_foods(["ciprofloxacin"])}
    assert "dairy" in ids


def test_no_food_hits_for_unrelated_drug():
    assert check_foods(["salbutamol"]) != []  # کافئین
    assert check_foods([]) == []


def test_analyze_shape_and_counts():
    out = analyze(["warfarin", "ibuprofen", "aspirin"])
    assert out["danger_count"] >= 2
    assert out["red_flags"]
    assert set(out) == {
        "pairs", "duplicates", "foods",
        "danger_count", "moderate_count", "caution_count", "red_flags",
    }


def test_data_integrity_all_food_drugs_exist():
    known = set(load_drugs())
    for gid, g in load_foods().items():
        unknown = [d for d in g["drugs"] if d not in known]
        assert not unknown, (gid, unknown)
        assert g["severity"] in SEVERITY_FA
