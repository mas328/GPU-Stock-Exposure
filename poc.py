"""Proof of concept: build real rows of the firm x day panel for 4 firms and
estimate a same-day compute beta.

Real:  stock returns (yfinance), market factor and risk-free rate (Ken French daily).
FAKE:  the GPU price column (data/ornn_FAKE/, Ornn format) until Ornn data arrives. Every row is
       labelled gpu_source=FAKE and the beta is a placeholder, not a result.

Run: python poc.py   ->  final_rows.csv
"""
import io
from pathlib import Path
import urllib.request
import zipfile

import numpy as np
import pandas as pd
import statsmodels.api as sm
import yfinance as yf

from ornn import gpu_on_trading_days, load_ornn

TICKERS = ["NVDA", "MSFT", "ORCL", "KO"]          # KO = control
START, END = "2025-01-01", "2025-06-30"
FF_URL = ("https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/"
          "F-F_Research_Data_Factors_daily_CSV.zip")

# 1. Returns (real)
px = yf.download(TICKERS, start=START, end=END, auto_adjust=True, progress=False)["Close"]
ret = px.pct_change().dropna(how="all").stack().rename("ret").reset_index()
ret.columns = ["date", "ticker", "ret"]

# 2. Fama-French market factor + risk-free (real); French publishes percent
with urllib.request.urlopen(FF_URL, timeout=60) as r:
    zf = zipfile.ZipFile(io.BytesIO(r.read()))
lines = [l for l in zf.read(zf.namelist()[0]).decode("latin-1").splitlines()
         if l[:8].strip().isdigit() and len(l.split(",")) == 5]
ff = pd.read_csv(io.StringIO("\n".join(lines)), header=None,
                 names=["date", "mkt_rf", "smb", "hml", "rf"])
ff["date"] = pd.to_datetime(ff["date"].astype(str).str.strip(), format="%Y%m%d")
ff[["mkt_rf", "rf"]] /= 100

# 3. GPU price change: real Ornn files in data/ornn/ if present, else data/ornn_FAKE/
#    (same format). Price as of each trading day's 4pm ET close; see ornn.py.
ornn, gpu_source = load_ornn()
days = pd.DatetimeIndex(sorted(ret["date"].unique()))
gpu = gpu_on_trading_days(ornn, "H100", days)[["date", "d_gpu"]].assign(gpu_source=gpu_source)

# 4. Panel
panel = (ret.merge(ff[["date", "mkt_rf", "rf"]], on="date")
            .merge(gpu, on="date")
            .assign(ex_ret=lambda d: d["ret"] - d["rf"])
            .sort_values(["ticker", "date"]).reset_index(drop=True))
assert not panel.duplicated(["ticker", "date"]).any() and panel.notna().all().all()
panel.to_csv("final_rows.csv", index=False)
print(f"{len(panel)} rows, {panel.ticker.nunique()} firms, "
      f"{panel.date.min().date()} to {panel.date.max().date()}")
print(panel.groupby("ticker").head(2).to_string(index=False))

# 5. Proof of concept: ex_ret = a + b_mkt*mkt_rf + b_gpu*d_gpu
print("\nSame-day compute betas (GPU column is FAKE -> placeholders):")
for t, g in panel.groupby("ticker"):
    m = sm.OLS(g["ex_ret"], sm.add_constant(g[["mkt_rf", "d_gpu"]])).fit(cov_type="HC1")
    print(f"{t:5s} n={int(m.nobs)}  b_mkt={m.params['mkt_rf']:.2f}  "
          f"b_gpu={m.params['d_gpu']:.3f}  t={m.tvalues['d_gpu']:.2f}")
