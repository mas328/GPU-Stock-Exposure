# GPU-Stock-Exposure

**Dashboard:** https://gpu-stock-exposure-3lbnphcqxaujhhmhoxlndv.streamlit.app/

**Team:** GPU Stock Exposure (Drew Hetzer, Matt Stugart, Cullen Kingston). Proposal:
[`PROPOSAL.md`](PROPOSAL.md). Current status: [`STATUS.md`](STATUS.md).

Do stock returns move with the price of renting GPU compute? For each stock we regress its daily
excess return on the market, a Nasdaq-100 control, and the daily change in a GPU rental price index
(the "compute beta"). Lead/lag correlations are exploratory.

## Main test (prespecified)

**b_gpu from `ex_ret = a + b_mkt·mkt_rf + b_gpu·d_gpu + b_ctrl·ex_qqq`, daily, one regression per
stock, GPU series = H100, timing rule = `same_day`, HC1 standard errors, with Newey–West (HAC,
5 lags) reported alongside** (the `primary == True` rows of `outputs/compute_betas.csv`; HAC in
`se_gpu_hac`, `t_gpu_hac`). Everything else is a robustness check or exploratory. Every
specification, correlation grid and lag range we have run is logged in [`specs_tried.md`](specs_tried.md).

`compute_betas.csv` reports each stock under both timing rules (`timing_rule`) and three
specifications (`spec`: `base` = market only, `+qqq`, `+smh`). `b_gpu_change_vs_base` shows how much
of the compute beta the QQQ or SMH control absorbs. On the FAKE GPU series, adding QQQ moves b_gpu by
0.043 on average (same-day rule), against an average |b_gpu| of 0.076. That is noise, as expected
with a made-up GPU series. With real data, this is the test of whether a compute beta is just a
Nasdaq/AI factor.

- **Real:** stock returns and QQQ/SMH returns (Yahoo Finance adjusted close: splits and dividends),
  market factor and risk-free rate (Ken French daily factors).
- **Estimation window:** **2024-06-25 to 2026-09-30**, 569 trading days per stock
  (`outputs/final_rows.csv`). Stock prices run 2023-12-12 to 2026-11-05, but the panel starts
  when the H100 series starts (FAKE H100 begins 2024-06-23) and ends at the last date in the pinned
  Ken French file (2026-09-30). `poc.py` prints the rows each merge drops.
- **FAKE:** the GPU price series, until the full Ornn history is available. Rows are tagged
  `gpu_source=FAKE`, so every beta and correlation is a placeholder, not a result.

## How to run (from the repo root)

```bash
pip install -r requirements.txt
python run_all.py          # deletes outputs/, rebuilds every table and figure, runs hand checks
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
| 1 | `poc.py` | `data/prices_adjusted/` (stocks, QQQ, SMH), `data/ornn_FAKE/` (H100), `data/ff_factors/` (Ken French, pinned) | `final_rows.csv` (one row = one stock on one trading day, primary timing rule), `compute_betas.csv` (one row = one stock × timing rule × spec) |
| 2 | `graph.py` | `final_rows.csv` | `levels.png`, `leadlag.png` (exploratory, with family-wise band) |
| 3 | `plot.py` | `final_rows.csv` | `correlation.png` |
| 4 | `make_chart.py` | `data/prices_adjusted/`, `data/ornn_FAKE/` (all six GPUs) | `stocks_vs_gpu.png/.html`, `correlation_daily.csv`, `correlation_weekly.csv` (primary rule), `correlation_*_next_day.csv` (other rule), `correlation_heatmap.png` |
| 5 | `make_correlation.py` | same as step 4 | `correlation_tests.png`, `leadlag_scan_test.csv` (multiple-testing check of the lag scan) |
| 6 | `hand_check.py` | raw inputs + `final_rows.csv`, `compute_betas.csv` | nothing; asserts one number per step recomputed by hand (return, d_gpu, ex_ret, main-test beta and HC1 SE) |
| | `pull_stock_prices.py` | Yahoo Finance (network; not run by `run_all.py`) | `data/prices_adjusted/` stock files + metadata |
| | `pull_etf_prices.py` | Yahoo Finance (network; not run by `run_all.py`) | `data/prices_adjusted/etf_adjusted_closing_prices_trading_days.csv` + metadata |
| | `make_fake_ornn.py` | nothing (seeded random numbers) | `data/ornn_FAKE/` |
| | `app.py` | `outputs/final_rows.csv` | the Streamlit dashboard (Introduction, Methodology, Results, Explore) |

## Raw inputs

| Input | Source | Where |
|---|---|---|
| Stock prices | Yahoo Finance via `yfinance`, `auto_adjust=True`, pulled 2026-11-13 (see `stock_adjusted_close_metadata.json`). `pull_stock_prices.py` is a **reconstruction** of the original pull script, which was not saved. A re-pull with it on 2026-11-20 matched the committed file: same 728 NYSE dates, returns within 0.006 bp, levels within 5×10⁻⁷ | `data/prices_adjusted/` |
| QQQ, SMH (factor controls) | Yahoo Finance via `yfinance`, `auto_adjust=True`, same window, pulled 2026-11-20 by `pull_etf_prices.py` (see `etf_adjusted_close_metadata.json`) | `data/prices_adjusted/` |
| Market factor, risk-free rate | Ken French Data Library, daily 3 factors, pulled 2026-11-20, last date 2026-09-30 (see `ff_factors_metadata.json`). Pinned so a new French release cannot silently change the betas; `python poc.py --refresh-ff` re-downloads it | `data/ff_factors/` |
| GPU rental prices | Ornn, through our professor. **Private**: never committed | `data/ornn/` (git-ignored) |
| GPU rental prices, FAKE | Made-up prices in Ornn's layout, so the code runs for anyone; made by `make_fake_ornn.py` (seed 331, reproduces the files byte for byte) | `data/ornn_FAKE/` |

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

## Lead/lag sign convention

Everywhere in this repo (`graph.py`, `make_correlation.py`, `multiple_testing.py`, `app.py`), a lead/lag
correlation at **lag L** is corr(stock return on day t, GPU change on day t − L). **Positive L = the GPU
change comes first (GPU leads); negative L = the stock moves first.** Lead/lag results are
exploratory (see `specs_tried.md`).

## Threats to validity

From the proposal, plus what the Checkpoint 2 audits raised. "Status" says what is done about each.

| Threat | Why it matters | Check / status |
|---|---|---|
| **GPU data is FAKE** | Every beta and correlation in `outputs/` is a placeholder. | Rows tagged `gpu_source=FAKE`; the dashboard warns. Real Ornn data goes in `data/ornn/` (git-ignored, never committed, per Ornn's request). |
| **GPU price timing** | A price set before the close belongs to that day's return; one set after belongs to the next. On the FAKE series the choice flips the sign of 4 of 10 betas. | One shared rule (`gpu_timing.py`); betas reported under both rules; question to Ornn pending (see Timing). **Open.** |
| **Compute beta is really a Nasdaq/AI factor** | AI news (earnings, model launches) can move GPU prices and AI stocks together. | QQQ control in the main test, SMH as a robustness check; `b_gpu_change_vs_base` shows how much they absorb. |
| **Searching many correlations** | About 800 correlations; some cross a single-test band by chance, and the "most exposed" firm is partly the luckiest. | One prespecified main test; every spec logged in `specs_tried.md`; lag scans labelled exploratory, with a simulated family-wise band. |
| **Levels look related by chance** | Two trending price series can look like they move together. | Inference uses daily changes only; `levels.png`, `stocks_vs_gpu.png` and the dashboard Levels view are captioned "descriptive only". |
| **Stale GPU prices / autocorrelation** | Rental prices may not update every day, so errors are autocorrelated and HC1 SEs are too small. | Newey–West (HAC, 5 lags) SEs reported next to HC1. |
| **One short regime** | About 2.3 years (2024-06-25 to 2026-09-30) is one AI-boom regime; results may not hold in a downturn. | Disclosed. Rolling 90-day correlations (`correlation_tests.png`) show stability within the sample only. |
| **Merges drop or duplicate rows** | Joins of returns, factors and GPU prices can silently lose dates. | `validate="m:1"` and unique-key asserts; `poc.py` prints the rows and dates each merge drops. |
| **Inputs change under us** | Yahoo re-adjusts history and French publishes new vintages. | Prices and French factors committed with pull dates; pull scripts in the repo. |
| **Calendar-day price files use a future close** | The weekend/holiday fill in `stock_adjusted_closing_prices_daily.csv` averages in the next close. | Those files are not used for returns; the pipeline reads the trading-day file only. |
