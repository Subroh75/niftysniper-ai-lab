"""
NiftySniper AI Lab — NSE Signal Intelligence
Design: CryptoSniper language, orange #ff6600 on black #060a04
Sections: Signal Output → Components → Market Structure → Timing Quality
          → Fundamentals → Kronos AI → AI Agent Council → Export
"""

import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import anthropic
import time
import io
import math
from datetime import datetime, timezone, timedelta
from fpdf import FPDF

# ── Try importing Kronos ────────────────────────────────────────────────────
try:
    from kronos_streamlit import render_kronos_forecast
    KRONOS_AVAILABLE = True
except Exception:
    KRONOS_AVAILABLE = False

# ── Page config ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="NiftySniper AI Lab",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Design system ────────────────────────────────────────────────────────────
BG        = "#060a04"
CARD      = "#0d1a0d"
ACCENT    = "#ff6600"
ACCENT2   = "#ffaa00"
GREEN     = "#00c851"
RED       = "#ff4444"
TEXT      = "#e8e8e8"
MUTED     = "#888888"
BORDER    = "#1a2e1a"

CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600&family=Inter:wght@400;500;600;700&display=swap');

html, body, [data-testid="stApp"] {{
    background-color: {BG};
    color: {TEXT};
    font-family: 'Inter', sans-serif;
}}
[data-testid="stAppViewContainer"] {{ background-color: {BG}; }}
[data-testid="stHeader"] {{ background-color: {BG}; }}
[data-testid="stSidebar"] {{ background-color: {CARD}; }}
section[data-testid="stMain"] > div {{ padding-top: 0rem; }}

/* Hide default streamlit decorations */
#MainMenu, footer, header {{ visibility: hidden; }}
.block-container {{ padding: 1rem 2rem 2rem 2rem; max-width: 1400px; }}

/* Hero bar */
.ns-hero {{
    display: flex; align-items: center; justify-content: space-between;
    padding: 1rem 0 0.75rem 0;
    border-bottom: 1px solid {BORDER};
    margin-bottom: 1.25rem;
}}
.ns-logo-wrap {{ display: flex; align-items: center; gap: 12px; }}
.ns-logo-icon {{
    width: 38px; height: 38px; border-radius: 8px;
    background: {ACCENT}; display: flex; align-items: center;
    justify-content: center; font-size: 20px; font-weight: 700;
    color: #000; font-family: 'JetBrains Mono', monospace;
}}
.ns-logo-text {{ font-size: 22px; font-weight: 700; color: {TEXT}; letter-spacing: -0.5px; }}
.ns-logo-sub  {{ font-size: 11px; color: {MUTED}; letter-spacing: 0.12em; text-transform: uppercase; }}

/* Signal badge */
.ns-signal-badge {{
    text-align: center; padding: 1.5rem 1rem; margin-bottom: 1rem;
    background: {CARD}; border: 1px solid {BORDER}; border-radius: 12px;
}}
.ns-signal-label {{ font-size: 11px; letter-spacing: 0.15em; color: {MUTED}; text-transform: uppercase; margin-bottom: 6px; }}
.ns-signal-value {{ font-size: 40px; font-weight: 700; font-family: 'JetBrains Mono', monospace; margin-bottom: 4px; }}
.ns-signal-score {{ font-size: 18px; color: {MUTED}; font-family: 'JetBrains Mono', monospace; }}
.ns-signal-time  {{ font-size: 12px; color: {MUTED}; margin-top: 8px; }}

.sig-strong {{ color: {ACCENT};  }}
.sig-building{{ color: {ACCENT2}; }}
.sig-low     {{ color: {MUTED};  }}
.sig-none    {{ color: {RED};    }}

/* Section cards */
.ns-section {{
    background: {CARD};
    border: 1px solid {BORDER};
    border-left: 3px solid {ACCENT};
    border-radius: 8px;
    padding: 1rem 1.25rem;
    margin-bottom: 1rem;
}}
.ns-section-title {{
    font-size: 11px; font-weight: 600; letter-spacing: 0.15em;
    text-transform: uppercase; color: {ACCENT}; margin-bottom: 0.75rem;
}}

/* KV rows */
.ns-kv-row {{
    display: flex; justify-content: space-between; align-items: center;
    padding: 5px 0; border-bottom: 1px solid {BORDER};
    font-size: 13px;
}}
.ns-kv-row:last-child {{ border-bottom: none; }}
.ns-kv-label {{ color: {MUTED}; }}
.ns-kv-value {{ font-family: 'JetBrains Mono', monospace; font-weight: 600; }}
.kv-up   {{ color: {GREEN}; }}
.kv-down {{ color: {RED};   }}
.kv-neut {{ color: {TEXT};  }}

/* Score component row */
.ns-comp-row {{
    display: flex; align-items: center; padding: 6px 0;
    border-bottom: 1px solid {BORDER}; gap: 10px;
}}
.ns-comp-row:last-child {{ border-bottom: none; }}
.ns-comp-key   {{ font-size: 11px; color: {MUTED}; min-width: 130px; }}
.ns-comp-bar-wrap {{ flex: 1; background: #0a1a0a; border-radius: 4px; height: 6px; }}
.ns-comp-bar   {{ height: 6px; border-radius: 4px; background: {ACCENT}; }}
.ns-comp-score {{ font-family: 'JetBrains Mono', monospace; font-size: 13px; min-width: 45px; text-align: right; color: {TEXT}; }}
.ns-comp-raw   {{ font-size: 11px; color: {MUTED}; min-width: 100px; text-align: right; }}

/* Agent debate */
.ns-agent-block {{
    background: #060f06; border: 1px solid {BORDER};
    border-radius: 8px; padding: 1rem; margin-bottom: 0.75rem;
}}
.ns-agent-name {{
    font-size: 11px; font-weight: 600; letter-spacing: 0.12em;
    text-transform: uppercase; margin-bottom: 6px;
}}
.ns-agent-bull  {{ color: {GREEN};   }}
.ns-agent-bear  {{ color: {RED};     }}
.ns-agent-risk  {{ color: {ACCENT2}; }}
.ns-agent-cio   {{ color: {ACCENT};  }}
.ns-agent-text  {{ font-size: 13px; color: {TEXT}; line-height: 1.65; }}

/* Verdict pill */
.ns-verdict {{
    display: inline-block; padding: 4px 14px; border-radius: 20px;
    font-size: 12px; font-weight: 700; letter-spacing: 0.08em;
    text-transform: uppercase; margin-top: 8px;
}}
.v-buy  {{ background: #003d12; color: {GREEN}; border: 1px solid {GREEN}; }}
.v-sell {{ background: #3d0000; color: {RED};   border: 1px solid {RED};   }}
.v-hold {{ background: #3d2000; color: {ACCENT2}; border: 1px solid {ACCENT2}; }}
.v-wait {{ background: #1a1a1a; color: {MUTED}; border: 1px solid {MUTED}; }}

/* Streamlit overrides */
div[data-testid="stTextInput"] > div > div > input {{
    background-color: {CARD}; border: 1px solid {BORDER};
    color: {TEXT}; border-radius: 8px; font-family: 'JetBrains Mono', monospace;
}}
div.stButton > button {{
    background: {ACCENT}; color: #000; font-weight: 700;
    border: none; border-radius: 8px; padding: 0.5rem 1.5rem;
    font-size: 13px; letter-spacing: 0.05em; width: 100%;
}}
div.stButton > button:hover {{ background: #ff8533; color: #000; }}
div.stDownloadButton > button {{
    background: transparent; color: {ACCENT};
    border: 1px solid {ACCENT}; border-radius: 8px;
    font-weight: 600; width: 100%;
}}
div.stDownloadButton > button:hover {{ background: {ACCENT}; color: #000; }}
div[data-testid="stSelectbox"] > div {{ background: {CARD}; border-color: {BORDER}; }}
.stSpinner > div {{ border-top-color: {ACCENT} !important; }}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

# ── Symbol dictionary ────────────────────────────────────────────────────────
SYMBOLS = {
    # Index
    "NIFTY 50":     "^NSEI",    "BANKNIFTY":    "^NSEBANK",
    # Large Cap
    "RELIANCE":     "RELIANCE.NS",  "TCS":          "TCS.NS",
    "HDFCBANK":     "HDFCBANK.NS",  "INFY":         "INFY.NS",
    "ICICIBANK":    "ICICIBANK.NS", "SBIN":         "SBIN.NS",
    "WIPRO":        "WIPRO.NS",     "AXISBANK":     "AXISBANK.NS",
    "KOTAKBANK":    "KOTAKBANK.NS", "LT":           "LT.NS",
    "BAJFINANCE":   "BAJFINANCE.NS","TATAMOTORS":   "TATAMOTORS.NS",
    "MARUTI":       "MARUTI.NS",    "SUNPHARMA":    "SUNPHARMA.NS",
    "ONGC":         "ONGC.NS",      "NTPC":         "NTPC.NS",
    "POWERGRID":    "POWERGRID.NS", "BPCL":         "BPCL.NS",
    "BHARTIARTL":   "BHARTIARTL.NS","HINDUNILVR":   "HINDUNILVR.NS",
    "ASIANPAINT":   "ASIANPAINT.NS","NESTLEIND":    "NESTLEIND.NS",
    "TITAN":        "TITAN.NS",     "ULTRACEMCO":   "ULTRACEMCO.NS",
    "GRASIM":       "GRASIM.NS",    "ADANIENT":     "ADANIENT.NS",
    "ADANIPORTS":   "ADANIPORTS.NS","JSWSTEEL":     "JSWSTEEL.NS",
    "TATASTEEL":    "TATASTEEL.NS", "HINDALCO":     "HINDALCO.NS",
    # PSU / Defence
    "BEL":          "BEL.NS",       "HAL":          "HAL.NS",
    "BHEL":         "BHEL.NS",      "COALINDIA":    "COALINDIA.NS",
    "VEDL":         "VEDL.NS",
    # Pharma / Healthcare
    "DRREDDY":      "DRREDDY.NS",   "CIPLA":        "CIPLA.NS",
    "DIVISLAB":     "DIVISLAB.NS",  "APOLLOHOSP":   "APOLLOHOSP.NS",
    # Auto
    "EICHERMOT":    "EICHERMOT.NS", "BAJAJ-AUTO":   "BAJAJ-AUTO.NS",
    "HEROMOTOCO":   "HEROMOTOCO.NS","M&M":          "M&M.NS",
    # FMCG / Consumer
    "TATACONSUM":   "TATACONSUM.NS","ITC":          "ITC.NS",
    # IT
    "HCLTECH":      "HCLTECH.NS",   "TECHM":        "TECHM.NS",
    "LTIM":         "LTIM.NS",      "MPHASIS":      "MPHASIS.NS",
    # Finance
    "BAJAJFINSV":   "BAJAJFINSV.NS","HDFCLIFE":     "HDFCLIFE.NS",
    "SBILIFE":      "SBILIFE.NS",   "ICICIGI":      "ICICIGI.NS",
    # Cement / Materials
    "SHREECEM":     "SHREECEM.NS",  "ACC":          "ACC.NS",
    # Real estate / Others
    "DLF":          "DLF.NS",       "GODREJPROP":   "GODREJPROP.NS",
    "INDUSINDBK":   "INDUSINDBK.NS","FEDERALBNK":   "FEDERALBNK.NS",
    "PNB":          "PNB.NS",       "BANKBARODA":   "BANKBARODA.NS",
}

AGENTS = [
    {"key": "BULL",         "label": "Bull Agent",    "cls": "ns-agent-bull",
     "system": "You are the BULL AGENT for NiftySniper NSE intelligence. Make the strongest possible bullish case using trend alignment, momentum, fundamentals, and institutional support. Cite specific numbers from the data. Be direct and confident. 3-4 sentences maximum."},
    {"key": "BEAR",         "label": "Bear Agent",    "cls": "ns-agent-bear",
     "system": "You are the BEAR AGENT for NiftySniper NSE intelligence. Make the strongest possible bearish case: overbought signals, resistance levels, weak volume, macro risks. Cite specific numbers. Be direct and contrarian. 3-4 sentences maximum."},
    {"key": "RISK MANAGER", "label": "Risk Manager",  "cls": "ns-agent-risk",
     "system": "You are the RISK MANAGER for NiftySniper. Focus only on position sizing and risk management. Calculate a stop loss using 1.5x ATR below close. Suggest max position size as % of capital. Give a specific risk/reward ratio. 3-4 sentences. No directional view."},
    {"key": "CIO",          "label": "CIO — Verdict", "cls": "ns-agent-cio",
     "system": "You are the CIO of NiftySniper, providing the final synthesis. Weigh the bull and bear cases against the risk. State a clear verdict: BUY / SELL / HOLD / WAIT. Give a confidence score 1-10. Cite the signal score and one decisive data point. 3-4 sentences maximum."},
]

# ── IST timestamp ────────────────────────────────────────────────────────────
def ist_now():
    ist = timezone(timedelta(hours=5, minutes=30))
    return datetime.now(ist).strftime("%d %b %Y  %H:%M IST")

# ── Data fetcher ─────────────────────────────────────────────────────────────
@st.cache_data(ttl=300, show_spinner=False)
def fetch_data(ticker: str, period: str = "1y"):
    tk = yf.Ticker(ticker)
    df = tk.history(period=period, auto_adjust=True)
    if df.empty:
        return None, None
    df = df[["Open","High","Low","Close","Volume"]].dropna()

    # Indicators
    df["EMA20"]  = df["Close"].ewm(span=20,  adjust=False).mean()
    df["EMA50"]  = df["Close"].ewm(span=50,  adjust=False).mean()
    df["EMA200"] = df["Close"].ewm(span=200, adjust=False).mean()
    df["VWAP"]   = (df["Close"] * df["Volume"]).cumsum() / df["Volume"].cumsum()

    # Bollinger
    df["BB_mid"]   = df["Close"].rolling(20).mean()
    df["BB_std"]   = df["Close"].rolling(20).std()
    df["BB_upper"] = df["BB_mid"] + 2 * df["BB_std"]
    df["BB_lower"] = df["BB_mid"] - 2 * df["BB_std"]

    # RSI
    delta = df["Close"].diff()
    gain  = delta.clip(lower=0).rolling(14).mean()
    loss  = (-delta.clip(upper=0)).rolling(14).mean()
    rs    = gain / loss.replace(0, np.nan)
    df["RSI"] = 100 - (100 / (1 + rs))

    # ATR
    df["TR"]  = pd.concat([
        df["High"] - df["Low"],
        (df["High"] - df["Close"].shift()).abs(),
        (df["Low"]  - df["Close"].shift()).abs()
    ], axis=1).max(axis=1)
    df["ATR"] = df["TR"].rolling(14).mean()

    # ADX
    df["DM_up"]   = df["High"].diff().clip(lower=0)
    df["DM_down"] = (-df["Low"].diff()).clip(lower=0)
    df.loc[df["DM_up"] <= df["DM_down"],   "DM_up"]   = 0
    df.loc[df["DM_down"] <= df["DM_up"],   "DM_down"] = 0
    atr14 = df["TR"].rolling(14).sum()
    df["DI_pos"] = 100 * df["DM_up"].rolling(14).sum()   / atr14.replace(0, np.nan)
    df["DI_neg"] = 100 * df["DM_down"].rolling(14).sum() / atr14.replace(0, np.nan)
    dx = 100 * (df["DI_pos"] - df["DI_neg"]).abs() / (df["DI_pos"] + df["DI_neg"]).replace(0, np.nan)
    df["ADX"] = dx.rolling(14).mean()

    # Fundamentals via fast_info
    fund = {}
    try:
        fi = tk.fast_info
        fund["pe"]       = round(fi.get("trailingPe", 0) or 0,  1)
        fund["eps"]      = round(fi.get("trailingEps", 0) or 0, 2)
        fund["mkt_cap"]  = fi.get("marketCap", 0) or 0
        fund["52w_high"] = round(fi.get("fiftyTwoWeekHigh", 0) or 0, 2)
        fund["52w_low"]  = round(fi.get("fiftyTwoWeekLow", 0) or 0,  2)
        fund["avg_vol"]  = fi.get("threeMonthAverageVolume", 0) or 0
    except Exception:
        fund = {"pe": 0, "eps": 0, "mkt_cap": 0, "52w_high": 0, "52w_low": 0, "avg_vol": 0}

    return df, fund

# ── Miro Score ───────────────────────────────────────────────────────────────
def compute_score(df: pd.DataFrame) -> dict:
    r   = df.iloc[-1]
    r_1 = df.iloc[-2] if len(df) > 1 else r

    avg_vol = df["Volume"].rolling(20).mean().iloc[-1]
    vol_ratio = r["Volume"] / avg_vol if avg_vol > 0 else 1
    pct_chg   = (r["Close"] - r_1["Close"]) / r_1["Close"] * 100
    hi_lo     = r["High"] - r["Low"]
    range_pos = (r["Close"] - r["Low"]) / hi_lo if hi_lo > 0 else 0.5

    # V — Volume (max 5)
    v = 5 if vol_ratio >= 5 else 3 if vol_ratio >= 2 else 2 if vol_ratio >= 1.5 else 0
    # P — Momentum (max 3)
    p = 3 if abs(pct_chg) >= 5 else 2 if abs(pct_chg) >= 3 else 1 if abs(pct_chg) >= 1 else 0
    # R — Range Position (max 2)
    rng = 2 if range_pos >= 0.75 else 1 if range_pos >= 0.5 else 0
    # T — Trend Alignment (max 3)
    t = 0
    if r["Close"] > r["EMA20"]:  t += 1
    if r["EMA20"]  > r["EMA50"]: t += 1
    if r["ADX"] > 25:            t += 1

    total = v + p + rng + t
    if total >= 8:
        tier, tier_cls = "STRONG SIGNAL",   "sig-strong"
    elif total >= 5:
        tier, tier_cls = "BUILDING",        "sig-building"
    elif total >= 3:
        tier, tier_cls = "LOW SIGNAL",      "sig-low"
    else:
        tier, tier_cls = "NO SIGNAL",       "sig-none"

    return {
        "total": total, "v": v, "p": p, "r": rng, "t": t,
        "tier": tier, "tier_cls": tier_cls,
        "vol_ratio": round(vol_ratio, 2),
        "pct_chg": round(pct_chg, 2),
        "range_pos": round(range_pos, 2),
    }

# ── Formatting helpers ───────────────────────────────────────────────────────
def fmt_cap(n):
    if n == 0: return "N/A"
    if n >= 1e12: return f"₹{n/1e12:.2f}T"
    if n >= 1e9:  return f"₹{n/1e9:.2f}B"
    if n >= 1e7:  return f"₹{n/1e7:.2f}Cr"
    return f"₹{n:,.0f}"

def fmt_vol(n):
    if n == 0: return "N/A"
    if n >= 1e7: return f"{n/1e7:.2f}Cr"
    if n >= 1e5: return f"{n/1e5:.2f}L"
    return f"{n:,.0f}"

def bar_html(score, max_score, width=100):
    pct = int((score / max_score) * width) if max_score > 0 else 0
    return f'<div class="ns-comp-bar-wrap"><div class="ns-comp-bar" style="width:{pct}%"></div></div>'

# ── Build context string for agents ─────────────────────────────────────────
def build_context(symbol, score, df, fund):
    r = df.iloc[-1]
    return f"""
SYMBOL: {symbol}
SIGNAL: {score['tier']} ({score['total']}/13)
COMPONENTS: V={score['v']}/5 (vol_ratio={score['vol_ratio']}x)  P={score['p']}/3 (chg={score['pct_chg']}%)  R={score['r']}/2 (range_pos={score['range_pos']})  T={score['t']}/3

MARKET STRUCTURE:
  Close:  {r['Close']:.2f}
  EMA20:  {r['EMA20']:.2f}  ({'ABOVE' if r['Close']>r['EMA20'] else 'BELOW'})
  EMA50:  {r['EMA50']:.2f}  ({'ABOVE' if r['Close']>r['EMA50'] else 'BELOW'})
  EMA200: {r['EMA200']:.2f} ({'ABOVE' if r['Close']>r['EMA200'] else 'BELOW'})
  VWAP:   {r['VWAP']:.2f}   ({'ABOVE' if r['Close']>r['VWAP'] else 'BELOW'})
  BB Upper/Lower: {r['BB_upper']:.2f} / {r['BB_lower']:.2f}

TIMING QUALITY:
  RSI14: {r['RSI']:.1f}
  ADX14: {r['ADX']:.1f}  +DI={r['DI_pos']:.1f}  -DI={r['DI_neg']:.1f}
  ATR14: {r['ATR']:.4f}  ({r['ATR']/r['Close']*100:.2f}% of price)

FUNDAMENTALS:
  PE: {fund['pe'] if fund['pe'] else 'N/A'}
  EPS: {fund['eps'] if fund['eps'] else 'N/A'}
  Market Cap: {fmt_cap(fund['mkt_cap'])}
  52W High/Low: {fund['52w_high']} / {fund['52w_low']}
""".strip()

# ── Stream a single agent ────────────────────────────────────────────────────
def stream_agent(agent, context, api_key, container):
    client = anthropic.Anthropic(api_key=api_key)
    full_text = ""
    container.markdown(
        f'<div class="ns-agent-block">'
        f'<div class="ns-agent-name {agent["cls"]}">{agent["label"]}</div>'
        f'<div class="ns-agent-text">Analysing...</div></div>',
        unsafe_allow_html=True
    )
    with client.messages.stream(
        model="claude-haiku-4-5-20251001",
        max_tokens=300,
        system=agent["system"],
        messages=[{"role": "user", "content": f"Analyse this NSE stock:\n\n{context}"}],
    ) as stream:
        for text in stream.text_stream:
            full_text += text
            container.markdown(
                f'<div class="ns-agent-block">'
                f'<div class="ns-agent-name {agent["cls"]}">{agent["label"]}</div>'
                f'<div class="ns-agent-text">{full_text}▌</div></div>',
                unsafe_allow_html=True
            )
    # Extract verdict for CIO
    verdict_pill = ""
    if agent["key"] == "CIO":
        ul = full_text.upper()
        if "BUY"  in ul: verdict_pill = '<span class="ns-verdict v-buy">BUY</span>'
        elif "SELL" in ul: verdict_pill = '<span class="ns-verdict v-sell">SELL</span>'
        elif "HOLD" in ul: verdict_pill = '<span class="ns-verdict v-hold">HOLD</span>'
        else:               verdict_pill = '<span class="ns-verdict v-wait">WAIT</span>'
    container.markdown(
        f'<div class="ns-agent-block">'
        f'<div class="ns-agent-name {agent["cls"]}">{agent["label"]}</div>'
        f'<div class="ns-agent-text">{full_text}</div>'
        f'{verdict_pill}</div>',
        unsafe_allow_html=True
    )
    return full_text

# ── PDF Generator ────────────────────────────────────────────────────────────
class NiftyPDF(FPDF):
    def __init__(self):
        super().__init__()
        self.set_auto_page_break(auto=True, margin=15)

    def header(self):
        # Dark background full width
        self.set_fill_color(6, 10, 4)
        self.rect(0, 0, 210, 297, "F")
        # Orange top bar
        self.set_fill_color(255, 102, 0)
        self.rect(0, 0, 210, 2, "F")
        # Logo text
        self.set_xy(10, 6)
        self.set_font("Helvetica", "B", 18)
        self.set_text_color(255, 102, 0)
        self.cell(0, 10, "NIFTYSNIPER", ln=0)
        self.set_font("Helvetica", "", 9)
        self.set_text_color(136, 136, 136)
        self.set_xy(10, 16)
        self.cell(0, 6, "DETECT EARLY. ACT SMART.", ln=1)
        self.set_xy(0, 26)

    def footer(self):
        self.set_y(-12)
        self.set_font("Helvetica", "I", 7)
        self.set_text_color(80, 80, 80)
        self.cell(0, 5, "Data via Yahoo Finance / NSE. Signals are not financial advice. Past performance does not guarantee future results.", align="C")

    def section_title(self, title):
        self.set_fill_color(13, 26, 13)
        self.set_draw_color(255, 102, 0)
        self.set_line_width(0.5)
        self.rect(10, self.get_y(), 190, 7, "F")
        # Left orange accent bar
        self.set_fill_color(255, 102, 0)
        self.rect(10, self.get_y(), 2, 7, "F")
        self.set_xy(14, self.get_y() + 0.5)
        self.set_font("Helvetica", "B", 8)
        self.set_text_color(255, 102, 0)
        self.cell(0, 6, title.upper(), ln=1)
        self.set_draw_color(26, 46, 26)
        self.ln(1)

    def kv_row(self, label, value, value_color=(232, 232, 232)):
        self.set_fill_color(13, 26, 13)
        self.rect(10, self.get_y(), 190, 6, "F")
        self.set_x(12)
        self.set_font("Helvetica", "", 8)
        self.set_text_color(136, 136, 136)
        self.cell(80, 6, label)
        self.set_font("Courier", "B", 8)
        self.set_text_color(*value_color)
        self.cell(0, 6, str(value), ln=1)

    def agent_block(self, name, text, name_color):
        self.set_fill_color(6, 15, 6)
        y0 = self.get_y()
        self.set_font("Helvetica", "B", 8)
        self.set_text_color(*name_color)
        self.set_x(12)
        self.cell(0, 6, name, ln=1)
        self.set_font("Helvetica", "", 7.5)
        self.set_text_color(220, 220, 220)
        self.set_x(12)
        self.multi_cell(186, 5, text)
        self.ln(3)


def generate_pdf(symbol, score, df, fund, agent_texts, kronos_data=None) -> bytes:
    r   = df.iloc[-1]
    pdf = NiftyPDF()
    pdf.add_page()

    # ── Signal badge ──
    pdf.set_fill_color(13, 26, 13)
    pdf.rect(10, pdf.get_y(), 190, 24, "F")
    pdf.set_xy(10, pdf.get_y() + 2)
    pdf.set_font("Helvetica", "", 8)
    pdf.set_text_color(136, 136, 136)
    pdf.cell(0, 5, f"{symbol}  |  1D  |  {ist_now()}", align="C", ln=1)
    pdf.set_font("Helvetica", "B", 22)
    sig_color = (255,102,0) if "STRONG" in score["tier"] else \
                (255,170,0) if "BUILDING" in score["tier"] else \
                (136,136,136)
    pdf.set_text_color(*sig_color)
    pdf.cell(0, 12, f"SIGNAL: {score['tier']}  ({score['total']}/13)", align="C", ln=1)
    pdf.ln(4)

    # ── Signal Components ──
    pdf.section_title("Signal Components")
    comp_rows = [
        ("V — Volume (max 5)",       f"{score['v']}/5",   f"vol_ratio = {score['vol_ratio']}x"),
        ("P — Momentum (max 3)",     f"{score['p']}/3",   f"chg = {score['pct_chg']}%"),
        ("R — Range Position (max 2)",f"{score['r']}/2",  f"range_pos = {score['range_pos']}"),
        ("T — Trend Alignment (max 3)",f"{score['t']}/3", f"ADX = {r['ADX']:.1f}"),
    ]
    for lbl, sc, raw in comp_rows:
        pdf.set_fill_color(13, 26, 13)
        pdf.rect(10, pdf.get_y(), 190, 6, "F")
        pdf.set_x(12)
        pdf.set_font("Helvetica", "", 8)
        pdf.set_text_color(136, 136, 136)
        pdf.cell(90, 6, lbl)
        pdf.set_font("Courier", "B", 8)
        pdf.set_text_color(255, 102, 0)
        pdf.cell(20, 6, sc)
        pdf.set_font("Helvetica", "", 8)
        pdf.set_text_color(136, 136, 136)
        pdf.cell(0, 6, raw, ln=1)
    pdf.ln(3)

    # ── Market Structure ──
    pdf.section_title("Market Structure")
    def vc(val, ref): return (0,200,81) if val > ref else (255,68,68)
    pdf.kv_row("Close",        f"{r['Close']:.2f}")
    pdf.kv_row("EMA 20",       f"{r['EMA20']:.2f}  ({'above' if r['Close']>r['EMA20'] else 'below'})",  vc(r['Close'],r['EMA20']))
    pdf.kv_row("EMA 50",       f"{r['EMA50']:.2f}  ({'above' if r['Close']>r['EMA50'] else 'below'})",  vc(r['Close'],r['EMA50']))
    pdf.kv_row("EMA 200",      f"{r['EMA200']:.2f} ({'above' if r['Close']>r['EMA200'] else 'below'})", vc(r['Close'],r['EMA200']))
    pdf.kv_row("VWAP",         f"{r['VWAP']:.2f}   ({'above' if r['Close']>r['VWAP'] else 'below'})",  vc(r['Close'],r['VWAP']))
    pdf.kv_row("BB Upper/Lower",f"{r['BB_upper']:.2f} / {r['BB_lower']:.2f}")
    pdf.ln(3)

    # ── Timing Quality ──
    pdf.section_title("Timing Quality")
    pdf.kv_row("RSI 14",  f"{r['RSI']:.1f}")
    pdf.kv_row("ADX 14",  f"{r['ADX']:.1f}  ({'Trending' if r['ADX']>25 else 'Ranging'})")
    pdf.kv_row("+DI / -DI", f"{r['DI_pos']:.1f} / {r['DI_neg']:.1f}")
    pdf.kv_row("ATR 14",  f"{r['ATR']:.4f}  ({r['ATR']/r['Close']*100:.2f}% of price)")
    pdf.ln(3)

    # ── Fundamentals ──
    pdf.section_title("Fundamentals")
    pdf.kv_row("PE Ratio",    str(fund['pe'])  if fund['pe']  else "N/A")
    pdf.kv_row("EPS",         str(fund['eps']) if fund['eps'] else "N/A")
    pdf.kv_row("Market Cap",  fmt_cap(fund['mkt_cap']))
    pdf.kv_row("52W High",    str(fund['52w_high']) if fund['52w_high'] else "N/A")
    pdf.kv_row("52W Low",     str(fund['52w_low'])  if fund['52w_low']  else "N/A")
    pdf.kv_row("3M Avg Vol",  fmt_vol(fund['avg_vol']))
    pdf.ln(3)

    # ── Kronos Forecast ──
    if kronos_data:
        pdf.section_title("Kronos-Mini AI Forecast")
        for k, v in kronos_data.items():
            pdf.kv_row(k, str(v))
        pdf.ln(3)

    # ── AI Agent Council ──
    pdf.section_title("AI Lab — Agent Debate")
    agent_colors = {
        "BULL":         (0,200,81),
        "BEAR":         (255,68,68),
        "RISK MANAGER": (255,170,0),
        "CIO":          (255,102,0),
    }
    for ag in AGENTS:
        text = agent_texts.get(ag["key"], "")
        if text:
            pdf.agent_block(
                f"{ag['label']} — Verdict",
                text,
                agent_colors.get(ag["key"], (232,232,232))
            )

    return bytes(pdf.output())

# ═══════════════════════════════════════════════════════════════════════════
# MAIN APP
# ═══════════════════════════════════════════════════════════════════════════

# ── Hero bar ─────────────────────────────────────────────────────────────────
st.markdown("""
<div class="ns-hero">
  <div class="ns-logo-wrap">
    <div class="ns-logo-icon">NS</div>
    <div>
      <div class="ns-logo-text">NiftySniper <span style="color:#ff6600">AI Lab</span></div>
      <div class="ns-logo-sub">NSE Signal Intelligence · Detect Early. Act Smart.</div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

# ── Input row ─────────────────────────────────────────────────────────────────
col_sym, col_btn = st.columns([4, 1])
with col_sym:
    symbol_input = st.selectbox(
        "Select stock",
        options=[""] + sorted(SYMBOLS.keys()),
        format_func=lambda x: "— Type or select an NSE symbol —" if x == "" else x,
        label_visibility="collapsed",
    )
with col_btn:
    analyse_btn = st.button("ANALYSE →", use_container_width=True)

# API key from secrets
api_key = st.secrets.get("ANTHROPIC_API_KEY", "") if hasattr(st, "secrets") else ""

# ── Guard ────────────────────────────────────────────────────────────────────
if not symbol_input:
    st.markdown(f"""
    <div style="text-align:center; padding: 4rem 0; color:{MUTED};">
        <div style="font-size:48px; margin-bottom:1rem;">🎯</div>
        <div style="font-size:18px; font-weight:600; color:{TEXT}; margin-bottom:0.5rem;">Select an NSE symbol above</div>
        <div style="font-size:14px;">Multi-factor signal intelligence · Kronos AI Forecast · AI Agent Council</div>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

# ── Fetch data ────────────────────────────────────────────────────────────────
ticker = SYMBOLS.get(symbol_input, f"{symbol_input}.NS")
with st.spinner(f"Fetching {symbol_input} data..."):
    df, fund = fetch_data(ticker)

if df is None or len(df) < 30:
    st.error(f"Could not fetch sufficient data for **{symbol_input}**. Try another symbol.")
    st.stop()

score  = compute_score(df)
r      = df.iloc[-1]
context_str = build_context(symbol_input, score, df, fund)

# ── Two-column layout ─────────────────────────────────────────────────────────
left, right = st.columns([3, 2], gap="medium")

# ───────────────────────────── LEFT COLUMN ──────────────────────────────────
with left:

    # 01 SIGNAL OUTPUT
    st.markdown(f"""
    <div class="ns-signal-badge">
      <div class="ns-signal-label">Signal Output — {symbol_input}</div>
      <div class="ns-signal-value {score['tier_cls']}">{score['tier']}</div>
      <div class="ns-signal-score">Score: {score['total']} / 13</div>
      <div class="ns-signal-time">{ist_now()}</div>
    </div>
    """, unsafe_allow_html=True)

    # 02 SIGNAL COMPONENTS
    st.markdown('<div class="ns-section"><div class="ns-section-title">02 — Signal Components</div>', unsafe_allow_html=True)
    comps = [
        ("V — Volume",          score['v'], 5,  f"vol_ratio = {score['vol_ratio']}x"),
        ("P — Momentum",        score['p'], 3,  f"chg = {score['pct_chg']}%"),
        ("R — Range Position",  score['r'], 2,  f"range_pos = {score['range_pos']}"),
        ("T — Trend Alignment", score['t'], 3,  f"ADX = {r['ADX']:.1f}"),
    ]
    for lbl, sc, mx, raw in comps:
        pct = int(sc / mx * 100) if mx else 0
        st.markdown(f"""
        <div class="ns-comp-row">
          <div class="ns-comp-key">{lbl}</div>
          <div class="ns-comp-bar-wrap"><div class="ns-comp-bar" style="width:{pct}%"></div></div>
          <div class="ns-comp-score">{sc}/{mx}</div>
          <div class="ns-comp-raw">{raw}</div>
        </div>
        """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # 03 MARKET STRUCTURE
    def up_down(val, ref):
        cls = "kv-up" if val > ref else "kv-down"
        tag = "▲ ABOVE" if val > ref else "▼ BELOW"
        return cls, tag

    st.markdown('<div class="ns-section"><div class="ns-section-title">03 — Market Structure</div>', unsafe_allow_html=True)
    struct_rows = [
        ("Close",       f"{r['Close']:.2f}",   "kv-neut", ""),
        ("EMA 20",      f"{r['EMA20']:.2f}",   *up_down(r['Close'], r['EMA20'])),
        ("EMA 50",      f"{r['EMA50']:.2f}",   *up_down(r['Close'], r['EMA50'])),
        ("EMA 200",     f"{r['EMA200']:.2f}",  *up_down(r['Close'], r['EMA200'])),
        ("VWAP",        f"{r['VWAP']:.2f}",    *up_down(r['Close'], r['VWAP'])),
        ("BB Upper",    f"{r['BB_upper']:.2f}", "kv-neut", ""),
        ("BB Lower",    f"{r['BB_lower']:.2f}", "kv-neut", ""),
    ]
    for lbl, val, cls, tag in struct_rows:
        st.markdown(f"""
        <div class="ns-kv-row">
          <div class="ns-kv-label">{lbl}</div>
          <div class="ns-kv-value {cls}">{val} <span style="font-size:11px;font-weight:400">{tag}</span></div>
        </div>
        """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # 04 TIMING QUALITY
    rsi_cls = "kv-down" if r['RSI'] > 70 else "kv-up" if r['RSI'] < 30 else "kv-neut"
    adx_lbl = "Trending" if r['ADX'] > 25 else "Ranging"
    st.markdown(f"""
    <div class="ns-section"><div class="ns-section-title">04 — Timing Quality</div>
    <div class="ns-kv-row"><div class="ns-kv-label">RSI 14</div>
      <div class="ns-kv-value {rsi_cls}">{r['RSI']:.1f}</div></div>
    <div class="ns-kv-row"><div class="ns-kv-label">ADX 14</div>
      <div class="ns-kv-value kv-neut">{r['ADX']:.1f} <span style="font-size:11px">({adx_lbl})</span></div></div>
    <div class="ns-kv-row"><div class="ns-kv-label">+DI / -DI</div>
      <div class="ns-kv-value kv-neut">{r['DI_pos']:.1f} / {r['DI_neg']:.1f}</div></div>
    <div class="ns-kv-row"><div class="ns-kv-label">ATR 14</div>
      <div class="ns-kv-value kv-neut">{r['ATR']:.4f} <span style="font-size:11px">({r['ATR']/r['Close']*100:.2f}% of price)</span></div></div>
    </div>
    """, unsafe_allow_html=True)

    # 05 FUNDAMENTALS
    pe_disp  = str(fund['pe'])  if fund['pe']  else "N/A"
    eps_disp = str(fund['eps']) if fund['eps'] else "N/A"
    cap_disp = fmt_cap(fund['mkt_cap'])
    h52_disp = str(fund['52w_high']) if fund['52w_high'] else "N/A"
    l52_disp = str(fund['52w_low'])  if fund['52w_low']  else "N/A"
    avl_disp = fmt_vol(fund['avg_vol'])
    # % from 52w high
    pct_from_high = ((r['Close'] - fund['52w_high']) / fund['52w_high'] * 100) if fund['52w_high'] else 0
    high_cls = "kv-up" if pct_from_high > -5 else "kv-down"

    st.markdown(f"""
    <div class="ns-section"><div class="ns-section-title">05 — Fundamentals</div>
    <div class="ns-kv-row"><div class="ns-kv-label">PE Ratio</div>
      <div class="ns-kv-value kv-neut">{pe_disp}</div></div>
    <div class="ns-kv-row"><div class="ns-kv-label">EPS (TTM)</div>
      <div class="ns-kv-value kv-neut">{eps_disp}</div></div>
    <div class="ns-kv-row"><div class="ns-kv-label">Market Cap</div>
      <div class="ns-kv-value kv-neut">{cap_disp}</div></div>
    <div class="ns-kv-row"><div class="ns-kv-label">52W High</div>
      <div class="ns-kv-value {high_cls}">{h52_disp} <span style="font-size:11px">({pct_from_high:+.1f}%)</span></div></div>
    <div class="ns-kv-row"><div class="ns-kv-label">52W Low</div>
      <div class="ns-kv-value kv-neut">{l52_disp}</div></div>
    <div class="ns-kv-row"><div class="ns-kv-label">3M Avg Volume</div>
      <div class="ns-kv-value kv-neut">{avl_disp}</div></div>
    </div>
    """, unsafe_allow_html=True)

# ───────────────────────────── RIGHT COLUMN ──────────────────────────────────
with right:

    # 06 KRONOS AI FORECAST
    st.markdown('<div class="ns-section"><div class="ns-section-title">06 — Kronos-Mini AI Forecast</div>', unsafe_allow_html=True)

    kronos_result = None
    if KRONOS_AVAILABLE:
        if f"kronos_{ticker}" not in st.session_state:
            with st.spinner("Running Kronos forecast..."):
                try:
                    kronos_result = render_kronos_forecast(ticker, df)
                    st.session_state[f"kronos_{ticker}"] = kronos_result
                except Exception as e:
                    st.session_state[f"kronos_{ticker}"] = None
        else:
            kronos_result = st.session_state[f"kronos_{ticker}"]

    if kronos_result and isinstance(kronos_result, dict):
        dir_color = GREEN if str(kronos_result.get("Direction","")).upper() == "UP" else RED
        dir_arrow = "▲" if str(kronos_result.get("Direction","")).upper() == "UP" else "▼"
        for k, v in kronos_result.items():
            v_str = str(v)
            v_cls = "kv-up" if k == "Direction" and "UP" in v_str.upper() else \
                    "kv-down" if k == "Direction" else "kv-neut"
            if k == "Direction":
                v_str = f"{dir_arrow} {v_str}"
            st.markdown(f"""
            <div class="ns-kv-row">
              <div class="ns-kv-label">{k}</div>
              <div class="ns-kv-value {v_cls}">{v_str}</div>
            </div>
            """, unsafe_allow_html=True)
    else:
        # Mock Kronos if not available — AR1 placeholder
        pct_pred = round(-score['pct_chg'] * 0.6 + np.random.uniform(-2, 2), 2)
        pred_close = round(r['Close'] * (1 + pct_pred / 100), 2)
        bull_pct   = round(50 + score['total'] * 2 + np.random.uniform(-5, 5), 1)
        kronos_result = {
            "Direction":        "UP" if pct_pred > 0 else "DOWN",
            "Predicted Change": f"{pct_pred:+.2f}%",
            "Predicted Close":  pred_close,
            "Forecast Peak":    round(pred_close * 1.04, 2),
            "Forecast Trough":  round(pred_close * 0.96, 2),
            "Bull Candle %":    f"{bull_pct}%",
            "Candles Forecast": 20,
        }
        dir_arrow = "▲" if kronos_result["Direction"] == "UP" else "▼"
        for k, v in kronos_result.items():
            v_cls = "kv-up" if k == "Direction" and "UP" in str(v) else \
                    "kv-down" if k == "Direction" else "kv-neut"
            v_str = f"{dir_arrow} {v}" if k == "Direction" else str(v)
            st.markdown(f"""
            <div class="ns-kv-row">
              <div class="ns-kv-label">{k}</div>
              <div class="ns-kv-value {v_cls}">{v_str}</div>
            </div>
            """, unsafe_allow_html=True)
        st.markdown(f'<div style="font-size:10px;color:{MUTED};margin-top:4px;">AR1 mock — Kronos module not loaded</div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

    # 07 AI AGENT COUNCIL
    st.markdown('<div class="ns-section"><div class="ns-section-title">07 — AI Agent Council</div>', unsafe_allow_html=True)

    debate_key = f"debate_{ticker}_{score['total']}"
    agent_texts = {}

    if not api_key:
        st.markdown(f'<div style="color:{MUTED};font-size:13px;padding:0.5rem 0">Add ANTHROPIC_API_KEY to Streamlit secrets to enable AI debate.</div>', unsafe_allow_html=True)
    elif debate_key in st.session_state:
        agent_texts = st.session_state[debate_key]
        for ag in AGENTS:
            text = agent_texts.get(ag["key"], "")
            verdict_pill = ""
            if ag["key"] == "CIO":
                ul = text.upper()
                if "BUY"  in ul: verdict_pill = '<span class="ns-verdict v-buy">BUY</span>'
                elif "SELL" in ul: verdict_pill = '<span class="ns-verdict v-sell">SELL</span>'
                elif "HOLD" in ul: verdict_pill = '<span class="ns-verdict v-hold">HOLD</span>'
                else:               verdict_pill = '<span class="ns-verdict v-wait">WAIT</span>'
            st.markdown(f"""
            <div class="ns-agent-block">
              <div class="ns-agent-name {ag['cls']}">{ag['label']}</div>
              <div class="ns-agent-text">{text}</div>
              {verdict_pill}
            </div>
            """, unsafe_allow_html=True)
    else:
        run_debate = st.button("Run AI Debate →", key="run_debate", use_container_width=True)
        if run_debate:
            containers = [st.empty() for _ in AGENTS]
            for ag, cont in zip(AGENTS, containers):
                text = stream_agent(ag, context_str, api_key, cont)
                agent_texts[ag["key"]] = text
                time.sleep(0.3)
            st.session_state[debate_key] = agent_texts
            st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)

    # 08 EXPORT
    st.markdown('<div class="ns-section"><div class="ns-section-title">08 — Export Report</div>', unsafe_allow_html=True)

    k_data = {}
    if kronos_result and isinstance(kronos_result, dict):
        k_data = kronos_result

    if agent_texts or not api_key:
        try:
            pdf_bytes = generate_pdf(symbol_input, score, df, fund, agent_texts, k_data)
            fname = f"NiftySniper_{symbol_input}_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
            st.download_button(
                label="⬇  Download PDF Report",
                data=pdf_bytes,
                file_name=fname,
                mime="application/pdf",
                use_container_width=True,
            )
            st.markdown(f'<div style="font-size:11px;color:{MUTED};margin-top:6px;text-align:center">{fname}</div>', unsafe_allow_html=True)
        except Exception as e:
            st.error(f"PDF generation error: {e}")
    else:
        st.markdown(f'<div style="font-size:13px;color:{MUTED};padding:0.25rem 0">Run the AI debate first to include agent analysis in the report.</div>', unsafe_allow_html=True)
        try:
            pdf_bytes = generate_pdf(symbol_input, score, df, fund, {}, k_data)
            fname = f"NiftySniper_{symbol_input}_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
            st.download_button(
                label="⬇  Download Signal Report (no debate)",
                data=pdf_bytes,
                file_name=fname,
                mime="application/pdf",
                use_container_width=True,
            )
        except Exception as e:
            st.error(f"PDF generation error: {e}")

    st.markdown('</div>', unsafe_allow_html=True)

    # Disclaimer
    st.markdown(f"""
    <div style="font-size:10px; color:{MUTED}; text-align:center; margin-top:1rem; padding-top:0.75rem; border-top:1px solid {BORDER};">
    Data via Yahoo Finance / NSE. Signals are not financial advice.<br>
    Past performance does not guarantee future results.
    </div>
    """, unsafe_allow_html=True)
