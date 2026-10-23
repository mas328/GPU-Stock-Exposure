# Specifications tried

Every specification we run goes here, including the ones that didn't work. `outputs/specs_run_log.csv` is the machine log (every firm × spec, with sample dates and whether the GPU data was REAL or FAKE). This file explains *why* each one was run.

| # | Date | Spec | Firms | GPU series | GPU data | Why | Result / note |
|---|---|---|---|---|---|---|---|
| 1 | 2026-10-23 | S1 same-day, S2 +QQQ, S3 leads/lags ±2 | POC 5 (NVDA, MSFT, ORCL, PLTR, KO) | H100 / US / on-demand | FAKE | Checkpoint 1 proof of concept: test the pipeline end to end | Placeholder only; betas are meaningless on fake data |

## Judgment calls to revisit

- **Group assignments.** META is in AI-heavy software, but it is one of the largest GPU buyers. MSFT, AMZN, and GOOGL are both cloud providers *and* AI-software firms. ORCL, CRWV, and NBIS are closer to pure GPU rental.
- **GPU series.** H100 / US / on-demand is a placeholder until we see what Ornn provides.
- **Newey-West lags.** 5 trading days.
