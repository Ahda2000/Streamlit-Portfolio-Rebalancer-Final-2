"""
ETF Scout — Agentic Screener
pages/screener.py
Supabase persistence: screener_runs table
"""

import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import json
import anthropic
from datetime import datetime, timezone
from supabase import create_client

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(page_title="ETF Scout", page_icon="🔭", layout="wide")

# ── Fonts & palette ────────────────────────────────────────────────────────────
st.markdown("""
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600&family=DM+Mono:wght@400;500&family=Playfair+Display:wght@400;600&display=swap" rel="stylesheet">
<style>
:root {
    --bg:       #f7f5f2;
    --surface:  #ffffff;
    --gold:     #8a6f2e;
    --gold-lt:  #b8952a;
    --ink:      #1a1a1a;
    --muted:    #6b6459;
    --border:   #e2ddd7;
    --green:    #2e7d32;
    --red:      #c62828;
}
html, body, [data-testid="stAppViewContainer"] { background: var(--bg) !important; }
[data-testid="stSidebar"] { background: #f0ede8 !important; border-right: 1px solid var(--border); }
* { font-family: 'DM Sans', sans-serif; color: var(--ink); }
h1, h2, h3 { font-family: 'Playfair Display', serif; }
code, .mono { font-family: 'DM Mono', monospace; }
[data-testid="stButton"] button {
    background: var(--gold) !important;
    color: #fff !important;
    border: none !important;
    border-radius: 6px !important;
    font-weight: 500 !important;
    padding: 0.5rem 1.4rem !important;
}
[data-testid="stButton"] button:hover { background: var(--gold-lt) !important; }
.metric-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 1rem 1.2rem;
    margin-bottom: 0.5rem;
}
.rank-badge {
    display: inline-block;
    background: var(--gold);
    color: #fff;
    border-radius: 50%;
    width: 26px; height: 26px;
    text-align: center;
    line-height: 26px;
    font-size: 0.8rem;
    font-weight: 600;
    margin-right: 0.5rem;
}
.freshness-bar {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 0.45rem 1rem;
    font-size: 0.8rem;
    color: var(--muted);
    margin-bottom: 1.2rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}
.summary-box {
    background: var(--surface);
    border-left: 3px solid var(--gold);
    border-radius: 0 8px 8px 0;
    padding: 1rem 1.2rem;
    margin-bottom: 1.5rem;
    font-size: 0.92rem;
    line-height: 1.6;
}
.stRadio label { font-size: 0.85rem !important; }
</style>
""", unsafe_allow_html=True)

# ── Constants ──────────────────────────────────────────────────────────────────
TICKERS = ["VGT","VHT","GLD","BLOK","BND","BNDX","BRK-B","PDBC","VB","VEA","VNQ","VNQI","VO","VV","VWO"]
LOOKBACK_DAYS = 252  # ~1 trading year
MODEL = "claude-haiku-4-5-20251001"

# ── Supabase client ────────────────────────────────────────────────────────────
@st.cache_resource
def get_supabase():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

def load_history(limit: int = 10):
    """Load last N screener runs from Supabase."""
    try:
        sb = get_supabase()
        resp = sb.table("screener_runs") \
                 .select("id, created_at, label, summary, results") \
                 .order("created_at", desc=True) \
                 .limit(limit) \
                 .execute()
        return resp.data or []
    except Exception as e:
        st.warning(f"Could not load history: {e}")
        return []

def save_run(label: str, summary: dict, results: list):
    """Persist a completed screener run to Supabase."""
    try:
        sb = get_supabase()
        sb.table("screener_runs").insert({
            "label":   label,
            "summary": summary,
            "results": results,
        }).execute()
    except Exception as e:
        st.warning(f"Could not save run: {e}")

# ── Data fetching ──────────────────────────────────────────────────────────────
@st.cache_data(ttl=3600)
def fetch_metrics(tickers: list) -> pd.DataFrame:
    """Fetch price history and compute momentum + volatility metrics."""
    records = []
    for tkr in tickers:
        try:
            hist = yf.download(tkr, period="1y", progress=False, auto_adjust=True)
            if hist.empty or len(hist) < 30:
                continue
            closes = hist["Close"].squeeze()
            ret_1m = (closes.iloc[-1] / closes.iloc[-21] - 1) * 100 if len(closes) >= 21 else np.nan
            ret_3m = (closes.iloc[-1] / closes.iloc[-63] - 1) * 100 if len(closes) >= 63 else np.nan
            ret_6m = (closes.iloc[-1] / closes.iloc[-126] - 1) * 100 if len(closes) >= 126 else np.nan
            ret_1y = (closes.iloc[-1] / closes.iloc[0]  - 1) * 100
            daily_rets = closes.pct_change().dropna()
            vol_ann = daily_rets.std() * np.sqrt(252) * 100
            sharpe   = (daily_rets.mean() * 252) / (daily_rets.std() * np.sqrt(252)) if daily_rets.std() > 0 else np.nan
            price    = float(closes.iloc[-1])
            records.append({
                "Ticker":  tkr,
                "Price":   price,
                "1M %":    round(ret_1m, 2),
                "3M %":    round(ret_3m, 2),
                "6M %":    round(ret_6m, 2),
                "1Y %":    round(ret_1y, 2),
                "Vol(ann)%": round(vol_ann, 2),
                "Sharpe":  round(sharpe, 2),
            })
        except Exception:
            continue
    return pd.DataFrame(records)

# ── Momentum ranking ───────────────────────────────────────────────────────────
def rank_tickers(df: pd.DataFrame) -> pd.DataFrame:
    """Composite momentum score (weighted avg of 1M/3M/6M ranks) + inverse-vol weight."""
    df = df.copy().dropna(subset=["1M %","3M %","6M %","Vol(ann)%"])
    df["r1"] = df["1M %"].rank(ascending=True)
    df["r3"] = df["3M %"].rank(ascending=True)
    df["r6"] = df["6M %"].rank(ascending=True)
    df["MomScore"] = (0.5*df["r6"] + 0.3*df["r3"] + 0.2*df["r1"])
    df["MomRank"] = df["MomScore"].rank(ascending=False).astype(int)
    inv_vol = 1 / df["Vol(ann)%"]
    df["IVWeight%"] = (inv_vol / inv_vol.sum() * 100).round(2)
    return df.sort_values("MomRank").drop(columns=["r1","r3","r6","MomScore"])

# ── Claude analysis ────────────────────────────────────────────────────────────
def run_claude_analysis(df_ranked: pd.DataFrame) -> tuple[str, str]:
    """
    Returns (streaming_text, full_text).
    Calls Claude with ranked metrics; yields streamed response.
    """
    top5  = df_ranked.head(5)[["Ticker","1M %","3M %","6M %","1Y %","Vol(ann)%","Sharpe","IVWeight%"]].to_markdown(index=False)
    all_t = df_ranked[["Ticker","MomRank","1Y %","Vol(ann)%","IVWeight%"]].to_markdown(index=False)

    prompt = f"""You are a systematic ETF analyst. Based on the momentum and volatility metrics below, provide a concise investment-grade screener report.

TOP 5 BY MOMENTUM:
{top5}

FULL UNIVERSE RANKINGS:
{all_t}

Structure your response as:
1. **Market Regime Summary** (2–3 sentences on what the rankings reveal about current macro/sector conditions)
2. **Top Picks Rationale** (bullet per top-3 ticker: why it ranks well, any caveats)
3. **Risk Flags** (any tickers with momentum but excessive volatility, or tail risks)
4. **Portfolio Tilt Recommendation** (one paragraph: given inverse-vol weights, what posture does this suggest?)

Be direct, evidence-based, and concise. No disclaimers about not being a financial advisor."""

    client = anthropic.Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])
    full_text = ""
    placeholder = st.empty()

    with client.messages.stream(
        model=MODEL,
        max_tokens=900,
        messages=[{"role": "user", "content": prompt}]
    ) as stream:
        for text in stream.text_stream:
            full_text += text
            placeholder.markdown(
                f'<div class="summary-box">{full_text}▌</div>',
                unsafe_allow_html=True
            )

    placeholder.markdown(
        f'<div class="summary-box">{full_text}</div>',
        unsafe_allow_html=True
    )
    return full_text

# ── Render a completed run ─────────────────────────────────────────────────────
def render_run(run: dict):
    """Display a saved run (from history or freshly computed)."""
    created_at = run.get("created_at", "")
    label      = run.get("label", "")
    summary    = run.get("summary", {})
    results    = run.get("results", [])

    # Freshness bar
    if created_at:
        try:
            ts = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
            age_min = int((datetime.now(timezone.utc) - ts).total_seconds() / 60)
            age_str = f"{age_min}m ago" if age_min < 60 else f"{age_min//60}h {age_min%60}m ago"
        except Exception:
            age_str = created_at
        st.markdown(
            f'<div class="freshness-bar">🕐 Run: <strong>{label}</strong> &nbsp;·&nbsp; {age_str}</div>',
            unsafe_allow_html=True
        )

    # Claude summary
    analysis_text = summary.get("analysis", "")
    if analysis_text:
        st.markdown("### 🤖 Analysis")
        st.markdown(f'<div class="summary-box">{analysis_text}</div>', unsafe_allow_html=True)

    # Rankings table
    if results:
        st.markdown("### 📊 Rankings")
        df = pd.DataFrame(results)
        # Colour helpers
        def pct_color(val):
            try:
                v = float(val)
                return f"color: {'#2e7d32' if v >= 0 else '#c62828'}"
            except Exception:
                return ""

        display_cols = [c for c in ["Ticker","MomRank","1M %","3M %","6M %","1Y %","Vol(ann)%","Sharpe","IVWeight%"] if c in df.columns]
        styled = df[display_cols].style \
            .applymap(pct_color, subset=[c for c in ["1M %","3M %","6M %","1Y %"] if c in display_cols]) \
            .format({c: "{:.2f}" for c in display_cols if c not in ["Ticker","MomRank"]}) \
            .set_properties(**{"font-family": "DM Mono, monospace", "font-size": "0.85rem"})
        st.dataframe(styled, use_container_width=True, hide_index=True)

        # IVWeight bar chart
        st.markdown("### ⚖️ Inverse-Vol Weights")
        chart_df = df.set_index("Ticker")[["IVWeight%"]].sort_values("IVWeight%", ascending=False)
        st.bar_chart(chart_df)

# ── Sidebar history ────────────────────────────────────────────────────────────
def build_sidebar(history: list) -> int | None:
    """
    Renders sidebar history radio.
    Returns index into history list of selected run, or None if 'New Run'.
    """
    st.sidebar.markdown("## 🔭 ETF Scout")
    st.sidebar.markdown("---")

    if not history:
        st.sidebar.caption("No saved runs yet.")
        return None

    options = ["▶ New Run"] + [r.get("label", f"Run {i+1}") for i, r in enumerate(history)]
    choice = st.sidebar.radio("History (last 10)", options, index=0)

    if choice == "▶ New Run":
        return None
    idx = options.index(choice) - 1
    return idx

# ── Main ───────────────────────────────────────────────────────────────────────
def main():
    st.markdown("# 🔭 ETF Scout")
    st.markdown("*Momentum + inverse-volatility screener across the 15-ticker universe.*")
    st.markdown("---")

    history = load_history(10)
    selected_idx = build_sidebar(history)

    # ── Show historical run ──
    if selected_idx is not None:
        run = history[selected_idx]
        render_run(run)
        return

    # ── Show latest run by default (unless none exist) ──
    if history and "run_just_completed" not in st.session_state:
        st.info("Showing latest saved run. Click **Run Screener** to refresh.")
        render_run(history[0])

    # ── Run button ──
    st.markdown("### Run fresh screener")
    col1, col2 = st.columns([2, 1])
    with col1:
        run_label = st.text_input(
            "Label for this run",
            value=datetime.now().strftime("%Y-%m-%d %H:%M"),
            label_visibility="collapsed",
            placeholder="Label e.g. 2025-06-07 morning"
        )
    with col2:
        go = st.button("🚀 Run Screener", use_container_width=True)

    if go:
        st.session_state["run_just_completed"] = True
        with st.spinner("Fetching prices…"):
            df_raw = fetch_metrics(TICKERS)

        if df_raw.empty:
            st.error("Could not fetch price data. Try again later.")
            return

        df_ranked = rank_tickers(df_raw)

        st.markdown("### 🤖 Claude Analysis")
        analysis_text = run_claude_analysis(df_ranked)

        results_list = df_ranked.to_dict(orient="records")
        summary_dict = {"analysis": analysis_text, "generated_at": datetime.utcnow().isoformat()}

        save_run(
            label=run_label or datetime.now().strftime("%Y-%m-%d %H:%M"),
            summary=summary_dict,
            results=results_list,
        )

        # Render full run inline
        render_run({
            "created_at": datetime.now(timezone.utc).isoformat(),
            "label":      run_label,
            "summary":    summary_dict,
            "results":    results_list,
        })

        st.success("Run saved to history.")

if __name__ == "__main__":
    main()
