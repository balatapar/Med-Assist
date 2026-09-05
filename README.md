# دارویار (Daroyar) — دستیار تداخل دارویی و جدول مصرف

اپلیکیشن تحت وب (Streamlit) برای تحلیل تداخل دارویی، ساخت جدول مصرف، یادآور تقویم و راهنمای دوز فراموش‌شده.
تحلیل با **Google Gemini**؛ در صورت قطع اینترنت، **فول‌بک لوکال** فعال می‌شود.

## قابلیت‌ها
- 🔍 **تشخیص هوشمند دارو**: نام فارسی، برند ایرانی، انگلیسی، فینگلیش — همه شناخته می‌شوند
- ⚠️ **تداخل دارو-دارو**: شدت (خطرناک/متوسط/احتیاط)، مکانیزم، اقدام، علائم هشدار
- 🍽️ **تداخل دارو-غذا**: گریپ‌فروت، لبنیات، کافئین، الکل، سبزی برگ‌سبز، و غیره
- 📅 **جدول زمانی**: تفسیر دستور پزشک (BD، q12h، هر ۸ ساعت، شب‌ها...)، نسبت با غذا
- ⏰ **یادآور تقویم (.ics)**: داروهای دوره‌ای (هر ۷۲ ساعت، هفتگی، ماهانه...) با زنگ گوشی
- 📋 **راهنمای دوز فراموش‌شده**: عمومی + اختصاصی هر دارو/کلاس
- 🌐 **RTL کامل**: فونت وزیرمتن (میزبانی محلی، بدون Google Fonts)

## اجرا لوکال
```bash
# پیش‌نیاز: Python 3.12+, uv (یا pip)
uv venv
uv pip install -r requirements.txt

# کلید Gemini (در ویندوز در HKCU\Environment تنظیم شده)
# در لینوکس/مک: export GEMINI_API_KEY=...

streamlit run app.py --server.port 8600
```

## استقرار در Railway (رایگان)
1. این مخزن را به GitHub push کنید
2. در [Railway](https://railway.app) پروژه جدید → Deploy from GitHub
3. متغیرهای محیطی را ست کنید:
   - `GEMINI_API_KEY` = کلید Gemini شما
4. Deploy — Railway خودکار `Dockerfile` را می‌بیند و پورت را ست می‌کند

## استقرار در Koyeb / Render / Fly.io
مشابه Railway — همه از Dockerfile پشتیبانی می‌کنند.

## ساختار پروژه
```
daroyar/
├── app.py                 # اپلیکیشن Streamlit
├── requirements.txt
├── Dockerfile
├── railway.json
├── .github/workflows/deploy.yml
├── core/
│   ├── __init__.py
│   ├── analyzer.py        # لایه یکپارچه: Gemini + لوکال
│   ├── gemini_engine.py   # موتور Gemini (JSON ساختاریافته)
│   ├── interactions.py    # موتور تداخل لوکال
│   ├── normalize.py       # نرمال‌سازی نام دارو
│   ├── schedule.py        # برنامه زمانی لوکال
│   ├── ics.py             # تولید iCalendar
│   ├── render.py          # رندر HTML فارسی
│   └── theme.py           # تم RTL + فونت وزیرمتن
├── data/
│   ├── drugs.json              # ۱۵۰ داروی پرمصرف ایران
│   ├── interactions.json       # ۷۷۶ جفت تداخل لوکال
│   └── food_interactions.json  # ۱۲ گروه غذایی
├── assets/fonts/               # Vazirmatn (woff2)
└── tests/                      # ۴۷ تست pytest
```

## مجوز
MIT License — آزاد برای استفاده، تغییر و توزیع.

---
⚠️ **توضیح مهم**: این برنامه جایگزین پزشک و داروساز نیست. اطلاعات آموزشی و برای یادآوری است.
