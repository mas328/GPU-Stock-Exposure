# Skeptical review: raw agent output (Checkpoint 2)

This file holds the coding agent's raw output. It is **not** the self-audit. The team writes
`audits/01_self_audit.md`: which findings are real, what was fixed, what's open, and the
10-point checklist.

**Prompt** (FIN331 Quick Reference, Starter prompts for coding agents, #5; how to rerun it is in
[`SKEPTICAL_REVIEW_PROMPT.md`](SKEPTICAL_REVIEW_PROMPT.md)):

> Review this repo like a skeptical finance professor. Look for look-ahead bias and leakage,
> merges without validate, unit and frequency mismatches, hard-coded paths or keys, and steps
> that don't reproduce from run_all.py. List issues ranked by severity; don't fix anything yet.

**Run on:** branch `checkpoint-2`, 2026-11-13, by Claude Code (Claude Opus 5.5), after
`python run_all.py` completed without errors.

## Findings, most severe first

### High

1. **Every GPU number is fake.** `poc.py`, `make_chart.py`, and `make_correlation.py` all read
   `data/ornn_FAKE/`. The two real Ornn files in `data/ornn/` have one row each. No beta or
   correlation in `outputs/` says anything about real GPU prices yet.

2. **The GPU timing assumption may be wrong.** `poc.py` treats each daily GPU print as set at
   17:00 ET (`GPU_PRICE_TIME_ET`), after the close, so it maps to the *next* trading day. The two
   real Ornn exports are stamped 17:00 and 19:00 **UTC**, which is 1–3 pm ET, *before* the close.
   If Ornn prices are set intraday, `d_gpu` is lagged one day relative to the stock return it
   should line up with, which biases the same-day beta toward zero.

3. **The chart scripts use a different (look-ahead) timing rule from `poc.py`.** In
   `make_chart.py` `build()`, the GPU price for trading day *t* is the last print *on or before*
   calendar date *t* (`reindex(days, method="ffill")`). Under `poc.py`'s 17:00 ET assumption, a
   print dated *t* is not public until after the close on *t*, so these charts use it one day
   early. `correlation_daily.csv`, `correlation_weekly.csv`, `correlation_heatmap.png`, and
   `correlation_tests.png` all inherit this. The two halves of the pipeline should share one rule.

### Medium

4. **The factor data is downloaded live and isn't pinned.** `poc.py` fetches Ken French's daily
   factors on every run. The file currently ends 2026-09-30, so the panel drops the last ~5 weeks
   of stock data (stocks run to 2026-11-05). Reruns after French updates will silently change the
   sample and the betas. Save a dated copy in `data/` or record the download date and end date
   in `outputs/`.

5. **There's no code that regenerates the stock prices.** `data/prices_adjusted/` was committed
   with a metadata file, but the script that pulled it isn't in the repo. Adjusted closes also
   depend on when they're pulled (`"adjustment_as_of": "Yahoo adjustments available at retrieval
   time"`). Provenance item 2 needs the pull script.

6. **The calendar-day price files contain look-ahead.** `data/prices_adjusted/*_daily.csv` and
   `stock_adjusted_closing_prices_daily.csv` fill weekends and holidays with
   `(previous close + next close) / 2`, which uses a future price. No current script reads them
   (the pipeline uses `..._trading_days.csv`), but nothing stops someone from using them later.

7. **Many tests, no log.** `make_correlation.py` checks 10 stocks × 41 lags against the GPU
   average and prints the "best lag" for each stock. `make_chart.py` adds 10 × 6 GPU series at
   two horizons. With that many correlations, a few will cross the ±0.073 noise band by chance
   (several already do on fake data). There's no `specs_tried.md`, and there's no multiple-testing
   adjustment.

8. **The lead/lag sign conventions are opposite.** In `graph.py` and `app.py`, negative *k* means
   the GPU leads. In `make_correlation.py`, positive lag means the GPU leads. Both are labeled
   correctly, but a reader comparing `leadlag.png` with `correlation_tests.png` will misread one
   of them.

9. **The "levels" charts can show spurious co-movement.** `stocks_vs_gpu.png` and `levels.png`
   plot cumulative levels. Any two trending series look related in levels. These charts should
   be labeled as descriptive only, and inference should rest on changes, which the betas and
   correlations already use.

### Low

10. **The standard errors are HC1, not Newey-West.** Daily returns and GPU changes may be
    autocorrelated, especially if GPU prices are sticky (many unchanged days). Newey-West
    errors would be safer.
11. **The compute beta isn't separated from a tech or AI factor.** There's no QQQ or SMH control
    yet, so a compute beta could just be an "AI sentiment" factor.
12. **`requirements.txt` isn't pinned to versions**, so a fresh machine may install newer pandas
    or yfinance with different behavior.
13. **`STATUS.md.pdf` at the repo root** isn't referenced anywhere and may be stale.
14. **`outputs/stocks_vs_gpu.html` changes on every run.** Plotly writes a random element ID into
    the file, so `git` shows it as modified after each `run_all.py` even when nothing changed.
    This doesn't affect any number, but it makes "did the outputs change?" harder to check.

### Checked and OK

- No hard-coded absolute paths or API keys in any `.py` file.
- `poc.py` merges use `validate="m:1"`, and `(ticker, date)` uniqueness is asserted.
- Stock returns are computed from the trading-day file only (no filled weekend prices), from
  prices adjusted for splits and dividends.
- `run_all.py` deletes `outputs/` and rebuilds all 11 outputs from scratch without errors. On a
  second run, `final_rows.csv`, `compute_betas.csv`, `correlation_daily.csv`, and
  `correlation_weekly.csv` came out byte-for-byte identical.
- Stock prices spot-checked: KO's adjusted closes match a fresh Yahoo download to within
  $0.0001. KO's and PG's near-zero market betas (−0.04 and 0.07) over Jun 2024 – Sep 2026 are
  in the data, not a bug.
- `data/ornn/` (private) is in `.gitignore`.
