"""Hand checks: recompute one number per pipeline step independently, assert it matches.

Instructor audit A5 / project-seeds checklist item 8. Run after poc.py (run_all.py does it).
None of this code is shared with poc.py: it reads the RAW input files directly and uses plain
numpy arithmetic, so a bug in the pipeline would show up as a failed assert here.

  1. Stock return     NVDA on one date, from the raw adjusted-close file.
  2. GPU change       d_gpu on a MONDAY under the same_day rule, from the raw Ornn-layout file:
                      Monday's own print / Friday's print - 1 (Sat/Sun prints are superseded).
  3. Excess return    ex_ret = ret - rf for that row, rf straight from the pinned French file.
  4. Compute beta     NVDA b_gpu and its HC1 SE for the main test (same_day, +qqq), by
                      numpy least squares and the HC1 sandwich formula written out by hand.
"""
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
OUT = HERE / "outputs"
TICKER, DAY = "NVDA", pd.Timestamp("2025-03-10")          # a Monday inside the sample
TOL = 1e-10

rows = pd.read_csv(OUT / "final_rows.csv", parse_dates=["date"])
betas = pd.read_csv(OUT / "compute_betas.csv")
row = rows[(rows.ticker == TICKER) & (rows.date == DAY)].iloc[0]

# 1. stock return from raw prices
px = pd.read_csv(HERE / "data/prices_adjusted/stock_adjusted_closing_prices_trading_days.csv",
                 parse_dates=["date"]).set_index("date")[TICKER]
prev_trading_day = px.index[px.index.get_loc(DAY) - 1]
ret_hand = px[DAY] / px[prev_trading_day] - 1
assert abs(ret_hand - row.ret) < TOL, (ret_hand, row.ret)
print(f"1. {TICKER} return {DAY.date()}: hand {ret_hand:.8f} = pipeline {row.ret:.8f}  OK")

# 2. GPU change on a Monday, same_day rule, from the raw file
assert DAY.dayofweek == 0 and prev_trading_day == DAY - pd.Timedelta(days=3)
gpu = pd.read_csv(HERE / "data/ornn_FAKE/ornn-price-history-h100_FAKE.csv")
gpu = dict(zip(gpu.iloc[:, 0], gpu.iloc[:, 1]))
mon, fri = gpu[str(DAY.date())], gpu[str(prev_trading_day.date())]
d_gpu_hand = mon / fri - 1
assert abs(d_gpu_hand - row.d_gpu) < TOL, (d_gpu_hand, row.d_gpu)
print(f"2. d_gpu {DAY.date()} (Mon): {mon} / {fri} (Fri) - 1 = {d_gpu_hand:.8f} = pipeline  OK")

# 3. excess return with rf from the pinned French file (percent -> decimal)
ff = pd.read_csv(HERE / "data/ff_factors/F-F_Research_Data_Factors_daily.csv")
rf = ff.loc[ff["date"] == int(DAY.strftime("%Y%m%d")), "rf"].item() / 100
assert abs((ret_hand - rf) - row.ex_ret) < TOL
print(f"3. ex_ret = {ret_hand:.8f} - {rf:.6f} = {ret_hand - rf:.8f} = pipeline  OK")

# 4. main-test beta and HC1 SE by hand
g = rows[rows.ticker == TICKER].sort_values("date")
X = np.column_stack([np.ones(len(g)), g.mkt_rf, g.d_gpu, g.ex_qqq])
y = g.ex_ret.to_numpy()
b, *_ = np.linalg.lstsq(X, y, rcond=None)
e = y - X @ b
n, k = X.shape
XtX_inv = np.linalg.inv(X.T @ X)
V_hc1 = XtX_inv @ (X.T * e ** 2) @ X @ XtX_inv * n / (n - k)
se_hand = np.sqrt(V_hc1[2, 2])
main = betas[(betas.ticker == TICKER) & betas.primary].iloc[0]
assert main.spec == "+qqq" and main.timing_rule == "same_day"
assert abs(b[2] - main.b_gpu) < 1e-9 and abs(se_hand - main.se_gpu) < 1e-9, (b[2], se_hand, main)
print(f"4. {TICKER} main-test b_gpu: hand {b[2]:.6f} (SE {se_hand:.6f}) = "
      f"compute_betas.csv {main.b_gpu:.6f} ({main.se_gpu:.6f})  OK")
print("All hand checks passed.")
