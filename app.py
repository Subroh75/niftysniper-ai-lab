import streamlit as st
import pandas as pd
import numpy as np
import requests
import json
from datetime import datetime, timedelta
from anthropic import Anthropic

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="NiftySniper AI Lab",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Styling ───────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
* { font-family: 'Inter', sans-serif; }
.main { background: #0a0a0f; }
.stApp { background: #0a0a0f; }

.hero {
    background: linear-gradient(135deg, #0a0a0f 0%, #0d1117 50%, #0a0a0f 100%);
    border: 1px solid #1a1a2e;
    border-radius: 16px;
    padding: 32px;
    margin-bottom: 24px;
    text-align: center;
}
.hero h1 {
    font-size: 2.4rem;
    font-weight: 700;
    background: linear-gradient(135deg, #00d4aa, #7c3aed);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin: 0 0 8px 0;
}
.hero p { color: #6b7280; font-size: 1rem; margin: 0; }

.metric-card {
    background: #0d1117;
    border: 1px solid #1a1a2e;
    border-radius: 12px;
    padding: 16px;
    text-align: center;
    transition: border-color 0.2s;
}
.metric-card:hover { border-color: #00d4aa44; }
.metric-label { color: #6b7280; font-size: 0.75rem; font-weight: 500; letter-spacing: 0.05em; text-transform: uppercase; margin-bottom: 6px; }
.metric-value { font-size: 1.6rem; font-weight: 700; color: #f9fafb; }
.metric-sub { color: #6b7280; font-size: 0.8rem; margin-top: 4px; }

.signal-bull { color: #00d4aa !important; }
.signal-bear { color: #f87171 !important; }
.signal-neutral { color: #fbbf24 !important; }

.section-card {
    background: #0d1117;
    border: 1px solid #1a1a2e;
    border-radius: 12px;
    padding: 20px;
    margin-bottom: 16px;
}
.section-title {
    color: #f9fafb;
    font-size: 0.85rem;
    font-weight: 600;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    margin-bottom: 14px;
    padding-bottom: 10px;
    border-bottom: 1px solid #1a1a2e;
}

.agent-msg {
    background: #111827;
    border-left: 3px solid #7c3aed;
    border-radius: 0 8px 8px 0;
    padding: 12px 16px;
    margin-bottom: 10px;
    color: #d1d5db;
    font-size: 0.875rem;
    line-height: 1.6;
}
.agent-name {
    font-size: 0.75rem;
    font-weight: 600;
    letter-spacing: 0.05em;
    text-transform: uppercase;
    margin-bottom: 6px;
}
.agent-bull .agent-msg { border-left-color: #00d4aa; }
.agent-bear .agent-msg { border-left-color: #f87171; }
.agent-trader .agent-msg { border-left-color: #fbbf24; }
.agent-risk .agent-msg { border-left-color: #60a5fa; }
.agent-fund .agent-msg { border-left-color: #a78bfa; }

.news-item {
    background: #111827;
    border: 1px solid #1a1a2e;
    border-radius: 8px;
    padding: 12px;
    margin-bottom: 8px;
}
.news-headline { color: #e5e7eb; font-size: 0.875rem; font-weight: 500; }
.news-meta { color: #4b5563; font-size: 0.75rem; margin-top: 4px; }

.score-bar-bg { background: #1a1a2e; border-radius: 4px; height: 6px; margin-top: 8px; }
.score-bar-fill { border-radius: 4px; height: 6px; }

.verdict-box {
    background: linear-gradient(135deg, #0d1117, #111827);
    border: 1px solid #00d4aa33;
    border-radius: 12px;
    padding: 20px;
    text-align: center;
    margin-top: 8px;
}
.verdict-label { color: #6b7280; font-size: 0.75rem; font-weight: 600; letter-spacing: 0.08em; text-transform: uppercase; margin-bottom: 8px; }
.verdict-text { font-size: 1.8rem; font-weight: 700; }

[data-testid="stTextInput"] input {
    background: #111827 !important;
    border: 1px solid #374151 !important;
    border-radius: 10px !important;
    color: #f9fafb !important;
    font-size: 1.1rem !important;
    padding: 12px 16px !important;
}
[data-testid="stTextInput"] input:focus {
    border-color: #00d4aa !important;
    box-shadow: 0 0 0 2px #00d4aa22 !important;
}
.stButton button {
    background: linear-gradient(135deg, #00d4aa, #059669) !important;
    color: #000 !important;
    font-weight: 700 !important;
    border: none !important;
    border-radius: 10px !important;
    padding: 12px 24px !important;
    font-size: 1rem !important;
    width: 100% !important;
}
.stButton button:hover { opacity: 0.9 !important; }
div[data-testid="stHorizontalBlock"] { gap: 12px; }
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
        url = f"https://finnhub.io/api/v1/company-news?symbol={symbol}.NS&from={from_dt}&to={to_dt}&token={finnhub_key}"
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
        url = f"https://finnhub.io/api/v1/stock/recommendation?symbol={symbol}.NS&token={finnhub_key}"
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
    ("📈 Bull Analyst",    "bull",    "#00d4aa", "You are an optimistic equity analyst. Find compelling bullish reasons to buy this stock based on the data. Be specific about price targets and catalysts. 3-4 sentences."),
    ("📉 Bear Analyst",    "bear",    "#f87171", "You are a cautious short-seller. Identify the key risks, red flags and reasons to avoid this stock right now. Be specific. 3-4 sentences."),
    ("⚡ Swing Trader",    "trader",  "#fbbf24", "You are an experienced NSE swing trader. Give a concrete trading plan: entry zone, stop loss, target, and timeframe. Be very specific with numbers. 3-4 sentences."),
    ("🛡️ Risk Manager",   "risk",    "#60a5fa", "You are a portfolio risk manager. Assess the risk/reward, suggest position sizing as % of portfolio, and key levels to watch. 3-4 sentences."),
    ("🏛️ Fundamentalist", "fund",    "#a78bfa", "You are a fundamental analyst. Comment on valuation context, sector dynamics, and whether the technical picture aligns with fundamentals. 3-4 sentences."),
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

def score_bar(val, max_val=10, color="#00d4aa"):
    pct = int(val / max_val * 100)
    return f"""
<div class="score-bar-bg">
  <div class="score-bar-fill" style="width:{pct}%; background:{color};"></div>
</div>"""

# ── Main UI ───────────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero">
  <h1>🎯 NiftySniper AI Lab</h1>
  <p>Single-stock deep analysis powered by AI agents · NSE India</p>
</div>
""", unsafe_allow_html=True)

# Search bar
col_inp, col_btn = st.columns([5, 1])
with col_inp:
    symbol = st.text_input(
        "", placeholder="Enter NSE symbol (e.g. RELIANCE, TCS, INFY, HDFCBANK)...",
        label_visibility="collapsed",
        key="symbol_input",
    ).upper().strip()
with col_btn:
    analyse = st.button("🔍 Analyse", key="analyse_btn")

# Popular picks
st.markdown(
    "<div style='text-align:center; color:#4b5563; font-size:0.8rem; margin: -8px 0 16px'>Quick picks: "
    + " · ".join([f"<span style='color:#6b7280; cursor:pointer'>{s}</span>"
                  for s in ["RELIANCE","TCS","HDFCBANK","INFY","SBIN","TITAN","BAJFINANCE","NIFTY50"]])
    + "</div>", unsafe_allow_html=True
)

# ── Analysis ──────────────────────────────────────────────────────────────────
if analyse and symbol:
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
    chg_col = "#00d4aa" if chg >= 0 else "#f87171"
    chg_sym = "▲" if chg >= 0 else "▼"

    # ── Stock Header ──────────────────────────────────────────────────────────
    st.markdown(f"""
<div class="section-card" style="margin-bottom:20px;">
  <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:12px;">
    <div>
      <div style="color:#f9fafb; font-size:1.6rem; font-weight:700;">{symbol}</div>
      <div style="color:#6b7280; font-size:0.875rem;">{quote.get('name', symbol)} · NSE</div>
    </div>
    <div style="text-align:right;">
      <div style="color:#f9fafb; font-size:2rem; font-weight:700;">₹{cp:,.2f}</div>
      <div style="color:{chg_col}; font-size:1rem; font-weight:600;">{chg_sym} {abs(chg):.2f}%</div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

    # ── Key Metrics Row ───────────────────────────────────────────────────────
    miro  = ind["miro_score"]
    miro_c = "signal-bull" if miro >= 6.5 else "signal-bear" if miro < 4 else "signal-neutral"
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
    c6.markdown(render_metric("MA 20", f"₹{ind['ma20']:,}", "Above" if cp > ind['ma20'] else "Below"), unsafe_allow_html=True)
    c7.markdown(render_metric("MA 200", f"₹{ind['ma200']:,}", "Above" if cp > ind['ma200'] else "Below"), unsafe_allow_html=True)
    c8.markdown(render_metric("ATR (14)", f"₹{ind['atr']}", "Daily range est."), unsafe_allow_html=True)
    c9.markdown(render_metric("Volume", f"{ind['vol_ratio']}x", "vs 20D avg"), unsafe_allow_html=True)
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
                s_col = "#00d4aa" if sentiment == "positive" else "#f87171" if sentiment == "negative" else "#6b7280"
                st.markdown(f"""
<div class="news-item">
  <div class="news-headline">{n.get('headline','')}</div>
  <div class="news-meta">{n.get('source','')} · {ts} <span style="color:{s_col}">●</span></div>
</div>""", unsafe_allow_html=True)
        else:
            st.markdown('<div style="color:#4b5563; font-size:0.875rem; padding:8px 0;">Add FINNHUB_API_KEY to secrets for live news & filings.</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        # Price chart
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">📊 Price Chart (200D)</div>', unsafe_allow_html=True)
        chart_df = df[["date","Close","Open"]].tail(200).set_index("date")
        st.line_chart(chart_df, color=["#00d4aa","#374151"], height=200)
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
            col_s = "#00d4aa" if bull else "#f87171" if "❌" in val else "#fbbf24"
            st.markdown(f"""
<div style="display:flex; justify-content:space-between; padding:7px 0; border-bottom:1px solid #1a1a2e;">
  <span style="color:#9ca3af; font-size:0.8rem;">{label}</span>
  <span style="color:{col_s}; font-size:0.8rem; font-weight:600;">{val}</span>
</div>""", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        # Analyst recs
        if rec:
            st.markdown('<div class="section-card">', unsafe_allow_html=True)
            st.markdown('<div class="section-title">🏦 Analyst Consensus</div>', unsafe_allow_html=True)
            total = (rec.get("buy",0) + rec.get("hold",0) + rec.get("sell",0) + rec.get("strongBuy",0) + rec.get("strongSell",0)) or 1
            for label, key, col in [("Strong Buy","strongBuy","#00d4aa"),("Buy","buy","#34d399"),("Hold","hold","#fbbf24"),("Sell","sell","#f87171"),("Strong Sell","strongSell","#dc2626")]:
                n_rec = rec.get(key, 0)
                pct   = int(n_rec / total * 100)
                st.markdown(f"""
<div style="display:flex; align-items:center; gap:8px; margin-bottom:6px;">
  <span style="color:#9ca3af; font-size:0.75rem; width:70px;">{label}</span>
  <div style="flex:1; background:#1a1a2e; border-radius:3px; height:6px;">
    <div style="width:{pct}%; background:{col}; border-radius:3px; height:6px;"></div>
  </div>
  <span style="color:{col}; font-size:0.75rem; width:20px;">{n_rec}</span>
</div>""", unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

        # Verdict
        bull_signals = bull_count
        verdict = "STRONG BUY" if bull_signals >= 6 else "BUY" if bull_signals >= 5 else "HOLD" if bull_signals >= 3 else "AVOID"
        v_col   = "#00d4aa" if "BUY" in verdict else "#f87171" if verdict == "AVOID" else "#fbbf24"
        st.markdown(f"""
<div class="verdict-box">
  <div class="verdict-label">AI Technical Verdict</div>
  <div class="verdict-text" style="color:{v_col};">{verdict}</div>
  <div style="color:#4b5563; font-size:0.75rem; margin-top:6px;">{bull_signals}/7 bullish signals</div>
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
<div style="text-align:center; color:#374151; font-size:0.75rem; margin-top:24px; padding:12px; border-top:1px solid #1a1a2e;">
⚠️ Not SEBI registered. Not financial advice. For educational purposes only. Always do your own research.
</div>""", unsafe_allow_html=True)

elif not symbol and not analyse:
    # Landing state
    st.markdown("""
<div style="text-align:center; padding:60px 20px; color:#374151;">
  <div style="font-size:3rem; margin-bottom:16px;">🎯</div>
  <div style="color:#6b7280; font-size:1rem; margin-bottom:32px;">Type any NSE symbol above and click Analyse</div>
  <div style="display:flex; justify-content:center; gap:24px; flex-wrap:wrap; font-size:0.8rem;">
    <div style="color:#4b5563;">✅ Live NSE data via Yahoo Finance</div>
    <div style="color:#4b5563;">✅ 7 technical indicators</div>
    <div style="color:#4b5563;">✅ 5 AI trading agents</div>
    <div style="color:#4b5563;">✅ News & analyst data</div>
  </div>
</div>
""", unsafe_allow_html=True)
