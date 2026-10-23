"""Write data/processed/firms.csv: one row per firm with its exposure group."""
import pandas as pd

from common import check, config, selected_tickers

firms = pd.DataFrame([(t, g) for g, ts in config.FIRMS.items() for t in ts], columns=["ticker", "group"])
firms = firms[firms["ticker"].isin(selected_tickers())]
config.PROCESSED.mkdir(parents=True, exist_ok=True)
firms.to_csv(config.PROCESSED / "firms.csv", index=False)
check(firms, ["ticker"], "01 firms")
print(firms.groupby("group").size().to_string())
