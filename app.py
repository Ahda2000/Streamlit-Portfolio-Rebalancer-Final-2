import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import warnings
import requests
import xml.etree.ElementTree as ET
import time
warnings.filterwarnings('ignore')

st.set_page_config(
    page_title="Portfolio Allocator",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Playfair+Display:wght@700;900&family=DM+Sans:wght@300;400;500&display=swap');
:root {
    --bg: #f7f5f2; --surface: #ffffff; --surface2: #f0ede8;
    --border: #d8d2c8; --gold: #8a6f2e; --gold-dim: #b8962e;
    --green: #2e7d52; --red: #c0392b; --yellow: #b8860b;
    --text: #1a1a1a; --text-dim: #6b6560;
}
html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; background-color: var(--bg); color: var(--text); }
.stApp { background-color: var(--bg); }
h1, h2, h3 { font-family: 'Playfair Display', serif; }
.header-block { border-left: 3px solid var(--gold); padding: 0.5rem 0 0.5rem 1.2rem; margin-bottom: 2rem; }
.header-block h1 { font-size: 2.4rem; font-weight: 900; color: var(--text); margin: 0; letter-spacing: -0.5px; }
.header-block p { font-family: 'DM Mono', monospace; font-size: 0.78rem; color: var(--text-dim); margin: 0.3rem 0 0 0; letter-spacing: 0.05em; }
.metric-card { background: var(--surface); border: 1px solid var(--border); border-radius: 8px; padding: 1.2rem 1.4rem; margin-bottom: 1rem; }
.metric-label { font-family: 'DM Mono', monospace; font-size: 0.68rem; color: var(--text-dim); letter-spacing: 0.1em; text-transform: uppercase; margin-bottom: 0.3rem; }
.metric-value { font-family: 'DM Mono', monospace; font-size: 1.5rem; font-weight: 500; color: var(--gold); }
.section-label { font-family: 'DM Mono', monospace; font-size: 0.7rem; letter-spacing: 0.15em; text-transform: uppercase; color: var(--gold-dim); margin: 2rem 0 0.8rem 0; padding-bottom: 0.4rem; border-bottom: 1px solid var(--border); }
.tag-invest { background: rgba(46,125,82,0.12); color: var(--green); border: 1px solid rgba(46,125,82,0.3); border-radius: 4px; padding: 2px 8px; font-family: 'DM Mono', monospace; font-size: 0.7rem; font-weight: 500; }
.tag-cash { background: rgba(184,134,11,0.10); color: var(--yellow); border: 1px solid rgba(184,134,11,0.3); border-radius: 4px; padding: 2px 8px; font-family: 'DM Mono', monospace; font-size: 0.7rem; }
div[data-testid="stButton"] button { background: var(--gold); color: #ffffff; border: none; font-family: 'DM Mono', monospace; font-size: 0.8rem; font-weight: 500; padding: 0.5rem 1.5rem; border-radius: 4px; }
.footer-note { font-family: 'DM Mono', monospace; font-size: 0.68rem; color: var(--text-dim); text-align: center; margin-top: 3rem; padding-top: 1rem; border-top: 1px solid var(--border); }
.pos { color: var(--green); font-family: 'DM Mono', monospace; }
.neg { color: var(--red); font-family: 'DM Mono', monospace; }
.neu { color: var(--text-dim); font-family: 'DM Mono', monospace; }
table { width: 100%; border-collapse: collapse; }
th { font-family: 'DM Mono', monospace; font-size: 0.68rem; letter-spacing: 0.08em; text-transform: uppercase; color: var(--text-dim); padding: 0.5rem 0.8rem; text-align: right; border-bottom: 2px solid var(--border); background: var(--surface2); }
th:first-child { text-align: left; }
td { font-family: 'DM Mono', monospace; font-size: 0.82rem; padding: 0.55rem 0.8rem; border-bottom: 1px solid var(--border); text-align: right; color: var(--text); }
td:first-child { text-align: left; font-weight: 500; }
tr:hover td { background: var(--surface2); }
.delta-buy { color: var(--green); font-family: 'DM Mono', monospace; }
.delta-sell { color: var(--red); font-family: 'DM Mono', monospace; }
.delta-hold { color: var(--text-dim); font-family: 'DM Mono', monospace; }
.ibkr-badge { display: inline-block; font-family: 'DM Mono', monospace; font-size: 0.65rem; color: var(--gold); border: 1px solid var(--gold); border-radius: 3px; padding: 1px 6px; margin-left: 6px; vertical-align: middle; }
.ibkr-warn { font-family: 'DM Mono', monospace; font-size: 0.72rem; color: var(--yellow); background: rgba(184,134,11,0.06); border: 1px solid rgba(184,134,11,0.25); border-radius: 6px; padding: 0.6rem 1rem; margin-bottom: 1rem; }
.band-note { font-family: 'DM Mono', monospace; font-size: 0.68rem; color: var(--text-dim); background: var(--surface2); border: 1px solid var(--border); border-radius: 4px; padding: 0.4rem 0.8rem; display: inline-block; margin-bottom: 0.8rem; }
</style>
""", unsafe_allow_html=True)

TICKERS = ["VGT","VHT","GLD","BLOK","BND","BNDX","BRK-B","PDBC","VB","VEA","VNQ","VNQI","VO","VV","VWO"]

TICKER_NAMES = {
    "VGT":"US Tech / AI","VHT":"Healthcare","GLD":"Gold","BLOK":"Crypto-Adjacent",
    "BND":"US Bonds","BNDX":"Intl Bonds","BRK-B":"Value / Compounding","PDBC":"Commodities",
    "VB":"US Small Cap","VEA":"Intl Developed","VNQ":"US Real Estate","VNQI":"Intl Real Estate",
    "VO":"US Mid Cap","VV":"US Large Cap","VWO":"Emerging Markets",
}

TURNOVER_BAND = 0.04  # 4 percentage points — only rebalance if drift exceeds this

# ── IBKR Flex Query ───────────────────────────────────────────────────────────

def fetch_ibkr_positions():
    """
    Fetch current positions from IBKR via Flex Web Service.
    Returns dict: {symbol: {"quantity": float, "position_value_usd": float}}
    or None if credentials missing / request fails.
    """
    try:
        token = st.secrets["IBKR_TOKEN"]
        query_id = st.secrets["IBKR_QUERY_ID"]
    except (KeyError, FileNotFoundError):
        return None, "IBKR credentials not found in secrets"

    base_url = "https://ndcdyn.interactivebrokers.com/AccountManagement/FlexWebService/SendRequest"
    download_url = "https://ndcdyn.interactivebrokers.com/AccountManagement/FlexWebService/GetStatement"

    headers = {"User-Agent": "Python/3.11"}

    # Step 1: Request the report
    try:
        r1 = requests.get(base_url, params={"t": token, "q": query_id, "v": "3"}, headers=headers, timeout=15)
        r1.raise_for_status()
    except Exception as e:
        return None, f"IBKR request failed: {e}"

    r1_text = r1.text

    try:
        root1 = ET.fromstring(r1_text)
        status = root1.findtext("Status")
        if status != "Success":
            error_msg = root1.findtext("ErrorMessage") or "Unknown error"
            with st.expander("🔍 IBKR debug — raw Step 1 response", expanded=True):
                st.code(r1_text)
            return None, f"IBKR: {error_msg}"
        reference_code = root1.findtext("ReferenceCode")
    except Exception as e:
        with st.expander("🔍 IBKR debug — raw Step 1 response", expanded=True):
            st.code(r1_text)
        return None, f"IBKR response parse error: {e}"

    # Step 2: Poll for the report
    time.sleep(5)
    r2_text = ""
    for attempt in range(5):
        try:
            r2 = requests.get(download_url, params={"t": token, "q": reference_code, "v": "3"}, headers=headers, timeout=15)
            r2.raise_for_status()
            r2_text = r2.text
            if "<FlexQueryResponse" in r2_text or "<OpenPosition" in r2_text:
                break
            time.sleep(4)
        except Exception as e:
            return None, f"IBKR download failed: {e}"
    else:
        with st.expander("🔍 IBKR debug — raw Step 2 response", expanded=True):
            st.code(r2_text)
        return None, "IBKR report not ready after retries — try refreshing"

    # Step 3: Parse XML positions
    try:
        root2 = ET.fromstring(r2_text)
        positions = {}
        for pos in root2.iter("OpenPosition"):
            symbol = pos.get("symbol", "").strip()
            currency = pos.get("currency", "USD")
            qty_str = pos.get("position") or pos.get("quantity", "0")
            val_str = pos.get("positionValue", "0")
            if not symbol:
                continue
            try:
                qty = float(qty_str)
                val = float(val_str)
            except ValueError:
                continue
            positions[symbol] = {
                "quantity": qty,
                "position_value_usd": val,
                "currency": currency,
            }
        return positions, None
    except Exception as e:
        with st.expander("🔍 IBKR debug — raw Step 2 response", expanded=True):
            st.code(r2_text)
        return None, f"IBKR XML parse error: {e}"


@st.cache_data(ttl=3600)
def fetch_data():
    end = datetime.today()
    start = end - timedelta(days=420)
    closes = {}
    errors = {}
    for ticker in TICKERS:
        try:
            raw = yf.download(ticker, start=start, end=end, auto_adjust=True, progress=False)
            if raw.empty:
                errors[ticker] = "Empty response"
                continue
            if isinstance(raw.columns, pd.MultiIndex):
                col = raw["Close"].iloc[:, 0]
            else:
                col = raw["Close"]
            closes[ticker] = col
        except Exception as e:
            errors[ticker] = str(e)
    return pd.DataFrame(closes), errors

@st.cache_data(ttl=3600)
def fetch_fx():
    try:
        fx = yf.Ticker("USDSGD=X")
        hist = fx.history(period="5d")
        if not hist.empty:
            return round(hist["Close"].iloc[-1], 4)
    except:
        pass
    return None

def compute_metrics(close_df):
    results = {}
    for ticker in TICKERS:
        if ticker not in close_df.columns:
            continue
        series = close_df[ticker].dropna()
        if len(series) < 210:
            continue
        series = series.iloc[-253:]
        price_today = float(series.iloc[-1])
        # ── FIX: use last 200 days only for the 200D SMA ──
        sma200 = float(series.iloc[-200:].mean())
        vs_200sma = (price_today - sma200) / sma200
        def perf(n):
            if len(series) < n + 1:
                return None
            return (price_today - float(series.iloc[-(n+1)])) / float(series.iloc[-(n+1)])
        p1, p6, p12 = perf(21), perf(126), perf(252)
        if any(x is None for x in [p1, p6, p12]):
            continue
        avg_perf = (p1 + p6 + p12) / 3
        daily_returns = series.pct_change().dropna()
        sum_sq = float((daily_returns ** 2).sum())
        volatility = sum_sq ** 0.5
        inverse_vol = 1 / volatility if volatility > 0 else 0
        results[ticker] = {
            "price": price_today, "sma200": sma200, "vs_200sma": vs_200sma,
            "perf_1m": p1, "perf_6m": p6, "perf_12m": p12, "avg_perf": avg_perf,
            "volatility": volatility, "inverse_vol": inverse_vol, "investable": vs_200sma > 0,
        }
    return results

def compute_allocation(metrics):
    ranked = sorted(metrics.items(), key=lambda x: x[1]["avg_perf"], reverse=True)
    top6 = ranked[:6]
    total_inv_vol = sum(d["inverse_vol"] for _, d in top6)
    allocation = []
    for ticker, d in top6:
        weight = d["inverse_vol"] / total_inv_vol if total_inv_vol > 0 else 1/6
        allocation.append({
            "ticker": ticker, "name": TICKER_NAMES.get(ticker, ""),
            "price": d["price"], "vs_200sma": d["vs_200sma"], "avg_perf": d["avg_perf"],
            "perf_1m": d["perf_1m"], "perf_6m": d["perf_6m"], "perf_12m": d["perf_12m"],
            "weight": weight, "investable": d["investable"],
        })
    return allocation, ranked

def compute_current_weights(ibkr_positions, allocation, portfolio_val_usd):
    """
    Given live IBKR positions and current prices, compute each holding's
    actual weight as a fraction of the total portfolio (USD basis).
    Returns dict: {ticker: actual_weight}
    """
    if not ibkr_positions or portfolio_val_usd <= 0:
        return {}
    weights = {}
    for row in allocation:
        ticker = row["ticker"]
        if ticker in ibkr_positions:
            pos_val = ibkr_positions[ticker]["position_value_usd"]
            weights[ticker] = pos_val / portfolio_val_usd
        else:
            weights[ticker] = 0.0
    return weights

def needs_rebalance(target_weight, actual_weight, band=TURNOVER_BAND):
    """Return True if drift exceeds the turnover band."""
    return abs(target_weight - actual_weight) > band

def color_pct(val, decimals=2):
    if val is None:
        return "<span class='neu'>—</span>"
    cls = "pos" if val > 0 else ("neg" if val < 0 else "neu")
    sign = "+" if val > 0 else ""
    return f"<span class='{cls}'>{sign}{val*100:.{decimals}f}%</span>"

def delta_cell(delta_usd, needs_trade):
    """Render a coloured delta USD cell, with HOLD if within turnover band."""
    if delta_usd is None:
        return "<span class='delta-hold'>—</span>"
    if not needs_trade:
        return "<span class='delta-hold'>≈ HOLD (within 4%)</span>"
    if abs(delta_usd) < 0.01:
        return "<span class='delta-hold'>≈ flat</span>"
    sign = "+" if delta_usd > 0 else ""
    cls = "delta-buy" if delta_usd > 0 else "delta-sell"
    label = "BUY" if delta_usd > 0 else "SELL"
    return f"<span class='{cls}'>{label} {sign}${abs(delta_usd):,.2f}</span>"

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="header-block">
    <h1>Portfolio Allocator</h1>
    <p>TREND-FOLLOWING · INVERSE VOLATILITY WEIGHTING · MONTHLY REBALANCE</p>
</div>
""", unsafe_allow_html=True)

col_refresh, col_date, col_fx, col_spacer = st.columns([1, 2, 2, 4])
with col_refresh:
    if st.button("↻ Refresh"):
        st.cache_data.clear()
        st.rerun()

# ── Load market data ──────────────────────────────────────────────────────────
with st.spinner("Fetching market data…"):
    try:
        close_df, fetch_errors = fetch_data()
        fx_rate = fetch_fx()
    except Exception as e:
        import traceback
        st.error(f"Fatal error: {e}")
        st.code(traceback.format_exc())
        st.stop()

metrics = compute_metrics(close_df)

if len(metrics) < 6:
    st.error(f"Only {len(metrics)} tickers have sufficient data (need at least 6). Try refreshing.")
    st.stop()

allocation, ranked = compute_allocation(metrics)

now = datetime.now().strftime("%d %b %Y, %H:%M")
with col_date:
    st.markdown(f'<div class="metric-card" style="padding:0.7rem 1rem;"><div class="metric-label">As of</div><div class="metric-value" style="font-size:1rem;">{now}</div></div>', unsafe_allow_html=True)
with col_fx:
    fx_display = f"{fx_rate:.4f}" if fx_rate else "N/A"
    st.markdown(f'<div class="metric-card" style="padding:0.7rem 1rem;"><div class="metric-label">USD / SGD</div><div class="metric-value" style="font-size:1rem;">{fx_display}</div></div>', unsafe_allow_html=True)

# ── Section 1: Monthly Allocation ─────────────────────────────────────────────
st.markdown('<div class="section-label">① Monthly Allocation — Top 6</div>', unsafe_allow_html=True)

rows = ""
for row in allocation:
    tag = "<span class='tag-invest'>INVEST</span>" if row["investable"] else "<span class='tag-cash'>CASH (USD)</span>"
    rows += f"<tr><td><strong>{row['ticker']}</strong></td><td style='color:#6b6560;font-size:0.75rem;'>{row['name']}</td><td>${row['price']:.2f}</td><td>{color_pct(row['vs_200sma'])}</td><td>{color_pct(row['perf_1m'])}</td><td>{color_pct(row['perf_6m'])}</td><td>{color_pct(row['perf_12m'])}</td><td>{color_pct(row['avg_perf'])}</td><td><strong style='color:#8a6f2e;'>{row['weight']*100:.2f}%</strong></td><td>{tag}</td></tr>"

st.markdown(f"<table><tr><th>Ticker</th><th>Asset Class</th><th>Price</th><th>vs 200D SMA</th><th>1M</th><th>6M</th><th>12M</th><th>Avg Perf</th><th>Weight</th><th>Status</th></tr>{rows}</table>", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)
bar_cols = st.columns(6)
for i, row in enumerate(allocation):
    color = "#2e7d52" if row["investable"] else "#b8860b"
    with bar_cols[i]:
        st.markdown(f'<div style="text-align:center;"><div style="font-family:DM Mono,monospace;font-size:0.75rem;color:#6b6560;">{row["ticker"]}</div><div style="font-family:DM Mono,monospace;font-size:1.1rem;font-weight:500;color:{color};">{row["weight"]*100:.1f}%</div><div style="background:#d8d2c8;border-radius:3px;height:4px;margin-top:4px;"><div style="background:{color};border-radius:3px;height:4px;width:{row["weight"]*100:.1f}%;"></div></div></div>', unsafe_allow_html=True)

# ── Section 2: Full Universe ──────────────────────────────────────────────────
st.markdown('<div class="section-label">② Full Universe — Momentum Screen</div>', unsafe_allow_html=True)

rows2 = ""
for rank, (ticker, d) in enumerate(ranked, 1):
    in_top6 = rank <= 6
    signal = "<span class='tag-invest'>▲ INVEST</span>" if d["investable"] else "<span class='tag-cash'>▼ CASH</span>"
    style = "" if in_top6 else "opacity:0.4;"
    rank_disp = f"<strong style='color:#8a6f2e;'>{rank}</strong>" if in_top6 else str(rank)
    rows2 += f"<tr style='{style}'><td>{rank_disp}</td><td><strong>{ticker}</strong></td><td style='color:#6b6560;font-size:0.75rem;'>{TICKER_NAMES.get(ticker,'')}</td><td>${d['price']:.2f}</td><td>${d['sma200']:.2f}</td><td>{color_pct(d['vs_200sma'])}</td><td>{color_pct(d['perf_1m'])}</td><td>{color_pct(d['perf_6m'])}</td><td>{color_pct(d['perf_12m'])}</td><td>{color_pct(d['avg_perf'])}</td><td>{''+signal if in_top6 else ''}</td></tr>"

st.markdown(f"<table><tr><th>Rank</th><th>Ticker</th><th>Asset Class</th><th>Price</th><th>200D SMA</th><th>vs 200D SMA</th><th>1M</th><th>6M</th><th>12M</th><th>Avg Perf</th><th>Signal</th></tr>{rows2}</table>", unsafe_allow_html=True)

# ── Section 3: Rebalancing Calculator ────────────────────────────────────────
st.markdown('<div class="section-label">③ Rebalancing Calculator</div>', unsafe_allow_html=True)

# Fetch IBKR positions
with st.spinner("Fetching IBKR positions…"):
    ibkr_positions, ibkr_error = fetch_ibkr_positions()

if ibkr_error:
    st.markdown(f'<div class="ibkr-warn">⚠ IBKR positions unavailable: {ibkr_error}. Delta column will show target units only.</div>', unsafe_allow_html=True)
elif ibkr_positions is not None and len(ibkr_positions) == 0:
    st.markdown('<p style="font-size:0.75rem;color:#6b6560;margin-bottom:0.5rem;">✓ IBKR connected <span class="ibkr-badge">LIVE</span> — no open positions yet.</p>', unsafe_allow_html=True)
elif ibkr_positions:
    pos_tickers = ", ".join(ibkr_positions.keys())
    st.markdown(f'<p style="font-size:0.75rem;color:#2e7d52;margin-bottom:0.5rem;">✓ IBKR positions loaded <span class="ibkr-badge">LIVE</span> — {len(ibkr_positions)} holdings: {pos_tickers}</p>', unsafe_allow_html=True)

st.markdown('<div class="band-note">Turnover band: 4% — positions within band show HOLD and are not traded this cycle.</div>', unsafe_allow_html=True)
st.markdown('<p style="font-size:0.85rem;color:#6b6560;margin-bottom:1rem;">Enter your current portfolio value in SGD to see target amounts and trade deltas per slot.</p>', unsafe_allow_html=True)

portfolio_val = st.number_input("Portfolio value (SGD)", min_value=0.0, value=10000.0, step=500.0, format="%.2f")

if portfolio_val > 0 and fx_rate:
    portfolio_val_usd = portfolio_val / fx_rate

    # Compute actual weights from live IBKR data
    actual_weights = compute_current_weights(ibkr_positions, allocation, portfolio_val_usd)

    rows3 = ""
    rebalance_needed = False

    for row in allocation:
        ticker = row["ticker"]
        target_w = row["weight"]
        actual_w = actual_weights.get(ticker, None)
        sgd_amt = target_w * portfolio_val
        usd_amt = sgd_amt / fx_rate
        tag = "<span class='tag-invest'>INVEST</span>" if row["investable"] else "<span class='tag-cash'>CASH</span>"

        # Actual weight display
        if actual_w is not None:
            actual_w_display = f"{actual_w*100:.2f}%"
            drift = target_w - actual_w
            trade_required = needs_rebalance(target_w, actual_w)
        else:
            actual_w_display = "<span class='neu'>—</span>"
            drift = None
            trade_required = True  # No position yet — always buy on first run

        drift_display = color_pct(drift) if drift is not None else "<span class='neu'>—</span>"

        if row["investable"]:
            if ibkr_positions and ticker in ibkr_positions:
                current_usd = ibkr_positions[ticker]["position_value_usd"]
                delta_usd = usd_amt - current_usd
                current_usd_display = f"${current_usd:,.2f}"
            else:
                current_usd = None
                delta_usd = usd_amt  # First buy — full target amount
                current_usd_display = "<span class='neu'>—</span>"

            if trade_required:
                rebalance_needed = True

            d_display = delta_cell(delta_usd, trade_required)
        else:
            # Cash slot
            current_usd_display = "<span class='neu'>—</span>"
            d_display = "<span class='delta-hold'>Keep as USD</span>"
            drift_display = "<span class='neu'>—</span>"

        rows3 += (
            f"<tr>"
            f"<td><strong>{ticker}</strong></td>"
            f"<td>{tag}</td>"
            f"<td style='color:#8a6f2e;'>{target_w*100:.2f}%</td>"
            f"<td>{actual_w_display}</td>"
            f"<td>{drift_display}</td>"
            f"<td>S${sgd_amt:,.2f}</td>"
            f"<td>${usd_amt:,.2f}</td>"
            f"<td>{current_usd_display}</td>"
            f"<td>{d_display}</td>"
            f"</tr>"
        )

    st.markdown(
        f"<table>"
        f"<tr><th>Ticker</th><th>Status</th><th>Target Wt</th><th>Actual Wt</th><th>Drift</th><th>SGD Target</th><th>USD Target</th><th>Current USD</th><th>Δ Trade (USD)</th></tr>"
        f"{rows3}"
        f"</table>",
        unsafe_allow_html=True
    )

    invested = sum(r["weight"] for r in allocation if r["investable"]) * portfolio_val
    cash_usd = sum(r["weight"] for r in allocation if not r["investable"]) * portfolio_val
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f'<div class="metric-card" style="margin-top:1rem;"><div class="metric-label">To Invest (USD ETFs)</div><div class="metric-value" style="color:#2e7d52;">S${invested:,.2f}</div></div>', unsafe_allow_html=True)
    with c2:
        st.markdown(f'<div class="metric-card" style="margin-top:1rem;"><div class="metric-label">To Keep as USD Cash</div><div class="metric-value" style="color:#b8860b;">S${cash_usd:,.2f}</div></div>', unsafe_allow_html=True)
    with c3:
        rebal_label = "REBALANCE THIS CYCLE" if rebalance_needed else "NO TRADE — ALL WITHIN BAND"
        rebal_color = "#c0392b" if rebalance_needed else "#2e7d52"
        st.markdown(f'<div class="metric-card" style="margin-top:1rem;"><div class="metric-label">Action</div><div class="metric-value" style="color:{rebal_color};font-size:1rem;">{rebal_label}</div></div>', unsafe_allow_html=True)

st.markdown('<div class="footer-note">Data via Yahoo Finance · Positions via IBKR Flex Web Service · 200D SMA · 4% turnover band · Not financial advice · Built for personal use</div>', unsafe_allow_html=True)
