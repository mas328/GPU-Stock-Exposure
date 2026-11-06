"""Write data/ornn_FAKE/: made-up GPU prices in Ornn's exact export format.

One CSV per GPU, columns: GPU, Timestamp (UTC), "<GPU> hourly index (USD/GPU-hr)".
One observation per calendar day (weekends included) at 19:00 UTC. Newer chips start
later, as they will in the real data. These numbers are random: never use them as results.

Run: python make_fake_ornn.py
"""
import numpy as np
import pandas as pd

from ornn import FAKE_DIR

END = "2026-10-31"
SERIES = [  # (GPU label as Ornn writes it, file slug, first date, starting $/GPU-hr)
    ("A100 SXM", "a100-sxm", "2021-01-01", 2.20),
    ("H100 SXM", "h100-sxm", "2023-04-01", 4.50),
    ("H200",     "h200",     "2024-08-01", 4.00),
    ("B200",     "b200",     "2025-03-01", 9.00),
]

rng = np.random.default_rng(331)
FAKE_DIR.mkdir(parents=True, exist_ok=True)
for label, slug, start, p0 in SERIES:
    ts = pd.date_range(f"{start} 19:00", f"{END} 19:00", freq="D", tz="UTC")
    log_p = np.log(p0) + np.cumsum(rng.normal(-0.0005, 0.012, len(ts)))
    df = pd.DataFrame({
        "GPU": label,
        "Timestamp (UTC)": ts.strftime("%Y-%m-%dT%H:%M:%SZ"),
        f"{label} hourly index (USD/GPU-hr)": np.exp(log_p).round(4),
    })
    path = FAKE_DIR / f"ornn-price-history-{slug}_FAKE.csv"
    df.to_csv(path, index=False)
    print(f"wrote {path.relative_to(FAKE_DIR.parent.parent)}  {len(df)} rows  {start} -> {END}  (FAKE)")
