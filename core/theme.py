"""استایل RTL و سیستم طراحی دارویی مدرن، گرم، پرانرژی و دسترسی‌پذیر (Contrast & Typography)."""

from __future__ import annotations

import base64
from functools import lru_cache
from pathlib import Path

FONT_DIR = Path(__file__).resolve().parent.parent / "assets" / "fonts"
FONT_WEIGHTS = {"Vazirmatn-Regular.woff2": 400, "Vazirmatn-Medium.woff2": 500, "Vazirmatn-Bold.woff2": 700}


@lru_cache(maxsize=1)
def font_faces() -> str:
    """فونت را base64 تزریق می‌کند چون Streamlit فایل استاتیک دلخواه سرو نمی‌کند."""
    blocks = []
    for fname, weight in FONT_WEIGHTS.items():
        f = FONT_DIR / fname
        if not f.exists():
            continue
        b64 = base64.b64encode(f.read_bytes()).decode("ascii")
        blocks.append(
            "@font-face{font-family:'Vazirmatn';font-style:normal;font-weight:%d;"
            "font-display:swap;src:url(data:font/woff2;base64,%s) format('woff2');}" % (weight, b64)
        )
    return "\n".join(blocks)


CSS = """
:root{
  /* 1. پس‌زمینه کل صفحه */
  --bg-app-start: #f8fafc;
  --bg-app-end: #edf2f7;

  /* 2 & 4. کارت‌ها و نوارهای تیره */
  --surface: #ffffff;
  --surface-header-dark: #1e293b;
  --text-white: #ffffff;

  /* 5. گرادینت مرجانی / دکمه CTA */
  --coral-start: #ff6b6b;
  --coral-end: #ee5253;

  /* 6. باکس هشدار سیترون / خردلی */
  --amber-alert-bg: #fef3c7;
  --amber-alert-text: #b45309;
  --amber-alert-border: #fde68a;

  /* 7. گرادینت سبز کله‌غازی / هدر دارویار */
  --teal-grad-start: #0d9488;
  --teal-grad-end: #059669;

  /* پالت رنگی کمکی و بالینی */
  --navy-slate: #0f172a;
  --text-main: #0f172a;
  --text-body: #334155;
  --text-muted: #64748b;

  --ruby-danger: #f43f5e;
  --ruby-bg: #fff1f2;
  --ruby-border: #fecdd3;

  --amber-warn: #f59e0b;
  --amber-bg: #fffbeb;
  --amber-border: #fde68a;

  --citrus-food: #ea580c;
  --citrus-bg: #fff7ed;
  --citrus-border: #fed7aa;

  --lavender-dup: #8b5cf6;
  --lavender-bg: #f5f3ff;
  --lavender-border: #ddd6fe;

  --blue-info: #0284c7;
  --blue-bg: #f0f9ff;
  --blue-border: #bae6fd;

  --border-subtle: #e2e8f0;
  --shadow-sm: 0 2px 8px rgba(15, 23, 42, 0.05);
  --shadow-card: 0 10px 25px -5px rgba(0, 0, 0, 0.06), 0 4px 6px -2px rgba(0, 0, 0, 0.03);
}

html,body,[class*="css"],.stApp,button,input,textarea,select{
  font-family:'Vazirmatn',Tahoma,sans-serif !important;
}

/* 1. پس‌زمینه کل صفحه: گرادینت نرم از #f8fafc به #edf2f7 */
.stApp{
  background-color: var(--bg-app-start) !important;
  background-image: linear-gradient(180deg, #f8fafc 0%, #edf2f7 100%) !important;
  background-attachment: fixed !important;
  color: var(--text-main);
  min-height: 100vh;
}

/* ریسپانسیو محتوا */
.main .block-container{
  max-width: 1260px;
  width: 94%;
  margin-inline: auto;
  padding-top: 2rem;
  padding-bottom: 5rem;
  padding-inline: 1.5rem;
}

@media (min-width: 1400px){
  .main .block-container{
    max-width: 1440px;
    width: 90%;
    padding-inline: 2.5rem;
  }
}

/* RTL Scoped */
.hero,.card,.alert,.badge,.chip,.stat,.disclaimer,table.tt,.statgrid,.chips,
.main [data-testid="stMarkdownContainer"] p,
.main [data-testid="stMarkdownContainer"] li,
.main [data-testid="stMarkdownContainer"] h1,
.main [data-testid="stMarkdownContainer"] h2,
.main [data-testid="stMarkdownContainer"] h3,
.main [data-testid="stMarkdownContainer"] h4,
[data-testid="stExpanderSummary"],
.stCaption,
label[for],
.stTextInput label,
.stTextArea label,
.stNumberInput label,
.stSelectbox label,
.stForm label,
[data-testid="stBlockContainer"] .stCaption{
  direction: rtl;
  text-align: right;
}

[data-testid="stHeader"]{ background: transparent; }
#MainMenu,footer,[data-testid="stDecoration"]{ display: none; }

/* Section Headings */
.main [data-testid="stMarkdownContainer"] h3{
  margin-top: 2.5rem !important;
  margin-bottom: 1.2rem !important;
  font-size: 1.55rem !important;
  font-weight: 800 !important;
  color: var(--navy-slate) !important;
  display: flex;
  align-items: center;
  gap: 12px;
}

.main [data-testid="stMarkdownContainer"] h4{
  margin-top: 1.8rem !important;
  margin-bottom: 1rem !important;
  font-size: 1.25rem !important;
  font-weight: 700 !important;
  color: var(--navy-slate) !important;
}

/* 7. هدر اصلی دارویار: گرادینت سبز کله‌غازی شاداب (#0d9488 تا #059669) با متن سفید */
.hero{
  background: linear-gradient(135deg, #0d9488 0%, #059669 100%) !important;
  border-radius: 18px !important;
  padding: 36px 42px;
  margin-bottom: 30px;
  box-shadow: 0 16px 30px -8px rgba(13, 148, 136, 0.35), 0 0 0 1px rgba(255, 255, 255, 0.2) inset !important;
  position: relative;
  overflow: hidden;
  color: #ffffff !important;
}

.hero::after{
  content: "";
  position: absolute;
  top: -40px;
  left: -40px;
  width: 240px;
  height: 240px;
  background: radial-gradient(circle, rgba(255, 255, 255, 0.22) 0%, transparent 70%);
  pointer-events: none;
}

.hero h1{
  margin: 0 0 10px;
  font-size: 3rem !important;
  font-weight: 900 !important;
  color: #ffffff !important;
  letter-spacing: -0.5px;
  line-height: 1.2;
  text-shadow: 0 2px 10px rgba(0, 0, 0, 0.25);
}

.hero p{
  margin: 0;
  color: #ffffff !important;
  font-size: 1.12rem;
  line-height: 2.1;
  max-width: 920px;
  font-weight: 500;
  text-shadow: 0 1px 4px rgba(0, 0, 0, 0.15);
}

/* 2 & 4. کارت تنظیمات و نوار تایتل آکاردئون */
[data-testid="stExpander"]{
  background: #ffffff !important;
  border: 1px solid #e2e8f0 !important;
  border-radius: 16px !important;
  box-shadow: var(--shadow-card) !important;
  margin-bottom: 24px !important;
  overflow: hidden !important;
}

/* 2. نوار تایتل آکاردئون: پس‌زمینه #1e293b و متن کاملاً سفید #ffffff */
[data-testid="stExpanderSummary"],
summary.st-emotion-cache-1s4g1qq,
[data-testid="stExpander"] summary{
  background: #1e293b !important;
  color: #ffffff !important;
  font-size: 1.1rem !important;
  font-weight: 800 !important;
  padding: 16px 22px !important;
  border-radius: 14px 14px 0 0 !important;
  border-bottom: 1px solid #334155 !important;
}

[data-testid="stExpanderSummary"] span,
[data-testid="stExpanderSummary"] p,
[data-testid="stExpanderSummary"] div,
[data-testid="stExpanderSummary"] svg,
[data-testid="stExpander"] summary span,
[data-testid="stExpander"] summary p,
[data-testid="stExpander"] summary div,
[data-testid="stExpander"] summary svg{
  color: #ffffff !important;
  fill: #ffffff !important;
}

/* 4. بدنه کارت اصلی تنظیمات: سفید یک‌دست با پدینگ مناسب */
[data-testid="stExpanderDetails"]{
  background: #ffffff !important;
  padding: 22px 26px 26px !important;
  color: #1e293b !important;
}

[data-testid="stExpanderDetails"] label,
[data-testid="stExpanderDetails"] p,
[data-testid="stExpanderDetails"] span{
  color: #1e293b !important;
}

/* 3. دکمه چشم پسورد: پس‌زمینه کاملاً شفاف، حذف کادر سیاه، آیکون #64748b */
[data-testid="stTextInput"] button,
div[data-baseweb="input"] button,
.stTextInput button{
  background: transparent !important;
  background-color: transparent !important;
  border: none !important;
  box-shadow: none !important;
  color: #64748b !important;
}

[data-testid="stTextInput"] button svg,
div[data-baseweb="input"] button svg,
.stTextInput button svg{
  fill: #64748b !important;
  color: #64748b !important;
}

[data-testid="stTextInput"] button:hover,
div[data-baseweb="input"] button:hover,
.stTextInput button:hover{
  background: rgba(100, 116, 139, 0.08) !important;
}

/* 5. دکمه‌های بخش کلید: دکمه ذخیره در لینک با گرادینت مرجانی */
.key-btns{
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin: 16px 0 8px;
  width: 100%;
}

.key-btns>div{ width: 100% !important; }

.key-btns .stButton>button{
  width: 100% !important;
  background: #f8fafc !important;
  color: #0f172a !important;
  border: 1.5px solid #cbd5e1 !important;
  border-radius: 14px !important;
  font-size: 1rem !important;
  font-weight: 700 !important;
  white-space: normal !important;
  line-height: 1.8;
  padding: .85rem 1.2rem !important;
  text-align: right;
  box-shadow: var(--shadow-sm) !important;
}

.key-btns .stButton>button:hover{
  background: #f0fdfa !important;
  border-color: var(--teal-grad-start) !important;
  color: var(--teal-grad-start) !important;
  box-shadow: 0 6px 18px -2px rgba(13, 148, 136, 0.25) !important;
  transform: translateY(-2px) !important;
}

/* 5. دکمه اول (ذخیره در لینک): گرادینت مرجانی/قرمز #ff6b6b به #ee5253 با متن سفید */
[data-testid="stExpanderDetails"] .stButton:first-of-type > button{
  background: linear-gradient(135deg, #ff6b6b 0%, #ee5253 100%) !important;
  color: #ffffff !important;
  border: none !important;
  box-shadow: 0 8px 20px -4px rgba(238, 82, 83, 0.45) !important;
}

[data-testid="stExpanderDetails"] .stButton:first-of-type > button:hover{
  box-shadow: 0 12px 25px -4px rgba(238, 82, 83, 0.6) !important;
  filter: brightness(1.05) !important;
  color: #ffffff !important;
  transform: translateY(-2px) !important;
}

/* 6. باکس هشدار/اطلاعیه: پس‌زمینه #fef3c7، متن و کادر #b45309 */
[data-testid="stAlert"],
.stAlert{
  background-color: #fef3c7 !important;
  color: #b45309 !important;
  border: 1.5px solid #fde68a !important;
  border-inline-start: 6px solid #b45309 !important;
  border-radius: 14px !important;
  box-shadow: 0 4px 14px rgba(180, 83, 9, 0.08) !important;
  padding: 16px 20px !important;
}

[data-testid="stAlert"] *,
.stAlert *{
  color: #b45309 !important;
}

[data-testid="stAlert"] svg,
.stAlert svg{
  fill: #b45309 !important;
  color: #b45309 !important;
}

/* کارت‌های آماری */
.statgrid{
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(210px, 1fr));
  gap: 18px;
  margin: 18px 0 28px;
}

.stat{
  background: #ffffff;
  border-radius: 16px;
  padding: 22px 20px;
  text-align: center;
  position: relative;
  overflow: hidden;
  border: 1px solid var(--border-subtle);
  box-shadow: var(--shadow-card);
  transition: transform .2s ease, box-shadow .2s ease;
}

.stat:hover{
  transform: translateY(-4px);
  box-shadow: 0 16px 30px -6px rgba(0, 0, 0, 0.1);
}

.stat .ico{
  font-size: 1.8rem;
  margin-bottom: 6px;
}

.stat .n{
  font-size: 2.5rem;
  font-weight: 900;
  line-height: 1.15;
  letter-spacing: -0.5px;
}

.stat .l{
  font-size: .95rem;
  font-weight: 700;
  color: var(--text-muted);
  margin-top: 6px;
}

.stat.stat-blue{
  border-color: #bae6fd;
  background: linear-gradient(180deg, #f0f9ff 0%, #ffffff 100%);
}
.stat.stat-blue .n{ color: #0284c7; }

.stat.stat-danger{
  border-color: #fecdd3;
  background: linear-gradient(180deg, #fff1f2 0%, #ffffff 100%);
}
.stat.stat-danger .n{ color: #f43f5e; }

.stat.stat-warn{
  border-color: #fde68a;
  background: linear-gradient(180deg, #fffbeb 0%, #ffffff 100%);
}
.stat.stat-warn .n{ color: #f59e0b; }

.stat.stat-orange{
  border-color: #fed7aa;
  background: linear-gradient(180deg, #fff7ed 0%, #ffffff 100%);
}
.stat.stat-orange .n{ color: #ea580c; }

/* کارت‌های هشدار تخصصی تداخلات */
.alert{
  border-radius: 16px;
  padding: 20px 24px;
  margin-bottom: 18px;
  box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.06);
  transition: transform .18s ease;
}

.alert:hover{
  transform: translateX(-3px);
}

.alert .hd{
  font-weight: 800;
  font-size: 1.15rem;
  margin-bottom: 10px;
  display: flex;
  align-items: center;
  gap: 10px;
}

.alert .bd{
  font-size: 1rem;
  line-height: 2;
  color: #334155;
}

.alert .sym{
  margin-top: 12px;
  padding-top: 10px;
  border-top: 1px solid rgba(0, 0, 0, 0.08);
  font-size: .95rem;
  font-weight: 700;
}

.a-danger{
  background: #fff1f2;
  border: 1px solid #fecdd3;
  border-inline-start: 6px solid #f43f5e;
}
.a-danger .hd{ color: #9f1239; }
.a-danger .sym{ color: #be123c; }

.a-moderate{
  background: #fffbeb;
  border: 1px solid #fde68a;
  border-inline-start: 6px solid #f59e0b;
}
.a-moderate .hd{ color: #92400e; }
.a-moderate .sym{ color: #b45309; }

.a-duplicate{
  background: #f5f3ff;
  border: 1px solid #ddd6fe;
  border-inline-start: 6px solid #8b5cf6;
}
.a-duplicate .hd{ color: #5b21b6; }
.a-duplicate .sym{ color: #6d28d9; }

.a-food{
  background: #fff7ed;
  border: 1px solid #fed7aa;
  border-inline-start: 6px solid #ea580c;
}
.a-food .hd{ color: #9a3412; }

.a-safe{
  background: #ecfdf5;
  border: 1px solid #a7f3d0;
  border-inline-start: 6px solid #10b981;
}
.a-safe .hd{ color: #065f46; }

/* کارت‌های عمومی */
.card{
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 16px;
  padding: 24px 28px;
  margin-bottom: 22px;
  box-shadow: var(--shadow-card);
  transition: transform .2s ease, box-shadow .2s ease;
}

.card:hover{
  transform: translateY(-2px);
  box-shadow: 0 14px 28px -4px rgba(0, 0, 0, 0.1);
}

.card h4{
  margin: 0 0 14px;
  font-size: 1.25rem;
  font-weight: 800;
  color: #0f766e !important;
  letter-spacing: -0.2px;
}

.card .bd{
  font-size: 1.02rem;
  line-height: 2;
  color: #334155;
}

.card.c-purple{
  background: linear-gradient(180deg, #f5f3ff 0%, #ffffff 100%);
  border-color: #ddd6fe;
}
.card.c-purple h4{ color: #7c3aed !important; }

.card.c-food{
  background: linear-gradient(180deg, #fff7ed 0%, #ffffff 100%);
  border-color: #fed7aa;
}
.card.c-food h4{ color: #ea580c !important; }

.card.c-warn{
  background: linear-gradient(180deg, #fffbeb 0%, #ffffff 100%);
  border-color: #fde68a;
}
.card.c-warn h4{ color: #d97706 !important; }

.card.c-info{
  background: linear-gradient(180deg, #f0f9ff 0%, #ffffff 100%);
  border-color: #bae6fd;
}
.card.c-info h4{ color: #0284c7 !important; }

/* بج‌ها */
.badge{
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 16px;
  border-radius: 999px;
  font-size: .88rem;
  font-weight: 700;
  margin-inline-end: 8px;
  margin-bottom: 8px;
  box-shadow: 0 2px 6px rgba(15, 23, 42, 0.06);
}
.b-danger{ background: #fff1f2; color: #e11d48; border: 1px solid #fecdd3; }
.b-moderate{ background: #fffbeb; color: #b45309; border: 1px solid #fde68a; }
.b-caution{ background: #fffbeb; color: #b45309; border: 1px solid #fde68a; }
.b-ok{ background: #ecfdf5; color: #047857; border: 1px solid #a7f3d0; }
.b-info{ background: #f0f9ff; color: #0369a1; border: 1px solid #bae6fd; }
.b-purple{ background: #f5f3ff; color: #6d28d9; border: 1px solid #ddd6fe; }

/* جدول مصرف */
table.tt{
  width: 100%;
  border-collapse: separate;
  border-spacing: 0;
  font-size: 1rem;
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 16px;
  overflow: hidden;
  box-shadow: var(--shadow-card);
  margin-bottom: 26px;
}

table.tt th{
  background: #f1f5f9;
  padding: 16px 20px;
  text-align: right;
  font-weight: 800;
  color: var(--navy-slate);
  font-size: .95rem;
  border-bottom: 2px solid #e2e8f0;
  white-space: nowrap;
}

table.tt td{
  padding: 16px 20px;
  border-bottom: 1px solid #f1f5f9;
  vertical-align: middle;
  line-height: 1.95;
  color: #334155;
}

table.tt tr:hover td{ background: #f8fafc; }
table.tt tr:last-child td{ border-bottom: none; }

.time-badge{
  display: inline-block;
  background: #ccfbf1;
  color: #0f766e;
  border: 1px solid #99f6e4;
  padding: 4px 12px;
  border-radius: 8px;
  font-weight: 800;
  font-size: 1.05rem;
  font-variant-numeric: tabular-nums;
}

table.tt td.n{
  font-weight: 800;
  color: #0f172a;
  font-size: 1.08rem;
}

.slot-pill{
  display: inline-block;
  padding: 4px 12px;
  border-radius: 999px;
  font-size: .88rem;
  font-weight: 700;
}
.slot-morning{ background: #fef3c7; color: #92400e; border: 1px solid #fde68a; }
.slot-noon{ background: #e0f2fe; color: #0369a1; border: 1px solid #bae6fd; }
.slot-evening{ background: #ffedd5; color: #9a3412; border: 1px solid #fed7aa; }
.slot-night{ background: #ede9fe; color: #5b21b6; border: 1px solid #ddd6fe; }
.slot-default{ background: #f1f5f9; color: #475569; border: 1px solid #e2e8f0; }

ul.bullet-list{
  margin: 0;
  padding-right: 20px;
}
ul.bullet-list li{
  margin-bottom: 8px;
  line-height: 1.9;
}

/* دکمه‌های عمومی و دانلود */
.stButton>button{
  width: 100%;
  border-radius: 14px !important;
  font-weight: 800 !important;
  background: linear-gradient(135deg, #0d9488 0%, #059669 100%) !important;
  color: #ffffff !important;
  border: none !important;
  padding: .85rem 1.6rem !important;
  font-size: 1.08rem !important;
  box-shadow: 0 8px 20px -4px rgba(13, 148, 136, 0.45) !important;
  transition: all .2s cubic-bezier(0.16, 1, 0.3, 1) !important;
  cursor: pointer;
}

.stButton>button:hover{
  transform: translateY(-2px) !important;
  box-shadow: 0 14px 28px -4px rgba(13, 148, 136, 0.6) !important;
  filter: brightness(1.06) !important;
  color: #ffffff !important;
}

[data-testid="stForm"] .stButton>button{
  background: linear-gradient(135deg, #f43f5e 0%, #e11d48 50%, #f59e0b 100%) !important;
  box-shadow: 0 8px 20px -4px rgba(244, 63, 94, 0.45) !important;
  color: #ffffff !important;
  font-size: 1.15rem !important;
}

[data-testid="stForm"] .stButton>button:hover{
  box-shadow: 0 14px 28px -4px rgba(244, 63, 94, 0.65) !important;
  filter: brightness(1.06) !important;
  color: #ffffff !important;
}

.stDownloadButton>button{
  width: 100%;
  border-radius: 14px !important;
  font-weight: 800 !important;
  background: linear-gradient(135deg, #0d9488 0%, #059669 100%) !important;
  color: #ffffff !important;
  border: none !important;
  padding: .85rem 1.6rem !important;
  font-size: 1.08rem !important;
  box-shadow: 0 8px 20px -4px rgba(13, 148, 136, 0.45) !important;
  transition: all .2s ease !important;
}

.stDownloadButton>button:hover{
  transform: translateY(-2px) !important;
  box-shadow: 0 14px 28px -4px rgba(13, 148, 136, 0.6) !important;
  color: #ffffff !important;
}

/* تب‌ها */
.stTabs [data-baseweb="tab-list"]{
  gap: 10px;
  direction: rtl;
  border-bottom: 2px solid #e2e8f0;
  padding-bottom: 6px;
  margin-bottom: 22px;
}

.stTabs [data-baseweb="tab"]{
  background: #ffffff !important;
  border-radius: 14px 14px 0 0 !important;
  padding: 12px 26px !important;
  font-size: 1.05rem !important;
  font-weight: 700 !important;
  border: 1.5px solid #e2e8f0 !important;
  border-bottom: none !important;
  color: #475569 !important;
  box-shadow: 0 -2px 8px rgba(0, 0, 0, 0.03) !important;
  transition: all .2s ease !important;
}

.stTabs [data-baseweb="tab"] p,
.stTabs [data-baseweb="tab"] span{
  color: #475569 !important;
}

.stTabs [data-baseweb="tab"]:hover{
  background: #f0fdfa !important;
  color: #0d9488 !important;
}

.stTabs [aria-selected="true"]{
  background: linear-gradient(135deg, #0d9488 0%, #059669 100%) !important;
  color: #ffffff !important;
  font-weight: 800 !important;
  border-color: #0d9488 !important;
  box-shadow: 0 6px 18px rgba(13, 148, 136, 0.35) !important;
}

.stTabs [aria-selected="true"] p,
.stTabs [aria-selected="true"] span{
  color: #ffffff !important;
}

/* فیلدهای ورودی */
.stTextArea textarea,
.stTextInput input,
.stNumberInput input{
  background: #ffffff !important;
  color: #0f172a !important;
  border: 2px solid #cbd5e1 !important;
  border-radius: 14px !important;
  direction: rtl;
  text-align: right;
  padding: .85rem 1.1rem !important;
  font-size: 1rem !important;
  box-shadow: 0 2px 5px rgba(0, 0, 0, 0.04) inset !important;
  transition: border-color .2s ease, box-shadow .2s ease !important;
}

.stTextArea textarea::placeholder,
.stTextInput input::placeholder{
  color: #64748b !important;
  opacity: 1 !important;
}

.stTextArea textarea:focus,
.stTextInput input:focus,
.stNumberInput input:focus{
  border-color: #0d9488 !important;
  box-shadow: 0 0 0 4px rgba(13, 148, 136, 0.2) !important;
}

/* لیبل‌ها و کپشن‌ها: همیشه تیره و خوانا — در هیچ مرورگر/حالتی محو نمی‌شوند */
[data-testid="stWidgetLabel"] p,
.stCheckbox label p,
.stRadio label p{
  color: #0f172a !important;
  font-weight: 700 !important;
}

.stCaption,
[data-testid="stCaptionContainer"],
[data-testid="stCaptionContainer"] p{
  color: #475569 !important;
}

/* چیپ‌ها */
.chips{
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 12px;
}

.chip{
  background: #ffffff;
  border: 1.5px solid #e2e8f0;
  border-radius: 14px;
  padding: 12px 16px;
  font-size: .95rem;
  font-weight: 700;
  text-align: center;
  overflow-wrap: anywhere;
  box-shadow: 0 4px 10px rgba(0, 0, 0, 0.05);
  color: #0f172a;
  transition: transform .15s ease, box-shadow .15s ease;
}

.chip:hover{
  transform: translateY(-2px);
  box-shadow: 0 8px 16px rgba(0, 0, 0, 0.08);
}

.chip.miss{
  border-color: #fde68a;
  color: #92400e;
  background: #fffbeb;
}

/* سلب مسئولیت */
.disclaimer{
  background: linear-gradient(135deg, #fffbeb 0%, #fef3c7 100%);
  border: 1.5px solid #fde68a;
  border-radius: 16px;
  padding: 22px 26px;
  font-size: .98rem;
  line-height: 2.1;
  color: #92400e;
  margin-top: 36px;
  box-shadow: 0 6px 16px rgba(245, 158, 11, 0.08);
}

/* موبایل */
@media (max-width: 680px){
  .main .block-container{
    width: 100%;
    padding-inline: 1rem;
    padding-top: 1.4rem;
  }
  .hero{
    padding: 26px 22px;
    border-radius: 18px;
  }
  .hero h1{
    font-size: 2.3rem !important;
  }
  .hero p{
    font-size: 1.05rem;
    line-height: 2;
  }
  .statgrid{
    grid-template-columns: repeat(2, 1fr);
    gap: 12px;
  }
  .stat{ padding: 18px 14px; border-radius: 14px; }
  .stat .n{ font-size: 2rem; }
  table.tt{ font-size: .9rem; border-radius: 14px; }
  table.tt th, table.tt td{ padding: 12px 10px; }
}
"""


def page_style() -> str:
    return f"<style>\n{font_faces()}\n{CSS}\n</style>"
