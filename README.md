# GPU-Stock-Exposure

Which stocks are exposed to GPU compute prices? We regress each stock's return on the market and on the daily change in Ornn's GPU rental index. See **`ANALYSIS_PLAN.md`** for the full plan.

## Data rule: Ornn's data is private

Real Ornn files go in `data/ornn/`, which is git-ignored and never committed. `data/ornn_FAKE/` has made-up prices in **the exact same format** (`GPU, Timestamp (UTC), <GPU> hourly index (USD/GPU-hr)`, one file per GPU), so the code runs for anyone. Every output is tagged `gpu_source = REAL` or `FAKE`.

## Run (from the repo root)

```bash
pip install -r requirements.txt
python ornn_audit.py       # step 1: which GPU series, start dates, frequency, weekends/holidays
python pull_universe.py    # step 2: daily prices for universe.csv from yfinance
python poc.py              # proof of concept: 4 firms, same-day GPU beta
```

| File | What it is |
|---|---|
| `ornn.py` | Loads Ornn files (real or fake) and aligns GPU prices to the 4pm ET stock close |
| `ornn_audit.py` | Step 1 checks on the Ornn data |
| `make_fake_ornn.py` | Regenerates `data/ornn_FAKE/` |
| `ORNN_DATA_REQUEST.md` | What we have from Ornn so far and the draft request for the full history |
| `universe.csv` | 76 stocks + benchmarks, each with group, expected sign, and reason |
| `pull_universe.py` | Writes `data/prices/` (git-ignored) and `outputs/universe_coverage.csv` |
| `ANALYSIS_PLAN.md` | Step 3: one row of the dataset, the regression, and group comparisons |
| `poc.py` | Original proof of concept, now reading the Ornn-format fake |
