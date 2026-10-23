# GPU-Stock-Exposure (proof of concept)

`python poc.py` builds real rows of the firm x day panel for NVDA, MSFT, ORCL and KO
(control), Jan-Jun 2025, and estimates a same-day compute beta.

- **Real:** stock returns (yfinance), market factor and risk-free rate (Ken French daily).
- **FAKE:** the GPU price column, until Ornn data is available. Rows are tagged `gpu_source=FAKE`,
  so the betas are placeholders, not results.

Output: `final_rows.csv`.
