"""Scatter of daily GPU price change vs stock excess return, one panel per firm.
Run after poc.py: python plot.py  ->  correlation.png
The GPU column is FAKE until Ornn data arrives, so any correlation here is noise."""
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

df = pd.read_csv("final_rows.csv", parse_dates=["date"])
tickers = sorted(df["ticker"].unique())

fig, axes = plt.subplots(1, len(tickers), figsize=(4 * len(tickers), 4), sharex=True)
for ax, t in zip(axes, tickers):
    g = df[df["ticker"] == t]
    slope, intercept = np.polyfit(g["d_gpu"], g["ex_ret"], 1)
    r = g["d_gpu"].corr(g["ex_ret"])
    ax.scatter(g["d_gpu"], g["ex_ret"], s=10, alpha=0.5)
    xs = np.array([g["d_gpu"].min(), g["d_gpu"].max()])
    ax.plot(xs, intercept + slope * xs, color="red")
    ax.set_title(f"{t}  (r = {r:.2f})")
    ax.set_xlabel("GPU price change (FAKE)")
axes[0].set_ylabel("Stock excess return")
fig.suptitle("Daily stock return vs GPU price change - placeholder GPU data")
fig.tight_layout()
fig.savefig("correlation.png", dpi=150)
print(df.pivot(index="date", columns="ticker", values="ex_ret").corrwith(
      df.drop_duplicates("date").set_index("date")["d_gpu"]).round(3))
