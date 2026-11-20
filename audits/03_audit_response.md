# Response to instructor audit 02 (Checkpoint 2)

**Team:** GPU Stock Exposure (Drew Hetzer, Matt Stugart, Cullen Kingston)
**Audited commit:** `e6d1e13` (main) · **Response branch:** `audit-response-phase1`
**Commits:** `fdf7f76` (A1, A2, A3) · `8c31ab0` (A4, A5, A6) · `36abe8a` (reproducible HTML) · this file

A note on commits: the audit asked for one commit per finding. We grouped them, A1–A3 in one commit and
A4–A6 in another, and pushed before splitting them. Rather than rewrite a shared branch, each entry
below lists the files that carry its fix, so `git show <commit> -- <file>` isolates it.

## Summary

| ID | Severity | Response | Where |
|---|---|---|---|
| A1 | Major | **Fixed**. Ornn's confirmed pricing time is **disclosed as a limitation** (open) | `fdf7f76`; README "Timing", "Threats to validity" |
| A2 | Major | **Fixed** | `fdf7f76`, `8c31ab0` |
| A3 | Major | **Fixed** | `fdf7f76` |
| A4 | Minor | **Fixed** | `8c31ab0` |
| A5 | Minor | **Fixed** (one self-audit line left for the team, see below) | `8c31ab0` |
| A6 | Minor | **Fixed**. "Two years is one regime" **disclosed as a limitation** | `8c31ab0`; README "Threats to validity" |

## Reproduction check (Phase 3)

On 2026-11-20 we made a fresh clone of `audit-response-phase1` at `36abe8a` and ran `python run_all.py`:
exit 0 in 26 s, no network download (Ken French is read from the pinned copy), and `hand_check.py`
passed. `git status` after the run showed **zero changed files**: every CSV, PNG and the HTML in
`outputs/` is byte-identical to what is committed. The panel runs 2024-06-25 to 2026-09-30, the
window the README states.

## A1 · GPU timing rule. Fixed; Ornn's time disclosed as a limitation

**What we did** (`fdf7f76`: `gpu_timing.py`, `poc.py`, `make_chart.py`, `make_correlation.py`, `README.md`, `app.py`)

- **One mapping function.** `map_gpu_to_trading_day()` in `gpu_timing.py` is now the only place the
  timing decision is made. `poc.py`, `make_chart.py` and `make_correlation.py` import it, and
  `graph.py`, `plot.py` and `app.py` read its output through `final_rows.csv`. The inline logic in
  `poc.py` and the `reindex(method="ffill")` in `make_chart.py` are gone. Running `python gpu_timing.py`
  self-checks both rules on a Fri–Tue example.
- **Primary rule is `same_day`.** We chose it because the two real Ornn exports we hold are stamped
  17:00 and 19:00 UTC (1:00 and 3:00 pm ET), before the close. `next_day`, the old `poc.py`
  assumption, is reported alongside it.
- **Both rules are reported.** `compute_betas.csv` has a `timing_rule` column. Like the audit, we find
  that 4 of 10 base betas change sign between the rules (NVDA −0.065 → +0.066, ORCL −0.020 → +0.132,
  VRT +0.049 → −0.034, PG −0.012 → +0.0005). `poc.py` prints this count on every run.

**Correlation files: why `correlation_daily.csv` and `correlation_weekly.csv` did not change.** The audit expected them to change. They
didn't, because the old `make_chart.py` forward-fill already paired a price dated D with day D's close,
which *is* the `same_day` rule. Moving to the shared function reproduced those files byte for byte. That
confirms the two code paths now agree; what changed is the betas, which used to follow `next_day`.
The other rule's correlations are in the new `correlation_daily_next_day.csv` and
`correlation_weekly_next_day.csv`.

**Disclosed as a limitation:** Ornn has not yet confirmed when each daily print is set. The question
is written out in the README "Timing" section, and the issue is listed as **open** under "Threats to
validity". If Ornn says prices are set after the close, we switch `PRIMARY_RULE` in `gpu_timing.py` to
`next_day` and log the change in `specs_tried.md`.

## A2 · No specs_tried.md; "best lag" search. Fixed

**What we did** (`fdf7f76`: `specs_tried.md`, `multiple_testing.py`, `graph.py`, `make_correlation.py`, `README.md`; `8c31ab0`: `specs_tried.md`)

- **`specs_tried.md`** logs 17 entries: every regression, correlation grid, lag range, GPU series and
  timing rule, with the date first run. It includes the October specs and the dashboard's interactive
  views. In total that is about 800 correlations and 70 regressions.
- **Prespecified main test** (README "Main test" and `specs_tried.md`): the H100 compute beta with
  market and QQQ controls, `same_day` timing, HC1 errors. These are the `primary == True` rows of
  `compute_betas.csv`. Everything else is labelled robustness or exploratory.
- **Multiple-testing correction for the lag scans.** `multiple_testing.py` simulates the largest |r|
  across a whole grid when there is no relationship. It circularly shifts the GPU series 2,000 times,
  which keeps each series' own autocorrelation. The 95th percentile is drawn as a red dashed band on
  `leadlag.png` and `correlation_tests.png`, with the Bonferroni band for comparison, and saved to
  `outputs/leadlag_scan_test.csv`. Both figures are titled "EXPLORATORY".
- **Result on the FAKE data.** PG's "best lag" r = −0.101, the example in the audit, crosses the
  single-test band (±0.073) but not the band for all 410 correlations (±0.134). The chance of a max
  |r| that large by luck alone is p = 0.91. No lag survives in either scan.

## A3 · Compute beta vs. a Nasdaq/AI factor. Fixed

**What we did** (`fdf7f76`: `pull_etf_prices.py`, `data/prices_adjusted/etf_*`, `poc.py`, `README.md`)

- **Control data.** QQQ and SMH adjusted closes are pulled with the same yfinance method and window
  as the stocks. They are committed with metadata, and their dates match the stock file exactly
  (728 days).
- **Specifications.** `compute_betas.csv` has a `spec` column: `base` (market only), `+qqq` and `+smh`,
  each under both timing rules. That is 60 rows. `b_gpu_base` and `b_gpu_change_vs_base` show how much
  each control absorbs.
- **Result on the FAKE data.** Under `same_day`, adding QQQ moves b_gpu by 0.043 on average, against an
  average |b_gpu| of 0.076. That is noise, as expected when the GPU series is made up. Under `next_day`
  we reproduce your NVDA number (−0.0652 → −0.0641). With real Ornn data, this is the test of whether a
  compute beta is a Nasdaq/AI factor in disguise. Both specifications are listed in `specs_tried.md`.

## A4 · Inputs not pinned; sample silently ends 2026-09-30. Fixed

**What we did** (`8c31ab0`: `poc.py`, `data/ff_factors/`, `pull_stock_prices.py`, `make_fake_ornn.py`, `README.md`, `PROPOSAL.md`)

- **Ken French is pinned.** The copy in `data/ff_factors/` is the file every run uses. Its pull date
  (2026-11-20) and last date (2026-09-30) are in `ff_factors_metadata.json`. `poc.py` downloads only if
  the file is missing or when run with `--refresh-ff`. The fresh-clone run above made no download.
- **Merge drops are printed.** For example: Ken French drops 260 rows (26 dates, 2026-10-01 to
  2026-11-05), and the GPU merge drops 1,320 rows (132 dates before H100 data starts). This delivers
  the check the proposal promised.
- **Price-pull script.** The original script was never committed. `pull_stock_prices.py` rebuilds it
  from `stock_adjusted_close_metadata.json` and is labelled as a reconstruction. A re-pull on
  2026-11-20 matched the committed file: same 728 NYSE dates, an identical imputation file, returns
  within 0.006 bp and levels within 5×10⁻⁷.
- **FAKE-data generator restored.** The copy from before `f490fed` is an older 4-chip version that
  does not produce the current files. We restored the 6-chip version from `75bddac`, without the Time
  column (as in `f40afb5`). It reproduces all six `data/ornn_FAKE/` files byte for byte.
- **Actual window stated.** README and `PROPOSAL.md` now give the estimation window, 2024-06-25 to
  2026-09-30 (569 days per stock), alongside the price data range (2023-12-12 to 2026-11-05), and
  explain both endpoints.

## A5 · Required items misnamed, stale or missing. Fixed

**What we did** (`8c31ab0`: renames, `STATUS.md`, `README.md`, `audits/01_self_audit.md`, `hand_check.py`, `run_all.py`, `requirements.txt`)

- **Proposal:** `Proposal.MD` → `PROPOSAL.md` (via `git mv`).
- **Status memo:** a new `STATUS.md` is current as of this response. The Checkpoint 1 PDF is kept at
  `archive/STATUS_checkpoint1.pdf`.
- **README:** has the dashboard URL (the separate `Streamlit app` file is deleted) and a
  **Threats to validity** table. It carries over the proposal's threats and adds the ones this audit
  raised, each with its status.
- **Self-audit:** header filled in (team, members, PR #4 link), template comments removed. *One line
  is still for the team to write: "Anything you found yourselves that the review missed."*
- **Hand check:** `hand_check.py` runs as the last step of `run_all.py`. Using raw input files and
  plain numpy, it recomputes one number per step and asserts each against the pipeline: an NVDA
  return, a Monday `d_gpu` under the `same_day` rule, the excess return, and the main-test b_gpu
  (0.120631) with its HC1 SE (0.067448, from the sandwich formula written out).
- **Pinned versions:** `requirements.txt` pins the nine packages the project uses, at the versions
  the pipeline was last run and checked with. We did not use a full `pip freeze`, which in our
  Anaconda environment would list hundreds of unrelated packages.

## A6 · Opposite lag conventions; levels charts; HC1 only. Fixed; one regime disclosed

**What we did** (`8c31ab0`: `graph.py`, `make_correlation.py`, `app.py`, `make_chart.py`, `poc.py`, `README.md`)

- **One sign convention.** Lag L means corr(stock on day t, GPU change on day t − L), and
  **positive L = GPU leads**. It is the same in `graph.py`, `make_correlation.py`,
  `multiple_testing.py` and the dashboard, uses the same axis label wording, and is stated in the
  README section "Lead/lag sign convention". `graph.py` was the file that flipped.
- **Levels are descriptive only.** `levels.png`, `stocks_vs_gpu.png`/`.html` and the dashboard's
  Levels view carry a "DESCRIPTIVE ONLY" caption. All inference uses daily changes.
- **HAC errors.** `compute_betas.csv` has `se_gpu_hac` and `t_gpu_hac` (Newey–West, 5 lags = one
  trading week) next to HC1 in every row. On the FAKE data they are close (NVDA main test: t = 1.79
  with HC1, 1.81 with HAC).
- **Disclosed as a limitation:** the sample is about 2.3 years, one AI-boom regime. This is listed in
  README "Threats to validity" and in `STATUS.md` under Risks.

## Also fixed

- **Self-audit item 14:** `stocks_vs_gpu.html` used to change on every run because plotly wrote a
  random div id. `36abe8a` fixes the id, which is why the fresh-clone rerun leaves zero files changed.
