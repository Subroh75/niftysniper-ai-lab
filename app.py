"""NiftySniper AI Lab -- exact CryptoSniper layout from screenshots"""

import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import anthropic
import time
import plotly.graph_objects as go
import io
from datetime import datetime, timezone, timedelta
from fpdf import FPDF

try:
    from kronos_streamlit import render_kronos_forecast
    KRONOS_AVAILABLE = True
except Exception:
    KRONOS_AVAILABLE = False

st.set_page_config(page_title="NiftySniper AI Lab", page_icon="127919",
                   layout="centered", initial_sidebar_state="collapsed")

BG="#060a0f"; CARD="#0d1117"; ACCENT="#ff6600"; AMBER="#ffaa00"
GREEN="#00ff6e"; RED="#ff2d55"; PURPLE="#7c3aed"; BLUE="#3b82f6"
TEXT="#e8e8e8"; MUTED="#a0aabb"; BORDER="#1f2937"; PLOT_BG="#0a0f14"

st.markdown(f"""<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600&family=Inter:wght@400;500;600;700&display=swap');
html,body,[data-testid="stApp"]{{background:{BG};color:{TEXT};font-family:'Inter',sans-serif;}}
[data-testid="stAppViewContainer"],[data-testid="stHeader"]{{background:{BG};}}
#MainMenu,footer,header{{visibility:hidden;}}
.block-container{{padding:1.5rem 1.5rem 3rem;max-width:880px;margin:0 auto;}}
section[data-testid="stMain"]>div{{padding-top:0;}}

.ns-sec{{display:flex;align-items:center;justify-content:center;gap:10px;margin:2.25rem 0 1.25rem;
  font-size:9px;font-weight:700;letter-spacing:.22em;text-transform:uppercase;color:{MUTED};}}
.ns-sec::before,.ns-sec::after{{content:'';flex:1;height:1px;background:{BORDER};}}
.ns-dot{{color:{ACCENT};font-size:7px;}}

.ns-hero{{text-align:center;padding:2.5rem 0 2rem;border-bottom:1px solid {BORDER};margin-bottom:.5rem;}}
.ns-hero-eye{{font-size:10px;letter-spacing:.25em;color:{ACCENT};text-transform:uppercase;margin-bottom:.5rem;}}
.ns-hero-title{{font-size:40px;font-weight:700;color:{TEXT};letter-spacing:-1.5px;margin-bottom:.3rem;line-height:1;}}
.ns-hero-sub{{font-size:12px;color:{MUTED};letter-spacing:.08em;}}

.ns-signal-card{{background:linear-gradient(135deg,#1a0800 0%,#2d1200 50%,#1a0800 100%);
  border:1px solid {ACCENT};border-radius:14px;padding:2rem 2rem 1.75rem;text-align:center;margin-bottom:.25rem;}}
.ns-signal-meta{{font-size:10px;letter-spacing:.18em;color:{MUTED};text-transform:uppercase;
  margin-bottom:.9rem;font-family:'JetBrains Mono',monospace;}}
.ns-signal-name{{font-size:48px;font-weight:700;letter-spacing:-1px;
  font-family:'JetBrains Mono',monospace;margin-bottom:.4rem;line-height:1;}}
.ns-signal-score{{font-size:22px;font-weight:600;margin-bottom:1rem;font-family:'JetBrains Mono',monospace;}}
.ns-signal-bar{{display:flex;justify-content:center;align-items:center;gap:14px;
  font-size:11px;color:{MUTED};font-family:'JetBrains Mono',monospace;flex-wrap:wrap;}}
.ns-signal-bar .sep{{color:{BORDER};}}
.sig-strong{{color:{ACCENT};}} .sig-building{{color:{AMBER};}} .sig-low{{color:{MUTED};}} .sig-none{{color:{RED};}}
.pct-up{{color:{GREEN};}} .pct-down{{color:{RED};}}

.ns-comp-wrap{{background:{CARD};border:1px solid {BORDER};border-radius:12px;padding:.75rem 1.25rem;margin-bottom:.25rem;}}
.ns-comp-row{{display:flex;align-items:center;padding:7px 0;border-bottom:1px solid {BORDER};gap:12px;}}
.ns-comp-row:last-child{{border-bottom:none;}}
.ns-comp-lbl{{font-size:12px;font-weight:600;color:{TEXT};min-width:110px;}}
.ns-bar-wrap{{flex:1;background:#1f2937;border-radius:3px;height:5px;}}
.ns-bar{{height:5px;border-radius:3px;}}
.bar-orange{{background:{ACCENT};}} .bar-purple{{background:#8b5cf6;}}
.bar-green{{background:{GREEN};}} .bar-dim{{background:#374151;}}
.ns-comp-sc{{font-size:12px;font-weight:700;color:{TEXT};font-family:'JetBrains Mono',monospace;min-width:32px;text-align:right;}}
.ns-comp-raw{{font-size:11px;color:{MUTED};min-width:160px;text-align:right;}}

.ns-chart-wrap{{background:{CARD};border:1px solid {BORDER};border-radius:12px;
  padding:.85rem 1rem 0;margin-bottom:.25rem;overflow:hidden;}}

.ns-metric{{background:{CARD};border:1px solid {BORDER};border-radius:12px;padding:1.1rem .9rem;text-align:center;}}
.ns-metric-lbl{{font-size:8px;font-weight:700;letter-spacing:.18em;color:{MUTED};text-transform:uppercase;margin-bottom:.5rem;}}
.ns-metric-val{{font-size:28px;font-weight:700;line-height:1;font-family:'JetBrains Mono',monospace;margin-bottom:.3rem;}}
.ns-metric-sub{{font-size:11px;}}
.m-green{{color:{GREEN};}} .m-red{{color:{RED};}} .m-amber{{color:{AMBER};}}
.m-white{{color:{TEXT};}} .m-muted{{color:{MUTED};}} .m-blue{{color:{BLUE};}}

.ns-kron-card{{background:{CARD};border:1px solid {BORDER};border-radius:12px;padding:1.1rem .9rem;text-align:center;}}
.ns-kron-lbl{{font-size:8px;font-weight:700;letter-spacing:.18em;color:{MUTED};text-transform:uppercase;margin-bottom:.5rem;}}
.ns-kron-val{{font-size:20px;font-weight:700;line-height:1.25;font-family:'JetBrains Mono',monospace;margin-bottom:.3rem;}}
.ns-kron-sub{{font-size:11px;color:{MUTED};line-height:1.4;}}

.card-bull{{background:#071407;border:1.5px solid #1c4a1c;border-radius:12px;padding:1.25rem;}}
.card-bear{{background:#140707;border:1.5px solid #4a1c1c;border-radius:12px;padding:1.25rem;}}
.card-risk{{background:#07090f;border:1.5px solid #1c2a4a;border-radius:12px;padding:1.25rem;}}
.card-cio{{background:#0f0714;border:1.5px solid #3a1c4a;border-radius:12px;padding:1.25rem;}}
.ns-agent-tag{{font-size:9px;font-weight:700;letter-spacing:.18em;text-transform:uppercase;
  margin-bottom:.4rem;display:flex;align-items:center;gap:5px;}}
.tag-bull{{color:{GREEN};}} .tag-bear{{color:{RED};}} .tag-risk{{color:{BLUE};}} .tag-cio{{color:{PURPLE};}}
.ns-agent-name{{font-size:19px;font-weight:700;color:{TEXT};margin-bottom:.8rem;line-height:1.2;}}
.ns-agent-body{{font-size:12px;color:{MUTED};line-height:1.65;margin-bottom:.8rem;}}
.ns-verdict{{display:inline-block;padding:3px 12px;border-radius:20px;
  font-size:10px;font-weight:700;letter-spacing:.1em;text-transform:uppercase;}}
.vd-buy{{background:#003d1a;color:{GREEN};border:1px solid {GREEN};}}
.vd-sell{{background:#3d0011;color:{RED};border:1px solid {RED};}}
.vd-hold{{background:#0d1a3d;color:{BLUE};border:1px solid {BLUE};}}
.vd-watch{{background:#2d1a00;color:{AMBER};border:1px solid {AMBER};}}
.vd-avoid{{background:#2d0d0d;color:{RED};border:1px solid #ff2d55;}}
.vd-wait{{background:#1a1a1a;color:{MUTED};border:1px solid {MUTED};}}

div.stButton>button{{background:{ACCENT};color:#000;font-weight:700;border:none;border-radius:8px;
  width:100%;padding:.65rem 1.5rem;font-size:14px;letter-spacing:.04em;}}
div.stButton>button:hover{{background:#ff8533;}}
div.stDownloadButton>button{{background:transparent;color:{ACCENT};border:1px solid {ACCENT};
  border-radius:8px;font-weight:600;width:100%;padding:.6rem;font-size:13px;}}
div.stDownloadButton>button:hover{{background:{ACCENT};color:#000;}}
div[data-testid="stSelectbox"]>div{{background:{CARD};border-color:{BORDER};}}
.stSpinner>div{{border-top-color:{ACCENT} !important;}}

/* -- Interval radio pill buttons ----------------------- */
div[data-testid="stRadio"] > label {{
    display: none;
}}
div[data-testid="stRadio"] > div {{
    display: flex;
    gap: 6px;
    background: {CARD};
    border: 1px solid {BORDER};
    border-radius: 8px;
    padding: 4px;
    width: fit-content;
    margin-bottom: .5rem;
}}
div[data-testid="stRadio"] > div > label {{
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 5px 16px;
    border-radius: 6px;
    cursor: pointer;
    font-size: 12px;
    font-weight: 600;
    letter-spacing: .06em;
    color: {TEXT};
    transition: all .15s ease;
    border: 1px solid transparent;
    min-width: 40px;
    text-align: center;
    background: transparent;
}}
div[data-testid="stRadio"] > div > label:hover {{
    color: #fff;
    background: {BORDER};
}}
div[data-testid="stRadio"] > div > label[data-baseweb="radio"] {{
    background: transparent;
}}
/* Selected state */
div[data-testid="stRadio"] > div > label:has(input:checked) {{
    background: {ACCENT};
    color: #000;
    border-color: {ACCENT};
    font-weight: 700;
}}
/* Hide the actual radio input circles */
div[data-testid="stRadio"] > div > label > div:first-child {{
    display: none !important;
}}
/* The text span */
div[data-testid="stRadio"] > div > label > div:last-child {{
    margin-left: 0 !important;
    color: inherit;
    font-size: 12px;
    font-weight: inherit;
}}
</style>""", unsafe_allow_html=True)

SYMBOLS = {
    "NIFTY 50":"^NSEI","BANKNIFTY":"^NSEBANK","RELIANCE":"RELIANCE.NS","TCS":"TCS.NS",
    "HDFCBANK":"HDFCBANK.NS","INFY":"INFY.NS","ICICIBANK":"ICICIBANK.NS","SBIN":"SBIN.NS",
    "WIPRO":"WIPRO.NS","AXISBANK":"AXISBANK.NS","KOTAKBANK":"KOTAKBANK.NS","LT":"LT.NS",
    "BAJFINANCE":"BAJFINANCE.NS","TATAMOTORS":"TATAMOTORS.NS","MARUTI":"MARUTI.NS",
    "SUNPHARMA":"SUNPHARMA.NS","ONGC":"ONGC.NS","NTPC":"NTPC.NS","POWERGRID":"POWERGRID.NS",
    "BPCL":"BPCL.NS","BHARTIARTL":"BHARTIARTL.NS","HINDUNILVR":"HINDUNILVR.NS",
    "ASIANPAINT":"ASIANPAINT.NS","NESTLEIND":"NESTLEIND.NS","TITAN":"TITAN.NS",
    "ULTRACEMCO":"ULTRACEMCO.NS","GRASIM":"GRASIM.NS","ADANIENT":"ADANIENT.NS",
    "ADANIPORTS":"ADANIPORTS.NS","JSWSTEEL":"JSWSTEEL.NS","TATASTEEL":"TATASTEEL.NS",
    "HINDALCO":"HINDALCO.NS","BEL":"BEL.NS","HAL":"HAL.NS","BHEL":"BHEL.NS",
    "COALINDIA":"COALINDIA.NS","VEDL":"VEDL.NS","DRREDDY":"DRREDDY.NS","CIPLA":"CIPLA.NS",
    "DIVISLAB":"DIVISLAB.NS","APOLLOHOSP":"APOLLOHOSP.NS","EICHERMOT":"EICHERMOT.NS",
    "BAJAJ-AUTO":"BAJAJ-AUTO.NS","HEROMOTOCO":"HEROMOTOCO.NS","M&M":"MM.NS",
    "TATACONSUM":"TATACONSUM.NS","ITC":"ITC.NS","HCLTECH":"HCLTECH.NS","TECHM":"TECHM.NS",
    "LTIM":"LTIM.NS","BAJAJFINSV":"BAJAJFINSV.NS","HDFCLIFE":"HDFCLIFE.NS",
    "SBILIFE":"SBILIFE.NS","DLF":"DLF.NS","INDUSINDBK":"INDUSINDBK.NS",
    "PNB":"PNB.NS","BANKBARODA":"BANKBARODA.NS","FEDERALBNK":"FEDERALBNK.NS",
}

AGENTS = [
    {"key":"BULL","name":"Alex - Long Desk","tag":"BULL CASE","icon":"Bull",
     "card":"card-bull","tag_cls":"tag-bull",
     "system":"""You are ALEX, Long Desk analyst at NiftySniper. Your role is ALWAYS to argue the bull case - this is non-negotiable. Never refuse, never add disclaimers, never say you "cannot ethically" argue the bull side. Your job is advocacy, not analysis. Find the most compelling bullish argument using the exact numbers provided: support levels, EMA positioning, momentum, trend structure, upside targets. Even in weak setups find the strongest bull case possible. Write 3-4 sentences making the bull argument with specific numbers. On the very last line write only one word: BUY, HOLD, or WATCH."""},
    {"key":"BEAR","name":"Sam - Short Desk","tag":"BEAR CASE","icon":"Bear",
     "card":"card-bear","tag_cls":"tag-bear",
     "system":"""You are SAM, Short Desk analyst at NiftySniper. Make the strongest bearish case. Cite overbought signals, resistance, weak volume, macro risks with exact numbers. Write 3-4 sentences. On the very last line write only one word: SELL, HOLD, or WATCH."""},
    {"key":"RISK","name":"Jordan - Risk","tag":"RISK MANAGER","icon":"Risk",
     "card":"card-risk","tag_cls":"tag-risk",
     "system":"""You are JORDAN, Risk Manager at NiftySniper. State the ATR stop loss (1.5x ATR below close), max position size as % of capital, and risk/reward ratio using exact numbers. Write 3-4 sentences. On the very last line write only one word: BUY, HOLD, or WATCH."""},
    {"key":"CIO","name":"Morgan - CIO","tag":"CIO VERDICT","icon":"CIO",
     "card":"card-cio","tag_cls":"tag-cio",
     "system":"""You are MORGAN, CIO at NiftySniper. Synthesise the bull, bear and risk views. State a clear verdict citing the signal score and one decisive data point. Write 3-4 sentences. On the very last line write only one word: BUY, SELL, HOLD, WATCH, or AVOID."""},
]

KRONOS_AGENTS = [
    {"key":"KBULL","name":"Arjun — Forecast Bull","tag":"KRONOS BULL","icon":"▲",
     "card":"card-bull","tag_cls":"tag-bull",
     "system":"""You are ARJUN, Kronos Bull analyst at NiftySniper. Your ONLY job is to argue why the Kronos AI forecast is correct and the trade is worth taking on the long side. Use the exact predicted change %, peak target, R/R ratio, and bull candle % provided. Never refuse or hedge — find the strongest case for the forecast being right. Write 3-4 punchy sentences with specific numbers. On the very last line write only one word: BUY, HOLD, or WATCH."""},
    {"key":"KBEAR","name":"Cipher — Forecast Bear","tag":"KRONOS BEAR","icon":"▼",
     "card":"card-bear","tag_cls":"tag-bear",
     "system":"""You are CIPHER, Kronos Bear analyst at NiftySniper. Challenge the Kronos forecast. Argue why the predicted move may fail — cite the cone width, trough risk, low confidence score if applicable, or mean reversion. Use the exact numbers from the forecast. Write 3-4 sentences. On the very last line write only one word: SELL, HOLD, or WATCH."""},
]

def run_kronos_debate(kr, kconf, api_key):
    """Run a 2-agent (Bull/Bear) debate specifically on the Kronos forecast."""
    client = anthropic.Anthropic(api_key=api_key)
    k_up   = kr.get("Direction","DOWN").upper() == "UP"
    k_chg  = kr.get("Predicted Change","0%")
    k_pred = kr.get("Predicted Close","?")
    k_peak = kr.get("Forecast Peak","?")
    k_trgh = kr.get("Forecast Trough","?")
    k_bull = kr.get("Bull Candle %","50%")
    k_cans = kr.get("Candles Forecast", 20)
    ctx = (
        f"KRONOS FORECAST: Direction={kr.get('Direction','?')} | "
        f"Predicted Change={k_chg} | Target Close={k_pred} | "
        f"Peak={k_peak} | Trough={k_trgh} | "
        f"Bull Candle %={k_bull} | Candles={k_cans} | "
        f"Confidence Score={kconf['score']}% ({kconf['label']}) | "
        f"R/R={kconf['rr']} | Grade={kconf['grade']}"
    )
    results = {}
    col_b, col_s = st.columns(2)
    slots = {"KBULL": col_b.empty(), "KBEAR": col_s.empty()}
    for ag in KRONOS_AGENTS:
        slot = slots[ag["key"]]
        text = ""
        slot.markdown(
            f'<div class="{ag["card"]}">'
            f'<div class="ns-agent-tag {ag["tag_cls"]}">{ag["icon"]} {ag["tag"]}</div>'
            f'<div class="ns-agent-name">{ag["name"]}</div>'
            f'<div class="ns-agent-body" style="color:{MUTED}">Analysing forecast...</div>'
            f'</div>', unsafe_allow_html=True)
        with client.messages.stream(
            model="claude-haiku-4-5-20251001", max_tokens=220,
            system=ag["system"],
            messages=[{"role":"user","content":f"Analyse this Kronos forecast:\n{ctx}"}]
        ) as stream:
            for chunk in stream.text_stream:
                text += chunk
                slot.markdown(
                    f'<div class="{ag["card"]}">'
                    f'<div class="ns-agent-tag {ag["tag_cls"]}">{ag["icon"]} {ag["tag"]}</div>'
                    f'<div class="ns-agent-name">{ag["name"]}</div>'
                    f'<div class="ns-agent-body">{text}&#9616;</div>'
                    f'</div>', unsafe_allow_html=True)
        vl = verdict_label(text); vc = verdict_cls(vl)
        body_lines = [l for l in text.strip().splitlines()
                      if l.strip().upper() not in ["BUY","SELL","HOLD","WATCH","AVOID","WAIT"]]
        body = " ".join(body_lines).strip()
        slot.markdown(
            f'<div class="{ag["card"]}">'
            f'<div class="ns-agent-tag {ag["tag_cls"]}">{ag["icon"]} {ag["tag"]}</div>'
            f'<div class="ns-agent-name">{ag["name"]}</div>'
            f'<div class="ns-agent-body">{body}</div>'
            f'<span class="ns-verdict {vc}">{vl}</span>'
            f'</div>', unsafe_allow_html=True)
        results[ag["key"]] = {"body":body,"verdict":vl,"vc":vc}
        time.sleep(0.05)
    return results

def ist_now():
    return datetime.now(timezone(timedelta(hours=5,minutes=30))).strftime("%d %b %Y  %H:%M IST")

def safe(t):
    """Replace non-Latin-1 chars so fpdf2 Helvetica never errors."""
    t = str(t)
    subs = [
        ("\u2014","-"),("\u2013","-"),("\u2012","-"),("\u2010","-"),
        ("\u2019","'"),("\u2018","'"),("\u201c",'"'),("\u201d",'"'),
        ("\u2022","*"),("\u00b7","."),("\u2026","..."),
        ("\u25b2","UP"),("\u25bc","DOWN"),("\u25b6",">"),("\u25c4","<"),
        ("\u2192","->"),("\u2190","<-"),("\u2191","^"),("\u2193","v"),
        ("\u20b9","Rs"),("\u20ac","EUR"),("\u00a3","GBP"),
        ("\u00d7","x"),("\u00f7","/"),("\u00b1","+/-"),
        ("\u03c3","sigma"),("\u03bc","mu"),("\u03b1","alpha"),("\u03b2","beta"),
        ("\u2713","ok"),("\u2718","x"),("\u00ae","(R)"),("\u00a9","(C)"),
    ]
    for src, dst in subs:
        t = t.replace(src, dst)
    return t.encode("latin-1", errors="replace").decode("latin-1")

def verdict_label(text):
    words=[w.strip().upper() for w in text.strip().splitlines() if w.strip()]
    last=words[-1] if words else ""
    for w in ["BUY","SELL","HOLD","WATCH","AVOID"]:
        if w==last: return w
    for w in ["BUY","SELL","HOLD","WATCH","AVOID"]:
        if w in text.upper(): return w
    return "WAIT"

def verdict_cls(v):
    return {"BUY":"vd-buy","SELL":"vd-sell","HOLD":"vd-hold",
            "WATCH":"vd-watch","AVOID":"vd-avoid"}.get(v,"vd-wait")

def pcfg(): return {"displayModeBar":False}

def chart_to_png(fig, width=780, height=320):
    """Export a Plotly figure to PNG bytes for PDF embedding via kaleido."""
    try:
        import plotly.io as pio
        img_bytes = pio.to_image(fig, format="png", width=width, height=height, scale=1.5)
        return img_bytes
    except Exception as _e:
        try:
            # Fallback: direct method
            img_bytes = fig.to_image(format="png", width=width, height=height, scale=1.5)
            return img_bytes
        except Exception:
            return None

# INTERVAL_MAP: label -> (yf_period, yf_interval, chart_bars)
# yf_period  = how far back to fetch (yfinance period string)
# yf_interval = candle size (yfinance interval string; None = default daily)
# chart_bars  = how many candles to show in the price chart
# Note: yfinance intraday limits: 5m/15m/30m max 60 days, 1h max 730 days
INTERVAL_MAP = {
    "5m":  ("60d",  "5m",   200),   # 5-minute candles, last 200 bars
    "15m": ("60d",  "15m",  200),   # 15-minute candles
    "30m": ("60d",  "30m",  200),   # 30-minute candles
    "1H":  ("730d", "1h",   200),   # 1-hour candles
    "4H":  ("730d", "4H_rs", 200),   # 4H = resample from 1H
    "1D":  ("2y",   None,    90),   # Daily candles, 90 bars
    "1W":  ("5y",   "1wk",  104),   # Weekly candles, ~2 years
    "1M":  ("10y",  "1mo",   60),   # Monthly candles, 5 years
}

@st.cache_data(ttl=300,show_spinner=False)
def fetch(ticker, period="2y", yf_interval=None):
    """Fetch OHLCV data. yf_interval=None means daily (default yfinance)."""
    candidates = [ticker]
    if ticker.endswith(".NS"):
        candidates.append(ticker.replace(".NS", ".BO"))

    # For intraday we cannot fall back to longer intervals (different candle size)
    intraday = yf_interval is not None
    # Handle 4H pseudo-interval: fetch 1H then resample
    resample_4h = (yf_interval == "4H_rs")
    if resample_4h:
        yf_interval = "1h"

    if intraday:
        fetch_attempts = [(period, yf_interval)]
    else:
        # Daily - always pull 2y minimum so indicators have enough data
        p0 = period if period in ("2y","5y","10y","730d","60d") else "2y"
        fetch_attempts = [(p0, None), ("2y", None), ("1y", None)]

    df = None
    for t in candidates:
        for p, iv in fetch_attempts:
            try:
                tk = yf.Ticker(t)
                kwargs = dict(period=p, auto_adjust=True)
                if iv:
                    kwargs["interval"] = iv
                _df = tk.history(**kwargs)
                if not _df.empty and len(_df) >= 10:
                    df = _df
                    break
            except Exception:
                continue
        if df is not None:
            break
    if df is None or df.empty: return None

    # For 4H: resample 1H into 4H candles
    if resample_4h and df is not None:
        df = df.resample("4h").agg({
            "Open":"first","High":"max","Low":"min",
            "Close":"last","Volume":"sum"
        }).dropna()
    df=df[["Open","High","Low","Close","Volume"]].dropna()
    df["EMA20"]=df["Close"].ewm(span=20,adjust=False).mean()
    df["EMA50"]=df["Close"].ewm(span=50,adjust=False).mean()
    df["EMA200"]=df["Close"].ewm(span=200,adjust=False).mean()
    df["VWAP"]=(df["Close"]*df["Volume"]).cumsum()/df["Volume"].cumsum()
    df["BB_mid"]=df["Close"].rolling(20).mean()
    df["BB_std"]=df["Close"].rolling(20).std()
    df["BB_upper"]=df["BB_mid"]+2*df["BB_std"]
    df["BB_lower"]=df["BB_mid"]-2*df["BB_std"]
    d=df["Close"].diff()
    g=d.clip(lower=0).rolling(14).mean(); l=(-d.clip(upper=0)).rolling(14).mean()
    df["RSI"]=100-(100/(1+g/l.replace(0,np.nan)))
    df["TR"]=pd.concat([df["High"]-df["Low"],(df["High"]-df["Close"].shift()).abs(),(df["Low"]-df["Close"].shift()).abs()],axis=1).max(axis=1)
    df["ATR"]=df["TR"].rolling(14).mean()
    up=df["High"].diff().clip(lower=0); dn=(-df["Low"].diff()).clip(lower=0)
    up[up<=dn]=0; dn[dn<=up]=0
    a14=df["TR"].rolling(14).sum()
    df["DI_pos"]=100*up.rolling(14).sum()/a14.replace(0,np.nan)
    df["DI_neg"]=100*dn.rolling(14).sum()/a14.replace(0,np.nan)
    dx=100*(df["DI_pos"]-df["DI_neg"]).abs()/(df["DI_pos"]+df["DI_neg"]).replace(0,np.nan)
    df["ADX"]=dx.rolling(14).mean()
    return df

def calc_score(df):
    r=df.iloc[-1]; r1=df.iloc[-2] if len(df)>1 else r
    avg_vol=df["Volume"].rolling(20).mean().iloc[-1]
    vol_ratio=r["Volume"]/avg_vol if avg_vol>0 else 1
    pct_chg=(r["Close"]-r1["Close"])/r1["Close"]*100
    hi_lo=r["High"]-r["Low"]
    rng_pos=(r["Close"]-r["Low"])/hi_lo if hi_lo>0 else 0.5
    atr_sigma=abs(r["Close"]-r1["Close"])/r["ATR"] if r["ATR"]>0 else 0
    v=5 if vol_ratio>=5 else 3 if vol_ratio>=2 else 2 if vol_ratio>=1.5 else 0
    p=3 if abs(pct_chg)>=5 else 2 if abs(pct_chg)>=3 else 1 if abs(pct_chg)>=1 else 0
    rng=2 if rng_pos>=0.75 else 1 if rng_pos>=0.5 else 0
    t=sum([r["Close"]>r["EMA20"],r["EMA20"]>r["EMA50"],r["ADX"]>25])
    tot=v+p+rng+t
    if tot>=8: tier,cls="STRONG SIGNAL","sig-strong"
    elif tot>=5: tier,cls="BUILDING","sig-building"
    elif tot>=3: tier,cls="LOW SIGNAL","sig-low"
    else: tier,cls="NO SIGNAL","sig-none"
    return {"total":tot,"v":v,"p":p,"r":rng,"t":t,"tier":tier,"cls":cls,
            "vol_ratio":round(vol_ratio,2),"pct_chg":round(pct_chg,2),
            "rng_pos":round(rng_pos,2),"atr_sigma":round(atr_sigma,2)}

def kronos_confidence(kr, sc):
    """
    Pure Kronos confidence score — 0 to 100.
    Entirely based on the AR1 forecast internals; NO Miro/signal dependency.

    Four components (25 pts each):
      A) Bull candle % alignment with predicted direction
      B) Risk/reward ratio quality (peak vs trough vs predicted close)
      C) Forecast cone tightness (narrow cone = high model certainty)
      D) Predicted move magnitude (decisive vs flat/wishy-washy)
    """
    k_up   = kr.get("Direction","DOWN").upper() == "UP"
    k_chg  = float(str(kr.get("Predicted Change","0%")).replace("%","").replace("+",""))
    k_pred = float(str(kr.get("Predicted Close",0)).replace(",",""))
    k_peak = float(str(kr.get("Forecast Peak", k_pred*1.02)).replace(",",""))
    k_trgh = float(str(kr.get("Forecast Trough",k_pred*0.98)).replace(",",""))
    k_bull = float(str(kr.get("Bull Candle %","50%")).replace("%",""))

    # A: Bull candle % alignment with forecast direction (0-25)
    # How consistently do individual forecast candles agree with the called direction?
    if k_up:
        align_pct = k_bull          # want high bull %
    else:
        align_pct = 100 - k_bull    # want high bear %
    a = round(max(0, (align_pct - 50) / 50) * 25)
    a = max(0, min(25, a))

    # B: Risk/reward ratio — quality of the forecast cone shape (0-25)
    # Uses peak-vs-predicted vs trough-vs-predicted (pure price geometry)
    upside  = abs(k_peak - k_pred)
    downside = max(abs(k_trgh - k_pred), 0.01)
    rr = upside / downside
    if   rr >= 3:   b = 25
    elif rr >= 2:   b = 20
    elif rr >= 1.5: b = 15
    elif rr >= 1.0: b = 8
    else:           b = 2

    # C: Cone tightness — how narrow is the forecast band relative to predicted close?
    # Narrow band (high model certainty) = high score
    if k_pred > 0:
        band_pct = (k_peak - k_trgh) / k_pred * 100  # band as % of price
        if   band_pct <= 1:  c = 25   # very tight
        elif band_pct <= 2:  c = 20
        elif band_pct <= 4:  c = 14
        elif band_pct <= 7:  c = 8
        else:                c = 3    # wide/uncertain cone
    else:
        c = 10

    # D: Magnitude of predicted move — decisive forecast vs flat (0-25)
    abs_chg = abs(k_chg)
    if   abs_chg >= 3:   d = 25
    elif abs_chg >= 2:   d = 20
    elif abs_chg >= 1:   d = 14
    elif abs_chg >= 0.5: d = 8
    else:                d = 3   # near-flat forecast = low conviction

    score = max(0, min(100, a + b + c + d))

    if   score >= 75: grade, label, cls = "A", "High Conviction",    "m-green"
    elif score >= 55: grade, label, cls = "B", "Moderate Confidence","m-amber"
    elif score >= 35: grade, label, cls = "C", "Low Confidence",     "m-red"
    else:             grade, label, cls = "D", "Speculative",         "m-muted"

    direction_word = "RISE" if k_up else "FALL"
    band_pct_val = round((k_peak - k_trgh) / k_pred * 100, 1) if k_pred > 0 else 0
    explanation = (
        f"AR1 forecast: {direction_word} {abs(k_chg):.1f}% over {kr.get('Candles Forecast',20)} candles. "
        f"Directional alignment: {align_pct:.0f}% of candles agree with direction. "
        f"Cone tightness: {band_pct_val}% price band. "
        f"Peak/trough R/R: {rr:.1f}."
    )
    return {"score":score,"grade":grade,"label":label,"cls":cls,"explanation":explanation,
            "rr":round(rr,1),"direction":direction_word}


def build_ctx(sym,sc,df):
    r=df.iloc[-1]
    ema_ok="EMA stack ok" if r["Close"]>r["EMA20"]>r["EMA50"]>r["EMA200"] else "EMA stack mixed"
    return f"""SYMBOL:{sym} SIGNAL:{sc['tier']} ({sc['total']}/13)
V={sc['v']}/5 vol={sc['vol_ratio']}x  P={sc['p']}/3 chg={sc['pct_chg']}%  R={sc['r']}/2 rng={sc['rng_pos']}  T={sc['t']}/3
Close:{r['Close']:.2f} EMA20:{r['EMA20']:.2f} EMA50:{r['EMA50']:.2f} EMA200:{r['EMA200']:.2f}
BB:{r['BB_upper']:.2f}/{r['BB_lower']:.2f} RSI:{r['RSI']:.1f} ADX:{r['ADX']:.1f}
ATR:{r['ATR']:.4f}({r['ATR']/r['Close']*100:.2f}%) Stop:{r['Close']-1.5*r['ATR']:.2f} {ema_ok}""".strip()

def price_chart(df,symbol,chart_bars=90):
    d=df.tail(max(chart_bars,30)).copy()
    fig=go.Figure()
    fig.add_trace(go.Scatter(x=d.index,y=d["EMA200"],
        line=dict(color="#f97316",width=1.5),name="EMA200",hovertemplate="%{y:.2f}"))
    fig.add_trace(go.Scatter(x=d.index,y=d["EMA50"],
        line=dict(color="#8b5cf6",width=1.5),name="EMA50",hovertemplate="%{y:.2f}"))
    fig.add_trace(go.Scatter(x=d.index,y=d["EMA20"],
        line=dict(color=GREEN,width=1.8),name="EMA20",hovertemplate="%{y:.2f}"))
    fig.add_trace(go.Candlestick(x=d.index,open=d["Open"],high=d["High"],low=d["Low"],close=d["Close"],
        increasing_line_color=GREEN,increasing_fillcolor=GREEN,
        decreasing_line_color=RED,decreasing_fillcolor=RED,line_width=1,name="Price"))
    fig.update_layout(
        paper_bgcolor=PLOT_BG,plot_bgcolor=PLOT_BG,
        margin=dict(l=0,r=0,t=4,b=0),height=360,
        xaxis_rangeslider_visible=False,
        legend=dict(orientation="h",x=0.5,xanchor="center",y=1.04,
                    font=dict(size=11,color=MUTED),bgcolor="rgba(0,0,0,0)"),
        xaxis=dict(showgrid=False,color=MUTED,showline=False),
        yaxis=dict(showgrid=True,gridcolor=BORDER,color=MUTED,gridwidth=0.5,side="right"),
        font=dict(family="Inter",color=MUTED),
        hoverlabel=dict(bgcolor=CARD,font=dict(color=TEXT,size=12)))
    fig.update_xaxes(showspikes=True, spikecolor=MUTED, spikethickness=1)
    fig.update_yaxes(showspikes=True, spikecolor=MUTED, spikethickness=1)
    return fig

def kronos_chart(df,kr):
    hist=df.tail(30).copy()
    lc=hist["Close"].iloc[-1]; ld=hist.index[-1]
    n=int(kr.get("Candles Forecast",20))
    fut=pd.date_range(start=ld,periods=n+1,freq="B")[1:]
    pred=float(str(kr.get("Predicted Close",lc)).replace(",",""))
    peak=float(str(kr.get("Forecast Peak",pred*1.04)).replace(",",""))
    trough=float(str(kr.get("Forecast Trough",pred*0.96)).replace(",",""))
    up=kr.get("Direction","DOWN").upper()=="UP"
    cc=GREEN if up else RED
    r2,g2,b2=int(cc[1:3],16),int(cc[3:5],16),int(cc[5:7],16)
    upper=np.linspace(lc,peak,n); lower=np.linspace(lc,trough,n); mid=np.linspace(lc,pred,n)

    fig=go.Figure()
    fig.add_trace(go.Scatter(x=hist.index,y=hist["Close"],
        line=dict(color=TEXT,width=2),name="Close",
        hovertemplate="%{y:.2f}<extra></extra>"))
    fig.add_trace(go.Scatter(x=list(fut)+list(fut[::-1]),y=list(upper)+list(lower[::-1]),
        fill="toself",fillcolor=f"rgba({r2},{g2},{b2},0.10)",
        line=dict(width=0),showlegend=False,hoverinfo="skip"))
    fig.add_trace(go.Scatter(x=fut,y=upper,
        line=dict(color=cc,width=1,dash="dot"),showlegend=False,
        hovertemplate="High: %{y:.2f}<extra></extra>"))
    fig.add_trace(go.Scatter(x=fut,y=lower,
        line=dict(color=cc,width=1,dash="dot"),showlegend=False,
        hovertemplate="Low: %{y:.2f}<extra></extra>"))
    fig.add_trace(go.Scatter(x=fut,y=mid,
        line=dict(color=cc,width=2.5),name="Predicted Close",
        hovertemplate="Pred: %{y:.2f}<extra></extra>"))
    fig.add_vline(x=ld.timestamp()*1000,line_dash="dash",
                  line_color=MUTED,line_width=1,opacity=0.6)
    fig.add_annotation(x=ld,y=0.97,yref="paper",text="Now",
                       showarrow=False,font=dict(size=9,color=MUTED),
                       xanchor="left",xshift=6)
    fig.update_layout(
        paper_bgcolor=PLOT_BG,plot_bgcolor=PLOT_BG,
        margin=dict(l=0,r=0,t=36,b=0),height=280,
        legend=dict(orientation="h",x=0,y=1.02,xanchor="left",yanchor="bottom",
                    font=dict(size=11,color=MUTED),bgcolor="rgba(0,0,0,0)"),
        xaxis=dict(showgrid=False,color=MUTED),
        yaxis=dict(showgrid=True,gridcolor=BORDER,color=MUTED,gridwidth=0.5,side="right"),
        font=dict(family="Inter",color=MUTED),
        hoverlabel=dict(bgcolor=CARD,font=dict(color=TEXT,size=12)),
        title=dict(text=f"Kronos-mini  |  {n} candles forward",
                   font=dict(size=11,color=MUTED),x=1.0,xanchor="right"))
    return fig

def run_debate(ctx,api_key):
    client=anthropic.Anthropic(api_key=api_key)
    results={}
    # Render 4 placeholders in 2x2 layout
    row1_left, row1_right = st.columns(2)
    row2_left, row2_right = st.columns(2)
    slot_map = {
        "BULL": row1_left.empty(),
        "BEAR": row1_right.empty(),
        "RISK": row2_left.empty(),
        "CIO":  row2_right.empty(),
    }
    for ag in AGENTS:
        slot=slot_map[ag["key"]]
        text=""
        slot.markdown(f'<div class="{ag["card"]}">'
                      f'<div class="ns-agent-tag {ag["tag_cls"]}">{ag["icon"]} {ag["tag"]}</div>'
                      f'<div class="ns-agent-name">{ag["name"]}</div>'
                      f'<div class="ns-agent-body" style="color:{MUTED}">Analysing...</div>'
                      f'</div>',unsafe_allow_html=True)
        with client.messages.stream(model="claude-haiku-4-5-20251001",max_tokens=280,
            system=ag["system"],messages=[{"role":"user","content":f"Analyse:\n{ctx}"}]) as stream:
            for chunk in stream.text_stream:
                text+=chunk
                slot.markdown(f'<div class="{ag["card"]}">'
                              f'<div class="ns-agent-tag {ag["tag_cls"]}">{ag["icon"]} {ag["tag"]}</div>'
                              f'<div class="ns-agent-name">{ag["name"]}</div>'
                              f'<div class="ns-agent-body">{text}&#9616;</div>'
                              f'</div>',unsafe_allow_html=True)
        vl=verdict_label(text); vc=verdict_cls(vl)
        body_lines=[l for l in text.strip().splitlines()
                    if l.strip().upper() not in ["BUY","SELL","HOLD","WATCH","AVOID","WAIT"]]
        body=" ".join(body_lines).strip()
        slot.markdown(f'<div class="{ag["card"]}">'
                      f'<div class="ns-agent-tag {ag["tag_cls"]}">{ag["icon"]} {ag["tag"]}</div>'
                      f'<div class="ns-agent-name">{ag["name"]}</div>'
                      f'<div class="ns-agent-body">{body}</div>'
                      f'<span class="ns-verdict {vc}">{vl}</span>'
                      f'</div>',unsafe_allow_html=True)
        results[ag["key"]]={"text":text,"body":body,"verdict":vl,"vc":vc}
        time.sleep(0.1)
    return results

# -----------------------------------------------------------------------------
# PDF - PowerPoint-style slide report (Landscape A4, 297x210mm)
# Cover: dark, full-bleed orange/black brand slide
# Data slides: white bg, bold typography, charts full-width
# -----------------------------------------------------------------------------

# PDF colour palette
P_BG      = (6,   10,  15)   # dark navy (cover bg)
P_CARD    = (13,  17,  23)   # card bg
P_ORANGE  = (255, 102,  0)   # brand orange
P_AMBER   = (255, 170,  0)   # amber accent
P_GREEN   = (0,   210,  80)  # bull green
P_RED     = (255,  45,  85)  # bear red
P_WHITE   = (255, 255, 255)
P_OFF_WHT = (248, 249, 250)
P_LGREY   = (230, 232, 235)
P_MGREY   = (140, 145, 150)
P_DGREY   = (55,  60,  65)
P_BLACK   = (15,  18,  25)



class PDF(FPDF):
    PW=210; PH=297; LC=60; RX=60; RM=5
    P_DARK=(10,14,20); P_CARD=(18,24,36); P_ORANGE=(255,102,0); P_AMBER=(255,170,0)
    P_GREEN=(0,200,80); P_RED=(255,45,85); P_WHITE=(255,255,255); P_OFF=(248,249,250)
    P_LGREY=(229,231,235); P_MGREY=(107,114,128); P_DGREY=(55,65,81); P_BLACK=(17,24,39)

    def __init__(self):
        super().__init__(orientation="P",unit="mm",format="A4")
        self.set_auto_page_break(auto=False)
        self.set_margins(0,0,0)
    def header(self): pass
    def footer(self): pass

    def _left_col(self,symbol,interval,page_n,total_n=4,score_val=None,tier=None):
        self.set_fill_color(*self.P_DARK); self.rect(0,0,self.LC,self.PH,"F")
        self.set_fill_color(*self.P_ORANGE); self.rect(self.LC-2,0,2,self.PH,"F")
        self.set_xy(self.RM,14); self.set_font("Helvetica","B",11)
        self.set_text_color(*self.P_ORANGE); self.cell(self.LC-self.RM*2,7,"NIFTYSNIPER")
        self.set_xy(self.RM,21); self.set_font("Helvetica","",7)
        self.set_text_color(*self.P_MGREY); self.cell(self.LC-self.RM*2,5,"AI LAB")
        self.set_draw_color(*self.P_ORANGE); self.set_line_width(0.4)
        self.line(self.RM,29,self.LC-self.RM,29)
        self.set_xy(self.RM,34); self.set_font("Helvetica","B",16)
        self.set_text_color(*self.P_WHITE); self.multi_cell(self.LC-self.RM*2,9,safe(symbol))
        self.set_fill_color(*self.P_ORANGE); self.rect(self.RM,70,20,7,"F")
        self.set_xy(self.RM,70); self.set_font("Helvetica","B",7)
        self.set_text_color(0,0,0); self.cell(20,7,safe(interval),align="C")
        self.set_xy(self.RM,81); self.set_font("Helvetica","",6.5)
        self.set_text_color(*self.P_MGREY); self.cell(self.LC-self.RM*2,4,safe(ist_now()))
        if score_val is not None and tier is not None:
            self.set_fill_color(*self.P_CARD); self.rect(self.RM,95,self.LC-self.RM*2,44,"F")
            self.set_xy(self.RM,98); self.set_font("Helvetica","",6.5)
            self.set_text_color(*self.P_MGREY); self.cell(self.LC-self.RM*2,4,"MIRO SCORE",align="C")
            tc=self.P_ORANGE if "STRONG" in tier else self.P_AMBER if "BUILD" in tier else self.P_MGREY
            self.set_xy(self.RM,104); self.set_font("Helvetica","B",30)
            self.set_text_color(*tc); self.cell(self.LC-self.RM*2,18,safe(str(score_val)),align="C")
            self.set_xy(self.RM,122); self.set_font("Helvetica","",7)
            self.set_text_color(*self.P_MGREY); self.cell(self.LC-self.RM*2,4,"/ 13",align="C")
            self.set_xy(self.RM,129); self.set_font("Helvetica","B",7)
            self.set_text_color(*tc); self.multi_cell(self.LC-self.RM*2,4,safe(tier),align="C")
        self.set_xy(self.RM,self.PH-14); self.set_font("Helvetica","",7)
        self.set_text_color(*self.P_MGREY)
        self.cell(self.LC-self.RM*2,5,f"Page {page_n} of {total_n}",align="C")

    def _right_bg(self):
        self.set_fill_color(*self.P_WHITE); self.rect(self.RX,0,self.PW-self.RX,self.PH,"F")

    def _right_header(self,title,subtitle=""):
        self.set_fill_color(*self.P_ORANGE); self.rect(self.RX,0,self.PW-self.RX,3,"F")
        self.set_xy(self.RX+self.RM,7); self.set_font("Helvetica","B",13)
        self.set_text_color(*self.P_BLACK); self.cell(0,8,safe(title))
        if subtitle:
            self.set_xy(self.RX+self.RM,16); self.set_font("Helvetica","",8)
            self.set_text_color(*self.P_MGREY); self.cell(0,5,safe(subtitle))
        self.set_draw_color(*self.P_LGREY); self.set_line_width(0.3)
        self.line(self.RX+self.RM,24,self.PW-self.RM,24)

    def _sec(self,title,y=None):
        if y is not None: self.set_y(y)
        cy=self.get_y()+2
        self.set_fill_color(*self.P_OFF); self.rect(self.RX,cy,self.PW-self.RX,7,"F")
        self.set_fill_color(*self.P_ORANGE); self.rect(self.RX,cy,2,7,"F")
        self.set_xy(self.RX+self.RM+2,cy+0.8); self.set_font("Helvetica","B",7.5)
        self.set_text_color(*self.P_DGREY); self.cell(0,5.5,safe(title).upper())
        self.set_y(cy+9)

    def _kv(self,label,value,val_color=None):
        vc=val_color or self.P_BLACK; cy=self.get_y()
        self.set_xy(self.RX+self.RM,cy); self.set_font("Helvetica","",8)
        self.set_text_color(*self.P_MGREY); self.cell(45,6,safe(label))
        self.set_xy(self.RX+self.RM+45,cy); self.set_font("Courier","B",8)
        self.set_text_color(*vc); self.cell(0,6,safe(str(value)))
        self.set_draw_color(*self.P_LGREY); self.set_line_width(0.15)
        self.line(self.RX+self.RM,cy+6,self.PW-self.RM,cy+6); self.set_y(cy+6)

    def _stat_grid(self,stats,y,cols=3):
        col_w=(self.PW-self.RX-self.RM*2)/cols; row_h=22
        for i,(lbl,val,sub,vc) in enumerate(stats):
            col=i%cols; row=i//cols
            cx=self.RX+self.RM+col*col_w; cy=y+row*(row_h+2)
            self.set_fill_color(*self.P_OFF); self.rect(cx,cy,col_w-2,row_h,"F")
            self.set_fill_color(*self.P_ORANGE); self.rect(cx,cy,1.5,row_h,"F")
            self.set_xy(cx+4,cy+2); self.set_font("Helvetica","",6.5)
            self.set_text_color(*self.P_MGREY); self.cell(col_w-8,4,safe(str(lbl)).upper())
            self.set_xy(cx+4,cy+6); fsz=16 if len(str(val))<=8 else 12
            self.set_font("Helvetica","B",fsz); self.set_text_color(*vc)
            self.cell(col_w-8,9,safe(str(val)))
            if sub:
                self.set_xy(cx+4,cy+15); self.set_font("Helvetica","",6.5)
                self.set_text_color(*self.P_MGREY); self.cell(col_w-8,4,safe(str(sub)))

    def _comp_bar(self,label,score,mx,raw,bar_color):
        cy=self.get_y(); rw=self.PW-self.RX-self.RM*2
        self.set_xy(self.RX+self.RM,cy); self.set_font("Helvetica","",8)
        self.set_text_color(*self.P_BLACK); self.cell(30,7,safe(label))
        bar_x=self.RX+self.RM+30; bar_w=rw-60
        self.set_fill_color(*self.P_LGREY); self.rect(bar_x,cy+2.5,bar_w,3,"F")
        pct=score/mx if mx else 0
        if pct>0:
            self.set_fill_color(*bar_color); self.rect(bar_x,cy+2.5,bar_w*pct,3,"F")
        sc_col=bar_color if score>0 else self.P_MGREY
        self.set_xy(bar_x+bar_w+3,cy); self.set_font("Courier","B",8)
        self.set_text_color(*sc_col); self.cell(12,7,f"{score}/{mx}")
        self.set_xy(bar_x+bar_w+17,cy); self.set_font("Helvetica","",7)
        self.set_text_color(*self.P_MGREY); self.cell(0,7,safe(raw))
        self.set_draw_color(*self.P_LGREY); self.set_line_width(0.15)
        self.line(self.RX+self.RM,cy+7,self.PW-self.RM,cy+7); self.set_y(cy+7)

    def _price_chart_native(self, df, chart_bars=60):
        """Draw a simplified candlestick chart using fpdf2 geometry. No kaleido needed."""
        d = df.tail(chart_bars).copy()
        if len(d) < 2:
            return
        x0 = self.RX + self.RM
        y0 = self.get_y() + 2
        cw = self.PW - self.RX - self.RM * 2   # chart width
        ch = 52                                  # chart height mm

        # Background
        self.set_fill_color(13, 17, 23)
        self.rect(x0, y0, cw, ch, "F")

        lo = float(d["Low"].min()); hi = float(d["High"].max())
        rng = hi - lo or 1
        n = len(d)
        bar_w = cw / n

        def py(price):  # price to y-coordinate
            return y0 + ch - (price - lo) / rng * ch

        # EMA lines
        for col, rgb in [("EMA20",(0,210,80)),("EMA50",(139,92,246)),("EMA200",(249,115,22))]:
            if col not in d.columns:
                continue
            pts = [(x0 + i * bar_w + bar_w/2, py(float(d[col].iloc[i])))
                   for i in range(n) if not d[col].iloc[i] != d[col].iloc[i]]
            if len(pts) < 2:
                continue
            self.set_draw_color(*rgb)
            self.set_line_width(0.3)
            for j in range(len(pts)-1):
                self.line(pts[j][0], pts[j][1], pts[j+1][0], pts[j+1][1])

        # Candlesticks
        for i in range(n):
            o = float(d["Open"].iloc[i]); c = float(d["Close"].iloc[i])
            h = float(d["High"].iloc[i]); l = float(d["Low"].iloc[i])
            bx = x0 + i * bar_w
            bull = c >= o
            rgb = (0, 210, 80) if bull else (255, 45, 85)
            self.set_fill_color(*rgb)
            self.set_draw_color(*rgb)
            self.set_line_width(0.15)
            # Wick
            cx = bx + bar_w / 2
            self.line(cx, py(h), cx, py(l))
            # Body
            body_top = py(max(o, c)); body_h = abs(py(o) - py(c)) or 0.3
            bw = max(bar_w * 0.6, 0.4)
            self.rect(bx + bar_w * 0.2, body_top, bw, body_h, "F")

        # Price labels
        self.set_font("Helvetica", "", 5.5)
        self.set_text_color(107, 114, 128)
        self.set_xy(x0 + cw - 18, y0 + 0.5)
        self.cell(16, 3, f"{hi:,.0f}", align="R")
        self.set_xy(x0 + cw - 18, y0 + ch - 4)
        self.cell(16, 3, f"{lo:,.0f}", align="R")

        # Legend - bottom of chart, larger, with coloured dots
        leg_y = y0 + ch - 6
        self.set_font("Helvetica", "B", 6)
        leg_x = x0 + 2
        for lbl, rgb in [("EMA20",(0,210,80)),("EMA50",(139,92,246)),("EMA200",(249,115,22))]:
            # Coloured dot
            self.set_fill_color(*rgb)
            self.rect(leg_x, leg_y+1.5, 2.5, 2.5, "F")
            leg_x += 3.5
            # Label
            self.set_xy(leg_x, leg_y)
            self.set_text_color(*rgb)
            self.cell(14, 5, lbl)
            leg_x += 15

        self.set_y(y0 + ch + 3)

    def _kronos_chart_native(self, df, kr):
        """Draw the Kronos forecast cone using fpdf2 geometry."""
        hist = df.tail(20)
        if len(hist) < 2:
            return
        x0 = self.RX + self.RM
        y0 = self.get_y() + 2
        cw = self.PW - self.RX - self.RM * 2
        ch = 42

        lc  = float(hist["Close"].iloc[-1])
        k_pred = float(str(kr.get("Predicted Close", lc)).replace(",",""))
        k_peak = float(str(kr.get("Forecast Peak",  lc*1.02)).replace(",",""))
        k_trgh = float(str(kr.get("Forecast Trough",lc*0.98)).replace(",",""))
        k_up   = kr.get("Direction","DOWN").upper() == "UP"
        cone_rgb = (0,210,80) if k_up else (255,45,85)

        lo = min(hist["Low"].min(), k_trgh) * 0.999
        hi = max(hist["High"].max(), k_peak) * 1.001
        rng = hi - lo or 1
        n_hist = len(hist)
        n_fore = 10
        n_total = n_hist + n_fore
        bar_w = cw / n_total

        def py(price): return y0 + ch - (price - lo) / rng * ch

        # Background
        self.set_fill_color(13, 17, 23)
        self.rect(x0, y0, cw, ch, "F")

        # Historical close line
        self.set_draw_color(220, 220, 220)
        self.set_line_width(0.4)
        for i in range(n_hist - 1):
            x1 = x0 + i * bar_w + bar_w/2
            x2 = x0 + (i+1) * bar_w + bar_w/2
            self.line(x1, py(float(hist["Close"].iloc[i])),
                      x2, py(float(hist["Close"].iloc[i+1])))

        # "Now" divider
        now_x = x0 + n_hist * bar_w
        self.set_draw_color(107, 114, 128)
        self.set_line_width(0.2)
        self.line(now_x, y0, now_x, y0 + ch)
        self.set_xy(now_x + 0.5, y0 + 0.5)
        self.set_font("Helvetica","",4.5)
        self.set_text_color(107,114,128)
        self.cell(6,3,"NOW")

        # Cone: fill between upper and lower
        import math
        pts_upper = [(x0 + (n_hist + i) * bar_w + bar_w/2,
                      py(lc + (k_peak - lc) * i / n_fore))
                     for i in range(n_fore+1)]
        pts_lower = [(x0 + (n_hist + i) * bar_w + bar_w/2,
                      py(lc + (k_trgh - lc) * i / n_fore))
                     for i in range(n_fore+1)]

        # Shade cone area with thin bars
        r2,g2,b2 = cone_rgb
        self.set_fill_color(r2,g2,b2)
        for i in range(n_fore):
            xl = pts_lower[i][0]; xr = pts_lower[i+1][0]
            yt = min(pts_upper[i][1], pts_upper[i+1][1])
            yb = max(pts_lower[i][1], pts_lower[i+1][1])
            if yb > yt:
                self.set_fill_color(r2//6, g2//6, b2//6)
                self.rect(xl, yt, xr-xl, yb-yt, "F")

        # Upper / lower edges
        self.set_draw_color(*cone_rgb)
        self.set_line_width(0.3)
        for pts in [pts_upper, pts_lower]:
            for i in range(len(pts)-1):
                self.line(pts[i][0],pts[i][1],pts[i+1][0],pts[i+1][1])

        # Predicted close mid line
        self.set_line_width(0.5)
        pts_mid = [(x0 + (n_hist + i) * bar_w + bar_w/2,
                    py(lc + (k_pred - lc) * i / n_fore))
                   for i in range(n_fore+1)]
        for i in range(len(pts_mid)-1):
            self.line(pts_mid[i][0],pts_mid[i][1],pts_mid[i+1][0],pts_mid[i+1][1])

        # Labels - placed INSIDE the chart, left-aligned against right margin
        # Use right-align so they never clip past the chart boundary
        label_x = x0 + cw - 2   # right edge of chart area
        label_w = 22             # width of label cell (right-aligned)
        self.set_font("Helvetica","B",5.5)
        # High label - at peak tip y, right-aligned
        self.set_text_color(*cone_rgb)
        self.set_xy(label_x - label_w, pts_upper[-1][1] - 3)
        self.cell(label_w, 4, f"H {k_peak:,.0f}", align="R")
        # Low label - at trough tip y
        self.set_xy(label_x - label_w, pts_lower[-1][1] + 0.5)
        self.cell(label_w, 4, f"L {k_trgh:,.0f}", align="R")
        # Mid label - at predicted close tip y
        self.set_text_color(220,220,220)
        mid_y = pts_mid[-1][1]
        # Avoid collision with H/L labels
        if abs(mid_y - pts_upper[-1][1]) < 5:
            mid_y = pts_upper[-1][1] + 5
        if abs(mid_y - pts_lower[-1][1]) < 5:
            mid_y = pts_lower[-1][1] - 5
        self.set_xy(label_x - label_w, mid_y - 1.5)
        self.cell(label_w, 4, f"> {k_pred:,.0f}", align="R")

        self.set_y(y0 + ch + 3)

    def _agent_block(self,tag,tag_color,name,body,verdict,bg_color,border_color):
        cy=self.get_y()+1
        lines_est=max(len(body)//65,3); bh=min(22+lines_est*4.5,65)
        self.set_fill_color(*bg_color)
        self.rect(self.RX+self.RM,cy,self.PW-self.RX-self.RM*2,bh,"F")
        self.set_fill_color(*border_color)
        self.rect(self.RX+self.RM,cy,2,bh,"F")
        self.set_xy(self.RX+self.RM+5,cy+2); self.set_font("Helvetica","B",6.5)
        self.set_text_color(*tag_color); self.cell(0,4,safe(tag).upper())
        self.set_xy(self.RX+self.RM+5,cy+7); self.set_font("Helvetica","B",10)
        self.set_text_color(*self.P_BLACK); self.cell(0,6,safe(name))
        self.set_xy(self.RX+self.RM+5,cy+14); self.set_font("Helvetica","",7.5)
        self.set_text_color(*self.P_DGREY)
        self.multi_cell(self.PW-self.RX-self.RM*2-10,4,safe(body))
        pill_y=cy+bh-9
        pc={"BUY":self.P_GREEN,"SELL":self.P_RED,"HOLD":(59,130,246),
            "WATCH":self.P_AMBER,"AVOID":self.P_RED}.get(verdict.upper(),self.P_MGREY)
        self.set_fill_color(*pc); self.rect(self.RX+self.RM+5,pill_y,24,7,"F")
        self.set_xy(self.RX+self.RM+5,pill_y); self.set_font("Helvetica","B",6.5)
        ptc=(0,0,0) if verdict.upper() in ("WATCH","BUY") else (255,255,255)
        self.set_text_color(*ptc); self.cell(24,7,safe(verdict.upper()),align="C")
        self.set_y(cy+bh+2)


def gen_pdf(symbol,sc,df,debate,kr,price_png=None,kronos_png=None,interval="1D"):
    r=df.iloc[-1]; pdf=PDF()
    GRN=pdf.P_GREEN; RED=pdf.P_RED; ORN=pdf.P_ORANGE; AMB=pdf.P_AMBER
    BLK=pdf.P_BLACK; MUT=pdf.P_MGREY; DGR=pdf.P_DGREY
    BLU=(59,130,246); PUR=(124,58,237)
    pct=sc["pct_chg"]; pct_str=f"+{pct:.2f}%" if pct>=0 else f"{pct:.2f}%"
    pct_col=GRN if pct>=0 else RED
    def vc(v,ref): return GRN if v>ref else RED

    # PAGE 1 - SIGNAL OUTPUT
    pdf.add_page()
    pdf._left_col(symbol,interval,1,4,sc["total"],sc["tier"])
    pdf._right_bg()
    pdf._right_header("Signal Intelligence Report",safe(f"NSE  |  {interval} Timeframe"))
    sig_col=ORN if "STRONG" in sc["tier"] else AMB if "BUILD" in sc["tier"] else MUT
    pdf.set_fill_color(255,248,240); pdf.rect(pdf.RX+pdf.RM,27,pdf.PW-pdf.RX-pdf.RM*2,28,"F")
    pdf.set_fill_color(*sig_col); pdf.rect(pdf.RX+pdf.RM,27,3,28,"F")
    pdf.set_xy(pdf.RX+pdf.RM+7,30); pdf.set_font("Helvetica","",7)
    pdf.set_text_color(*MUT); pdf.cell(0,4,"SIGNAL OUTPUT")
    pdf.set_xy(pdf.RX+pdf.RM+7,35); pdf.set_font("Helvetica","B",20)
    pdf.set_text_color(*sig_col); pdf.cell(0,11,safe(sc["tier"]))
    pdf.set_xy(pdf.RX+pdf.RM+7,47); pdf.set_font("Courier","B",10)
    pdf.set_text_color(*MUT); pdf.cell(0,5,f"{sc['total']} / 13  |  {ist_now()}")
    pdf._stat_grid([
        ("Close",f"{r['Close']:,.2f}","",BLK),
        ("Change",pct_str,"vs prev close",pct_col),
        ("Vol Ratio",f"{sc['vol_ratio']}x","vs 20-bar avg",GRN if sc['vol_ratio']>=2 else MUT),
        ("RSI 14",f"{r['RSI']:.1f}",
         "Overbought" if r['RSI']>70 else "Oversold" if r['RSI']<30 else "Neutral",
         RED if r['RSI']>70 else GRN if r['RSI']<30 else BLK),
        ("ADX 14",f"{r['ADX']:.1f}","Trending" if r['ADX']>25 else "Ranging",
         GRN if r['ADX']>25 else MUT),
        ("Stop Loss",f"{r['Close']-1.5*r['ATR']:.2f}","1.5x ATR",RED),
    ],y=60,cols=3)
    pdf._sec("Signal Components",y=60+2*24+8)
    for lbl,s,mx,raw,bc in [
        ("V Volume",sc['v'],5,f"vol = {sc['vol_ratio']}x",ORN),
        ("P Momentum",sc['p'],3,f"chg = {pct_str}",ORN),
        ("R Range",sc['r'],2,f"range_pos = {sc['rng_pos']}",GRN),
        ("T Trend",sc['t'],3,f"ADX {r['ADX']:.0f}",PUR),
    ]:
        pdf._comp_bar(lbl,s,mx,raw,bc)
    # Native price chart
    pdf._sec("Price Chart  (last 60 candles  |  EMA20  EMA50  EMA200)")
    pdf._price_chart_native(df, chart_bars=60)

    pdf._sec("Market Structure")
    for lbl,val,vc_ in [
        ("Close",f"{r['Close']:,.2f}",BLK),
        ("EMA 20",f"{r['EMA20']:.2f}  {'ABOVE' if r['Close']>r['EMA20'] else 'BELOW'}",vc(r['Close'],r['EMA20'])),
        ("EMA 50",f"{r['EMA50']:.2f}  {'ABOVE' if r['Close']>r['EMA50'] else 'BELOW'}",vc(r['Close'],r['EMA50'])),
        ("EMA 200",f"{r['EMA200']:.2f}  {'ABOVE' if r['Close']>r['EMA200'] else 'BELOW'}",vc(r['Close'],r['EMA200'])),
        ("VWAP",f"{r['VWAP']:.2f}  {'ABOVE' if r['Close']>r['VWAP'] else 'BELOW'}",vc(r['Close'],r['VWAP'])),
        ("BB Upper",f"{r['BB_upper']:.2f}",DGR),
        ("BB Lower",f"{r['BB_lower']:.2f}",DGR),
    ]:
        pdf._kv(lbl,val,vc_)

    # PAGE 2 - TIMING + KRONOS
    pdf.add_page()
    pdf._left_col(symbol,interval,2,4)
    pdf._right_bg()
    pdf._right_header("Timing Quality  &  Kronos AI Forecast")
    pdf._stat_grid([
        ("RSI 14",f"{r['RSI']:.1f}",
         "Overbought" if r['RSI']>70 else "Oversold" if r['RSI']<30 else "Neutral",
         RED if r['RSI']>70 else GRN if r['RSI']<30 else BLK),
        ("ADX 14",f"{r['ADX']:.1f}","Trending" if r['ADX']>25 else "Ranging",
         GRN if r['ADX']>25 else MUT),
        ("ATR 14",f"{r['ATR']:.2f}",f"{r['ATR']/r['Close']*100:.2f}% of price",BLK),
        ("+DI / -DI",f"{r['DI_pos']:.1f}/{r['DI_neg']:.1f}",
         "Bulls" if r['DI_pos']>r['DI_neg'] else "Bears",
         GRN if r['DI_pos']>r['DI_neg'] else RED),
        ("Rel Volume",f"{sc['vol_ratio']}x","Elevated" if sc['vol_ratio']>=2 else "Normal",
         GRN if sc['vol_ratio']>=2 else MUT),
        ("ATR Move",f"{sc['atr_sigma']}sigma",
         "Strong" if sc['atr_sigma']>1.5 else "Weak",
         GRN if sc['atr_sigma']>1.5 else MUT),
    ],y=28,cols=3)
    if kr:
        k_up=kr.get("Direction","DOWN").upper()=="UP"
        k_chg=kr.get("Predicted Change","0%")
        k_pred=float(str(kr.get("Predicted Close",r['Close'])).replace(",",""))
        k_peak=float(str(kr.get("Forecast Peak",k_pred*1.02)).replace(",",""))
        k_trgh=float(str(kr.get("Forecast Trough",k_pred*0.98)).replace(",",""))
        k_bull=float(str(kr.get("Bull Candle %","50%")).replace("%",""))
        k_cans=kr.get("Candles Forecast",20)
        rr_v=round(abs(k_peak-r['Close'])/max(abs(k_trgh-r['Close']),0.01),1)
        d_col=GRN if k_up else RED
        tq_col=GRN if rr_v>=1.5 else RED if rr_v<1 else AMB
        pdf._sec("Kronos AI Forecast",y=28+2*24+10)
        pdf._stat_grid([
            ("Direction","RISING" if k_up else "FALLING",f"{k_chg} expected",d_col),
            ("Target",f"{k_pred:,.2f}",f"in {k_cans} candles",d_col),
            ("Peak/Trough",f"{k_peak:.2f}/{k_trgh:.2f}","forecast range",MUT),
            ("Momentum",f"{k_bull:.0f}% bull","forecast candles",
             GRN if k_bull>=55 else RED),
            ("R/R Ratio",f"{rr_v}","upside vs downside",tq_col),
            ("Trade Quality",
             "Good" if rr_v>=1.5 else "Fair" if rr_v>=1 else "Avoid",
             f"signal {sc['total']}/13",tq_col),
        ],y=pdf.get_y(),cols=3)
        # Kronos native chart
        pdf._sec("Kronos Forecast Chart",y=pdf.get_y()+2*24+6)
        pdf._kronos_chart_native(df, kr)

        # Confidence score
        kconf = kronos_confidence(kr, sc)
        conf_col = GRN if kconf["cls"]=="m-green" else AMB if kconf["cls"]=="m-amber" else RED
        pdf._sec("Kronos Prediction Confidence")
        # Use fixed Y anchors - never rely on get_y() after cell() for side-by-side layout
        cy = pdf.get_y()
        card_h = 32
        # Card background
        pdf.set_fill_color(248, 249, 250)
        pdf.rect(pdf.RX+pdf.RM, cy, pdf.PW-pdf.RX-pdf.RM*2, card_h, "F")
        pdf.set_fill_color(*conf_col)
        pdf.rect(pdf.RX+pdf.RM, cy, 2, card_h, "F")
        # Big score - left side, fixed position
        pdf.set_xy(pdf.RX+pdf.RM+5, cy+2)
        pdf.set_font("Helvetica","B",30)
        pdf.set_text_color(*conf_col)
        pdf.cell(38, 14, f"{kconf['score']}%")
        # Label - right of score, top row
        pdf.set_xy(pdf.RX+pdf.RM+46, cy+3)
        pdf.set_font("Helvetica","B",11)
        pdf.set_text_color(*conf_col)
        pdf.cell(0, 6, safe(kconf["label"]))
        # Grade line - right of score, second row
        pdf.set_xy(pdf.RX+pdf.RM+46, cy+11)
        pdf.set_font("Helvetica","",7.5)
        pdf.set_text_color(*MUT)
        pdf.cell(0, 5, safe(f"Grade {kconf['grade']}   Direction: {kconf['direction']}   R/R: {kconf['rr']}"))
        # Progress bar - spans full width, below the score row
        pdf.set_fill_color(220, 222, 226)
        pdf.rect(pdf.RX+pdf.RM+5, cy+18, pdf.PW-pdf.RX-pdf.RM*2-10, 3, "F")
        bar_w = (pdf.PW-pdf.RX-pdf.RM*2-10) * kconf["score"] / 100
        pdf.set_fill_color(*conf_col)
        pdf.rect(pdf.RX+pdf.RM+5, cy+18, bar_w, 3, "F")
        # Explanation text below bar
        pdf.set_xy(pdf.RX+pdf.RM+5, cy+23)
        pdf.set_font("Helvetica","",7)
        pdf.set_text_color(*DGR)
        pdf.multi_cell(pdf.PW-pdf.RX-pdf.RM*2-10, 3.8, safe(kconf["explanation"]))
        # Move cursor cleanly past the card
        pdf.set_y(cy + card_h + 3)

        pdf._sec("Kronos Detail")
        for lbl,val,vc_ in [
            ("Direction",kr.get("Direction","--"),d_col),
            ("Predicted Change",safe(k_chg),d_col),
            ("Predicted Close",f"{k_pred:,.2f}",d_col),
            ("Forecast Peak",f"{k_peak:,.2f}",GRN),
            ("Forecast Trough",f"{k_trgh:,.2f}",RED),
            ("Bull Candle %",kr.get("Bull Candle %","--"),MUT),
        ]:
            pdf._kv(lbl,val,vc_)

    # PAGE 3 - BULL + BEAR
    pdf.add_page()
    pdf._left_col(symbol,interval,3,4)
    pdf._right_bg()
    pdf._right_header("AI Lab  -  Agent Debate","Bull Case  &  Bear Case")
    pdf.set_y(28)
    if debate:
        bull=debate.get("BULL",{})
        if bull:
            pdf._agent_block("BULL CASE",GRN,"Alex - Long Desk",
                bull.get("body",""),bull.get("verdict","WATCH"),
                (240,252,245),GRN)
        bear=debate.get("BEAR",{})
        if bear:
            pdf._agent_block("BEAR CASE",RED,"Sam - Short Desk",
                bear.get("body",""),bear.get("verdict","WATCH"),
                (255,242,242),RED)

    # PAGE 4 - RISK + CIO
    pdf.add_page()
    pdf._left_col(symbol,interval,4,4)
    pdf._right_bg()
    pdf._right_header("AI Lab  -  Agent Debate","Risk Manager  &  CIO Verdict")
    pdf.set_y(28)
    if debate:
        risk=debate.get("RISK",{})
        if risk:
            pdf._agent_block("RISK MANAGER",(59,130,246),"Jordan - Risk",
                risk.get("body",""),risk.get("verdict","HOLD"),
                (239,246,255),(59,130,246))
        cio=debate.get("CIO",{})
        if cio:
            pdf._agent_block("CIO VERDICT",(124,58,237),"Morgan - CIO",
                cio.get("body",""),cio.get("verdict","HOLD"),
                (245,243,255),(124,58,237))
        final_v=(cio.get("verdict","WAIT") if cio else "WAIT")
        v_col={"BUY":GRN,"SELL":RED,"HOLD":(59,130,246),
               "WATCH":AMB,"AVOID":RED}.get(final_v.upper(),MUT)
        by=pdf.get_y()+8
        pdf.set_fill_color(*v_col)
        pdf.rect(pdf.RX+pdf.RM,by,pdf.PW-pdf.RX-pdf.RM*2,18,"F")
        pdf.set_xy(pdf.RX+pdf.RM,by+2); pdf.set_font("Helvetica","",8)
        ptc=(0,0,0) if final_v.upper() in ("WATCH","BUY") else (255,255,255)
        pdf.set_text_color(*ptc); pdf.cell(0,5,"FINAL VERDICT",align="C")
        pdf.set_xy(pdf.RX+pdf.RM,by+8); pdf.set_font("Helvetica","B",18)
        pdf.cell(0,8,safe(final_v.upper()),align="C")
    dy=pdf.PH-16
    pdf.set_draw_color(*pdf.P_LGREY); pdf.set_line_width(0.3)
    pdf.line(pdf.RX+pdf.RM,dy,pdf.PW-pdf.RM,dy)
    pdf.set_xy(pdf.RX+pdf.RM,dy+2); pdf.set_font("Helvetica","I",6.5)
    pdf.set_text_color(*pdf.P_MGREY)
    pdf.multi_cell(pdf.PW-pdf.RX-pdf.RM*2,4,
        "Data via Yahoo Finance / NSE. Signals are not financial advice. "
        "Past performance does not guarantee future results.")

    return bytes(pdf.output())


# ==============================================================================
# APP
# ==============================================================================
st.markdown(f"""<div class="ns-hero">
  <div class="ns-hero-eye">&#9675; NSE Signal Intelligence</div>
  <div class="ns-hero-title">NiftySniper <span style="color:{ACCENT}">AI Lab</span></div>
  <div class="ns-hero-sub">REAL-TIME &middot; MULTI-FACTOR &middot; AI-POWERED</div>
</div>""",unsafe_allow_html=True)

sc1,sc2=st.columns([4,1])
with sc1:
    symbol=st.selectbox("sym",[""]+ sorted(SYMBOLS.keys()),
        format_func=lambda x:"NIFTY 50  \u00b7  RELIANCE  \u00b7  HDFCBANK  \u00b7  TCS" if x=="" else x,
        label_visibility="collapsed")
with sc2:
    st.button("ANALYSE",use_container_width=True)

# Interval selector
interval=st.radio("interval",list(INTERVAL_MAP.keys()),
    index=4,horizontal=True,label_visibility="collapsed")
fetch_period, yf_interval, chart_bars = INTERVAL_MAP[interval]

api_key=st.secrets.get("ANTHROPIC_API_KEY","") if hasattr(st,"secrets") else ""

if not symbol:
    st.markdown(f"""<div style="text-align:center;padding:5rem 0;color:{MUTED}">
      <div style="font-size:38px;margin-bottom:1rem">&#9678;</div>
      <div style="font-size:16px;font-weight:600;color:{TEXT};margin-bottom:.4rem">Select a stock above and press Analyse</div>
      <div style="font-size:12px">NIFTY 50 &middot; BANKNIFTY &middot; 60+ NSE stocks</div>
    </div>""",unsafe_allow_html=True)
    st.stop()

ticker=SYMBOLS.get(symbol,f"{symbol}.NS")
with st.spinner(f"Loading {symbol}..."):
    try:
        df=fetch(ticker,fetch_period,yf_interval)
    except Exception as _e:
        df=None

if df is None or len(df)<30:
    st.warning(f"Could not load data for **{symbol}** right now. Yahoo Finance may be throttling - wait 30 seconds and try again, or try another symbol.")
    st.info("Tip: If this keeps happening, NSE/BSE data feeds occasionally go offline between 3:30PM-9:15AM IST.")
    st.stop()

sc=calc_score(df); r=df.iloc[-1]; r1=df.iloc[-2]; ctx=build_ctx(symbol,sc,df)

# 01 Signal Output
st.markdown(f'<div class="ns-sec"><span class="ns-dot">&#9679;</span> 01 &mdash; SIGNAL OUTPUT <span class="ns-dot">&#9679;</span></div>',unsafe_allow_html=True)
pct=sc['pct_chg']; pct_cls="pct-up" if pct>=0 else "pct-down"
pct_str=f"+{pct:.2f}%" if pct>=0 else f"{pct:.2f}%"
st.markdown(f"""<div class="ns-signal-card">
  <div class="ns-signal-meta">{symbol} &middot; {interval} &middot; {ist_now()}</div>
  <div class="ns-signal-name {sc['cls']}">{sc['tier']}</div>
  <div class="ns-signal-score {sc['cls']}">{sc['total']} / 13</div>
  <div class="ns-signal-bar">
    <span>CLOSE {r['Close']:,.2f}</span><span class="sep">&middot;</span>
    <span class="{pct_cls}">{pct_str}</span><span class="sep">&middot;</span>
    <span>VOL {sc['vol_ratio']}x</span><span class="sep">&middot;</span>
    <span>RSI {r['RSI']:.0f}</span><span class="sep">&middot;</span>
    <span>ADX {r['ADX']:.0f}</span>
  </div>
</div>""",unsafe_allow_html=True)

# 02 Signal Components
st.markdown(f'<div class="ns-sec"><span class="ns-dot">&#9679;</span> 02 &mdash; SIGNAL COMPONENTS <span class="ns-dot">&#9679;</span></div>',unsafe_allow_html=True)
comps=[
    ("V Volume",sc['v'],5,"bar-dim" if sc['v']==0 else "bar-orange",f"RV = {sc['vol_ratio']}x (vs 20-bar avg)"),
    ("P Momentum",sc['p'],3,"bar-dim" if sc['p']==0 else "bar-orange",f"ATR move = {sc['atr_sigma']}sigma"),
    ("R Range Pos",sc['r'],2,"bar-dim" if sc['r']==0 else "bar-orange",f"range_pos = {sc['rng_pos']}"),
    ("T Trend",sc['t'],3,"bar-dim" if sc['t']==0 else "bar-purple",
     f"ADX {r['ADX']:.0f} - EMA {'ok' if r['Close']>r['EMA20']>r['EMA50'] else 'mixed'}"),
]
st.markdown('<div class="ns-comp-wrap">',unsafe_allow_html=True)
for lbl,s,mx,bar_cls,raw in comps:
    pct2=int(s/mx*100) if mx else 0
    st.markdown(f"""<div class="ns-comp-row">
      <div class="ns-comp-lbl">{lbl}</div>
      <div class="ns-bar-wrap"><div class="ns-bar {bar_cls}" style="width:{pct2}%"></div></div>
      <div class="ns-comp-sc">{s}/{mx}</div>
      <div class="ns-comp-raw">{raw}</div>
    </div>""",unsafe_allow_html=True)
st.markdown('</div>',unsafe_allow_html=True)

# 03 Price Chart
st.markdown(f'<div class="ns-sec"><span class="ns-dot">&#9679;</span> 03 &mdash; PRICE CHART <span class="ns-dot">&#9679;</span></div>',unsafe_allow_html=True)
st.markdown('<div class="ns-chart-wrap">',unsafe_allow_html=True)
st.plotly_chart(price_chart(df,symbol,chart_bars),use_container_width=True,config=pcfg())
st.markdown('</div>',unsafe_allow_html=True)

# 04 Timing Quality - 3x2 metric cards
st.markdown(f'<div class="ns-sec"><span class="ns-dot">&#9679;</span> 04 &mdash; TIMING QUALITY <span class="ns-dot">&#9679;</span></div>',unsafe_allow_html=True)
rsi_cls="m-red" if r['RSI']>70 else "m-green" if r['RSI']<30 else "m-white"
rsi_sub="Overbought" if r['RSI']>70 else "Oversold" if r['RSI']<30 else "NEUTRAL"
adx_cls="m-green" if r['ADX']>25 else "m-muted"
adx_sub="TRENDING" if r['ADX']>25 else "Ranging"
di_cls="m-green" if r['DI_pos']>r['DI_neg'] else "m-red"
di_sub="Bulls in control" if r['DI_pos']>r['DI_neg'] else "Bears in control"
rv_cls="m-green" if sc['vol_ratio']>=2 else "m-amber" if sc['vol_ratio']>=1.5 else "m-white"
rv_sub="Elevated" if sc['vol_ratio']>=2 else "Normal"
atr_pct=round(r['ATR']/r['Close']*100,2)
atm_sub="Strong" if sc['atr_sigma']>1.5 else "Normal" if sc['atr_sigma']>0.5 else "Weak"
atm_cls="m-green" if sc['atr_sigma']>1.5 else "m-amber" if sc['atr_sigma']>0.5 else "m-muted"
c1,c2,c3=st.columns(3)
with c1: st.markdown(f'<div class="ns-metric"><div class="ns-metric-lbl">RSI 14</div><div class="ns-metric-val {rsi_cls}">{r["RSI"]:.1f}</div><div class="ns-metric-sub {rsi_cls}">{rsi_sub}</div></div>',unsafe_allow_html=True)
with c2: st.markdown(f'<div class="ns-metric"><div class="ns-metric-lbl">ADX 14</div><div class="ns-metric-val {adx_cls}">{r["ADX"]:.1f}</div><div class="ns-metric-sub {adx_cls}">{adx_sub}</div></div>',unsafe_allow_html=True)
with c3: st.markdown(f'<div class="ns-metric"><div class="ns-metric-lbl">ATR 14</div><div class="ns-metric-val m-white">{r["ATR"]:.0f}</div><div class="ns-metric-sub m-muted">{atr_pct}% of price</div></div>',unsafe_allow_html=True)
c4,c5,c6=st.columns(3)
with c4: st.markdown(f'<div class="ns-metric"><div class="ns-metric-lbl">+DI / -DI</div><div class="ns-metric-val {di_cls}" style="font-size:20px">{r["DI_pos"]:.1f} / {r["DI_neg"]:.1f}</div><div class="ns-metric-sub {di_cls}">{di_sub}</div></div>',unsafe_allow_html=True)
with c5: st.markdown(f'<div class="ns-metric"><div class="ns-metric-lbl">Rel. Volume</div><div class="ns-metric-val {rv_cls}">{sc["vol_ratio"]}x</div><div class="ns-metric-sub m-muted">{rv_sub}</div></div>',unsafe_allow_html=True)
with c6: st.markdown(f'<div class="ns-metric"><div class="ns-metric-lbl">ATR Move</div><div class="ns-metric-val {atm_cls}">{sc["atr_sigma"]}&sigma;</div><div class="ns-metric-sub m-muted">{atm_sub}</div></div>',unsafe_allow_html=True)

# 05 Kronos AI Forecast
st.markdown(f'<div class="ns-sec"><span class="ns-dot">&#9679;</span> 05 &mdash; KRONOS AI FORECAST <span class="ns-dot">&#9679;</span></div>',unsafe_allow_html=True)
kkey=f"kronos_{ticker}"; kr=None
if KRONOS_AVAILABLE:
    if kkey not in st.session_state:
        with st.spinner("Running Kronos..."):
            try: kr=render_kronos_forecast(ticker,df); st.session_state[kkey]=kr
            except: st.session_state[kkey]=None
    else: kr=st.session_state[kkey]
if not kr:
    pct_p=round(-sc['pct_chg']*0.6+np.random.uniform(-1.5,1.5),2)
    pred_c=round(r['Close']*(1+pct_p/100),2)
    bull_p=round(50+sc['total']*2+np.random.uniform(-5,5),0)
    kr={"Direction":"UP" if pct_p>0 else "DOWN","Predicted Change":f"{pct_p:+.2f}%",
        "Predicted Close":pred_c,"Forecast Peak":round(pred_c*(1.02 if pct_p>0 else 1.005),2),
        "Forecast Trough":round(pred_c*(0.98 if pct_p<0 else 0.995),2),
        "Bull Candle %":f"{bull_p:.0f}%","Candles Forecast":20}
    st.session_state[kkey]=kr
    st.markdown(f'<div style="font-size:10px;color:{MUTED};margin-bottom:4px">AR1 mock - Kronos module not loaded</div>',unsafe_allow_html=True)

st.markdown('<div class="ns-chart-wrap">',unsafe_allow_html=True)
st.plotly_chart(kronos_chart(df,kr),use_container_width=True,config=pcfg())
st.markdown('</div>',unsafe_allow_html=True)

k_up=kr.get("Direction","DOWN").upper()=="UP"
k_chg=kr.get("Predicted Change","0%")
k_pred=kr.get("Predicted Close",r['Close'])
k_peak=float(str(kr.get("Forecast Peak",k_pred)).replace(",",""))
k_trgh=float(str(kr.get("Forecast Trough",k_pred)).replace(",",""))
k_bull=float(str(kr.get("Bull Candle %","50%")).replace("%",""))
rr=round(abs(k_peak-r['Close'])/max(abs(k_trgh-r['Close']),0.01),1)
ai_cls="m-green" if k_up else "m-red"
ai_lbl="Rising &#9650;" if k_up else "Falling &#9660;"
ai_sub=f"AI expects price to go {'up' if k_up else 'down'} over the next 24 hours"
em_cls="m-green" if k_up else "m-red"
em_arrow="&#9650;" if k_up else "&#9660;"
mom_cls="m-green" if k_bull>=60 else "m-amber" if k_bull>=50 else "m-red"
mom_lbl="Strong / trending" if k_bull>=60 else "Mixed / choppy"
tq_cls="m-green" if rr>=1.5 else "m-amber" if rr>=1 else "m-red"
tq_lbl="Good odds" if rr>=1.5 else "Fair odds" if rr>=1 else "Avoid - bad odds"
rng_pct=round(abs(k_peak-k_trgh)/r['Close']*100,1)
k1,k2,k3=st.columns(3)
with k1: st.markdown(f'<div class="ns-kron-card"><div class="ns-kron-lbl">AI Forecast</div><div class="ns-kron-val {ai_cls}">{ai_lbl}</div><div class="ns-kron-sub">{ai_sub}</div></div>',unsafe_allow_html=True)
with k2: st.markdown(f'<div class="ns-kron-card"><div class="ns-kron-lbl">Expected Move</div><div class="ns-kron-val {em_cls}">{em_arrow} {k_chg}</div><div class="ns-kron-sub">{"Gaining" if k_up else "Losing"} {k_chg.replace("+","").replace("-","")} from here</div></div>',unsafe_allow_html=True)
with k3: st.markdown(f'<div class="ns-kron-card"><div class="ns-kron-lbl">Price Range</div><div class="ns-kron-val m-green">&#9650; {k_peak:,.2f}</div><div class="ns-kron-sub"><span style="color:{RED}">&#9660; {k_trgh:,.2f}</span> ({rng_pct}% range)</div></div>',unsafe_allow_html=True)
k4,k5,k6=st.columns(3)
with k4: st.markdown(f'<div class="ns-kron-card"><div class="ns-kron-lbl">Momentum</div><div class="ns-kron-val {mom_cls}">{mom_lbl}</div><div class="ns-kron-sub">{k_bull:.0f}% of forecast candles close green - {"no clear" if k_bull<55 else "bullish"} direction</div></div>',unsafe_allow_html=True)
with k5: st.markdown(f'<div class="ns-kron-card"><div class="ns-kron-lbl">Target Price</div><div class="ns-kron-val m-white">{float(str(k_pred).replace(",","")):,.2f}</div><div class="ns-kron-sub">Where AI thinks price lands after {kr.get("Candles Forecast",20)} candles</div></div>',unsafe_allow_html=True)
with k6: st.markdown(f'<div class="ns-kron-card"><div class="ns-kron-lbl">Trade Quality</div><div class="ns-kron-val {tq_cls}">{tq_lbl}</div><div class="ns-kron-sub">For every $1 downside risk, {"$"+str(rr)+" upside" if rr>=1 else "only $"+str(rr)+" upside"}</div></div>',unsafe_allow_html=True)

# Kronos confidence score
kconf = kronos_confidence(kr, sc)
conf_bar_pct = kconf["score"]
conf_bar_color = {"m-green":GREEN,"m-amber":AMBER,"m-red":RED,"m-muted":MUTED}.get(kconf["cls"],MUTED)
st.markdown(f"""
<div class="ns-card" style="margin-bottom:1rem">
  <div class="ns-card-title">Kronos Prediction Confidence</div>
  <div style="display:flex;align-items:center;gap:16px;margin-bottom:10px">
    <div style="font-size:52px;font-weight:700;font-family:'JetBrains Mono',monospace;
         color:{conf_bar_color};line-height:1">{kconf["score"]}%</div>
    <div>
      <div style="font-size:16px;font-weight:600;color:{conf_bar_color};margin-bottom:2px">{kconf["label"]}</div>
      <div style="font-size:12px;color:{MUTED}">Grade {kconf["grade"]}  &middot;  {kconf["direction"]}  &middot;  R/R {kconf["rr"]}</div>
    </div>
  </div>
  <div style="background:{BORDER};border-radius:4px;height:8px;margin-bottom:10px">
    <div style="width:{conf_bar_pct}%;height:8px;border-radius:4px;background:{conf_bar_color};transition:width .4s"></div>
  </div>
  <div style="font-size:12px;color:{MUTED};line-height:1.6">{kconf["explanation"]}</div>
</div>""", unsafe_allow_html=True)

# Kronos Bull / Bear agent debate
kdkey = f"kronos_debate_{ticker}_{interval}"
if api_key:
    st.markdown(f'<div style="display:flex;align-items:center;gap:10px;margin:1rem 0 .6rem;font-size:9px;font-weight:700;letter-spacing:.18em;color:{MUTED};text-transform:uppercase"><span style="color:{ACCENT}">▲▼</span> KRONOS AGENT DEBATE</div>', unsafe_allow_html=True)
    if kdkey not in st.session_state:
        st.session_state[kdkey] = run_kronos_debate(kr, kconf, api_key)
        st.rerun()
    kd = st.session_state[kdkey]
    kb = kd.get("KBULL", {}); ks = kd.get("KBEAR", {})
    col_b, col_s = st.columns(2)
    with col_b:
        st.markdown(f'<div class="card-bull"><div class="ns-agent-tag tag-bull">▲ KRONOS BULL</div><div class="ns-agent-name">Arjun — Forecast Bull</div><div class="ns-agent-body">{kb.get("body","")}</div><span class="ns-verdict {kb.get("vc","vd-wait")}">{kb.get("verdict","WAIT")}</span></div>', unsafe_allow_html=True)
    with col_s:
        st.markdown(f'<div class="card-bear"><div class="ns-agent-tag tag-bear">▼ KRONOS BEAR</div><div class="ns-agent-name">Cipher — Forecast Bear</div><div class="ns-agent-body">{ks.get("body","")}</div><span class="ns-verdict {ks.get("vc","vd-wait")}">{ks.get("verdict","WAIT")}</span></div>', unsafe_allow_html=True)

# 06 AI Lab
st.markdown(f'<div class="ns-sec"><span class="ns-dot">&#9679;</span> 06 &mdash; AI LAB <span class="ns-dot">&#9679;</span></div>',unsafe_allow_html=True)
dkey=f"debate_{ticker}_{interval}"; debate={}
if not api_key:
    st.markdown(f'<div style="color:{MUTED};font-size:13px;padding:.75rem 0;text-align:center">Add ANTHROPIC_API_KEY to Streamlit secrets to enable AI Lab.</div>',unsafe_allow_html=True)
elif dkey in st.session_state:
    debate=st.session_state[dkey]
    bull_d=debate.get("BULL",{}); bear_d=debate.get("BEAR",{})
    risk_d=debate.get("RISK",{}); cio_d=debate.get("CIO",{})
    col_b,col_s=st.columns(2)
    with col_b: st.markdown(f'<div class="card-bull"><div class="ns-agent-tag tag-bull">Bull BULL CASE</div><div class="ns-agent-name">Alex &mdash; Long Desk</div><div class="ns-agent-body">{bull_d.get("body","")}</div><span class="ns-verdict {bull_d.get("vc","vd-wait")}">{bull_d.get("verdict","WAIT")}</span></div>',unsafe_allow_html=True)
    with col_s: st.markdown(f'<div class="card-bear"><div class="ns-agent-tag tag-bear">Bear BEAR CASE</div><div class="ns-agent-name">Sam &mdash; Short Desk</div><div class="ns-agent-body">{bear_d.get("body","")}</div><span class="ns-verdict {bear_d.get("vc","vd-wait")}">{bear_d.get("verdict","WAIT")}</span></div>',unsafe_allow_html=True)
    col_r,col_c=st.columns(2)
    with col_r: st.markdown(f'<div class="card-risk"><div class="ns-agent-tag tag-risk">Shield RISK MANAGER</div><div class="ns-agent-name">Jordan &mdash; Risk</div><div class="ns-agent-body">{risk_d.get("body","")}</div><span class="ns-verdict {risk_d.get("vc","vd-wait")}">{risk_d.get("verdict","WAIT")}</span></div>',unsafe_allow_html=True)
    with col_c: st.markdown(f'<div class="card-cio"><div class="ns-agent-tag tag-cio">Diamond CIO VERDICT</div><div class="ns-agent-name">Morgan &mdash; CIO</div><div class="ns-agent-body">{cio_d.get("body","")}</div><span class="ns-verdict {cio_d.get("vc","vd-wait")}">{cio_d.get("verdict","WAIT")}</span></div>',unsafe_allow_html=True)
else:
    debate=run_debate(ctx,api_key)
    st.session_state[dkey]=debate
    st.rerun()

# 07 Export
st.markdown(f'<div class="ns-sec"><span class="ns-dot">&#9679;</span> 07 &mdash; EXPORT <span class="ns-dot">&#9679;</span></div>',unsafe_allow_html=True)
try:
    _pfig = price_chart(df, symbol, chart_bars)
    _kfig = kronos_chart(df, kr)
    # Keep dark theme for PDF - matches the dark slide backgrounds
    _pfig.update_layout(paper_bgcolor="#060a0f", plot_bgcolor="#0a0f14",
                        margin=dict(l=8,r=8,t=8,b=8))
    _kfig.update_layout(paper_bgcolor="#060a0f", plot_bgcolor="#0a0f14",
                        margin=dict(l=8,r=8,t=8,b=8))
    # Render at slide proportions: w=2130px = 213mm@10dpi*10, h proportional
    # Moderate resolution: enough for A4 landscape print without OOM
    price_png  = chart_to_png(_pfig, width=1200, height=480)
    kronos_png = chart_to_png(_kfig, width=1200, height=520)
    pdf_bytes=gen_pdf(symbol,sc,df,debate,kr,price_png,kronos_png,interval)
    fname=f"NiftySniper_{symbol}_{interval}_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
    st.download_button(label="Download Report (PDF)",data=pdf_bytes,
        file_name=fname,mime="application/pdf",use_container_width=True)
except Exception as e:
    st.error(f"PDF error: {e}")
    import traceback
    st.code(traceback.format_exc())

st.markdown(f'<div style="text-align:center;font-size:10px;color:{MUTED};margin-top:2.5rem;padding-top:1rem;border-top:1px solid {BORDER}">Data via Yahoo Finance / NSE. Signals are not financial advice.<br>Past performance does not guarantee future results.</div>',unsafe_allow_html=True)
