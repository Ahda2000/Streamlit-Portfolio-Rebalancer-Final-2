# Portfolio Allocator

A rules-based trend-following portfolio allocation tool.

## Logic
1. Fetch 252 trading days of OHLCV data for all tickers
2. Compute average of 1M / 6M / 12M performance → rank universe → pick Top 6
3. For each of the Top 6, check Last Price vs 200D SMA:
   - Positive → INVEST (buy that ticker)
   - Negative → CASH (keep as SGD)
4. Compute inverse volatility weights across all 6 slots
5. Output allocation table + rebalancing calculator

## Ticker Universe
VGT, VHT, GLD, BLOK, BND, BNDX, BRK-B, PDBC, VB, VEA, VNQ, VNQI, VO, VV, VWO

## Deployment (Streamlit Community Cloud)

1. Push this folder to a GitHub repository (can be private)
2. Go to https://share.streamlit.io
3. Sign in with GitHub
4. Click "New app" → select your repo → set main file as `app.py`
5. Deploy — your app will be live at a public URL

## Running Locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Switching Data Provider (future)
Replace the `fetch_data()` function in app.py with Tiingo or Alpha Vantage.
Tiingo Python client: `pip install tiingo`
```python
from tiingo import TiingoClient
client = TiingoClient({'api_key': 'YOUR_KEY'})
```
