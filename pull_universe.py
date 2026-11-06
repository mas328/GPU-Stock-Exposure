"""Step 2: pull daily prices for every name in universe.csv from yfinance.

Reads:  universe.csv
Writes: data/prices/adj_close.csv      (wide: date x ticker; git-ignored, re-pullable)
        data/prices/returns_long.csv   (long: date, ticker, ret; git-ignored)
        outputs/universe_coverage.csv  (one row per ticker: first/last date, days; committed)

Run: python pull_universe.py
"""
from pathlib import Path

import pandas as pd
import yfinance as yf

ROOT = Path(__file__).resolve().parent
START = "2019-01-01"           # aim for 5+ years; GPU history will be the binding constraint
PRICES = ROOT / "data" / "prices"
PRICES.mkdir(parents=True, exist_ok=True)

uni = pd.read_csv(ROOT / "universe.csv", dtype=str, keep_default_na=False)
assert uni["ticker"].is_unique, "duplicate tickers in universe.csv"
assert {"SPY", "^GSPC"} <= set(uni["ticker"]), "need SPY and ^GSPC to control for the market"
tickers = uni["ticker"].tolist()

px = yf.download(tickers, start=START, auto_adjust=True, progress=False)["Close"]
px.index = pd.to_datetime(px.index).tz_localize(None)
px.index.name = "date"
px.columns.name = "ticker"
px = px.dropna(how="all")
missing = sorted(set(tickers) - set(px.columns[px.notna().any()]))
assert not missing, f"yfinance returned nothing for: {missing}"
px.to_csv(PRICES / "adj_close.csv")

# ^IRX is a yield, not a price: convert annualized percent to a daily rate, don't pct_change it
rf_daily = (px["^IRX"] / 100 / 252).rename("rf")
stocks = px.drop(columns=["^IRX"])
ret = stocks.pct_change(fill_method=None).stack().dropna().rename("ret").reset_index()
ret = ret.merge(rf_daily.reset_index(), on="date", how="left")
assert not ret.duplicated(["date", "ticker"]).any()
assert ret["ret"].abs().lt(3).all(), "a daily return of 300%+ usually means a bad split adjustment"
big = ret[ret["ret"].abs() >= 0.6]
if len(big):  # real for small caps / de-SPACs (SYM, SERV, APLD), but worth a look; winsorize in analysis
    print(f"Note: {len(big)} stock-days with |return| >= 60%:\n{big.to_string(index=False)}\n")
ret.to_csv(PRICES / "returns_long.csv", index=False)

cov = (px.notna().apply(lambda c: pd.Series({
           "first_date": c[c].index.min().date(), "last_date": c[c].index.max().date(),
           "trading_days": int(c.sum())})).T
       .rename_axis("ticker").reset_index()
       .merge(uni[["ticker", "name", "group", "subgroup"]], on="ticker"))
cov["years"] = ((pd.to_datetime(cov["last_date"]) - pd.to_datetime(cov["first_date"])).dt.days / 365.25).round(1)
cov = cov.sort_values(["group", "subgroup", "ticker"])
(ROOT / "outputs").mkdir(exist_ok=True)
cov.to_csv(ROOT / "outputs" / "universe_coverage.csv", index=False)

print(f"{px.shape[1]} tickers, {px.index.min().date()} to {px.index.max().date()}, {len(ret):,} stock-day returns")
print(cov.groupby("group").agg(n=("ticker", "size"), min_years=("years", "min")).to_string())
short = cov[cov["years"] < 5]
print("\nShorter than 5 years (fine; they enter when they list):")
print(short[["ticker", "group", "first_date", "years"]].to_string(index=False))
