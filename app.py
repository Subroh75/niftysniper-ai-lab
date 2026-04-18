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
TEXT="#e8e8e8"; MUTED="#6b7280"; BORDER="#1f2937"; PLOT_BG="#0a0f14"

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

/* ── Interval radio pill buttons ─────────────────────── */
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
    {"key":"BULL","name":"Alex — Long Desk","tag":"BULL CASE","icon":"Bull",
     "card":"card-bull","tag_cls":"tag-bull",
     "system":"""You are ALEX, Long Desk analyst at NiftySniper. Make the strongest bullish case for this NSE stock. Be specific with exact numbers from the data provided. Write 3-4 sentences. On the very last line write only one word: BUY, HOLD, or WATCH."""},
    {"key":"BEAR","name":"Sam — Short Desk","tag":"BEAR CASE","icon":"Bear",
     "card":"card-bear","tag_cls":"tag-bear",
     "system":"""You are SAM, Short Desk analyst at NiftySniper. Make the strongest bearish case. Cite overbought signals, resistance, weak volume, macro risks with exact numbers. Write 3-4 sentences. On the very last line write only one word: SELL, HOLD, or WATCH."""},
    {"key":"RISK","name":"Jordan — Risk","tag":"RISK MANAGER","icon":"Risk",
     "card":"card-risk","tag_cls":"tag-risk",
     "system":"""You are JORDAN, Risk Manager at NiftySniper. State the ATR stop loss (1.5x ATR below close), max position size as % of capital, and risk/reward ratio using exact numbers. Write 3-4 sentences. On the very last line write only one word: BUY, HOLD, or WATCH."""},
    {"key":"CIO","name":"Morgan — CIO","tag":"CIO VERDICT","icon":"CIO",
     "card":"card-cio","tag_cls":"tag-cio",
     "system":"""You are MORGAN, CIO at NiftySniper. Synthesise the bull, bear and risk views. State a clear verdict citing the signal score and one decisive data point. Write 3-4 sentences. On the very last line write only one word: BUY, SELL, HOLD, WATCH, or AVOID."""},
]

def ist_now():
    return datetime.now(timezone(timedelta(hours=5,minutes=30))).strftime("%d %b %Y  %H:%M IST")

def safe(t):
    s={"\u2014":"-","\u2013":"-","\u2019":"'","\u2018":"'","\u201c":'"',"\u201d":'"',
       "\u2022":"*","\u25b2":"UP","\u25bc":"DOWN","\u2192":"->","\u20b9":"Rs","\u2026":"..."}
    t=str(t)
    for c,r in s.items(): t=t.replace(c,r)
    return t.encode("latin-1",errors="replace").decode("latin-1")

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
    """Export a Plotly figure to PNG bytes for PDF embedding."""
    try:
        img_bytes = fig.to_image(format="png", width=width, height=height, scale=2)
        return img_bytes
    except Exception:
        return None

INTERVAL_MAP = {
    "1D":"5d","1W":"1mo","1M":"3mo","3M":"6mo","6M":"1y","1Y":"2y"
}

@st.cache_data(ttl=300,show_spinner=False)
def fetch(ticker, period="6mo"):
    # Try the primary ticker first, then fallback strategies
    candidates = [ticker]
    # If .NS suffix, also try .BO (BSE) as fallback
    if ticker.endswith(".NS"):
        candidates.append(ticker.replace(".NS", ".BO"))
    # If period is very short and might return empty, also try longer period
    fallback_periods = [period, "1y", "6mo"] if period in ("5d","1mo") else [period, "6mo"]

    df = None
    for t in candidates:
        for p in fallback_periods:
            try:
                tk = yf.Ticker(t)
                _df = tk.history(period=p, auto_adjust=True)
                if not _df.empty and len(_df) >= 5:
                    df = _df
                    break
            except Exception:
                continue
        if df is not None:
            break
    if df is None or df.empty: return None
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

def build_ctx(sym,sc,df):
    r=df.iloc[-1]
    ema_ok="EMA stack ok" if r["Close"]>r["EMA20"]>r["EMA50"]>r["EMA200"] else "EMA stack mixed"
    return f"""SYMBOL:{sym} SIGNAL:{sc['tier']} ({sc['total']}/13)
V={sc['v']}/5 vol={sc['vol_ratio']}x  P={sc['p']}/3 chg={sc['pct_chg']}%  R={sc['r']}/2 rng={sc['rng_pos']}  T={sc['t']}/3
Close:{r['Close']:.2f} EMA20:{r['EMA20']:.2f} EMA50:{r['EMA50']:.2f} EMA200:{r['EMA200']:.2f}
BB:{r['BB_upper']:.2f}/{r['BB_lower']:.2f} RSI:{r['RSI']:.1f} ADX:{r['ADX']:.1f}
ATR:{r['ATR']:.4f}({r['ATR']/r['Close']*100:.2f}%) Stop:{r['Close']-1.5*r['ATR']:.2f} {ema_ok}""".strip()

def price_chart(df,symbol):
    d=df.tail(90).copy()
    fig=go.Figure()
    fig.add_trace(go.Scatter(x=d.index,y=d["BB_upper"],
        line=dict(color="rgba(255,255,255,0.3)",width=1,dash="dot"),name="BB+",hovertemplate="%{y:.2f}"))
    fig.add_trace(go.Scatter(x=d.index,y=d["BB_lower"],
        line=dict(color="rgba(255,255,255,0.3)",width=1,dash="dot"),
        fill="tonexty",fillcolor="rgba(255,255,255,0.04)",name="BB-",hovertemplate="%{y:.2f}"))
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

class PDF(FPDF):
    """White-background, black-text PDF matching a professional report style."""
    def __init__(self):
        super().__init__()
        self.set_auto_page_break(auto=True, margin=18)

    def header(self):
        # White background
        self.set_fill_color(255,255,255)
        self.rect(0,0,210,297,"F")
        # Orange top bar
        self.set_fill_color(255,102,0)
        self.rect(0,0,210,3,"F")
        # Logo
        self.set_xy(12,7)
        self.set_font("Helvetica","B",20)
        self.set_text_color(255,102,0)
        self.cell(0,10,"NIFTYSNIPER",ln=0)
        self.set_font("Helvetica","",9)
        self.set_text_color(150,150,150)
        self.set_xy(12,18)
        self.cell(0,5,"DETECT EARLY. ACT SMART.",ln=1)
        # Thin rule
        self.set_draw_color(220,220,220)
        self.set_line_width(0.3)
        self.line(10,27,200,27)
        self.set_xy(0,30)

    def footer(self):
        self.set_y(-13)
        self.set_draw_color(220,220,220)
        self.set_line_width(0.3)
        self.line(10,self.get_y(),200,self.get_y())
        self.set_font("Helvetica","I",7)
        self.set_text_color(150,150,150)
        self.cell(0,6,"Data via Yahoo Finance / NSE. Signals are not financial advice. Past performance does not guarantee future results.",align="C")

    def sec(self, title):
        """Section header — orange left bar, grey background row."""
        self.set_fill_color(245,245,245)
        self.rect(10,self.get_y(),190,7,"F")
        self.set_fill_color(255,102,0)
        self.rect(10,self.get_y(),2.5,7,"F")
        self.set_xy(15, self.get_y()+0.75)
        self.set_font("Helvetica","B",8)
        self.set_text_color(80,80,80)
        self.cell(0,6,safe(title).upper(),ln=1)
        self.ln(1)

    def kv(self, label, value, bold=False, color=(40,40,40)):
        """Key-value row on white background."""
        self.set_fill_color(255,255,255)
        self.rect(10,self.get_y(),190,6,"F")
        self.set_x(13)
        self.set_font("Helvetica","",8)
        self.set_text_color(120,120,120)
        self.cell(80,6,safe(label))
        self.set_font("Courier","B" if bold else "",8)
        self.set_text_color(*color)
        self.cell(0,6,safe(str(value)),ln=1)
        # Hairline rule
        self.set_draw_color(235,235,235)
        self.set_line_width(0.2)
        self.line(10,self.get_y(),200,self.get_y())

    def embed_chart(self, img_bytes, label="", w=188, h=70):
        """Embed a PNG chart image."""
        if img_bytes is None:
            return
        self.set_fill_color(248,248,248)
        self.rect(10,self.get_y(),190,h+6,"F")
        if label:
            self.set_xy(12,self.get_y()+1)
            self.set_font("Helvetica","",7)
            self.set_text_color(150,150,150)
            self.cell(0,4,safe(label),ln=1)
        bio = io.BytesIO(img_bytes)
        self.image(bio, x=11, y=self.get_y(), w=w, h=h)
        self.set_y(self.get_y()+h+4)
        self.ln(2)

    def agent_blk(self, name, body, verdict, color=(40,40,40)):
        self.set_fill_color(250,250,250)
        self.rect(10,self.get_y(),190,4,"F")
        self.set_x(13)
        self.set_font("Helvetica","B",8)
        self.set_text_color(*color)
        self.cell(150,5,safe(name),ln=0)
        self.set_font("Helvetica","B",8)
        self.cell(0,5,f"  [{verdict}]",ln=1)
        self.set_font("Helvetica","",7.5)
        self.set_text_color(70,70,70)
        self.set_x(13)
        self.multi_cell(184,4.5,safe(body))
        self.set_draw_color(230,230,230)
        self.set_line_width(0.2)
        self.line(10,self.get_y(),200,self.get_y())
        self.ln(2)


def gen_pdf(symbol, sc, df, debate, kr, price_png=None, kronos_png=None, interval="1D"):
    r = df.iloc[-1]
    pdf = PDF()
    pdf.add_page()

    # ── Signal badge (light orange bg) ───────────────────────────────────────
    pdf.set_fill_color(255,245,235)
    pdf.rect(10,pdf.get_y(),190,30,"F")
    pdf.set_draw_color(255,102,0)
    pdf.set_line_width(0.5)
    pdf.rect(10,pdf.get_y(),190,30)
    # Meta line
    pdf.set_xy(10,pdf.get_y()+3)
    pdf.set_font("Helvetica","",8)
    pdf.set_text_color(150,150,150)
    pdf.cell(0,4,safe(f"{symbol}  |  {interval}  |  {ist_now()}"),align="C",ln=1)
    # Signal name
    sig_col = (200,80,0) if "STRONG" in sc["tier"] else               (180,130,0) if "BUILDING" in sc["tier"] else (100,100,100)
    pdf.set_font("Helvetica","B",20)
    pdf.set_text_color(*sig_col)
    pdf.cell(0,11,safe(f"SIGNAL: {sc['tier']}  ({sc['total']}/13)"),align="C",ln=1)
    # Stats bar
    pdf.set_font("Courier","",8)
    pdf.set_text_color(80,80,80)
    pct = sc['pct_chg']
    pct_str = f"+{pct:.2f}%" if pct>=0 else f"{pct:.2f}%"
    pdf.cell(0,5,safe(f"CLOSE {r['Close']:,.2f}   {pct_str}   VOL {sc['vol_ratio']}x   RSI {r['RSI']:.0f}   ADX {r['ADX']:.0f}"),align="C",ln=1)
    pdf.ln(5)

    # ── Signal Components ─────────────────────────────────────────────────────
    pdf.sec("Signal Components")
    green=(0,140,60); red=(200,40,40); orange=(200,80,0)
    for lbl,s,mx,raw in [
        ("V Volume (max 5)",       sc['v'], 5, f"vol = {sc['vol_ratio']}x vs 20-bar avg"),
        ("P Momentum (max 3)",     sc['p'], 3, f"chg = {sc['pct_chg']}%"),
        ("R Range Position (max 2)",sc['r'],2, f"range_pos = {sc['rng_pos']}"),
        ("T Trend Alignment (max 3)",sc['t'],3,f"ADX {r['ADX']:.1f}"),
    ]:
        sc_col = green if s==mx else orange if s>0 else (160,160,160)
        pdf.set_fill_color(255,255,255)
        pdf.rect(10,pdf.get_y(),190,6,"F")
        pdf.set_x(13)
        pdf.set_font("Helvetica","",8); pdf.set_text_color(80,80,80)
        pdf.cell(95,6,safe(lbl))
        pdf.set_font("Courier","B",8); pdf.set_text_color(*sc_col)
        pdf.cell(20,6,f"{s}/{mx}")
        pdf.set_font("Helvetica","",8); pdf.set_text_color(130,130,130)
        pdf.cell(0,6,safe(raw),ln=1)
        pdf.set_draw_color(235,235,235); pdf.set_line_width(0.2)
        pdf.line(10,pdf.get_y(),200,pdf.get_y())
    pdf.ln(3)

    # ── Price Chart ───────────────────────────────────────────────────────────
    if price_png:
        pdf.sec("Price Chart")
        pdf.embed_chart(price_png, label="Candlestick  |  EMA20  EMA50  EMA200  BB+/-", h=72)
        pdf.ln(1)

    # ── Timing Quality ────────────────────────────────────────────────────────
    def vc(v,ref): return green if v>ref else red
    pdf.sec("Timing Quality")
    pdf.kv("RSI 14",    f"{r['RSI']:.1f}",   bold=True, color=red if r['RSI']>70 else green if r['RSI']<30 else (40,40,40))
    pdf.kv("ADX 14",    f"{r['ADX']:.1f}   ({'Trending' if r['ADX']>25 else 'Ranging'})")
    pdf.kv("+DI / -DI", f"{r['DI_pos']:.1f} / {r['DI_neg']:.1f}", bold=True,
           color=green if r['DI_pos']>r['DI_neg'] else red)
    pdf.kv("ATR 14",    f"{r['ATR']:.4f}   ({r['ATR']/r['Close']*100:.2f}% of price)")
    pdf.kv("Stop (1.5x ATR)", f"{r['Close']-1.5*r['ATR']:.2f}", bold=True, color=red)
    pdf.ln(3)

    # ── Market Structure ──────────────────────────────────────────────────────
    pdf.sec("Market Structure")
    pdf.kv("Close",    f"{r['Close']:.2f}", bold=True)
    pdf.kv("EMA 20",   f"{r['EMA20']:.2f}   ({'above' if r['Close']>r['EMA20'] else 'below'})", color=vc(r['Close'],r['EMA20']))
    pdf.kv("EMA 50",   f"{r['EMA50']:.2f}   ({'above' if r['Close']>r['EMA50'] else 'below'})", color=vc(r['Close'],r['EMA50']))
    pdf.kv("EMA 200",  f"{r['EMA200']:.2f}  ({'above' if r['Close']>r['EMA200'] else 'below'})",color=vc(r['Close'],r['EMA200']))
    pdf.kv("BB Upper/Lower", f"{r['BB_upper']:.2f} / {r['BB_lower']:.2f}")
    pdf.ln(3)

    # ── Kronos Forecast ───────────────────────────────────────────────────────
    if kr:
        pdf.sec("Kronos AI Forecast")
        if kronos_png:
            pdf.embed_chart(kronos_png, label="Kronos-mini forecast cone", h=60)
        for k,v in kr.items():
            pdf.kv(k, str(v))
        pdf.ln(3)

    # ── AI Lab ────────────────────────────────────────────────────────────────
    if debate:
        pdf.sec("AI Lab — Agent Debate")
        agent_colors = {
            "BULL":(0,140,60),"BEAR":(200,40,40),
            "RISK":(30,80,180),"CIO":(100,40,180)
        }
        for ag in AGENTS:
            d = debate.get(ag["key"])
            if d:
                pdf.agent_blk(
                    ag["name"], d.get("body",""), d.get("verdict",""),
                    color=agent_colors.get(ag["key"],(40,40,40)))

    return bytes(pdf.output())

# ══════════════════════════════════════════════════════════════════════════════
# APP
# ══════════════════════════════════════════════════════════════════════════════
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
    index=3,horizontal=True,label_visibility="collapsed")
period=INTERVAL_MAP[interval]

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
        df=fetch(ticker,period)
    except Exception as _e:
        df=None

if df is None or len(df)<30:
    st.warning(f"Could not load data for **{symbol}** right now. Yahoo Finance may be throttling — wait 30 seconds and try again, or try another symbol.")
    st.info("Tip: If this keeps happening, NSE/BSE data feeds occasionally go offline between 3:30PM–9:15AM IST.")
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
st.plotly_chart(price_chart(df,symbol),use_container_width=True,config=pcfg())
st.markdown('</div>',unsafe_allow_html=True)

# 04 Timing Quality — 3x2 metric cards
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

# 06 AI Lab
st.markdown(f'<div class="ns-sec"><span class="ns-dot">&#9679;</span> 06 &mdash; AI LAB <span class="ns-dot">&#9679;</span></div>',unsafe_allow_html=True)
dkey=f"debate_{ticker}_{sc['total']}_{interval}"; debate={}
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
    _pfig = price_chart(df, symbol)
    _kfig = kronos_chart(df, kr)
    _pfig.update_layout(paper_bgcolor="white",plot_bgcolor="#f9fafb",font=dict(color="#333"))
    _pfig.update_yaxes(gridcolor="#e5e7eb")
    _kfig.update_layout(paper_bgcolor="white",plot_bgcolor="#f9fafb",font=dict(color="#333"))
    _kfig.update_yaxes(gridcolor="#e5e7eb")
    price_png  = chart_to_png(_pfig, width=760, height=280)
    kronos_png = chart_to_png(_kfig, width=760, height=210)
    pdf_bytes=gen_pdf(symbol,sc,df,debate,kr,price_png,kronos_png,interval)
    fname=f"NiftySniper_{symbol}_{interval}_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
    st.download_button(label="Download Report (PDF)",data=pdf_bytes,
        file_name=fname,mime="application/pdf",use_container_width=True)
except Exception as e: st.error(f"PDF error: {e}")

st.markdown(f'<div style="text-align:center;font-size:10px;color:{MUTED};margin-top:2.5rem;padding-top:1rem;border-top:1px solid {BORDER}">Data via Yahoo Finance / NSE. Signals are not financial advice.<br>Past performance does not guarantee future results.</div>',unsafe_allow_html=True)
