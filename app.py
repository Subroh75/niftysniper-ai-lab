import streamlit as st
import pandas as pd
import numpy as np
import requests
import json
from datetime import datetime, timedelta
from anthropic import Anthropic

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
    page_title="NiftySniper AI Lab",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Styling ───────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;600&display=swap');
* { font-family: 'Inter', sans-serif; }
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
    margin-bottom: 10px; color: #cccccc; font-size: 0.875rem; line-height: 1.7;
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
            "name":     meta.get("longName", symbol),
            "currency": meta.get("currency", "INR"),
            "exchange": meta.get("exchangeName", "NSE"),
        }
    except Exception:
        return {}

@st.cache_data(ttl=600, show_spinner=False)
def fetch_news(symbol: str, finnhub_key: str) -> list:
    """Fetch company news from Finnhub."""
    if not finnhub_key:
        return []
    try:
        to_dt   = datetime.now().strftime("%Y-%m-%d")
        from_dt = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        # Finnhub uses exchange-qualified symbol: NSE:RELIANCE format
        fh_sym = f"NSE:{symbol}"
        url = f"https://finnhub.io/api/v1/company-news?symbol={fh_sym}&from={from_dt}&to={to_dt}&token={finnhub_key}"
        r   = requests.get(url, timeout=8)
        news = r.json()
        return news[:6] if isinstance(news, list) else []
    except Exception:
        return []

@st.cache_data(ttl=600, show_spinner=False)
def fetch_recommendation(symbol: str, finnhub_key: str) -> dict:
    """Fetch analyst recommendations from Finnhub."""
    if not finnhub_key:
        return {}
    try:
        fh_sym2 = f"NSE:{symbol}"
        url = f"https://finnhub.io/api/v1/stock/recommendation?symbol={fh_sym2}&token={finnhub_key}"
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
    news_txt = "\n".join([f"- {n.get('headline','')}" for n in news[:4]]) or "No recent news"
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
    ("📈 Bull Analyst",    "bull",    "#00c851", "You are an optimistic equity analyst. Find compelling bullish reasons to buy this stock based on the data. Be specific about price targets and catalysts. 3-4 sentences."),
    ("📉 Bear Analyst",    "bear",    "#ff4444", "You are a cautious short-seller. Identify the key risks, red flags and reasons to avoid this stock right now. Be specific. 3-4 sentences."),
    ("⚡ Swing Trader",    "trader",  "#ffaa00", "You are an experienced NSE swing trader. Give a concrete trading plan: entry zone, stop loss, target, and timeframe. Be very specific with numbers. 3-4 sentences."),
    ("🛡️ Risk Manager",   "risk",    "#3399ff", "You are a portfolio risk manager. Assess the risk/reward, suggest position sizing as % of portfolio, and key levels to watch. 3-4 sentences."),
    ("🏛️ Fundamentalist", "fund",    "#aa88ff", "You are a fundamental analyst. Comment on valuation context, sector dynamics, and whether the technical picture aligns with fundamentals. 3-4 sentences."),
]

def stream_agent(client, agent_name, persona, context, placeholder):
    msgs = [{"role": "user", "content": f"{context}\n\nYour role: {persona}\nAnalyse this stock now."}]
    full = ""
    try:
        with client.messages.stream(
            model="claude-sonnet-4-6",
            max_tokens=300,
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
  <h1>⚡ NIFTYSNIPER AI LAB</h1>
  <p>Single-stock intelligence terminal · NSE India · Powered by AI agents</p>
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
    company_name = quote.get('name', symbol) or symbol
    st.markdown(f"""
<div class="section-card" style="margin-bottom:20px; border-top:2px solid #ff6600;">
  <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:12px;">
    <div>
      <div style="color:#ff6600; font-size:0.7rem; font-weight:600; letter-spacing:0.14em; text-transform:uppercase; font-family:'JetBrains Mono',monospace; margin-bottom:2px;">NSE · EQUITY</div>
      <div style="color:#ffffff; font-size:1.8rem; font-weight:700; font-family:'JetBrains Mono',monospace; letter-spacing:0.05em; line-height:1.1;">{symbol}</div>
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
        # News
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">📰 Recent News & Filings</div>', unsafe_allow_html=True)
        if news:
            for n in news[:5]:
                ts = datetime.fromtimestamp(n.get("datetime", 0)).strftime("%d %b") if n.get("datetime") else ""
                sentiment = n.get("sentiment", "")
                s_col = "#ff6600" if sentiment == "positive" else "#cc3300" if sentiment == "negative" else "#555555"
                st.markdown(f"""
<div class="news-item">
  <div class="news-headline">{n.get('headline','')}</div>
  <div class="news-meta">{n.get('source','')} · {ts} <span style="color:{s_col}">●</span></div>
</div>""", unsafe_allow_html=True)
        else:
            st.markdown('<div style="color:#555555; font-size:0.875rem; padding:8px 0;">Add FINNHUB_API_KEY to secrets for live news & filings.</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        # Price chart
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">📊 Price Chart — Last 90 Days</div>', unsafe_allow_html=True)
        chart_data = df.tail(90)
        # Candlestick via HTML5 canvas — zero dependency
        candle_df = chart_data.reset_index(drop=True)
        import json as _json
        _candles = []
        for _, _r in candle_df.iterrows():
            _candles.append({"d":str(_r["date"])[:10],"o":round(float(_r["Open"]),2),
                             "h":round(float(_r["High"]),2),"l":round(float(_r["Low"]),2),
                             "c":round(float(_r["Close"]),2)})
        _cj = _json.dumps(_candles)
        st.components.v1.html(f"""<canvas id='cv' width='900' height='260'
          style='width:100%;background:#0d0d0d;border-radius:6px;display:block'></canvas>
<script>(function(){{
  const D={_cj},cv=document.getElementById('cv'),ctx=cv.getContext('2d');
  const W=cv.width,H=cv.height,pl=55,pr=10,pt=15,pb=28,cW=W-pl-pr,cH=H-pt-pb,n=D.length;
  const hi=Math.max(...D.map(d=>d.h)),lo=Math.min(...D.map(d=>d.l)),rng=hi-lo||1;
  const Y=p=>pt+cH-((p-lo)/rng*cH),bw=Math.max(2,cW/n*0.55);
  ctx.fillStyle='#0d0d0d';ctx.fillRect(0,0,W,H);
  // Grid
  for(let i=0;i<=4;i++){{const y=pt+cH*i/4;ctx.strokeStyle='#1a1a1a';ctx.lineWidth=1;
    ctx.beginPath();ctx.moveTo(pl,y);ctx.lineTo(W-pr,y);ctx.stroke();
    ctx.fillStyle='#555';ctx.font='10px monospace';ctx.textAlign='right';
    ctx.fillText('₹'+(hi-rng*i/4).toFixed(0),pl-3,y+3);}}
  // MA20
  ctx.strokeStyle='#ffaa00';ctx.lineWidth=1.5;ctx.setLineDash([3,3]);ctx.beginPath();
  D.forEach((d,i)=>{{const s=Math.max(0,i-19),ma=D.slice(s,i+1).reduce((a,x)=>a+x.c,0)/(i-s+1);
    const x=pl+(i+0.5)*cW/n;i===0?ctx.moveTo(x,Y(ma)):ctx.lineTo(x,Y(ma));}});
  ctx.stroke();ctx.setLineDash([]);
  // Candles
  D.forEach((d,i)=>{{const x=pl+(i+0.5)*cW/n,up=d.c>=d.o,col=up?'#00c851':'#ff4444';
    ctx.strokeStyle=col;ctx.lineWidth=1;
    ctx.beginPath();ctx.moveTo(x,Y(d.h));ctx.lineTo(x,Y(d.l));ctx.stroke();
    const y1=Y(Math.max(d.o,d.c)),bh=Math.max(1,Y(Math.min(d.o,d.c))-y1);
    ctx.fillStyle=up?col:col+'99';ctx.fillRect(x-bw/2,y1,bw,bh);
    if(!up){{ctx.strokeRect(x-bw/2,y1,bw,bh);}}}});
  // X labels
  ctx.fillStyle='#555';ctx.font='9px monospace';ctx.textAlign='center';
  D.forEach((d,i)=>{{if(i%15===0)ctx.fillText(d.d.slice(5),pl+(i+0.5)*cW/n,H-6);}});
}})();</script>""", height=270)
        st.markdown('</div>', unsafe_allow_html=True)

    with right:
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
<div style="display:flex; justify-content:space-between; padding:7px 0; border-bottom:1px solid #1a1a1a;">
  <span style="color:#9ca3af; font-size:0.8rem;">{label}</span>
  <span style="color:{col_s}; font-size:0.8rem; font-weight:600;">{val}</span>
</div>""", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

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
⚠️ Not SEBI registered. Not financial advice. For educational purposes only. Always do your own research.
</div>""", unsafe_allow_html=True)


    # ── Download Report ─────────────────────────────────────
    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
    _report = "\n".join([
        "NIFTYSNIPER AI LAB - ANALYSIS REPORT",
        "="*50,
        f"Stock: {symbol} | Price: Rs.{cp:,.2f} ({chg:+.2f}%)",
        f"Miro Score: {ind['miro_score']}/10 | Trend: {ind['trend']}",
        f"Weekly: {ind.get('weekly_trend','n/a')} ({ind.get('weekly_chg',0):+.2f}%)",
        f"RSI: {ind['rsi']} | Z-Score: {ind['z_score']} | IBS: {ind['ibs']}",
        f"MA20: Rs.{ind['ma20']:,} | MA50: Rs.{ind['ma50_display']:,} | MA200: Rs.{ind['ma200']:,}",
        f"Verdict: {verdict} ({bull_signals}/7 signals)",
        "="*50,
        "Not SEBI registered. Not financial advice.",
    ])
    _col1, _col2, _col3 = st.columns([1,2,1])
    with _col2:
        st.download_button(
            label="⬇️  DOWNLOAD REPORT",
            data=_report,
            file_name=f"NiftySniper_{symbol}_{datetime.now().strftime('%Y%m%d')}.txt",
            mime="text/plain",
            use_container_width=True,
        )

elif not symbol and not analyse:
    # Landing state
    st.markdown("""
<div style="text-align:center; padding:60px 20px; color:#333333;">
  <div style="font-size:3rem; margin-bottom:16px;">🎯</div>
  <div style="color:#555555; font-size:1rem; margin-bottom:32px;">Type any NSE symbol above and click Analyse</div>
  <div style="display:flex; justify-content:center; gap:24px; flex-wrap:wrap; font-size:0.8rem;">
    <div style="color:#555555;">✅ Live NSE data via Yahoo Finance</div>
    <div style="color:#555555;">✅ 7 technical indicators</div>
    <div style="color:#555555;">✅ 5 AI trading agents</div>
    <div style="color:#555555;">✅ News & analyst data</div>
  </div>
</div>
""", unsafe_allow_html=True)
