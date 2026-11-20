"""Same-day co-movement and lead/lag between GPU price changes and stock returns.
Run after poc.py: python graph.py -> outputs/levels.png, outputs/leadlag.png
Uses final_rows.csv, so the GPU price is on trading days by the shared rule in gpu_timing.py.
The lead/lag grid is an EXPLORATORY scan (stocks x 11 lags), not the main test: a simulated
family-wise band (multiple_testing.py) is drawn so the "best lag" is not read as significant
just because many correlations were searched. GPU data is FAKE for now."""
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from pathlib import Path

from multiple_testing import scan_summary

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
fig.text(0.01, 0.01, "DESCRIPTIVE ONLY: price levels, rebased. Two trending series can look related by chance; inference uses daily changes (compute_betas.csv), not levels.", fontsize=9, color="#a00")
fig.tight_layout(rect=(0, 0.04, 1, 1))
fig.savefig(OUT / "levels.png", dpi=150)

# 2. Lead/lag: corr(stock excess return on day t, GPU change on day t - lag)
#    Project-wide sign convention (same in make_correlation.py, multiple_testing.py, app.py):
#    lag = 0 same day | lag > 0 GPU change comes FIRST (GPU leads)
#                     | lag < 0 stock move comes first (stock leads)
band = 1.96 / np.sqrt(df.groupby("ticker").size().iloc[0])
wide = df.pivot(index="date", columns="ticker", values="ex_ret")[tickers]
gpu_chg = df.drop_duplicates("date").set_index("date")["d_gpu"].reindex(wide.index)
scan = scan_summary(wide.to_numpy(), gpu_chg.to_numpy(), list(LAGS))
fw = scan["simulated_fw_band"]
NCOL = min(5, len(tickers)); NROW = -(-len(tickers) // NCOL)
fig, axes = plt.subplots(NROW, NCOL, figsize=(4 * NCOL, 3.8 * NROW), sharey=True, squeeze=False)
for ax in axes.flat[len(tickers):]:
    ax.set_visible(False)
rows = []
for ax, t in zip(axes.flat, tickers):
    g = df[df["ticker"] == t].set_index("date")
    r = [g["ex_ret"].corr(g["d_gpu"].shift(lag)) for lag in LAGS]
    rows.append(pd.Series(r, index=list(LAGS), name=t))
    ax.bar(list(LAGS), r, color=["C3" if lag == 0 else "C0" for lag in LAGS])
    ax.axhline(band, ls=":", c="gray"); ax.axhline(-band, ls=":", c="gray")
    ax.axhline(fw, ls="--", c="C3", lw=1); ax.axhline(-fw, ls="--", c="C3", lw=1)
    ax.set_title(t); ax.set_xlabel("lag, trading days (+ = GPU leads)")
for row in axes:
    row[0].set_ylabel("Correlation")
fig.suptitle("EXPLORATORY lead/lag scan: corr(stock excess return on day t, GPU price change on day t - lag); "
             "positive lag = GPU change comes first\n"
             f"(dotted = 95% band for one test; red dashed = 95% band for all {scan['n_tests']} tests, simulated)")
fig.tight_layout()
fig.savefig(OUT / "leadlag.png", dpi=150)
print(pd.DataFrame(rows).round(3).to_string())
print(f"95% noise band (one test): +/-{band:.3f}")
print(f"Exploratory scan, {scan['n_tests']} correlations: max |r| = {scan['observed_max_abs_r']:.3f}; "
      f"family-wise 95% band +/-{fw:.3f} (simulated), +/-{scan['bonferroni_band']:.3f} (Bonferroni); "
      f"p(max this large by chance) = {scan['p_max']:.2f}")
