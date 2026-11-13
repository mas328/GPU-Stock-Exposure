# GPU-Stock-Exposure (proof of concept)

`python poc.py` builds real rows of the firm x day panel for NVDA, MSFT, ORCL and KO
(control), Jan-Jun 2025, and estimates a same-day compute beta.

- **Real:** stock returns (yfinance), market factor and risk-free rate (Ken French daily).
- **FAKE:** the GPU price column, until Ornn data is available. Rows are tagged `gpu_source=FAKE`,
  so the betas are placeholders, not results.

Output: `final_rows.csv`.

## Timing

Each GPU price is mapped to the stock trading day it can actually affect: set at or before
4:00 pm ET on a trading day -> that day; set after 4:00 pm ET, or on a weekend/holiday -> the
next trading day (the latest price wins if several land on one day). `d_gpu` is the change in
that price from the previous trading day. Ornn's real pricing time is unknown, so
`GPU_PRICE_TIME_ET` in `poc.py` (currently 17:00) is a placeholder.
