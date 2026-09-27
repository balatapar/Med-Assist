"""لایه یکپارچه: اول Gemini، در صورت خطا فول‌بک به لوکال."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any

from .gemini_engine import get_engine, get_llm_engine
from .interactions import analyze as local_analyze, fa_name
from .normalize import load_drugs, parse_drug_lines
from .schedule import (
    DEFAULT_CLOCK,
    SLOT_FA,
    FOOD_FA,
    build_schedule as local_build_schedule,
    empty_stomach_conflicts,
    missed_dose_guide as local_missed_guide,
    spacing_advice,
)


@dataclass
class AnalysisResult:
    pairs: list
    duplicates: list
    foods: list
    danger_count: int
    moderate_count: int
    caution_count: int
    red_flags: list
    source: str  # "gemini" | "local" | "hybrid"


@dataclass
class ScheduleResult:
    rows: list
    conflicts: list
    empty_conflicts: list
    spacing_tips: list
    source: str


def _normalize_gemini_pairs(gem: dict, all_drugs: list) -> list:
    """خروجی Gemini pairs → فرمت یکپارچه"""
    out = []
    for p in gem.get("pairs", []):
        a, b = p.get("a"), p.get("b")
        if not a or not b:
            continue
        out.append({
            "a": a, "b": b,
            "a_fa": fa_name(a), "b_fa": fa_name(b),
            "severity": p.get("severity", "moderate"),
            "severity_fa": {"danger":"خطرناک","moderate":"متوسط","caution":"نیازمند احتیاط"}[p.get("severity","moderate")],
            "icon": {"danger":"🛑","moderate":"⚠️","caution":"ℹ️"}[p.get("severity","moderate")],
            "why_fa": p.get("mechanism_fa", ""),
            "do_fa": p.get("action_fa", ""),
            "symptoms_fa": p.get("symptoms_fa", ""),
        })
    return out


def _normalize_gemini_foods(gem: dict) -> list:
    out = []
    for f in gem.get("food_warnings", []):
        out.append({
            "id": f.get("drug","food").lower().replace(" ","_"),
            "food_fa": f.get("food_fa",""),
            "severity": f.get("severity","caution"),
            "severity_fa": {"danger":"خطرناک","moderate":"متوسط","caution":"نیازمند احتیاط"}[f.get("severity","caution")],
            "icon": {"danger":"🛑","moderate":"⚠️","caution":"ℹ️"}[f.get("severity","caution")],
            "why_fa": f.get("why_fa",""),
            "do_fa": f.get("do_fa",""),
            "drugs_fa": [fa_name(f.get("drug",""))],
        })
    return out


def _normalize_gemini_dups(gem: dict) -> list:
    out = []
    for d in gem.get("duplicate_class_warnings", []):
        out.append({
            "class": d.get("class_fa",""),
            "members": d.get("drugs_en",[]),
            "members_fa": [fa_name(x) for x in d.get("drugs_en",[])],
        })
    return out


def _merge_pairs(local: list, gemini: list) -> list:
    """ادغام: اول Gemini، بعد لوکال برای مواردی که Gemini نداشته"""
    seen = set()
    merged = []
    for p in gemini + local:
        k = tuple(sorted((p["a"], p["b"])))
        if k not in seen:
            seen.add(k)
            merged.append(p)
    # مرتب‌سازی بر اساس شدت
    order = {"danger": 0, "moderate": 1, "caution": 2}
    merged.sort(key=lambda x: order.get(x["severity"], 3))
    return merged


def _resolve_key(provider: str, api_key: str | None) -> str:
    if api_key and api_key.strip():
        return api_key.strip()
    env_name = "OPENROUTER_API_KEY" if (provider or "gemini") == "openrouter" else "GEMINI_API_KEY"
    return os.environ.get(env_name, "").strip()


def analyze_drugs(drug_text: str, doctor_order: str = "", *, provider: str = "gemini",
                  model: str | None = None, api_key: str | None = None) -> AnalysisResult:
    """نقطه ورود اصلی: متن کاربر → تحلیل کامل"""
    # 1) استخراج داروها
    items = parse_drug_lines(drug_text)
    keys = [i["key"] for i in items if i["key"]]
    unmatched = [i for i in items if not i["key"]]

    # اگر همه داروها در لوکال هستند و تعداد کم است → سریع لوکال
    use_local_first = len(keys) <= 5 and not unmatched and all(k in load_drugs() for k in keys)

    # 2) تلاش LLM (مگر در حالت آفلاین/بدون کلید)
    gem_ok = False
    gem_pairs = gem_foods = gem_dups = gem_red = []
    eff_key = _resolve_key(provider, api_key)
    if eff_key:
        try:
            eng = get_llm_engine(provider, model, eff_key)
            # شناسایی مجدد با Gemini برای داروهای ناشناخته
            if unmatched:
                extra = "\n".join(i["raw"] for i in unmatched)
                identified = eng.identify_drugs(extra)
                for idf in identified:
                    gen = idf.get("generic_en")
                    if gen and gen not in keys:
                        keys.append(gen)
            # تحلیل تداخل
            identified_all = [{"generic_en": k} for k in keys]
            if identified_all:
                gem = eng.analyze_interactions(identified_all)
                gem_pairs = _normalize_gemini_pairs(gem, keys)
                gem_foods = _normalize_gemini_foods(gem)
                gem_dups = _normalize_gemini_dups(gem)
                gem_red = gem.get("red_flags_fa", [])
                gem_ok = True
        except Exception as e:
            print(f"[Gemini analyze error] {e}")

    # 3) لوکال همیشه (برای پوشش کامل)
    local = local_analyze(keys)

    # 4) ادغام
    if gem_ok:
        pairs = _merge_pairs(local["pairs"], gem_pairs)
        foods = gem_foods + [f for f in local["foods"] if f["id"] not in {x["id"] for x in gem_foods}]
        dups = gem_dups + [d for d in local["duplicates"] if set(d["members"]) not in {set(x["members"]) for x in gem_dups}]
        red = list(dict.fromkeys(gem_red + local["red_flags"]))
        source = "hybrid"
    else:
        pairs, foods, dups, red = local["pairs"], local["foods"], local["duplicates"], local["red_flags"]
        source = "local"

    return AnalysisResult(
        pairs=pairs,
        duplicates=dups,
        foods=foods,
        danger_count=sum(1 for p in pairs if p["severity"]=="danger"),
        moderate_count=sum(1 for p in pairs if p["severity"]=="moderate"),
        caution_count=sum(1 for p in pairs if p["severity"]=="caution"),
        red_flags=red,
        source=source,
    )


def build_schedule_unified(drug_text: str, doctor_order: str = "", clock: dict = None, *,
                           provider: str = "gemini", model: str | None = None,
                           api_key: str | None = None) -> ScheduleResult:
    items = parse_drug_lines(drug_text)
    keys = [i["key"] for i in items if i["key"]]
    unmatched = [i for i in items if not i["key"]]

    gem_ok = False
    gem_rows = gem_conf = gem_empty = []
    eff_key = _resolve_key(provider, api_key)
    if eff_key:
        try:
            eng = get_llm_engine(provider, model, eff_key)
            if unmatched:
                extra = "\n".join(i["raw"] for i in unmatched)
                identified = eng.identify_drugs(extra)
                for idf in identified:
                    gen = idf.get("generic_en")
                    if gen and gen not in keys:
                        keys.append(gen)
            identified_all = [{"generic_en": k, "raw": next((i["raw"] for i in items if i["key"]==k), "")} for k in keys]
            if identified_all:
                gem = eng.build_schedule(identified_all, doctor_order, clock)
                # نرمال‌سازی ردیف‌های Gemini به فرمت local rows
                gem_rows = []
                for r in gem.get("rows", []):
                    generic = r.get("generic_en", "")
                    rec = load_drugs().get(generic, {})
                    slot = r.get("slot", "morning")
                    gem_rows.append({
                        "key": generic,
                        "name_fa": rec.get("fa") or r.get("generic_fa") or generic,
                        "raw": r.get("raw") or generic,
                        "slot": slot,
                        "slot_fa": SLOT_FA.get(slot, slot),
                        "time": r["time_hhmm"],
                        "food": r["food"],
                        "food_fa": r["food_fa"],
                        "how_fa": r["instruction_fa"],
                        "matched": True,
                        "order_source": r.get("source","doctor"),
                        "conflict_fa": "",
                        "every_hours": None,
                    })
                gem_conf = gem.get("conflicts_fa", [])
                gem_empty = gem.get("empty_stomach_conflicts_fa", [])
                gem_ok = True
        except Exception as e:
            print(f"[Gemini schedule error] {e}")

    # لوکال
    local_rows = local_build_schedule(items, doctor_order, clock)
    local_conf = [r["conflict_fa"] for r in local_rows if r.get("conflict_fa")]
    local_empty = [{"time": c["time"], "names_fa": c["names_fa"]} for c in empty_stomach_conflicts(local_rows)]

    if gem_ok:
        # ادغام ساده: Gemini برای داروهای شناخته‌شده، لوکال برای بقیه
        rows = gem_rows + [r for r in local_rows if r["key"] not in {x["key"] for x in gem_rows}]
        rows.sort(key=lambda x: (x["time"], x["name_fa"]))
        conflicts = list(dict.fromkeys(gem_conf + local_conf))
        empty_c = gem_empty + local_empty
        source = "hybrid"
    else:
        rows, conflicts, empty_c = local_rows, local_conf, local_empty
        source = "local"

    spacing = spacing_advice(rows)
    return ScheduleResult(
        rows=rows,
        conflicts=conflicts,
        empty_conflicts=empty_c,
        spacing_tips=spacing,
        source=source,
    )


def missed_dose_unified(drug_text: str, *, provider: str = "gemini",
                        model: str | None = None, api_key: str | None = None) -> dict:
    items = parse_drug_lines(drug_text)
    keys = [i["key"] for i in items if i["key"]]
    unmatched = [i for i in items if not i["key"]]

    gem_ok = False
    gen = spec = []
    eff_key = _resolve_key(provider, api_key)
    if eff_key:
        try:
            eng = get_llm_engine(provider, model, eff_key)
            if unmatched:
                identified_unknown = eng.identify_drugs("\n".join(i["raw"] for i in unmatched))
                for item in identified_unknown:
                    generic = item.get("generic_en")
                    if generic and generic not in keys:
                        keys.append(generic)
            if keys:
                identified = [{"generic_en": k} for k in keys]
                gem = eng.missed_dose_guide(identified)
            gen, spec = gem.get("general_fa", []), gem.get("specific_fa", [])
            gem_ok = True
        except Exception as e:
            print(f"[Gemini missed error] {e}")

    local = local_missed_guide(keys)
    if gem_ok:
        return {
            "general": list(dict.fromkeys(gen + local["general"])),
            "specific": list(dict.fromkeys(spec + local["specific"])),
        }
    return local
