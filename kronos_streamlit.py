"""
kronos_streamlit.py
Self-contained Kronos-style AI forecast panel for NiftySniper AI Lab.
Runs entirely inside Streamlit — no external service needed.
Uses AR1 + volatility model on real yfinance data as a drop-in for
the GBM Probability Cone until real Kronos GPU service is available.
"""
import numpy as np
import pandas as pd
import yfinance as yf
import streamlit as st


@st.cache_data(ttl=3600, show_spinner=False)
def _fetch_and_forecast(symbol: str, pred_len: int = 15) -> dict:
    """Fetch OHLCV and run AR1 forecast — cached 1 hour."""
    try:
        sym = symbol.upper() + ".NS" if not symbol.upper().endswith(".NS") else symbol.upper()
        df = yf.download(sym, period="6mo", interval="1d", auto_adjust=True, progress=False)
        if df.empty:
            return None

        df = df.rename(columns={"Open":"open","High":"high","Low":"low","Close":"close","Volume":"volume"})
        closes = df["close"].dropna().values.astype(float)
        if len(closes) < 10:
            return None

        # Compute volatility and drift from last 60 days
        returns = np.diff(np.log(closes[-60:]))
        mu  = float(np.mean(returns))
        sig = float(np.std(returns))
        last_close = float(closes[-1])

        # AR1 forecast with mean reversion
        ar1_coef = 0.3  # mild mean reversion
        pred_closes, pred_highs, pred_lows, pred_opens = [], [], [], []
        c = last_close
        long_mean = float(np.mean(closes[-20:]))
        for _ in range(pred_len):
            shock  = np.random.normal(mu, sig)
            revert = ar1_coef * (long_mean - c) / long_mean
            c_new  = c * np.exp(shock + revert)
            h = c_new * (1 + abs(np.random.normal(0, sig * 0.5)))
            l = c_new * (1 - abs(np.random.normal(0, sig * 0.5)))
            o = c * (1 + np.random.normal(0, sig * 0.3))
            pred_closes.append(round(c_new, 2))
            pred_highs.append(round(h, 2))
            pred_lows.append(round(l, 2))
            pred_opens.append(round(o, 2))
            c = c_new

        # Derive signals
        dir_pct   = round((pred_closes[-1] - last_close) / last_close * 100, 2)
        direction = "bullish" if dir_pct > 1.5 else "bearish" if dir_pct < -1.5 else "neutral"
        up_moves  = sum(1 for i in range(1, len(pred_closes)) if pred_closes[i] > pred_closes[i-1])
        conviction= round(max(up_moves, pred_len-1-up_moves) / max(pred_len-1, 1) * 100, 1)

        return {
            "direction":    direction,
            "direction_pct":dir_pct,
            "target_price": round(max(pred_closes), 2),
            "support_price":round(min(pred_lows), 2),
            "conviction":   conviction,
            "pred_closes":  pred_closes,
            "last_close":   last_close,
        }
    except Exception as e:
        return None


def render_kronos_forecast(symbol: str, cp: float):
    """
    Drop-in replacement for render_probability_cone().
    Call from app.py right column with the current symbol and price.
    """
    data = _fetch_and_forecast(symbol)

    if data is None:
        st.markdown(
            '<div class="ns-card" style="text-align:center;color:#333;font-size:10px;padding:16px;">'
            'Kronos forecast unavailable for this symbol</div>',
            unsafe_allow_html=True
        )
        return

    direction   = data["direction"]
    dir_pct     = data["direction_pct"]
    target      = data["target_price"]
    support     = data["support_price"]
    conviction  = data["conviction"]
    closes      = data["pred_closes"]
    last_close  = data["last_close"]

    dir_col  = "#00c851" if direction == "bullish" else "#ff4444" if direction == "bearish" else "#ffaa00"
    dir_icon = "&#9650;" if direction == "bullish" else "&#9660;" if direction == "bearish" else "&#8212;"
    conv_col = "#00c851" if conviction >= 70 else "#ffaa00" if conviction >= 50 else "#ff4444"
    target_pct  = round((target  - last_close) / last_close * 100, 1)
    support_pct = round((support - last_close) / last_close * 100, 1)

    # Mini sparkline
    all_p  = [last_close] + closes
    min_p  = min(all_p); max_p = max(all_p); rng = max_p - min_p or 1
    W, H   = 220, 48
    pts    = " ".join([
        f"L{((i+1)/len(closes))*W:.1f},{H-((c-min_p)/rng)*H:.1f}"
        for i, c in enumerate(closes)
    ])
    sp     = f"M0,{H-((last_close-min_p)/rng)*H:.1f} {pts}"

    st.markdown(f"""
<div class="ns-ct">&#127919; Kronos AI Forecast
  <span class="ns-tag">AR1 MODEL</span>
</div>
<div style="background:#0d0d0d;border:1px solid #1a1a1a;border-top:2px solid {dir_col};border-radius:6px;padding:12px;margin-bottom:10px;">
  <div style="font-size:8px;color:#333;letter-spacing:.12em;text-transform:uppercase;font-family:'JetBrains Mono',monospace;margin-bottom:6px;">15-day AI direction</div>
  <div style="display:flex;align-items:center;gap:8px;margin-bottom:4px;">
    <span style="font-size:16px;color:{dir_col};">{dir_icon}</span>
    <span style="font-size:18px;font-weight:700;color:{dir_col};font-family:'JetBrains Mono',monospace;">{direction.upper()}</span>
  </div>
  <div style="font-size:9px;color:#555;font-family:'JetBrains Mono',monospace;">
    Predicted move: <span style="color:{dir_col};font-weight:700;">{'+' if dir_pct > 0 else ''}{dir_pct}%</span> over 15 days
  </div>
</div>
<div style="background:#111;border-radius:5px;padding:8px 10px;margin-bottom:10px;">
  <svg width="{W}" height="{H}" style="display:block;overflow:visible;">
    <circle cx="0" cy="{H-((last_close-min_p)/rng)*H:.1f}" r="3" fill="#ff6600"/>
    <path d="{sp}" fill="none" stroke="{dir_col}" stroke-width="1.5"/>
  </svg>
  <div style="display:flex;justify-content:space-between;font-size:8px;color:#333;font-family:'JetBrains Mono',monospace;margin-top:4px;">
    <span>Now &#8377;{last_close:,.0f}</span>
    <span>+15d &#8377;{closes[-1]:,.0f}</span>
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
  AR1 + mean reversion &middot; NSE daily &middot; 15-candle forecast
</div>""", unsafe_allow_html=True)
