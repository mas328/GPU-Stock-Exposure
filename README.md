# GPU-Stock-Exposure

**Dashboard:** _link coming: deploy `app.py` on Streamlit Community Cloud and paste the URL here._

Do stock returns move with the price of renting GPU compute? For each stock we regress its daily
excess return on the market and on the daily change in a GPU rental price index (the
"compute beta"), and look at lead/lag correlations.

- **Real:** stock returns (Yahoo Finance adjusted close: splits and dividends), market factor and
  risk-free rate (Ken French daily factors).
- **FAKE:** the GPU price series, until the full Ornn history is available. Rows are tagged
  `gpu_source=FAKE`, so every beta and correlation is a placeholder, not a result.

## How to run (from the repo root)

```bash
pip install -r requirements.txt
python run_all.py          # deletes outputs/ and rebuilds every table and figure
streamlit run app.py       # opens the dashboard at localhost:8501
```

## Stocks (v0 sample)

| Group | Tickers |
|---|---|
| Sell compute (chips, GPU cloud, hyperscaler) | NVDA, AMD, IREN, ORCL |
| Buy compute | META, ADBE |
| Power / datacenter infrastructure | VST, VRT |
| Controls (no compute exposure) | KO, PG |

## Pipeline

| Step | File | Reads | Writes (`outputs/`) |
|---|---|---|---|
| 1 | `poc.py` | `data/prices_adjusted/`, `data/ornn_FAKE/` (H100), Ken French daily factors (downloaded) | `final_rows.csv` (one row = one stock on one trading day), `compute_betas.csv` (one row = one stock) |
| 2 | `graph.py` | `final_rows.csv` | `levels.png`, `leadlag.png` |
| 3 | `plot.py` | `final_rows.csv` | `correlation.png` |
| 4 | `make_chart.py` | `data/prices_adjusted/`, `data/ornn_FAKE/` (all six GPUs) | `stocks_vs_gpu.png/.html`, `correlation_daily.csv`, `correlation_weekly.csv`, `correlation_heatmap.png` |
| 5 | `make_correlation.py` | same as step 4 | `correlation_tests.png` |
| | `app.py` | `outputs/final_rows.csv` | the Streamlit dashboard (Introduction, Methodology, Results, Explore) |

## Raw inputs

| Input | Source | Where |
|---|---|---|
| Stock prices | Yahoo Finance via `yfinance`, `auto_adjust=True`, pulled 2026-11-13 (see `stock_adjusted_close_metadata.json`) | `data/prices_adjusted/` |
| Market factor, risk-free rate | Ken French Data Library, daily 3 factors | downloaded by `poc.py` each run |
| GPU rental prices | Ornn, through our professor. **Private**: never committed | `data/ornn/` (git-ignored) |
| GPU rental prices, FAKE | Made-up prices in Ornn's layout, so the code runs for anyone | `data/ornn_FAKE/` |

## Timing

Each GPU price is mapped to the stock trading day it can actually affect: set at or before
4:00 pm ET on a trading day -> that day; set after 4:00 pm ET, or on a weekend/holiday -> the
next trading day (the latest price wins if several land on one day). `d_gpu` is the change in
that price from the previous trading day. Ornn's real pricing time is unknown, so
`GPU_PRICE_TIME_ET` in `poc.py` (currently 17:00) is a placeholder.
