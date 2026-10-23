"""Build the firm x day panel: one row per firm per trading day.

Reads:  data/processed/{firms,returns,gpu_trading_day}.csv, data/raw/ff3_daily.csv
Writes: data/processed/panel_firm_day.csv  (git-ignored: contains GPU changes)
Columns: ticker, date, group, ret, rf, ex_ret, mkt_rf, ex_qqq, ex_smh,
         d_gpu, d_gpu_lag1.., d_gpu_lead1.., is_stale, gpu_source
"""
import pandas as pd

from common import check, config

firms = pd.read_csv(config.PROCESSED / "firms.csv")
rets = pd.read_csv(config.PROCESSED / "returns.csv", parse_dates=["date"])
ff = pd.read_csv(config.RAW / "ff3_daily.csv", parse_dates=["date"])
gpu = pd.read_csv(config.PROCESSED / "gpu_trading_day.csv", parse_dates=["date", "gpu_obs_date"])

# Leads and lags of the GPU change, computed on the trading-day series BEFORE merging
K = config.LEAD_LAG_K
for k in range(1, K + 1):
    gpu[f"d_gpu_lag{k}"] = gpu["d_gpu"].shift(k)     # GPU moved k days BEFORE the stock return
    gpu[f"d_gpu_lead{k}"] = gpu["d_gpu"].shift(-k)   # GPU moves k days AFTER the stock return

# Benchmark returns as columns (one row per date)
bench = (rets[rets.ticker.isin(["QQQ", "SMH"])]
         .pivot(index="date", columns="ticker", values="ret")
         .rename(columns={"QQQ": "ret_qqq", "SMH": "ret_smh"}).reset_index())

panel = (rets[rets.ticker.isin(firms.ticker)]
         .merge(firms, on="ticker", how="left", validate="m:1")
         .merge(ff[["date", "mkt_rf", "rf"]], on="date", how="inner", validate="m:1")
         .merge(bench, on="date", how="left", validate="m:1")
         .merge(gpu, on="date", how="inner", validate="m:1"))
panel["ex_ret"] = panel["ret"] - panel["rf"]
panel["ex_qqq"] = panel["ret_qqq"] - panel["rf"]
panel["ex_smh"] = panel["ret_smh"] - panel["rf"]

cols = (["ticker", "date", "group", "ret", "rf", "ex_ret", "mkt_rf", "ex_qqq", "ex_smh", "d_gpu"]
        + [f"d_gpu_lag{k}" for k in range(1, K + 1)] + [f"d_gpu_lead{k}" for k in range(1, K + 1)]
        + ["is_stale", "gpu_source"])
panel = panel[cols].sort_values(["ticker", "date"]).reset_index(drop=True)
assert panel["group"].notna().all(), "a firm has no group"
config.OUTPUTS.mkdir(exist_ok=True)
panel.to_csv(config.PROCESSED / "panel_firm_day.csv", index=False)

check(panel, ["ticker", "date"], "05 panel")
print(panel.groupby("ticker")["date"].agg(["min", "max", "count"]).to_string())
sources = sorted(panel.gpu_source.unique())
print("\nGPU source in this panel:", sources)

# A few real rows for STATUS.md / the checkpoint PR. Only written when the GPU column is FAKE,
# because rows built from real Ornn prices must never be committed.
if sources == ["FAKE"]:
    sample = panel.groupby("ticker").head(3)
    sample.to_csv(config.OUTPUTS / "panel_sample_rows_FAKE_GPU.csv", index=False)
    print("wrote outputs/panel_sample_rows_FAKE_GPU.csv (returns/factors real, GPU column fake)")
