"""موتور تحلیل دارویی با LLM — تولید JSON ساختاریافته.

دو ارائه‌دهنده (مثل Wokeness-Rate، انتخاب با کاربر):
- gemini: مدل‌های Gemini با google-genai
- openrouter: هر مدل OpenAI-compatible از طریق OpenRouter (پیش‌فرض: openai/gpt-4o-mini)
کلید هر کاربر فقط در موتور خودش نگه داشته می‌شود و با بقیه قاطی نمی‌شود.
"""

from __future__ import annotations

import json
import os
import re
from functools import lru_cache
from typing import Any

from google import genai
from google.genai import types

# مدل‌های پیش‌فرض (اولین موجود استفاده می‌شود)
MODEL_CHAIN = [
    "gemini-3.5-flash",
    "gemini-flash-latest",
    "gemini-2.5-flash",
    "gemini-2.5-flash-lite",
]

PROVIDERS = ("gemini", "openrouter")
DEFAULT_MODELS = {"gemini": "", "openrouter": "openai/gpt-4o-mini"}  # gemini خالی = انتخاب خودکار از MODEL_CHAIN
PROVIDER_FA = {"gemini": "Gemini (گوگل)", "openrouter": "OpenRouter"}

# پرامپت‌های سیستم — خروجی فقط JSON، بدون markdown
SYS_IDENTIFY = """شما یک داروساز متخصص هستید. وظیفه: استخراج داروها از متن آزاد کاربر.
خروجی: فقط JSON معتبر، بدون markdown، بدون توضیح اضافی.
اسکیما:
{
  "drugs": [
    {
      "raw": "متن اصلی کاربر برای این دارو",
      "generic_fa": "نام ژنریک فارسی",
      "generic_en": "generic name in English",
      "brand_fa": "برند رایج ایران (اختیاری)",
      "dose": "دوز و واحد (مثال: 500 mg، 10 mg، 20 mg/5 ml)",
      "route": "oral | sublingual | topical | inhaler | injection | suppository | other",
      "frequency_text": "دستور تکرار همان‌طور که نوشته شده (مثال: روزی 2 بار، هر 8 ساعت، BD)",
      "timing_text": "ارتباط با غذا همان‌طور که نوشته شده (مثال: بعد از غذا، ناشتا، همراه غذا)",
      "notes": "نکات اضافی کاربر"
    }
  ]
}
قوانین:
- اگر کاربر چند دارو در یک خط نوشته، جدا کن.
- نام ژنریک انگلیسی را استاندارد بنویس (INN).
- اگر مطمئن نیستی generic_en را null بگذار.
- frequency_text و timing_text دقیقاً عبارت کاربر را نگه دار.
"""

SYS_INTERACTIONS = """شما یک فارماکولوژیست متخصص هستید. با لیست داروهای ژنریک داده شده، تداخل‌های بالینی مهم را تحلیل کن.
خروجی: فقط JSON معتبر.
اسکیما:
{
  "pairs": [
    {
      "a": "generic_en_A",
      "b": "generic_en_B",
      "severity": "danger | moderate | caution",
      "mechanism_fa": "مکانیزم تداخل به فارسی ساده",
      "action_fa": "اقدام عملی کاربر به فارسی",
      "symptoms_fa": "علائم هشداردهنده به فارسی"
    }
  ],
  "food_warnings": [
    {
      "drug": "generic_en",
      "food_fa": "نام غذا/گروه غذایی",
      "severity": "danger | moderate | caution",
      "why_fa": "چرا تداخل دارد",
      "do_fa": "چه کاری باید بکند"
    }
  ],
  "duplicate_class_warnings": [
    {
      "class_fa": "نام کلاس به فارسی",
      "drugs_en": ["generic_en1", "generic_en2"],
      "warning_fa": "هشدار دوز مضاعف"
    }
  ],
  "red_flags_fa": ["علائم اورژانسی به فارسی"]
}
قوانین:
- فقط تداخل‌های بالینی مهم و مستند را گزارش کن.
- severity: danger = تهدید حیات/عضو، moderate = نیاز به پایش/تغییر دوز، caution = آگاه‌سازی.
- اگر تداخلی نیست، آرایه خالی برگردان.
"""

SYS_SCHEDULE = """شما یک داروساز بالینی هستید. برای هر دارو، برنامه زمانی دقیق روزانه بساز.
ورودی: لیست داروها با frequency_text و timing_text، و دستور کلی پزشک (اختیاری).
خروجی: فقط JSON.
اسکیما:
{
  "rows": [
    {
      "generic_en": "drug key",
      "slot": "morning | noon | evening | night | bedtime",
      "time_hhmm": "08:00",
      "food": "empty | before | with | after | any",
      "food_fa": "ناشتا (معده خالی) | ۳۰ دقیقه قبل غذا | همراه غذا | بعد از غذا | با یا بدون غذا",
      "instruction_fa": "نحوه مصرف کامل به فارسی",
      "source": "doctor | default | inferred"
    }
  ],
  "conflicts_fa": ["هشدارهای تداخل زمانی/غذا بین داروها"],
  "empty_stomach_conflicts_fa": ["داروهای ناشتا که در یک ساعت افتاده‌اند"]
}
قوانین:
- ساعات پیش‌فرض: morning=08:00, noon=13:30, evening=18:00, night=20:30, bedtime=22:30
- دستور پزشک بر پیش‌فرض دارو مقدم است، مگر برای داروهای حساس (تیروئید، بيسفسفات، PPI، آنتی‌تی‌بی) که قاعده غذایی‌شان ثابت است.
- اگر frequency_text = "هر 8 ساعت" → 3 نوبت با فاصله 8 ساعته.
- food_fa باید دقیقاً یکی از 5 گزینه بالا باشد.
"""

SYS_MISSED = """شما یک داروساز هستید. برای لیست داروهای داده‌شده، راهنمای دوز فراموش‌شده بنویس.
خروجی: فقط JSON.
اسکیما:
{
  "general_fa": ["قاعده عمومی"],
  "specific_fa": ["راهنمای اختصاصی هر دارو/کلاس"]
}
قوانین:
- قاعده عمومی: تا نوبت بعد بخور، دو دوز با هم نخور، بیش از یک نوبت یادت رفت با پزشک مشورت کن.
- specific: برای وارفارین، قرص ضدبارداری، آنتی‌بیوتیک، لووتیروکسین، آنتی‌تشنج، داروهای قند، آلندرونات هفتگی، متوترکسات، کورتون، بنزودیازپین/خواب‌آورها.
"""

def parse_json_fallback(text: str) -> dict:
    """متن پاسخ مدل → dict با چند استراتژی؛ در بدترین حالت {}."""
    text = (text or "").strip()
    if not text:
        return {}
    for strategy in [
        lambda t: json.loads(t),
        lambda t: json.loads(re.search(r"\{.*\}", t, re.DOTALL).group(0)) if re.search(r"\{.*\}", t, re.DOTALL) else None,
        lambda t: json.loads(t[t.index("{"):t.rindex("}") + 1]) if "{" in t and "}" in t else None,
    ]:
        try:
            result = strategy(text)
            if isinstance(result, dict):
                return result
        except Exception:
            continue
    return {}


class GeminiEngine:
    def __init__(self, api_key: str | None = None, model: str | None = None):
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not set")
        self.forced_model = (model or "").strip() or None
        self.client = genai.Client(api_key=self.api_key)
        self._model_name = None

    def _pick_model(self) -> str:
        if self.forced_model:
            return self.forced_model
        if self._model_name:
            return self._model_name
        for m in MODEL_CHAIN:
            try:
                # quick check by listing models is expensive; just try generate
                self.client.models.generate_content(
                    model=m,
                    contents="test",
                    config=types.GenerateContentConfig(max_output_tokens=5)
                )
                self._model_name = m
                return m
            except Exception:
                continue
        raise RuntimeError("No working Gemini model found")

    def _generate_json(self, system: str, user: str, max_tokens: int = 4096) -> dict:
        model = self._pick_model()
        resp = self.client.models.generate_content(
            model=model,
            contents=user,
            config=types.GenerateContentConfig(
                system_instruction=system,
                max_output_tokens=max_tokens,
                temperature=0.0,
                response_mime_type="application/json",
            )
        )
        text = resp.text.strip()
        # Parse with multiple fallback strategies
        for strategy in [
            lambda t: json.loads(t),
            lambda t: json.loads(re.search(r"\{.*\}", t, re.DOTALL).group(0)) if re.search(r"\{.*\}", t, re.DOTALL) else None,
            lambda t: json.loads(t[t.index("{"):t.rindex("}")+1]) if "{" in t and "}" in t else None,
        ]:
            try:
                result = strategy(text)
                if result is not None:
                    return result
            except Exception:
                continue
        # Last resort: return empty structure
        print(f"[Gemini JSON parse failed] Raw text (first 500): {text[:500]}")
        return {"pairs": [], "food_warnings": [], "duplicate_class_warnings": [], "red_flags_fa": []}

    def identify_drugs(self, text: str) -> list[dict]:
        """متن آزاد → لیست داروهای ساختاریافته"""
        if not text.strip():
            return []
        return self._generate_json(SYS_IDENTIFY, text).get("drugs", [])

    def analyze_interactions(self, drugs: list[dict]) -> dict:
        """لیست داروهای identified → تداخل‌ها"""
        if not drugs:
            return {"pairs": [], "food_warnings": [], "duplicate_class_warnings": [], "red_flags_fa": []}
        generic_list = [d.get("generic_en") or d.get("generic_fa") for d in drugs if d.get("generic_en") or d.get("generic_fa")]
        user = "لیست داروها (ژنریک): " + ", ".join(generic_list)
        return self._generate_json(SYS_INTERACTIONS, user)

    def build_schedule(self, drugs: list[dict], doctor_order: str = "", clock: dict | None = None) -> dict:
        """سازماندهی جدول زمانی"""
        if not drugs:
            return {"rows": [], "conflicts_fa": [], "empty_stomach_conflicts_fa": []}
        clock = clock or {"morning": "08:00", "noon": "13:30", "evening": "18:00", "night": "20:30", "bedtime": "22:30"}
        user = json.dumps({
            "drugs": drugs,
            "doctor_order": doctor_order,
            "default_clock": clock,
        }, ensure_ascii=False)
        return self._generate_json(SYS_SCHEDULE, user)

    def missed_dose_guide(self, drugs: list[dict]) -> dict:
        if not drugs:
            return {"general_fa": [], "specific_fa": []}
        generic_list = [d.get("generic_en") or d.get("generic_fa") for d in drugs if d.get("generic_en") or d.get("generic_fa")]
        user = "داروها: " + ", ".join(generic_list)
        return self._generate_json(SYS_MISSED, user)


@lru_cache(maxsize=1)
def get_engine() -> GeminiEngine:
    return GeminiEngine()


class OpenRouterEngine:
    """موتور OpenAI-compatible از طریق OpenRouter — همان ۴ متد GeminiEngine."""

    URL = "https://openrouter.ai/api/v1/chat/completions"

    def __init__(self, api_key: str | None = None, model: str | None = None):
        self.api_key = api_key or os.environ.get("OPENROUTER_API_KEY")
        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY not set")
        self.model = (model or "").strip() or DEFAULT_MODELS["openrouter"]

    def _chat_json(self, system: str, user: str, max_tokens: int = 4096) -> dict:
        import requests

        r = requests.post(
            self.URL,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
                "HTTP-Referer": "https://github.com/balatapar/Med-Assist",
                "X-Title": "daroyar",
            },
            json={
                "model": self.model,
                "temperature": 0.0,
                "max_tokens": max_tokens,
                "response_format": {"type": "json_object"},
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
            },
            timeout=90,
        )
        if r.status_code != 200:
            raise RuntimeError(f"OpenRouter error {r.status_code}: {r.text[:200]}")
        content = (r.json()["choices"][0]["message"]["content"] or "")
        return parse_json_fallback(content)

    def identify_drugs(self, text: str) -> list[dict]:
        if not text.strip():
            return []
        return self._chat_json(SYS_IDENTIFY, text).get("drugs", [])

    def analyze_interactions(self, drugs: list[dict]) -> dict:
        if not drugs:
            return {"pairs": [], "food_warnings": [], "duplicate_class_warnings": [], "red_flags_fa": []}
        generic_list = [d.get("generic_en") or d.get("generic_fa") for d in drugs if d.get("generic_en") or d.get("generic_fa")]
        return self._chat_json(SYS_INTERACTIONS, "لیست داروها (ژنریک): " + ", ".join(generic_list))

    def build_schedule(self, drugs: list[dict], doctor_order: str = "", clock: dict | None = None) -> dict:
        if not drugs:
            return {"rows": [], "conflicts_fa": [], "empty_stomach_conflicts_fa": []}
        clock = clock or {"morning": "08:00", "noon": "13:30", "evening": "18:00", "night": "20:30", "bedtime": "22:30"}
        user = json.dumps({"drugs": drugs, "doctor_order": doctor_order, "default_clock": clock}, ensure_ascii=False)
        return self._chat_json(SYS_SCHEDULE, user)

    def missed_dose_guide(self, drugs: list[dict]) -> dict:
        if not drugs:
            return {"general_fa": [], "specific_fa": []}
        generic_list = [d.get("generic_en") or d.get("generic_fa") for d in drugs if d.get("generic_en") or d.get("generic_fa")]
        return self._chat_json(SYS_MISSED, "داروها: " + ", ".join(generic_list))


_ENGINES: dict = {}


def get_llm_engine(provider: str = "gemini", model: str | None = None, api_key: str | None = None):
    """کارخانه موتور بر اساس انتخاب کاربر؛ کش جدا برای هر (provider, model, key)."""
    provider = (provider or "gemini").lower()
    if provider not in PROVIDERS:
        provider = "gemini"
    cache_key = (provider, (model or "").strip(), api_key or "")
    if cache_key not in _ENGINES:
        if provider == "openrouter":
            _ENGINES[cache_key] = OpenRouterEngine(api_key, model)
        else:
            _ENGINES[cache_key] = GeminiEngine(api_key, model)
    return _ENGINES[cache_key]
