import base64
import io
import math
import os
from datetime import datetime, timezone
from tempfile import NamedTemporaryFile

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import mplfinance as mpf
import numpy as np
import pandas as pd
import streamlit as st
import yfinance as yf
from PIL import Image, ImageDraw, ImageFont
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    Image as RLImage,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

st.set_page_config(page_title="Nifty Sniper", page_icon="📈", layout="wide")

# ---------- Theme ----------
BLACK = "#000000"
CARD = "#0B0B0B"
CARD_2 = "#111111"
BORDER = "#242424"
ORANGE = "#FF8C00"
ORANGE_2 = "#FF6A00"
TEXT = "#FFFFFF"
MUTED = "#A1A1A1"
GREEN = "#26C281"
RED = "#E74C3C"

LOGO_PATH = "assets/nifty_sniper_logo.png"

NIFTY_SYMBOLS = {
    "RELIANCE": "RELIANCE.NS",
    "TCS": "TCS.NS",
    "INFY": "INFY.NS",
    "HDFCBANK": "HDFCBANK.NS",
    "ICICIBANK": "ICICIBANK.NS",
    "SBIN": "SBIN.NS",
    "LT": "LT.NS",
    "BHARTIARTL": "BHARTIARTL.NS",
    "ITC": "ITC.NS",
    "KOTAKBANK": "KOTAKBANK.NS",
    "HINDUNILVR": "HINDUNILVR.NS",
    "ASIANPAINT": "ASIANPAINT.NS",
    "BAJFINANCE": "BAJFINANCE.NS",
    "AXISBANK": "AXISBANK.NS",
    "MARUTI": "MARUTI.NS",
    "SUNPHARMA": "SUNPHARMA.NS",
    "ULTRACEMCO": "ULTRACEMCO.NS",
    "M&M": "M&M.NS",
    "NTPC": "NTPC.NS",
    "POWERGRID": "POWERGRID.NS",
    "TITAN": "TITAN.NS",
    "WIPRO": "WIPRO.NS",
    "NESTLEIND": "NESTLEIND.NS",
    "TECHM": "TECHM.NS",
    "HCLTECH": "HCLTECH.NS",
    "TATAMOTORS": "TATAMOTORS.NS",
    "ADANIENT": "ADANIENT.NS",
    "BAJAJFINSV": "BAJAJFINSV.NS",
    "JSWSTEEL": "JSWSTEEL.NS",
    "TATASTEEL": "TATASTEEL.NS",
}

INTERVAL_MAP = {
    "1m": {"interval": "1m", "period": "5d"},
    "5m": {"interval": "5m", "period": "1mo"},
    "15m": {"interval": "15m", "period": "2mo"},
    "30m": {"interval": "30m", "period": "3mo"},
    "1H": {"interval": "60m", "period": "6mo"},
    "4H": {"interval": "1h", "period": "1y"},
    "1D": {"interval": "1d", "period": "2y"},
}


# ---------- Utilities ----------
def ensure_logo():
    os.makedirs(os.path.dirname(LOGO_PATH), exist_ok=True)
    if os.path.exists(LOGO_PATH):
        return
    img = Image.new("RGBA", (900, 240), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle((10, 30, 220, 210), radius=42, fill=(255, 140, 0, 255))
    draw.polygon([(58, 162), (112, 88), (160, 126), (196, 74)], fill=(0, 0, 0, 255))
    draw.text((260, 62), "NIFTY SNIPER", fill=(0, 0, 0, 255), font=ImageFont.load_default())
    draw.text((260, 120), "India Equity Signal Engine", fill=(40, 40, 40, 255), font=ImageFont.load_default())
    img.save(LOGO_PATH)


ensure_logo()


def img_to_base64(path: str) -> str:
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def symbol_from_input(raw: str) -> str:
    s = raw.strip().upper().replace(" ", "")
    if not s:
        return ""
    if s.endswith(".NS"):
        return s
    if s in NIFTY_SYMBOLS:
        return NIFTY_SYMBOLS[s]
    return f"{s}.NS"


def get_kronos_horizon(timeframe: str) -> int:
    return 24 if timeframe in ["1m", "5m", "15m", "30m", "1H"] else 12


def fmt_num(v, digits=2):
    try:
        return f"{float(v):,.{digits}f}"
    except Exception:
        return "-"


def calculate_rsi(series: pd.Series, period: int = 14) -> pd.Series:
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    rsi = 100 - (100 / (1 + rs))
    return rsi.fillna(50)


def calculate_adx(df: pd.DataFrame, period: int = 14):
    high = df["High"]
    low = df["Low"]
    close = df["Close"]

    plus_dm = high.diff()
    minus_dm = -low.diff()
    plus_dm = plus_dm.where((plus_dm > minus_dm) & (plus_dm > 0), 0.0)
    minus_dm = minus_dm.where((minus_dm > plus_dm) & (minus_dm > 0), 0.0)

    tr1 = high - low
    tr2 = (high - close.shift()).abs()
    tr3 = (low - close.shift()).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

    atr = tr.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
    plus_di = 100 * (plus_dm.ewm(alpha=1 / period, min_periods=period, adjust=False).mean() / atr)
    minus_di = 100 * (minus_dm.ewm(alpha=1 / period, min_periods=period, adjust=False).mean() / atr)
    dx = 100 * ((plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, np.nan))
    adx = dx.ewm(alpha=1 / period, min_periods=period, adjust=False).mean().fillna(0)
    return adx.fillna(0), plus_di.fillna(0), minus_di.fillna(0), atr.fillna(0)


def fetch_data(symbol: str, timeframe: str):
    cfg = INTERVAL_MAP[timeframe]
    ticker = yf.Ticker(symbol)
    df = ticker.history(period=cfg["period"], interval=cfg["interval"], auto_adjust=False, prepost=False)
    if df.empty:
        return None, None
    if isinstance(df.index, pd.DatetimeIndex):
        df = df.tz_localize(None) if df.index.tz is not None else df
    df = df[["Open", "High", "Low", "Close", "Volume"]].dropna().copy()
    info = ticker.fast_info if hasattr(ticker, "fast_info") else {}
    return df, info


@st.cache_data(show_spinner=False)
def fetch_benchmark(timeframe: str):
    cfg = INTERVAL_MAP[timeframe]
    bench = yf.Ticker("^NSEI").history(period=cfg["period"], interval=cfg["interval"], auto_adjust=False)
    if bench.empty:
        return None
    if isinstance(bench.index, pd.DatetimeIndex):
        bench = bench.tz_localize(None) if bench.index.tz is not None else bench
    return bench[["Close"]].dropna().copy()


def enrich_df(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["EMA20"] = out["Close"].ewm(span=20, adjust=False).mean()
    out["EMA50"] = out["Close"].ewm(span=50, adjust=False).mean()
    out["EMA200"] = out["Close"].ewm(span=200, adjust=False).mean()
    mid = out["Close"].rolling(20).mean()
    std = out["Close"].rolling(20).std()
    out["BB_MID"] = mid
    out["BB_UPPER"] = mid + 2 * std
    out["BB_LOWER"] = mid - 2 * std
    typical = (out["High"] + out["Low"] + out["Close"]) / 3
    out["VWAP"] = (typical * out["Volume"]).cumsum() / out["Volume"].replace(0, np.nan).cumsum()
    out["RSI14"] = calculate_rsi(out["Close"], 14)
    adx, plus_di, minus_di, atr = calculate_adx(out, 14)
    out["ADX14"] = adx
    out["PLUS_DI"] = plus_di
    out["MINUS_DI"] = minus_di
    out["ATR14"] = atr
    out["RVOL"] = out["Volume"] / out["Volume"].rolling(20).mean()
    out["DAY_CHANGE_PCT"] = out["Close"].pct_change() * 100
    hh = out["High"].rolling(20).max()
    ll = out["Low"].rolling(20).min()
    out["RANGE_POS"] = ((out["Close"] - ll) / (hh - ll).replace(0, np.nan)).clip(0, 1).fillna(0)
    out["ATR_MOVE"] = (out["Close"] - out["Close"].shift(1)) / out["ATR14"].replace(0, np.nan)
    return out.dropna().copy()


def relative_strength_score(df: pd.DataFrame, benchmark: pd.DataFrame):
    if benchmark is None or benchmark.empty:
        return 0.0, 0.0
    merged = pd.DataFrame(index=df.index)
    merged["stock"] = df["Close"]
    merged["bench"] = benchmark["Close"].reindex(df.index).ffill().bfill()
    stock_ret = merged["stock"].pct_change(20).iloc[-1] if len(merged) > 20 else 0
    bench_ret = merged["bench"].pct_change(20).iloc[-1] if len(merged) > 20 else 0
    diff = (stock_ret - bench_ret) * 100
    score = 2 if diff > 3 else 1 if diff > 0 else 0
    return float(score), float(diff)


def compute_signal(df: pd.DataFrame, benchmark: pd.DataFrame):
    row = df.iloc[-1]
    prev = df.iloc[-2]

    v = 0
    if row["RVOL"] >= 8:
        v = 5
    elif row["RVOL"] >= 4:
        v = 3
    elif row["RVOL"] >= 2:
        v = 2

    atr_move = row["ATR_MOVE"] if pd.notna(row["ATR_MOVE"]) else 0
    p = 0
    if row["Close"] > prev["Close"]:
        if atr_move >= 4:
            p = 3
        elif atr_move >= 2.5:
            p = 2
        elif atr_move >= 1.5:
            p = 1

    rp = float(row["RANGE_POS"])
    r = 2 if rp >= 0.85 else 1 if rp >= 0.70 else 0

    t = 0
    if row["Close"] > row["EMA20"]:
        t += 1
    if row["EMA20"] > row["EMA50"]:
        t += 1
    if row["ADX14"] >= 20:
        t += 1

    rs_score, rs_diff = relative_strength_score(df, benchmark)
    x_penalty = 0
    if row["Close"] < row["EMA50"]:
        x_penalty += 1
    if row["RSI14"] > 78:
        x_penalty += 1
    if row["RVOL"] < 1:
        x_penalty += 1

    total = v + p + r + t + rs_score - x_penalty
    max_score = 15
    if total >= 10:
        signal = "HIGH CONVICTION"
    elif total >= 7:
        signal = "STRONG"
    elif total >= 4:
        signal = "MODERATE"
    else:
        signal = "NO SIGNAL"

    components = {
        "V - Volume Strength": {"score": v, "max": 5, "detail": f"RVOL = {row['RVOL']:.2f}x"},
        "P - Price Expansion": {"score": p, "max": 3, "detail": f"ATR move = {atr_move:.2f}"},
        "R - Position in Range": {"score": r, "max": 2, "detail": f"range_pos = {rp:.2f}"},
        "T - Trend Alignment": {"score": t, "max": 3, "detail": f"ADX = {row['ADX14']:.1f}"},
        "RS - Relative Strength": {"score": rs_score, "max": 2, "detail": f"vs Nifty = {rs_diff:.2f}%"},
        "X - Risk Penalty": {"score": -x_penalty, "max": 0, "detail": f"penalty = {x_penalty}"},
    }

    return {
        "signal": signal,
        "score": total,
        "max_score": max_score,
        "components": components,
        "rs_diff": rs_diff,
    }


def market_structure(df: pd.DataFrame, signal_pack: dict):
    row = df.iloc[-1]
    close = row["Close"]
    trend_state = (
        "Bullish Trend Continuation"
        if close > row["EMA20"] > row["EMA50"] > row["EMA200"]
        else "Bullish but Extended"
        if close > row["EMA20"] > row["EMA50"] and row["RSI14"] > 70
        else "Sideways Compression"
        if abs(close - row["EMA20"]) / close < 0.01 and row["ADX14"] < 20
        else "Weak / Bearish"
    )
    support = min(row["EMA20"], row["BB_LOWER"])
    resistance = max(row["BB_UPPER"], row["High"])
    table = [
        ("Close", fmt_num(close, 2)),
        ("EMA 20", f"{fmt_num(row['EMA20'], 2)} ({'above' if close > row['EMA20'] else 'below'})"),
        ("EMA 50", f"{fmt_num(row['EMA50'], 2)} ({'above' if close > row['EMA50'] else 'below'})"),
        ("EMA 200", f"{fmt_num(row['EMA200'], 2)} ({'above' if close > row['EMA200'] else 'below'})"),
        ("VWAP", f"{fmt_num(row['VWAP'], 2)} ({'above' if close > row['VWAP'] else 'below'})"),
        ("BB Upper / Lower", f"{fmt_num(row['BB_UPPER'], 2)} / {fmt_num(row['BB_LOWER'], 2)}"),
        ("Day Change", f"{fmt_num(row['DAY_CHANGE_PCT'], 2)}%"),
        ("Rel Strength vs Nifty", f"{fmt_num(signal_pack['rs_diff'], 2)}%"),
        ("Trend State", trend_state),
        ("Support / Resistance", f"{fmt_num(support, 2)} / {fmt_num(resistance, 2)}"),
    ]
    return table, trend_state


def timing_quality(df: pd.DataFrame):
    row = df.iloc[-1]
    quality = (
        "Strong entry timing"
        if row["RSI14"] < 68 and row["ADX14"] > 20 and row["RVOL"] > 1.2 and row["ATR_MOVE"] > 1
        else "Good setup, needs confirmation"
        if row["ADX14"] > 18 and row["ATR_MOVE"] > 0.5
        else "Extended, avoid chasing"
        if row["RSI14"] > 75
        else "Weak timing quality"
    )
    metrics = {
        "RSI 14": fmt_num(row["RSI14"], 1),
        "ADX 14": f"{fmt_num(row['ADX14'], 1)} ({'Trending' if row['ADX14'] >= 20 else 'Soft'})",
        "+DI / -DI": f"{fmt_num(row['PLUS_DI'], 1)} / {fmt_num(row['MINUS_DI'], 1)}",
        "ATR 14": f"{fmt_num(row['ATR14'], 2)} ({fmt_num((row['ATR14']/row['Close'])*100, 2)}% of price)",
        "Rel Volume": f"{fmt_num(row['RVOL'], 2)}x",
        "ATR Move": fmt_num(row["ATR_MOVE"], 2),
    }
    return quality, metrics


def kronos_forecast(df: pd.DataFrame, timeframe: str):
    horizon = get_kronos_horizon(timeframe)
    closes = df["Close"].tail(60).values
    x = np.arange(len(closes))
    slope, intercept = np.polyfit(x, closes, 1)
    base = intercept + slope * (len(closes) - 1)
    atr = df["ATR14"].iloc[-1]
    momentum = df["Close"].pct_change(5).iloc[-1] * 100 if len(df) > 5 else 0

    forecast = []
    upper = []
    lower = []
    curr = closes[-1]
    drift = slope * (1.15 if momentum > 0 else 0.85)
    for i in range(1, horizon + 1):
        seasonal = math.sin(i / 3.5) * atr * 0.25
        price = curr + drift * i + seasonal
        band = atr * (1.4 + i / max(horizon, 1) * 0.8)
        forecast.append(price)
        upper.append(price + band)
        lower.append(max(0.01, price - band))

    predicted_close = float(forecast[-1])
    predicted_change = ((predicted_close / curr) - 1) * 100
    peak = float(max(upper))
    trough = float(min(lower))
    bull_pct = float(np.mean(np.diff(np.array([curr] + forecast)) > 0) * 100)
    direction = "UP" if predicted_change >= 0 else "DOWN"
    momentum_label = (
        "Strong"
        if abs(predicted_change) > 4
        else "Balanced"
        if abs(predicted_change) > 1.5
        else "Soft"
    )
    trade_quality = (
        "High"
        if abs(predicted_change) > 3 and bull_pct > 55 and (peak - trough) / curr < 0.18
        else "Moderate"
        if abs(predicted_change) > 1.5
        else "Cautious"
    )

    cards = {
        "AI Forecast": direction,
        "Expected Move": f"{predicted_change:+.2f}%",
        "Price Range": f"{trough:.2f} to {peak:.2f}",
        "Momentum": momentum_label,
        "Target Price": f"{predicted_close:.2f}",
        "Trade Quality": trade_quality,
    }
    kronos_bull = (
        f"Forecast path leans {direction.lower()} with target near {predicted_close:.2f}. "
        f"Bull-candle rate at {bull_pct:.1f}% suggests {'constructive' if bull_pct >= 50 else 'fragile'} sequencing. "
        f"Upside band reaches {peak:.2f}, so a clean hold above current price can still extend the move."
    )
    kronos_bear = (
        f"Forecast band remains wide from {trough:.2f} to {peak:.2f}, which means path risk is real. "
        f"Expected move of {predicted_change:+.2f}% can still fail if volatility expands against the position. "
        f"If price loses near-term structure, the forecast trough around {trough:.2f} becomes the stress test."
    )

    return {
        "horizon": horizon,
        "direction": direction,
        "expected_move": predicted_change,
        "predicted_close": predicted_close,
        "peak": peak,
        "trough": trough,
        "bull_pct": bull_pct,
        "cards": cards,
        "series": forecast,
        "upper": upper,
        "lower": lower,
        "momentum_label": momentum_label,
        "trade_quality": trade_quality,
        "bull_case": kronos_bull,
        "bear_case": kronos_bear,
    }


def ai_lab(signal_pack, trend_state, timing_label, kronos_pack, df):
    row = df.iloc[-1]
    bull = (
        f"Trend structure remains {trend_state.lower()}. Price is trading above key moving averages, "
        f"signal score is {signal_pack['score']}/{signal_pack['max_score']}, and Kronos points {kronos_pack['direction'].lower()} with "
        f"a target near {kronos_pack['predicted_close']:.2f}. If follow-through volume improves, this can continue."
    )
    bear = (
        f"Risk sits in extension and failed continuation. RSI is {row['RSI14']:.1f}, ADX is {row['ADX14']:.1f}, and the forecast band still stretches down to "
        f"{kronos_pack['trough']:.2f}. If price loses EMA20 or relative strength fades, the setup can unwind quickly."
    )
    risk = (
        f"Timing quality is '{timing_label}'. Use ATR at {row['ATR14']:.2f} as sizing anchor. "
        f"A disciplined stop can sit near {max(0.01, row['Close'] - 1.5 * row['ATR14']):.2f}. Best practice is to avoid oversizing when RVOL is only {row['RVOL']:.2f}x."
    )
    cio = (
        f"Verdict: {signal_pack['signal']}. Full-stack read combines signal components, market structure, timing, and Kronos. "
        f"Current edge is {'actionable' if signal_pack['score'] >= 7 else 'developing' if signal_pack['score'] >= 4 else 'not strong enough yet'}."
    )
    return {
        "Bull": bull,
        "Bear": bear,
        "Risk Manager": risk,
        "CIO": cio,
    }


def make_price_chart(df: pd.DataFrame, symbol: str, timeframe: str) -> str:
    recent = df.tail(80).copy()
    ap = [
        mpf.make_addplot(recent["EMA20"], color="#00c2a0", width=1.45),
        mpf.make_addplot(recent["EMA50"], color="#7b86ff", width=1.35),
        mpf.make_addplot(recent["EMA200"], color="#f0a04b", width=1.35),
        mpf.make_addplot(recent["BB_UPPER"], color="#334f7d", width=0.95, linestyle="--", alpha=0.85),
        mpf.make_addplot(recent["BB_LOWER"], color="#334f7d", width=0.95, linestyle="--", alpha=0.85),
    ]
    style = mpf.make_mpf_style(
        base_mpf_style="nightclouds",
        facecolor=BLACK,
        figcolor=BLACK,
        edgecolor=BORDER,
        gridcolor="#16233a",
        gridstyle="-",
        y_on_right=False,
        marketcolors=mpf.make_marketcolors(
            up="#16d6a4",
            down="#ff6b6b",
            edge={"up": "#16d6a4", "down": "#ff6b6b"},
            wick={"up": "#16d6a4", "down": "#ff6b6b"},
            volume={"up": "#16d6a4", "down": "#ff6b6b"},
            ohlc="inherit",
        ),
        rc={
            "axes.labelcolor": TEXT,
            "xtick.color": "#6f7f99",
            "ytick.color": "#6f7f99",
            "text.color": TEXT,
            "axes.titlecolor": "#9aa8bf",
            "font.size": 9,
        },
    )
    tmp = NamedTemporaryFile(delete=False, suffix=".png")
    mpf.plot(
        recent,
        type="candle",
        style=style,
        addplot=ap,
        volume=False,
        figsize=(10, 3),
        tight_layout=True,
        xrotation=0,
        datetime_format="%H:%M",
        title=f"{symbol} · {timeframe} · Market Structure",
        savefig=dict(fname=tmp.name, dpi=150, bbox_inches="tight", pad_inches=0.05),
    )
    return tmp.name


def make_forecast_chart(df: pd.DataFrame, kronos_pack: dict, symbol: str, timeframe: str, white=False) -> str:
    bg = "white" if white else BLACK
    fg = "black" if white else TEXT
    grid = "#DDDDDD" if white else "#16233a"
    hist_color = "#8fa0bb" if not white else "#55657d"
    forecast_color = "#ff7b7b"
    band_color = "#4a2ca8" if not white else "#7a63d1"
    current_color = "#cfd6e4" if not white else "#666666"

    fig, ax = plt.subplots(figsize=(10, 3), facecolor=bg)
    fig.subplots_adjust(left=0.06, right=0.98, top=0.88, bottom=0.12)
    ax.set_facecolor(bg)
    hist = df["Close"].tail(40).reset_index(drop=True)
    x_hist = np.arange(len(hist))
    x_fc = np.arange(len(hist) - 1, len(hist) + kronos_pack["horizon"])
    series = np.array([hist.iloc[-1]] + kronos_pack["series"])
    upper = np.array([hist.iloc[-1]] + kronos_pack["upper"])
    lower = np.array([hist.iloc[-1]] + kronos_pack["lower"])

    ax.plot(x_hist, hist.values, linewidth=1.55, color=hist_color, label="Historical Close")
    ax.plot(x_fc, series, linewidth=2.15, color=forecast_color, label="Predicted Close")
    ax.fill_between(x_fc, lower, upper, color=band_color, alpha=0.22, label="High/Low Band")
    ax.axhline(hist.iloc[-1], linestyle=(0, (4, 3)), linewidth=1.0, color=current_color, alpha=0.9)
    ax.set_title(f"{symbol} · {timeframe} · Kronos Forecast", color=fg, pad=6)
    ax.grid(True, color=grid, linestyle="-", alpha=0.55, linewidth=0.8)
    ax.tick_params(colors=fg, labelsize=8.5)
    plt.margins(x=0)
    for spine in ax.spines.values():
        spine.set_color(grid)
        spine.set_linewidth(0.8)
    leg = ax.legend(frameon=False, fontsize=8, ncol=3, loc="upper right")
    for text in leg.get_texts():
        text.set_color(fg)
    tmp = NamedTemporaryFile(delete=False, suffix=".png")
    fig.savefig(tmp.name, dpi=150, bbox_inches="tight", pad_inches=0.05, facecolor=bg)
    plt.close(fig)
    return tmp.name


def make_pdf(symbol, timeframe, signal_pack, components, structure_rows, timing_label, timing_metrics, kronos_pack, kronos_chart, price_chart, ai_lab_pack):
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=14 * mm, rightMargin=14 * mm, topMargin=12 * mm, bottomMargin=12 * mm)
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("title", parent=styles["Heading1"], fontSize=18, leading=22, textColor=colors.black, spaceAfter=8)
    h2 = ParagraphStyle("h2", parent=styles["Heading2"], fontSize=12, leading=14, textColor=colors.HexColor(ORANGE), spaceBefore=8, spaceAfter=6)
    body = ParagraphStyle("body", parent=styles["BodyText"], fontSize=9.4, leading=12, textColor=colors.black)
    small = ParagraphStyle("small", parent=styles["BodyText"], fontSize=8, leading=10, textColor=colors.HexColor("#444444"))

    story = []
    if os.path.exists(LOGO_PATH):
        story.append(RLImage(LOGO_PATH, width=52 * mm, height=14 * mm))
        story.append(Spacer(1, 4))
    story.append(Paragraph(f"{symbol.replace('.NS','')} | {timeframe} | {datetime.now().strftime('%Y-%m-%d %H:%M %Z')}", small))
    story.append(Paragraph("Nifty Sniper Research Report", title_style))

    story.append(Paragraph("01 · Signal Output", h2))
    summary_data = [
        ["Signal", signal_pack["signal"], "Score", f"{signal_pack['score']}/{signal_pack['max_score']}"],
        ["Expected Move", f"{kronos_pack['expected_move']:+.2f}%", "Target Price", f"{kronos_pack['predicted_close']:.2f}"],
    ]
    table = Table(summary_data, colWidths=[32 * mm, 48 * mm, 32 * mm, 48 * mm])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#D5D5D5")),
        ("TEXTCOLOR", (0, 0), (-1, -1), colors.black),
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#FFF4E8")),
        ("BACKGROUND", (0, 1), (-1, 1), colors.HexColor("#FAFAFA")),
        ("PADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(table)
    story.append(Spacer(1, 8))

    story.append(Paragraph("02 · Market Structure Chart", h2))
    story.append(RLImage(price_chart, width=180 * mm, height=72 * mm))
    story.append(Spacer(1, 8))

    story.append(Paragraph("03 · Signal Components", h2))
    comp_rows = [["Component", "Score", "Detail"]]
    for name, item in components.items():
        shown = f"{item['score']}/{item['max']}" if item['max'] > 0 else str(item['score'])
        comp_rows.append([name, shown, item['detail']])
    comp_table = Table(comp_rows, colWidths=[62 * mm, 22 * mm, 86 * mm])
    comp_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#FFF4E8")),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#D8D8D8")),
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("PADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(comp_table)
    story.append(Spacer(1, 8))

    story.append(Paragraph("04 · Market Structure", h2))
    ms_rows = [["Metric", "Reading"]] + [list(r) for r in structure_rows]
    ms_table = Table(ms_rows, colWidths=[58 * mm, 112 * mm])
    ms_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#FFF4E8")),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#D8D8D8")),
        ("PADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(ms_table)
    story.append(Spacer(1, 8))

    story.append(Paragraph("05 · Timing Quality", h2))
    tq_rows = [[k, v] for k, v in timing_metrics.items()]
    tq_table = Table(tq_rows, colWidths=[52 * mm, 118 * mm])
    tq_table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#D8D8D8")),
        ("PADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(Paragraph(timing_label, body))
    story.append(Spacer(1, 5))
    story.append(tq_table)
    story.append(Spacer(1, 8))

    story.append(Paragraph("06 · Kronos Forecast", h2))
    story.append(RLImage(kronos_chart, width=180 * mm, height=72 * mm))
    story.append(Spacer(1, 8))

    story.append(Paragraph("07 · Kronos Summary", h2))
    card_items = list(kronos_pack["cards"].items())
    grid = [card_items[:2], card_items[2:4], card_items[4:6]]
    kronos_grid = []
    for row in grid:
        kronos_grid.append([f"{row[0][0]}\n{row[0][1]}", f"{row[1][0]}\n{row[1][1]}"])
    kg_table = Table(kronos_grid, colWidths=[85 * mm, 85 * mm], rowHeights=[16 * mm] * 3)
    kg_table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#D8D8D8")),
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#FCFCFC")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("PADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(kg_table)
    story.append(Spacer(1, 6))
    story.append(Paragraph("Kronos Bull Case", body))
    story.append(Paragraph(kronos_pack["bull_case"], body))
    story.append(Spacer(1, 4))
    story.append(Paragraph("Kronos Bear Case", body))
    story.append(Paragraph(kronos_pack["bear_case"], body))
    story.append(Spacer(1, 8))

    story.append(Paragraph("08 · AI Lab Debate", h2))
    for role, text in ai_lab_pack.items():
        story.append(Paragraph(f"<b>{role}</b>", body))
        story.append(Paragraph(text, body))
        story.append(Spacer(1, 4))

    story.append(Spacer(1, 8))
    story.append(Paragraph("Data via Yahoo Finance. Signals are not financial advice. Past performance does not guarantee future results.", small))
    doc.build(story)
    return buf.getvalue()



# ---------- UI ----------
def section_divider(num: str, title: str, dot_color: str = ORANGE):
    st.markdown(
        f"""
        <div class='section-wrap'>
          <div class='section-line'></div>
          <div class='section-center'><span class='section-dot' style='color:{dot_color}'>●</span>&nbsp;&nbsp;{num} — {title}&nbsp;&nbsp;<span class='section-dot' style='color:{dot_color}'>●</span></div>
          <div class='section-line'></div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def compact_metric_card(label: str, value: str, sub: str = "", accent: str = TEXT):
    st.markdown(
        f"""
        <div class='metric-card'>
          <div class='metric-kicker'>{label}</div>
          <div class='metric-main' style='color:{accent};'>{value}</div>
          <div class='metric-sub'>{sub}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


st.markdown(
    f"""
    <style>
    :root {{
      --bg: {BLACK};
      --card: #07101f;
      --card2: #091425;
      --muted: #93A1B5;
      --line: #1A2740;
      --orange: {ORANGE};
      --orange2: {ORANGE_2};
      --text: {TEXT};
      --green: {GREEN};
      --red: {RED};
    }}
    .stApp {{
      background: radial-gradient(circle at top, #010c1f 0%, #000814 38%, #000000 100%);
      color: var(--text);
    }}
    .block-container {{
      max-width: 1500px;
      padding-top: 0.65rem;
      padding-bottom: 1.8rem;
    }}
    p, li, div {{ font-size: 13px; }}
    h1,h2,h3,h4 {{ letter-spacing: 0.02em; }}
    [data-testid="stAppViewContainer"] {{ background: transparent; }}
    [data-testid="stHeader"] {{ background: transparent; }}

    .top-sub {{ text-align:center; color:#8e99ab; font-size:11px; font-weight:700; letter-spacing:0.26em; text-transform:uppercase; margin: 4px 0 18px; }}

    div[data-baseweb="radio"] > div {{ gap: 18px; justify-content:center; flex-wrap: wrap; margin-bottom: 8px; }}
    div[role="radiogroup"] label {{
        background: rgba(11,22,44,0.92);
        border: 1.3px solid #375074;
        border-radius: 15px;
        min-width: 118px;
        height: 60px;
        display:flex !important;
        align-items:center;
        justify-content:center;
        box-shadow: inset 0 0 0 1px rgba(255,255,255,0.03);
        transition: all .18s ease;
        padding: 0 16px !important;
    }}
    div[role="radiogroup"] label p {{ font-size: 11px !important; font-weight: 800 !important; color: #F7FAFF !important; letter-spacing: 0.05em; }}
    div[role="radiogroup"] label[data-selected="true"] {{
        border-color:#ff8c00;
        box-shadow: 0 0 0 1px rgba(255,140,0,.30), 0 0 16px rgba(255,140,0,.18);
    }}

    .stTextInput label, .stRadio label[data-testid="stWidgetLabel"] {{ display:none !important; }}
    .stTextInput > div > div > input {
        background: linear-gradient(180deg, #0a1530 0%, #081120 100%) !important;
        color: #ffffff !important;
        border-radius: 18px !important;
        border: 2px solid rgba(241,244,251,0.88) !important;
        box-shadow: 0 0 0 2px rgba(255,255,255,0.06) inset !important;
        padding: 0 20px !important;
        height: 72px !important;
        min-height: 72px !important;
        line-height: 72px !important;
        font-size: 28px !important;
        font-weight: 800 !important;
        text-align: center !important;
        letter-spacing: 0.05em !important;
        vertical-align: middle !important;
    }
    div[data-testid="stTextInput"] input::placeholder {
        color: #d9deea !important;
        opacity: 0.9 !important;
    }
    div[data-testid="stButton"] button {
        height: 60px !important;
        border-radius: 16px !important;
        background: linear-gradient(90deg, #ff8c00, #ff6a00) !important;
        color: white !important;
        border: 0 !important;
        font-size: 16px !important;
        font-weight: 700 !important;
        letter-spacing: 0.10em !important;
        box-shadow: 0 8px 18px rgba(255,106,0, 0.20);
        margin-bottom: 6px !important;
    }
    div[data-testid="stDownloadButton"] button {{
        height: 58px !important;
        border-radius: 16px !important;
        background: linear-gradient(180deg, #0b1630 0%, #081120 100%) !important;
        color: #d4dce8 !important;
        border: 1px solid #223453 !important;
        font-size: 17px !important;
        font-weight: 700 !important;
    }}

    .section-wrap {{ display:flex; align-items:center; gap:16px; margin: 28px 0 14px; }}
    .section-line {{ flex:1; height:1px; background: linear-gradient(90deg, rgba(28,43,72,0.95), rgba(28,43,72,0.12)); }}
    .section-center {{ color:#a6afc0; font-size:11px; letter-spacing:0.32em; font-weight:800; text-transform:uppercase; white-space:nowrap; }}
    .section-dot {{ font-size:13px; }}

    .hero-signal {{
        background: linear-gradient(90deg, rgba(49,20,0,0.92), rgba(64,28,0,0.95));
        border: 1.5px solid rgba(255,140,0,0.9);
        border-radius: 28px;
        padding: 34px 28px 30px;
        text-align:center;
        box-shadow: inset 0 0 0 1px rgba(255,153,0,0.08);
    }}
    .hero-head {{ color:#b2bccd; font-size:11px; font-weight:800; letter-spacing:0.25em; text-transform:uppercase; }}
    .hero-word {{ color:#ff9d00; font-size:60px; line-height:0.95; font-weight:900; margin: 18px 0 8px; letter-spacing:0.015em; }}
    .hero-score {{ color:#ff9d00; font-size:24px; font-weight:900; margin-bottom: 14px; }}
    .hero-strip {{ display:flex; justify-content:center; gap:26px; flex-wrap:wrap; color:#aeb7c8; font-size:13px; letter-spacing:0.10em; text-transform:uppercase; font-weight:700; }}
    .hero-strip .pos {{ color:#18d08e; font-weight:900; }}
    .hero-strip .down {{ color:#ff8585; font-weight:900; }}

    .component-grid {{ display:grid; grid-template-columns: 160px minmax(200px,1fr) 56px 220px; gap: 10px; align-items:center; margin-bottom: 10px; }}
    .component-name {{ font-size:12px; font-weight:800; color:#E4E9F3; letter-spacing:0.02em; }}
    .component-rail {{ height:11px; background:#071733; border-radius:999px; overflow:hidden; }}
    .component-fill {{ height:11px; border-radius:999px; }}
    .component-score {{ font-size:12px; font-weight:900; text-align:right; color:#F3F6FB; letter-spacing:0.02em; }}
    .component-detail {{ color:#95A2B7; font-size:11px; text-align:left; }}

    [data-testid="stImage"] img {{ border-radius: 8px; }}

    .table-shell {{ border: 1px solid rgba(20,34,58,.70); overflow:hidden; margin-top: 4px; }}
    .table-row {{ display:grid; grid-template-columns: 1.05fr 1.35fr; border-bottom:1px solid rgba(20,34,58,.70); }}
    .table-row:last-child {{ border-bottom:none; }}
    .table-key, .table-val {{ padding: 14px 18px; font-size: 13px; }}
    .table-key {{ color:#98A5B8; background: rgba(3,11,25,.58); font-weight:700; }}
    .table-val {{ color:#F5F7FB; font-weight:800; }}
    .up {{ color:#18d08e; }}
    .down {{ color:#ff7b7b; }}

    .metric-card {{ background: linear-gradient(180deg, #081530 0%, #071224 100%); border:1px solid #203659; border-radius: 22px; padding: 22px 22px; min-height: 158px; }}
    .metric-kicker {{ color:#AAB5C8; font-size:11px; letter-spacing:0.22em; text-transform:uppercase; font-weight:800; margin-bottom: 20px; }}
    .metric-main {{ color:#F7FAFF; font-size:24px; font-weight:900; line-height:1.05; }}
    .metric-sub {{ color:#93A1B5; font-size:12px; margin-top: 14px; line-height:1.45; }}

    .debate-card {{ border-radius: 22px; padding: 22px 22px 20px; min-height: 230px; border:1px solid transparent; }}
    .debate-green {{ background: rgba(0,72,28,.42); border-color: rgba(0,193,108,.62); }}
    .debate-red {{ background: rgba(73,0,0,.42); border-color: rgba(234,76,76,.62); }}
    .debate-violet {{ background: rgba(35,17,86,.34); border-color: rgba(136,93,255,.62); }}
    .debate-title {{ color:#f5f7fb; font-size:14px; font-weight:900; margin: 12px 0 12px; }}
    .debate-kicker {{ font-size:11px; letter-spacing:0.22em; text-transform:uppercase; font-weight:800; }}
    .debate-body {{ color:#D7DDE8; font-size:14px; line-height:1.6; }}
    .verdict-pill {{ display:inline-block; margin-top:16px; background:#2138a8; color:#d7e0ff; border-radius:999px; padding:7px 14px; font-size:12px; font-weight:800; }}
    .watch-pill {{ display:inline-block; background: rgba(255,160,0,.12); color:#ffb21f; border-radius:999px; padding:7px 14px; font-size:12px; font-weight:800; float:right; }}

    .export-shell {{ max-width: 700px; margin: 0 auto; }}

    @media (max-width: 1100px) {{
      .component-grid {{ grid-template-columns: 1fr; gap:6px; }}
      .hero-word {{ font-size:42px; }}
      .hero-strip {{ gap:14px; font-size:12px; }}
      .table-row {{ grid-template-columns: 1fr; }}
    }}
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown("<div class='top-sub'>REAL-TIME · MULTI-FACTOR · AI-POWERED</div>", unsafe_allow_html=True)

timeframe = st.radio("Timeframe", ["1m", "5m", "15m", "30m", "1H", "4H", "1D"], index=1, horizontal=True, label_visibility="collapsed")

c1, c2 = st.columns([6.2, 1.5], vertical_alignment="bottom")
with c1:
    stock_input = st.text_input("Ticker", value="BTC" if False else "", placeholder="RELIANCE", label_visibility="collapsed")
with c2:
    analyse = st.button("ANALYSE", use_container_width=True)

if analyse:
    symbol = symbol_from_input(stock_input)
    if not symbol:
        st.error("Enter a valid NSE stock symbol first.")
        st.stop()

    with st.spinner("Pulling market data and building the signal stack..."):
        raw_df, info = fetch_data(symbol, timeframe)
        if raw_df is None or raw_df.empty or len(raw_df) < 60:
            st.error("Not enough data returned for this symbol/timeframe. Try another stock or a higher timeframe.")
            st.stop()
        benchmark = fetch_benchmark(timeframe)
        df = enrich_df(raw_df)
        signal_pack = compute_signal(df, benchmark)
        structure_rows, trend_state = market_structure(df, signal_pack)
        timing_label, timing_metrics = timing_quality(df)
        kronos_pack = kronos_forecast(df, timeframe)
        ai_pack = ai_lab(signal_pack, trend_state, timing_label, kronos_pack, df)
        price_chart = make_price_chart(df, symbol, timeframe)
        kronos_chart_dark = make_forecast_chart(df, kronos_pack, symbol, timeframe, white=False)
        kronos_chart_white = make_forecast_chart(df, kronos_pack, symbol, timeframe, white=True)

        recent = df.tail(80).copy()
        ap = [
            mpf.make_addplot(recent["EMA20"], color="#00c2a0", width=1.45),
            mpf.make_addplot(recent["EMA50"], color="#7b86ff", width=1.35),
            mpf.make_addplot(recent["EMA200"], color="#f0a04b", width=1.35),
            mpf.make_addplot(recent["BB_UPPER"], color="#8ea0bf", width=0.9, linestyle="--"),
            mpf.make_addplot(recent["BB_LOWER"], color="#8ea0bf", width=0.9, linestyle="--"),
        ]
        style_white = mpf.make_mpf_style(
            base_mpf_style="classic",
            facecolor="white",
            figcolor="white",
            edgecolor="#DDDDDD",
            gridcolor="#E5E5E5",
            gridstyle="-",
            marketcolors=mpf.make_marketcolors(
                up="#16d6a4",
                down="#ff6b6b",
                edge={"up": "#16d6a4", "down": "#ff6b6b"},
                wick={"up": "#16d6a4", "down": "#ff6b6b"},
                volume={"up": "#16d6a4", "down": "#ff6b6b"},
                ohlc="inherit",
            ),
            rc={"axes.labelcolor": "black", "xtick.color": "#667085", "ytick.color": "#667085", "text.color": "black", "font.size": 9},
        )
        price_chart_white = NamedTemporaryFile(delete=False, suffix=".png").name
        mpf.plot(
            recent,
            type="candle",
            style=style_white,
            addplot=ap,
            volume=False,
            figsize=(10, 3),
            tight_layout=True,
            xrotation=0,
            datetime_format="%H:%M",
            title=f"{symbol} · {timeframe} · Market Structure",
            savefig=dict(fname=price_chart_white, dpi=150, bbox_inches="tight", pad_inches=0.05),
        )

        pdf_bytes = make_pdf(
            symbol,
            timeframe,
            signal_pack,
            signal_pack["components"],
            structure_rows,
            timing_label,
            timing_metrics,
            kronos_pack,
            kronos_chart_white,
            price_chart_white,
            ai_pack,
        )

    row = df.iloc[-1]
    timestamp_text = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')

    section_divider("01", "Signal Output", ORANGE)
    change_cls = "pos" if row['DAY_CHANGE_PCT'] >= 0 else "down"
    st.markdown(
        f"""
        <div class='hero-signal'>
          <div class='hero-head'>{symbol.replace('.NS','')} • {timeframe} • {timestamp_text}</div>
          <div class='hero-word'>{signal_pack['signal']}</div>
          <div class='hero-score'>{signal_pack['score']} / {signal_pack['max_score']}</div>
          <div class='hero-strip'>
            <span>CLOSE {fmt_num(row['Close'],2)}</span>
            <span>•</span>
            <span class='{change_cls}'>{row['DAY_CHANGE_PCT']:+.2f}%</span>
            <span>•</span>
            <span>VOL {fmt_num(row['RVOL'],1)}×</span>
            <span>•</span>
            <span>RSI {fmt_num(row['RSI14'],0)}</span>
            <span>•</span>
            <span>ADX {fmt_num(row['ADX14'],0)}</span>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    section_divider("02", "Signal Components", "#7f8cff")
    component_colors = [ORANGE, ORANGE, ORANGE, "#c084fc", "#ffb454", "#ff7f7f"]
    for idx, (name, item) in enumerate(signal_pack["components"].items()):
        label_map = {'V - Volume Strength':'V Volume','P - Price Expansion':'P Momentum','R - Position in Range':'R Range Pos','T - Trend Alignment':'T Trend','RS - Relative Strength':'RS Strength','X - Risk Penalty':'X Risk'}
        label = label_map.get(name, name.replace(" - ", " "))
        pct = 0 if item["max"] <= 0 else max(0, min(100, int(item["score"] / item["max"] * 100)))
        shown = f"{int(item['score'])}/{int(item['max'])}" if item["max"] > 0 else f"{item['score']}"
        color = component_colors[idx % len(component_colors)]
        st.markdown(
            f"""
            <div class='component-grid'>
              <div class='component-name'>{label}</div>
              <div class='component-rail'><div class='component-fill' style='width:{pct}%; background:{color};'></div></div>
              <div class='component-score'>{shown}</div>
              <div class='component-detail'>{item['detail']}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    section_divider("03", "Market Structure", "#39b6ff")
    st.image(price_chart, width=900)
    st.markdown("<div class='table-shell'>", unsafe_allow_html=True)
    for key, val in structure_rows:
        value_html = str(val)
        value_html = value_html.replace('(above)', "<span class='up'>▲ above</span>").replace('(below)', "<span class='down'>▼ below</span>")
        st.markdown(
            f"<div class='table-row'><div class='table-key'>{key}</div><div class='table-val'>{value_html}</div></div>",
            unsafe_allow_html=True,
        )
    st.markdown("</div>", unsafe_allow_html=True)

    section_divider("04", "Timing Quality", ORANGE)
    tq_cols = st.columns(3)
    timing_subs = {
        "RSI 14": "Neutral" if row['RSI14'] < 60 else "Firm" if row['RSI14'] < 70 else "Hot",
        "ADX 14": "TRENDING" if row['ADX14'] >= 20 else "SOFT",
        "ATR 14": f"{(row['ATR14']/row['Close'])*100:.2f}% of price",
        "+DI / -DI": "Bulls in control" if row['PLUS_DI'] > row['MINUS_DI'] else "Bears in control",
        "Rel Volume": "Normal" if row['RVOL'] < 1.5 else "Elevated",
        "ATR Move": "Strong" if row['ATR_MOVE'] > 1 else "Weak" if row['ATR_MOVE'] < 0.8 else "Building",
    }
    timing_accents = {
        "RSI 14": TEXT,
        "ADX 14": GREEN if row['ADX14'] >= 20 else TEXT,
        "ATR 14": TEXT,
        "+DI / -DI": GREEN if row['PLUS_DI'] > row['MINUS_DI'] else '#ff8a8a',
        "Rel Volume": TEXT,
        "ATR Move": TEXT,
    }
    for idx, (k, v) in enumerate(timing_metrics.items()):
        with tq_cols[idx % 3]:
            compact_metric_card(k, v.split(' (')[0] if k == 'ATR 14' else v, timing_subs.get(k, ''), timing_accents.get(k, TEXT))

    section_divider("05", "Kronos AI Forecast", "#8f56ff")
    st.image(kronos_chart_dark, width=900)
    cards = list(kronos_pack["cards"].items())
    kcols = st.columns(3)
    for idx, (k, v) in enumerate(cards):
        with kcols[idx % 3]:
            sub = ""
            accent = TEXT
            if k == "AI Forecast":
                sub = f"AI expects price to go {'up' if kronos_pack['direction']=='UP' else 'down'} over the next {kronos_pack['horizon']} candles"
                accent = GREEN if kronos_pack['direction']=='UP' else '#ff8a8a'
            elif k == "Expected Move":
                sub = f"{('Gaining' if kronos_pack['expected_move'] >= 0 else 'Losing')} {abs(kronos_pack['expected_move']):.2f}% from where it is now"
                accent = GREEN if kronos_pack['expected_move'] >= 0 else '#ff8a8a'
            elif k == "Price Range":
                sub = f"{kronos_pack['trough']:.2f} to {kronos_pack['peak']:.2f}"
            elif k == "Momentum":
                sub = f"{kronos_pack['bull_pct']:.0f}% of forecast candles close green"
                accent = ORANGE
            elif k == "Target Price":
                sub = f"Where AI thinks price lands after {kronos_pack['horizon']} candles"
            elif k == "Trade Quality":
                sub = "Favorable reward/risk" if kronos_pack['trade_quality'] in ['High', 'Moderate'] else "Avoid — bad odds"
                accent = '#ff8a8a' if kronos_pack['trade_quality'] == 'Cautious' else TEXT
            compact_metric_card(k, v, sub, accent)
    b1, b2 = st.columns(2)
    with b1:
        st.markdown(
            f"""
            <div class='debate-card debate-green'>
              <div class='debate-kicker' style='color:#19d38d;'>🐂 Bull Case <span class='watch-pill'>WATCH</span></div>
              <div class='debate-body' style='margin-top:28px;'>{kronos_pack['bull_case']}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with b2:
        st.markdown(
            f"""
            <div class='debate-card debate-red'>
              <div class='debate-kicker' style='color:#ff8787;'>🐻 Bear Case <span class='watch-pill'>WATCH</span></div>
              <div class='debate-body' style='margin-top:28px;'>{kronos_pack['bear_case']}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    section_divider("06", "AI Lab", "#ad78ff")
    cols = st.columns(2)
    ai_meta = [
        ("Bull", "🐂 Bull Case", "Alex — Long Desk", "debate-green", "#19d38d", "HOLD"),
        ("Bear", "🐻 Bear Case", "Sam — Short Desk", "debate-red", "#ff8787", "HOLD"),
        ("Risk Manager", "🛡 Risk Manager", "Jordan — Risk", "debate-violet", "#8f9dff", "HOLD"),
        ("CIO", "◉ CIO Verdict", "Morgan — CIO", "debate-violet", "#d199ff", "WATCHLIST"),
    ]
    for idx, (key, kicker, title, klass, kcolor, verdict) in enumerate(ai_meta):
        with cols[idx % 2]:
            st.markdown(
                f"""
                <div class='debate-card {klass}' style='margin-bottom:18px;'>
                  <div class='debate-kicker' style='color:{kcolor};'>{kicker}</div>
                  <div class='debate-title'>{title}</div>
                  <div class='debate-body'>{ai_pack[key]}</div>
                  <div class='verdict-pill'>{verdict}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    section_divider("07", "Export", "#5c6d86")
    st.markdown("<div class='export-shell'>", unsafe_allow_html=True)
    st.download_button(
        label="⇩ Download Report (PDF)",
        data=pdf_bytes,
        file_name=f"{symbol.replace('.NS','')}_{timeframe}_nifty_sniper_report.pdf",
        mime="application/pdf",
        use_container_width=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)
    st.caption("Data via Yahoo Finance. Signals are not financial advice. Past performance does not guarantee future results.")
