"""Same-day co-movement and lead/lag between GPU price changes and stock returns.
Run after poc.py: python graph.py -> outputs/levels.png, outputs/leadlag.png
Uses the trading-day mapping from poc.py (GPU price assigned to the day it can affect a
stock), so every GPU point lines up with a stock close. GPU data is FAKE for now."""
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from pathlib import Path

OUT = Path(__file__).resolve().parent / "outputs"
df = pd.read_csv(OUT / "final_rows.csv", parse_dates=["date"])
tickers = sorted(df["ticker"].unique())
LAGS = range(-5, 6)

# 1. One graph: GPU price and stocks, all rebased to 100 on the first day, same dates
fig, ax = plt.subplots(figsize=(11, 5))
for t in tickers:
    g = df[df["ticker"] == t].set_index("date")
    ax.plot(g.index, 100 * (1 + g["ret"]).cumprod(), label=t, lw=1.2)
gpu = df.drop_duplicates("date").set_index("date")["gpu_price"]
ax.plot(gpu.index, 100 * gpu / gpu.iloc[0], "k--", lw=2, label="GPU price (FAKE)")
ax.set_ylabel("Rebased to 100")
ax.set_title("GPU rental price vs stocks, aligned to trading days (GPU data is FAKE)")
ax.legend(ncol=5)
fig.tight_layout()
fig.savefig(OUT / "levels.png", dpi=150)

# 2. Lead/lag: corr(stock excess return on day t, GPU change on day t+k)
#    k = 0 same day | k < 0 GPU change comes BEFORE the stock move (GPU leads)
#                   | k > 0 GPU change comes AFTER the stock move (stocks lead)
band = 1.96 / np.sqrt(df.groupby("ticker").size().iloc[0])
NCOL = min(5, len(tickers)); NROW = -(-len(tickers) // NCOL)
fig, axes = plt.subplots(NROW, NCOL, figsize=(4 * NCOL, 3.8 * NROW), sharey=True, squeeze=False)
for ax in axes.flat[len(tickers):]:
    ax.set_visible(False)
rows = []
for ax, t in zip(axes.flat, tickers):
    g = df[df["ticker"] == t].set_index("date")
    r = [g["ex_ret"].corr(g["d_gpu"].shift(-k)) for k in LAGS]
    rows.append(pd.Series(r, index=list(LAGS), name=t))
    ax.bar(list(LAGS), r, color=["C3" if k == 0 else "C0" for k in LAGS])
    ax.axhline(band, ls=":", c="gray"); ax.axhline(-band, ls=":", c="gray")
    ax.set_title(t); ax.set_xlabel("k (neg: GPU leads, pos: stock leads)")
for row in axes:
    row[0].set_ylabel("Correlation")
fig.suptitle("Lead/lag correlation, stock excess return vs GPU price change (dotted = 95% noise band)")
fig.tight_layout()
fig.savefig(OUT / "leadlag.png", dpi=150)
print(pd.DataFrame(rows).round(3).to_string())
print(f"95% noise band: +/-{band:.3f}")
