"""Show whether stock returns and GPU price changes move together, scale-free.
Panels: (1) scatter of weekly returns, stock vs GPU average, with fit and r;
        (2) rolling 90-day correlation of daily returns; (3) lead-lag correlation (GPU leads if lag>0).
Usage: python make_correlation.py"""
from pathlib import Path
import matplotlib.pyplot as plt, numpy as np, pandas as pd
from make_chart import load_stocks, load_gpus, build, STOCK_COLORS, HERE

stocks, gpus = load_stocks(HERE/"data/prices/stock_closing_prices_trading_days.csv"), load_gpus(HERE/"data/ornn_FAKE")
cum, tick, gn, st, gd = build(stocks, gpus)
gavg = gd.pct_change().mean(axis=1, skipna=True)          # equal-weight daily GPU return
rs = st.pct_change()
fig = plt.figure(figsize=(14, 11)); gs = fig.add_gridspec(3, 4, height_ratios=[1.1, 1, 1])
# 1 scatter weekly
for i, t in enumerate(tick):
    ax = fig.add_subplot(gs[0, i])
    w = pd.concat([(1+rs[t]).rolling(5).apply(np.prod, raw=True)-1, (1+gavg).rolling(5).apply(np.prod, raw=True)-1], axis=1).dropna().iloc[::5]*100
    x, y = w.iloc[:, 1], w.iloc[:, 0]; r = x.corr(y); b = np.polyfit(x, y, 1)
    ax.scatter(x, y, s=14, alpha=.5, color=STOCK_COLORS[t]); xx = np.array([x.min(), x.max()]); ax.plot(xx, np.polyval(b, xx), color="#cc0000", lw=2)
    ax.axhline(0, c="#999", lw=.6); ax.axvline(0, c="#999", lw=.6)
    ax.set_title(f"{t}: r = {r:+.2f} (n={len(w)})", fontsize=11, loc="left"); ax.set_xlabel("GPU avg weekly return %"); 
    if i == 0: ax.set_ylabel("Stock weekly return %")
# 2 rolling
ax = fig.add_subplot(gs[1, :])
for t in tick: ax.plot(rs[t].rolling(90).corr(gavg), color=STOCK_COLORS[t], label=t, lw=1.8)
ax.axhline(0, c="#555", lw=1); ax.set_ylim(-1, 1); ax.set_ylabel("90-day rolling correlation\n(daily returns)"); ax.legend(ncol=4, frameon=False)
ax.set_title("Is the relationship stable over time? (stays near 0 = no relationship)", loc="left"); ax.grid(axis="y", c="#e5e5e5")
# 3 lead-lag
ax = fig.add_subplot(gs[2, :]); lags = range(-20, 21); wd = .2
for k, t in enumerate(tick):
    ax.bar(np.array(list(lags)) + (k-1.5)*wd, [rs[t].corr(gavg.shift(l)) for l in lags], width=wd, color=STOCK_COLORS[t], label=t)
n = rs.dropna().shape[0]; band = 1.96/np.sqrt(n); ax.axhspan(-band, band, color="#ddd", alpha=.6, label="±95% noise band")
ax.set_xlabel("Lag in trading days (positive = GPU price change comes first)"); ax.set_ylabel("Correlation"); ax.legend(ncol=5, frameon=False)
ax.set_title("Does one lead the other?", loc="left")
for a in fig.axes:
    for s in ("top", "right"): a.spines[s].set_visible(False)
fig.suptitle("Stock returns vs GPU price changes: correlation tests (GPU data is FAKE placeholder)", fontsize=15, fontweight="bold", x=.01, ha="left")
fig.tight_layout(); fig.savefig(HERE/"correlation_tests.png", dpi=200)
for t in tick:
    print(t, "daily r=%.3f" % rs[t].corr(gavg), "best lag r=%.3f at %d" % max(((rs[t].corr(gavg.shift(l)), l) for l in lags), key=lambda z: abs(z[0])))
print(f"95 pct noise band: +-{band:.3f}")
