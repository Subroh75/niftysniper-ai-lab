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

# ââ Page config âââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââ
# ââ NSE Symbol lookup ââââââââââââââââââââââââââââââââââââââââââââââââââââ
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
    page_icon="ð¯",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ââ Styling âââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââ
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

/* ââ INPUT: force white text ââââââââââââââââââââââââââââââ */
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

# ââ Clients âââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââ
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

# ââ Data fetching âââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââ

@st.cache_data(ttl=600, show_spinner=False)
def fetch_bse_filings(symbol: str) -> list:
    """Fetch real BSE filings via BSE India public API."""
    import requests, re
    # Map NSE symbol â BSE security code (common large caps)
    BSE_CODE = {
        "SUNPHARMA":"524715","RELIANCE":"500325","TCS":"532540","HDFCBANK":"500180",
        "INFY":"500209","ICICIBANK":"532174","SBIN":"500112","BAJFINANCE":"500034",
        "AXISBANK":"532215","MARUTI":"532500","HINDUNILVR":"500696","ITC":"500875",
        "WIPRO":"507685","HCLTECH":"532281","TATAMOTORS":"500570","TATASTEEL":"500470",
        "ONGC":"500312","COALINDIA":"533278","BHARTIARTL":"532454","LT":"500510",
        "ADANIENT":"512599","ADANIPORTS":"532921","ASIANPAINT":"500820","TITAN":"500114",
        "NESTLEIND":"500790","ULTRACEMCO":"532538","DRREDDY":"500124","CIPLA":"500087",
        "BAJAJFINSV":"532978","TECHM":"532755","KOTAKBANK":"500247","POWERGRID":"532898",
        "NTPC":"532555","DIVISLAB":"532488","JSWSTEEL":"500228","HINDALCO":"500440","BEL":"500049","BAJAJ-AUTO":"532977","HDFCLIFE":"540777","SBILIFE":"540719","BRITANNIA":"500825","GRASIM":"500300","BPCL":"500547","HEROMOTOCO":"500182","EICHERMOT":"505200","APOLLOHOSP":"508869","TATACONSUM":"500800","PIDILITIND":"500331","DMART":"540376","NAUKRI":"663532","MUTHOOTFIN":"533398","HAVELLS":"517354","BOSCHLTD":"500530","SIEMENS":"500550","TRENT":"500251","ZOMATO":"543320","PAYTM":"543396","IRCTC":"542830","POLYCAB":"542652","GODREJCP":"532424","MARICO":"531642","COLPAL":"500830","DABUR":"500096","EMAMILTD":"531162","ALKEM":"539523","TORNTPHARM":"500420","AUROPHARMA":"524804","GLAXO":"500660","PFIZER":"500680","ABBOTINDIA":"500488","CHOLAFIN":"500878","MFSL":"500271","ICICIGI":"540716","ICICIPRULI":"540133","SBICARD":"543066","SHRIRAMFIN":"511218","RECLTD":"532955","PFC":"532810","IRFC":"543257","NHPC":"533098","SJVN":"533206","HAL":"541154","BDL":"541143","COCHINSHIP":"526881","GRSE":"543582","MAZAGON":"543237","RVNL":"542649","RAILTEL":"543265","IRCON":"541956","HUDCO":"540530","NBCC":"534309","BEML":"500048","BHEL":"500103","NLC":"513683","SAIL":"500113","NMDC":"526371","MOIL":"532756","NALCO":"532234","HINDZINC":"500188","VEDL":"500295","HINDCOPPER":"513599","GMRINFRA":"532754","ADANIPOWER":"533096","ADANITRANS":"542066","ADANIGREEN":"541578","ADANIENT":"512599","ADANIPORTS":"532921","AWL":"543458",
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
                    results.append({"title": f"Dividend â¹{row['Dividends']:.2f}/share", "category": "Dividend", "sub": "Corporate Action", "date": str(date)[:10], "url": "", "exchange": "NSE"})
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

    # Reddit â search r/IndianStockMarket via old.reddit JSON
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



def run_miro_backtest(df: "pd.DataFrame", threshold: float = 8.0) -> dict:
    """
    Scan historical OHLCV for past Miro score signals above threshold.
    Uses a rolling compute of Miro score components, measures 15-day forward return.
    Returns win_rate, avg_gain, avg_loss, n_signals, returns_list.
    """
    import numpy as np
    results = []
    if df is None or len(df) < 60:
        return {}
    close = df["Close"].values
    vol   = df["Volume"].values
    n = len(close)
    fwd = 15
    for i in range(30, n - fwd):
        sl = close[max(0,i-19):i+1]
        if len(sl) < 10: continue
        ma20 = sl.mean()
        ma50_sl = close[max(0,i-49):i+1].mean() if i >= 49 else sl.mean()
        rsi_gain = sum(max(c-p,0) for c,p in zip(sl[1:],sl[:-1])) / max(len(sl)-1,1)
        rsi_loss = sum(max(p-c,0) for c,p in zip(sl[1:],sl[:-1])) / max(len(sl)-1,1)
        rsi = 100 - 100/(1+rsi_gain/rsi_loss) if rsi_loss > 0 else 50
        z = (close[i]-ma20) / (np.std(sl)+1e-9)
        vol_ratio = vol[i] / (np.mean(vol[max(0,i-19):i])+1e-9)
        tr_vals = [abs(close[k]-close[k-1]) for k in range(max(1,i-13),i+1)]
        atr = np.mean(tr_vals) if tr_vals else 1
        atr_pct = atr / close[i] * 100
        # Miro components (simplified)
        s = 0.0
        if close[i] > ma50_sl: s += 2
        if 40 < rsi < 70:      s += 2
        elif rsi < 40:         s += 1
        if z < -0.3:           s += 2
        elif -0.3 <= z < 0.5:  s += 1
        if vol_ratio > 1.2:    s += 2
        if atr_pct < 3:        s += 2
        elif atr_pct < 5:      s += 1
        miro = min(s, 10)
        if miro >= threshold:
            fwd_ret = (close[i+fwd] - close[i]) / close[i] * 100
            results.append(round(fwd_ret, 2))
    if not results:
        return {}
    wins = [r for r in results if r > 0]
    losses = [r for r in results if r <= 0]
    return {
        "win_rate":  round(len(wins)/len(results)*100),
        "avg_gain":  round(sum(wins)/len(wins), 1) if wins else 0,
        "avg_loss":  round(sum(losses)/len(losses), 1) if losses else 0,
        "n_signals": len(results),
        "returns":   results[-30:],
    }


def run_monte_carlo(ind: dict, n_sims: int = 1000, horizon: int = 15,
                    target_pct: float = 5.0, stop_pct: float = -2.0) -> dict:
    """
    GBM Monte Carlo: simulate 1000 price paths using ATR-derived volatility
    and Miro-score-biased drift. Returns probability of hitting target before stop.
    """
    import numpy as np, math
    price  = ind.get("price", 100)
    atr    = ind.get("atr", price * 0.02)
    miro   = ind.get("miro_score", 5)
    adx    = ind.get("adx", 20)
    # Daily vol from ATR
    daily_vol = atr / price
    # Drift: Miro provides a mild positive bias, ADX strength amplifies it
    adx_factor = min(adx / 50, 1.0)
    daily_drift = ((miro - 5) / 5) * 0.002 * adx_factor
    target = price * (1 + target_pct/100)
    stop   = price * (1 + stop_pct/100)
    hits_target, hits_stop = 0, 0
    cone_paths = {"p90":[], "p50":[], "p10":[]}
    all_finals = []
    rng = np.random.default_rng(42)
    path_snapshots = []
    for sim in range(n_sims):
        p = price
        hit_t = hit_s = False
        day_prices = [price]
        for d in range(horizon):
            shock = rng.normal(daily_drift, daily_vol)
            p *= math.exp(shock)
            day_prices.append(p)
            if not hit_t and not hit_s:
                if p >= target: hit_t = True
                elif p <= stop: hit_s = True
        if hit_t: hits_target += 1
        elif hit_s: hits_stop += 1
        all_finals.append(p)
        path_snapshots.append(day_prices)
    # Build cone: p10/p50/p90 at each day
    finals = np.array(all_finals)
    prob_target = round(hits_target / n_sims * 100)
    prob_stop   = round(hits_stop / n_sims * 100)
    expected    = round((finals.mean() - price) / price * 100, 1)
    # Cone paths
    snap_arr = np.array(path_snapshots)
    cone_p90 = [round((np.percentile(snap_arr[:,d], 90) - price)/price*100, 2) for d in range(horizon+1)]
    cone_p50 = [round((np.percentile(snap_arr[:,d], 50) - price)/price*100, 2) for d in range(horizon+1)]
    cone_p10 = [round((np.percentile(snap_arr[:,d], 10) - price)/price*100, 2) for d in range(horizon+1)]
    return {
        "prob_target":  prob_target,
        "prob_stop":    prob_stop,
        "expected":     expected,
        "target_pct":   target_pct,
        "stop_pct":     stop_pct,
        "horizon":      horizon,
        "cone_p90":     cone_p90,
        "cone_p50":     cone_p50,
        "cone_p10":     cone_p10,
        "daily_vol_pct": round(daily_vol*100, 1),
        "miro":         miro,
        "adx":          adx,
    }


def render_miro_backtest(bt: dict, symbol: str):
    """Render Miro Performance Backtest as a Chart.js bar chart."""
    if not bt or not bt.get("returns"):
        st.markdown('<div style="color:#555;font-size:0.85rem;padding:8px 0;">Not enough historical data for backtest.</div>', unsafe_allow_html=True)
        return
    import json as _json
    wr  = bt["win_rate"]
    ag  = bt["avg_gain"]
    al  = bt["avg_loss"]
    ns  = bt["n_signals"]
    rets = bt["returns"]
    wr_col = "#00c851" if wr >= 65 else "#ffaa00" if wr >= 55 else "#ff4444"
    ag_col = "#00c851" if ag > 0 else "#ff4444"
    colors_js = _json.dumps(["#00c851cc" if v >= 0 else "#ff4444cc" for v in rets])
    data_js   = _json.dumps(rets)
    labels_js = _json.dumps([f"S{i+1}" for i in range(len(rets))])
    st.markdown(f"""
<div style="display:flex;gap:10px;margin-bottom:12px;flex-wrap:wrap;">
  <div style="background:#0d0d0d;border:1px solid #1a1a1a;border-radius:6px;padding:9px 12px;flex:1;min-width:70px;">
    <div style="font-size:0.6rem;color:#555;font-family:monospace;letter-spacing:0.1em;text-transform:uppercase;margin-bottom:3px;">Win rate</div>
    <div style="font-size:1.1rem;font-weight:600;font-family:monospace;color:{wr_col};">{wr}%</div>
  </div>
  <div style="background:#0d0d0d;border:1px solid #1a1a1a;border-radius:6px;padding:9px 12px;flex:1;min-width:70px;">
    <div style="font-size:0.6rem;color:#555;font-family:monospace;letter-spacing:0.1em;text-transform:uppercase;margin-bottom:3px;">Avg gain</div>
    <div style="font-size:1.1rem;font-weight:600;font-family:monospace;color:{ag_col};">+{ag}%</div>
  </div>
  <div style="background:#0d0d0d;border:1px solid #1a1a1a;border-radius:6px;padding:9px 12px;flex:1;min-width:70px;">
    <div style="font-size:0.6rem;color:#555;font-family:monospace;letter-spacing:0.1em;text-transform:uppercase;margin-bottom:3px;">Avg loss</div>
    <div style="font-size:1.1rem;font-weight:600;font-family:monospace;color:#ff4444;">{al}%</div>
  </div>
  <div style="background:#0d0d0d;border:1px solid #1a1a1a;border-radius:6px;padding:9px 12px;flex:1;min-width:70px;">
    <div style="font-size:0.6rem;color:#555;font-family:monospace;letter-spacing:0.1em;text-transform:uppercase;margin-bottom:3px;">Signals</div>
    <div style="font-size:1.1rem;font-weight:600;font-family:monospace;color:#aaa;">{ns}</div>
  </div>
</div>""", unsafe_allow_html=True)
    st.components.v1.html(f"""
<div style="background:#0d0d0d;padding:8px;border-radius:6px;">
<canvas id="bt-chart" height="120"></canvas>
</div>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
<script>
new Chart(document.getElementById('bt-chart'), {{
  type:'bar',
  data:{{labels:{labels_js},datasets:[{{data:{data_js},backgroundColor:{colors_js},borderRadius:3,borderSkipped:false}}]}},
  options:{{
    responsive:true,maintainAspectRatio:false,
    plugins:{{legend:{{display:false}},tooltip:{{callbacks:{{label:c=>c.raw.toFixed(1)+'%'}}}}}},
    scales:{{
      x:{{ticks:{{display:false}},grid:{{color:'#1a1a1a'}},border:{{color:'#2a2a2a'}}}},
      y:{{ticks:{{color:'#555',font:{{family:'monospace',size:10}},callback:v=>v+'%'}},grid:{{color:'#1a1a1a'}},border:{{color:'#2a2a2a'}}}}
    }}
  }}
}});
</script>""", height=150)
    st.markdown('<div style="font-size:0.65rem;color:#444;font-family:monospace;margin-top:4px;">Each bar = 15-day forward return after Miro signal. Lookback: full history.</div>', unsafe_allow_html=True)


def render_monte_carlo(mc: dict):
    """Render Monte Carlo probability cone as inline SVG + stats."""
    if not mc:
        st.markdown('<div style="color:#555;font-size:0.85rem;padding:8px 0;">Monte Carlo data unavailable.</div>', unsafe_allow_html=True)
        return
    import json as _json
    pt  = mc["prob_target"]
    ps  = mc["prob_stop"]
    exp = mc["expected"]
    tgt = mc["target_pct"]
    stp = mc["stop_pct"]
    hz  = mc["horizon"]
    p90 = mc["cone_p90"]
    p50 = mc["cone_p50"]
    p10 = mc["cone_p10"]
    dvol = mc["daily_vol_pct"]
    pt_col = "#00c851" if pt >= 65 else "#ffaa00" if pt >= 50 else "#ff4444"
    # Stats row
    st.markdown(f"""
<div style="display:flex;gap:10px;margin-bottom:12px;flex-wrap:wrap;">
  <div style="background:#0d0d0d;border:1px solid #1a1a1a;border-radius:6px;padding:9px 12px;flex:1;">
    <div style="font-size:0.6rem;color:#555;font-family:monospace;letter-spacing:0.1em;text-transform:uppercase;margin-bottom:3px;">Hit +{tgt}%</div>
    <div style="font-size:1.1rem;font-weight:600;font-family:monospace;color:{pt_col};">{pt}%</div>
  </div>
  <div style="background:#0d0d0d;border:1px solid #1a1a1a;border-radius:6px;padding:9px 12px;flex:1;">
    <div style="font-size:0.6rem;color:#555;font-family:monospace;letter-spacing:0.1em;text-transform:uppercase;margin-bottom:3px;">Hit {stp}%</div>
    <div style="font-size:1.1rem;font-weight:600;font-family:monospace;color:#ff4444;">{ps}%</div>
  </div>
  <div style="background:#0d0d0d;border:1px solid #1a1a1a;border-radius:6px;padding:9px 12px;flex:1;">
    <div style="font-size:0.6rem;color:#555;font-family:monospace;letter-spacing:0.1em;text-transform:uppercase;margin-bottom:3px;">Expected</div>
    <div style="font-size:1.1rem;font-weight:600;font-family:monospace;color:#ffaa00;">{exp:+.1f}%</div>
  </div>
  <div style="background:#0d0d0d;border:1px solid #1a1a1a;border-radius:6px;padding:9px 12px;flex:1;">
    <div style="font-size:0.6rem;color:#555;font-family:monospace;letter-spacing:0.1em;text-transform:uppercase;margin-bottom:3px;">Daily vol</div>
    <div style="font-size:1.1rem;font-weight:600;font-family:monospace;color:#aaa;">{dvol}%</div>
  </div>
</div>""", unsafe_allow_html=True)
    # Build SVG cone
    W, H, pl, pr, pt_, pb = 440, 180, 50, 30, 15, 30
    cw = W - pl - pr
    ch = H - pt_ - pb
    # Y scale: center at 0, show -8% to +10%
    y_min, y_max = -8, 10
    def ypx(pct): return pt_ + ch - (pct - y_min)/(y_max - y_min)*ch
    def xpx(i):   return pl + i/hz * cw
    # Build polygon points for cone (p10 to p90 shaded)
    p90_pts = " ".join(f"{xpx(i):.1f},{ypx(p90[i]):.1f}" for i in range(hz+1))
    p10_pts = " ".join(f"{xpx(i):.1f},{ypx(p10[i]):.1f}" for i in range(hz, -1, -1))
    cone_poly = p90_pts + " " + p10_pts
    p50_pts  = " ".join(f"{xpx(i):.1f},{ypx(p50[i]):.1f}" for i in range(hz+1))
    y0   = ypx(0)
    ytgt = ypx(tgt)
    ystp = ypx(stp)
    svg = f"""<svg viewBox="0 0 {W} {H}" style="width:100%;background:#0d0d0d;border-radius:6px;display:block;">
  <line x1="{pl}" y1="{y0:.0f}" x2="{W-pr}" y2="{y0:.0f}" stroke="#333" stroke-width="0.5" stroke-dasharray="3 3"/>
  <line x1="{pl}" y1="{ytgt:.0f}" x2="{W-pr}" y2="{ytgt:.0f}" stroke="#00c85140" stroke-width="0.8" stroke-dasharray="2 4"/>
  <line x1="{pl}" y1="{ystp:.0f}" x2="{W-pr}" y2="{ystp:.0f}" stroke="#ff444440" stroke-width="0.8" stroke-dasharray="2 4"/>
  <polygon points="{cone_poly}" fill="#ff660010" stroke="none"/>
  <polyline points="{p50_pts}" fill="none" stroke="#ffaa00" stroke-width="1.5"/>
  <circle cx="{xpx(0):.1f}" cy="{ypx(0):.1f}" r="3" fill="#ff6600"/>
  <text x="{pl-4}" y="{y0+4:.0f}" text-anchor="end" font-size="9" fill="#555" font-family="monospace">0%</text>
  <text x="{pl-4}" y="{ytgt+4:.0f}" text-anchor="end" font-size="9" fill="#00c85188" font-family="monospace">+{tgt}%</text>
  <text x="{pl-4}" y="{ystp+4:.0f}" text-anchor="end" font-size="9" fill="#ff444488" font-family="monospace">{stp}%</text>
  <text x="{W-pr}" y="{ytgt+4:.0f}" text-anchor="start" font-size="9" fill="#00c85188" font-family="monospace"> target</text>
  <text x="{W-pr}" y="{ystp+4:.0f}" text-anchor="start" font-size="9" fill="#ff444488" font-family="monospace"> stop</text>
  <text x="{xpx(hz):.0f}" y="{H-2}" text-anchor="end" font-size="9" fill="#444" font-family="monospace">Day {hz}</text>
  <text x="{pl+2}" y="{H-2}" text-anchor="start" font-size="9" fill="#444" font-family="monospace">Now</text>
</svg>"""
    verdict_col = "#00c851" if pt >= 65 else "#ffaa00" if pt >= 50 else "#ff4444"
    st.markdown(svg, unsafe_allow_html=True)
    st.markdown(f'<div style="background:{verdict_col}18;border:1px solid {verdict_col}35;border-radius:6px;padding:8px 12px;font-size:0.78rem;color:{verdict_col};font-family:monospace;margin-top:8px;">{pt}% probability of hitting +{tgt}% target before {stp}% stop Â· 1,000 GBM simulations Â· {hz}-day horizon</div>', unsafe_allow_html=True)



def render_ticker_velocity(ind: dict, symbol: str):
    """Ticker Velocity â how fast institutional momentum is building."""
    miro      = ind.get("miro_score", 0)
    vol_ratio = ind.get("vol_ratio", 1)
    pct_chg   = ind.get("change_pct", 0)
    adx       = ind.get("adx", 0)
    # Velocity score: weighted composite of Miro + volume surge + ADX
    vel = min(100, int(miro * 7 + min(max(vol_ratio - 1, 0), 4) * 7 + min(adx / 50, 1) * 20))
    vel_col = "#00c851" if vel>=70 else "#ffaa00" if vel>=40 else "#ff4444"
    vel_lbl = "Hot â¡" if vel>=70 else "Building" if vel>=40 else "Quiet"
    # Narrative drivers derived from indicators
    drivers = []
    if vol_ratio >= 2.0:  drivers.append(("Volume surge", f"{vol_ratio:.1f}x avg", "#ff6600"))
    elif vol_ratio >= 1.5: drivers.append(("Volume elevated", f"{vol_ratio:.1f}x avg", "#ffaa00"))
    if miro >= 7:          drivers.append(("Strong Miro signal", f"{miro}/10", "#00c851"))
    elif miro >= 5:        drivers.append(("Moderate momentum", f"{miro}/10", "#ffaa00"))
    if adx >= 25:          drivers.append(("Strong trend (ADX)", f"{adx:.0f}", "#3399ff"))
    if pct_chg >= 1:       drivers.append(("Price breakout", f"{pct_chg:+.2f}%", "#00c851"))
    elif pct_chg <= -1:    drivers.append(("Price declining", f"{pct_chg:+.2f}%", "#ff4444"))
    if not drivers:        drivers.append(("No dominant signal", "Monitor", "#555"))

    gauge_html = f"""
<div style="display:flex;align-items:center;gap:14px;margin-bottom:12px;">
  <div style="text-align:center;">
    <div style="font-size:2.2rem;font-weight:700;font-family:monospace;color:{vel_col};">{vel}</div>
    <div style="font-size:0.6rem;color:#555;font-family:monospace;letter-spacing:0.1em;text-transform:uppercase;">Velocity</div>
  </div>
  <div style="flex:1;">
    <div style="background:#1a1a1a;border-radius:4px;height:8px;margin-bottom:6px;">
      <div style="width:{vel}%;height:8px;border-radius:4px;background:{vel_col};transition:width 0.3s;"></div>
    </div>
    <div style="font-size:0.75rem;font-family:monospace;color:{vel_col};font-weight:600;">{vel_lbl}</div>
  </div>
</div>"""
    st.markdown(gauge_html, unsafe_allow_html=True)
    for name, val, col in drivers:
        st.markdown(f'<div style="display:flex;justify-content:space-between;padding:5px 0;border-bottom:1px solid #1a1a1a;font-size:0.78rem;"><span style="color:#888;">{name}</span><span style="color:{col};font-family:monospace;font-weight:600;">{val}</span></div>', unsafe_allow_html=True)


# ── Sector Index Map ─────────────────────────────────────────────────────────
SECTOR_INDEX_MAP = {
    "IT":           "^CNXIT",
    "Banking":      "^NSEBANK",
    "Metals":       "^CNXMETAL",
    "Energy":       "^CNXENERGY",
    "Pharma":       "^CNXPHARMA",
    "FMCG":         "^CNXFMCG",
    "Auto":         "^CNXAUTO",
    "Realty":       "^CNXREALTY",
    "Infra":        "^CNXINFRA",
    "Conglomerate": "^NSEI",
    "Finance":      "^CNXFINANCE",
}


@st.cache_data(ttl=3600, show_spinner=False)
def compute_sector_correlation(symbol: str, sector: str) -> dict:
    """Compute 20-day rolling correlation of stock vs its sector index."""
    try:
        idx_ticker = SECTOR_INDEX_MAP.get(sector, "^NSEI")
        stock_tk   = yf.Ticker(symbol + ".NS")
        idx_tk     = yf.Ticker(idx_ticker)
        stock_hist = stock_tk.history(period="35d")["Close"]
        idx_hist   = idx_tk.history(period="35d")["Close"]
        if len(stock_hist) < 10 or len(idx_hist) < 10:
            return {"error": True}
        stock_ret = stock_hist.pct_change().dropna()
        idx_ret   = idx_hist.pct_change().dropna()
        common    = stock_ret.index.intersection(idx_ret.index)
        if len(common) < 10:
            return {"error": True}
        s    = stock_ret.loc[common].values[-20:]
        b    = idx_ret.loc[common].values[-20:]
        corr = float(np.corrcoef(s, b)[0, 1])
        s20  = float((stock_hist.iloc[-1] / stock_hist.iloc[-min(20, len(stock_hist))] - 1) * 100)
        b20  = float((idx_hist.iloc[-1]   / idx_hist.iloc[-min(20, len(idx_hist))]   - 1) * 100)
        rel_str = s20 - b20
        return {
            "corr":    round(corr, 2),
            "rel_str": round(rel_str, 2),
            "s20":     round(s20, 2),
            "b20":     round(b20, 2),
            "sector":  sector,
            "idx":     idx_ticker,
            "error":   False,
        }
    except Exception:
        return {"error": True}


def render_sector_correlation(sc: dict, sector: str):
    """Sector Correlation panel."""
    if sc.get("error"):
        st.markdown('<div style="color:#555;font-size:0.78rem;font-family:monospace;">Sector data unavailable</div>', unsafe_allow_html=True)
        return
    corr    = sc["corr"]
    rel_str = sc["rel_str"]
    s20     = sc["s20"]
    b20     = sc["b20"]
    if corr >= 0.6 and rel_str > 0:
        verdict = "Sector Tailwind \u2705"
        v_col   = "#00c851"
    elif corr >= 0.6 and rel_str <= 0:
        verdict = "Sector Headwind \u26a0\ufe0f"
        v_col   = "#ffaa00"
    elif corr < 0.3:
        verdict = "Diverging from Sector"
        v_col   = "#3399ff"
    else:
        verdict = "Weakly Correlated"
        v_col   = "#888888"
    corr_col = "#00c851" if corr >= 0.6 else "#ffaa00" if corr >= 0.3 else "#ff4444"
    rel_col  = "#00c851" if rel_str > 0 else "#ff4444"
    s20_col  = "#00c851" if s20 > 0 else "#ff4444"
    b20_col  = "#00c851" if b20 > 0 else "#ff4444"
    html = f"""
<div style="font-size:0.78rem;font-family:monospace;">
  <div style="display:flex;justify-content:space-between;padding:5px 0;border-bottom:1px solid #1a1a1a;">
    <span style="color:#888;">Sector</span>
    <span style="color:#ccc;font-weight:600;">{sector}</span>
  </div>
  <div style="display:flex;justify-content:space-between;padding:5px 0;border-bottom:1px solid #1a1a1a;">
    <span style="color:#888;">20-day Correlation</span>
    <span style="color:{corr_col};font-weight:700;">{corr:+.2f}</span>
  </div>
  <div style="display:flex;justify-content:space-between;padding:5px 0;border-bottom:1px solid #1a1a1a;">
    <span style="color:#888;">Stock 20d Return</span>
    <span style="color:{s20_col};font-weight:600;">{s20:+.1f}%</span>
  </div>
  <div style="display:flex;justify-content:space-between;padding:5px 0;border-bottom:1px solid #1a1a1a;">
    <span style="color:#888;">Sector 20d Return</span>
    <span style="color:{b20_col};font-weight:600;">{b20:+.1f}%</span>
  </div>
  <div style="display:flex;justify-content:space-between;padding:5px 0;border-bottom:1px solid #1a1a1a;">
    <span style="color:#888;">Relative Strength</span>
    <span style="color:{rel_col};font-weight:700;">{rel_str:+.1f}%</span>
  </div>
  <div style="margin-top:10px;padding:8px 10px;border-radius:5px;border:1px solid #2a2a2a;background:#0d0d0d;text-align:center;">
    <span style="color:{v_col};font-weight:700;font-size:0.82rem;">{verdict}</span>
  </div>
</div>"""
    st.markdown(html, unsafe_allow_html=True)


def render_probability_cone(ind: dict, mc: dict):
    """Probability Cone â ATR-based uncertainty cone with Exhaustion flag."""
    if not mc:
        st.markdown('<div style="color:#555;font-size:0.85rem;">Run analysis to see cone.</div>', unsafe_allow_html=True)
        return
    pt      = mc.get("prob_target", 50)
    ps      = mc.get("prob_stop",   50)
    exp     = mc.get("expected",    0)
    tgt     = mc.get("target_pct",  5)
    stp     = mc.get("stop_pct",   -2)
    miro    = ind.get("miro_score", 0)
    z       = ind.get("z_score",    0)
    # Exhaustion check: high Miro but Z > 1.5 (stretched above mean)
    exhausted = miro >= 7 and z > 1.5
    pt_col = "#00c851" if pt >= 65 else "#ffaa00" if pt >= 50 else "#ff4444"
    verdict_lbl  = "â ï¸ Exhausted â Wait for pullback" if exhausted else (
                   "â Momentum aligned" if pt >= 65 else "â ï¸ Proceed with caution" if pt >= 50 else "â Risk/reward unfavourable")
    verdict_col  = "#ffaa00" if exhausted else pt_col
    st.markdown(f"""
<div style="display:flex;gap:10px;margin-bottom:12px;flex-wrap:wrap;">
  <div style="background:#0d0d0d;border:1px solid #1a1a1a;border-radius:6px;padding:8px 12px;flex:1;">
    <div style="font-size:0.6rem;color:#555;font-family:monospace;letter-spacing:0.1em;text-transform:uppercase;margin-bottom:3px;">Hit +{tgt}%</div>
    <div style="font-size:1.1rem;font-weight:600;font-family:monospace;color:{pt_col};">{pt}%</div>
  </div>
  <div style="background:#0d0d0d;border:1px solid #1a1a1a;border-radius:6px;padding:8px 12px;flex:1;">
    <div style="font-size:0.6rem;color:#555;font-family:monospace;letter-spacing:0.1em;text-transform:uppercase;margin-bottom:3px;">Hit {stp}%</div>
    <div style="font-size:1.1rem;font-weight:600;font-family:monospace;color:#ff4444;">{ps}%</div>
  </div>
  <div style="background:#0d0d0d;border:1px solid #1a1a1a;border-radius:6px;padding:8px 12px;flex:1;">
    <div style="font-size:0.6rem;color:#555;font-family:monospace;letter-spacing:0.1em;text-transform:uppercase;margin-bottom:3px;">Expected</div>
    <div style="font-size:1.1rem;font-weight:600;font-family:monospace;color:#ffaa00;">{exp:+.1f}%</div>
  </div>
</div>
<div style="background:{verdict_col}18;border:1px solid {verdict_col}35;border-radius:6px;padding:8px 12px;font-size:0.78rem;color:{verdict_col};font-family:monospace;">{verdict_lbl}</div>""",
    unsafe_allow_html=True)


def render_rubber_band(ind: dict):
    """Rubber Band Index â distance from MA20, mean reversion risk."""
    cp    = ind.get("price",  0)
    ma20  = ind.get("ma20",   cp or 1)
    ma8   = ind.get("ma20",   cp or 1)  # use MA20 as proxy if EMA8 not computed
    z     = ind.get("z_score", 0)
    dist_pct = (cp - ma20) / ma20 * 100 if ma20 else 0
    abs_dist = abs(dist_pct)
    # Tension level
    if abs_dist >= 10:   tension, t_col, t_lbl = 3, "#ff4444", "Overstretched â Wait"
    elif abs_dist >= 5:  tension, t_col, t_lbl = 2, "#ffaa00", "Stretched â Caution"
    else:                tension, t_col, t_lbl = 1, "#00c851", "Normal â OK to enter"
    above = dist_pct >= 0
    bar_pct = min(abs_dist / 15 * 100, 100)
    st.markdown(f"""
<div style="margin-bottom:10px;">
  <div style="display:flex;justify-content:space-between;font-size:0.75rem;margin-bottom:4px;">
    <span style="color:#888;font-family:monospace;">Distance from MA20</span>
    <span style="color:{t_col};font-family:monospace;font-weight:600;">{dist_pct:+.1f}%</span>
  </div>
  <div style="background:#1a1a1a;border-radius:3px;height:6px;margin-bottom:8px;">
    <div style="width:{bar_pct:.0f}%;height:6px;border-radius:3px;background:{t_col};"></div>
  </div>
  <div style="font-size:0.75rem;color:{t_col};font-family:monospace;font-weight:600;margin-bottom:8px;">{t_lbl}</div>
</div>
<div style="display:flex;gap:10px;">
  <div style="background:#0d0d0d;border:1px solid #1a1a1a;border-radius:6px;padding:8px 12px;flex:1;">
    <div style="font-size:0.6rem;color:#555;font-family:monospace;letter-spacing:0.1em;text-transform:uppercase;margin-bottom:3px;">Z-Score</div>
    <div style="font-size:1rem;font-weight:600;font-family:monospace;color:{"#00c851" if z<-0.5 else "#ff4444" if z>1.5 else "#ffaa00"};">{z:.2f}</div>
  </div>
  <div style="background:#0d0d0d;border:1px solid #1a1a1a;border-radius:6px;padding:8px 12px;flex:1;">
    <div style="font-size:0.6rem;color:#555;font-family:monospace;letter-spacing:0.1em;text-transform:uppercase;margin-bottom:3px;">MA20</div>
    <div style="font-size:1rem;font-weight:600;font-family:monospace;color:#aaa;">â¹{ma20:,.2f}</div>
  </div>
  <div style="background:#0d0d0d;border:1px solid #1a1a1a;border-radius:6px;padding:8px 12px;flex:1;">
    <div style="font-size:0.6rem;color:#555;font-family:monospace;letter-spacing:0.1em;text-transform:uppercase;margin-bottom:3px;">Tension</div>
    <div style="font-size:1rem;font-weight:600;font-family:monospace;color:{t_col};">{"High" if tension==3 else "Med" if tension==2 else "Low"}</div>
  </div>
</div>""", unsafe_allow_html=True)


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
            sc_sym = "â²" if sc=="Bullish" else "â¼" if sc=="Bearish" else "â"
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
    """Pull key fundamental metrics from yfinance ticker.info with fast_info fallback."""
    try:
        tk   = yf.Ticker(symbol.upper().strip() + ".NS")
        info = {}
        try:
            info = tk.info or {}
        except Exception:
            pass
        # fast_info fallback for market cap / price if info is sparse
        fi = {}
        try:
            fi = tk.fast_info or {}
        except Exception:
            pass
        def _pct(v): return f"{v*100:.1f}%" if v is not None else "â"
        def _x(v,d=1): return f"{v:.{d}f}x" if v is not None else "â"
        def _n(v,d=1): return f"{v:.{d}f}" if v is not None else "â"
        def _cr(v): return f"â¹{v/1e7:,.0f} Cr" if v is not None else "â"
        # Try getting missing fields from fast_info
        mkt_cap = info.get("marketCap") or getattr(fi, "market_cap", None)
        if not info and not mkt_cap:
            return {}
        return {
            "pe":          _n(info.get("trailingPE"),1),
            "fwd_pe":      _n(info.get("forwardPE"),1),
            "ev_ebitda":   _x(info.get("enterpriseToEbitda")),
            "pb":          _x(info.get("priceToBook") or getattr(fi,"price_to_book",None)),
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
            "sector":      info.get("sector") or info.get("industry") or "â",
            "employees":   f"{info.get('fullTimeEmployees',0):,}" if info.get("fullTimeEmployees") else "â",
            "mkt_cap":     _cr(mkt_cap),
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
        + fi("P/E (TTM)", fund.get("pe","â"), pe_c(fund.get("_pe_raw")))
        + fi("Forward P/E", fund.get("fwd_pe","â"), pe_c(fund.get("_pe_raw")))
        + fi("EV / EBITDA", fund.get("ev_ebitda","â"))
        + fi("Price / Book", fund.get("pb","â"))
        + fi("Price / Sales", fund.get("ps","â"))
        + fi("Sector", fund.get("sector","â"))
        + '</div>'
        + '<div class="fund-section-head">Financials</div>'
        + '<div class="fund-grid">'
        + fi("Revenue", fund.get("revenue","â"))
        + fi("Net Income", fund.get("net_income","â"), pm_c(fund.get("_pm_raw")))
        + fi("Profit Margin", fund.get("profit_margin","â"), pm_c(fund.get("_pm_raw")))
        + fi("ROE", fund.get("roe","â"), roe_c(fund.get("_roe_raw")))
        + fi("Debt / Equity", fund.get("debt_equity","â"), de_c(fund.get("_de_raw")))
        + fi("Current Ratio", fund.get("current_ratio","â"))
        + '</div>'
        + '<div class="fund-section-head">Ownership & Dividends</div>'
        + '<div class="fund-grid">'
        + fi("Promoter Hold", fund.get("promoter","â"))
        + fi("Inst. Holding", fund.get("inst_hold","â"))
        + fi("Div Yield", fund.get("div_yield","â"))
        + fi("Payout Ratio", fund.get("payout","â"))
        + fi("Employees", fund.get("employees","â"))
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


# ââ Company metadata ââââââââââââââââââââââââââââââââââââââââââââââââââââââââââ
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
    Fetch stock-specific filings and news via yfinance â no API key needed.
    Returns: Yahoo Finance news feed + upcoming corporate calendar events.
    """
    ticker_sym = symbol.upper().strip() + ".NS"
    results = []
    try:
        tk = yf.Ticker(ticker_sym)

        # 1. Yahoo Finance news â stock-specific articles
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

        # 2. Calendar â earnings date, ex-dividend date
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
                            "title":       f"Dividend: â¹{row['Dividends']:.2f} per share",
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
    """Stock-specific news. Chain: IndianAPI â GNews â Finnhub â Moneycontrol RSS."""
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

# ââ Indicators ââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââ
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

    # ââ Miro Score â Volume-first institutional momentum âââââââââââââââââ
    score = 0.0
    # 1. Volume Multiplier (primary factor â institutional interest)
    if   vol_ratio >= 5.0: score += 5.0  # Miro Spike
    elif vol_ratio >= 2.0: score += 3.0
    elif vol_ratio >= 1.5: score += 2.0
    # 2. Price Change % (confirms volume is buying not distribution)
    pct_chg = (cp - close[-2]) / close[-2] * 100 if len(close) >= 2 else 0
    if   pct_chg >= 5.0: score += 3.0
    elif pct_chg >= 3.0: score += 2.0
    elif pct_chg >= 1.0: score += 1.0
    # 3. Close position â top 25% of day range signals strength
    day_range = high[-1] - low[-1] if len(high) > 0 else 0
    if day_range > 0 and (cp - low[-1]) / day_range >= 0.75: score += 1.0
    # 4. Price above MA20 (trend confirmation)
    if cp > ma20: score += 1.0
    score = max(0.0, min(10.0, round(score, 1)))


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

# ââ AI Agents âââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââ
def build_context(symbol, ind, quote, fund, news, rec) -> str:
        news_txt = "\n".join([f"- {n.get('title', n.get('headline',''))}" for n in news[:4]]) or "No recent news."
        rec_txt  = f"Buy:{rec.get('buy',0)} Hold:{rec.get('hold',0)} Sell:{rec.get('sell',0)}" if rec else "No analyst data."
        miro     = ind.get("miro_score", 0)
        vol_r    = ind.get("vol_ratio", 1)
        pct_chg  = ind.get("change_pct", 0)
        ma_bull  = ind.get("price",0) > ind.get("ma50",0) > ind.get("ma200",0)
        return f"""
    Stock: {symbol} | Price: â¹{ind.get("price",0):,.2f} ({pct_chg:+.2f}%)
    Company: {quote.get("name", symbol)}
    
    MIRO SCORE: {miro}/10 (Volume-first institutional momentum)
    - Volume ratio: {vol_r:.2f}x average ({"Miro Spike" if vol_r>=5 else "High" if vol_r>=2 else "Elevated" if vol_r>=1.5 else "Normal"})
    - Price change today: {pct_chg:+.2f}%
    - MA Alignment: {"Bullish (price > MA50 > MA200)" if ma_bull else "Bearish (price below key MAs)"}
    - MA20: â¹{ind.get("ma20",0):,.2f} | MA50: â¹{ind.get("ma50",0):,.2f} | MA200: â¹{ind.get("ma200",0):,.2f}
    - Z-Score: {ind.get("z_score",0):.2f} (mean reversion signal)
    - ADX: {ind.get("adx",0):.1f} ({"Strong trend" if ind.get("adx",0)>=25 else "Weak/no trend"})
    - Weekly trend: {ind.get("weekly_trend","N/A")} ({ind.get("weekly_chg",0):+.2f}% this week)
    - ATR(14): â¹{ind.get("atr",0):.2f} (daily volatility)
    
    FUNDAMENTALS:
    "- Sector: {fund.get('sector', quote.get('sector','N/A'))}",
    "- P/E: {fund.get('pe','N/A')} | EV/EBITDA: {fund.get('ev_ebitda','N/A')}",
    "- ROE: {fund.get('roe','N/A')} | Debt/Equity: {fund.get('debt_equity','N/A')}",
    "- Promoter: {fund.get('promoter','N/A')} | Inst: {fund.get('inst_hold','N/A')}",
    
    ANALYST CONSENSUS: {rec_txt}
    RECENT NEWS:\n{news_txt}
    """
AGENTS = [
    ("ð Bull Analyst",    "bull",    "#00c851", "You are an optimistic NSE equity analyst. Focus ONLY on Miro Score strength, volume surge, MA alignment, and weekly momentum. If Miro > 7 and volume > 1.5x average, highlight the breakout. Reference specific numbers from the data. 4-5 sentences, be concise."),
    ("ð Bear Analyst",    "bear",    "#ff4444", "You are a cautious short-seller on NSE. Identify risks using MA breakdown, ADX below 25, low Miro Score, and weak volume. Reference the Z-Score for mean reversion risk. Reference specific numbers. 4-5 sentences, be concise."),
    ("â¡ Swing Trader",    "trader",  "#ffaa00", "You are an experienced NSE swing trader. Give a concrete plan using MA levels as entry/stop zones. Use ADX to judge trend strength (>25=strong). Use the Miro Score as your momentum filter â only trade Miro > 6. Entry, stop, target, timeframe. 4-5 sentences, be concise."),
    ("ð¡ï¸ Risk Manager",   "risk",    "#3399ff", "You are a portfolio risk manager. Use the Z-Score, ATR volatility, and Probability Cone data to assess risk/reward. Flag if the stock is at the top of its 2-SD cone (Exhausted). Suggest position size as % of portfolio. 4-5 sentences, be concise."),
    ("ðï¸ Fundamentalist", "fund",    "#aa88ff", "You are a fundamental analyst. Comment on P/E, EV/EBITDA, ROE, and promoter holding. Check if the Miro momentum aligns with the fundamental picture. Highlight divergence between technicals and fundamentals. 4-5 sentences, be concise."),
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
                placeholder.markdown(full + "â")
        placeholder.markdown(full)
    except Exception as e:
        placeholder.markdown(f"*Analysis unavailable: {e}*")
    return full

# ââ Helpers âââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââ
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

# ââ Main UI âââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââ
st.markdown("""
<div class="hero">
  <h1>â¡ NIFTY SNIPER</h1>
  <p>Stock intelligence terminal Â· NSE India Â· Powered by AI agents</p>
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
    analyse = st.button("ð Analyse", key="analyse_btn")

# Popular picks
st.markdown(
    "<div style='text-align:center; color:#555555; font-size:0.8rem; margin: -8px 0 16px'>Quick picks: "
    + " Â· ".join([f"<span style='color:#555555; cursor:pointer'>{s}</span>"
                  for s in ["RELIANCE","TCS","HDFCBANK","INFY","SBIN","TITAN","BAJFINANCE","NIFTY50"]])
    + "</div>", unsafe_allow_html=True
)

# ââ Analysis ââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââ
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
        st.error(f"â Could not fetch data for **{symbol}**. Check the NSE symbol and try again.")
        st.stop()

    ind = compute_indicators(df)
    backtest  = run_miro_backtest(df)
    mc        = run_monte_carlo(ind)
    if not ind:
        st.error("â Not enough data to compute indicators.")
        st.stop()

    cp      = ind["price"]
    chg     = ind["change_pct"]
    chg_col = "#00c851" if chg >= 0 else "#ff4444"
    chg_sym = "â²" if chg >= 0 else "â¼"

    # ââ Stock Header ââââââââââââââââââââââââââââââââââââââââââââââââââââââââââ
    display_symbol = symbol.replace(".NS","").replace(".BO","")
    company_name = (quote.get('name', symbol) or symbol).replace('.NS','').replace('.BO','')
    st.markdown(f"""
<div class="section-card" style="margin-bottom:20px; border-top:2px solid #ff6600;">
  <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:12px;">
    <div>
      <div style="color:#ff6600; font-size:0.7rem; font-weight:600; letter-spacing:0.14em; text-transform:uppercase; font-family:'JetBrains Mono',monospace; margin-bottom:2px;">NSE Â· EQUITY</div>
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

    # ââ Key Metrics Row âââââââââââââââââââââââââââââââââââââââââââââââââââââââ
    miro     = ind["miro_score"]
    miro_c   = "signal-bull" if miro >= 6.5 else "signal-bear" if miro < 4 else "signal-neutral"
    z        = ind["z_score"]
    z_c      = "signal-bull" if z < -0.5 else "signal-bear" if z > 1.5 else "signal-neutral"
    weekly_c = "signal-bull" if ind.get("weekly_chg",0) > 0.5 else "signal-bear" if ind.get("weekly_chg",0) < -0.5 else "signal-neutral"
    adx      = ind["adx"]
    trend    = ind["trend"]
    tr_c     = "signal-bull" if adx >= 25 and "Up" in trend else "signal-bear" if adx >= 25 and "Down" in trend else "signal-neutral"
    cp       = ind["price"]

    # ââ Metric cards row 1: Miro / Z-Score / Weekly / ADX âââââââââââââââ
    c1, c2, c3, c4 = st.columns(4)
    c1.markdown(render_metric("Miro Score",   f"{miro}/10", score_bar(miro), miro_c), unsafe_allow_html=True)
    c2.markdown(render_metric("Z-Score",      f"{z}",       "vs 20D mean",   z_c),    unsafe_allow_html=True)
    c3.markdown(render_metric("Weekly Trend", ind.get("weekly_trend","â"), f"{ind.get('weekly_chg',0):+.2f}% this week", weekly_c), unsafe_allow_html=True)
    c4.markdown(render_metric("ADX / Trend", f"{adx} {'â Strong' if adx>=25 else 'â ï¸ Weak'}", trend.replace(" ","<br>"), tr_c), unsafe_allow_html=True)

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    # ââ Metric cards row 2: MA20 / MA50 / MA200 âââââââââââââââââââââââââ
    cm1, cm2, cm3 = st.columns(3)
    cm1.markdown(render_metric("MA 20",  f"â¹{ind['ma20']:,}",         "<span style='color:#00c851'>â² Above</span>" if cp > ind["ma20"]         else "<span style='color:#ff4444'>â¼ Below</span>"), unsafe_allow_html=True)
    cm2.markdown(render_metric("MA 50",  f"â¹{ind['ma50_display']:,}",  "<span style='color:#00c851'>â² Above</span>" if cp > ind["ma50_display"]  else "<span style='color:#ff4444'>â¼ Below</span>"), unsafe_allow_html=True)
    cm3.markdown(render_metric("MA 200", f"â¹{ind['ma200']:,}",         "<span style='color:#00c851'>â² Above</span>" if cp > ind["ma200"]         else "<span style='color:#ff4444'>â¼ Below</span>"), unsafe_allow_html=True)

    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

    # ââ Two column layout: News + Chart data left, Signals right âââââââââââââ
    left, right = st.columns([3, 2])

    # ── Sector Correlation data ───────────────────────────────────────────────
    sector_label = COMPANY_META.get(symbol, ("", "", ""))[1]
    sc = compute_sector_correlation(symbol, sector_label)

    with left:
        ll, lr = st.columns([1, 1])

        with ll:
            # ââ Fundamentals ââââââââââââââââââââââââââââââââââââââââââââ
            st.markdown('<div class="section-card">', unsafe_allow_html=True)
            st.markdown('<div class="section-title">ð Fundamentals</div>', unsafe_allow_html=True)
            render_fundamentals(fund, symbol)
            st.markdown('</div>', unsafe_allow_html=True)
            # ââ Filings ââââââââââââââââââââââââââââââââââââââââââââââââââ
            st.markdown('<div class="section-card">', unsafe_allow_html=True)
            st.markdown(f'<div class="section-title">ð Filings â {display_symbol}</div>', unsafe_allow_html=True)
            render_filings(filings, symbol)
            st.markdown('</div>', unsafe_allow_html=True)

        with lr:
            # ââ Signal Summary âââââââââââââââââââââââââââââââââââââââââââ
            st.markdown('<div class="section-card">', unsafe_allow_html=True)
            st.markdown('<div class="section-title">ð¯ Signal Summary</div>', unsafe_allow_html=True)
            signals = [
                ("Miro Score",   f"{miro}/10 â {'Strong' if miro>=6.5 else 'Weak' if miro<4 else 'Moderate'}", miro >= 6.5),
                ("MA Alignment", "â Bullish" if cp > ind["ma50"] > ind["ma200"] else "â Bearish",              cp > ind["ma50"] > ind["ma200"]),
                ("Z-Score",      "â Oversold" if z < -0.5 else ("â Extended" if z > 1.5 else "â ï¸ Neutral"), z < -0.5),
                ("Weekly Trend", ind.get("weekly_trend","â"),                                                       ind.get("weekly_chg",0) > 0),
            ]
            bull_count = sum(1 for _, _, b in signals if b)
            for label, val, bull in signals:
                col_s = "#00c851" if bull else "#ff4444" if "â" in val else "#ff8800"
                st.markdown(f'<div style="padding:6px 0;border-bottom:1px solid #1a1a1a;font-size:0.8rem;"><span style="color:#888;font-family:monospace;">{label}&nbsp;&nbsp;</span><span style="color:{col_s};font-weight:600;font-family:monospace;">{val}</span></div>', unsafe_allow_html=True)
            bull_signals = bull_count
            verdict = "STRONG BUY" if bull_signals >= 4 else "BUY" if bull_signals >= 3 else "AVOID" if bull_signals <= 1 else "HOLD"
            v_col   = "#00c851" if "BUY" in verdict else "#ff4444" if verdict == "AVOID" else "#ffaa00"
            st.markdown(f'<div style="margin-top:14px;display:flex;justify-content:flex-start;"><div style="background:#0d0d0d;border:1px solid #2a2a2a;border-top:2px solid {v_col};border-radius:6px;padding:10px 16px;text-align:center;min-width:110px;"><div style="font-size:0.58rem;color:#555;font-family:monospace;letter-spacing:0.12em;text-transform:uppercase;margin-bottom:4px;">Signal Verdict</div><div style="font-size:1.3rem;font-weight:700;font-family:monospace;color:{v_col};">{verdict}</div><div style="font-size:0.62rem;color:#444;font-family:monospace;margin-top:3px;">{bull_signals}/4 bullish</div></div></div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

            # ââ Ticker Velocity ââââââââââââââââââââââââââââââââââââââââââ
            st.markdown('<div class="section-card">', unsafe_allow_html=True)
            st.markdown('<div class="section-title">â¡ Ticker Velocity</div>', unsafe_allow_html=True)
            render_ticker_velocity(ind, display_symbol)
            st.markdown('</div>', unsafe_allow_html=True)

            # ── Sector Correlation ────────────────────────────────────────────
            st.markdown('<div class="section-card">', unsafe_allow_html=True)
            st.markdown('<div class="section-title">📡 Sector Correlation</div>', unsafe_allow_html=True)
            render_sector_correlation(sc, sector_label)
            st.markdown('</div>', unsafe_allow_html=True)

    with right:
        # ââ Miro Backtest ââââââââââââââââââââââââââââââââââââââââââââââââ
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">ð Miro Performance Backtest</div>', unsafe_allow_html=True)
        render_miro_backtest(backtest, display_symbol)
        st.markdown('</div>', unsafe_allow_html=True)

        # ââ Probability Cone âââââââââââââââââââââââââââââââââââââââââââââ
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">ð Probability Cone</div>', unsafe_allow_html=True)
        render_probability_cone(ind, mc)
        st.markdown('</div>', unsafe_allow_html=True)

        # ââ Rubber Band âââââââââââââââââââââââââââââââââââââââââââââââââââ
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">ð¯ Rubber Band Index</div>', unsafe_allow_html=True)
        render_rubber_band(ind)
        st.markdown('</div>', unsafe_allow_html=True)

        # ââ Sentiment âââââââââââââââââââââââââââââââââââââââââââââââââââââ
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">ð¡ Market Sentiment</div>', unsafe_allow_html=True)
        render_sentiment(sentiment)
        st.markdown('</div>', unsafe_allow_html=True)

        # ââ Analyst Recs ââââââââââââââââââââââââââââââââââââââââââââââââââ
        if rec:
            st.markdown('<div class="section-card">', unsafe_allow_html=True)
            st.markdown('<div class="section-title">ð¦ Analyst Consensus</div>', unsafe_allow_html=True)
            total = (rec.get("buy",0) + rec.get("hold",0) + rec.get("sell",0) + rec.get("strongBuy",0) + rec.get("strongSell",0)) or 1
            for label, key, col in [("Strong Buy","strongBuy","#ff6600"),("Buy","buy","#00c851"),("Hold","hold","#ffaa00"),("Sell","sell","#ff4444"),("Strong Sell","strongSell","#cc0000")]:
                n_rec = rec.get(key, 0)
                pct   = int(n_rec / total * 100)
                st.markdown(f'<div style="display:flex;align-items:center;gap:8px;padding:4px 0;"><span style="color:#888;font-size:0.75rem;width:80px;">{label}</span><div style="flex:1;background:#1a1a1a;border-radius:2px;height:5px;"><div style="width:{pct}%;background:{col};height:5px;border-radius:2px;"></div></div><span style="color:{col};font-size:0.72rem;font-family:monospace;width:32px;text-align:right;">{pct}%</span></div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

    # ââ AI Agent Debate âââââââââââââââââââââââââââââââââââââââââââââââââââââââ
    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">ð¤ AI Agent Debate</div>', unsafe_allow_html=True)

    client = get_anthropic()
    if not client:
        st.warning("Add ANTHROPIC_API_KEY to Streamlit secrets to enable AI agent debate.")
    else:
        context = build_context(display_symbol, ind, quote, fund, news, rec)
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
â ï¸ <strong>Not SEBI registered. Not financial advice. For educational purposes only. Always do your own research.</strong>
</div>""", unsafe_allow_html=True)


    # ââ PDF Report ââââââââââââââââââââââââââââââââââââââââââââââââââââââââ
    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
    _vc = "#00c851" if "BUY" in verdict else "#ff4444" if verdict == "AVOID" else "#ffaa00"
    _cc = "#00c851" if chg >= 0 else "#ff4444"
    _co = quote.get('name', symbol) or symbol
    _dt = datetime.now().strftime('%d %B %Y, %H:%M IST')
    _sl_rows = ""
    for _sln,_slv,_slb in [
        ("MA Alignment","Bullish" if cp>ind["ma50_display"]>ind["ma200"] else "Bearish",cp>ind["ma50_display"]>ind["ma200"]),
        ("RSI (14)",f"{ind['rsi']} â Buy Zone" if ind['rsi']<40 else f"{ind['rsi']} â Hot" if ind['rsi']>65 else f"{ind['rsi']} â Neutral",ind['rsi']<40),
        ("Z-Score",f"{ind['z_score']} â Oversold" if ind['z_score']<-0.5 else f"{ind['z_score']} â Extended" if ind['z_score']>1.5 else f"{ind['z_score']} â Neutral",ind['z_score']<-0.5),
        ("IBS",f"{ind['ibs']} â Buy" if ind['ibs']<0.3 else f"{ind['ibs']} â Sell" if ind['ibs']>0.75 else f"{ind['ibs']} â Neutral",ind['ibs']<0.3),
        ("Donchian","Near High" if cp>ind['don_high']*0.97 else "Mid Range",cp>ind['don_high']*0.97),
        ("MACD","Positive" if ind['macd']>0 else "Negative",ind['macd']>0),
        ("Volume",f"{ind['vol_ratio']}x Surge" if ind['vol_ratio']>1.5 else f"{ind['vol_ratio']}x Normal",ind['vol_ratio']>1.5),
    ]:
        _sc2 = "#00c851" if _slb else "#ff4444"
        _sl_rows += f"<tr><td style='padding:6px 12px;color:#888;font-size:12px;border-bottom:1px solid #1e1e1e;'>{_sln}</td><td style='padding:6px 12px;color:{_sc2};font-size:12px;font-weight:600;border-bottom:1px solid #1e1e1e;'>{'â' if _slb else 'â'} {_slv}</td></tr>"
    _news_rows = ""
    if news:
        for _n2 in news[:5]:
            _nh2 = (_n2.get('title') or _n2.get('headline',''))[:85]
            _ns2 = datetime.fromtimestamp(_n2.get('datetime',0)).strftime('%d %b') if _n2.get('datetime') else ''
            _news_rows += f"<tr><td style='padding:5px 12px;color:#ccc;font-size:11px;border-bottom:1px solid #1e1e1e;'>{_nh2}</td><td style='padding:5px 12px;color:#666;font-size:11px;border-bottom:1px solid #1e1e1e;white-space:nowrap;'>{_n2.get('source','')} Â· {_ns2}</td></tr>"
    if not _news_rows:
        _news_rows = "<tr><td colspan='2' style='padding:8px 12px;color:#555;font-size:11px;'>No news data â add FINNHUB_API_KEY to Streamlit secrets</td></tr>"
    _miro_w = int(ind['miro_score']/10*100)
    _pdf = f"""<!DOCTYPE html><html><head><meta charset='UTF-8'><title>NiftySniper â {symbol}</title>
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
<button class='btn no-print' onclick='window.print()'>â¬ SAVE AS PDF (Ctrl+P)</button>
<div class='hdr'>
  <div><div class='logo'>â¡ NIFTY SNIPER</div><div class='logo-sub'>SINGLE-STOCK INTELLIGENCE REPORT</div></div>
  <div><div class='sym'>{symbol}</div><div class='co'>{_co}</div><div class='px'>â¹{cp:,.2f} <span style='color:{_cc};font-size:13px;'>{'+' if chg>=0 else ''}{chg:.2f}%</span></div><div class='logo-sub' style='text-align:right;margin-top:3px;'>NSE Â· {_dt}</div></div>
</div>
<div class='vbox'>
  <div><div class='vlbl'>AI Technical Verdict</div><div class='vsub'>{bull_signals}/8 signals Â· Miro Score {ind['miro_score']}/10</div></div>
  <div class='vval'>{verdict}</div>
</div>
<div class='grid'>
<div class='sec'><div class='stitle'>ð Technical Indicators</div><table>
<tr><td style='padding:6px 12px;color:#888;font-size:11px;border-bottom:1px solid #1e1e1e;'>Miro Score</td><td style='padding:6px 12px;border-bottom:1px solid #1e1e1e;'><span class='mono {"green" if ind["miro_score"]>=6.5 else "red" if ind["miro_score"]<4 else "amber"}'>{ind['miro_score']}/10</span><div class='mbar'><div class='mfill'></div></div></td></tr>
<tr><td style='padding:6px 12px;color:#888;font-size:11px;border-bottom:1px solid #1e1e1e;'>Trend</td><td style='padding:6px 12px;border-bottom:1px solid #1e1e1e;'><span class='mono {"green" if "Up" in ind["trend"] else "red" if "Down" in ind["trend"] else "amber"}'>{ind['trend']}</span> <span style='color:#555;font-size:10px;'>ADX {ind['adx']}</span></td></tr>
<tr><td style='padding:6px 12px;color:#888;font-size:11px;border-bottom:1px solid #1e1e1e;'>Weekly Trend</td><td style='padding:6px 12px;border-bottom:1px solid #1e1e1e;'><span class='mono {"green" if ind.get("weekly_chg",0)>0.5 else "red" if ind.get("weekly_chg",0)<-0.5 else "amber"}'>{ind.get("weekly_trend","â")} ({ind.get("weekly_chg",0):+.2f}%)</span></td></tr>
<tr><td style='padding:6px 12px;color:#888;font-size:11px;border-bottom:1px solid #1e1e1e;'>RSI (14)</td><td style='padding:6px 12px;border-bottom:1px solid #1e1e1e;'><span class='mono {"green" if ind["rsi"]<40 else "red" if ind["rsi"]>65 else "amber"}'>{ind['rsi']}</span></td></tr>
<tr><td style='padding:6px 12px;color:#888;font-size:11px;border-bottom:1px solid #1e1e1e;'>Z-Score</td><td style='padding:6px 12px;border-bottom:1px solid #1e1e1e;'><span class='mono {"green" if ind["z_score"]<-0.5 else "red" if ind["z_score"]>1.5 else "amber"}'>{ind['z_score']}</span></td></tr>
<tr><td style='padding:6px 12px;color:#888;font-size:11px;border-bottom:1px solid #1e1e1e;'>IBS</td><td style='padding:6px 12px;border-bottom:1px solid #1e1e1e;'><span class='mono'>{ind['ibs']}</span></td></tr>
<tr><td style='padding:6px 12px;color:#888;font-size:11px;border-bottom:1px solid #1e1e1e;'>MACD</td><td style='padding:6px 12px;border-bottom:1px solid #1e1e1e;'><span class='mono {"green" if ind["macd"]>0 else "red"}'>{ind['macd']:+.2f}</span></td></tr>
<tr><td style='padding:6px 12px;color:#888;font-size:11px;'>Volume Ratio</td><td style='padding:6px 12px;'><span class='mono {"green" if ind["vol_ratio"]>1.5 else "white"}'>{ind['vol_ratio']}x avg</span></td></tr>
</table></div>
<div class='sec'><div class='stitle'>ð Moving Averages & Key Levels</div><table>
<tr><td style='padding:6px 12px;color:#888;font-size:11px;border-bottom:1px solid #1e1e1e;'>MA 20</td><td style='padding:6px 12px;border-bottom:1px solid #1e1e1e;'><span class='mono white'>â¹{ind['ma20']:,}</span> <span style='color:{"#00c851" if cp>ind["ma20"] else "#ff4444"};font-size:10px;'>{"â²" if cp>ind["ma20"] else "â¼"}</span></td></tr>
<tr><td style='padding:6px 12px;color:#888;font-size:11px;border-bottom:1px solid #1e1e1e;'>MA 50</td><td style='padding:6px 12px;border-bottom:1px solid #1e1e1e;'><span class='mono white'>â¹{ind['ma50_display']:,}</span> <span style='color:{"#00c851" if cp>ind["ma50_display"] else "#ff4444"};font-size:10px;'>{"â²" if cp>ind["ma50_display"] else "â¼"}</span></td></tr>
<tr><td style='padding:6px 12px;color:#888;font-size:11px;border-bottom:1px solid #1e1e1e;'>MA 200</td><td style='padding:6px 12px;border-bottom:1px solid #1e1e1e;'><span class='mono white'>â¹{ind['ma200']:,}</span> <span style='color:{"#00c851" if cp>ind["ma200"] else "#ff4444"};font-size:10px;'>{"â²" if cp>ind["ma200"] else "â¼"}</span></td></tr>
<tr><td style='padding:6px 12px;color:#888;font-size:11px;border-bottom:1px solid #1e1e1e;'>Donchian</td><td style='padding:6px 12px;border-bottom:1px solid #1e1e1e;'><span class='mono white'>â¹{ind['don_low']:,} â â¹{ind['don_high']:,}</span></td></tr>
<tr><td style='padding:6px 12px;color:#888;font-size:11px;border-bottom:1px solid #1e1e1e;'>Bollinger Bands</td><td style='padding:6px 12px;border-bottom:1px solid #1e1e1e;'><span class='mono white'>â¹{ind['bb_dn']:,} â â¹{ind['bb_up']:,}</span></td></tr>
<tr><td style='padding:6px 12px;color:#888;font-size:11px;border-bottom:1px solid #1e1e1e;'>ATR (14)</td><td style='padding:6px 12px;border-bottom:1px solid #1e1e1e;'><span class='mono white'>â¹{ind['atr']}</span></td></tr>
<tr><td style='padding:6px 12px;color:#888;font-size:11px;border-bottom:1px solid #1e1e1e;'>52-Week Range</td><td style='padding:6px 12px;border-bottom:1px solid #1e1e1e;'><span class='mono white'>â¹{ind['wk52_low']:,} â â¹{ind['wk52_high']:,}</span></td></tr>
<tr><td style='padding:6px 12px;color:#888;font-size:11px;'>52W Position</td><td style='padding:6px 12px;'><span class='mono white'>{ind['wk52_pct']}% of range</span></td></tr>
</table></div>
</div>
<div class='grid'>
<div class='sec'><div class='stitle'>ð¯ Signal Checklist</div><table>{_sl_rows}</table></div>
<div class='sec'><div class='stitle'>ð° Recent News & Filings</div><table>{_news_rows}</table></div>
</div>
<div class='disc'>â ï¸ <strong>Nifty Sniper â For educational purposes only. Not registered with SEBI. Not financial advice. Always do your own research.</strong></div>
</body></html>"""
    _col1, _col2, _col3 = st.columns([1,2,1])
    with _col2:
        st.download_button(
            label="â¬ï¸  DOWNLOAD REPORT (PDF)",
            data=_pdf,
            file_name=f"NiftySniper_{symbol}_{datetime.now().strftime('%Y%m%d')}.html",
            mime="text/html",
            use_container_width=True,
        )
    st.caption("Opens in browser â click **â¬ SAVE AS PDF** inside â Print â Save as PDF")
