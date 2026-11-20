# GPU-Stock-Exposure

**Dashboard:** _link coming: deploy `app.py` on Streamlit Community Cloud and paste the URL here._

Do stock returns move with the price of renting GPU compute? For each stock we regress its daily
excess return on the market, a Nasdaq-100 control, and the daily change in a GPU rental price index
(the "compute beta"). Lead/lag correlations are exploratory.

## Main test (prespecified)

**b_gpu from `ex_ret = a + b_mkt·mkt_rf + b_gpu·d_gpu + b_ctrl·ex_qqq`, daily, one regression per
stock, GPU series = H100, timing rule = `same_day`, HC1 standard errors** (the `primary == True` rows
of `outputs/compute_betas.csv`). Everything else is a robustness check or exploratory. Every
specification, correlation grid and lag range we have run is logged in [`specs_tried.md`](specs_tried.md).

`compute_betas.csv` reports each stock under both timing rules (`timing_rule`) and three
specifications (`spec`: `base` = market only, `+qqq`, `+smh`). `b_gpu_change_vs_base` shows how much
of the compute beta the QQQ or SMH control absorbs. On the FAKE GPU series, adding QQQ moves b_gpu by
0.043 on average (same-day rule), against an average |b_gpu| of 0.076. That is noise, as expected
with a made-up GPU series. With real data, this is the test of whether a compute beta is just a
Nasdaq/AI factor.

- **Real:** stock returns and QQQ/SMH returns (Yahoo Finance adjusted close: splits and dividends),
  market factor and risk-free rate (Ken French daily factors).
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
| 0 | `gpu_timing.py` | (self-check) | nothing; the one GPU-to-trading-day rule every step imports |
| 1 | `poc.py` | `data/prices_adjusted/` (stocks, QQQ, SMH), `data/ornn_FAKE/` (H100), Ken French daily factors (downloaded) | `final_rows.csv` (one row = one stock on one trading day, primary timing rule), `compute_betas.csv` (one row = one stock × timing rule × spec) |
| 2 | `graph.py` | `final_rows.csv` | `levels.png`, `leadlag.png` (exploratory, with family-wise band) |
| 3 | `plot.py` | `final_rows.csv` | `correlation.png` |
| 4 | `make_chart.py` | `data/prices_adjusted/`, `data/ornn_FAKE/` (all six GPUs) | `stocks_vs_gpu.png/.html`, `correlation_daily.csv`, `correlation_weekly.csv` (primary rule), `correlation_*_next_day.csv` (other rule), `correlation_heatmap.png` |
| 5 | `make_correlation.py` | same as step 4 | `correlation_tests.png`, `leadlag_scan_test.csv` (multiple-testing check of the lag scan) |
| | `pull_etf_prices.py` | Yahoo Finance (network; not run by `run_all.py`) | `data/prices_adjusted/etf_adjusted_closing_prices_trading_days.csv` + metadata |
| | `app.py` | `outputs/final_rows.csv` | the Streamlit dashboard (Introduction, Methodology, Results, Explore) |

## Raw inputs

| Input | Source | Where |
|---|---|---|
| Stock prices | Yahoo Finance via `yfinance`, `auto_adjust=True`, pulled 2026-11-13 (see `stock_adjusted_close_metadata.json`) | `data/prices_adjusted/` |
| QQQ, SMH (factor controls) | Yahoo Finance via `yfinance`, `auto_adjust=True`, same window, pulled 2026-11-20 by `pull_etf_prices.py` (see `etf_adjusted_close_metadata.json`) | `data/prices_adjusted/` |
| Market factor, risk-free rate | Ken French Data Library, daily 3 factors | downloaded by `poc.py` each run |
| GPU rental prices | Ornn, through our professor. **Private**: never committed | `data/ornn/` (git-ignored) |
| GPU rental prices, FAKE | Made-up prices in Ornn's layout, so the code runs for anyone | `data/ornn_FAKE/` |

## Timing

A GPU price dated D can only move a stock once it is public. One function,
`map_gpu_to_trading_day` in `gpu_timing.py`, makes this call for every script (`poc.py`,
`make_chart.py`, `make_correlation.py`, and through `final_rows.csv`, `graph.py`, `plot.py` and `app.py`):

- **`same_day` (primary):** the price is set before the 4:00 pm ET close, so it belongs to day D's
  close if D is a trading day, and otherwise to the next trading day.
- **`next_day` (robustness):** the price is set after the close, so it belongs to the first trading
  day after D.

If several prices land on one trading day, the latest wins. `d_gpu` is the change from the previous
trading day.

**Why `same_day` is primary:** the two real Ornn exports we hold are stamped 17:00 UTC and 19:00 UTC,
which is 1:00 pm and 3:00 pm ET, before the close.

**Open question to Ornn (being sent; no answer yet):** *At what time, and in what time zone,
is each daily index print set? Is the 17:00/19:00 UTC stamp on the export the time the price was
fixed, or the time the file was generated?* We will record the answer here. Until then the timing
is an **open limitation**. It matters: on the FAKE series, 4 of 10 base compute betas change sign
between the two rules, so `compute_betas.csv` reports both.
