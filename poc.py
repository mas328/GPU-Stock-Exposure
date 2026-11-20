"""Build the firm x day panel for the ten study stocks and estimate compute betas.

Real:  stock returns (Yahoo Finance adjusted close, committed in data/prices_adjusted/),
       QQQ and SMH returns (same source, pull_etf_prices.py), used as factor controls,
       market factor and risk-free rate (Ken French daily factors, downloaded on each run).
FAKE:  the GPU price column (data/ornn_FAKE/, same layout as Ornn's export) until the
       real Ornn history arrives. Every row is labelled gpu_source=FAKE and the betas are
       placeholders, not results.

Run from the repo root:  python poc.py
Writes: outputs/final_rows.csv     one row = one stock on one trading day (primary timing rule)
        outputs/compute_betas.csv  one row = one stock x timing rule x specification
"""
import io
from pathlib import Path
import urllib.request
import zipfile

import numpy as np
import pandas as pd
import statsmodels.api as sm

from gpu_timing import PRIMARY_RULE, RULES, gpu_source_date, map_gpu_to_trading_day

HERE = Path(__file__).resolve().parent
OUT = HERE / "outputs"
PRICES_CSV = HERE / "data/prices_adjusted/stock_adjusted_closing_prices_trading_days.csv"
GPU_CSV = HERE / "data/ornn_FAKE/ornn-price-history-h100_FAKE.csv"   # primary series: H100
GPU_SOURCE = "FAKE" if "FAKE" in GPU_CSV.name else "REAL"
ETF_CSV = HERE / "data/prices_adjusted/etf_adjusted_closing_prices_trading_days.csv"
MAIN_SPEC = "+qqq"   # prespecified main test (README "Main test"): H100, PRIMARY_RULE, +QQQ
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
# The rule lives in gpu_timing.py, shared with every other script (audit A1). We build the
# panel under BOTH rules: the primary rule goes to final_rows.csv, both go to compute_betas.csv.
raw = pd.read_csv(GPU_CSV)
raw.columns = ["gpu_date", "price_usd_per_gpu_hour"]
raw["gpu_date"] = pd.to_datetime(raw["gpu_date"])
gpu_px = raw.dropna().drop_duplicates("gpu_date", keep="last").set_index("gpu_date")[
    "price_usd_per_gpu_hour"]
trading_days = pd.DatetimeIndex(sorted(ret["date"].unique()))


def gpu_on_trading_days(rule):
    """One row per trading day that received a GPU print: price, its calendar date, d_gpu."""
    g = pd.DataFrame({"gpu_price": map_gpu_to_trading_day(gpu_px, trading_days, rule),
                      "gpu_date": gpu_source_date(gpu_px, trading_days, rule)}).dropna()
    g["d_gpu"] = g["gpu_price"].pct_change()
    g.index.name = "date"
    return g.dropna(subset=["d_gpu"]).reset_index().assign(gpu_source=GPU_SOURCE, timing_rule=rule)


# 4. Factor-control ETFs (real): QQQ (Nasdaq-100) and SMH (semiconductors), audit A3
etf = pd.read_csv(ETF_CSV, parse_dates=["date"]).set_index("date").sort_index()
etf_ret = etf.pct_change(fill_method=None).iloc[1:].reset_index()


# 5. Panel: one row = one stock on one trading day
def build_panel(rule):
    p = (ret.merge(ff[["date", "mkt_rf", "rf"]], on="date", how="inner", validate="m:1")
            .merge(etf_ret, on="date", how="inner", validate="m:1")
            .merge(gpu_on_trading_days(rule), on="date", how="inner", validate="m:1")
            .assign(ex_ret=lambda d: d["ret"] - d["rf"],
                    ex_qqq=lambda d: d["QQQ"] - d["rf"],
                    ex_smh=lambda d: d["SMH"] - d["rf"],
                    group=lambda d: np.where(d["ticker"].isin(CONTROLS), "control", "exposed"))
            .drop(columns=["QQQ", "SMH"])
            .sort_values(["ticker", "date"]).reset_index(drop=True))
    assert not p.duplicated(["ticker", "date"]).any(), "keys (ticker, date) must be unique"
    assert p.notna().all().all(), "missing values in the panel"
    assert set(p["ticker"]) == set(TICKERS), "a ticker dropped out of the panel"
    return p


panels = {rule: build_panel(rule) for rule in RULES}
panel = panels[PRIMARY_RULE]
OUT.mkdir(exist_ok=True)
panel.to_csv(OUT / "final_rows.csv", index=False)
print(f"final_rows.csv uses timing rule '{PRIMARY_RULE}': {len(panel)} rows, "
      f"{panel.ticker.nunique()} firms, {panel.date.min().date()} to {panel.date.max().date()}")
print(panel.groupby("ticker").head(1).to_string(index=False))

# 6. Compute betas: every timing rule x every specification (all listed in specs_tried.md)
#    base:  ex_ret = a + b_mkt*mkt_rf + b_gpu*d_gpu
#    +qqq:  ... + b_ctrl*ex_qqq   (Nasdaq-100: is the compute beta an AI/Nasdaq factor?)
#    +smh:  ... + b_ctrl*ex_smh   (semiconductor index)
SPECS = {"base": [], "+qqq": ["ex_qqq"], "+smh": ["ex_smh"]}
rows = []
for rule, pnl in panels.items():
    for spec, ctrl in SPECS.items():
        for t, g in pnl.groupby("ticker"):
            X = sm.add_constant(g[["mkt_rf", "d_gpu"] + ctrl])
            m = sm.OLS(g["ex_ret"], X).fit(cov_type="HC1")
            rows.append({"ticker": t, "timing_rule": rule, "spec": spec, "n": int(m.nobs),
                         "b_mkt": m.params["mkt_rf"], "b_gpu": m.params["d_gpu"],
                         "se_gpu": m.bse["d_gpu"], "t_gpu": m.tvalues["d_gpu"],
                         "b_ctrl": m.params[ctrl[0]] if ctrl else np.nan,
                         "r2": m.rsquared, "start": g["date"].min().date(),
                         "end": g["date"].max().date(), "gpu_source": GPU_SOURCE,
                         "primary": rule == PRIMARY_RULE and spec == MAIN_SPEC})
betas = pd.DataFrame(rows)
# how much of the base compute beta the ETF control absorbs (same ticker, same timing rule)
base = betas[betas["spec"] == "base"].set_index(["ticker", "timing_rule"])["b_gpu"]
betas["b_gpu_base"] = [base[(t, r)] for t, r in zip(betas["ticker"], betas["timing_rule"])]
betas["b_gpu_change_vs_base"] = betas["b_gpu"] - betas["b_gpu_base"]
betas.to_csv(OUT / "compute_betas.csv", index=False)

tag = f"GPU column is {GPU_SOURCE}{' -> placeholders' if GPU_SOURCE == 'FAKE' else ''}"
print(f"\nCompute betas, b_gpu by timing rule x spec ({tag}):")
print(betas.pivot_table(index="ticker", columns=["timing_rule", "spec"], values="b_gpu")
           .round(3).to_string())
flips = (betas[betas.spec == "base"].pivot(index="ticker", columns="timing_rule", values="b_gpu")
         .pipe(lambda d: (np.sign(d["same_day"]) != np.sign(d["next_day"])).sum()))
print(f"\nTiming robustness: b_gpu (base) changes sign between rules for {flips} of "
      f"{len(TICKERS)} stocks.")
for spec in ("+qqq", "+smh"):
    s = betas[(betas.spec == spec) & (betas.timing_rule == PRIMARY_RULE)]
    print(f"Control {spec}: mean |change in b_gpu| vs base = "
          f"{s['b_gpu_change_vs_base'].abs().mean():.4f} "
          f"(mean |b_gpu| base = {s['b_gpu_base'].abs().mean():.4f})")
