"""Build the firm x day panel for the ten study stocks and estimate a same-day compute beta.

Real:  stock returns (Yahoo Finance adjusted close, committed in data/prices_adjusted/),
       market factor and risk-free rate (Ken French daily factors, downloaded on each run).
FAKE:  the GPU price column (data/ornn_FAKE/, same layout as Ornn's export) until the
       real Ornn history arrives. Every row is labelled gpu_source=FAKE and the betas are
       placeholders, not results.

Run from the repo root:  python poc.py
Writes: outputs/final_rows.csv     one row = one stock on one trading day
        outputs/compute_betas.csv  one row = one stock (same-day compute beta)
"""
import io
from pathlib import Path
import urllib.request
import zipfile

import numpy as np
import pandas as pd
import statsmodels.api as sm

HERE = Path(__file__).resolve().parent
OUT = HERE / "outputs"
PRICES_CSV = HERE / "data/prices_adjusted/stock_adjusted_closing_prices_trading_days.csv"
GPU_CSV = HERE / "data/ornn_FAKE/ornn-price-history-h100_FAKE.csv"   # primary series: H100
GPU_SOURCE = "FAKE" if "FAKE" in GPU_CSV.name else "REAL"
CONTROLS = ["KO", "PG"]                                                # no compute exposure
FF_URL = ("https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/"
          "F-F_Research_Data_Factors_daily_CSV.zip")

# 1. Returns (real): adjusted close on NYSE trading days only, so no filled weekend prices
px = pd.read_csv(PRICES_CSV, parse_dates=["date"]).set_index("date").sort_index()
assert px.index.is_unique, "duplicate price dates"
assert (px > 0).all().all(), "prices must be positive"
TICKERS = list(px.columns)
ret = px.pct_change(fill_method=None).iloc[1:].stack().rename("ret").reset_index()
ret.columns = ["date", "ticker", "ret"]
assert ret["ret"].abs().max() < 1, "a daily return of 100%+ usually means a bad price"

# 2. Fama-French market factor + risk-free (real); French publishes percent
with urllib.request.urlopen(FF_URL, timeout=60) as r:
    zf = zipfile.ZipFile(io.BytesIO(r.read()))
lines = [l for l in zf.read(zf.namelist()[0]).decode("latin-1").splitlines()
         if l[:8].strip().isdigit() and len(l.split(",")) == 5]
ff = pd.read_csv(io.StringIO("\n".join(lines)), header=None,
                 names=["date", "mkt_rf", "smb", "hml", "rf"])
ff["date"] = pd.to_datetime(ff["date"].astype(str).str.strip(), format="%Y%m%d")
ff[["mkt_rf", "rf"]] /= 100
assert ff["date"].is_unique

# 3. GPU price -> the stock trading day it can actually affect (no look-ahead)
# Stocks only react after a price is public, and the market closes at 4:00 pm ET.
# A price set at or before 4:00 pm ET on a trading day belongs to that day; a price set
# after 4:00 pm ET, or on a weekend/holiday, belongs to the NEXT trading day.
# ASSUMPTION: the Ornn file gives one price per calendar date with no time of day, so we
# treat it as set at GPU_PRICE_TIME_ET (after the close). Placeholder until Ornn confirms.
GPU_PRICE_TIME_ET = "17:00"
MARKET_CLOSE_ET = "16:00"
raw = pd.read_csv(GPU_CSV)
raw.columns = ["gpu_date", "price_usd_per_gpu_hour"]
raw["gpu_date"] = pd.to_datetime(raw["gpu_date"])
raw = raw.drop_duplicates("gpu_date", keep="last").dropna()
raw["set_at"] = pd.to_datetime(raw["gpu_date"].dt.strftime("%Y-%m-%d ") + GPU_PRICE_TIME_ET)

trading_days = pd.DatetimeIndex(sorted(ret["date"].unique()))
set_date = raw["set_at"].dt.normalize()
before_close = raw["set_at"].dt.strftime("%H:%M") <= MARKET_CLOSE_ET
on_trading_day = set_date.isin(trading_days)
# same day if set before the close on a trading day, otherwise the next trading day
idx = np.where(before_close & on_trading_day,
               trading_days.searchsorted(set_date, "left"),
               trading_days.searchsorted(set_date, "right"))
raw["date"] = [trading_days[i] if i < len(trading_days) else pd.NaT for i in idx]
# if several prices land on one trading day (e.g. weekend + Monday), use the latest
gpu = (raw.dropna(subset=["date"]).sort_values("set_at").groupby("date")
          .agg(gpu_price=("price_usd_per_gpu_hour", "last"), gpu_set_at=("set_at", "last")))
gpu["d_gpu"] = gpu["gpu_price"].pct_change()
gpu = gpu.dropna(subset=["d_gpu"]).reset_index().assign(gpu_source=GPU_SOURCE)

# 4. Panel: one row = one stock on one trading day
panel = (ret.merge(ff[["date", "mkt_rf", "rf"]], on="date", how="inner", validate="m:1")
            .merge(gpu, on="date", how="inner", validate="m:1")
            .assign(ex_ret=lambda d: d["ret"] - d["rf"],
                    group=lambda d: np.where(d["ticker"].isin(CONTROLS), "control", "exposed"))
            .sort_values(["ticker", "date"]).reset_index(drop=True))
assert not panel.duplicated(["ticker", "date"]).any(), "keys (ticker, date) must be unique"
assert panel.notna().all().all(), "missing values in the panel"
assert set(panel["ticker"]) == set(TICKERS), "a ticker dropped out of the panel"
OUT.mkdir(exist_ok=True)
panel.to_csv(OUT / "final_rows.csv", index=False)
print(f"{len(panel)} rows, {panel.ticker.nunique()} firms, "
      f"{panel.date.min().date()} to {panel.date.max().date()}")
print(panel.groupby("ticker").head(1).to_string(index=False))

# 5. Same-day compute beta: ex_ret = a + b_mkt*mkt_rf + b_gpu*d_gpu
rows = []
for t, g in panel.groupby("ticker"):
    m = sm.OLS(g["ex_ret"], sm.add_constant(g[["mkt_rf", "d_gpu"]])).fit(cov_type="HC1")
    rows.append({"ticker": t, "n": int(m.nobs), "b_mkt": m.params["mkt_rf"],
                 "b_gpu": m.params["d_gpu"], "se_gpu": m.bse["d_gpu"], "t_gpu": m.tvalues["d_gpu"],
                 "r2": m.rsquared, "start": g["date"].min().date(), "end": g["date"].max().date(),
                 "gpu_source": GPU_SOURCE})
betas = pd.DataFrame(rows)
betas.to_csv(OUT / "compute_betas.csv", index=False)
print(f"\nSame-day compute betas (GPU column is {GPU_SOURCE}"
      f"{' -> placeholders' if GPU_SOURCE == 'FAKE' else ''}):")
print(betas.round(3).to_string(index=False))
