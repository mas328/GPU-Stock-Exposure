"""Proof of concept: build real rows of the firm x day panel for 4 firms and
estimate a same-day compute beta.

Real:  stock returns (yfinance), market factor and risk-free rate (Ken French daily).
FAKE:  the GPU price column (random walk) until Ornn data arrives. Every row is
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

# 3. GPU price -> stock trading day it can actually affect (FAKE prices, real timing logic)
# Stocks only react after a price is public, and the market closes at 4:00 pm ET.
# A price set at or before 4:00 pm ET on a trading day belongs to that day; a price set
# after 4:00 pm ET, or on a weekend/holiday, belongs to the NEXT trading day.
# ASSUMPTION: Ornn's pricing time is unknown; GPU_PRICE_TIME_ET is a placeholder.
GPU_PRICE_TIME_ET = "17:00"
MARKET_CLOSE_ET = "16:00"
GPU_CSV = Path("gpu_FAKE.csv")
if not GPU_CSV.exists():
    rng = np.random.default_rng(0)
    cal = pd.date_range(pd.Timestamp(START) - pd.Timedelta(days=10), END, freq="D")  # incl. weekends
    pd.DataFrame({"timestamp_et": cal.strftime("%Y-%m-%d ") + GPU_PRICE_TIME_ET,
                  "price_usd_per_gpu_hour": 2.4 * np.exp(np.cumsum(rng.normal(0, 0.015, len(cal)))),
                  "gpu_source": "FAKE"}).to_csv(GPU_CSV, index=False)
raw = pd.read_csv(GPU_CSV)
raw["set_at"] = pd.to_datetime(raw["timestamp_et"]).dt.tz_localize("America/New_York")

trading_days = pd.DatetimeIndex(sorted(ret["date"].unique()))
set_date = raw["set_at"].dt.tz_localize(None).dt.normalize()
before_close = raw["set_at"].dt.strftime("%H:%M") <= MARKET_CLOSE_ET
on_trading_day = set_date.isin(trading_days)
# same day if set before the close on a trading day, otherwise the next trading day
side = np.where(before_close & on_trading_day, "left", "right")
idx = np.where(side == "left", trading_days.searchsorted(set_date, "left"),
               trading_days.searchsorted(set_date, "right"))
raw["date"] = [trading_days[i] if i < len(trading_days) else pd.NaT for i in idx]
# if several prices land on one trading day (e.g. weekend + Monday), use the latest
gpu = (raw.dropna(subset=["date"]).sort_values("set_at").groupby("date")
          .agg(gpu_price=("price_usd_per_gpu_hour", "last"), gpu_set_at=("timestamp_et", "last"),
               gpu_source=("gpu_source", "last")))
gpu["d_gpu"] = gpu["gpu_price"].pct_change()
gpu = gpu.dropna(subset=["d_gpu"]).reset_index()

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
