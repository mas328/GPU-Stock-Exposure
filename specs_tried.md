# Specifications tried

Every regression, correlation grid, lag range, GPU series and timing rule we have run, **including
the ones that are exploratory or didn't work**, with the date first run. If a script computes it,
it is listed here. The GPU data is FAKE in every row so far, so every number is a placeholder.

## Main test (prespecified, 2026-11-20, before any REAL Ornn data is in the pipeline)

> **b_gpu from `ex_ret = a + b_mkt·mkt_rf + b_gpu·d_gpu + b_ctrl·ex_qqq`, daily, one regression
> per stock, GPU series = H100, timing rule = `same_day`, HC1 standard errors.**
> Row in `outputs/compute_betas.csv`: `primary == True`.
> The question is whether the 8 exposed stocks have b_gpu different from zero, and different
> from the controls KO and PG. Everything else below is a robustness check or exploratory.

Why this one: H100 has the longest Ornn history of the GPU series. The `same_day` rule matches the
time stamps on Ornn's real exports (17:00 and 19:00 UTC, before the 4:00 pm ET close; still
unconfirmed, see README "Timing"). The QQQ control is there so a compute beta isn't just the
Nasdaq/AI factor (instructor audit A3).

## Log

| # | First run | Script | Spec | Firms | GPU series | Timing rule | Lags | # stats | Role | Result / note |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 2026-10-23 | (Oct. version, removed) | S1 same-day beta: `ex_ret ~ mkt_rf + d_gpu` | POC 5 (NVDA, MSFT, ORCL, PLTR, KO) | H100 / US / on-demand | not recorded | 0 | 5 | Checkpoint 1 pipeline test | FAKE; placeholders |
| 2 | 2026-10-23 | (Oct. version, removed) | S2 = S1 + ex_qqq | POC 5 | H100 | not recorded | 0 | 5 | robustness | FAKE; placeholders |
| 3 | 2026-10-23 | (Oct. version, removed) | S3 = S1 + leads/lags of d_gpu ±2 | POC 5 | H100 | not recorded | −2..+2 | 25 | exploratory | FAKE; placeholders |
| 4 | 2026-11-13 | `poc.py` | `base`: `ex_ret ~ mkt_rf + d_gpu`, HC1 | 10 | H100 | `next_day` (17:00 ET assumption) | 0 | 10 | was the headline at Checkpoint 2 | FAKE. Superseded by #7 as headline; kept as robustness |
| 5 | 2026-11-13 | `graph.py` | corr(ex_ret_t, d_gpu_{t+k}) | 10 | H100 | `next_day` until 2026-11-20, then `same_day` | k = −5..+5 | 110 | exploratory | FAKE. Max \|r\| 0.126 < family-wise band 0.136 (p = 0.12) |
| 6 | 2026-11-13 | `plot.py` | scatter + corr(ex_ret, d_gpu), same day | 10 | H100 | as #5 | 0 | 10 | descriptive | FAKE |
| 7 | 2026-11-20 | `poc.py` | `+qqq`: base + ex_qqq | 10 | H100 | `same_day` | 0 | 10 | **MAIN TEST** | FAKE; placeholders |
| 8 | 2026-11-20 | `poc.py` | `+qqq` | 10 | H100 | `next_day` | 0 | 10 | timing robustness | FAKE |
| 9 | 2026-11-20 | `poc.py` | `base` | 10 | H100 | `same_day` | 0 | 10 | how much QQQ absorbs | FAKE. 4/10 b_gpu flip sign vs #4 (timing matters) |
| 10 | 2026-11-20 | `poc.py` | `+smh`: base + ex_smh | 10 | H100 | `same_day` and `next_day` | 0 | 20 | robustness (semiconductor factor) | FAKE |
| 11 | 2026-11-13 | `make_chart.py` | corr of 1-day returns, stock × GPU | 10 | A100, B200, B300, H100, H200, RTX PRO 6000 | `same_day` (was an inline ffill; same mapping) | 0 | 60 | descriptive | FAKE → `correlation_daily.csv` |
| 12 | 2026-11-13 | `make_chart.py` | corr of 5-day returns, stock × GPU | 10 | 6 GPUs | `same_day` | 0 | 60 | descriptive | FAKE → `correlation_weekly.csv` |
| 13 | 2026-11-20 | `make_chart.py` | #11 and #12 under the other rule | 10 | 6 GPUs | `next_day` | 0 | 120 | timing robustness | FAKE → `correlation_*_next_day.csv` |
| 14 | 2026-11-13 | `make_correlation.py` | weekly-return scatter + corr, stock vs GPU average | 10 | equal-weight avg of 6 GPU daily changes | `same_day` | 0 | 10 | descriptive | FAKE |
| 15 | 2026-11-13 | `make_correlation.py` | rolling 90-day corr, daily, stock vs GPU average | 10 | GPU average | `same_day` | 0 | 10 series | descriptive | FAKE |
| 16 | 2026-11-13 | `make_correlation.py` | lead-lag corr(ret_t, gavg_{t−lag}), "best lag" per stock | 10 | GPU average | `same_day` | −20..+20 | 410 | exploratory | FAKE. Max \|r\| 0.102 (PG, −18) passes the one-test band 0.073 but not the family-wise band 0.134 (p = 0.91) |
| 17 | 2026-11-13 | `app.py` | dashboard: `ex_ret ~ mkt_rf + d_gpu` + lead/lag k = −5..+5 on any date range the user picks | user-chosen | H100 | as `final_rows.csv` (`same_day` from 2026-11-20) | −5..+5 | user-driven | descriptive / interactive | Not a test; anything the viewer finds by changing dates is a search |

Total so far: about 800 correlations and 70 regressions. With that many, some will look
significant by chance. Only #7 is the test; the "most exposed" firm in any exploratory grid is
partly the luckiest one.

## How the exploratory scans are corrected for multiple testing

`multiple_testing.py` simulates the largest |r| across a whole grid when there is no relationship.
It circularly shifts the GPU series by a random offset (2,000 draws, seed 331), which keeps each
series' own autocorrelation but breaks any alignment between the GPU series and stock returns. The 95th
percentile is the family-wise band, drawn as a red dashed line on `leadlag.png` and
`correlation_tests.png` and saved in `outputs/leadlag_scan_test.csv`, with the Bonferroni band
for comparison. A bar inside that band is not evidence of a lead or lag.

## Judgment calls to revisit

- **Timing rule.** `same_day` is primary because of the time stamps on Ornn's exports. If Ornn
  says prices are set after 4:00 pm ET, switch `PRIMARY_RULE` in `gpu_timing.py` to `next_day`
  and log the change here; the main test is then #8.
- **Group assignments.** META is in AI-heavy software but is one of the largest GPU buyers.
  ORCL and IREN are closer to pure GPU rental.
- **GPU series.** H100 for the main test; the GPU average appears only in descriptive and
  exploratory work.
- **Standard errors.** HC1 for now. Newey–West (HAC, 5 lags) is planned (instructor audit A6).
