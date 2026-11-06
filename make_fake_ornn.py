"""Write data/ornn_FAKE/: made-up GPU rental prices laid out exactly like an Ornn download.

One CSV per GPU with three columns, for example:

    Date (UTC),Time (UTC),A100 index (USD/GPU-hr)
    2023-12-13,00:00,1.8512

One row per calendar day (weekends included; compute rents 24/7). Each chip starts on the
date Ornn's real series starts and runs to END.

How the prices are made (all FAKE, never results):
  - A trend through a few hand-picked price points per chip, interpolated in logs. The points
    are rough market rental rates: older chips slide down as newer ones arrive, and prices
    firm up again in 2026 as demand for compute outruns supply.
  - Plus mean-reverting daily noise (AR(1) in logs), so the price wiggles around the trend
    instead of drifting off. Newer chips get more noise (thinner markets).

Run: python make_fake_ornn.py
"""
import numpy as np
import pandas as pd

from ornn import FAKE_DIR

END = "2026-11-06"     # "today" when this file was made; change it and rerun to extend
TIME_UTC = "00:00"     # one daily print; Ornn's real time of day is still to be confirmed
PHI = 0.97             # AR(1) persistence of the noise around the trend

# GPU label as Ornn writes it, file slug, daily noise sd (log points),
# and trend points (date, USD per GPU-hour). The first point is the series start date.
SERIES = [
    ("A100", "a100", 0.008, [("2023-12-13", 1.85), ("2024-06-01", 1.55), ("2025-01-01", 1.25),
                             ("2025-09-01", 1.05), ("2026-03-01", 1.10), (END, 1.20)]),
    ("H100", "h100", 0.010, [("2024-06-23", 3.10), ("2024-12-01", 2.50), ("2025-06-01", 2.10),
                             ("2025-10-01", 2.05), ("2026-04-01", 2.40), (END, 2.80)]),
    ("H200", "h200", 0.012, [("2025-01-23", 3.90), ("2025-07-01", 3.30), ("2025-12-01", 3.10),
                             ("2026-06-01", 3.35), (END, 3.60)]),
    ("RTX PRO 6000", "rtx-pro-6000", 0.012, [("2025-09-16", 1.95), ("2026-02-01", 1.70), (END, 1.75)]),
    ("B200", "b200", 0.015, [("2025-09-23", 5.80), ("2026-02-01", 5.40), ("2026-06-01", 6.20),
                             (END, 7.00)]),
    ("B300", "b300", 0.018, [("2026-06-11", 8.00), (END, 7.40)]),
]

rng = np.random.default_rng(331)
FAKE_DIR.mkdir(parents=True, exist_ok=True)
for old in FAKE_DIR.glob("*.csv"):          # drop files from the previous layout
    old.unlink()

for label, slug, sd, knots in SERIES:
    days = pd.date_range(knots[0][0], END, freq="D")
    k_days = pd.to_datetime([d for d, _ in knots])
    trend = np.interp(days.asi8, k_days.asi8, np.log([p for _, p in knots]))
    noise = np.zeros(len(days))
    shocks = rng.normal(0, sd, len(days))
    for t in range(1, len(days)):
        noise[t] = PHI * noise[t - 1] + shocks[t]
    price = np.exp(trend + noise)
    assert (price > 0).all()

    df = pd.DataFrame({
        "Date (UTC)": days.strftime("%Y-%m-%d"),
        "Time (UTC)": TIME_UTC,
        f"{label} index (USD/GPU-hr)": price.round(4),
    })
    path = FAKE_DIR / f"ornn-price-history-{slug}_FAKE.csv"
    df.to_csv(path, index=False)
    print(f"{label:13s} {len(df):5d} rows  {days[0].date()} -> {END}  "
          f"${price.min():.2f}-${price.max():.2f}, last ${price[-1]:.2f}  (FAKE)")
