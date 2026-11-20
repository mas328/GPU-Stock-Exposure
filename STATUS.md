# Status (2026-11-20, responding to the Checkpoint 2 instructor audit)

Team GPU Stock Exposure: Drew Hetzer, Matt Stugart, Cullen Kingston. Seed 15, compute costs:
which stocks are exposed to GPU prices? Industry partner: Ornn. The Checkpoint 1 memo is in
[`archive/STATUS_checkpoint1.pdf`](archive/STATUS_checkpoint1.pdf).

## Where we are

- **The pipeline reproduces.** `python run_all.py` rebuilds every table and figure from committed
  inputs and ends with `hand_check.py`, which recomputes one number per step by hand and asserts it.
- **The GPU data is still FAKE.** Every beta and correlation is a placeholder. The real Ornn history
  stays local in `data/ornn/` (git-ignored).
- **Main test is prespecified** (README "Main test"): the daily H100 compute beta, controlling
  for the market and QQQ, with the `same_day` timing rule. Everything else is a robustness check or
  exploratory, and all of it is logged in `specs_tried.md`.

## Done since Checkpoint 2 (instructor audit findings)

| Audit | What we did |
|---|---|
| A1 timing | One shared GPU timing function (`gpu_timing.py`) used by every script. `same_day` is primary because Ornn's exports are stamped before the close; `next_day` is reported alongside. |
| A2 specs | `specs_tried.md` logs every regression and correlation grid; the lag scans carry a simulated family-wise band. |
| A3 factor | QQQ and SMH controls; `compute_betas.csv` shows b_gpu with and without them. |
| A4 inputs | Ken French file pinned in `data/ff_factors/`; merges print the rows they drop; stock-price pull script reconstructed and checked; FAKE-data generator restored; the actual window (2024-06-25 to 2026-09-30) is stated. |
| A5 files | `PROPOSAL.md` renamed; this `STATUS.md`; dashboard URL and threats to validity in the README; self-audit header filled; `hand_check.py`; pinned `requirements.txt`. |
| A6 conventions | One lead/lag sign convention (positive = GPU leads); levels charts captioned "descriptive only"; Newey–West SEs next to HC1. |

## Next

1. **Get Ornn's pricing time** (time and time zone of each daily print) and record it in the README.
   If prices are set after the close, switch `PRIMARY_RULE` to `next_day` and log it in `specs_tried.md`.
2. **Swap in the real Ornn history** and rerun. Only then do magnitudes mean anything: we will
   report what a 10% move in H100 rental prices implies for each stock's return.
3. **Extend the window** when Ken French publishes October 2026 (`python poc.py --refresh-ff`) and log
   the new vintage.
4. **Every teammate can explain every step** (seeds checklist item 10): walk through the pipeline together.

## Risks

- Ornn's data covers about two years, which is a single AI-boom regime.
- If real GPU prices are stale for days, daily betas will be weak; the HAC SEs and the 5-day
  correlations are the check.
