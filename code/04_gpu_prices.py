"""Turn Ornn's GPU rental prices into one daily change per STOCK TRADING DAY.

Reads:  data/raw/ornn/*.csv if present (real, private), else data/raw/ornn_FAKE.csv
        data/processed/returns.csv (for the trading calendar, from SPY)
Writes: data/processed/gpu_trading_day.csv  (git-ignored: it is derived from Ornn's data)

Timing rule (our choice; confirm with Ornn when each day's price is set):
  - The GPU price "as of" trading day t is the last observation dated on or before t.
  - d_gpu_t = log(price_t) - log(price_{previous trading day}).
  - So weekend and holiday price moves roll into the next trading day (Mon gets Sat+Sun+Mon).
  - If no new GPU observation arrived since the prior trading day, is_stale = True.
"""
import numpy as np
import pandas as pd

from common import check, config

real_files = sorted(config.ORNN_REAL_DIR.glob("*.csv"))
if real_files:
    source = "REAL (Ornn, private)"
    gpu = pd.concat([pd.read_csv(f) for f in real_files], ignore_index=True)
else:
    source = "FAKE (data/raw/ornn_FAKE.csv)"
    gpu = pd.read_csv(config.ORNN_FAKE_FILE)
print(f"[04] GPU price source: {source}")

expected = {"date", "gpu_model", "region", "term", "price_usd_per_gpu_hour"}
assert expected <= set(gpu.columns), f"GPU file missing columns: {expected - set(gpu.columns)}"
gpu["date"] = pd.to_datetime(gpu["date"])

print("[04] series available (model x region x term):")
print(gpu.groupby(["gpu_model", "region", "term"]).size().to_string(), "\n")

one = gpu[(gpu.gpu_model == config.GPU_MODEL) & (gpu.region == config.GPU_REGION)
          & (gpu.term == config.GPU_TERM)]
assert len(one), "chosen GPU series is empty; check GPU_MODEL/REGION/TERM in config.py"
# One price per calendar date (average if the source has several quotes in a day)
daily = one.groupby("date", as_index=False)["price_usd_per_gpu_hour"].mean().sort_values("date")
weekend_share = (daily["date"].dt.dayofweek >= 5).mean()
print(f"[04] {len(daily)} calendar days of prices, {weekend_share:.0%} on weekends")

# Trading calendar = days SPY has a return
rets = pd.read_csv(config.PROCESSED / "returns.csv", parse_dates=["date"])
cal = pd.DataFrame({"date": np.sort(rets.loc[rets.ticker == "SPY", "date"].unique())})

daily = daily.rename(columns={"date": "gpu_obs_date", "price_usd_per_gpu_hour": "gpu_price"})
aligned = pd.merge_asof(cal, daily, left_on="date", right_on="gpu_obs_date", direction="backward")
aligned = aligned.dropna(subset=["gpu_price"])
aligned["d_gpu"] = np.log(aligned["gpu_price"]).diff()
aligned["is_stale"] = aligned["gpu_obs_date"].eq(aligned["gpu_obs_date"].shift())
aligned = aligned.dropna(subset=["d_gpu"])
aligned["gpu_source"] = "FAKE" if not real_files else "REAL"

out = aligned[["date", "gpu_obs_date", "gpu_price", "d_gpu", "is_stale", "gpu_source"]]
out.to_csv(config.PROCESSED / "gpu_trading_day.csv", index=False)
check(out, ["date"], "04 gpu")
print(f"[04] stale trading days: {out.is_stale.sum()}  |  sd of d_gpu: {out.d_gpu.std():.4f}")
