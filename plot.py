"""Scatter of daily GPU price change vs stock excess return, one panel per firm.
Run after poc.py: python plot.py  ->  outputs/correlation.png
The GPU column is FAKE until Ornn data arrives, so any correlation here is noise."""
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from pathlib import Path

OUT = Path(__file__).resolve().parent / "outputs"
df = pd.read_csv(OUT / "final_rows.csv", parse_dates=["date"])
tickers = sorted(df["ticker"].unique())

NCOL = min(5, len(tickers)); NROW = -(-len(tickers) // NCOL)
fig, axes = plt.subplots(NROW, NCOL, figsize=(4 * NCOL, 3.8 * NROW), sharex=True, squeeze=False)
for ax in axes.flat[len(tickers):]:
    ax.set_visible(False)
for ax, t in zip(axes.flat, tickers):
    g = df[df["ticker"] == t]
    slope, intercept = np.polyfit(g["d_gpu"], g["ex_ret"], 1)
    r = g["d_gpu"].corr(g["ex_ret"])
    ax.scatter(g["d_gpu"], g["ex_ret"], s=10, alpha=0.5)
    xs = np.array([g["d_gpu"].min(), g["d_gpu"].max()])
    ax.plot(xs, intercept + slope * xs, color="red")
    ax.set_title(f"{t}  (r = {r:.2f})")
    ax.set_xlabel("GPU price change (FAKE)")
for row in axes:
    row[0].set_ylabel("Stock excess return")
fig.suptitle("Daily stock return vs GPU price change - placeholder GPU data")
fig.tight_layout()
fig.savefig(OUT / "correlation.png", dpi=150)
print(df.pivot(index="date", columns="ticker", values="ex_ret").corrwith(
      df.drop_duplicates("date").set_index("date")["d_gpu"]).round(3))
