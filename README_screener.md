# ETF Scout — setup guide

## What this is
`screener.py` is a second page for your existing Portfolio Allocator Streamlit app.
It runs as a proper AI agent: Claude searches the web for ETF news, discovers new candidates,
fetches live data via yfinance, and reasons against your criteria — all in one automated loop.

---

## File structure after setup

```
your-project/
├── app.py              ← your existing app (unchanged)
├── screener.py         ← new file (this)
├── .streamlit/
│   └── secrets.toml    ← add ANTHROPIC_API_KEY here
└── requirements.txt    ← add anthropic
```

---

## Setup steps

### 1. Place screener.py in your project folder
Copy `screener.py` alongside your existing `app.py`.

### 2. Add your Anthropic API key to secrets
In `.streamlit/secrets.toml`:
```toml
ANTHROPIC_API_KEY = "sk-ant-..."
IBKR_TOKEN = "..."        # already there
IBKR_QUERY_ID = "..."     # already there
```

### 3. Install the anthropic package
```bash
pip install anthropic
```
Or add to `requirements.txt`:
```
anthropic>=0.40.0
```

### 4. Run it as a multi-page app
Streamlit automatically detects multiple `.py` files as pages.
Run your app the same way you always do:
```bash
streamlit run app.py
```
`ETF Scout` will appear in the left sidebar as a second page.

---

## How the agent works (3-step loop)

```
Step 1 — Discover
  Claude + web_search → finds ETF news, new launches, sector trends
  → proposes 15–25 candidate tickers (your universe + new ones)

Step 2 — Fetch
  yfinance → live price, 200D SMA, TER, div yield, AUM for every candidate

Step 3 — Reason
  Claude reads live data → screens against your criteria
  → returns pass/partial/watch/fail + investment case for each ETF
  → flags recommended new additions with app.py patch
```

---

## Deploying to your own webpage (Streamlit Community Cloud)

1. Push your project to a GitHub repository
2. Go to share.streamlit.io → "New app"
3. Point it at your repo and `app.py`
4. Add secrets in the Streamlit Cloud dashboard (same keys as secrets.toml)
5. Done — you get a public URL like `https://yourname-portfolio.streamlit.app`

That IS your standalone webpage. No server to manage, free tier is sufficient.

---

## Costs

- Anthropic API: ~$0.01–0.05 per screen run (uses claude-opus-4-5)
- yfinance: free
- Streamlit Community Cloud: free
