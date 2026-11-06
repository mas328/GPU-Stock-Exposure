"""Step 1 check: what is in the Ornn data, before any analysis.

For every series it reports:
  - which GPU / index (rental vs. spot and region are read from the index name if Ornn adds them)
  - first and last timestamp, number of observations
  - frequency (median gap between observations)
  - whether weekends and US market holidays are present, and how often the price is
    unchanged from the previous observation (a sign of carry-forward / stale fills)

Run: python ornn_audit.py
Uses data/ornn/ (real, private) if it has CSVs, else data/ornn_FAKE/.
The REAL audit is written to data/processed/ (git-ignored); only the FAKE one goes in outputs/.
"""
import pandas as pd

from ornn import ROOT, load_ornn

try:  # NYSE holidays, if pandas_market_calendars is installed; else federal holidays as a proxy
    import pandas_market_calendars as mcal
    _nyse = mcal.get_calendar("NYSE")
    def market_holidays(a, b):
        sched = _nyse.valid_days(a, b).tz_localize(None)
        return pd.bdate_range(a, b).difference(sched)
except ImportError:
    from pandas.tseries.holiday import USFederalHolidayCalendar
    def market_holidays(a, b):
        return USFederalHolidayCalendar().holidays(a, b)

ornn, source = load_ornn()
rows = []
for gpu, g in ornn.groupby("gpu"):
    ts = g["ts_utc"].sort_values()
    d = ts.dt.tz_convert(None).dt.normalize()
    gaps_h = ts.diff().dt.total_seconds().div(3600).dropna()
    first, last = d.min(), d.max()
    hol = market_holidays(first, last)
    cal_days = pd.date_range(first, last, freq="D")
    rows.append({
        "gpu": gpu,
        "index_name": g["index_name"].iloc[0],
        "files": ", ".join(sorted(g["file"].unique())),
        "first_obs_utc": ts.min(), "last_obs_utc": ts.max(),
        "n_obs": len(g),
        "years": round((last - first).days / 365.25, 2),
        "median_gap_hours": gaps_h.median() if len(gaps_h) else None,
        "max_gap_days": round(gaps_h.max() / 24, 1) if len(gaps_h) else None,
        "calendar_days_covered": round(d.nunique() / len(cal_days), 3),
        "has_weekends": bool((d.dt.dayofweek >= 5).any()),
        "weekend_share_of_obs": round((d.dt.dayofweek >= 5).mean(), 3),
        "market_holidays_in_range": len(hol),
        "market_holidays_with_obs": int(d.isin(hol).groupby(d).any().sum()) if len(hol) else 0,
        "share_unchanged_vs_prev": round(g["price"].diff().eq(0).iloc[1:].mean(), 3) if len(g) > 1 else None,
        "min_price": g["price"].min(), "max_price": g["price"].max(),
    })

audit = pd.DataFrame(rows).sort_values("first_obs_utc")
pd.set_option("display.width", 200, "display.max_columns", 30)
print(f"Ornn source: {source}\n")
print(audit.drop(columns=["files", "index_name"]).to_string(index=False))

too_short = audit[audit["n_obs"] < 250]
if len(too_short):
    print(f"\n!! {len(too_short)} series have fewer than 250 observations: "
          f"{', '.join(too_short['gpu'])}. Check that this is the full history (newer chips are expected to be short).")

out = (ROOT / "data" / "processed" / "ornn_audit_REAL.csv") if source == "REAL" else (ROOT / "outputs" / "ornn_audit_FAKE.csv")
out.parent.mkdir(parents=True, exist_ok=True)
audit.to_csv(out, index=False)
print(f"\nwrote {out.relative_to(ROOT)}")
