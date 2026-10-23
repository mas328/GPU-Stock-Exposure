"""Create data/raw/ornn_FAKE.csv: random numbers with the columns we expect from Ornn.

The real Ornn data is private and never committed. This fake file lets anyone (including
the auditors) run the whole pipeline. Columns are our best guess until we see Ornn's files.
Prices exist every calendar day, including weekends, because compute rents 24/7.
"""
import numpy as np
import pandas as pd

from common import config

rng = np.random.default_rng(331)
dates = pd.date_range("2024-09-01", "2026-10-22", freq="D")
rows = []
for model, start in [("H100", 2.40), ("A100", 1.30)]:
    for region in ["US", "EU"]:
        for term in ["on_demand", "1mo"]:
            log_p = np.log(start) + np.cumsum(rng.normal(-0.0004, 0.012, len(dates)))
            rows.append(pd.DataFrame({
                "date": dates.date, "gpu_model": model, "region": region,
                "term": term, "price_usd_per_gpu_hour": np.exp(log_p).round(4)}))
fake = pd.concat(rows, ignore_index=True)
fake.to_csv(config.ORNN_FAKE_FILE, index=False)
print(f"wrote {config.ORNN_FAKE_FILE.relative_to(config.ROOT)}  rows={len(fake)}  (FAKE DATA)")
