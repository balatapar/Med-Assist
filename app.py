# -*- coding: utf-8 -*-
"""دارویار — دستیار تداخل دارویی و جدول مصرف (Gemini + لوکال، فارسی / RTL)."""

from __future__ import annotations

import os
import sys
from datetime import date, time
from pathlib import Path

import streamlit as st

# بارگذاری کلید Gemini از رجیستری ویندوز (اگر در env نیست)
if not os.environ.get("GEMINI_API_KEY"):
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment") as k:
            os.environ["GEMINI_API_KEY"], _ = winreg.QueryValueEx(k, "GEMINI_API_KEY")
    except Exception:
        pass

sys.path.insert(0, str(Path(__file__).resolve().parent))

from core import render as R
from core.analyzer import (
    analyze_drugs,
    build_schedule_unified,
    missed_dose_unified,
)
from core.ics import REPEAT_OPTIONS, ics_bytes
from core.normalize import load_drugs, parse_drug_lines, to_fa_digits
from core.schedule import DEFAULT_CLOCK, SLOT_FA
from core.theme import page_style

st.set_page_config(
    page_title="دارویار — دستیار تداخل دارویی",
    page_icon="💊",
    layout="centered",
    initial_sidebar_state="collapsed",
)

st.markdown(page_style(), unsafe_allow_html=True)
st.markdown(
    "<script>document.documentElement.setAttribute('dir','rtl');"
    "document.documentElement.setAttribute('lang','fa');</script>",
    unsafe_allow_html=True,
)

DRUGS = load_drugs()

# نشان‌دهنده منبع تحلیل
def source_badge(src: str) -> str:
    if src == "gemini":
        return '<span class="badge b-info">🤖 تحلیل شده با هوش مصنوعی</span>'
    if src == "hybrid":
        return '<span class="badge b-ok">🔀 هوش مصنوعی + لوکال</span>'
    return '<span class="badge b-caution">📦 تحلیل لوکال (آفلاین)</span>'

st.markdown(
    '<div class="hero"><h1>💊 دارویار</h1>'
    "<p>نام داروهایت و دستور پزشک را بنویس. تداخل‌ها، جدول مصرف، یادآور تقویم و راهنمای دوز فراموش‌شده می‌گیری."
    "تحلیل با هوش مصنوعی (Gemini یا OpenRouter — با کلید خودت)؛ در صورت قطع اینترنت، فول‌بک لوکال فعال می‌شود.</p></div>",
    unsafe_allow_html=True,
)

# ─────────────────── تنظیمات هوش مصنوعی: ارائه‌دهنده + کلید (هر کاربر مال خودش) ───────────────────
from core.gemini_engine import PROVIDER_FA, DEFAULT_MODELS

IS_WINDOWS = sys.platform.startswith("win")
st.session_state.setdefault("llm_provider", "gemini")
st.session_state.setdefault("llm_model", "")
st.session_state.setdefault("llm_key", "")

_url_key = (st.query_params.get("key") or "").strip()
if _url_key and _url_key != st.session_state["llm_key"]:
    st.session_state["llm_key"] = _url_key

_provider = st.session_state["llm_provider"]
_model_default = DEFAULT_MODELS.get(_provider, "")
_env_name = "OPENROUTER_API_KEY" if _provider == "openrouter" else "GEMINI_API_KEY"
_env_key = os.environ.get(_env_name, "").strip()
_session_key = st.session_state["llm_key"].strip()
active_key = _url_key or _session_key or _env_key
key_source = ("لینک" if _url_key else "این پنجره" if _session_key
              else "پیش‌فرض سرور" if _env_key else "—")

with st.expander(
    "⚙️ تنظیمات هوش مصنوعی — ارائه‌دهنده و کلید" + (f"  •  {_provider} • کلید: {key_source}" if active_key else ""),
    expanded=not bool(active_key),
):
    st.caption("هر کاربر کلید خودش را می‌زند و تحلیل با سهمیه‌ی خودش انجام می‌شود. کلید در سرور ذخیره نمی‌شود.")
    c_prov, c_model = st.columns([1, 1])
    with c_prov:
        prov = st.radio("ارائه‌دهنده", ["gemini", "openrouter"],
                        format_func=lambda p: PROVIDER_FA[p], horizontal=True, key="llm_provider")
    with c_model:
        st.text_input("مدل (خالی = خودکار)", key="llm_model",
                      placeholder=_model_default or "خودکار",
                      help="Gemini: خالی بگذار تا اولین مدل سالم انتخاب شود. OpenRouter مثل: openai/gpt-4o-mini")
    entered = st.text_input("کلید API", type="password", value=st.session_state["llm_key"],
                            placeholder="Gemini: AIza... | OpenRouter: sk-or-...",
                            label_visibility="collapsed")
    if entered.strip() != st.session_state["llm_key"]:
        st.session_state["llm_key"] = entered.strip()
        st.rerun()
    b1, b2, b3 = st.columns(3)
    with b1:
        if st.button("🔗 ذخیره در لینک"):
            if not entered.strip():
                st.warning("اول کلید را وارد کن.")
            else:
                st.session_state["llm_key"] = entered.strip()
                st.query_params["key"] = entered.strip()
                st.success("ذخیره شد — این صفحه را بوکمارک کن.")
                st.rerun()
    with b2:
        if IS_WINDOWS and st.button("💻 ذخیره در ویندوز"):
            if not entered.strip():
                st.warning("اول کلید را وارد کن.")
            else:
                try:
                    import winreg
                    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment", 0, winreg.KEY_SET_VALUE) as reg:
                        winreg.SetValueEx(reg, "GEMINI_API_KEY", 0, winreg.REG_SZ, entered.strip())
                    st.session_state["llm_key"] = entered.strip()
                    st.success("در ویندوز ذخیره شد.")
                    st.rerun()
                except Exception as e:
                    st.error(f"ثبت نشد: {e}")
    with b3:
        if (_url_key or _session_key) and st.button("🗑️ پاک کردن کلید"):
            st.session_state.pop("llm_key", None)
            st.query_params.pop("key", None)
            st.rerun()
    if not IS_WINDOWS:
        st.caption("«ذخیره در ویندوز» فقط روی کامپیوتر خودت است؛ در گوشی از «ذخیره در لینک» استفاده کن.")
    st.caption("[دریافت کلید رایگان Gemini](https://aistudio.google.com/apikey) • [کلید OpenRouter](https://openrouter.ai)")

_provider = st.session_state["llm_provider"]
_model = st.session_state["llm_model"].strip() or None
_session_key = st.session_state["llm_key"].strip()
_url_key = (st.query_params.get("key") or "").strip()
_env_key = os.environ.get("OPENROUTER_API_KEY" if _provider == "openrouter" else "GEMINI_API_KEY", "").strip()
active_key = _url_key or _session_key or _env_key

if not active_key:
    st.info("هنوز کلیدی فعال نیست — از باکس بالا ارائه‌دهنده و کلید خودت را وارد کن (بدون کلید فقط تحلیل لوکال).")

tab_check, tab_ics, tab_db = st.tabs(["🔍 بررسی داروها", "📅 یادآور تقویم", "📚 بانک دارو"])

# ─────────────────────────── تب ۱: بررسی ───────────────────────────
with tab_check:
    with st.form("drug_form"):
        drugs_text = st.text_area(
            "نام داروها (هر دارو در یک خط)",
            height=150,
            placeholder="nمتفورمین ۵۰۰ بعد غذا\nوارفارین ۵ شب",
            help="نام فارسی، برند ایرانی، انگلیسی یا فینگلیش — همه شناخته می‌شوند. دوز و زمان اختیاری.",
        )
        order_text = st.text_input(
            "دستور کلی پزشک (اختیاری)",
            placeholder="مثلاً: روزی ۲ بار بعد از غذا  /  هر ۸ ساعت  /  شب‌ها",
            help="اگر خالی بگذاری، زمان استاندارد هر دارو استفاده می‌شود",
        )
        with st.expander("⚙️ تنظیم ساعت نوبت‌ها"):
            c1, c2, c3 = st.columns(3)
            clock = {}
            widgets = [
                (c1, "morning"), (c2, "noon"), (c3, "evening"),
                (c1, "night"), (c2, "bedtime"),
            ]
            for col, slot in widgets:
                with col:
                    clock[slot] = st.text_input(
                        SLOT_FA[slot], value=DEFAULT_CLOCK[slot], key=f"clk_{slot}"
                    )
        submitted = st.form_submit_button("🔍 بررسی کن")

    if submitted and drugs_text.strip():
        with st.spinner("در حال تحلیل..."):
            a = analyze_drugs(drugs_text, order_text, provider=_provider, model=_model, api_key=active_key or None)
            s = build_schedule_unified(drugs_text, order_text, clock, provider=_provider, model=_model, api_key=active_key or None)
            m = missed_dose_unified(drugs_text, provider=_provider, model=_model, api_key=active_key or None)

        st.markdown(R.stats_html(a, len(parse_drug_lines(drugs_text))), unsafe_allow_html=True)
        st.markdown(source_badge(a.source), unsafe_allow_html=True)

        items = parse_drug_lines(drugs_text)
        st.session_state["last_names"] = [
            (item.get("raw") or item.get("key") or "").strip()
            for item in items if (item.get("raw") or item.get("key"))
        ]
        st.markdown(R.unmatched_html(items), unsafe_allow_html=True)

        st.markdown("### ۱️⃣ هشدار تداخل‌ها")
        st.markdown(R.duplicates_html(a.duplicates), unsafe_allow_html=True)
        st.markdown(R.pairs_html(a.pairs), unsafe_allow_html=True)

        st.markdown("#### 🍽️ تداخل با مواد غذایی")
        st.markdown(R.foods_html(a.foods), unsafe_allow_html=True)
        st.markdown(R.red_flags_html(a.red_flags), unsafe_allow_html=True)

        st.markdown("### ۲️⃣ جدول زمانی مصرف")
        st.markdown(R.schedule_table_html(s.rows), unsafe_allow_html=True)
        st.markdown(R.conflicts_html([{"conflict_fa": c} for c in s.conflicts]), unsafe_allow_html=True)
        st.markdown(R.empty_stomach_html(s.empty_conflicts), unsafe_allow_html=True)
        sp = R.spacing_html(s.spacing_tips)
        if sp:
            st.markdown("#### ⏱️ داروهای نیاز به فاصله‌گذاری")
            st.markdown(sp, unsafe_allow_html=True)

        st.markdown("### ۴️⃣ راهنمای دوز فراموش‌شده")
        st.markdown(R.missed_dose_html(m), unsafe_allow_html=True)

        # دانلود جدول متنی
        lines = ["برنامه مصرف دارو", "=" * 30]
        for r in s.rows:
            lines.append(f'{to_fa_digits(r["time"])} | {r["name_fa"]} | {r["food_fa"]} | {r["how_fa"]}')
        st.download_button(
            "⬇️ دانلود جدول مصرف (متن)",
            data="\n".join(lines).encode("utf-8"),
            file_name="barnameh-masraf.txt",
            mime="text/plain",
        )
        st.info("برای ساخت فایل یادآور تقویم، به تب «📅 یادآور تقویم» برو.")
    elif submitted:
        st.warning("اول نام داروها را وارد کن.")

# ─────────────────────────── تب ۲: ICS ───────────────────────────
with tab_ics:
    st.markdown(
        '<div class="card"><h4>📅 ساخت فایل یادآور تقویم (.ics)</h4>'
        "<div class=\"bd\">فایل را بساز و روی گوشی باز کن — مستقیم به تقویم اضافه "
        "می‌شود و سر ساعت زنگ می‌زند. مخصوص داروهای دوره‌ای مثل آمپول هر ۷۲ ساعت "
        "یا قرص هفتگی.</div></div>",
        unsafe_allow_html=True,
    )

    suggested = st.session_state.get("last_names", [])
    if suggested:
        st.caption("داروهای بررسی‌شده: " + "، ".join(suggested))

    n = st.number_input("چند دارو می‌خواهی یادآور بگذاری؟", 1, 8, 1, key="ics_n")
    repeat_labels = {k: v["fa"] for k, v in REPEAT_OPTIONS.items()}

    with st.form("ics_form"):
        events = []
        for i in range(int(n)):
            st.markdown(f"**دارو {to_fa_digits(i + 1)}**")
            c1, c2 = st.columns([2, 1])
            with c1:
                default_name = suggested[i] if i < len(suggested) else ""
                name = st.text_input("نام دارو", value=default_name, key=f"nm{i}")
            with c2:
                tm = st.time_input("ساعت یادآور", value=None, key=f"tm{i}")
            c3, c4 = st.columns(2)
            with c3:
                sd = st.date_input("تاریخ شروع", value=date.today(), key=f"sd{i}")
            with c4:
                rep = st.selectbox(
                    "فاصله تکرار",
                    options=list(REPEAT_OPTIONS),
                    format_func=lambda k: repeat_labels[k],
                    index=list(REPEAT_OPTIONS).index("every_72h"),
                    key=f"rp{i}",
                )
            c5, c6 = st.columns(2)
            with c5:
                cnt = st.number_input(
                    "چند نوبت؟ (۰ = بی‌پایان)", 0, 365, 0, key=f"cn{i}"
                )
            with c6:
                note = st.text_input("یادداشت", value="", key=f"nt{i}",
                                     placeholder="مثلاً: با آب زیاد، بعد از غذا")
            events.append({"name": name, "start_date": sd, "start_time": tm,
                           "repeat": rep, "count": cnt or None, "note": note})
            st.markdown("<hr>", unsafe_allow_html=True)

        alarm = st.select_slider(
            "زنگ چند دقیقه قبل؟",
            options=[0, 5, 10, 15, 30, 60],
            value=10,
            format_func=lambda v: "سر ساعت" if v == 0 else f"{to_fa_digits(v)} دقیقه قبل",
        )
        make = st.form_submit_button("📥 ساخت فایل تقویم")

    if make:
        clean = [e for e in events if (e["name"] or "").strip() and e["start_time"]]
        if not clean:
            st.warning("برای هر دارو حداقل نام و ساعت یادآور لازم است.")
        else:
            for e in clean:
                e["start_time"] = e["start_time"].strftime("%H:%M")
            try:
                payload = ics_bytes(clean, alarm_minutes=int(alarm))
                st.success(
                    f"فایل آماده است — {to_fa_digits(len(clean))} یادآور، "
                    f"حجم {to_fa_digits(len(payload))} بایت."
                )
                st.download_button(
                    "⬇️ دانلود فایل تقویم (.ics)",
                    data=payload,
                    file_name="Med-Assist-reminders.ics",
                    mime="text/calendar",
                )
                for e in clean:
                    st.markdown(
                        f'<div class="chip">💊 {e["name"]} — '
                        f'{to_fa_digits(e["start_time"])} — '
                        f'{repeat_labels[e["repeat"]]}</div>',
                        unsafe_allow_html=True,
                    )
                with st.expander("👀 محتوای فایل"):
                    st.code(payload.decode("utf-8-sig"), language="text")
            except ValueError as exc:
                st.error(f"ساخت فایل ممکن نشد: {exc}")

# ─────────────────────────── تب ۳: بانک دارو ───────────────────────────
with tab_db:
    st.markdown(
        f'<div class="card"><h4>📚 بانک اطلاعاتی لوکال (فول‌بک آفلاین)</h4>'
        f'<div class="bd">{to_fa_digits(len(DRUGS))} داروی پرمصرف ایران برای حالت آفلاین.</div></div>',
        unsafe_allow_html=True,
    )
    q = st.text_input("جستجوی دارو", placeholder="مثلاً: متفورمین یا گلوکوفاژ یا metformin")
    if q.strip():
        from core.normalize import normalize_text

        nq = normalize_text(q)
        hits = [
            (k, v) for k, v in DRUGS.items()
            if nq in normalize_text(v["fa"]) or nq in normalize_text(k)
            or any(nq in normalize_text(b) for b in v["brands_fa"])
            or any(nq in normalize_text(al) for al in v["aliases"])
        ]
        st.caption(f"{to_fa_digits(len(hits))} نتیجه")
        for k, v in hits[:25]:
            brands = "، ".join(v["brands_fa"]) or "—"
            slots = "، ".join(SLOT_FA[s] for s in v["timing"])
            st.markdown(
                f'<div class="card"><h4>{v["fa"]} <span class="badge b-ok">{v["en"]}</span></h4>'
                f'<div class="bd">برندها: {brands}<br>نوبت استاندارد: {slots}<br>'
                f'نحوه مصرف: {v["note_fa"]}</div></div>',
                unsafe_allow_html=True,
            )

st.markdown(
    '<div class="disclaimer">⚠️ <b>این برنامه جایگزین پزشک و داروساز نیست.</b> '
    "اطلاعات آن آموزشی و برای یادآوری است. هیچ دارویی را بر اساس این خروجی قطع، "
    "اضافه یا کم نکن. اگر تداخل خطرناکی دیدی، قبل از هر تغییری با پزشک یا "
    "داروساز خودت حرف بزن.</div>",
    unsafe_allow_html=True,
)
