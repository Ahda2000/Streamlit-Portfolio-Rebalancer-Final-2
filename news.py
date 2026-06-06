"""
Market Pulse — News Digest
pages/news.py
Supabase persistence: news_runs table
"""

import streamlit as st
import anthropic
import json
from datetime import datetime, timezone
from supabase import create_client

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(page_title="Market Pulse", page_icon="📰", layout="wide")

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
}
html, body, [data-testid="stAppViewContainer"] { background: var(--bg) !important; }
[data-testid="stSidebar"] { background: #f0ede8 !important; border-right: 1px solid var(--border); }
* { font-family: 'DM Sans', sans-serif; color: var(--ink); }
h1, h2, h3, h4 { font-family: 'Playfair Display', serif; }
code { font-family: 'DM Mono', monospace; }
[data-testid="stButton"] button {
    background: var(--gold) !important;
    color: #fff !important;
    border: none !important;
    border-radius: 6px !important;
    font-weight: 500 !important;
    padding: 0.5rem 1.4rem !important;
}
[data-testid="stButton"] button:hover { background: var(--gold-lt) !important; }
.freshness-bar {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 0.45rem 1rem;
    font-size: 0.8rem;
    color: var(--muted);
    margin-bottom: 1.2rem;
}
.digest-body {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 1.4rem 1.6rem;
    line-height: 1.75;
    font-size: 0.94rem;
    margin-bottom: 1.5rem;
}
.story-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-left: 3px solid var(--gold);
    border-radius: 0 8px 8px 0;
    padding: 0.9rem 1.1rem;
    margin-bottom: 0.75rem;
}
.story-card h4 {
    margin: 0 0 0.3rem 0;
    font-size: 0.95rem;
}
.story-card p {
    margin: 0;
    font-size: 0.85rem;
    color: var(--muted);
}
.story-meta {
    font-family: 'DM Mono', monospace;
    font-size: 0.75rem;
    color: var(--gold);
    margin-bottom: 0.3rem;
}
.stRadio label { font-size: 0.85rem !important; }
.sentiment-tag {
    display: inline-block;
    padding: 0.15rem 0.5rem;
    border-radius: 4px;
    font-size: 0.75rem;
    font-weight: 600;
    margin-left: 0.5rem;
}
.sent-positive { background: #e8f5e9; color: #2e7d32; }
.sent-negative { background: #ffebee; color: #c62828; }
.sent-neutral  { background: #f5f5f5; color: #616161; }
</style>
""", unsafe_allow_html=True)

# ── Constants ──────────────────────────────────────────────────────────────────
TICKERS = ["VGT","VHT","GLD","BLOK","BND","BNDX","BRK-B","PDBC","VB","VEA","VNQ","VNQI","VO","VV","VWO"]
MODEL   = "claude-haiku-4-5-20251001"

# ── Supabase client ────────────────────────────────────────────────────────────
@st.cache_resource
def get_supabase():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

def load_history(limit: int = 10):
    try:
        sb = get_supabase()
        resp = sb.table("news_runs") \
                 .select("id, created_at, label, digest, stories") \
                 .order("created_at", desc=True) \
                 .limit(limit) \
                 .execute()
        return resp.data or []
    except Exception as e:
        st.warning(f"Could not load history: {e}")
        return []

def save_run(label: str, digest: str, stories: list):
    try:
        sb = get_supabase()
        sb.table("news_runs").insert({
            "label":   label,
            "digest":  digest,
            "stories": stories,
        }).execute()
    except Exception as e:
        st.warning(f"Could not save run: {e}")

# ── Claude: fetch & digest ─────────────────────────────────────────────────────
def fetch_news_and_digest() -> tuple[str, list]:
    """
    Two-step Claude call:
    1. Use web_search tool to find recent ETF/market news.
    2. Synthesise into a digest + structured stories list.
    Returns (digest_text, stories_list).
    """
    client = anthropic.Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])

    ticker_str = ", ".join(TICKERS)

    # ── Step 1: Search ────────────────────────────────────────────────────────
    search_prompt = f"""Search for the latest financial news (last 48 hours) relevant to these ETFs and their underlying sectors:
{ticker_str}

Categories to cover:
- Technology sector (VGT, BLOK)
- Healthcare sector (VHT)
- Commodities: gold, oil/energy (GLD, PDBC)
- Fixed income / rates / Fed (BND, BNDX)
- Berkshire Hathaway (BRK-B)
- Small/mid/large cap US equities (VB, VO, VV)
- International developed markets (VEA)
- Real estate / REITs (VNQ, VNQI)
- Emerging markets (VWO)

Find 6–10 distinct, material stories. For each story capture: headline, source, 1-sentence summary, and which ticker(s) it affects."""

    step1 = client.messages.create(
        model=MODEL,
        max_tokens=1500,
        tools=[{"type": "web_search_20250305", "name": "web_search"}],
        messages=[{"role": "user", "content": search_prompt}]
    )

    # Extract text blocks from step 1
    raw_search = "\n".join(
        b.text for b in step1.content if hasattr(b, "text")
    )

    # ── Step 2: Synthesise ────────────────────────────────────────────────────
    synthesis_prompt = f"""You are a market analyst writing a concise daily market digest.

Based on the following raw search results, produce:

1. A **Market Digest** (3–5 paragraphs): synthesised narrative covering macro backdrop, key sector developments, and what it means for a systematic ETF investor. Be direct and informative.

2. A **Stories JSON array** — respond with ONLY valid JSON after the digest, delimited by ---JSON--- on its own line. Each story object must have:
   - "headline": string
   - "source": string (publication name)
   - "summary": string (1–2 sentences)
   - "tickers": array of affected tickers from {json.dumps(TICKERS)}
   - "sentiment": one of "positive", "negative", "neutral"

RAW SEARCH RESULTS:
{raw_search}

Format your full response as:
<DIGEST>
...your 3–5 paragraph digest here...
</DIGEST>
---JSON---
[...array of story objects...]"""

    step2 = client.messages.create(
        model=MODEL,
        max_tokens=2000,
        messages=[{"role": "user", "content": synthesis_prompt}]
    )

    full_text = "\n".join(b.text for b in step2.content if hasattr(b, "text"))

    # Parse digest
    digest = full_text
    stories = []

    if "<DIGEST>" in full_text and "</DIGEST>" in full_text:
        digest = full_text.split("<DIGEST>")[1].split("</DIGEST>")[0].strip()

    if "---JSON---" in full_text:
        json_part = full_text.split("---JSON---")[-1].strip()
        try:
            stories = json.loads(json_part)
        except json.JSONDecodeError:
            # best-effort: try to find the array
            start = json_part.find("[")
            end   = json_part.rfind("]") + 1
            if start != -1 and end > start:
                try:
                    stories = json.loads(json_part[start:end])
                except Exception:
                    stories = []

    return digest, stories

# ── Render run ─────────────────────────────────────────────────────────────────
def render_run(run: dict):
    created_at = run.get("created_at", "")
    label      = run.get("label", "")
    digest     = run.get("digest", "")
    stories    = run.get("stories", []) or []

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

    # Digest
    if digest:
        st.markdown("### 📋 Market Digest")
        st.markdown(f'<div class="digest-body">{digest}</div>', unsafe_allow_html=True)

    # Stories
    if stories:
        st.markdown("### 📰 Stories")
        for story in stories:
            headline  = story.get("headline", "")
            source    = story.get("source", "")
            summary   = story.get("summary", "")
            tickers   = story.get("tickers", [])
            sentiment = story.get("sentiment", "neutral").lower()

            sent_class = {"positive": "sent-positive", "negative": "sent-negative"}.get(sentiment, "sent-neutral")
            sent_emoji = {"positive": "▲", "negative": "▼"}.get(sentiment, "●")
            tickers_str = " · ".join(tickers) if tickers else "—"

            st.markdown(f"""
<div class="story-card">
  <div class="story-meta">{source} &nbsp;|&nbsp; {tickers_str} &nbsp;<span class="sentiment-tag {sent_class}">{sent_emoji} {sentiment.capitalize()}</span></div>
  <h4>{headline}</h4>
  <p>{summary}</p>
</div>""", unsafe_allow_html=True)
    elif digest:
        st.info("No structured stories parsed — digest above contains the full summary.")

# ── Sidebar history ────────────────────────────────────────────────────────────
def build_sidebar(history: list) -> int | None:
    st.sidebar.markdown("## 📰 Market Pulse")
    st.sidebar.markdown("---")

    if not history:
        st.sidebar.caption("No saved runs yet.")
        return None

    options = ["▶ New Run"] + [r.get("label", f"Run {i+1}") for i, r in enumerate(history)]
    choice = st.sidebar.radio("History (last 10)", options, index=0)

    if choice == "▶ New Run":
        return None
    return options.index(choice) - 1

# ── Main ───────────────────────────────────────────────────────────────────────
def main():
    st.markdown("# 📰 Market Pulse")
    st.markdown("*AI-powered news digest for your ETF universe.*")
    st.markdown("---")

    history      = load_history(10)
    selected_idx = build_sidebar(history)

    # Historical run selected
    if selected_idx is not None:
        render_run(history[selected_idx])
        return

    # Show latest by default
    if history and "news_run_just_done" not in st.session_state:
        st.info("Showing latest saved digest. Click **Fetch Latest News** to refresh.")
        render_run(history[0])

    # Fetch button
    st.markdown("### Fetch fresh digest")
    col1, col2 = st.columns([2, 1])
    with col1:
        run_label = st.text_input(
            "Label",
            value=datetime.now().strftime("%Y-%m-%d %H:%M"),
            label_visibility="collapsed",
            placeholder="Label e.g. 2025-06-07 morning"
        )
    with col2:
        go = st.button("🌐 Fetch Latest News", use_container_width=True)

    if go:
        st.session_state["news_run_just_done"] = True
        with st.spinner("Searching the web and generating digest…"):
            try:
                digest, stories = fetch_news_and_digest()
            except Exception as e:
                st.error(f"Error fetching news: {e}")
                return

        label = run_label or datetime.now().strftime("%Y-%m-%d %H:%M")
        save_run(label=label, digest=digest, stories=stories)

        render_run({
            "created_at": datetime.now(timezone.utc).isoformat(),
            "label":      label,
            "digest":     digest,
            "stories":    stories,
        })
        st.success("Digest saved to history.")

if __name__ == "__main__":
    main()
