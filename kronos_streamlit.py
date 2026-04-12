"""
kronos_streamlit.py - Drop-in replacement for render_probability_cone()
in niftysniper-ai-lab/app.py

Usage:
    from kronos_streamlit import render_kronos_forecast
    render_kronos_forecast(display_symbol, cp)
"""
import os, requests
import streamlit as st
import pandas as pd
import numpy as np

KRONOS_URL = os.getenv("KRONOS_SERVICE_URL", "https://niftysniper-kronos.onrender.com")

@st.cache_data(ttl=1800, show_spinner=False)
def fetch_kronos_forecast(symbol: str, pred_len: int = 15) -> dict | None:
    try:
        r = requests.post(f"{KRONOS_URL}/forecast",
            json={"symbol": symbol, "lookback": 120, "pred_len": pred_len, "interval": "1d"},
            timeout=30)
        if r.status_code == 200:
            return r.json()
    except Exception as e:
        st.warning(f"Kronos unavailable: {e}")
    return None

def render_kronos_forecast(symbol: str, cp: float):
    data = fetch_kronos_forecast(symbol)
    if data is None:
        st.markdown('<div class="ns-card" style="text-align:center;color:#333;font-size:10px;">Kronos forecast unavailable</div>', unsafe_allow_html=True)
        return

    direction  = data.get("direction","neutral")
    dir_pct    = data.get("direction_pct", 0)
    target     = data.get("target_price", cp)
    support    = data.get("support_price", cp)
    conviction = data.get("conviction", 0)
    candles    = data.get("candles", [])
    is_mock    = data.get("mock", False)

    dir_col  = "#00c851" if direction=="bullish" else "#ff4444" if direction=="bearish" else "#ffaa00"
    dir_icon = "&#9650;" if direction=="bullish" else "&#9660;" if direction=="bearish" else "&#8212;"
    mock_badge = '<span style="font-size:8px;background:#1a1a00;border:1px solid #333;color:#666;border-radius:3px;padding:1px 4px;margin-left:6px;">DEMO</span>' if is_mock else ""

    target_pct  = round((target  - cp) / cp * 100, 1)
    support_pct = round((support - cp) / cp * 100, 1)
    conv_col = "#00c851" if conviction>=70 else "#ffaa00" if conviction>=50 else "#ff4444"

    closes = [c["close"] for c in candles]
    all_p  = [cp] + closes
    min_p, max_p = min(all_p), max(all_p)
    rng = max_p - min_p or 1
    W, H = 220, 48
    pts = " ".join([f"L{((i+1)/max(len(closes),1))*W:.1f},{H-((c-min_p)/rng)*H:.1f}" for i,c in enumerate(closes)])
    sp  = f"M0,{H-((cp-min_p)/rng)*H:.1f} {pts}"

    st.markdown(f"""
<div class="ns-ct">&#127919; Kronos AI Forecast<span class="ns-tag">AAAI 2026</span>{mock_badge}</div>
<div style="background:#0d0d0d;border:1px solid #1a1a1a;border-top:2px solid {dir_col};border-radius:6px;padding:12px;margin-bottom:10px;">
  <div style="font-size:8px;color:#333;letter-spacing:.12em;text-transform:uppercase;font-family:'JetBrains Mono',monospace;margin-bottom:6px;">15-day AI direction</div>
  <div style="display:flex;align-items:center;gap:8px;margin-bottom:4px;">
    <span style="font-size:16px;color:{dir_col};">{dir_icon}</span>
    <span style="font-size:18px;font-weight:700;color:{dir_col};font-family:'JetBrains Mono',monospace;">{direction.upper()}</span>
  </div>
  <div style="font-size:9px;color:#555;font-family:'JetBrains Mono',monospace;">
    Predicted move: <span style="color:{dir_col};font-weight:700;">{'+' if dir_pct>0 else ''}{dir_pct}%</span> over 15 days
  </div>
</div>
<div style="background:#111;border-radius:5px;padding:8px 10px;margin-bottom:10px;">
  <svg width="{W}" height="{H}" style="display:block;overflow:visible;">
    <circle cx="0" cy="{H-((cp-min_p)/rng)*H:.1f}" r="3" fill="#ff6600"/>
    <path d="{sp}" fill="none" stroke="{dir_col}" stroke-width="1.5"/>
  </svg>
  <div style="display:flex;justify-content:space-between;font-size:8px;color:#333;font-family:'JetBrains Mono',monospace;margin-top:4px;">
    <span>Now &#8377;{cp:,.0f}</span><span>+15d &#8377;{closes[-1] if closes else cp:,.0f}</span>
  </div>
</div>
<div style="display:grid;grid-template-columns:repeat(3,1fr);gap:6px;margin-bottom:8px;">
  <div style="background:#111;border-radius:4px;padding:8px;text-align:center;">
    <div style="font-size:7px;color:#333;text-transform:uppercase;letter-spacing:.08em;font-family:'JetBrains Mono',monospace;margin-bottom:3px;">AI Target</div>
    <div style="font-size:11px;font-weight:700;color:#00c851;font-family:'JetBrains Mono',monospace;">&#8377;{target:,.0f}</div>
    <div style="font-size:8px;color:#555;font-family:'JetBrains Mono',monospace;">+{target_pct}%</div>
  </div>
  <div style="background:#111;border-radius:4px;padding:8px;text-align:center;">
    <div style="font-size:7px;color:#333;text-transform:uppercase;letter-spacing:.08em;font-family:'JetBrains Mono',monospace;margin-bottom:3px;">AI Support</div>
    <div style="font-size:11px;font-weight:700;color:#ff4444;font-family:'JetBrains Mono',monospace;">&#8377;{support:,.0f}</div>
    <div style="font-size:8px;color:#555;font-family:'JetBrains Mono',monospace;">{support_pct}%</div>
  </div>
  <div style="background:#111;border-radius:4px;padding:8px;text-align:center;">
    <div style="font-size:7px;color:#333;text-transform:uppercase;letter-spacing:.08em;font-family:'JetBrains Mono',monospace;margin-bottom:3px;">Conviction</div>
    <div style="font-size:11px;font-weight:700;color:{conv_col};font-family:'JetBrains Mono',monospace;">{conviction}%</div>
    <div style="font-size:8px;color:#555;font-family:'JetBrains Mono',monospace;">trend consistency</div>
  </div>
</div>
<div style="font-size:8px;color:#222;text-align:center;font-family:'JetBrains Mono',monospace;">
  {data.get('model','kronos')} &middot; NSE daily &middot; 15-candle AI forecast
</div>""", unsafe_allow_html=True)
