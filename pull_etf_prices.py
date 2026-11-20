"""Pull adjusted daily closes for the factor-control ETFs (QQQ = Nasdaq-100, SMH = semiconductors).

Same method as the stock prices in data/prices_adjusted/: Yahoo Finance via yfinance,
auto_adjust=True (splits and dividends), field Close, same requested window as the stocks.
Used by poc.py as controls, so a compute beta is not just a Nasdaq/AI factor (instructor audit A3).

Not part of run_all.py (it needs the network); the output is committed so the pipeline runs offline.
Run from the repo root:  python pull_etf_prices.py
Writes: data/prices_adjusted/etf_adjusted_closing_prices_trading_days.csv  (date, QQQ, SMH)
        data/prices_adjusted/etf_adjusted_close_metadata.json
"""
import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import yfinance as yf

HERE = Path(__file__).resolve().parent
OUT_DIR = HERE / "data/prices_adjusted"
STOCKS_CSV = OUT_DIR / "stock_adjusted_closing_prices_trading_days.csv"
TICKERS = ["QQQ", "SMH"]
START, END = "2023-12-12", "2026-11-05"          # same window as the stock pull (inclusive)

raw = yf.download(TICKERS, start=START, end=(pd.Timestamp(END) + pd.Timedelta(days=1)).date(),
                  auto_adjust=True, progress=False)["Close"][TICKERS]
raw.index = pd.DatetimeIndex(raw.index).tz_localize(None).normalize()
raw.index.name = "date"

# keep exactly the stock file's trading days, so the two files line up row for row
days = pd.read_csv(STOCKS_CSV, parse_dates=["date"])["date"]
etf = raw.reindex(days)
missing = etf[etf.isna().any(axis=1)]
assert missing.empty, f"ETF prices missing on stock trading days:\n{missing}"
assert (etf > 0).all().all()

etf.round(6).to_csv(OUT_DIR / "etf_adjusted_closing_prices_trading_days.csv")
meta = {
    "source": "Yahoo Finance via yfinance",
    "script": "pull_etf_prices.py",
    "downloaded_at_utc": datetime.now(timezone.utc).isoformat(),
    "tickers": TICKERS,
    "auto_adjust": True,
    "returned_field": "Close",
    "requested_start_inclusive": START,
    "requested_end_inclusive": END,
    "trading_day_rows": len(etf),
    "calendar": "the dates in stock_adjusted_closing_prices_trading_days.csv",
    "package_versions": {"yfinance": yf.__version__, "pandas": pd.__version__},
}
(OUT_DIR / "etf_adjusted_close_metadata.json").write_text(json.dumps(meta, indent=2) + "\n")
print(f"{len(etf)} trading days, {etf.index.min().date()} to {etf.index.max().date()}")
print(etf.tail(3))
