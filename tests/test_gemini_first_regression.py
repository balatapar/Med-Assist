import os
from unittest.mock import patch
from core.analyzer import analyze_drugs

def test_unknown_vyvanse_is_sent_to_gemini_without_local_filter():
    fake = {"pairs": [], "food_warnings": [], "duplicate_class_warnings": [], "red_flags_fa": []}
    with patch.dict(os.environ, {"GEMINI_API_KEY": "test-key"}):
        with patch("core.analyzer.get_engine") as get_engine:
            eng=get_engine.return_value
            eng.identify_drugs.return_value=[{"generic_en":"lisdexamfetamine","generic_fa":"لیزدگزامفتامین","raw":"ویاس"}]
            eng.analyze_interactions.return_value=fake
            result=analyze_drugs("ویاس ۳۰ صبح")
    eng.analyze_interactions.assert_called_once()
    sent=eng.analyze_interactions.call_args.args[0]
    assert any(d.get("generic_en")=="lisdexamfetamine" for d in sent)
    assert result.source == "hybrid"


def test_unknown_vyvanse_schedule_is_not_dropped():
    fake = {"rows": [{"generic_en":"lisdexamfetamine","slot":"morning","time_hhmm":"08:00","food":"any","food_fa":"با یا بدون غذا","instruction_fa":"طبق دستور پزشک","source":"doctor"}], "conflicts_fa": [], "empty_stomach_conflicts_fa": []}
    with patch.dict(os.environ, {"GEMINI_API_KEY": "test-key"}):
        with patch("core.analyzer.get_engine") as get_engine:
            eng=get_engine.return_value
            eng.identify_drugs.return_value=[{"generic_en":"lisdexamfetamine","generic_fa":"لیزدگزامفتامین","raw":"ویاس"}]
            eng.build_schedule.return_value=fake
            result=__import__("core.analyzer",fromlist=["build_schedule_unified"]).build_schedule_unified("ویاس ۳۰ صبح")
    eng.build_schedule.assert_called_once()
    assert any(r["key"]=="lisdexamfetamine" for r in result.rows)


def test_unknown_vyvanse_missed_dose_reaches_gemini():
    fake={"general_fa":["قاعده عمومی"],"specific_fa":["راهنمای ویاس"]}
    with patch.dict(os.environ, {"GEMINI_API_KEY": "test-key"}):
        with patch("core.analyzer.get_engine") as get_engine:
            eng=get_engine.return_value
            eng.identify_drugs.return_value=[{"generic_en":"lisdexamfetamine","generic_fa":"لیزدگزامفتامین","raw":"ویاس"}]
            eng.missed_dose_guide.return_value=fake
            result=__import__("core.analyzer",fromlist=["missed_dose_unified"]).missed_dose_unified("ویاس ۳۰ صبح")
    eng.missed_dose_guide.assert_called_once()
    assert "راهنمای ویاس" in result["specific"]
