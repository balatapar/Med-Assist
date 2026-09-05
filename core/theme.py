"""استایل RTL و فونت وزیرمتن (میزبانی محلی — بدون گوگل فونتس)."""

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
  --bg:#0f1419; --card:#1a2129; --card2:#212b35; --line:#2e3a45;
  --txt:#e8edf2; --muted:#b3a79c; --accent:#4db6ac;
  --danger:#ff6b6b; --danger-bg:#3a1e22; --warn:#ffb74d; --warn-bg:#3a2f1e;
  --info:#64b5f6; --info-bg:#1e2c3a; --ok:#81c784;
}
html,body,[class*="css"],.stApp,button,input,textarea,select{
  font-family:'Vazirmatn',Tahoma,sans-serif !important;
}
.stApp{background:var(--bg);color:var(--txt);}
.main .block-container{max-width:920px;padding-top:1.2rem;padding-bottom:3rem;}
h1,h2,h3,h4,p,li,label,span,div{direction:rtl;text-align:right;}
[data-testid="stHeader"]{background:transparent;}
#MainMenu,footer,[data-testid="stDecoration"]{display:none;}

.hero{background:linear-gradient(135deg,#152028 0%,#1d2b35 100%);
  border:1px solid var(--line);border-radius:18px;padding:22px 24px;margin-bottom:18px;}
.hero h1{margin:0 0 6px;font-size:1.7rem;font-weight:700;}
.hero p{margin:0;color:var(--muted);font-size:.95rem;line-height:1.8;}

.card{background:var(--card);border:1px solid var(--line);border-radius:14px;
  padding:16px 18px;margin-bottom:12px;}
.card h4{margin:0 0 10px;font-size:1.05rem;}

.alert{border-radius:12px;padding:14px 16px;margin-bottom:10px;border-inline-start:5px solid;}
.alert .hd{font-weight:700;font-size:1rem;margin-bottom:6px;}
.alert .bd{font-size:.92rem;line-height:1.9;color:#dbe3ea;}
.alert .sym{margin-top:8px;font-size:.87rem;color:var(--muted);}
.a-danger{background:var(--danger-bg);border-color:var(--danger);}
.a-moderate{background:var(--warn-bg);border-color:var(--warn);}
.a-caution{background:var(--info-bg);border-color:var(--info);}

.badge{display:inline-block;padding:3px 11px;border-radius:999px;font-size:.78rem;
  font-weight:500;margin-inline-end:6px;}
.b-danger{background:var(--danger-bg);color:#ffa8a8;border:1px solid var(--danger);}
.b-moderate{background:var(--warn-bg);color:#ffd28a;border:1px solid var(--warn);}
.b-caution{background:var(--info-bg);color:#a5d3f8;border:1px solid var(--info);}
.b-ok{background:#1e3324;color:#a5d6a7;border:1px solid var(--ok);}

.statgrid{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:10px;margin:4px 0 14px;}
.stat{background:var(--card2);border:1px solid var(--line);border-radius:12px;padding:12px 14px;text-align:center;}
.stat .n{font-size:1.5rem;font-weight:700;line-height:1.3;}
.stat .l{font-size:.8rem;color:var(--muted);}

table.tt{width:100%;border-collapse:separate;border-spacing:0;font-size:.9rem;
  background:var(--card);border:1px solid var(--line);border-radius:12px;overflow:hidden;}
table.tt th{background:var(--card2);padding:11px 10px;text-align:right;font-weight:600;
  color:var(--muted);font-size:.83rem;border-bottom:1px solid var(--line);white-space:nowrap;}
table.tt td{padding:11px 10px;border-bottom:1px solid #262f38;vertical-align:top;line-height:1.75;}
table.tt tr:last-child td{border-bottom:none;}
table.tt td.t{font-weight:700;color:var(--accent);white-space:nowrap;font-variant-numeric:tabular-nums;}
table.tt td.n{font-weight:500;min-width:0;overflow-wrap:anywhere;}

.chips{display:grid;grid-template-columns:repeat(auto-fill,minmax(130px,1fr));gap:8px;}
.chip{background:var(--card2);border:1px solid var(--line);border-radius:10px;
  padding:8px 10px;font-size:.85rem;text-align:center;overflow-wrap:anywhere;}
.chip.miss{border-color:var(--warn);color:#ffd28a;}

.stButton>button,.stDownloadButton>button{width:100%;border-radius:11px;font-weight:600;
  background:var(--accent);color:#06231f;border:none;padding:.6rem 1rem;}
.stButton>button:hover,.stDownloadButton>button:hover{filter:brightness(1.1);}
.stTextArea textarea,.stTextInput input{background:var(--card2)!important;color:var(--txt)!important;
  border:1px solid var(--line)!important;border-radius:11px!important;direction:rtl;text-align:right;}
.stTextArea textarea::placeholder{color:#7d8b98;}
[data-baseweb="select"]>div{background:var(--card2)!important;border-color:var(--line)!important;}
.stTabs [data-baseweb="tab-list"]{gap:4px;direction:rtl;}
.stTabs [data-baseweb="tab"]{background:var(--card);border-radius:10px 10px 0 0;padding:8px 14px;}
[data-testid="stExpander"]{background:var(--card);border:1px solid var(--line);border-radius:12px;}
hr{border-color:var(--line);}

.disclaimer{background:#2a2419;border:1px solid #5c4a1f;border-radius:12px;padding:13px 16px;
  font-size:.86rem;line-height:1.9;color:#e6d7b8;margin-top:18px;}

@media (max-width:600px){
  .main .block-container{padding-inline:.7rem;}
  .hero h1{font-size:1.35rem;}
  table.tt{font-size:.82rem;}
  table.tt th,table.tt td{padding:8px 6px;}
  .two-col{grid-template-columns:1fr!important;}
}
"""


def page_style() -> str:
    return f"<style>\n{font_faces()}\n{CSS}\n</style>"
