import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime
import anthropic
import json
import warnings
warnings.filterwarnings('ignore')

# ── Inherit styling from app.py ───────────────────────────────────────────────

st.set_page_config(
    page_title="ETF Scout — Portfolio Allocator",
    page_icon="🔭",
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
.section-label { font-family: 'DM Mono', monospace; font-size: 0.7rem; letter-spacing: 0.15em; text-transform: uppercase; color: var(--gold-dim); margin: 2rem 0 0.8rem 0; padding-bottom: 0.4rem; border-bottom: 1px solid var(--border); }
.metric-card { background: var(--surface); border: 1px solid var(--border); border-radius: 8px; padding: 1.2rem 1.4rem; margin-bottom: 1rem; }
.metric-label { font-family: 'DM Mono', monospace; font-size: 0.68rem; color: var(--text-dim); letter-spacing: 0.1em; text-transform: uppercase; margin-bottom: 0.3rem; }
.metric-value { font-family: 'DM Mono', monospace; font-size: 1.5rem; font-weight: 500; color: var(--gold); }
div[data-testid="stButton"] button { background: var(--gold); color: #ffffff; border: none; font-family: 'DM Mono', monospace; font-size: 0.8rem; font-weight: 500; padding: 0.5rem 1.5rem; border-radius: 4px; }
.pos { color: var(--green); font-family: 'DM Mono', monospace; }
.neg { color: var(--red); font-family: 'DM Mono', monospace; }
.neu { color: var(--text-dim); font-family: 'DM Mono', monospace; }
table { width: 100%; border-collapse: collapse; }
th { font-family: 'DM Mono', monospace; font-size: 0.68rem; letter-spacing: 0.08em; text-transform: uppercase; color: var(--text-dim); padding: 0.5rem 0.8rem; text-align: right; border-bottom: 2px solid var(--border); background: var(--surface2); }
th:first-child { text-align: left; }
td { font-family: 'DM Mono', monospace; font-size: 0.82rem; padding: 0.55rem 0.8rem; border-bottom: 1px solid var(--border); text-align: right; color: var(--text); }
td:first-child { text-align: left; font-weight: 500; }
tr:hover td { background: var(--surface2); }
.etf-card { background: var(--surface); border: 1px solid var(--border); border-radius: 8px; padding: 1.2rem 1.6rem; margin-bottom: 1rem; }
.etf-ticker { font-family: 'Playfair Display', serif; font-size: 1.3rem; font-weight: 700; color: var(--gold); }
.etf-name { font-family: 'DM Sans', sans-serif; font-size: 0.85rem; color: var(--text-dim); margin: 0.1rem 0 0.6rem 0; }
.badge { display: inline-block; font-family: 'DM Mono', monospace; font-size: 0.65rem; border-radius: 3px; padding: 2px 8px; margin-left: 6px; vertical-align: middle; font-weight: 500; }
.badge-pass { background: rgba(46,125,82,0.12); color: var(--green); border: 1px solid rgba(46,125,82,0.3); }
.badge-partial { background: rgba(184,134,11,0.10); color: var(--yellow); border: 1px solid rgba(184,134,11,0.3); }
.badge-watch { background: rgba(55,138,221,0.10); color: #185fa5; border: 1px solid rgba(55,138,221,0.3); }
.badge-fail { background: rgba(192,57,43,0.08); color: var(--red); border: 1px solid rgba(192,57,43,0.25); }
.ai-note { font-family: 'DM Sans', sans-serif; font-size: 0.83rem; color: var(--text-dim); background: var(--surface2); border-left: 2px solid var(--gold-dim); padding: 0.6rem 1rem; border-radius: 0 4px 4px 0; margin-top: 0.6rem; line-height: 1.6; }
.ai-note-label { font-family: 'DM Mono', monospace; font-size: 0.62rem; letter-spacing: 0.1em; text-transform: uppercase; color: var(--gold); margin-bottom: 0.3rem; }
.thought-block { font-family: 'DM Mono', monospace; font-size: 0.72rem; color: var(--text-dim); background: var(--surface2); border: 1px dashed var(--border); border-radius: 4px; padding: 0.5rem 0.8rem; margin-bottom: 0.5rem; line-height: 1.5; }
.patch-block { font-family: 'DM Mono', monospace; font-size: 0.8rem; background: #1a1a1a; color: #d4c89a; border-radius: 6px; padding: 1rem 1.2rem; margin-top: 0.8rem; line-height: 1.7; white-space: pre; overflow-x: auto; }
.footer-note { font-family: 'DM Mono', monospace; font-size: 0.68rem; color: var(--text-dim); text-align: center; margin-top: 3rem; padding-top: 1rem; border-top: 1px solid var(--border); }
</style>
""", unsafe_allow_html=True)

# ── Current universe from app.py ──────────────────────────────────────────────

CURRENT_TICKERS = [
    "VGT","VHT","GLD","BLOK","BND","BNDX","BRK-B","PDBC",
    "VB","VEA","VNQ","VNQI","VO","VV","VWO"
]

CURRENT_NAMES = {
    "VGT":"US Tech / AI","VHT":"Healthcare","GLD":"Gold","BLOK":"Crypto-Adjacent",
    "BND":"US Bonds","BNDX":"Intl Bonds","BRK-B":"Value / Compounding","PDBC":"Commodities",
    "VB":"US Small Cap","VEA":"Intl Developed","VNQ":"US Real Estate","VNQI":"Intl Real Estate",
    "VO":"US Mid Cap","VV":"US Large Cap","VWO":"Emerging Markets",
}

# ── yfinance helpers ──────────────────────────────────────────────────────────

@st.cache_data(ttl=3600)
def fetch_etf_metrics(ticker: str) -> dict | None:
    """Fetch live price, 200D SMA, div yield, TER for a single ticker."""
    try:
        t = yf.Ticker(ticker)
        hist = t.history(period="1y", auto_adjust=True)
        if hist.empty or len(hist) < 50:
            return None
        price = float(hist["Close"].iloc[-1])
        sma200 = float(hist["Close"].tail(200).mean()) if len(hist) >= 200 else float(hist["Close"].mean())
        vs_200sma = (price - sma200) / sma200
        info = t.info or {}
        div_yield = info.get("dividendYield") or info.get("trailingAnnualDividendYield") or 0.0
        ter = info.get("annualReportExpenseRatio") or info.get("expenseRatio") or None
        aum = info.get("totalAssets") or None
        name = info.get("longName") or info.get("shortName") or ticker
        issuer = info.get("fundFamily") or "Unknown"
        category = info.get("category") or ""
        return {
            "ticker": ticker,
            "name": name,
            "issuer": issuer,
            "category": category,
            "price": round(price, 2),
            "sma200": round(sma200, 2),
            "vs_200sma": round(vs_200sma * 100, 2),
            "div_yield": round(div_yield * 100, 2) if div_yield else 0.0,
            "ter": round(ter * 100, 4) if ter else None,
            "aum_bn": round(aum / 1e9, 1) if aum else None,
            "momentum": "above" if vs_200sma > 0 else "below",
        }
    except Exception:
        return None

# ── Agentic screener ──────────────────────────────────────────────────────────

def run_agent(criteria: dict, custom_tickers: list[str], show_thinking: bool) -> list[dict]:
    """
    Agentic loop:
    1. Claude web-searches for ETF news and new ETFs worth investigating
    2. Claude decides which tickers to fetch live data for
    3. yfinance fetches real metrics
    4. Claude reasons against criteria and produces final recommendations
    """
    client = anthropic.Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])

    current_str = ", ".join(CURRENT_TICKERS)
    focus_str = ", ".join(criteria["focus"]) or "general"
    custom_str = ", ".join(custom_tickers) if custom_tickers else "none"

    step1_placeholder = st.empty()
    step1_placeholder.markdown('<div class="thought-block">① Agent searching for ETF market news and new candidates…</div>', unsafe_allow_html=True)

    # ── Step 1: Agent searches and proposes candidate tickers ──────────────────
    discovery_prompt = f"""You are an ETF research agent for a growth-oriented investor based in Singapore.

Current portfolio universe: {current_str}
User's custom additions to screen: {custom_str}
Criteria:
- Max TER: {criteria['max_ter']:.2f}%
- Min dividend yield: {criteria['min_div']:.1f}%
- Min AUM: ${criteria['min_aum_bn']:.0f}B
- Momentum: price must be {criteria['momentum']} 200-day moving average
- Focus areas: {focus_str}
- Preference: growth-centric, reputable issuer (Vanguard, iShares, Schwab, Invesco, SPDR, ARK)

Use the web_search tool to:
1. Search for "best ETFs 2025 2026 growth" and similar queries
2. Search for any newly launched ETFs in relevant sectors
3. Search for ETF news relevant to the user's focus areas

Then return a JSON object (ONLY JSON, no markdown) with this exact shape:
{{
  "search_summary": "2-3 sentence summary of what you found in the news",
  "candidates": ["TICKER1","TICKER2",...],
  "reasoning": "Why you chose these candidates"
}}

Include: tickers already in universe (to screen them), custom additions, AND any new ones you discovered.
Aim for 15-25 total tickers. Return US-listed ETF tickers only."""

    resp1 = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1500,
        tools=[{"type": "web_search_20250305", "name": "web_search"}],
        messages=[{"role": "user", "content": discovery_prompt}]
    )

    discovery_text = "".join(b.text for b in resp1.content if hasattr(b, "text"))
    try:
        clean = discovery_text.replace("```json","").replace("```","").strip()
        discovery = json.loads(clean)
    except Exception:
        discovery = {"search_summary": "Web search complete.", "candidates": CURRENT_TICKERS + custom_tickers, "reasoning": "Defaulting to current universe."}

    candidates = list(dict.fromkeys(discovery.get("candidates", CURRENT_TICKERS)))
    step1_placeholder.markdown(
        f'<div class="thought-block">① Search complete — {len(candidates)} candidates identified.<br>'
        f'<span style="color:var(--gold)">{discovery.get("search_summary","")}</span></div>',
        unsafe_allow_html=True
    )

    # ── Step 2: Fetch live yfinance data for all candidates ────────────────────
    step2_placeholder = st.empty()
    step2_placeholder.markdown(f'<div class="thought-block">② Fetching live data for {len(candidates)} tickers via yfinance…</div>', unsafe_allow_html=True)

    live_data = {}
    prog = st.progress(0)
    for i, ticker in enumerate(candidates):
        m = fetch_etf_metrics(ticker)
        if m:
            live_data[ticker] = m
        prog.progress((i + 1) / len(candidates))
    prog.empty()

    step2_placeholder.markdown(f'<div class="thought-block">② Live data fetched — {len(live_data)}/{len(candidates)} tickers returned data.</div>', unsafe_allow_html=True)

    # ── Step 3: Claude reasons against criteria with live data ─────────────────
    step3_placeholder = st.empty()
    step3_placeholder.markdown('<div class="thought-block">③ Agent reasoning against your criteria…</div>', unsafe_allow_html=True)

    data_str = json.dumps(live_data, indent=2)

    reasoning_prompt = f"""You are an ETF analyst. Here is live market data for {len(live_data)} ETFs:

{data_str}

Screen each ETF against these criteria:
- Max TER: {criteria['max_ter']:.2f}% (if TER data available; flag if missing)
- Min dividend yield: {criteria['min_div']:.1f}%
- Min AUM: ${criteria['min_aum_bn']:.0f}B
- Momentum: {criteria['momentum']} 200-day moving average (vs_200sma > 0 means above)
- Focus: {focus_str}
- Preference: growth-centric, reputable issuer

Return ONLY a JSON array (no markdown). Each object:
{{
  "ticker": "...",
  "name": "...",
  "issuer": "...",
  "ter": 0.03,
  "div_yield": 1.8,
  "aum_bn": 50.0,
  "vs_200sma": 4.2,
  "momentum": "above",
  "status": "pass" | "partial" | "watch" | "fail",
  "criteria_hits": ["ter ok","momentum above",...],
  "criteria_misses": ["div yield below threshold",...],
  "is_new": true | false,
  "reputable": true | false,
  "ai_note": "2-3 sentences: investment case, why watch even if failed, standout quality for a growth-oriented investor. Be specific and candid.",
  "add_to_universe": true | false
}}

is_new = true if NOT in this list: {current_str}
add_to_universe = true only for tickers you genuinely recommend adding (pass or strong watch).
Be selective — recommend at most 3-4 new additions."""

    resp3 = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=4000,
        messages=[{"role": "user", "content": reasoning_prompt}]
    )

    raw3 = "".join(b.text for b in resp3.content if hasattr(b, "text"))
    try:
        clean3 = raw3.replace("```json","").replace("```","").strip()
        results = json.loads(clean3)
    except Exception:
        results = []

    step3_placeholder.markdown(f'<div class="thought-block">③ Reasoning complete — {len(results)} ETFs evaluated.</div>', unsafe_allow_html=True)

    return results, discovery

# ── UI ─────────────────────────────────────────────────────────────────────────

st.markdown("""
<div class="header-block">
    <h1>ETF Scout</h1>
    <p>AGENTIC SCREENER · WEB-SEARCH · LIVE DATA · GROWTH-ORIENTED</p>
</div>
""", unsafe_allow_html=True)

with st.expander("⚙ Screening criteria", expanded=True):
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        max_ter = st.slider("Max TER (%)", 0.0, 1.0, 0.30, 0.01)
    with col2:
        min_div = st.slider("Min dividend yield (%)", 0.0, 5.0, 1.0, 0.1)
    with col3:
        min_aum = st.slider("Min AUM ($B)", 1, 50, 5, 1)
    with col4:
        momentum = st.selectbox("Momentum", ["above", "any"])

    focus_options = ["Global","Growth","Technology","Healthcare","Emerging Markets","Dividend","Small Cap","ESG","Commodities","Real Estate"]
    focus = st.multiselect("Focus areas", focus_options, default=["Global","Growth"])

    st.markdown("**Additional tickers to screen** (beyond current universe)")
    custom_raw = st.text_input("Comma-separated tickers", placeholder="e.g. SCHG, VUG, AVUV")
    custom_tickers = [t.strip().upper() for t in custom_raw.split(",") if t.strip()] if custom_raw else []

    show_thinking = st.checkbox("Show agent reasoning steps", value=True)

criteria = {
    "max_ter": max_ter,
    "min_div": min_div,
    "min_aum_bn": min_aum,
    "momentum": momentum,
    "focus": [f.lower() for f in focus],
}

if st.button("🔭 Run agent screen"):
    st.markdown('<div class="section-label">Agent log</div>', unsafe_allow_html=True)

    with st.spinner(""):
        results, discovery = run_agent(criteria, custom_tickers, show_thinking)

    if not results:
        st.error("Agent returned no results. Check your ANTHROPIC_API_KEY in secrets.")
        st.stop()

    # ── Summary metrics ────────────────────────────────────────────────────────
    passed   = [r for r in results if r["status"] == "pass"]
    partial  = [r for r in results if r["status"] == "partial"]
    watches  = [r for r in results if r["status"] == "watch"]
    new_recs = [r for r in results if r.get("is_new") and r.get("add_to_universe")]

    st.markdown('<div class="section-label">Screen results</div>', unsafe_allow_html=True)
    mc1, mc2, mc3, mc4 = st.columns(4)
    for col, label, val, color in [
        (mc1, "Passed",          len(passed),         "var(--green)"),
        (mc2, "Partial / watch", len(partial)+len(watches), "var(--yellow)"),
        (mc3, "Screened total",  len(results),        "var(--gold)"),
        (mc4, "New additions",   len(new_recs),        "#185fa5"),
    ]:
        with col:
            st.markdown(f'<div class="metric-card"><div class="metric-label">{label}</div><div class="metric-value" style="color:{color};">{val}</div></div>', unsafe_allow_html=True)

    # ── Results cards ──────────────────────────────────────────────────────────
    order = {"pass": 0, "partial": 1, "watch": 2, "fail": 3}
    results_sorted = sorted(results, key=lambda r: (order.get(r["status"], 3), -r.get("vs_200sma", 0)))

    def color_pct(val):
        if val is None: return "<span class='neu'>—</span>"
        cls = "pos" if val > 0 else ("neg" if val < 0 else "neu")
        sign = "+" if val > 0 else ""
        return f"<span class='{cls}'>{sign}{val:.2f}%</span>"

    for r in results_sorted:
        status = r.get("status","fail")
        badge_map = {"pass":"badge-pass","partial":"badge-partial","watch":"badge-watch","fail":"badge-fail"}
        label_map = {"pass":"PASS","partial":"PARTIAL","watch":"WATCH","fail":"FAIL"}
        badge_cls = badge_map.get(status,"badge-fail")
        badge_lbl = label_map.get(status,"FAIL")
        new_tag = '<span class="badge" style="background:rgba(55,138,221,0.1);color:#185fa5;border:1px solid rgba(55,138,221,0.3)">NEW</span>' if r.get("is_new") else ""
        rep_tag  = '<span class="badge" style="background:rgba(46,125,82,0.1);color:var(--green);border:1px solid rgba(46,125,82,0.3)">REPUTABLE</span>' if r.get("reputable") else ""

        hits_str   = " · ".join(r.get("criteria_hits",[]))
        misses_str = " · ".join(r.get("criteria_misses",[]))

        ter_disp = f'{r["ter"]:.2f}%' if r.get("ter") else "N/A"
        div_disp = f'{r["div_yield"]:.1f}%' if r.get("div_yield") is not None else "N/A"
        aum_disp = f'${r["aum_bn"]:.1f}B' if r.get("aum_bn") else "N/A"

        st.markdown(f"""
<div class="etf-card">
  <div style="display:flex;justify-content:space-between;align-items:flex-start">
    <div>
      <span class="etf-ticker">{r['ticker']}</span>
      <span class="badge {badge_cls}">{badge_lbl}</span>{new_tag}{rep_tag}
      <div class="etf-name">{r.get('name','')} · {r.get('issuer','')}</div>
    </div>
    <div style="text-align:right;font-family:'DM Mono',monospace;font-size:0.75rem;color:var(--text-dim)">
      vs 200D SMA: {color_pct(r.get('vs_200sma'))}
    </div>
  </div>
  <table style="margin-top:0.5rem">
    <tr>
      <th>TER</th><th>Div Yield</th><th>AUM</th><th>Momentum</th>
    </tr>
    <tr>
      <td style="text-align:center">{ter_disp}</td>
      <td style="text-align:center">{div_disp}</td>
      <td style="text-align:center">{aum_disp}</td>
      <td style="text-align:center">{r.get('momentum','—')}</td>
    </tr>
  </table>
  {'<div style="font-size:0.72rem;color:var(--green);margin-top:0.4rem;font-family:DM Mono,monospace">✓ ' + hits_str + '</div>' if hits_str else ''}
  {'<div style="font-size:0.72rem;color:var(--red);margin-top:0.2rem;font-family:DM Mono,monospace">✗ ' + misses_str + '</div>' if misses_str else ''}
  <div class="ai-note">
    <div class="ai-note-label">AI reasoning</div>
    {r.get('ai_note','')}
  </div>
</div>
""", unsafe_allow_html=True)

    # ── Recommended additions patch ────────────────────────────────────────────
    if new_recs:
        st.markdown('<div class="section-label">④ Recommended additions — app.py patch</div>', unsafe_allow_html=True)
        st.markdown("The agent recommends adding the following to your `TICKERS` list in `app.py`:")

        new_tickers_str = "\n".join(f'    "{r["ticker"]}",  # {r.get("name","")} — {r.get("ai_note","")[:80]}…' for r in new_recs)
        current_block = "\n".join(f'    "{t}",' for t in CURRENT_TICKERS)

        patch = f"""# ── Suggested TICKERS update in app.py ──────────────────────────────────────
# Generated by ETF Scout on {datetime.now().strftime('%d %b %Y')}
# Review each addition before applying.

TICKERS = [
{current_block}
    # ── Agent-recommended additions ──
{new_tickers_str}
]

# Also update TICKER_NAMES:
TICKER_NAMES_ADDITIONS = {{
{chr(10).join(f'    "{r["ticker"]}": "{r.get("name","")}",' for r in new_recs)}
}}"""

        st.markdown(f'<div class="patch-block">{patch}</div>', unsafe_allow_html=True)
        st.download_button(
            label="⬇ Download patch as .txt",
            data=patch,
            file_name=f"etf_patch_{datetime.now().strftime('%Y%m%d')}.txt",
            mime="text/plain"
        )

st.markdown(
    '<div class="footer-note">Data via Yahoo Finance · Reasoning via Claude · Web search via Anthropic API · Not financial advice · Built for personal use</div>',
    unsafe_allow_html=True
)
