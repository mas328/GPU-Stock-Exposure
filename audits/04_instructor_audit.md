# Instructor audit: GPU Stock Exposure, Checkpoint 3

**Repo:** mas328/GPU-Stock-Exposure · **Audited commit:** `19b7b0f` (2026-11-20, `main`, merge of PR #7) · **Seed:** 15, compute costs: which stocks are exposed to GPU prices? (Ornn) · **CP2 audit:** `audits/02_instructor_audit.md` (commit `e6d1e13`)

> Note from your human teacher: This review is generated with minimal supervision from Opus 5.5-high. It is thorough, but can be too generous at times and doesn't know my taste for what is "good". Grades it and I would assign are correlated, but noisy, ok? If you want additional feedback from _me_, you need to find me before/after/during class or during office hours for a guaranteed speedy reply. I will try to respond to emails and issues, but can not respond to student inquiries around the clock across the final weeks of class. Response times will be unpredictable, though during Thanksgiving week, I will do my best to respond quickly virtually, as in person options will be nil.

## Summary

An exemplary response to the CP2 audit: all six findings are fixed, each with evidence that checks out.
- `python run_all.py` from a fresh copy runs in 22 s, the hand check passes, and every CSV in `outputs/` is identical.
- My own OLS reproduces all 10 primary compute betas, with both HC1 and Newey–West errors, exactly. My own `same_day` mapping reproduces the GPU changes.
- You still follow the Ornn data rule: nothing real is in the repo or its history.

What's missing is v1 itself (B1). Every committed number is still on the FAKE GPU series and 10 firms. You have the real Ornn data, so run the pipeline on it locally, keep the data itself out of the repo (as you do now), and commit the results. The seed's MVP is also 30 firms in clear groups.

## Follow-up on your Checkpoint 2 audit

Response file: `audits/03_audit_response.md` found (on `main`).

| CP2 finding | Status | Evidence |
|---|---|---|
| A1 · GPU timing rule inconsistent | fixed | `gpu_timing.py:27` `map_gpu_to_trading_day()` is used by `poc.py`, `make_chart.py` and `make_correlation.py`. `compute_betas.csv` has both rules in `timing_rule` (60 rows), and the `correlation_*_next_day.csv` files exist. Ornn's print time is disclosed as an open limitation (README "Timing", threats table). My own `same_day` mapping of `ornn-price-history-h100_FAKE.csv` reproduces `d_gpu` in `final_rows.csv` (max difference 1e-16, 568 days) |
| A2 · No `specs_tried.md`; best-lag search | fixed | `specs_tried.md` (17 entries). `multiple_testing.py` writes `leadlag_scan_test.csv`, which regenerated identically. The README names the main test (`+qqq`, `same_day`, HC1: the `primary == True` rows) |
| A3 · Nasdaq/AI factor | fixed | `compute_betas.csv` `spec` ∈ {`base`, `+qqq`, `+smh`} × both rules. QQQ/SMH prices are committed with metadata (`data/prices_adjusted/etf_*`) |
| A4 · Inputs not pinned; silent 2026-09-30 end | fixed | Ken French is pinned in `data/ff_factors/` with `ff_factors_metadata.json`. The README and `PROPOSAL.md` state the 2024-06-25 to 2026-09-30 window, which matches `final_rows.csv` (569 days per stock). `make_fake_ornn.py` and `pull_stock_prices.py` are restored |
| A5 · Required items misnamed or missing | fixed | `PROPOSAL.md`, a current `STATUS.md` and a README threats table all exist. `hand_check.py` runs last in `run_all.py` and passed. `requirements.txt` pins 9 packages, and a venv built from it ran everything |
| A6 · Lag sign conventions; levels charts; HC1 only | fixed | One convention ("positive L = GPU leads") across the scripts and README. `se_gpu_hac`/`t_gpu_hac` are in every row of `compute_betas.csv`, and match my own Newey–West (Bartlett, 5 lags). Levels charts are labeled descriptive only |

**6 of 6 fixed, 0 still open.**

## Checkpoint 3 checks

| Check | Result |
|---|---|
| Reruns from scratch (full sample) | ⚠️ ✅ reruns exactly, but on the FAKE GPU series and 10 firms (B1) |
| Inputs have provenance | ✅ metadata JSON for prices, ETFs and French; the FAKE generator is seeded and reproduces its files |
| Keys unique, merges validated | ✅ `(ticker, date)` asserted; merge drops printed |
| No look-ahead / survivorship | ✅ timing handled with both rules. Firms chosen with hindsight is disclosed |
| LLM leakage handled | n/a |
| `specs_tried.md` complete | ✅ |
| Magnitudes discussed | ❌ not possible on FAKE data. STATUS plans "a 10% move in H100 prices implies…" (B1) |
| Hand checks | ✅ `hand_check.py` (NVDA return, Monday `d_gpu`, excess return, main-test b_gpu and its HC1 SE by hand) |
| Threats to validity | ✅ README threats table, with status per item |
| Every number traces to `outputs/` | ✅ |
| Dashboard matches `outputs/` | ✅ reads `final_rows.csv` and `compute_betas.csv` (`app.py:20-26`). "Period: 2024-06-25 to 2026-09-30 (569 trading days)" matches `final_rows.csv` |

Steps not rerun by design: none. The default run uses only committed files.

## Getting ready for Dec 1

Presentations run only from URLs, with a hard cutoff at 9 minutes (10:45 section) or 10 minutes (12:10 section). Put your URL(s) in column G of the Team Projects sheet.

| Check | Result |
|---|---|
| Dashboard launches from a clean clone | ✅ `streamlit run app.py --server.headless true --server.port 8605` (venv from `requirements.txt`) on a clean export of `19b7b0f`: `/_stcore/health` returned `ok` after 3 s. A headless browser clicked all 4 tabs, with no exceptions on the page or in the log |
| Dashboard shows the v1 numbers from `outputs/` | ⚠️ it reads `outputs/` and labels every result "FAKE … a placeholder, not a finding", which is honest. But there is no v1 result to show (B1) |
| README links the live URL(s) | ✅ `README.md:3` links the `…streamlit.app` dashboard (the live site itself wasn't checked). `requirements.txt` pins `streamlit==1.62.0` and the rest |

**Core story for 9–10 minutes:** the question and who would pay; the compute beta with QQQ control as the prespecified test; the timing problem (both rules); then the real-data compute betas by group, with the FAKE run as a one-line check that the pipeline finds nothing when there is nothing (true beta 0).

## What holds up

- **Exact reproduction.** `run_all.py` (exit 0, 21.6 s) reproduces `compute_betas.csv` (60 × 18, max relative difference 8e-15), `final_rows.csv` (5,690 × 14), the four correlation files and `leadlag_scan_test.csv`. The PNGs and `stocks_vs_gpu.html` differ in bytes here: the HTML only in the last bits of plotly's encoded floats, so it's platform numerics, not your code. Your "zero changed files" holds on your machine, not on every machine.
- **Independent regressions.** My own OLS of `ex_ret` on `mkt_rf`, `d_gpu` and `ex_qqq` per firm (n = 569) reproduces `b_gpu`, `se_gpu` (HC1) and `se_gpu_hac` (Newey–West, Bartlett, 5 lags) for all 10 primary rows to 1e-15. For example, NVDA is 0.120631 (HC1 SE 0.067448, HAC 0.066635), and IREN is 0.258364 (0.210630).
- **Multiple-testing done right.** The circular-shift simulation keeps each series' autocorrelation, and the dashboard prints both bands ("±0.082 … ±0.136 … p = 0.12").
- **Seed 15 items:** changes not levels; both timing rules; weekend prices; every firm logged; the QQQ/SMH control; and private data handled by the rule.

## New findings

### B1 · Blocking · v1 results don't exist yet: FAKE GPU data, and 10 firms rather than 30

**Evidence:** Every row of `final_rows.csv` and `compute_betas.csv` has `gpu_source = FAKE`. README threats ("GPU data is FAKE … Every beta and correlation in `outputs/` is a placeholder") and `STATUS.md` ("Swap in the real Ornn history and rerun") say so too. The panel has 10 tickers (ADBE, AMD, IREN, KO, META, NVDA, ORCL, PG, VRT, VST). Seed 15's MVP is "30 firms in clear groups (chipmakers, cloud providers, AI-heavy software, and a control group)".

**Why it matters:** Checkpoint 3 was v1 on the full sample. On FAKE data the true compute beta is zero by construction, so there is nothing to report about GPU exposure. The real series is what Ornn and your audience care about. With 10 firms, the group comparisons rest on 2 controls and a handful per group.

**Fix:**
1. **Firms:** grow the list to about 30 in fixed groups, logged in `specs_tried.md` before running.
2. **Real data, locally:** put the Ornn files in `data/ornn/` (already git-ignored) and run the same pipeline on them. The Ornn prices themselves never go in the repo, the dashboard or any output file: no price levels or changes, only estimates (betas, SEs, lead/lag coefficients), labeled `gpu_source = Ornn`. That means a real-data `final_rows.csv` (it has `gpu_price` and `d_gpu`) stays local, and the dashboard's levels and lead-lag views either run on FAKE or show only estimates.
3. **Keep the FAKE path** as the default run, so anyone can still rerun the code, and say in the README which committed outputs come from the real data.

**How to show it's fixed:** about 30 tickers in 4 groups, and a committed table of real-data compute betas, with no Ornn price series anywhere in the repo or its history. I will rerun `run_all.py` (FAKE) and the independent regressions.

### B2 · Minor · Don't read `b_mkt` in the `+qqq` specification

**Evidence:** `compute_betas.csv`, `+qqq`, `same_day`: `b_mkt` = −2.23 (AMD), −0.60 (NVDA), −0.59 (VRT), −0.58 (IREN). The market and QQQ excess returns are highly collinear (correlation 0.946 over the 569 days in `final_rows.csv`), so in that specification `b_mkt` is the market beta net of QQQ, not a market beta.

**Fix:** Don't show or interpret `b_mkt` from the `+qqq`/`+smh` rows, or label it as such. Report the market beta from `base`, and the correlation between `mkt_rf` and `ex_qqq` in the sample.

**How to show it's fixed:** The dashboard and README use `base` market betas, or label the conditional ones.

## How to respond

This audit is `audits/04_instructor_audit.md` in your repo. Fix what you can, then add `audits/05_audit_response.md`, replying to each **B** finding (no CP2 findings are still open): fixed (the commit), disputed (why), or disclosed as a limitation (where).

There's no separate deadline for this response. Keep working through these until your final deliverables are due: the final repo is audited again then.
