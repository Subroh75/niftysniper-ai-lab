import streamlit as st
import pandas as pd
import numpy as np
import requests
import json
from datetime import datetime, timedelta
from anthropic import Anthropic
import hashlib
import xml.etree.ElementTree as ET
import yfinance as yf

# ── Page config ───────────────────────────────────────────────────────────────
# ── NSE Symbol lookup ────────────────────────────────────────────────────
NSE_LOOKUP = {
    "reliance":"RELIANCE","reliance industries":"RELIANCE",
    "tata consultancy":"TCS","tcs":"TCS","tata consultancy services":"TCS",
    "hdfc bank":"HDFCBANK","hdfcbank":"HDFCBANK","hdfc":"HDFCBANK",
    "infosys":"INFY","infy":"INFY",
    "icici bank":"ICICIBANK","icici":"ICICIBANK",
    "state bank":"SBIN","sbi":"SBIN","state bank of india":"SBIN",
    "kotak":"KOTAKBANK","kotak mahindra":"KOTAKBANK","kotak bank":"KOTAKBANK",
    "bharti airtel":"BHARTIARTL","airtel":"BHARTIARTL",
    "hindustan unilever":"HINDUNILVR","hul":"HINDUNILVR",
    "axis bank":"AXISBANK","axis":"AXISBANK",
    "larsen":"LT","larsen toubro":"LT","l&t":"LT","l and t":"LT",
    "maruti":"MARUTI","maruti suzuki":"MARUTI",
    "hcl":"HCLTECH","hcl technologies":"HCLTECH","hcl tech":"HCLTECH",
    "bajaj finance":"BAJFINANCE","bajaj fin":"BAJFINANCE",
    "wipro":"WIPRO","titan":"TITAN","titan company":"TITAN",
    "sun pharma":"SUNPHARMA","sun pharmaceutical":"SUNPHARMA",
    "ntpc":"NTPC","tata motors":"TATAMOTORS","tata steel":"TATASTEEL",
    "tech mahindra":"TECHM","cipla":"CIPLA",
    "dr reddy":"DRREDDY","dr reddys":"DRREDDY",
    "apollo hospitals":"APOLLOHOSP","apollo hospital":"APOLLOHOSP",
    "bajaj finserv":"BAJAJFINSV","jsw steel":"JSWSTEEL","jsw":"JSWSTEEL",
    "hindalco":"HINDALCO","nestle":"NESTLEIND","nestle india":"NESTLEIND",
    "divis":"DIVISLAB","divis laboratories":"DIVISLAB",
    "eicher":"EICHERMOT","eicher motors":"EICHERMOT","royal enfield":"EICHERMOT",
    "bpcl":"BPCL","bharat petroleum":"BPCL","coal india":"COALINDIA",
    "hero moto":"HEROMOTOCO","hero motocorp":"HEROMOTOCO",
    "britannia":"BRITANNIA","indusind":"INDUSINDBK","indusind bank":"INDUSINDBK",
    "tata consumer":"TATACONSUM","grasim":"GRASIM",
    "asian paints":"ASIANPAINT","ultratech":"ULTRACEMCO","ultratech cement":"ULTRACEMCO",
    "ongc":"ONGC","itc":"ITC","itc limited":"ITC",
    "adani enterprises":"ADANIENT","adani ports":"ADANIPORTS",
    "trent":"TRENT","zomato":"ZOMATO","bajaj auto":"BAJAJ-AUTO",
    "shriram finance":"SHRIRAMFIN","bel":"BEL","bharat electronics":"BEL",
    "power grid":"POWERGRID","nifty":"NIFTY50","nifty 50":"NIFTY50",
    "bank nifty":"BANKNIFTY","sensex":"SENSEX",
    "pidilite":"PIDILITIND","havells":"HAVELLS","siemens":"SIEMENS",
    "abb":"ABB","polycab":"POLYCAB","dlf":"DLF",
    "marico":"MARICO","pfc":"PFC","rec":"RECLTD",
    "tata power":"TATAPOWER","bank of baroda":"BANKBARODA","bob":"BANKBARODA",
    "lupin":"LUPIN","muthoot":"MUTHOOTFIN","muthoot finance":"MUTHOOTFIN",
    "naukri":"NAUKRI","info edge":"NAUKRI","bosch":"BOSCHLTD",
}
def resolve_symbol(raw):
    cleaned = raw.strip().lower()
    if cleaned in NSE_LOOKUP:
        return NSE_LOOKUP[cleaned]
    for key, ticker in NSE_LOOKUP.items():
        if cleaned in key or key in cleaned:
            return ticker
    return raw.strip().upper()

st.set_page_config(
    page_title="Nifty Sniper",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Styling ───────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;600&display=swap');
    * { font-family: 'Space Grotesk', sans-serif; }
.main { background: #080808; }
.stApp { background: #080808; color: #cccccc; }
#MainMenu, footer, header { visibility: hidden; }

/* Force all Streamlit default text to be readable */
.stApp p, .stApp span, .stApp div, .stApp label { color: #cccccc; }
.stMarkdown { color: #cccccc; }

.hero {
    background: linear-gradient(135deg, #0a0500 0%, #111111 60%, #0a0500 100%);
    border: 1px solid #ff660022; border-top: 2px solid #ff6600;
    border-radius: 10px; padding: 32px; margin-bottom: 24px;
    text-align: center; box-shadow: 0 0 40px #ff660011;
}
.hero h1 {
    font-size: 2rem; font-weight: 700; color: #ff6600;
    letter-spacing: 0.1em; text-transform: uppercase;
    margin: 0 0 8px 0; font-family: 'JetBrains Mono', monospace;
}
.hero p { color: #999999; font-size: 0.8rem; letter-spacing: 0.15em; text-transform: uppercase; margin: 0; }

.metric-card {
    background: #111; border: 1px solid #222; border-radius: 8px;
    padding: 14px; text-align: center; transition: border-color 0.2s;
}
.metric-card:hover { border-color: #ff660055; }
.metric-label { color: #777; font-size: 0.7rem; font-weight: 600; letter-spacing: 0.1em; text-transform: uppercase; margin-bottom: 6px; }
.metric-value { font-size: 1.4rem; font-weight: 700; color: #ffffff; font-family: 'JetBrains Mono', monospace; }
.metric-sub { color: #666; font-size: 0.72rem; margin-top: 4px; }

.signal-bull { color: #00c851 !important; }
.signal-bear { color: #ff4444 !important; }
.signal-neutral { color: #ffaa00 !important; }

.section-card { background: #111; border: 1px solid #1a1a1a; border-radius: 8px; padding: 20px; margin-bottom: 16px; }
.section-title {
    color: #ff6600; font-size: 0.72rem; font-weight: 600;
    letter-spacing: 0.12em; text-transform: uppercase;
    margin-bottom: 14px; padding-bottom: 10px;
    border-bottom: 1px solid #ff660022;
    font-family: 'JetBrains Mono', monospace;
}

.agent-msg {
    background: #0d0d0d; border-left: 3px solid #ff6600;
    border-radius: 0 6px 6px 0; padding: 12px 16px;
    margin-bottom: 10px; color: #cccccc; font-size: 0.875rem; line-height: 1.8; font-family: 'Space Grotesk', sans-serif; letter-spacing: 0.01em;
}
.agent-name {
    font-size: 0.7rem; font-weight: 600; letter-spacing: 0.1em;
    text-transform: uppercase; margin-bottom: 6px;
    font-family: 'JetBrains Mono', monospace;
}
.agent-bull .agent-msg  { border-left-color: #00c851; }
.agent-bear .agent-msg  { border-left-color: #ff4444; }
.agent-trader .agent-msg{ border-left-color: #ffaa00; }
.agent-risk .agent-msg  { border-left-color: #3399ff; }
.agent-fund .agent-msg  { border-left-color: #aa88ff; }

.news-item {
    background: #0d0d0d; border: 1px solid #1a1a1a;
    border-left: 2px solid #ff660044;
    border-radius: 0 6px 6px 0; padding: 12px; margin-bottom: 8px;
}
.news-headline { color: #e2e8f0; font-size: 0.875rem; font-weight: 500; }
.news-meta { color: #666; font-size: 0.75rem; margin-top: 4px; }

.news-tag { font-size: 9px; padding: 2px 7px; border-radius: 3px; font-weight: 600; text-transform: uppercase; }
.news-sentiment-pos { background: #00c85122; color: #00c851; border: 1px solid #00c85133; }
.news-sentiment-neg { background: #ff444422; color: #ff4444; border: 1px solid #ff444433; }
.news-sentiment-neu { background: #1f1f1f; color: #9ca3af; border: 1px solid #2a2a2a; }
.news-source { color: #666; }
.news-time { color: #555; }

.fund-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; margin-bottom: 12px; }
.fund-item { background: #0d0d0d; border: 1px solid #1a1a1a; border-radius: 6px; padding: 10px 12px; }
.fund-label { color: #555; font-size: 0.62rem; font-weight: 600; letter-spacing: 0.1em; text-transform: uppercase; margin-bottom: 4px; font-family: 'JetBrains Mono',monospace; }
.fund-value { color: #e2e8f0; font-size: 1rem; font-weight: 600; font-family: 'JetBrains Mono',monospace; }
.fund-value.good { color: #00c851; }
.fund-value.warn { color: #ffaa00; }
.fund-value.bad  { color: #ff4444; }
.fund-section-head { color: #444; font-size: 0.62rem; font-weight: 600; letter-spacing: 0.12em; text-transform: uppercase; margin: 12px 0 7px; font-family: 'JetBrains Mono',monospace; border-top: 1px solid #1a1a1a; padding-top: 10px; }

.score-bar-bg { background: #1a1a1a; border-radius: 2px; height: 4px; margin-top: 8px; }
.score-bar-fill { border-radius: 2px; height: 4px; }

.verdict-box {
    background: linear-gradient(135deg, #0a0500, #111);
    border: 1px solid #ff660033; border-top: 2px solid #ff6600;
    border-radius: 8px; padding: 20px; text-align: center;
    margin-top: 8px; box-shadow: 0 0 20px #ff660011;
}
.verdict-label { color: #777; font-size: 0.7rem; font-weight: 600; letter-spacing: 0.12em; text-transform: uppercase; margin-bottom: 8px; font-family: 'JetBrains Mono', monospace; }
.verdict-text { font-size: 1.8rem; font-weight: 700; font-family: 'JetBrains Mono', monospace; letter-spacing: 0.05em; }

/* ── INPUT: force white text ────────────────────────────── */
[data-testid="stTextInput"] > div > div > input {
    background-color: #1a1a1a !important;
    border: 1px solid #ff660066 !important;
    border-radius: 6px !important;
    color: #ffffff !important;
    -webkit-text-fill-color: #ffffff !important;
    caret-color: #ff6600 !important;
    font-size: 1rem !important;
    padding: 12px 16px !important;
    font-family: 'JetBrains Mono', monospace !important;
    box-shadow: none !important;
}
[data-testid="stTextInput"] > div > div > input:focus {
    border-color: #ff6600 !important;
    box-shadow: 0 0 0 2px #ff660033 !important;
    outline: none !important;
}
[data-testid="stTextInput"] > div > div > input::placeholder {
    color: #555 !important;
    -webkit-text-fill-color: #555 !important;
}

.stDownloadButton > button {
    background: #ff6600 !important;
    color: #000000 !important;
    -webkit-text-fill-color: #000000 !important;
    font-weight: 700 !important;
    border: none !important;
    border-radius: 6px !important;
    padding: 14px 24px !important;
    font-size: 0.9rem !important;
    width: 100% !important;
    letter-spacing: 0.08em !important;
    text-transform: uppercase !important;
    font-family: 'JetBrains Mono', monospace !important;
    transition: background 0.2s !important;
}
.stDownloadButton > button:hover { background: #ff8800 !important; }
.stDownloadButton > button p { color: #000 !important; -webkit-text-fill-color: #000 !important; }
.stButton > button {
    background: #ff6600 !important;
    color: #000000 !important;
    -webkit-text-fill-color: #000000 !important;
    font-weight: 700 !important;
    border: none !important;
    border-radius: 6px !important;
    padding: 12px 24px !important;
    font-size: 0.85rem !important;
    width: 100% !important;
    letter-spacing: 0.08em !important;
    text-transform: uppercase !important;
    font-family: 'JetBrains Mono', monospace !important;
    transition: background 0.2s !important;
}
.stButton > button:hover { background: #ff8800 !important; }
.stButton > button p { color: #000000 !important; -webkit-text-fill-color: #000000 !important; }

hr { border-color: #1a1a1a !important; }
div[data-testid="stHorizontalBlock"] { gap: 10px; }
</style>
""", unsafe_allow_html=True)

# ── Clients ───────────────────────────────────────────────────────────────────
def get_anthropic():
    try:
        key = st.secrets.get("ANTHROPIC_API_KEY", "")
        return Anthropic(api_key=key) if key else None
    except Exception:
        return None

def get_finnhub_key():
    try:
        return st.secrets.get("FINNHUB_API_KEY", "")
    except Exception:
        return ""

# ── Data fetching ─────────────────────────────────────────────────────────────

@st.cache_data(ttl=600, show_spinner=False)
def fetch_bse_filings(symbol: str) -> list:
    """Fetch real BSE filings via BSE India public API."""
    import requests, re
    # Map NSE symbol → BSE security code (common large caps)
    BSE_CODE = {
        "SUNPHARMA":"524715","RELIANCE":"500325","TCS":"532540","HDFCBANK":"500180",
        "INFY":"500209","ICICIBANK":"532174","SBIN":"500112","BAJFINANCE":"500034",
        "AXISBANK":"532215","MARUTI":"532500","HINDUNILVR":"500696","ITC":"500875",
        "WIPRO":"507685","HCLTECH":"532281","TATAMOTORS":"500570","TATASTEEL":"500470",
        "ONGC":"500312","COALINDIA":"533278","BHARTIARTL":"532454","LT":"500510",
        "ADANIENT":"512599","ADANIPORTS":"532921","ASIANPAINT":"500820","TITAN":"500114",
        "NESTLEIND":"500790","ULTRACEMCO":"532538","DRREDDY":"500124","CIPLA":"500087",
        "BAJAJFINSV":"532978","TECHM":"532755","KOTAKBANK":"500247","POWERGRID":"532898",
        "NTPC":"532555","DIVISLAB":"532488","JSWSTEEL":"500228","HINDALCO":"500440",
    }
    code = BSE_CODE.get(symbol.upper(), "")
    results = []
    if code:
        try:
            url = f"https://api.bseindia.com/BseIndAPI/api/AnnSubCategoryGetData/w?pageno=1&strCat=-1&strPrevDate=&strScrip={code}&strSearch=P&strToDate=&strType=C&subcategory=-1"
            resp = requests.get(url, headers={"User-Agent":"Mozilla/5.0","Referer":"https://www.bseindia.com/"}, timeout=8)
            data = resp.json()
            for item in (data.get("Table") or [])[:8]:
                cat  = item.get("CATEGORYNAME","").strip()
                sub  = item.get("SUBCATNAME","").strip()
                head = item.get("HEADLINE","").strip()
                dt   = item.get("News_submission_dt","")[:10]
                link = item.get("ATTACHMENTNAME","")
                if link and not link.startswith("http"):
                    link = f"https://www.bseindia.com/xml-data/corpfiling/AttachLive/{link}"
                results.append({
                    "title": head or sub or cat,
                    "category": cat,
                    "sub": sub,
                    "date": dt,
                    "url": link,
                    "exchange": "BSE",
                })
        except Exception:
            pass

    # Always append yfinance calendar + actions as fallback/supplement
    try:
        tk = yf.Ticker(symbol.upper() + ".NS")
        cal = tk.calendar
        if isinstance(cal, dict):
            ed = cal.get("Earnings Date")
            xd = cal.get("Ex-Dividend Date")
            if ed:
                d = ed[0] if isinstance(ed, list) else ed
                results.append({"title": f"Earnings Date: {str(d)[:10]}", "category": "Results", "sub": "Upcoming", "date": str(d)[:10], "url": "", "exchange": "NSE"})
            if xd:
                results.append({"title": f"Ex-Dividend Date: {str(xd)[:10]}", "category": "Dividend", "sub": "Corporate Action", "date": str(xd)[:10], "url": "", "exchange": "NSE"})
        acts = tk.actions
        if acts is not None and not acts.empty:
            for date, row in acts.tail(3).iloc[::-1].iterrows():
                if row.get("Dividends", 0) > 0:
                    results.append({"title": f"Dividend ₹{row['Dividends']:.2f}/share", "category": "Dividend", "sub": "Corporate Action", "date": str(date)[:10], "url": "", "exchange": "NSE"})
                if row.get("Stock Splits", 0) > 0:
                    results.append({"title": f"Stock Split {row['Stock Splits']}:1", "category": "Corporate Action", "sub": "Split", "date": str(date)[:10], "url": "", "exchange": "NSE"})
    except Exception:
        pass

    return results[:10]


@st.cache_data(ttl=900, show_spinner=False)
def fetch_sentiment(symbol: str) -> dict:
    """Aggregate sentiment from StockTwits + Reddit (no API key needed)."""
    import requests, re, html
    posts = []
    bull, bear, total = 0, 0, 0

    # StockTwits public stream
    try:
        url = f"https://api.stocktwits.com/api/2/streams/symbol/{symbol}.json"
        resp = requests.get(url, timeout=6)
        data = resp.json()
        for m in (data.get("messages") or [])[:10]:
            sent = (m.get("entities",{}).get("sentiment") or {}).get("basic","")
            text = m.get("body","").strip()[:160]
            ts   = m.get("created_at","")[:10]
            if sent == "Bullish": bull += 1
            elif sent == "Bearish": bear += 1
            total += 1
            if text:
                posts.append({"text": text, "sent": sent or "Neutral", "age": ts, "score": m.get("likes",{}).get("total",0)})
    except Exception:
        pass

    # Reddit — search r/IndianStockMarket via old.reddit JSON
    try:
        url = f"https://www.reddit.com/r/IndianStockMarket/search.json?q={symbol}&sort=new&limit=8&restrict_sr=1"
        resp = requests.get(url, headers={"User-Agent":"NiftySniper/1.0"}, timeout=6)
        for p in (resp.json().get("data",{}).get("children") or [])[:5]:
            d = p.get("data",{})
            title = html.unescape(d.get("title",""))[:160]
            score = d.get("score",0)
            created = datetime.fromtimestamp(d.get("created_utc",0)).strftime("%Y-%m-%d")
            # keyword sentiment
            tl = title.lower()
            pos = sum(1 for w in ["surge","rally","buy","bullish","strong","growth","up","positive","good"] if w in tl)
            neg = sum(1 for w in ["fall","crash","bearish","sell","weak","loss","down","negative","bad","risk"] if w in tl)
            sent = "Bullish" if pos > neg else "Bearish" if neg > pos else "Neutral"
            if sent == "Bullish": bull += 1
            elif sent == "Bearish": bear += 1
            total += 1
            posts.append({"text": title, "sent": sent, "age": created, "score": score})
    except Exception:
        pass

    bull_pct  = round(bull / total * 100) if total else 50
    bear_pct  = round(bear / total * 100) if total else 50
    neut_pct  = 100 - bull_pct - bear_pct
    composite = round(bull_pct * 0.7 + (100 - bear_pct) * 0.3)
    if   composite >= 65: verdict = "Bullish"
    elif composite >= 55: verdict = "Moderately Bullish"
    elif composite >= 45: verdict = "Neutral"
    elif composite >= 35: verdict = "Moderately Bearish"
    else:                 verdict = "Bearish"

    # Sort posts by score desc, return top 3
    posts.sort(key=lambda x: x["score"], reverse=True)
    return {
        "composite": composite,
        "bull_pct":  bull_pct,
        "bear_pct":  bear_pct,
        "neut_pct":  neut_pct,
        "verdict":   verdict,
        "social":    bull_pct,
        "retail":    min(100, bull_pct + 5),
        "interest":  min(100, composite + 9),
        "posts":     posts[:3],
        "total":     total,
    }


def render_filings(filings: list, symbol: str):
    """Render BSE filings panel with filter tabs."""
    CAT_TAG = {
        "Results":           ("tag-result",     "Quarterly Result"),
        "Financial Results": ("tag-result",     "Quarterly Result"),
        "Dividend":          ("tag-dividend",   "Dividend"),
        "Board Meeting":     ("tag-board",      "Board Meeting"),
        "Shareholding":      ("tag-regulatory", "Regulatory"),
        "Insider Trading":   ("tag-regulatory", "Regulatory"),
        "Regulatory":        ("tag-regulatory", "Regulatory"),
        "Corporate Action":  ("tag-action",     "Corp Action"),
    }
    def get_tag(cat):
        for k,v in CAT_TAG.items():
            if k.lower() in cat.lower(): return v
        return ("tag-action", "Filing")

    if not filings:
        st.markdown('<div style="color:#555;font-size:0.85rem;padding:8px 0;">No recent filings found.</div>', unsafe_allow_html=True)
        return

    items_html = ""
    for f in filings:
        tag_cls, tag_lbl = get_tag(f.get("category",""))
        title = f.get("title","")[:120]
        url   = f.get("url","")
        date  = f.get("date","")
        exch  = f.get("exchange","BSE")
        link_o = f'<a href="{url}" target="_blank" style="color:#e2e8f0;text-decoration:none;">' if url else '<span style="color:#e2e8f0;">'
        link_c = '</a>' if url else '</span>'
        items_html += f"""
<div class="filing-item">
  <div class="filing-title">{link_o}{title}{link_c}</div>
  <div class="filing-meta">
    <span class="tag {tag_cls}">{tag_lbl}</span>
    <span class="filing-date">{date}</span>
    <span class="filing-exchange">{exch}</span>
  </div>
</div>"""
    st.markdown(items_html, unsafe_allow_html=True)


def render_sentiment(sent: dict):
    """Render the sentiment tracker card."""
    if not sent:
        st.markdown('<div style="color:#555;font-size:0.85rem;">Sentiment data unavailable.</div>', unsafe_allow_html=True)
        return
    composite = sent.get("composite", 50)
    verdict   = sent.get("verdict", "Neutral")
    bull_pct  = sent.get("bull_pct", 50)
    social    = sent.get("social", 50)
    retail    = sent.get("retail", 50)
    interest  = sent.get("interest", 50)
    posts     = sent.get("posts", [])
    total     = sent.get("total", 0)

    # Needle angle: -90 (bearish left) to +90 (bullish right), 0=neutral
    angle = round((composite - 50) * 1.8)

    # Verdict colour
    if composite >= 60:   vc = "#00c851"
    elif composite >= 50: vc = "#ffaa00"
    elif composite >= 40: vc = "#ffaa00"
    else:                 vc = "#ff4444"

    # Bar colour helper
    def bar_col(v): return "#00c851" if v>=60 else "#ffaa00" if v>=45 else "#ff4444"

    gauge_html = f"""
<div style="text-align:center;margin-bottom:12px;">
<svg viewBox="0 0 220 115" style="width:100%;max-width:240px;">
  <path d="M 20 105 A 90 90 0 0 1 200 105" fill="none" stroke="#1a1a1a" stroke-width="16" stroke-linecap="round"/>
  <path d="M 20 105 A 90 90 0 0 1 200 105" fill="none" stroke="{vc}" stroke-width="16" stroke-linecap="round"
        stroke-dasharray="283" stroke-dashoffset="{round(283*(1-composite/100))}"/>
  <line x1="110" y1="105" x2="110" y2="22" stroke="#ffffff" stroke-width="2" stroke-linecap="round"
        transform="rotate({angle}, 110, 105)"/>
  <circle cx="110" cy="105" r="5" fill="{vc}"/>
  <text x="12"  y="116" font-size="8.5" fill="#444" font-family="monospace">Bearish</text>
  <text x="82"  y="13"  font-size="8.5" fill="#444" font-family="monospace">Neutral</text>
  <text x="172" y="116" font-size="8.5" fill="#444" font-family="monospace">Bullish</text>
  <text x="110" y="87"  text-anchor="middle" font-size="24" font-weight="700" fill="{vc}" font-family="monospace">{composite}</text>
  <text x="110" y="100" text-anchor="middle" font-size="8" fill="#555" font-family="monospace">COMPOSITE</text>
</svg>
<div style="font-size:0.72rem;font-family:monospace;color:{vc};letter-spacing:0.1em;text-transform:uppercase;">{verdict}</div>
</div>
<div style="margin-bottom:12px;">
  <div style="display:flex;align-items:center;gap:10px;padding:5px 0;border-bottom:1px solid #1a1a1a;">
    <span style="font-size:0.68rem;color:#555;font-family:monospace;width:68px;">Social</span>
    <div style="flex:1;background:#1a1a1a;border-radius:3px;height:5px;"><div style="width:{social}%;height:5px;border-radius:3px;background:{bar_col(social)};"></div></div>
    <span style="font-size:0.72rem;font-family:monospace;color:{bar_col(social)};width:36px;text-align:right;">{social}%</span>
  </div>
  <div style="display:flex;align-items:center;gap:10px;padding:5px 0;border-bottom:1px solid #1a1a1a;">
    <span style="font-size:0.68rem;color:#555;font-family:monospace;width:68px;">Retail</span>
    <div style="flex:1;background:#1a1a1a;border-radius:3px;height:5px;"><div style="width:{retail}%;height:5px;border-radius:3px;background:{bar_col(retail)};"></div></div>
    <span style="font-size:0.72rem;font-family:monospace;color:{bar_col(retail)};width:36px;text-align:right;">{retail}%</span>
  </div>
  <div style="display:flex;align-items:center;gap:10px;padding:5px 0;">
    <span style="font-size:0.68rem;color:#555;font-family:monospace;width:68px;">Interest</span>
    <div style="flex:1;background:#1a1a1a;border-radius:3px;height:5px;"><div style="width:{interest}%;height:5px;border-radius:3px;background:#3399ff;"></div></div>
    <span style="font-size:0.72rem;font-family:monospace;color:#3399ff;width:36px;text-align:right;">{interest}</span>
  </div>
</div>"""
    st.markdown(gauge_html, unsafe_allow_html=True)

    if posts:
        st.markdown('<div style="border-top:1px solid #1a1a1a;padding-top:10px;margin-bottom:8px;font-size:0.62rem;color:#444;font-family:monospace;letter-spacing:0.1em;text-transform:uppercase;">Top signals</div>', unsafe_allow_html=True)
        for p in posts:
            text = p.get("text","")[:140]
            age  = p.get("age","")
            sc   = p.get("sent","Neutral")
            sc_col = "#00c851" if sc=="Bullish" else "#ff4444" if sc=="Bearish" else "#ffaa00"
            sc_sym = "▲" if sc=="Bullish" else "▼" if sc=="Bearish" else "●"
            st.markdown(f"""
<div style="background:#0d0d0d;border:1px solid #1a1a1a;border-radius:6px;padding:9px 11px;margin-bottom:7px;">
  <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:4px;">
    <span style="font-size:0.65rem;color:#444;font-family:monospace;">{age}</span>
    <span style="font-size:0.65rem;font-weight:700;font-family:monospace;color:{sc_col};">{sc_sym} {sc}</span>
  </div>
  <div style="font-size:0.8rem;color:#999;line-height:1.5;">{text}</div>
</div>""", unsafe_allow_html=True)

    st.markdown(f'<div style="display:flex;justify-content:space-between;font-size:0.65rem;color:#333;font-family:monospace;border-top:1px solid #1a1a1a;padding-top:8px;margin-top:4px;"><span>{total} signals aggregated</span><span>Live</span></div>', unsafe_allow_html=True)


@st.cache_data(ttl=300, show_spinner=False)
def fetch_ohlcv(symbol: str) -> pd.DataFrame:
    """Fetch 200-day OHLCV from Yahoo Finance for a single NSE stock."""
    ticker = symbol.upper().strip() + ".NS"
    end   = int(datetime.now().timestamp())
    start = int((datetime.now() - timedelta(days=400)).timestamp())
    url   = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?interval=1d&period1={start}&period2={end}"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        r = requests.get(url, headers=headers, timeout=10)
        data = r.json()
        result = data["chart"]["result"][0]
        timestamps = result["timestamp"]
        ohlcv = result["indicators"]["quote"][0]
        df = pd.DataFrame({
            "date":   pd.to_datetime(timestamps, unit="s"),
            "Open":   ohlcv["open"],
            "High":   ohlcv["high"],
            "Low":    ohlcv["low"],
            "Close":  ohlcv["close"],
            "Volume": ohlcv["volume"],
        }).dropna(subset=["Close"]).reset_index(drop=True)
        info = result.get("meta", {})
        return df, info
    except Exception as e:
        return pd.DataFrame(), {}

@st.cache_data(ttl=3600)
def fetch_fundamentals(symbol: str) -> dict:
    """Pull key fundamental metrics from yfinance ticker.info."""
    try:
        tk = yf.Ticker(symbol.upper().strip() + ".NS")
        info = tk.info or {}
        def _pct(v): return f"{v*100:.1f}%" if v is not None else "—"
        def _x(v,d=1): return f"{v:.{d}f}x" if v is not None else "—"
        def _n(v,d=1): return f"{v:.{d}f}" if v is not None else "—"
        def _cr(v): return f"₹{v/1e7:,.0f} Cr" if v is not None else "—"
        return {
            "pe":          _n(info.get("trailingPE"),1),
            "fwd_pe":      _n(info.get("forwardPE"),1),
            "ev_ebitda":   _x(info.get("enterpriseToEbitda")),
            "pb":          _x(info.get("priceToBook")),
            "ps":          _x(info.get("priceToSalesTrailing12Months")),
            "revenue":     _cr(info.get("totalRevenue")),
            "net_income":  _cr(info.get("netIncomeToCommon")),
            "profit_margin": _pct(info.get("profitMargins")),
            "roe":         _pct(info.get("returnOnEquity")),
            "debt_equity": _n(info.get("debtToEquity"),1),
            "current_ratio": _n(info.get("currentRatio"),2),
            "promoter":    _pct(info.get("heldPercentInsiders")),
            "inst_hold":   _pct(info.get("heldPercentInstitutions")),
            "div_yield":   _pct(info.get("dividendYield")),
            "payout":      _pct(info.get("payoutRatio")),
            "sector":      info.get("sector") or info.get("industry") or "—",
            "employees":   f"{info.get('fullTimeEmployees',0):,}" if info.get("fullTimeEmployees") else "—",
            "_pe_raw":     info.get("trailingPE"),
            "_de_raw":     info.get("debtToEquity"),
            "_pm_raw":     info.get("profitMargins"),
            "_roe_raw":    info.get("returnOnEquity"),
        }
    except Exception:
        return {}

def render_fundamentals(fund: dict, symbol: str):
    if not fund:
        st.markdown('<div style="color:#555;font-size:0.85rem;padding:8px 0;">Fundamentals unavailable.</div>', unsafe_allow_html=True)
        return
    def pe_c(v): return "good" if v and v<20 else "warn" if v and v<35 else "bad" if v else ""
    def de_c(v): return "good" if v and v<0.5 else "warn" if v and v<1.5 else "bad" if v else ""
    def pm_c(v): return "good" if v and v>0.15 else "warn" if v and v>0.05 else "bad" if v else ""
    def roe_c(v): return "good" if v and v>0.15 else "warn" if v and v>0.08 else "bad" if v else ""
    def fi(lbl,val,cls=""):
        return f'<div class="fund-item"><div class="fund-label">{lbl}</div><div class="fund-value {cls}">{val}</div></div>'
    html = (
        '<div class="fund-section-head" style="margin-top:0;border-top:none;padding-top:0;">Valuation</div>'
        '<div class="fund-grid">'
        + fi("P/E (TTM)", fund.get("pe","—"), pe_c(fund.get("_pe_raw")))
        + fi("Forward P/E", fund.get("fwd_pe","—"), pe_c(fund.get("_pe_raw")))
        + fi("EV / EBITDA", fund.get("ev_ebitda","—"))
        + fi("Price / Book", fund.get("pb","—"))
        + fi("Price / Sales", fund.get("ps","—"))
        + fi("Sector", fund.get("sector","—"))
        + '</div>'
        + '<div class="fund-section-head">Financials</div>'
        + '<div class="fund-grid">'
        + fi("Revenue", fund.get("revenue","—"))
        + fi("Net Income", fund.get("net_income","—"), pm_c(fund.get("_pm_raw")))
        + fi("Profit Margin", fund.get("profit_margin","—"), pm_c(fund.get("_pm_raw")))
        + fi("ROE", fund.get("roe","—"), roe_c(fund.get("_roe_raw")))
        + fi("Debt / Equity", fund.get("debt_equity","—"), de_c(fund.get("_de_raw")))
        + fi("Current Ratio", fund.get("current_ratio","—"))
        + '</div>'
        + '<div class="fund-section-head">Ownership & Dividends</div>'
        + '<div class="fund-grid">'
        + fi("Promoter Hold", fund.get("promoter","—"))
        + fi("Inst. Holding", fund.get("inst_hold","—"))
        + fi("Div Yield", fund.get("div_yield","—"))
        + fi("Payout Ratio", fund.get("payout","—"))
        + fi("Employees", fund.get("employees","—"))
        + '</div>'
    )
    st.markdown(html, unsafe_allow_html=True)




@st.cache_data(ttl=300, show_spinner=False)
def fetch_quote(symbol: str) -> dict:
    """Fetch live quote from Yahoo Finance."""
    ticker = symbol.upper().strip() + ".NS"
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?interval=1d&range=1d"
    try:
        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=8)
        meta = r.json()["chart"]["result"][0]["meta"]
        return {
            "price":    meta.get("regularMarketPrice", 0),
            "prev":     meta.get("chartPreviousClose", 0),
            "high52":   meta.get("fiftyTwoWeekHigh", 0),
            "low52":    meta.get("fiftyTwoWeekLow", 0),
            "name":     meta.get("longName", symbol).replace(".NS","").replace(".BO",""),
            "currency": meta.get("currency", "INR"),
            "exchange": meta.get("exchangeName", "NSE"),
        }
    except Exception:
        return {}


# ── Company metadata ──────────────────────────────────────────────────────────
COMPANY_META = {
    "HINDALCO":   ("Hindalco Industries",      "Metals",       "Novelis aluminium copper"),
    "TATASTEEL":  ("Tata Steel",               "Metals",       "steel Europe"),
    "JSWSTEEL":   ("JSW Steel",                "Metals",       "JSW steel"),
    "COALINDIA":  ("Coal India",               "Energy",       "coal mining CIL"),
    "ONGC":       ("ONGC",                     "Energy",       "oil gas upstream"),
    "RELIANCE":   ("Reliance Industries",      "Conglomerate", "Jio retail RIL"),
    "INFY":       ("Infosys",                  "IT",           "IT services"),
    "TCS":        ("Tata Consultancy Services","IT",           "TCS IT"),
    "HDFCBANK":   ("HDFC Bank",               "Banking",       "HDFC private bank"),
    "ICICIBANK":  ("ICICI Bank",              "Banking",       "ICICI private bank"),
    "AXISBANK":   ("Axis Bank",               "Banking",       "Axis private bank"),
    "SBIN":       ("State Bank of India",     "Banking",       "SBI public sector"),
    "BAJFINANCE": ("Bajaj Finance",           "NBFC",          "Bajaj NBFC lending"),
    "MARUTI":     ("Maruti Suzuki",           "Auto",          "Maruti passenger vehicles"),
    "TATAMOTORS": ("Tata Motors",             "Auto",          "Tata EV Jaguar JLR"),
    "WIPRO":      ("Wipro",                   "IT",            "Wipro IT services"),
    "HCLTECH":    ("HCL Technologies",        "IT",            "HCL IT"),
    "SUNPHARMA":  ("Sun Pharmaceutical",      "Pharma",        "Sun Pharma USFDA"),
    "DRREDDY":    ("Dr Reddy's Laboratories", "Pharma",        "Dr Reddy generics"),
    "CIPLA":      ("Cipla",                   "Pharma",        "Cipla drugs"),
    "ADANIENT":   ("Adani Enterprises",       "Conglomerate",  "Adani group"),
    "ADANIPORTS": ("Adani Ports",             "Infrastructure","Adani ports logistics"),
    "LT":         ("Larsen & Toubro",         "Infrastructure","L&T engineering"),
    "ULTRACEMCO": ("UltraTech Cement",        "Cement",        "UltraTech cement"),
    "ASIANPAINT": ("Asian Paints",            "Consumer",      "Asian Paints decorative"),
    "TITAN":      ("Titan Company",           "Consumer",      "Titan Tanishq jewellery"),
    "NESTLEIND":  ("Nestle India",            "FMCG",          "Nestle FMCG"),
    "HINDUNILVR": ("Hindustan Unilever",      "FMCG",          "HUL FMCG"),
    "ITC":        ("ITC Limited",             "FMCG",          "ITC cigarettes hotels"),
    "POWERGRID":  ("Power Grid Corporation",  "Utilities",     "Power Grid transmission"),
    "NTPC":       ("NTPC",                    "Utilities",     "NTPC power generation"),
    "TECHM":      ("Tech Mahindra",           "IT",            "Tech Mahindra telecom"),
    "KOTAKBANK":  ("Kotak Mahindra Bank",     "Banking",       "Kotak private bank"),
    "BAJAJFINSV": ("Bajaj Finserv",           "NBFC",          "Bajaj Finserv insurance"),
    "VEDL":       ("Vedanta",                 "Metals",        "Vedanta zinc aluminium"),
    "INDUSINDBK": ("IndusInd Bank",           "Banking",       "IndusInd private bank"),
    "HEROMOTOCO": ("Hero MotoCorp",           "Auto",          "Hero two-wheeler"),
    "BRITANNIA":  ("Britannia Industries",    "FMCG",          "Britannia biscuits"),
    "DIVISLAB":   ("Divi's Laboratories",     "Pharma",        "Divi's API pharma"),
    "EICHERMOT":  ("Eicher Motors",           "Auto",          "Royal Enfield"),
    "GRASIM":     ("Grasim Industries",       "Conglomerate",  "Grasim cement Birla"),
    "BPCL":       ("Bharat Petroleum",        "Energy",        "BPCL refining fuel"),
    "APOLLOHOSP": ("Apollo Hospitals",        "Healthcare",    "Apollo hospital healthcare"),
    "BHARTIARTL": ("Bharti Airtel",           "Telecom",       "Airtel telecom"),
    "ZOMATO":     ("Zomato",                  "Consumer Tech", "Zomato food delivery"),
    "TRENT":      ("Trent",                   "Retail",        "Trent Westside Zudio"),
}

def _get_company_meta(symbol: str) -> tuple:
    clean = symbol.upper().replace(".NS","").replace(".BO","")
    return COMPANY_META.get(clean, (clean.title(), "Equity", ""))

def _tag_article(title: str, description: str) -> tuple:
    text = (title + " " + description).lower()
    rules = [
        (["result","profit","revenue","earnings","ebitda","q1","q2","q3","q4",
          "quarterly","annual report"],                                 "Result",      "#1e3a2f","#34d399"),
        (["capex","expansion","plant","capacity","acquisition","merger",
          "stake","buyout","deal","jv","joint venture"],               "Corporate",   "#1e2a3a","#60a5fa"),
        (["ipo","fpo","buyback","dividend","bonus","split","listing",
          "qip","ncd","rights issue"],                                 "Corp action", "#2a1e3a","#a78bfa"),
        (["upgrade","downgrade","target price","analyst","brokerage",
          "overweight","underweight"],                                 "Analyst",     "#3a2a1e","#fb923c"),
        (["sebi","regulatory","compliance","fine","penalty",
          "notice","investigation"],                                   "Regulatory",  "#3a1e1e","#f87171"),
        (["lme","aluminium","aluminum","copper","zinc","steel",
          "iron ore","commodity","crude","coal price"],                "Commodity",   "#2a2a1e","#facc15"),
        (["sector","industry","peers","competition"],                  "Sector",      "#1e2a2a","#67e8f9"),
    ]
    for keywords, label, bg, fg in rules:
        if any(k in text for k in keywords):
            return label, bg, fg
    return "News", "#1f1f1f", "#9ca3af"

def _format_news_date(raw: str) -> str:
    for fmt in ("%Y-%m-%dT%H:%M:%SZ", "%a, %d %b %Y %H:%M:%S %z",
                "%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%d"):
        try:
            return datetime.strptime(raw[:25], fmt).strftime("%d %b %Y")
        except Exception:
            continue
    return raw[:10] if raw else ""

def _dedup_news(articles: list) -> list:
    seen, out = set(), []
    for a in articles:
        key = hashlib.md5(a.get("title","")[:60].encode()).hexdigest()
        if key not in seen:
            seen.add(key)
            out.append(a)
    return out

def _fetch_indianapi_news(symbol: str) -> list:
    key = st.secrets.get("INDIANAPI_KEY", "")
    if not key:
        return []
    company_name, _, _ = _get_company_meta(symbol)
    try:
        r = requests.get(
            "https://stock.indianapi.in/stock",
            params={"name": company_name},
            headers={"X-Api-Key": key},
            timeout=8,
        )
        r.raise_for_status()
        raw_news = r.json().get("recentNews", [])
        return [{"title": n.get("title") or n.get("headline",""),
                 "description": n.get("summary",""),
                 "url": n.get("url") or n.get("link",""),
                 "source": n.get("source","IndianAPI"),
                 "published": n.get("date") or n.get("publishedAt","")}
                for n in raw_news[:8] if n.get("title") or n.get("headline")]
    except Exception:
        return []

def _fetch_gnews_news(symbol: str) -> list:
    key = st.secrets.get("GNEWS_API_KEY", "")
    if not key:
        return []
    company_name, _, extra = _get_company_meta(symbol)
    extra_kw = " ".join(extra.split()[:2]) if extra else ""
    query = f'"{company_name}"' + (f" {extra_kw}" if extra_kw else "")
    try:
        r = requests.get("https://gnews.io/api/v4/search", params={
            "q": query, "lang": "en", "country": "in",
            "max": 8, "sortby": "publishedAt", "apikey": key,
        }, timeout=8)
        r.raise_for_status()
        return [{"title": a.get("title",""), "description": a.get("description",""),
                 "url": a.get("url",""), "source": a.get("source",{}).get("name",""),
                 "published": a.get("publishedAt","")}
                for a in r.json().get("articles",[])]
    except Exception:
        return []

def _fetch_finnhub_company_news(symbol: str, finnhub_key: str) -> list:
    if not finnhub_key:
        return []
    try:
        to_dt   = datetime.now().strftime("%Y-%m-%d")
        from_dt = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        r = requests.get("https://finnhub.io/api/v1/company-news", params={
            "symbol": f"NSE:{symbol}", "from": from_dt, "to": to_dt, "token": finnhub_key,
        }, timeout=8)
        news = r.json()
        if not isinstance(news, list) or not news:
            return []
        return [{"title": n.get("headline",""), "description": n.get("summary",""),
                 "url": n.get("url",""), "source": n.get("source","Finnhub"),
                 "published": datetime.fromtimestamp(n.get("datetime",0)).strftime("%Y-%m-%dT%H:%M:%SZ")
                              if n.get("datetime") else ""}
                for n in news[:8]]
    except Exception:
        return []


def _format_news_date(raw):
    for fmt in ("%Y-%m-%dT%H:%M:%SZ", "%a, %d %b %Y %H:%M:%S %z",
                "%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%d"):
        try:
            return datetime.strptime(raw[:25], fmt).strftime("%d %b %Y")
        except Exception:
            continue
    return raw[:10] if raw else ""

def _dedup_news(articles):
    seen, out = set(), []
    for a in articles:
        key = hashlib.md5(a.get("title","")[:60].encode()).hexdigest()
        if key not in seen:
            seen.add(key)
            out.append(a)
    return out

def _fetch_indianapi_news(symbol):
    """
    Fetch stock-specific filings and news via yfinance — no API key needed.
    Returns: Yahoo Finance news feed + upcoming corporate calendar events.
    """
    ticker_sym = symbol.upper().strip() + ".NS"
    results = []
    try:
        tk = yf.Ticker(ticker_sym)

        # 1. Yahoo Finance news — stock-specific articles
        news_items = tk.news or []
        for n in news_items[:5]:
            content = n.get("content", {})
            title   = content.get("title","") or n.get("title","")
            url     = content.get("canonicalUrl",{}).get("url","") or n.get("link","")
            source  = content.get("provider",{}).get("displayName","") or n.get("publisher","")
            pub_ts  = n.get("providerPublishTime") or 0
            pub_dt  = datetime.fromtimestamp(pub_ts).strftime("%d %b %Y") if pub_ts else ""
            if title:
                results.append({
                    "title":       title,
                    "description": "",
                    "url":         url,
                    "source":      source or "Yahoo Finance",
                    "published":   pub_dt,
                })

        # 2. Calendar — earnings date, ex-dividend date
        try:
            cal = tk.calendar
            if isinstance(cal, dict):
                earn_date = cal.get("Earnings Date")
                ex_div    = cal.get("Ex-Dividend Date")
                if earn_date:
                    d = earn_date[0] if isinstance(earn_date, list) else earn_date
                    results.append({
                        "title":       f"Earnings Date: {str(d)[:10]}",
                        "description": "",
                        "url":         "",
                        "source":      "NSE Calendar",
                        "published":   str(d)[:10],
                    })
                if ex_div:
                    results.append({
                        "title":       f"Ex-Dividend Date: {str(ex_div)[:10]}",
                        "description": "",
                        "url":         "",
                        "source":      "NSE Calendar",
                        "published":   str(ex_div)[:10],
                    })
        except Exception:
            pass

        # 3. Recent dividends/splits from actions
        try:
            actions = tk.actions
            if actions is not None and not actions.empty:
                for date, row in actions.tail(3).iloc[::-1].iterrows():
                    if row.get("Dividends", 0) > 0:
                        results.append({
                            "title":       f"Dividend: ₹{row['Dividends']:.2f} per share",
                            "description": "",
                            "url":         "",
                            "source":      "NSE Corporate Action",
                            "published":   str(date)[:10],
                        })
                    if row.get("Stock Splits", 0) > 0:
                        results.append({
                            "title":       f"Stock Split: {row['Stock Splits']}:1",
                            "description": "",
                            "url":         "",
                            "source":      "NSE Corporate Action",
                            "published":   str(date)[:10],
                        })
        except Exception:
            pass

    except Exception:
        pass

    return results[:6]

def _fetch_gnews_news(symbol):
    key = st.secrets.get("GNEWS_API_KEY", "")
    if not key:
        return []
    company_name, _, extra = _get_company_meta(symbol)
    extra_kw = " ".join(extra.split()[:2]) if extra else ""
    query = '"' + company_name + '"' + (" " + extra_kw if extra_kw else "")
    try:
        r = requests.get("https://gnews.io/api/v4/search", params={
            "q": query, "lang": "en", "country": "in",
            "max": 8, "sortby": "publishedAt", "apikey": key}, timeout=8)
        r.raise_for_status()
        return [{"title": a.get("title",""), "description": a.get("description",""),
                 "url": a.get("url",""), "source": a.get("source",{}).get("name",""),
                 "published": a.get("publishedAt","")}
                for a in r.json().get("articles",[])]
    except Exception:
        return []

def _fetch_finnhub_company_news(symbol, finnhub_key):
    if not finnhub_key:
        return []
    try:
        to_dt   = datetime.now().strftime("%Y-%m-%d")
        from_dt = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        r = requests.get("https://finnhub.io/api/v1/company-news", params={
            "symbol": "NSE:" + symbol, "from": from_dt, "to": to_dt,
            "token": finnhub_key}, timeout=8)
        news = r.json()
        if not isinstance(news, list) or not news:
            return []
        return [{"title": n.get("headline",""), "description": n.get("summary",""),
                 "url": n.get("url",""), "source": n.get("source","Finnhub"),
                 "published": datetime.fromtimestamp(n.get("datetime",0)).strftime("%Y-%m-%dT%H:%M:%SZ")
                              if n.get("datetime") else ""}
                for n in news[:8]]
    except Exception:
        return []

def _fetch_moneycontrol_rss(symbol: str) -> list:
    company_name, _, _ = _get_company_meta(symbol)
    try:
        r = requests.get("https://www.moneycontrol.com/rss/results.xml",
                         timeout=8, headers={"User-Agent": "Mozilla/5.0"})
        r.raise_for_status()
        root = ET.fromstring(r.content)
        name_lower = company_name.lower()
        items = []
        for item in root.findall(".//item"):
            title = (item.findtext("title") or "").strip()
            desc  = (item.findtext("description") or "").strip()
            if name_lower not in (title + desc).lower():
                continue
            items.append({"title": title, "description": desc,
                          "url": (item.findtext("link") or "").strip(),
                          "source": "Moneycontrol",
                          "published": (item.findtext("pubDate") or "").strip()})
            if len(items) >= 6:
                break
        return items
    except Exception:
        return []

@st.cache_data(ttl=1802, show_spinner=False)
def fetch_news(symbol: str, finnhub_key: str) -> list:
    """Stock-specific news. Chain: IndianAPI → GNews → Finnhub → Moneycontrol RSS."""
    raw: list = []
    for fetcher in [
        lambda: _fetch_indianapi_news(symbol),
        lambda: _fetch_gnews_news(symbol),
        lambda: _fetch_finnhub_company_news(symbol, finnhub_key),
        lambda: _fetch_moneycontrol_rss(symbol),
    ]:
        raw = fetcher()
        if raw:
            break
    raw = _dedup_news(raw)[:6]
    company_name, _, _ = _get_company_meta(symbol)
    enriched = []
    for a in raw:
        tag_label, tag_bg, tag_fg = _tag_article(a.get("title",""), a.get("description",""))
        enriched.append({**a,
            "published":  _format_news_date(a.get("published","")),
            "tag_label":  tag_label, "tag_bg": tag_bg, "tag_fg": tag_fg,
            "company":    company_name,
        })
    return enriched

@st.cache_data(ttl=600, show_spinner=False)
def fetch_recommendation(symbol: str, finnhub_key: str) -> dict:
    """Fetch analyst recommendations from Finnhub."""
    if not finnhub_key:
        return {}
    try:
        # Try NSE: prefix first, then plain symbol
        url = f"https://finnhub.io/api/v1/stock/recommendation?symbol=NSE:{symbol}&token={finnhub_key}"
        r_chk = requests.get(url, timeout=8)
        if r_chk.status_code != 200 or not r_chk.json():
            url = f"https://finnhub.io/api/v1/stock/recommendation?symbol={symbol}&token={finnhub_key}"
        r   = requests.get(url, timeout=8)
        recs = r.json()
        return recs[0] if recs and isinstance(recs, list) else {}
    except Exception:
        return {}

# ── Indicators ────────────────────────────────────────────────────────────────
def compute_indicators(df: pd.DataFrame) -> dict:
    if df.empty or len(df) < 20:
        return {}

    close = df["Close"].values
    high  = df["High"].values
    low   = df["Low"].values
    vol   = df["Volume"].values
    n     = len(close)

    # Moving averages
    ma20  = np.mean(close[-20:])
    ma50  = np.mean(close[-50:])  if n >= 50  else np.mean(close)
    ma200 = np.mean(close[-200:]) if n >= 200 else np.mean(close)
    cp    = close[-1]
    # Weekly candle (last 5 trading days)
    wk_open  = close[-6] if n >= 6 else close[0]
    wk_close = close[-1]
    wk_high  = np.max(high[-5:])  if n >= 5 else high[-1]
    wk_low   = np.min(low[-5:])   if n >= 5 else low[-1]
    wk_chg   = (wk_close - wk_open) / wk_open * 100 if wk_open else 0
    weekly_trend = "Bullish" if wk_chg > 0.5 else "Bearish" if wk_chg < -0.5 else "Flat"

    # RSI 14
    deltas = np.diff(close[-15:])
    gains  = np.where(deltas > 0, deltas, 0)
    losses = np.where(deltas < 0, -deltas, 0)
    avg_g  = np.mean(gains) if gains.any() else 1e-9
    avg_l  = np.mean(losses) if losses.any() else 1e-9
    rs     = avg_g / avg_l if avg_l else 100
    rsi    = 100 - (100 / (1 + rs))

    # ATR 14
    tr_arr = [max(high[i]-low[i], abs(high[i]-close[i-1]), abs(low[i]-close[i-1]))
              for i in range(max(1, n-14), n)]
    atr = np.mean(tr_arr) if tr_arr else 0

    # ADX 14
    def adx14():
        if n < 15: return 20
        dm_pos = [max(high[i]-high[i-1], 0) if high[i]-high[i-1] > low[i-1]-low[i] else 0 for i in range(n-14,n)]
        dm_neg = [max(low[i-1]-low[i], 0) if low[i-1]-low[i] > high[i]-high[i-1] else 0 for i in range(n-14,n)]
        tr14   = [max(high[i]-low[i], abs(high[i]-close[i-1]), abs(low[i]-close[i-1])) for i in range(n-14,n)]
        tr_s   = sum(tr14) or 1
        di_pos = 100 * sum(dm_pos) / tr_s
        di_neg = 100 * sum(dm_neg) / tr_s
        dx     = 100 * abs(di_pos-di_neg) / ((di_pos+di_neg) or 1)
        return dx
    adx = adx14()

    # Z-Score
    mu  = np.mean(close[-20:])
    sig = np.std(close[-20:]) or 1
    z   = (cp - mu) / sig

    # Bollinger Bands
    bb_up  = mu + 2*sig
    bb_dn  = mu - 2*sig

    # IBS
    ibs = (close[-1] - low[-1]) / (high[-1] - low[-1]) if high[-1] != low[-1] else 0.5

    # Donchian 20
    don_high = np.max(high[-20:])
    don_low  = np.min(low[-20:])

    # MACD
    def ema(arr, p):
        e, k = arr[0], 2/(p+1)
        for x in arr[1:]: e = x*k + e*(1-k)
        return e
    if n >= 26:
        macd_line = ema(close[-26:], 12) - ema(close[-26:], 26)
    else:
        macd_line = 0

    # Miro Score (composite 0-10)
    score = 5.0
    if cp > ma20:  score += 0.5
    if cp > ma50:  score += 0.5
    if cp > ma200: score += 1.0
    if rsi < 30:   score += 1.5
    elif rsi < 45: score += 0.8
    elif rsi > 70: score -= 1.5
    elif rsi > 60: score -= 0.5
    if z < -1:     score += 1.0
    elif z > 1:    score -= 1.0
    if ibs < 0.2:  score += 0.5
    elif ibs > 0.8:score -= 0.5
    if adx > 25:   score += 0.5
    if macd_line > 0: score += 0.3
    score = max(0, min(10, score))

    # Trend
    if cp > ma20 > ma50 > ma200 and adx > 25:
        trend = "Strong Uptrend"
    elif cp > ma50 > ma200:
        trend = "Uptrend"
    elif cp < ma20 < ma50 < ma200 and adx > 25:
        trend = "Strong Downtrend"
    elif cp < ma50 < ma200:
        trend = "Downtrend"
    else:
        trend = "Sideways"

    # HP Filter (simple trend via rolling regression)
    x = np.arange(min(60, n))
    y = close[-min(60,n):]
    if len(x) > 1:
        coeffs = np.polyfit(x, y, 1)
        hp_above = cp > np.polyval(coeffs, len(x)-1)
    else:
        hp_above = True

    # Volume surge
    avg_vol = np.mean(vol[-20:-1]) if n > 20 else np.mean(vol)
    vol_ratio = vol[-1] / avg_vol if avg_vol else 1

    # 52-week position %
    wk52_high = np.max(high[-min(252,n):])
    wk52_low  = np.min(low[-min(252,n):])
    wk52_pct  = (cp - wk52_low) / (wk52_high - wk52_low) * 100 if wk52_high != wk52_low else 50

    return {
        "price":      round(cp, 2),
        "change_pct": round((cp - close[-2]) / close[-2] * 100, 2) if n > 1 else 0,
        "ma20":       round(ma20, 2),
        "ma50":       round(ma50, 2),
        "ma200":      round(ma200, 2),
        "rsi":        round(rsi, 1),
        "atr":        round(atr, 2),
        "adx":        round(adx, 1),
        "z_score":    round(z, 2),
        "bb_up":      round(bb_up, 2),
        "bb_dn":      round(bb_dn, 2),
        "ibs":        round(ibs, 3),
        "don_high":   round(don_high, 2),
        "don_low":    round(don_low, 2),
        "macd":       round(macd_line, 2),
        "miro_score": round(score, 1),
        "trend":      trend,
        "hp_above":   hp_above,
        "vol_ratio":  round(vol_ratio, 2),
        "wk52_pct":   round(wk52_pct, 1),
        "wk52_high":  round(wk52_high, 2),
        "wk52_low":   round(wk52_low, 2),
        "weekly_trend": weekly_trend,
        "weekly_chg":   round(wk_chg, 2),
        "ma50_display": round(ma50, 2),
    }

# ── AI Agents ─────────────────────────────────────────────────────────────────
def build_context(symbol, ind, quote, news, rec) -> str:
    news_txt = "\n".join([f"- {n.get('title', n.get('headline',''))}" for n in news[:4]]) or "No recent news"
    rec_txt  = f"Buy:{rec.get('buy',0)} Hold:{rec.get('hold',0)} Sell:{rec.get('sell',0)}" if rec else "N/A"
    return f"""
Stock: {symbol}.NS | Price: ₹{ind.get('price',0)} ({ind.get('change_pct',0):+.2f}%)
Company: {quote.get('name', symbol)}

TECHNICAL INDICATORS:
- Miro Score: {ind.get('miro_score',5)}/10
- Trend: {ind.get('trend','N/A')} | ADX: {ind.get('adx',0)}
- RSI(14): {ind.get('rsi',50)} | MACD: {ind.get('macd',0)}
- Z-Score: {ind.get('z_score',0)} (vs 20d mean)
- IBS: {ind.get('ibs',0.5)} (0=oversold, 1=overbought)
- MA20: {ind.get('ma20')} | MA50: {ind.get('ma50')} | MA200: {ind.get('ma200')}
- Bollinger: {ind.get('bb_dn')} – {ind.get('bb_up')}
- Donchian 20d: {ind.get('don_low')} – {ind.get('don_high')}
- ATR(14): {ind.get('atr')} | Volume ratio: {ind.get('vol_ratio')}x avg
- 52W Range: ₹{ind.get('wk52_low')} – ₹{ind.get('wk52_high')} | Position: {ind.get('wk52_pct')}%
- HP Filter: {'Above trend' if ind.get('hp_above') else 'Below trend'}

ANALYST CONSENSUS: {rec_txt}

RECENT NEWS:
{news_txt}

DISCLAIMER: This is for educational purposes only. Not SEBI registered. Not financial advice.
"""

AGENTS = [
    ("📈 Bull Analyst",    "bull",    "#00c851", "You are an optimistic equity analyst. Find compelling bullish reasons to buy this stock based on the data. Be specific about price targets and catalysts. 4-5 sentences, be concise."),
    ("📉 Bear Analyst",    "bear",    "#ff4444", "You are a cautious short-seller. Identify the key risks, red flags and reasons to avoid this stock right now. Be specific. 4-5 sentences, be concise."),
    ("⚡ Swing Trader",    "trader",  "#ffaa00", "You are an experienced NSE swing trader. Give a concrete trading plan: entry zone, stop loss, target, and timeframe. Be very specific with numbers. 4-5 sentences, be concise."),
    ("🛡️ Risk Manager",   "risk",    "#3399ff", "You are a portfolio risk manager. Assess the risk/reward, suggest position sizing as % of portfolio, and key levels to watch. 4-5 sentences, be concise."),
    ("🏛️ Fundamentalist", "fund",    "#aa88ff", "You are a fundamental analyst. Comment on valuation context, sector dynamics, and whether the technical picture aligns with fundamentals. 4-5 sentences, be concise."),
]

def stream_agent(client, agent_name, persona, context, placeholder):
    msgs = [{"role": "user", "content": f"{context}\n\nYour role: {persona}\nAnalyse this stock now."}]
    full = ""
    try:
        with client.messages.stream(
            model="claude-sonnet-4-6",
            max_tokens=600,
            system="You are part of an AI trading desk. Give sharp, data-driven analysis. Reference specific numbers from the data provided. Be concise and actionable.",
            messages=msgs,
        ) as stream:
            for text in stream.text_stream:
                full += text
                placeholder.markdown(full + "▌")
        placeholder.markdown(full)
    except Exception as e:
        placeholder.markdown(f"*Analysis unavailable: {e}*")
    return full

# ── Helpers ───────────────────────────────────────────────────────────────────
def signal_color(val, low_good=False):
    if low_good:
        return "signal-bull" if val < 30 else "signal-bear" if val > 70 else "signal-neutral"
    return "signal-bull" if val > 0 else "signal-bear"

def render_metric(label, value, sub="", css_class=""):
    return f"""
<div class="metric-card">
  <div class="metric-label">{label}</div>
  <div class="metric-value {css_class}">{value}</div>
  {"<div class='metric-sub'>" + sub + "</div>" if sub else ""}
</div>"""

def score_bar(val, max_val=10, color="#00c851"):
    pct = int(val / max_val * 100)
    return f"""
<div class="score-bar-bg">
  <div class="score-bar-fill" style="width:{pct}%; background:{color};"></div>
</div>"""

# ── Main UI ───────────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero">
  <h1>⚡ NIFTY SNIPER</h1>
  <p>Stock intelligence terminal · NSE India · Powered by AI agents</p>
</div>
""", unsafe_allow_html=True)

# Search bar
col_inp, col_btn = st.columns([5, 1])
with col_inp:
    symbol = st.text_input(
        "", placeholder="Symbol (RELIANCE) or name (State Bank of India, Infosys)...",
        label_visibility="collapsed",
        key="symbol_input",
    ).upper().strip()
with col_btn:
    analyse = st.button("🔍 Analyse", key="analyse_btn")

# Popular picks
st.markdown(
    "<div style='text-align:center; color:#555555; font-size:0.8rem; margin: -8px 0 16px'>Quick picks: "
    + " · ".join([f"<span style='color:#555555; cursor:pointer'>{s}</span>"
                  for s in ["RELIANCE","TCS","HDFCBANK","INFY","SBIN","TITAN","BAJFINANCE","NIFTY50"]])
    + "</div>", unsafe_allow_html=True
)

# ── Analysis ──────────────────────────────────────────────────────────────────
if analyse and symbol:
    symbol = resolve_symbol(symbol)
    st.divider()

    with st.spinner(f"Fetching data for {symbol}..."):
        df, meta  = fetch_ohlcv(symbol)
        quote     = fetch_quote(symbol)
        fh_key    = get_finnhub_key()
        news      = fetch_news(symbol, fh_key)
        rec       = fetch_recommendation(symbol, fh_key)
        filings   = fetch_bse_filings(symbol)
        sentiment = fetch_sentiment(symbol)
        fund      = fetch_fundamentals(symbol)

    if df.empty:
        st.error(f"❌ Could not fetch data for **{symbol}**. Check the NSE symbol and try again.")
        st.stop()

    ind = compute_indicators(df)
    if not ind:
        st.error("❌ Not enough data to compute indicators.")
        st.stop()

    cp      = ind["price"]
    chg     = ind["change_pct"]
    chg_col = "#00c851" if chg >= 0 else "#ff4444"
    chg_sym = "▲" if chg >= 0 else "▼"

    # ── Stock Header ──────────────────────────────────────────────────────────
    display_symbol = symbol.replace(".NS","").replace(".BO","")
    company_name = (quote.get('name', symbol) or symbol).replace('.NS','').replace('.BO','')
    st.markdown(f"""
<div class="section-card" style="margin-bottom:20px; border-top:2px solid #ff6600;">
  <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:12px;">
    <div>
      <div style="color:#ff6600; font-size:0.7rem; font-weight:600; letter-spacing:0.14em; text-transform:uppercase; font-family:'JetBrains Mono',monospace; margin-bottom:2px;">NSE · EQUITY</div>
      <div style="color:#ffffff; font-size:1.8rem; font-weight:700; font-family:'JetBrains Mono',monospace; letter-spacing:0.05em; line-height:1.1;">{display_symbol}</div>
      <div style="color:#aaaaaa; font-size:0.95rem; margin-top:3px;">{company_name}</div>
    </div>
    <div style="text-align:right;">
      <div style="color:#ffffff; font-size:2.2rem; font-weight:700; font-family:'JetBrains Mono',monospace;">&#8377;{cp:,.2f}</div>
      <div style="color:{chg_col}; font-size:1rem; font-weight:600;">{chg_sym} {abs(chg):.2f}%</div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

    # ── Key Metrics Row ───────────────────────────────────────────────────────
    miro  = ind["miro_score"]
    miro_c = "signal-bull" if miro >= 6.5 else "signal-bear" if miro < 4 else "signal-neutral"
    weekly_c = "signal-bull" if ind.get("weekly_chg",0) > 0.5 else "signal-bear" if ind.get("weekly_chg",0) < -0.5 else "signal-neutral"
    rsi    = ind["rsi"]
    rsi_c  = "signal-bull" if rsi < 40 else "signal-bear" if rsi > 65 else "signal-neutral"
    z      = ind["z_score"]
    z_c    = "signal-bull" if z < -0.5 else "signal-bear" if z > 1.5 else "signal-neutral"
    ibs    = ind["ibs"]
    ibs_c  = "signal-bull" if ibs < 0.3 else "signal-bear" if ibs > 0.75 else "signal-neutral"
    trend  = ind["trend"]
    tr_c   = "signal-bull" if "Up" in trend else "signal-bear" if "Down" in trend else "signal-neutral"

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.markdown(render_metric("Miro Score", f"{miro}/10", score_bar(miro), miro_c), unsafe_allow_html=True)
    c2.markdown(render_metric("RSI (14)", rsi, "Oversold<30 | Hot>70", rsi_c), unsafe_allow_html=True)
    c3.markdown(render_metric("Z-Score", z, "vs 20D mean", z_c), unsafe_allow_html=True)
    c4.markdown(render_metric("IBS", ibs, "0=low 1=high", ibs_c), unsafe_allow_html=True)
    c5.markdown(render_metric("Trend", trend.replace(" ", "<br>"), f"ADX {ind['adx']}", tr_c), unsafe_allow_html=True)

    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

    # ── Second metrics row ────────────────────────────────────────────────────
    c6, c7, c8, c9, c10 = st.columns(5)
    c6.markdown(render_metric("MA 20", f"₹{ind['ma20']:,}", "<span style='color:#00c851'>▲ Above</span>" if cp > ind['ma20'] else "<span style='color:#ff4444'>▼ Below</span>"), unsafe_allow_html=True)
    c7.markdown(render_metric("MA 50", f"₹{ind['ma50_display']:,}", "<span style='color:#00c851'>▲ Above</span>" if cp > ind['ma50_display'] else "<span style='color:#ff4444'>▼ Below</span>"), unsafe_allow_html=True)
    c8.markdown(render_metric("MA 200", f"₹{ind['ma200']:,}", "<span style='color:#00c851'>▲ Above</span>" if cp > ind['ma200'] else "<span style='color:#ff4444'>▼ Below</span>"), unsafe_allow_html=True)
    c9.markdown(render_metric("Weekly Trend", ind.get("weekly_trend","—"), f"{ind.get('weekly_chg',0):+.2f}% this week", weekly_c), unsafe_allow_html=True)
    c10.markdown(render_metric("52W Position", f"{ind['wk52_pct']}%", f"H:{ind['wk52_high']} L:{ind['wk52_low']}"), unsafe_allow_html=True)

    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

    # ── Two column layout: News + Chart data left, Signals right ─────────────
    left, right = st.columns([3, 2])

    with left:
        # ── Fundamentals ────────────────────────────────────────────────────
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">📐 Fundamentals</div>', unsafe_allow_html=True)
        render_fundamentals(fund, symbol)
        st.markdown('</div>', unsafe_allow_html=True)

        # ── BSE Filings ──────────────────────────────────────────────────────
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown(f'<div class="section-title">📋 Filings & Corporate Actions — {display_symbol}</div>', unsafe_allow_html=True)
        render_filings(filings, symbol)
        st.markdown('</div>', unsafe_allow_html=True)
    with right:
        # ── Sentiment Tracker ────────────────────────────────────────────────
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">📡 Market Sentiment</div>', unsafe_allow_html=True)
        render_sentiment(sentiment)
        st.markdown('</div>', unsafe_allow_html=True)

        # Signal summary
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">🎯 Signal Summary</div>', unsafe_allow_html=True)

        signals = [
            ("HP Filter",    "✅ Above Trend" if ind["hp_above"] else "❌ Below Trend",   ind["hp_above"]),
            ("Donchian",     "✅ Near High"   if cp > ind["don_high"]*0.97 else "⚠️ Mid Range", cp > ind["don_high"]*0.97),
            ("Bollinger",    "✅ Near Lower"  if cp < ind["bb_dn"]*1.02 else ("❌ Near Upper" if cp > ind["bb_up"]*0.98 else "⚠️ Mid Band"), cp < ind["bb_dn"]*1.02),
            ("MA Alignment", "✅ Bullish" if cp > ind["ma50"] > ind["ma200"] else "❌ Bearish", cp > ind["ma50"] > ind["ma200"]),
            ("MACD",         "✅ Positive" if ind["macd"] > 0 else "❌ Negative", ind["macd"] > 0),
            ("RSI Zone",     "✅ Buy Zone" if rsi < 40 else ("❌ Overbought" if rsi > 65 else "⚠️ Neutral"), rsi < 40),
            ("Volume",       f"✅ {ind['vol_ratio']}x Surge" if ind["vol_ratio"] > 1.5 else "⚠️ Normal", ind["vol_ratio"] > 1.5),
        ]
        bull_count = sum(1 for _, _, b in signals if b)
        for label, val, bull in signals:
            col_s = "#00c851" if bull else "#ff4444" if "❌" in val else "#ff8800"
            st.markdown(f"""
<div style="display:flex;align-items:center;padding:6px 0;border-bottom:1px solid #1a1a1a;">
  <span style="flex:1;color:#888;font-size:0.8rem;font-family:'Space Grotesk',sans-serif;">{label}</span>
  <span style="color:{col_s};font-size:0.8rem;font-weight:500;white-space:nowrap;">{val}</span>
</div>""", unsafe_allow_html=True)

        # Analyst recs
        if rec:
            st.markdown('<div class="section-card">', unsafe_allow_html=True)
            st.markdown('<div class="section-title">🏦 Analyst Consensus</div>', unsafe_allow_html=True)
            total = (rec.get("buy",0) + rec.get("hold",0) + rec.get("sell",0) + rec.get("strongBuy",0) + rec.get("strongSell",0)) or 1
            for label, key, col in [("Strong Buy","strongBuy","#ff6600"),("Buy","buy","#ff8800"),("Hold","hold","#ff8800"),("Sell","sell","#cc3300"),("Strong Sell","strongSell","#991100")]:
                n_rec = rec.get(key, 0)
                pct   = int(n_rec / total * 100)
                st.markdown(f"""
<div style="display:flex; align-items:center; gap:8px; margin-bottom:6px;">
  <span style="color:#9ca3af; font-size:0.75rem; width:70px;">{label}</span>
  <div style="flex:1; background:#1a1a1a; border-radius:3px; height:6px;">
    <div style="width:{pct}%; background:{col}; border-radius:3px; height:6px;"></div>
  </div>
  <span style="color:{col}; font-size:0.75rem; width:20px;">{n_rec}</span>
</div>""", unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

        # Verdict
        bull_signals = bull_count
        verdict = "STRONG BUY" if bull_signals >= 6 else "BUY" if bull_signals >= 5 else "HOLD" if bull_signals >= 3 else "AVOID"
        v_col   = "#00c851" if "BUY" in verdict else "#ff4444" if verdict == "AVOID" else "#ffaa00"
        st.markdown(f"""
<div class="verdict-box">
  <div class="verdict-label">AI Technical Verdict</div>
  <div class="verdict-text" style="color:{v_col};">{verdict}</div>
  <div style="color:#555555; font-size:0.75rem; margin-top:6px;">{bull_signals}/7 bullish signals</div>
</div>""", unsafe_allow_html=True)

    # ── AI Agent Debate ───────────────────────────────────────────────────────
    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">🤖 AI Agent Debate</div>', unsafe_allow_html=True)

    client = get_anthropic()
    if not client:
        st.warning("Add ANTHROPIC_API_KEY to Streamlit secrets to enable AI agent debate.")
    else:
        context = build_context(symbol, ind, quote, news, rec)
        for agent_name, agent_key, color, persona in AGENTS:
            st.markdown(f"""
<div class="agent-{agent_key}">
  <div class="agent-name" style="color:{color};">{agent_name}</div>
</div>""", unsafe_allow_html=True)
            placeholder = st.empty()
            stream_agent(client, agent_name, persona, context, placeholder)
            st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

    # Disclaimer
    st.markdown("""
<div style="text-align:center; color:#333333; font-size:0.75rem; margin-top:24px; padding:12px; border-top:1px solid #1a1a1a;">
⚠️ <strong>Not SEBI registered. Not financial advice. For educational purposes only. Always do your own research.</strong>
</div>""", unsafe_allow_html=True)


    # ── PDF Report ────────────────────────────────────────────────────────
    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
    _vc = "#00c851" if "BUY" in verdict else "#ff4444" if verdict == "AVOID" else "#ffaa00"
    _cc = "#00c851" if chg >= 0 else "#ff4444"
    _co = quote.get('name', symbol) or symbol
    _dt = datetime.now().strftime('%d %B %Y, %H:%M IST')
    _sl_rows = ""
    for _sln,_slv,_slb in [
        ("HP Filter","Above Trend" if ind["hp_above"] else "Below Trend",ind["hp_above"]),
        ("MA Alignment","Bullish" if cp>ind["ma50_display"]>ind["ma200"] else "Bearish",cp>ind["ma50_display"]>ind["ma200"]),
        ("RSI (14)",f"{ind['rsi']} — Buy Zone" if ind['rsi']<40 else f"{ind['rsi']} — Hot" if ind['rsi']>65 else f"{ind['rsi']} — Neutral",ind['rsi']<40),
        ("Z-Score",f"{ind['z_score']} — Oversold" if ind['z_score']<-0.5 else f"{ind['z_score']} — Extended" if ind['z_score']>1.5 else f"{ind['z_score']} — Neutral",ind['z_score']<-0.5),
        ("IBS",f"{ind['ibs']} — Buy" if ind['ibs']<0.3 else f"{ind['ibs']} — Sell" if ind['ibs']>0.75 else f"{ind['ibs']} — Neutral",ind['ibs']<0.3),
        ("Donchian","Near High" if cp>ind['don_high']*0.97 else "Mid Range",cp>ind['don_high']*0.97),
        ("MACD","Positive" if ind['macd']>0 else "Negative",ind['macd']>0),
        ("Volume",f"{ind['vol_ratio']}x Surge" if ind['vol_ratio']>1.5 else f"{ind['vol_ratio']}x Normal",ind['vol_ratio']>1.5),
    ]:
        _sc2 = "#00c851" if _slb else "#ff4444"
        _sl_rows += f"<tr><td style='padding:6px 12px;color:#888;font-size:12px;border-bottom:1px solid #1e1e1e;'>{_sln}</td><td style='padding:6px 12px;color:{_sc2};font-size:12px;font-weight:600;border-bottom:1px solid #1e1e1e;'>{'✓' if _slb else '✗'} {_slv}</td></tr>"
    _news_rows = ""
    if news:
        for _n2 in news[:5]:
            _nh2 = (_n2.get('title') or _n2.get('headline',''))[:85]
            _ns2 = datetime.fromtimestamp(_n2.get('datetime',0)).strftime('%d %b') if _n2.get('datetime') else ''
            _news_rows += f"<tr><td style='padding:5px 12px;color:#ccc;font-size:11px;border-bottom:1px solid #1e1e1e;'>{_nh2}</td><td style='padding:5px 12px;color:#666;font-size:11px;border-bottom:1px solid #1e1e1e;white-space:nowrap;'>{_n2.get('source','')} · {_ns2}</td></tr>"
    if not _news_rows:
        _news_rows = "<tr><td colspan='2' style='padding:8px 12px;color:#555;font-size:11px;'>No news data — add FINNHUB_API_KEY to Streamlit secrets</td></tr>"
    _miro_w = int(ind['miro_score']/10*100)
    _pdf = f"""<!DOCTYPE html><html><head><meta charset='UTF-8'><title>NiftySniper — {symbol}</title>
<link href='https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;600&display=swap' rel='stylesheet'>
<style>*{{margin:0;padding:0;box-sizing:border-box}}body{{background:#080808;color:#ccc;font-family:Inter,sans-serif;padding:32px;max-width:900px;margin:0 auto}}
@media print{{body{{padding:16px;background:#000}}@page{{size:A4;margin:12mm;background:#000}}.no-print{{display:none}}}}
.btn{{background:#ff6600;color:#000;border:none;padding:11px 28px;border-radius:6px;font-weight:700;font-size:13px;cursor:pointer;letter-spacing:.08em;font-family:'JetBrains Mono',monospace;margin-bottom:24px;}}
.btn:hover{{background:#ff8800}}
.hdr{{background:#0f0f0f;border-top:3px solid #ff6600;border-radius:8px;padding:22px 24px;margin-bottom:18px;display:flex;justify-content:space-between;align-items:flex-start}}
.logo{{color:#ff6600;font-family:'JetBrains Mono',monospace;font-size:17px;font-weight:700;letter-spacing:.1em}}
.logo-sub{{color:#555;font-size:9px;letter-spacing:.15em;margin-top:3px}}
.sym{{color:#fff;font-family:'JetBrains Mono',monospace;font-size:24px;font-weight:700;text-align:right}}
.co{{color:#aaa;font-size:12px;margin-top:2px;text-align:right}}
.px{{color:#fff;font-family:'JetBrains Mono',monospace;font-size:20px;font-weight:700;text-align:right;margin-top:3px}}
.vbox{{background:#0f0f0f;border:1px solid {_vc}44;border-left:4px solid {_vc};border-radius:8px;padding:14px 20px;margin-bottom:18px;display:flex;justify-content:space-between;align-items:center}}
.vlbl{{color:#666;font-size:9px;letter-spacing:.1em;text-transform:uppercase;font-family:'JetBrains Mono',monospace}}
.vval{{color:{_vc};font-size:26px;font-weight:700;font-family:'JetBrains Mono',monospace}}
.vsub{{color:#888;font-size:11px;margin-top:2px}}
.grid{{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-bottom:14px}}
.sec{{background:#0f0f0f;border:1px solid #1e1e1e;border-radius:8px;overflow:hidden}}
.stitle{{background:#141414;color:#ff6600;font-size:9px;font-weight:700;letter-spacing:.12em;text-transform:uppercase;padding:7px 12px;font-family:'JetBrains Mono',monospace;border-bottom:1px solid #1e1e1e}}
table{{width:100%;border-collapse:collapse}}
.mbar{{height:3px;background:#1a1a1a;border-radius:2px;margin-top:3px}}.mfill{{height:3px;background:#00c851;border-radius:2px;width:{_miro_w}%}}
.green{{color:#00c851}}.red{{color:#ff4444}}.amber{{color:#ffaa00}}.white{{color:#fff}}.mono{{font-family:'JetBrains Mono',monospace;font-weight:600}}
.disc{{color:#444;font-size:9px;text-align:center;margin-top:18px;padding-top:12px;border-top:1px solid #1a1a1a;line-height:1.7}}
</style></head><body>
<button class='btn no-print' onclick='window.print()'>⬇ SAVE AS PDF (Ctrl+P)</button>
<div class='hdr'>
  <div><div class='logo'>⚡ NIFTY SNIPER</div><div class='logo-sub'>SINGLE-STOCK INTELLIGENCE REPORT</div></div>
  <div><div class='sym'>{symbol}</div><div class='co'>{_co}</div><div class='px'>₹{cp:,.2f} <span style='color:{_cc};font-size:13px;'>{'+' if chg>=0 else ''}{chg:.2f}%</span></div><div class='logo-sub' style='text-align:right;margin-top:3px;'>NSE · {_dt}</div></div>
</div>
<div class='vbox'>
  <div><div class='vlbl'>AI Technical Verdict</div><div class='vsub'>{bull_signals}/8 signals · Miro Score {ind['miro_score']}/10</div></div>
  <div class='vval'>{verdict}</div>
</div>
<div class='grid'>
<div class='sec'><div class='stitle'>📊 Technical Indicators</div><table>
<tr><td style='padding:6px 12px;color:#888;font-size:11px;border-bottom:1px solid #1e1e1e;'>Miro Score</td><td style='padding:6px 12px;border-bottom:1px solid #1e1e1e;'><span class='mono {"green" if ind["miro_score"]>=6.5 else "red" if ind["miro_score"]<4 else "amber"}'>{ind['miro_score']}/10</span><div class='mbar'><div class='mfill'></div></div></td></tr>
<tr><td style='padding:6px 12px;color:#888;font-size:11px;border-bottom:1px solid #1e1e1e;'>Trend</td><td style='padding:6px 12px;border-bottom:1px solid #1e1e1e;'><span class='mono {"green" if "Up" in ind["trend"] else "red" if "Down" in ind["trend"] else "amber"}'>{ind['trend']}</span> <span style='color:#555;font-size:10px;'>ADX {ind['adx']}</span></td></tr>
<tr><td style='padding:6px 12px;color:#888;font-size:11px;border-bottom:1px solid #1e1e1e;'>Weekly Trend</td><td style='padding:6px 12px;border-bottom:1px solid #1e1e1e;'><span class='mono {"green" if ind.get("weekly_chg",0)>0.5 else "red" if ind.get("weekly_chg",0)<-0.5 else "amber"}'>{ind.get("weekly_trend","—")} ({ind.get("weekly_chg",0):+.2f}%)</span></td></tr>
<tr><td style='padding:6px 12px;color:#888;font-size:11px;border-bottom:1px solid #1e1e1e;'>RSI (14)</td><td style='padding:6px 12px;border-bottom:1px solid #1e1e1e;'><span class='mono {"green" if ind["rsi"]<40 else "red" if ind["rsi"]>65 else "amber"}'>{ind['rsi']}</span></td></tr>
<tr><td style='padding:6px 12px;color:#888;font-size:11px;border-bottom:1px solid #1e1e1e;'>Z-Score</td><td style='padding:6px 12px;border-bottom:1px solid #1e1e1e;'><span class='mono {"green" if ind["z_score"]<-0.5 else "red" if ind["z_score"]>1.5 else "amber"}'>{ind['z_score']}</span></td></tr>
<tr><td style='padding:6px 12px;color:#888;font-size:11px;border-bottom:1px solid #1e1e1e;'>IBS</td><td style='padding:6px 12px;border-bottom:1px solid #1e1e1e;'><span class='mono'>{ind['ibs']}</span></td></tr>
<tr><td style='padding:6px 12px;color:#888;font-size:11px;border-bottom:1px solid #1e1e1e;'>MACD</td><td style='padding:6px 12px;border-bottom:1px solid #1e1e1e;'><span class='mono {"green" if ind["macd"]>0 else "red"}'>{ind['macd']:+.2f}</span></td></tr>
<tr><td style='padding:6px 12px;color:#888;font-size:11px;'>Volume Ratio</td><td style='padding:6px 12px;'><span class='mono {"green" if ind["vol_ratio"]>1.5 else "white"}'>{ind['vol_ratio']}x avg</span></td></tr>
</table></div>
<div class='sec'><div class='stitle'>📈 Moving Averages & Key Levels</div><table>
<tr><td style='padding:6px 12px;color:#888;font-size:11px;border-bottom:1px solid #1e1e1e;'>MA 20</td><td style='padding:6px 12px;border-bottom:1px solid #1e1e1e;'><span class='mono white'>₹{ind['ma20']:,}</span> <span style='color:{"#00c851" if cp>ind["ma20"] else "#ff4444"};font-size:10px;'>{"▲" if cp>ind["ma20"] else "▼"}</span></td></tr>
<tr><td style='padding:6px 12px;color:#888;font-size:11px;border-bottom:1px solid #1e1e1e;'>MA 50</td><td style='padding:6px 12px;border-bottom:1px solid #1e1e1e;'><span class='mono white'>₹{ind['ma50_display']:,}</span> <span style='color:{"#00c851" if cp>ind["ma50_display"] else "#ff4444"};font-size:10px;'>{"▲" if cp>ind["ma50_display"] else "▼"}</span></td></tr>
<tr><td style='padding:6px 12px;color:#888;font-size:11px;border-bottom:1px solid #1e1e1e;'>MA 200</td><td style='padding:6px 12px;border-bottom:1px solid #1e1e1e;'><span class='mono white'>₹{ind['ma200']:,}</span> <span style='color:{"#00c851" if cp>ind["ma200"] else "#ff4444"};font-size:10px;'>{"▲" if cp>ind["ma200"] else "▼"}</span></td></tr>
<tr><td style='padding:6px 12px;color:#888;font-size:11px;border-bottom:1px solid #1e1e1e;'>Donchian</td><td style='padding:6px 12px;border-bottom:1px solid #1e1e1e;'><span class='mono white'>₹{ind['don_low']:,} — ₹{ind['don_high']:,}</span></td></tr>
<tr><td style='padding:6px 12px;color:#888;font-size:11px;border-bottom:1px solid #1e1e1e;'>Bollinger Bands</td><td style='padding:6px 12px;border-bottom:1px solid #1e1e1e;'><span class='mono white'>₹{ind['bb_dn']:,} — ₹{ind['bb_up']:,}</span></td></tr>
<tr><td style='padding:6px 12px;color:#888;font-size:11px;border-bottom:1px solid #1e1e1e;'>ATR (14)</td><td style='padding:6px 12px;border-bottom:1px solid #1e1e1e;'><span class='mono white'>₹{ind['atr']}</span></td></tr>
<tr><td style='padding:6px 12px;color:#888;font-size:11px;border-bottom:1px solid #1e1e1e;'>52-Week Range</td><td style='padding:6px 12px;border-bottom:1px solid #1e1e1e;'><span class='mono white'>₹{ind['wk52_low']:,} — ₹{ind['wk52_high']:,}</span></td></tr>
<tr><td style='padding:6px 12px;color:#888;font-size:11px;'>52W Position</td><td style='padding:6px 12px;'><span class='mono white'>{ind['wk52_pct']}% of range</span></td></tr>
</table></div>
</div>
<div class='grid'>
<div class='sec'><div class='stitle'>🎯 Signal Checklist</div><table>{_sl_rows}</table></div>
<div class='sec'><div class='stitle'>📰 Recent News & Filings</div><table>{_news_rows}</table></div>
</div>
<div class='disc'>⚠️ <strong>Nifty Sniper — For educational purposes only. Not registered with SEBI. Not financial advice. Always do your own research.</strong></div>
</body></html>"""
    _col1, _col2, _col3 = st.columns([1,2,1])
    with _col2:
        st.download_button(
            label="⬇️  DOWNLOAD REPORT (PDF)",
            data=_pdf,
            file_name=f"NiftySniper_{symbol}_{datetime.now().strftime('%Y%m%d')}.html",
            mime="text/html",
            use_container_width=True,
        )
    st.caption("Opens in browser → click **⬇ SAVE AS PDF** inside → Print → Save as PDF")
