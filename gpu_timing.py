"""One place that decides which stock trading day a GPU price belongs to.

Every script that pairs a GPU price with a stock return imports this module, so the timing
rule cannot drift between files (instructor audit A1).

The question: a GPU price dated D (calendar day) can move a stock's close on which day?

  rule="same_day"  The price is set BEFORE the 4:00 pm ET close, so a price dated D belongs to
                   day D's close if D is a trading day, otherwise to the next trading day.
  rule="next_day"  The price is set AFTER the close, so a price dated D always belongs to the
                   first trading day strictly after D.

If several prices land on one trading day (e.g. Sat, Sun, Mon under same_day), the latest one
wins, because it is the most recent information the market could have had at that close.

What we know about Ornn's timing (UNCONFIRMED; we have asked Ornn, see README "Timing"):
the two real Ornn exports we hold are stamped 17:00 UTC and 19:00 UTC (= 1:00 pm and
3:00 pm ET in October), i.e. before the U.S. close. That points to same_day, so it is the
PRIMARY rule; next_day is reported alongside it as a robustness check until Ornn confirms.
"""
import pandas as pd

RULES = ("same_day", "next_day")
PRIMARY_RULE = "same_day"


def map_gpu_to_trading_day(prices, trading_days, rule=PRIMARY_RULE):
    """Map a calendar-day GPU price series onto stock trading days.

    prices        Series (one GPU) or DataFrame (one column per GPU) indexed by calendar date.
    trading_days  the stock trading days (DatetimeIndex or anything sortable into one).
    rule          "same_day" or "next_day" (see module docstring).

    Returns the same shape indexed by trading_days: the latest GPU price that belongs to each
    trading day. A trading day with no new print is left NaN here; callers that want a
    carried-forward (stale) price call .ffill() on the result.
    """
    if rule not in RULES:
        raise ValueError(f"rule must be one of {RULES}, got {rule!r}")
    if isinstance(prices, pd.DataFrame):
        return pd.DataFrame({c: map_gpu_to_trading_day(prices[c], trading_days, rule)
                             for c in prices.columns})

    days = pd.DatetimeIndex(sorted(pd.DatetimeIndex(trading_days).unique()))
    s = prices.dropna().sort_index()
    idx = pd.DatetimeIndex(s.index)
    idx = idx.tz_localize(None) if idx.tz is not None else idx
    s.index = idx.normalize()
    s = s[~s.index.duplicated(keep="last")]

    side = "left" if rule == "same_day" else "right"   # left: D itself if trading day
    pos = days.searchsorted(s.index, side=side)
    keep = pos < len(days)                               # prices after the last trading day drop
    mapped = pd.Series(s.values[keep], index=days[pos[keep]])
    mapped = mapped.groupby(level=0).last()              # input is date-sorted -> latest wins
    return mapped.reindex(days).rename(prices.name)


def gpu_source_date(prices, trading_days, rule=PRIMARY_RULE):
    """For each trading day, the calendar date of the GPU print assigned to it (for audit)."""
    s = pd.Series(pd.DatetimeIndex(prices.dropna().index), index=prices.dropna().index)
    return map_gpu_to_trading_day(s, trading_days, rule)


if __name__ == "__main__":   # tiny self-check of both rules
    days = pd.to_datetime(["2026-01-02", "2026-01-05", "2026-01-06"])        # Fri, Mon, Tue
    p = pd.Series([1.0, 2.0, 3.0, 4.0, 5.0],
                  index=pd.to_datetime(["2026-01-02", "2026-01-03", "2026-01-04",
                                        "2026-01-05", "2026-01-06"]))      # Fri..Tue
    same = map_gpu_to_trading_day(p, days, "same_day")
    nxt = map_gpu_to_trading_day(p, days, "next_day")
    assert same.tolist() == [1.0, 4.0, 5.0], same      # Mon gets Mon's own print
    assert nxt.isna().iloc[0] and nxt.iloc[1:].tolist() == [3.0, 4.0], nxt  # Mon gets Sun's
    print("gpu_timing self-check OK")
