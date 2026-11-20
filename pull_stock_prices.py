"""Pull adjusted daily closes for the ten study stocks into data/prices_adjusted/.

RECONSTRUCTION (2026-11-20): the script that made the committed files on 2026-11-13 was not
saved in the repo. This one rebuilds it from stock_adjusted_close_metadata.json (same source,
fields, window, calendar and fill rule) and was checked against the committed files: daily
returns on trading days match (see README "Raw inputs"). Price LEVELS can differ slightly from
the committed ones because Yahoo re-adjusts history after every new dividend or split.

Method (from the metadata):
  - Yahoo Finance via yfinance, auto_adjust=True (splits and dividends), field Close.
  - Window 2023-12-12 .. 2026-11-05 inclusive.
  - Trading days = NYSE sessions from pandas_market_calendars (full-day closures removed).
  - Calendar-day files fill every non-trading day with (previous close + next close) / 2.
    Those imputed prices use a LATER close, so they are for charts only, never for returns.

Not part of run_all.py (needs the network); the committed files are what the pipeline uses.
Run from the repo root:  python pull_stock_prices.py [--out-dir DIR]
"""
import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import pandas_market_calendars as mcal
import yfinance as yf

HERE = Path(__file__).resolve().parent
TICKERS = ["NVDA", "IREN", "ORCL", "AMD", "META", "ADBE", "VST", "VRT", "KO", "PG"]
START, END = "2023-12-12", "2026-11-05"

ap = argparse.ArgumentParser()
ap.add_argument("--out-dir", default=HERE / "data/prices_adjusted")
out = Path(ap.parse_args().out_dir)
out.mkdir(parents=True, exist_ok=True)

sessions = pd.DatetimeIndex(mcal.get_calendar("XNYS").valid_days(START, END)).tz_localize(None)
raw = yf.download(TICKERS, start=START, end=(pd.Timestamp(END) + pd.Timedelta(days=1)).date(),
                  auto_adjust=True, progress=False)["Close"][TICKERS]
raw.index = pd.DatetimeIndex(raw.index).tz_localize(None).normalize()

trading = raw.reindex(sessions)
trading.index.name = "date"
assert trading.notna().all().all(), f"missing closes:\n{trading[trading.isna().any(axis=1)]}"
assert set(raw.dropna(how="all").index) <= set(sessions), "Yahoo has a date that is not an NYSE session"
trading.to_csv(out / "stock_adjusted_closing_prices_trading_days.csv")

# calendar days: non-trading days get the midpoint of the surrounding closes
cal = pd.date_range(START, END, freq="D", name="date")
prev_day = pd.Series(sessions, index=sessions).reindex(cal, method="ffill")
next_day = pd.Series(sessions, index=sessions).reindex(cal, method="bfill")
is_imp = ~cal.isin(sessions)
daily = (trading.reindex(prev_day.values).set_axis(cal) +
         trading.reindex(next_day.values).set_axis(cal)) / 2
daily.loc[~is_imp] = trading.reindex(cal[~is_imp]).values
daily.to_csv(out / "stock_adjusted_closing_prices_daily.csv")
pd.DataFrame({"is_imputed": is_imp, "previous_trading_date": prev_day.dt.date.values,
              "next_trading_date": next_day.dt.date.values}, index=cal
             ).to_csv(out / "stock_adjusted_close_imputation.csv")
for t in TICKERS:
    pd.DataFrame({"adjusted_close": daily[t], "is_imputed": is_imp}, index=cal
                 ).to_csv(out / f"{t}_adjusted_close_daily.csv")

meta = {
    "source": "Yahoo Finance via yfinance",
    "script": "pull_stock_prices.py (reconstruction, see docstring)",
    "downloaded_at_utc": datetime.now(timezone.utc).isoformat(),
    "tickers": TICKERS, "currency": "USD", "auto_adjust": True, "returned_field": "Close",
    "price_definition": "Adjusted closing prices, accounting for stock splits and dividends.",
    "adjustment_as_of": "Yahoo adjustments available at retrieval time, not a historical vintage.",
    "requested_start_inclusive": START, "requested_end_inclusive": END,
    "trading_day_rows": len(trading), "calendar_day_rows": len(cal),
    "imputed_days_per_ticker": int(is_imp.sum()),
    "calendar": "NYSE full-day closures from pandas_market_calendars",
    "fill_rule": "Every non-trading day receives (previous adjusted Close + next adjusted Close) / 2.",
    "interpretation": "Imputed prices use a later close and are for historical comparisons.",
    "package_versions": {"yfinance": yf.__version__, "pandas": pd.__version__,
                         "pandas_market_calendars": mcal.__version__},
}
(out / "stock_adjusted_close_metadata.json").write_text(json.dumps(meta, indent=2) + "\n")
print(f"{len(trading)} trading days, {len(cal)} calendar days ({int(is_imp.sum())} imputed) -> {out}")
