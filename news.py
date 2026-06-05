import streamlit as st
import anthropic
import json
from datetime import datetime

st.set_page_config(
    page_title="Market Pulse — Portfolio Allocator",
    page_icon="📰",
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
div[data-testid="stButton"] button { background: var(--gold); color: #ffffff; border: none; font-family: 'DM Mono', monospace; font-size: 0.8rem; font-weight: 500; padding: 0.5rem 1.5rem; border-radius: 4px; }
.thought-block { font-family: 'DM Mono', monospace; font-size: 0.72rem; color: var(--text-dim); background: var(--surface2); border: 1px dashed var(--border); border-radius: 4px; padding: 0.5rem 0.8rem; margin-bottom: 0.5rem; line-height: 1.5; }
.news-card { background: var(--surface); border: 1px solid var(--border); border-radius: 8px; padding: 1.1rem 1.4rem; margin-bottom: 0.9rem; }
.news-headline { font-family: 'Playfair Display', serif; font-size: 1.05rem; font-weight: 700; color: var(--text); margin-bottom: 0.3rem; line-height: 1.4; }
.news-meta { font-family: 'DM Mono', monospace; font-size: 0.65rem; color: var(--text-dim); margin-bottom: 0.6rem; letter-spacing: 0.04em; }
.news-summary { font-family: 'DM Sans', sans-serif; font-size: 0.84rem; color: var(--text-dim); line-height: 1.65; margin-bottom: 0.7rem; }
.impact-box { border-left: 2px solid var(--gold-dim); padding: 0.5rem 0.9rem; background: var(--surface2); border-radius: 0 4px 4px 0; font-family: 'DM Sans', sans-serif; font-size: 0.8rem; color: var(--text); line-height: 1.55; }
.impact-label { font-family: 'DM Mono', monospace; font-size: 0.6rem; letter-spacing: 0.1em; text-transform: uppercase; color: var(--gold); margin-bottom: 0.25rem; }
.tag { display: inline-block; font-family: 'DM Mono', monospace; font-size: 0.62rem; border-radius: 3px; padding: 2px 7px; margin: 2px 3px 2px 0; }
.tag-high   { background: rgba(192,57,43,0.08);  color: var(--red);    border: 1px solid rgba(192,57,43,0.25); }
.tag-medium { background: rgba(184,134,11,0.10); color: var(--yellow); border: 1px solid rgba(184,134,11,0.3); }
.tag-low    { background: rgba(46,125,82,0.10);  color: var(--green);  border: 1px solid rgba(46,125,82,0.25); }
.tag-etf    { background: rgba(138,111,46,0.10); color: var(--gold);   border: 1px solid rgba(138,111,46,0.3); }
.digest-box { background: var(--surface); border: 1px solid var(--border); border-radius: 8px; padding: 1.3rem 1.6rem; margin-bottom: 1.5rem; }
.digest-box h3 { font-family: 'Playfair Display', serif; font-size: 1.1rem; margin: 0 0 0.7rem 0; color: var(--gold); }
.digest-body { font-family: 'DM Sans', sans-serif; font-size: 0.87rem; line-height: 1.75; color: var(--text-dim); }
.etf-chip { display: inline-block; font-family: 'DM Mono', monospace; font-size: 0.68rem; background: var(--surface2); border: 1px solid var(--border); border-radius: 4px; padding: 3px 8px; margin: 3px 4px 3px 0; color: var(--text); }
.etf-chip.active { background: rgba(138,111,46,0.12); border-color: rgba(138,111,46,0.4); color: var(--gold); font-weight: 500; }
.footer-note { font-family: 'DM Mono', monospace; font-size: 0.68rem; color: var(--text-dim); text-align: center; margin-top: 3rem; padding-top: 1rem; border-top: 1px solid var(--border); }
</style>
""", unsafe_allow_html=True)

# ── ETF universe with theme mappings ─────────────────────────────────────────

ALL_ETFS = {
    "VGT":  {"name": "US Tech / AI",          "themes": ["artificial intelligence", "semiconductors", "big tech earnings", "US technology sector", "cloud computing"]},
    "VHT":  {"name": "Healthcare",             "themes": ["pharmaceutical earnings", "FDA approvals", "healthcare policy US", "biotech sector", "Medicare Medicaid"]},
    "GLD":  {"name": "Gold",                   "themes": ["gold price", "Fed interest rates", "inflation CPI", "USD strength", "safe haven assets"]},
    "BLOK": {"name": "Crypto-Adjacent",        "themes": ["Bitcoin ETF", "blockchain technology", "cryptocurrency regulation", "crypto market", "digital assets"]},
    "BND":  {"name": "US Bonds",               "themes": ["Federal Reserve rate decision", "US treasury yields", "bond market", "inflation outlook", "FOMC"]},
    "BNDX": {"name": "Intl Bonds",             "themes": ["ECB rate decision", "global bond market", "emerging market debt", "currency risk", "sovereign bonds"]},
    "BRK-B":{"name": "Value / Compounding",    "themes": ["Berkshire Hathaway", "Warren Buffett", "value investing", "insurance sector", "banking stocks"]},
    "PDBC": {"name": "Commodities",            "themes": ["oil price", "commodity markets", "OPEC", "natural gas", "copper demand China"]},
    "VB":   {"name": "US Small Cap",           "themes": ["small cap stocks US", "Russell 2000", "domestic US economy", "interest rate impact small cap", "IPO market"]},
    "VEA":  {"name": "Intl Developed",         "themes": ["Europe economy", "Japan economy", "MSCI EAFE", "developed market equities", "EUR USD"]},
    "VNQ":  {"name": "US Real Estate",         "themes": ["US real estate market", "REIT sector", "commercial property", "mortgage rates", "housing market"]},
    "VNQI": {"name": "Intl Real Estate",       "themes": ["global real estate", "Asian property market", "China real estate", "international REIT", "property market Europe"]},
    "VO":   {"name": "US Mid Cap",             "themes": ["mid cap US stocks", "S&P 400", "industrial sector", "consumer discretionary", "earnings growth mid cap"]},
    "VV":   {"name": "US Large Cap",           "themes": ["S&P 500", "large cap US equities", "earnings season", "US economic outlook", "stock market rally"]},
    "VWO":  {"name": "Emerging Markets",       "themes": ["China economy", "emerging market equities", "India GDP", "EM currency", "commodity exporters"]},
}

# ── Header ────────────────────────────────────────────────────────────────────

st.markdown("""
<div class="header-block">
    <h1>Market Pulse</h1>
    <p>PORTFOLIO-RELEVANT NEWS · AI-CURATED · IMPACT ANALYSIS</p>
</div>
""", unsafe_allow_html=True)

# ── ETF selector ──────────────────────────────────────────────────────────────

st.markdown("**Select ETFs to monitor** — news will focus on themes that drive these holdings")

if "selected_etfs" not in st.session_state:
    st.session_state.selected_etfs = list(ALL_ETFS.keys())

cols = st.columns(8)
for i, (ticker, info) in enumerate(ALL_ETFS.items()):
    with cols[i % 8]:
        checked = st.checkbox(ticker, value=ticker in st.session_state.selected_etfs, key=f"chk_{ticker}", help=info["name"])

selected = [t for t in ALL_ETFS if st.session_state.get(f"chk_{t}", True)]

col_a, col_b, col_c = st.columns([1, 1, 4])
with col_a:
    depth = st.selectbox("Depth", ["Quick (5 stories)", "Standard (10 stories)", "Deep (15 stories)"], index=1)
with col_b:
    tone = st.selectbox("Slant", ["Balanced", "Risk-focused", "Opportunity-focused"])

depth_map = {"Quick (5 stories)": 5, "Standard (10 stories)": 10, "Deep (15 stories)": 15}
n_stories = depth_map[depth]

if not selected:
    st.warning("Select at least one ETF to monitor.")
    st.stop()

# ── Run ───────────────────────────────────────────────────────────────────────

if st.button("📰 Fetch latest news"):

    client = anthropic.Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])

    # Flatten themes for selected ETFs
    etf_theme_map = {t: ALL_ETFS[t] for t in selected}
    all_themes = []
    for t, info in etf_theme_map.items():
        for theme in info["themes"]:
            all_themes.append({"etf": t, "theme": theme})

    # Build compact context for the agent
    etf_context = "\n".join(
        f"- {t} ({ALL_ETFS[t]['name']}): {', '.join(ALL_ETFS[t]['themes'][:3])}"
        for t in selected
    )

    st.markdown('<div class="section-label">Agent log</div>', unsafe_allow_html=True)
    log1 = st.empty()
    log2 = st.empty()
    log3 = st.empty()

    log1.markdown('<div class="thought-block">① Searching for portfolio-relevant news across all selected ETF themes…</div>', unsafe_allow_html=True)

    # ── Agent: search + curate ────────────────────────────────────────────────
    prompt = f"""You are a financial news analyst for a growth-oriented investor in Singapore.
Their ETF portfolio / universe:
{etf_context}

Today is {datetime.now().strftime('%d %B %Y')}.

Use web_search to find the {n_stories} most relevant, recent news stories that could affect one or more of these ETFs.
Search across multiple themes — don't focus only on one ETF.
Slant: {tone}.

For each story, provide a JSON object in this array (return ONLY the JSON array, no markdown):
{{
  "headline": "Clear, informative headline",
  "source": "Publication name",
  "date": "Approximate date e.g. 4 Jun 2025",
  "summary": "2–3 sentence factual summary of what happened",
  "impact_analysis": "2–3 sentences: how this specifically affects the selected ETFs. Name the tickers. Be direct about bullish/bearish implications.",
  "affected_etfs": ["VGT","VV"],
  "impact_level": "high" | "medium" | "low",
  "url": "URL if found, else null"
}}

impact_level guide: high = could move the ETF >1% or signals a structural shift; medium = notable but contained; low = background context.
Return exactly {n_stories} stories, ordered by impact_level descending then recency."""

    with st.spinner(""):
        resp = client.messages.create(
            model="claude-opus-4-5",
            max_tokens=4000,
            tools=[{"type": "web_search_20250305", "name": "web_search"}],
            messages=[{"role": "user", "content": prompt}]
        )

    raw = "".join(b.text for b in resp.content if hasattr(b, "text"))
    try:
        clean = raw.replace("```json", "").replace("```", "").strip()
        stories = json.loads(clean)
    except Exception:
        st.error("Could not parse news response. Try again.")
        st.stop()

    log1.markdown(f'<div class="thought-block">① Search complete — {len(stories)} stories retrieved and ranked by portfolio impact.</div>', unsafe_allow_html=True)
    log2.markdown('<div class="thought-block">② Generating portfolio digest…</div>', unsafe_allow_html=True)

    # ── Digest ────────────────────────────────────────────────────────────────
    headlines_str = "\n".join(f"- {s['headline']} ({s.get('impact_level','').upper()}): {s['summary']}" for s in stories)
    digest_prompt = f"""Based on these news stories affecting a portfolio of {', '.join(selected)}:

{headlines_str}

Write a concise portfolio digest (4–6 sentences) for a growth-oriented investor in Singapore.
- What is the dominant theme across today's news?
- Which ETF positions face the most near-term pressure or tailwind?
- Any actionable watch-points for next month's rebalance?
Keep it direct, no fluff. Plain prose, no bullet points."""

    digest_resp = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=400,
        messages=[{"role": "user", "content": digest_prompt}]
    )
    digest_text = "".join(b.text for b in digest_resp.content if hasattr(b, "text"))

    log2.markdown('<div class="thought-block">② Digest ready.</div>', unsafe_allow_html=True)
    log3.markdown(f'<div class="thought-block">③ Rendered {len(stories)} stories · {datetime.now().strftime("%H:%M")} SGT</div>', unsafe_allow_html=True)

    # ── Render digest ─────────────────────────────────────────────────────────
    st.markdown('<div class="section-label">Portfolio digest</div>', unsafe_allow_html=True)
    st.markdown(f"""
<div class="digest-box">
  <h3>Today's read — {datetime.now().strftime('%d %b %Y')}</h3>
  <div class="digest-body">{digest_text}</div>
</div>
""", unsafe_allow_html=True)

    # ── Render stories ────────────────────────────────────────────────────────
    high   = [s for s in stories if s.get("impact_level") == "high"]
    medium = [s for s in stories if s.get("impact_level") == "medium"]
    low    = [s for s in stories if s.get("impact_level") == "low"]

    for section_label, section_stories, impact_cls in [
        ("High impact", high, "tag-high"),
        ("Medium impact", medium, "tag-medium"),
        ("Background context", low, "tag-low"),
    ]:
        if not section_stories:
            continue
        st.markdown(f'<div class="section-label">{section_label}</div>', unsafe_allow_html=True)
        for s in section_stories:
            etf_tags = "".join(f'<span class="tag tag-etf">{e}</span>' for e in s.get("affected_etfs", []))
            impact_tag = f'<span class="tag {impact_cls}">{s.get("impact_level","").upper()}</span>'
            url = s.get("url")
            headline_html = (
                f'<a href="{url}" target="_blank" style="color:var(--text);text-decoration:none;">{s["headline"]}</a>'
                if url else s["headline"]
            )
            st.markdown(f"""
<div class="news-card">
  <div class="news-headline">{headline_html}</div>
  <div class="news-meta">{s.get('source','Unknown source')} · {s.get('date','')} &nbsp;|&nbsp; {impact_tag} {etf_tags}</div>
  <div class="news-summary">{s.get('summary','')}</div>
  <div class="impact-box">
    <div class="impact-label">Portfolio impact</div>
    {s.get('impact_analysis','')}
  </div>
</div>
""", unsafe_allow_html=True)

st.markdown(
    '<div class="footer-note">News sourced via web search · Analysis by Claude · Not financial advice · Verify before acting</div>',
    unsafe_allow_html=True
)
