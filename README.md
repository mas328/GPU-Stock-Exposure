# Compute Costs: Which Stocks Are Exposed to GPU Prices?

**Team AI Slop** (FIN 331, Fall 2026): Cullen Kingston, Drew Hetzer, Matt Stugart
**Industry partner:** [Ornn](https://ornn.com), which builds markets and price benchmarks for GPU compute.

## The question

Which companies' share prices are most exposed to the cost of compute? Do GPU rental prices and stock returns move together on the same day, and do changes in compute prices **lead or lag** changes in stocks?

Who would pay for the answer: Ornn and its customers (anyone hedging compute costs), a PM sizing AI exposure, or a CFO whose margins depend on GPUs.

## ⚠️ Data rule: Ornn's data is private

Ornn's GPU price data is **never posted publicly**: not in this repo, not in the dashboard, not anywhere else.

- The real files come from Ornn **through Prof. Bowen**. Put them in `data/raw/ornn/`. That folder is git-ignored.
- Everything built from them (`data/processed/`) is git-ignored too. Only aggregate regression coefficients go in `outputs/`.
- So the pipeline runs for anyone, we commit **`data/raw/ornn_FAKE.csv`**: random numbers with the same columns, made by `code/00_make_fake_ornn.py`.
- `04_gpu_prices.py` uses the real files if `data/raw/ornn/` has any CSVs, and the fake file otherwise. Every output row carries `gpu_source` = `REAL` or `FAKE`.

## The data

**Final panel:** one row = **firm × trading day**.

| ticker | date | group | ex_ret | mkt_rf | ex_qqq | d_gpu | d_gpu_lag1 | d_gpu_lead1 |
|---|---|---|---|---|---|---|---|---|
| NVDA | 2025-03-04 | chipmaker | 0.021 | 0.008 | 0.011 | -0.013 | 0.004 | 0.002 |
| MSFT | 2025-03-04 | cloud_provider | 0.006 | 0.008 | 0.011 | -0.013 | 0.004 | 0.002 |
| KO | 2025-03-04 | control | -0.002 | 0.008 | 0.011 | -0.013 | 0.004 | 0.002 |

(Fake rows for illustration.) `d_gpu` = log change in the GPU rental price since the previous trading day.

**Final output:** one row = **firm × specification**: compute beta, standard error, lead and lag coefficients, and group.

| Input | Source | How we get it |
|---|---|---|
| GPU rental prices (~2 years, daily) | Ornn, via Prof. Bowen | Placed by hand in `data/raw/ornn/` (private) |
| Daily stock returns | yfinance (adjusted close) | `code/02_returns.py` |
| Market factor and risk-free rate | Ken French data library (daily FF3) | `code/03_factors.py` |
| Nasdaq-100 / semiconductor controls | yfinance (QQQ, SMH) | `code/02_returns.py` |

Each downloaded file gets a `.provenance.json` next to it (source, pull time, settings).

## Firms (MVP: 30 in four groups)

| Group | Tickers |
|---|---|
| Chipmakers | NVDA, AMD, AVGO, TSM, MU, MRVL, INTC, ARM |
| Cloud / GPU providers | MSFT, AMZN, GOOGL, ORCL, CRWV, NBIS, IBM |
| AI-heavy software | META, PLTR, CRM, NOW, SNOW, ADBE, AI |
| Control (no compute exposure) | KO, PG, JNJ, WMT, XOM, DUK, MCD, PEP |

Groups are set in `config.py`. Borderline assignments (for example META, a huge compute buyer) are logged in `specs_tried.md`.

## Method

For each firm, with Newey-West standard errors:

- **S1, same-day compute beta:** `ex_ret = a + b_m·mkt_rf + b_gpu·d_gpu + e`
- **S2, net of tech:** adds `ex_qqq`, to test whether "compute beta" is just a Nasdaq or AI-sentiment factor in disguise
- **S3, lead-lag:** adds `d_gpu` at t−2 … t+2. A significant lag means GPU prices move first. A significant lead means stocks move first.

Then we compare betas across the four groups.

**Timing rule.** The GPU price for trading day *t* is the last observation dated on or before *t*. The change is measured from the previous trading day, so weekend and holiday moves roll into the next trading day. *To confirm with Ornn: what time of day is each price set, relative to the 4pm stock close?*

## How to run

```bash
python -m venv .venv && source .venv/bin/activate     # or a conda env
pip install -r requirements.txt
python run_all.py
```

`run_all.py` runs `code/00` … `code/06` in order and stops at the first failure. Downloads are reused on reruns; set `FORCE` in `config.py` to re-pull.

- For a proof-of-concept run on 5 firms, keep `POC_TICKERS` in `config.py` as is.
- For all 30 firms, set `POC_TICKERS = None`.

| Script | Reads | Writes |
|---|---|---|
| `00_make_fake_ornn.py` | — | `data/raw/ornn_FAKE.csv` |
| `01_firm_universe.py` | `config.py` | `data/processed/firms.csv` |
| `02_returns.py` | yfinance | `data/raw/yf_adj_close.csv`, `data/processed/returns.csv` |
| `03_factors.py` | Ken French site | `data/raw/ff3_daily.csv` |
| `04_gpu_prices.py` | Ornn (real or fake), returns | `data/processed/gpu_trading_day.csv` |
| `05_build_panel.py` | the above | `data/processed/panel_firm_day.csv` |
| `06_compute_betas.py` | panel | `outputs/compute_betas.csv`, `outputs/specs_run_log.csv` |

## Threats to validity (running list)

- **Spurious trends:** we use changes, never levels.
- **Timing:** when each day's GPU price is set relative to the stock close is unknown, and GPU prices exist on weekends. See the timing rule above.
- **Multiple testing:** the "most exposed" of 30 firms may look exposed by chance. Every firm × spec is logged in `outputs/specs_run_log.csv` and `specs_tried.md`.
- **Tech factor in disguise:** S2 controls for QQQ. We will also try SMH.
- **Short sample:** two years is one regime (the AI build-out). Results may not generalize.
- **Recent listings:** CRWV (IPO March 2025) and NBIS have shorter histories.
- **Factor data lag:** Ken French's daily file ends 1–2 months before today, so the most recent days drop out.
- **Private data:** auditors can rerun everything on the fake file but cannot reproduce our real-data numbers without Ornn's files.
