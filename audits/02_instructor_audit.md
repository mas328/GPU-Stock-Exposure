# Instructor audit: GPU Stock Exposure, Checkpoint 2

**Repo:** mas328/GPU-Stock-Exposure · **Audited commit:** `e6d1e13` (2026-11-13, `main`) · **Seed:** 15, compute costs: which stocks are exposed to GPU prices? (Ornn)

> Note from your human teacher: This review is generated with minimal supervision from Opus 5.5-high. It is thorough, but can be too generous at times and doesn't know my taste for what is "good". Grades it and I would assign are correlated, but noisy, ok? If you want additional feedback from _me_, you need to find me before/after/during class or during office hours for a guaranteed speedy reply. I will try to respond to emails and issues, but can not respond to student inquiries around the clock across the final weeks of class. Response times will be unpredictable, though during Thanksgiving week, I will do my best to respond quickly virtually, as in person options will be nil.

## Summary

The v0 pipeline reproduces. A fresh clone runs `run_all.py` in 17 seconds and rebuilds every committed table identically. My own independent code reproduces all ten compute betas and standard errors exactly. You follow the Ornn data rule: a FAKE file runs the pipeline, every row is tagged, and the dashboard warns. Your self-audit is candid and already names most of what I found. What matters before v1 is in this seed's audit list:
1. The GPU-price **timing** is handled two different ways in the pipeline, and on your own fake data the choice flips the sign of 4 of 10 betas (A1).
2. There is no `specs_tried.md` for the hundreds of correlations you compute (A2).
3. Nothing yet separates a compute beta from a Nasdaq/AI factor (A3).

| Check | Result |
|---|---|
| Reruns from scratch | ✅ `run_all.py`, exit 0, 16.7 s. `compute_betas.csv`, `final_rows.csv`, `correlation_daily.csv`, `correlation_weekly.csv` identical to committed (rtol 1e-6) |
| Inputs have provenance | ⚠️ stock prices have metadata (pull time) but no pull script; Ken French is downloaded live and unpinned; the FAKE-file generator was deleted (A4) |
| Keys unique, merges validated | ✅ `assert`s on (ticker, date) and `validate="m:1"` in `poc.py:81-88` |
| No look-ahead / survivorship | ⚠️ the chart and correlation scripts pair a GPU print with the same day's close (A1) |
| LLM leakage handled | n/a |
| `specs_tried.md` complete | ❌ missing (A2) |
| Magnitudes discussed | ⚠️ not yet (FAKE data, fair at v0) |
| Hand checks | ❌ none in the repo (your self-audit: "not yet") (A5) |
| Threats to validity | ⚠️ in `Proposal.MD`, not in the README (A5) |
| Every number traces to `outputs/` | ⚠️ the proposal's sample (Dec 12 2023 – Nov 5 2026) is not the panel's (2024-06-25 – 2026-09-30) (A4) |

## What holds up

- **Reproduces, and an independent recomputation matches.** I wrote separate code: my own XNYS calendar, my own Ken French download, your stated GPU timing rule, and numpy OLS with HC1 errors. It gives the same 10 rows as `outputs/compute_betas.csv`. The largest difference is 4e-16 in `b_gpu` and 1e-16 in `se_gpu`. Examples: ADBE `b_gpu` 0.1327 (SE 0.0682), VST −0.1799 (0.1081), n = 569 for every stock.
- **Committed stock prices check out.** A fresh yfinance pull (2026-11-15, `auto_adjust=True`) gives the same daily returns as `data/prices_adjusted/…_trading_days.csv`, within 0.006 bp, for all ten stocks. The file's dates are exactly the NYSE sessions, with none missing.
- **Data rule.** `data/ornn/` is git-ignored. The FAKE files are clearly named. `gpu_source` is on every row. The app shows a warning while the data is FAKE.
- **Changes, not levels.** The betas use `d_gpu` (percent change). Weekend and holiday prices roll onto the next trading day, with the latest price winning (`poc.py:59-78`).
- **Honest self-audit.** It marks the timing conflict, the factor truncation, the missing specs log and the missing hand checks as real problems.

## Findings

### A1 · Major · The GPU timing rule is inconsistent and unconfirmed, and it changes the answer

**Evidence:**
- `poc.py:57` assumes every GPU price is set at 17:00 ET, after the close, so a price dated D moves to the next trading day (`poc.py:63-73`).
- `make_chart.py:59` (`reindex(days, method="ffill")`) instead pairs a price dated D with day D's close. `correlation_daily.csv`, `correlation_weekly.csv`, `correlation_heatmap.png` and `correlation_tests.png` all use that same-day rule.
- Your review output (`audits/00_skeptical_review_output.md`, finding 2) says Ornn's real exports are stamped 17:00 and 19:00 UTC, which is before the U.S. close.
- I re-estimated the betas with the same-day rule instead of yours: **4 of 10 `b_gpu` change sign** (NVDA −0.065 → +0.066, ORCL −0.020 → +0.132, VRT +0.049 → −0.034, PG −0.012 → +0.001).

**Why it matters:** Timing is on this seed's audit list. A price set during the trading day belongs to that day's return; one set after the close belongs to the next. Using the wrong day either looks ahead or weakens the same-day beta toward zero, and on this sample the choice decides the sign.

**Fix:**
1. Ask Ornn exactly when each daily print is set (time and time zone), and record the answer in the README.
2. Put one mapping function in one module, and have `poc.py`, `make_chart.py` and `make_correlation.py` all import it.
3. Report the betas under both rules as a robustness check until the time is confirmed.

**How to show it's fixed:** The auditor will grep for one shared mapping function, confirm `correlation_*.csv` changes accordingly, and look for the confirmed time in the README.

### A2 · Major · No `specs_tried.md`, and many correlations are searched for the "best lag"

**Evidence:**
- `specs_tried.md` does not exist at `e6d1e13`. It existed in the October zip and was removed.
- `make_correlation.py:30-43` computes 10 stocks × 41 lags and prints each stock's "best lag".
- `make_chart.py:67-71` adds 10 stocks × 6 GPUs × 2 horizons, and `graph.py` another 10 × 11 lags. On FAKE data, several already cross the ±0.073–0.082 noise bands, e.g. PG's "best lag r = −0.101 at −18".

**Why it matters:** "Ranking many firms" is on this seed's audit list. With hundreds of correlations, some will look significant by chance, and the "most exposed" firm will partly be the luckiest.

**Fix:** Add `specs_tried.md` listing every regression, correlation grid, lag range, GPU series and timing rule you have run, with dates. Prespecify the main test (for example the same-day beta on H100, or on the GPU average). Treat the lag scan as exploratory, or correct it for multiple testing (Bonferroni or a simulation of the max |r| under no relationship).

**How to show it's fixed:** `specs_tried.md` exists and covers every grid in the code. The README names the main test.

### A3 · Major · Nothing separates a compute beta from a Nasdaq/AI factor

**Evidence:**
- `poc.py:98` regresses `ex_ret` on `mkt_rf` and `d_gpu` only.
- Your proposal's threat 2 ("add … a semiconductor index") and review finding 11 both name this. The October version had `ex_qqq` and `ex_smh` columns, which the reset dropped.
- I added QQQ's excess return as a control in my own code. It runs, and on FAKE data `b_gpu` barely moves (NVDA −0.0652 → −0.0641), as expected when the GPU series is noise. With real data it is the test that matters.

**Why it matters:** This is on the seed's list: "whether a compute beta is just an AI-sentiment or Nasdaq factor in disguise."

**Fix:** Add QQQ and/or SMH (or an equal-weighted AI basket) excess returns as controls. Report `b_gpu` with and without them, and note how much the controls absorb.

**How to show it's fixed:** `compute_betas.csv` has both specifications, and `specs_tried.md` lists them.

### A4 · Minor · Inputs aren't pinned, and the sample silently ends at 2026-09-30

**Evidence:**
- `poc.py:41-48` downloads Ken French's daily factors on every run, without saving a copy or a pull date. That file currently ends 2026-09-30, so the inner merge at `poc.py:81` drops every stock day after it. The panel is 2024-06-25 to 2026-09-30 (569 days per stock), while the prices run to 2026-11-05. The next update from French will change every beta without any code change.
- `Proposal.MD:18` gives the date range as Dec 12, 2023 to Nov 5, 2026.
- The script that pulled `data/prices_adjusted/` isn't in the repo (only `stock_adjusted_close_metadata.json`).
- The generator for `data/ornn_FAKE/` (`make_fake_ornn.py`) was deleted in `f490fed`.

**Why it matters:** Provenance and reproducibility. An auditor can't tell which factor vintage made a number, and the proposal's sample isn't the one estimated.

**Fix:**
- Save the French file you use to `data/` with its pull date (or record its end date in `outputs/`), and print rows dropped by each merge, as your proposal promises.
- Commit the price-pull script and the FAKE generator.
- Make the proposal and README state the actual estimation window.

**How to show it's fixed:** A fresh clone with no network for French still runs, and the README's sample dates match `final_rows.csv`.

### A5 · Minor · Required items are misnamed, stale or missing

**Evidence:**
- The proposal is `Proposal.MD`, not `PROPOSAL.md` (case matters on Linux and on GitHub links).
- The status memo is `STATUS.md.pdf`, still the Checkpoint 1 memo.
- `README.md:3` says the dashboard link is "coming", but the URL is in a separate file named `Streamlit app`.
- The README has no threats-to-validity section. Your threats are in `Proposal.MD:38-50`.
- `audits/01_self_audit.md:3-5` still has "_team name_", "_names_" and the template comments.
- There is no hand check in any script (self-audit item 8).
- `requirements.txt` is unpinned (e.g. `pandas>=2.0`, bare `yfinance`).

**Fix:**
- Rename to `PROPOSAL.md`, and replace the PDF with a current `STATUS.md`.
- Put the URL in the README, and add a threats section there.
- Finish the self-audit header.
- Add one independent hand check, e.g. one stock's beta via `np.polyfit` or by hand, asserted against `compute_betas.csv`.
- Pin versions (`pip freeze`).

**How to show it's fixed:** The auditor will check each file and rerun the hand check.

### A6 · Minor · Lead/lag sign conventions are opposite in two figures, and levels charts invite spurious reads

**Evidence:**
- `graph.py:28-30`: k < 0 means "GPU leads".
- `make_correlation.py:3,30-35`: lag > 0 means "GPU price change comes first".
- `levels.png` and `stocks_vs_gpu.png` plot levels, rebased.
- HC1 errors (`poc.py:98`) ignore autocorrelation. Your FAKE GPU series is AR(1), and real rental prices may be stale for days.

**Why it matters:** Two of this seed's audit items: "use changes, not levels" for anything inferential, and the lead/lag direction is the question. A reader comparing the two figures will read opposite conclusions.

**Fix:** Pick one sign convention and label it the same everywhere. Caption the levels charts as descriptive only. Report Newey–West (HAC) errors next to HC1, and note that two years is one regime.

**How to show it's fixed:** Both figures use the same axis label and sign, and `compute_betas.csv` has a HAC SE column.

## How to respond

This audit is `audits/02_instructor_audit.md` in your repo. Fix what you can, then add `audits/03_audit_response.md`, replying to each finding ID: fixed (the commit), disputed (why), or disclosed as a limitation (where).

**Deadline: Saturday, November 21, 2026.**
