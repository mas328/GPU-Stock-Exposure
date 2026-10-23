"""Download daily adjusted closes from yfinance and compute daily simple returns.

Reads:  config (tickers, dates)
Writes: data/raw/yf_adj_close.csv (+ .provenance.json), data/processed/returns.csv
        returns.csv is long: ticker, date, ret
"""
import pandas as pd
import yfinance as yf

from common import check, config, selected_tickers, write_provenance

raw_file = config.RAW / "yf_adj_close.csv"
tickers = selected_tickers() + config.BENCHMARKS

if raw_file.exists() and not config.FORCE["returns"]:
    print(f"Reusing {raw_file.relative_to(config.ROOT)}")
    close = pd.read_csv(raw_file, index_col="date", parse_dates=["date"])
    missing = set(tickers) - set(close.columns)
    assert not missing, f"saved file lacks {missing}; set FORCE['returns'] = True"
else:
    close = yf.download(tickers, start=config.START_DATE, end=config.END_DATE,
                        auto_adjust=True, progress=False)["Close"]
    close.index.name = "date"
    close.to_csv(raw_file)
    write_provenance(raw_file, "yfinance yf.download(auto_adjust=True)",
                     tickers=tickers, start=config.START_DATE, end=config.END_DATE)

bad = [t for t in tickers if close[t].notna().sum() == 0]
assert not bad, f"no prices downloaded for {bad}"

rets = (close[tickers].pct_change(fill_method=None)
        .reset_index().melt(id_vars="date", var_name="ticker", value_name="ret")
        .dropna(subset=["ret"]))
rets.to_csv(config.PROCESSED / "returns.csv", index=False)
check(rets, ["ticker", "date"], "02 returns")
print(rets.groupby("ticker")["date"].agg(["min", "max", "count"]).to_string())
