"""
NiftySniper AI Lab — NSE Signal Intelligence
Mirror of CryptoSniper: single column, top to bottom
Sections: Signal Output -> Components -> Market Structure
       -> Timing Quality -> Kronos AI -> AI Agent Council -> Export
Theme: #ff6600 orange on #060a04 black
"""

import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import anthropic
import time
from datetime import datetime, timezone, timedelta
from fpdf import FPDF

try:
    from kronos_streamlit import render_kronos_forecast
    KRONOS_AVAILABLE = True
except Exception:
    KRONOS_AVAILABLE = False

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="NiftySniper AI Lab",
    page_icon="🎯",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ── Design tokens ─────────────────────────────────────────────────────────────
BG     = "#060a04"
CARD   = "#0d1a0d"
ACCENT = "#ff6600"
AMBER  = "#ffaa00"
GREEN  = "#00c851"
RED    = "#ff4444"
TEXT   = "#e8e8e8"
MUTED  = "#888888"
BORDER = "#1a2e1a"

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600&family=Inter:wght@400;500;600;700&display=swap');

html, body, [data-testid="stApp"] {{
    background: {BG}; color: {TEXT};
    font-family: 'Inter', sans-serif;
}}
[data-testid="stAppViewContainer"], [data-testid="stHeader"] {{ background: {BG}; }}
#MainMenu, footer, header {{ visibility: hidden; }}
.block-container {{ padding: 1.5rem 1.5rem 3rem; max-width: 780px; margin: 0 auto; }}
section[data-testid="stMain"] > div {{ padding-top: 0; }}

/* Hero */
.ns-hero {{
    text-align: center;
    padding: 2rem 0 1.5rem;
    border-bottom: 1px solid {BORDER};
    margin-bottom: 1.5rem;
}}
.ns-hero-logo {{
    font-size: 11px; font-weight: 600; letter-spacing: 0.2em;
    color: {ACCENT}; text-transform: uppercase; margin-bottom: 0.5rem;
}}
.ns-hero-title {{
    font-size: 36px; font-weight: 700; color: {TEXT};
    letter-spacing: -1px; margin-bottom: 0.25rem;
}}
.ns-hero-sub {{
    font-size: 13px; color: {MUTED};
    letter-spacing: 0.05em;
}}

/* Signal badge */
.ns-badge {{
    text-align: center;
    background: {CARD};
    border: 1px solid {BORDER};
    border-radius: 12px;
    padding: 2rem 1rem 1.5rem;
    margin-bottom: 1.25rem;
}}
.ns-badge-label {{
    font-size: 11px; letter-spacing: 0.15em;
    color: {MUTED}; text-transform: uppercase;
    margin-bottom: 0.5rem;
}}
.ns-badge-signal {{
    font-size: 38px; font-weight: 700;
    font-family: 'JetBrains Mono', monospace;
    margin-bottom: 0.25rem;
}}
.ns-badge-score {{
    font-size: 16px; color: {MUTED};
    font-family: 'JetBrains Mono', monospace;
    margin-bottom: 0.5rem;
}}
.ns-badge-time {{ font-size: 12px; color: {MUTED}; }}
.sig-strong  {{ color: {ACCENT}; }}
.sig-building{{ color: {AMBER};  }}
.sig-low     {{ color: {MUTED};  }}
.sig-none    {{ color: {RED};    }}

/* Section cards */
.ns-card {{
    background: {CARD};
    border: 1px solid {BORDER};
    border-left: 3px solid {ACCENT};
    border-radius: 8px;
    padding: 1rem 1.25rem;
    margin-bottom: 1rem;
}}
.ns-card-title {{
    font-size: 10px; font-weight: 600;
    letter-spacing: 0.18em; text-transform: uppercase;
    color: {ACCENT}; margin-bottom: 0.75rem;
}}

/* KV rows */
.ns-row {{
    display: flex; justify-content: space-between;
    align-items: center; padding: 5px 0;
    border-bottom: 1px solid {BORDER}; font-size: 13px;
}}
.ns-row:last-child {{ border-bottom: none; }}
.ns-lbl {{ color: {MUTED}; }}
.ns-val {{ font-family: 'JetBrains Mono', monospace; font-weight: 600; }}
.up   {{ color: {GREEN}; }}
.down {{ color: {RED};   }}
.neu  {{ color: {TEXT};  }}

/* Component bars */
.ns-comp {{
    display: flex; align-items: center;
    padding: 6px 0; border-bottom: 1px solid {BORDER};
    gap: 10px;
}}
.ns-comp:last-child {{ border-bottom: none; }}
.ns-comp-lbl  {{ font-size: 11px; color: {MUTED}; min-width: 140px; }}
.ns-bar-wrap  {{ flex: 1; background: #0a150a; border-radius: 3px; height: 5px; }}
.ns-bar       {{ height: 5px; border-radius: 3px; background: {ACCENT}; }}
.ns-comp-sc   {{ font-family: 'JetBrains Mono', monospace; font-size: 13px;
                 min-width: 40px; text-align: right; color: {TEXT}; }}
.ns-comp-raw  {{ font-size: 11px; color: {MUTED}; min-width: 110px; text-align: right; }}

/* Kronos */
.kron-dir-up   {{ font-size: 28px; font-weight: 700; color: {GREEN};
                  font-family: 'JetBrains Mono', monospace; }}
.kron-dir-down {{ font-size: 28px; font-weight: 700; color: {RED};
                  font-family: 'JetBrains Mono', monospace; }}
.kron-badge    {{ font-size: 10px; color: {MUTED}; letter-spacing: 0.1em; }}

/* Agent blocks */
.ns-agent {{
    background: #060f06; border: 1px solid {BORDER};
    border-radius: 8px; padding: 1rem; margin-bottom: 0.75rem;
}}
.ns-agent-name {{
    font-size: 10px; font-weight: 600;
    letter-spacing: 0.15em; text-transform: uppercase;
    margin-bottom: 6px;
}}
.ag-bull {{ color: {GREEN};  }}
.ag-bear {{ color: {RED};    }}
.ag-risk {{ color: {AMBER};  }}
.ag-cio  {{ color: {ACCENT}; }}
.ns-agent-text {{ font-size: 13px; color: {TEXT}; line-height: 1.65; }}

/* Verdict */
.verdict {{
    display: inline-block; padding: 4px 14px;
    border-radius: 20px; font-size: 11px;
    font-weight: 700; letter-spacing: 0.1em;
    text-transform: uppercase; margin-top: 8px;
}}
.v-buy  {{ background:#003d12; color:{GREEN}; border:1px solid {GREEN}; }}
.v-sell {{ background:#3d0000; color:{RED};   border:1px solid {RED};   }}
.v-hold {{ background:#3d2000; color:{AMBER}; border:1px solid {AMBER}; }}
.v-wait {{ background:#1a1a1a; color:{MUTED}; border:1px solid {MUTED}; }}

/* Streamlit overrides */
div.stButton > button {{
    background: {ACCENT}; color: #000; font-weight: 700;
    border: none; border-radius: 8px; width: 100%;
    padding: 0.6rem 1.5rem; font-size: 14px; letter-spacing: 0.04em;
}}
div.stButton > button:hover {{ background: #ff8533; }}
div.stDownloadButton > button {{
    background: transparent; color: {ACCENT};
    border: 1px solid {ACCENT}; border-radius: 8px;
    font-weight: 600; width: 100%; padding: 0.5rem;
}}
div.stDownloadButton > button:hover {{ background: {ACCENT}; color: #000; }}
div[data-testid="stSelectbox"] > div {{
    background: {CARD}; border-color: {BORDER};
}}
.stSpinner > div {{ border-top-color: {ACCENT} !important; }}
</style>
""", unsafe_allow_html=True)

# ── Symbol dictionary ─────────────────────────────────────────────────────────
SYMBOLS = {
    "NIFTY 50":    "^NSEI",      "BANKNIFTY":   "^NSEBANK",
    "RELIANCE":    "RELIANCE.NS","TCS":          "TCS.NS",
    "HDFCBANK":    "HDFCBANK.NS","INFY":         "INFY.NS",
    "ICICIBANK":   "ICICIBANK.NS","SBIN":        "SBIN.NS",
    "WIPRO":       "WIPRO.NS",   "AXISBANK":     "AXISBANK.NS",
    "KOTAKBANK":   "KOTAKBANK.NS","LT":          "LT.NS",
    "BAJFINANCE":  "BAJFINANCE.NS","TATAMOTORS": "TATAMOTORS.NS",
    "MARUTI":      "MARUTI.NS",  "SUNPHARMA":    "SUNPHARMA.NS",
    "ONGC":        "ONGC.NS",    "NTPC":         "NTPC.NS",
    "POWERGRID":   "POWERGRID.NS","BPCL":        "BPCL.NS",
    "BHARTIARTL":  "BHARTIARTL.NS","HINDUNILVR": "HINDUNILVR.NS",
    "ASIANPAINT":  "ASIANPAINT.NS","NESTLEIND":  "NESTLEIND.NS",
    "TITAN":       "TITAN.NS",   "ULTRACEMCO":   "ULTRACEMCO.NS",
    "GRASIM":      "GRASIM.NS",  "ADANIENT":     "ADANIENT.NS",
    "ADANIPORTS":  "ADANIPORTS.NS","JSWSTEEL":   "JSWSTEEL.NS",
    "TATASTEEL":   "TATASTEEL.NS","HINDALCO":    "HINDALCO.NS",
    "BEL":         "BEL.NS",     "HAL":          "HAL.NS",
    "BHEL":        "BHEL.NS",    "COALINDIA":    "COALINDIA.NS",
    "VEDL":        "VEDL.NS",    "DRREDDY":      "DRREDDY.NS",
    "CIPLA":       "CIPLA.NS",   "DIVISLAB":     "DIVISLAB.NS",
    "APOLLOHOSP":  "APOLLOHOSP.NS","EICHERMOT":  "EICHERMOT.NS",
    "BAJAJ-AUTO":  "BAJAJ-AUTO.NS","HEROMOTOCO": "HEROMOTOCO.NS",
    "M&M":         "M&M.NS",     "TATACONSUM":   "TATACONSUM.NS",
    "ITC":         "ITC.NS",     "HCLTECH":      "HCLTECH.NS",
    "TECHM":       "TECHM.NS",   "LTIM":         "LTIM.NS",
    "BAJAJFINSV":  "BAJAJFINSV.NS","HDFCLIFE":   "HDFCLIFE.NS",
    "SBILIFE":     "SBILIFE.NS", "DLF":          "DLF.NS",
    "INDUSINDBK":  "INDUSINDBK.NS","PNB":        "PNB.NS",
    "BANKBARODA":  "BANKBARODA.NS","FEDERALBNK": "FEDERALBNK.NS",
}

AGENTS = [
    {"key":"BULL", "label":"Bull Agent",   "cls":"ag-bull",
     "system":"You are the BULL AGENT for NiftySniper NSE intelligence. Make the strongest bullish case using trend alignment, momentum, and institutional support. Cite specific numbers from the data. 3-4 sentences max."},
    {"key":"BEAR", "label":"Bear Agent",   "cls":"ag-bear",
     "system":"You are the BEAR AGENT for NiftySniper NSE intelligence. Make the strongest bearish case: overbought signals, resistance, weak volume, macro risks. Cite specific numbers. 3-4 sentences max."},
    {"key":"RISK", "label":"Risk Manager", "cls":"ag-risk",
     "system":"You are the RISK MANAGER for NiftySniper. Focus only on position sizing and risk. Calculate stop loss using 1.5x ATR below close. Suggest max position size as % of capital. Give risk/reward ratio. 3-4 sentences. No directional view."},
    {"key":"CIO",  "label":"CIO Verdict",  "cls":"ag-cio",
     "system":"You are the CIO of NiftySniper giving the final synthesis. Weigh bull and bear against risk. State a clear verdict: BUY / SELL / HOLD / WAIT. Give a confidence score 1-10. Cite the signal score and one decisive data point. 3-4 sentences max."},
]

# ── Helpers ───────────────────────────────────────────────────────────────────
def ist_now():
    ist = timezone(timedelta(hours=5, minutes=30))
    return datetime.now(ist).strftime("%d %b %Y  %H:%M IST")

def safe(text: str) -> str:
    """Strip characters outside Latin-1 for fpdf2 Helvetica."""
    subs = {
        "\u2014":"-", "\u2013":"-", "\u2019":"'", "\u2018":"'",
        "\u201c":'"', "\u201d":'"', "\u2022":"*", "\u00b7":".",
        "\u25b2":"UP", "\u25bc":"DOWN", "\u2192":"->", "\u20b9":"Rs",
        "\u00d7":"x",  "\u2026":"...",
    }
    t = str(text)
    for c, r in subs.items():
        t = t.replace(c, r)
    return t.encode("latin-1", errors="replace").decode("latin-1")

# ── Data fetch ────────────────────────────────────────────────────────────────
@st.cache_data(ttl=300, show_spinner=False)
def fetch_data(ticker: str):
    tk = yf.Ticker(ticker)
    df = tk.history(period="1y", auto_adjust=True)
    if df.empty:
        return None
    df = df[["Open","High","Low","Close","Volume"]].dropna()

    df["EMA20"]  = df["Close"].ewm(span=20,  adjust=False).mean()
    df["EMA50"]  = df["Close"].ewm(span=50,  adjust=False).mean()
    df["EMA200"] = df["Close"].ewm(span=200, adjust=False).mean()
    df["VWAP"]   = (df["Close"]*df["Volume"]).cumsum() / df["Volume"].cumsum()

    df["BB_mid"]   = df["Close"].rolling(20).mean()
    df["BB_std"]   = df["Close"].rolling(20).std()
    df["BB_upper"] = df["BB_mid"] + 2*df["BB_std"]
    df["BB_lower"] = df["BB_mid"] - 2*df["BB_std"]

    delta = df["Close"].diff()
    gain  = delta.clip(lower=0).rolling(14).mean()
    loss  = (-delta.clip(upper=0)).rolling(14).mean()
    df["RSI"] = 100 - (100 / (1 + gain/loss.replace(0, np.nan)))

    df["TR"] = pd.concat([
        df["High"]-df["Low"],
        (df["High"]-df["Close"].shift()).abs(),
        (df["Low"] -df["Close"].shift()).abs()
    ], axis=1).max(axis=1)
    df["ATR"] = df["TR"].rolling(14).mean()

    up   = df["High"].diff().clip(lower=0)
    down = (-df["Low"].diff()).clip(lower=0)
    up[up <= down] = 0; down[down <= up] = 0
    atr14 = df["TR"].rolling(14).sum()
    df["DI_pos"] = 100 * up.rolling(14).sum()   / atr14.replace(0, np.nan)
    df["DI_neg"] = 100 * down.rolling(14).sum() / atr14.replace(0, np.nan)
    dx = 100*(df["DI_pos"]-df["DI_neg"]).abs() / (df["DI_pos"]+df["DI_neg"]).replace(0, np.nan)
    df["ADX"] = dx.rolling(14).mean()

    return df

# ── Signal score ──────────────────────────────────────────────────────────────
def compute_score(df: pd.DataFrame) -> dict:
    r   = df.iloc[-1]
    r1  = df.iloc[-2] if len(df) > 1 else r
    avg_vol   = df["Volume"].rolling(20).mean().iloc[-1]
    vol_ratio = r["Volume"] / avg_vol if avg_vol > 0 else 1
    pct_chg   = (r["Close"] - r1["Close"]) / r1["Close"] * 100
    hi_lo     = r["High"] - r["Low"]
    range_pos = (r["Close"] - r["Low"]) / hi_lo if hi_lo > 0 else 0.5

    v = 5 if vol_ratio>=5 else 3 if vol_ratio>=2 else 2 if vol_ratio>=1.5 else 0
    p = 3 if abs(pct_chg)>=5 else 2 if abs(pct_chg)>=3 else 1 if abs(pct_chg)>=1 else 0
    rng = 2 if range_pos>=0.75 else 1 if range_pos>=0.5 else 0
    t = sum([r["Close"]>r["EMA20"], r["EMA20"]>r["EMA50"], r["ADX"]>25])

    total = v + p + rng + t
    if   total >= 8: tier, cls = "STRONG SIGNAL", "sig-strong"
    elif total >= 5: tier, cls = "BUILDING",      "sig-building"
    elif total >= 3: tier, cls = "LOW SIGNAL",    "sig-low"
    else:            tier, cls = "NO SIGNAL",     "sig-none"

    return {"total":total, "v":v, "p":p, "r":rng, "t":t,
            "tier":tier, "cls":cls,
            "vol_ratio":round(vol_ratio,2),
            "pct_chg":round(pct_chg,2),
            "range_pos":round(range_pos,2)}

# ── Build context for agents ──────────────────────────────────────────────────
def build_context(symbol, sc, df):
    r = df.iloc[-1]
    return f"""SYMBOL: {symbol}
SIGNAL: {sc['tier']} ({sc['total']}/13)
COMPONENTS: V={sc['v']}/5 (vol={sc['vol_ratio']}x)  P={sc['p']}/3 (chg={sc['pct_chg']}%)  R={sc['r']}/2  T={sc['t']}/3

MARKET STRUCTURE:
  Close:  {r['Close']:.2f}
  EMA20:  {r['EMA20']:.2f}  ({'ABOVE' if r['Close']>r['EMA20'] else 'BELOW'})
  EMA50:  {r['EMA50']:.2f}  ({'ABOVE' if r['Close']>r['EMA50'] else 'BELOW'})
  EMA200: {r['EMA200']:.2f} ({'ABOVE' if r['Close']>r['EMA200'] else 'BELOW'})
  VWAP:   {r['VWAP']:.2f}
  BB:     {r['BB_upper']:.2f} / {r['BB_lower']:.2f}

TIMING:
  RSI14:  {r['RSI']:.1f}
  ADX14:  {r['ADX']:.1f}  +DI={r['DI_pos']:.1f}  -DI={r['DI_neg']:.1f}
  ATR14:  {r['ATR']:.4f} ({r['ATR']/r['Close']*100:.2f}% of price)
  Stop:   {r['Close'] - 1.5*r['ATR']:.2f} (1.5x ATR)""".strip()

# ── Stream one agent ──────────────────────────────────────────────────────────
def stream_agent(agent, ctx, api_key, slot):
    client = anthropic.Anthropic(api_key=api_key)
    text = ""
    slot.markdown(
        f'<div class="ns-agent"><div class="ns-agent-name {agent["cls"]}">'
        f'{agent["label"]}</div><div class="ns-agent-text">Analysing...</div></div>',
        unsafe_allow_html=True)
    with client.messages.stream(
        model="claude-haiku-4-5-20251001", max_tokens=300,
        system=agent["system"],
        messages=[{"role":"user","content":f"Analyse:\n{ctx}"}]
    ) as stream:
        for chunk in stream.text_stream:
            text += chunk
            slot.markdown(
                f'<div class="ns-agent"><div class="ns-agent-name {agent["cls"]}">'
                f'{agent["label"]}</div><div class="ns-agent-text">{text}▌</div></div>',
                unsafe_allow_html=True)
    pill = ""
    if agent["key"] == "CIO":
        u = text.upper()
        if "BUY"  in u: pill = '<span class="verdict v-buy">BUY</span>'
        elif "SELL" in u: pill = '<span class="verdict v-sell">SELL</span>'
        elif "HOLD" in u: pill = '<span class="verdict v-hold">HOLD</span>'
        else:              pill = '<span class="verdict v-wait">WAIT</span>'
    slot.markdown(
        f'<div class="ns-agent"><div class="ns-agent-name {agent["cls"]}">'
        f'{agent["label"]}</div><div class="ns-agent-text">{text}</div>{pill}</div>',
        unsafe_allow_html=True)
    return text

# ── PDF ───────────────────────────────────────────────────────────────────────
class NiftyPDF(FPDF):
    def __init__(self):
        super().__init__()
        self.set_auto_page_break(auto=True, margin=15)

    def header(self):
        self.set_fill_color(6, 10, 4)
        self.rect(0, 0, 210, 297, "F")
        self.set_fill_color(255, 102, 0)
        self.rect(0, 0, 210, 2, "F")
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
        self.cell(0, 5,
            "Data via Yahoo Finance / NSE. Signals are not financial advice. "
            "Past performance does not guarantee future results.", align="C")

    def sec(self, title):
        self.set_fill_color(13, 26, 13)
        self.rect(10, self.get_y(), 190, 7, "F")
        self.set_fill_color(255, 102, 0)
        self.rect(10, self.get_y(), 2, 7, "F")
        self.set_xy(14, self.get_y() + 0.5)
        self.set_font("Helvetica", "B", 8)
        self.set_text_color(255, 102, 0)
        self.cell(0, 6, safe(title).upper(), ln=1)
        self.ln(1)

    def kv(self, label, value, vc=(232, 232, 232)):
        self.set_fill_color(13, 26, 13)
        self.rect(10, self.get_y(), 190, 6, "F")
        self.set_x(12)
        self.set_font("Helvetica", "", 8)
        self.set_text_color(136, 136, 136)
        self.cell(80, 6, safe(label))
        self.set_font("Courier", "B", 8)
        self.set_text_color(*vc)
        self.cell(0, 6, safe(str(value)), ln=1)

    def agent(self, name, text, nc):
        self.set_fill_color(6, 15, 6)
        self.set_font("Helvetica", "B", 8)
        self.set_text_color(*nc)
        self.set_x(12)
        self.cell(0, 6, safe(name), ln=1)
        self.set_font("Helvetica", "", 7.5)
        self.set_text_color(220, 220, 220)
        self.set_x(12)
        self.multi_cell(186, 5, safe(text))
        self.ln(3)


def generate_pdf(symbol, sc, df, agent_texts, kronos_data=None) -> bytes:
    r   = df.iloc[-1]
    pdf = NiftyPDF()
    pdf.add_page()

    # Signal badge
    pdf.set_fill_color(13, 26, 13)
    pdf.rect(10, pdf.get_y(), 190, 26, "F")
    pdf.set_xy(10, pdf.get_y() + 2)
    pdf.set_font("Helvetica", "", 8)
    pdf.set_text_color(136, 136, 136)
    pdf.cell(0, 5, safe(f"{symbol}  |  1D  |  {ist_now()}"), align="C", ln=1)
    sig_col = (255,102,0) if "STRONG" in sc["tier"] else \
              (255,170,0) if "BUILDING" in sc["tier"] else (136,136,136)
    pdf.set_font("Helvetica", "B", 22)
    pdf.set_text_color(*sig_col)
    pdf.cell(0, 14, safe(f"SIGNAL: {sc['tier']}  ({sc['total']}/13)"), align="C", ln=1)
    pdf.ln(4)

    # Signal Components
    pdf.sec("Signal Components")
    for lbl, s, mx, raw in [
        ("V - Volume (max 5)",         f"{sc['v']}/5", sc['v'], f"vol_ratio = {sc['vol_ratio']}x"),
        ("P - Momentum (max 3)",        f"{sc['p']}/3", sc['p'], f"chg = {sc['pct_chg']}%"),
        ("R - Range Position (max 2)",  f"{sc['r']}/2", sc['r'], f"range_pos = {sc['range_pos']}"),
        ("T - Trend Alignment (max 3)", f"{sc['t']}/3", sc['t'], f"ADX = {r['ADX']:.1f}"),
    ]:
        pdf.set_fill_color(13, 26, 13)
        pdf.rect(10, pdf.get_y(), 190, 6, "F")
        pdf.set_x(12)
        pdf.set_font("Helvetica", "", 8)
        pdf.set_text_color(136, 136, 136)
        pdf.cell(90, 6, safe(lbl))
        pdf.set_font("Courier", "B", 8)
        pdf.set_text_color(255, 102, 0)
        pdf.cell(20, 6, safe(str(s)))
        pdf.set_font("Helvetica", "", 8)
        pdf.set_text_color(136, 136, 136)
        pdf.cell(0, 6, safe(raw), ln=1)
    pdf.ln(3)

    # Market Structure
    def vc(v, ref): return (0,200,81) if v>ref else (255,68,68)
    pdf.sec("Market Structure")
    pdf.kv("Close",      f"{r['Close']:.2f}")
    pdf.kv("EMA 20",     f"{r['EMA20']:.2f}  ({'above' if r['Close']>r['EMA20'] else 'below'})",  vc(r['Close'],r['EMA20']))
    pdf.kv("EMA 50",     f"{r['EMA50']:.2f}  ({'above' if r['Close']>r['EMA50'] else 'below'})",  vc(r['Close'],r['EMA50']))
    pdf.kv("EMA 200",    f"{r['EMA200']:.2f} ({'above' if r['Close']>r['EMA200'] else 'below'})", vc(r['Close'],r['EMA200']))
    pdf.kv("VWAP",       f"{r['VWAP']:.2f}   ({'above' if r['Close']>r['VWAP'] else 'below'})",  vc(r['Close'],r['VWAP']))
    pdf.kv("BB Upper/Lower", f"{r['BB_upper']:.2f} / {r['BB_lower']:.2f}")
    pdf.ln(3)

    # Timing Quality
    pdf.sec("Timing Quality")
    pdf.kv("RSI 14",   f"{r['RSI']:.1f}")
    pdf.kv("ADX 14",   f"{r['ADX']:.1f}  ({'Trending' if r['ADX']>25 else 'Ranging'})")
    pdf.kv("+DI / -DI",f"{r['DI_pos']:.1f} / {r['DI_neg']:.1f}")
    pdf.kv("ATR 14",   f"{r['ATR']:.4f}  ({r['ATR']/r['Close']*100:.2f}% of price)")
    pdf.kv("Stop (1.5x ATR)", f"{r['Close'] - 1.5*r['ATR']:.2f}")
    pdf.ln(3)

    # Kronos
    if kronos_data:
        pdf.sec("Kronos-Mini AI Forecast")
        for k, v in kronos_data.items():
            pdf.kv(k, str(v))
        pdf.ln(3)

    # AI Agent Council
    pdf.sec("AI Lab - Agent Debate")
    agent_cols = {"BULL":(0,200,81),"BEAR":(255,68,68),"RISK":(255,170,0),"CIO":(255,102,0)}
    for ag in AGENTS:
        txt = agent_texts.get(ag["key"], "")
        if txt:
            pdf.agent(f"{ag['label']} Verdict", txt, agent_cols.get(ag["key"], (232,232,232)))

    return bytes(pdf.output())


# ═══════════════════════════════════════════════════════════════════════════
# APP
# ═══════════════════════════════════════════════════════════════════════════

# Hero
st.markdown(f"""
<div class="ns-hero">
  <div class="ns-hero-logo">&#9675; Signal Intelligence</div>
  <div class="ns-hero-title">NiftySniper <span style="color:{ACCENT}">AI Lab</span></div>
  <div class="ns-hero-sub">REAL-TIME &middot; MULTI-FACTOR &middot; AI-POWERED</div>
</div>
""", unsafe_allow_html=True)

# Input
sym_col, btn_col = st.columns([4, 1])
with sym_col:
    symbol_input = st.selectbox(
        "symbol", options=[""] + sorted(SYMBOLS.keys()),
        format_func=lambda x: "BTC  \u00b7  ETH  \u00b7  NIFTY  \u00b7  RELIANCE" if x == "" else x,
        label_visibility="collapsed")
with btn_col:
    go = st.button("ANALYSE", use_container_width=True)

api_key = st.secrets.get("ANTHROPIC_API_KEY", "") if hasattr(st, "secrets") else ""

if not symbol_input:
    st.markdown(f"""
    <div style="text-align:center;padding:4rem 0;color:{MUTED}">
      <div style="font-size:40px;margin-bottom:1rem">&#9678;</div>
      <div style="font-size:16px;font-weight:600;color:{TEXT};margin-bottom:.5rem">
        Type a symbol above &middot; Press Enter or click Analyse
      </div>
      <div style="font-size:13px">NIFTY 50 &middot; BANKNIFTY &middot; 60+ NSE stocks</div>
    </div>""", unsafe_allow_html=True)
    st.stop()

# Fetch
ticker = SYMBOLS.get(symbol_input, f"{symbol_input}.NS")
with st.spinner(f"Fetching {symbol_input}..."):
    df = fetch_data(ticker)

if df is None or len(df) < 30:
    st.error(f"Could not load data for **{symbol_input}**. Try another symbol.")
    st.stop()

sc  = compute_score(df)
r   = df.iloc[-1]
ctx = build_context(symbol_input, sc, df)

# ── 01 SIGNAL OUTPUT ─────────────────────────────────────────────────────────
st.markdown(f"""
<div class="ns-badge">
  <div class="ns-badge-label">Signal Output &middot; {symbol_input}</div>
  <div class="ns-badge-signal {sc['cls']}">{sc['tier']}</div>
  <div class="ns-badge-score">{sc['total']} / 13</div>
  <div class="ns-badge-time">{ist_now()}</div>
</div>
""", unsafe_allow_html=True)

# ── 02 SIGNAL COMPONENTS ─────────────────────────────────────────────────────
st.markdown('<div class="ns-card"><div class="ns-card-title">Signal Components</div>', unsafe_allow_html=True)
for lbl, s, mx, raw in [
    ("V &mdash; Volume",          sc['v'], 5, f"vol_ratio = {sc['vol_ratio']}x"),
    ("P &mdash; Momentum",        sc['p'], 3, f"chg = {sc['pct_chg']}%"),
    ("R &mdash; Range Position",  sc['r'], 2, f"range_pos = {sc['range_pos']}"),
    ("T &mdash; Trend Alignment", sc['t'], 3, f"ADX = {r['ADX']:.1f}"),
]:
    pct = int(s/mx*100) if mx else 0
    st.markdown(f"""
    <div class="ns-comp">
      <div class="ns-comp-lbl">{lbl}</div>
      <div class="ns-bar-wrap"><div class="ns-bar" style="width:{pct}%"></div></div>
      <div class="ns-comp-sc">{s}/{mx}</div>
      <div class="ns-comp-raw">{raw}</div>
    </div>""", unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# ── 03 MARKET STRUCTURE ───────────────────────────────────────────────────────
def ud(val, ref):
    return ("up","&#9650; ABOVE") if val>ref else ("down","&#9660; BELOW")

st.markdown('<div class="ns-card"><div class="ns-card-title">Market Structure</div>', unsafe_allow_html=True)
rows = [
    ("Close",    f"{r['Close']:.2f}",   "neu", ""),
    ("EMA 20",   f"{r['EMA20']:.2f}",   *ud(r['Close'],r['EMA20'])),
    ("EMA 50",   f"{r['EMA50']:.2f}",   *ud(r['Close'],r['EMA50'])),
    ("EMA 200",  f"{r['EMA200']:.2f}",  *ud(r['Close'],r['EMA200'])),
    ("VWAP",     f"{r['VWAP']:.2f}",    *ud(r['Close'],r['VWAP'])),
    ("BB Upper", f"{r['BB_upper']:.2f}", "neu",""),
    ("BB Lower", f"{r['BB_lower']:.2f}", "neu",""),
]
for lbl, val, cls, tag in rows:
    st.markdown(f"""
    <div class="ns-row">
      <div class="ns-lbl">{lbl}</div>
      <div class="ns-val {cls}">{val}&nbsp;<span style="font-size:10px;font-weight:400">{tag}</span></div>
    </div>""", unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# ── 04 TIMING QUALITY ────────────────────────────────────────────────────────
rsi_cls = "down" if r['RSI']>70 else "up" if r['RSI']<30 else "neu"
adx_tag = "Trending" if r['ADX']>25 else "Ranging"
stop    = r['Close'] - 1.5*r['ATR']

st.markdown(f"""
<div class="ns-card"><div class="ns-card-title">Timing Quality</div>
<div class="ns-row"><div class="ns-lbl">RSI 14</div>
  <div class="ns-val {rsi_cls}">{r['RSI']:.1f}</div></div>
<div class="ns-row"><div class="ns-lbl">ADX 14</div>
  <div class="ns-val neu">{r['ADX']:.1f} <span style="font-size:10px">({adx_tag})</span></div></div>
<div class="ns-row"><div class="ns-lbl">+DI / -DI</div>
  <div class="ns-val neu">{r['DI_pos']:.1f} / {r['DI_neg']:.1f}</div></div>
<div class="ns-row"><div class="ns-lbl">ATR 14</div>
  <div class="ns-val neu">{r['ATR']:.4f} <span style="font-size:10px">({r['ATR']/r['Close']*100:.2f}% of price)</span></div></div>
<div class="ns-row"><div class="ns-lbl">Suggested stop</div>
  <div class="ns-val down">{stop:.2f} <span style="font-size:10px">(1.5x ATR below close)</span></div></div>
</div>""", unsafe_allow_html=True)

# ── 05 KRONOS AI FORECAST ────────────────────────────────────────────────────
st.markdown('<div class="ns-card"><div class="ns-card-title">Kronos-Mini AI Forecast</div>', unsafe_allow_html=True)

kronos = None
if KRONOS_AVAILABLE:
    key_k = f"kronos_{ticker}"
    if key_k not in st.session_state:
        with st.spinner("Running Kronos..."):
            try:
                kronos = render_kronos_forecast(ticker, df)
                st.session_state[key_k] = kronos
            except Exception:
                st.session_state[key_k] = None
    else:
        kronos = st.session_state[key_k]

if not kronos:
    # AR1 mock
    pct_pred  = round(-sc['pct_chg']*0.6 + np.random.uniform(-2,2), 2)
    pred_cl   = round(r['Close']*(1+pct_pred/100), 2)
    bull_pct  = round(50 + sc['total']*2 + np.random.uniform(-5,5), 1)
    kronos = {
        "Direction":       "UP" if pct_pred>0 else "DOWN",
        "Predicted Change": f"{pct_pred:+.2f}%",
        "Predicted Close":  pred_cl,
        "Forecast Peak":    round(pred_cl*1.04, 2),
        "Forecast Trough":  round(pred_cl*0.96, 2),
        "Bull Candle %":    f"{bull_pct}%",
        "Candles Forecast": 20,
    }
    st.markdown(f'<div style="font-size:10px;color:{MUTED};margin-bottom:6px">AR1 mock — Kronos module not loaded</div>', unsafe_allow_html=True)

arrow  = "&#9650;" if kronos["Direction"] == "UP" else "&#9660;"
k_cls  = "up" if kronos["Direction"] == "UP" else "down"
for k, v in kronos.items():
    v_str = f"{arrow} {v}" if k == "Direction" else str(v)
    v_cls = k_cls if k == "Direction" else "neu"
    st.markdown(f"""
    <div class="ns-row">
      <div class="ns-lbl">{k}</div>
      <div class="ns-val {v_cls}">{v_str}</div>
    </div>""", unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# ── 06 AI AGENT COUNCIL ───────────────────────────────────────────────────────
st.markdown('<div class="ns-card"><div class="ns-card-title">AI Lab &mdash; Agent Debate</div>', unsafe_allow_html=True)

dkey = f"debate_{ticker}_{sc['total']}"
agent_texts = {}

if not api_key:
    st.markdown(f'<div style="color:{MUTED};font-size:13px;padding:.5rem 0">Add ANTHROPIC_API_KEY to Streamlit secrets to enable AI debate.</div>', unsafe_allow_html=True)
elif dkey in st.session_state:
    agent_texts = st.session_state[dkey]
    for ag in AGENTS:
        txt = agent_texts.get(ag["key"], "")
        pill = ""
        if ag["key"] == "CIO":
            u = txt.upper()
            if   "BUY"  in u: pill = '<span class="verdict v-buy">BUY</span>'
            elif "SELL" in u: pill = '<span class="verdict v-sell">SELL</span>'
            elif "HOLD" in u: pill = '<span class="verdict v-hold">HOLD</span>'
            else:              pill = '<span class="verdict v-wait">WAIT</span>'
        st.markdown(f"""
        <div class="ns-agent">
          <div class="ns-agent-name {ag['cls']}">{ag['label']}</div>
          <div class="ns-agent-text">{txt}</div>
          {pill}
        </div>""", unsafe_allow_html=True)
else:
    if st.button("Run AI Debate", use_container_width=True):
        slots = [st.empty() for _ in AGENTS]
        for ag, slot in zip(AGENTS, slots):
            agent_texts[ag["key"]] = stream_agent(ag, ctx, api_key, slot)
            time.sleep(0.2)
        st.session_state[dkey] = agent_texts
        st.rerun()

st.markdown('</div>', unsafe_allow_html=True)

# ── 07 EXPORT ────────────────────────────────────────────────────────────────
st.markdown('<div class="ns-card"><div class="ns-card-title">Export Report</div>', unsafe_allow_html=True)

k_data = kronos if isinstance(kronos, dict) else {}
label  = "Download PDF Report" if agent_texts else "Download Signal Report (no debate)"

try:
    pdf_bytes = generate_pdf(symbol_input, sc, df, agent_texts, k_data)
    fname = f"NiftySniper_{symbol_input}_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
    st.download_button(label=f"Download {fname}", data=pdf_bytes,
                       file_name=fname, mime="application/pdf",
                       use_container_width=True)
except Exception as e:
    st.error(f"PDF error: {e}")

st.markdown('</div>', unsafe_allow_html=True)

# Disclaimer
st.markdown(f"""
<div style="text-align:center;font-size:10px;color:{MUTED};
margin-top:2rem;padding-top:1rem;border-top:1px solid {BORDER}">
Data via Yahoo Finance / NSE. Signals are not financial advice.<br>
Past performance does not guarantee future results.
</div>""", unsafe_allow_html=True)
