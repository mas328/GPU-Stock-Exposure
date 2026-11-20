"""Show whether stock returns and GPU price changes move together, scale-free.
Panels: (1) scatter of weekly returns, stock vs GPU average, with fit and r;
        (2) rolling 90-day correlation of daily returns; (3) lead-lag correlation, corr(stock_t, GPU_{t-lag}); positive lag = GPU leads (the
        project-wide convention, same as graph.py and app.py).
GPU prices are put on trading days by the shared rule in gpu_timing.py (via make_chart.build).
Panel 3 is an EXPLORATORY scan (10 stocks x 41 lags), not the main test (see README "Main test").
Its "best lag" is corrected for the number of correlations searched (multiple_testing.py):
a simulated family-wise 95% band and a Bonferroni band are drawn and written to
outputs/leadlag_scan_test.csv.
Usage: python make_correlation.py"""
from pathlib import Path
import matplotlib.pyplot as plt, numpy as np, pandas as pd
from make_chart import load_stocks, load_gpus, build, STOCK_COLORS, HERE
from gpu_timing import PRIMARY_RULE
from multiple_testing import scan_summary

stocks, gpus = load_stocks(HERE/"data/prices_adjusted/stock_adjusted_closing_prices_trading_days.csv"), load_gpus(HERE/"data/ornn_FAKE")
cum, tick, gn, st, gd = build(stocks, gpus, rule=PRIMARY_RULE)
gavg = gd.pct_change().mean(axis=1, skipna=True)          # equal-weight daily GPU return
rs = st.pct_change()
NCOL = 5; NSC = -(-len(tick) // NCOL)                     # scatter grid: 5 per row
fig = plt.figure(figsize=(16, 4 * NSC + 8)); gs = fig.add_gridspec(NSC + 2, NCOL, height_ratios=[1.1] * NSC + [1.2, 1.2])
# 1 scatter weekly
for i, t in enumerate(tick):
    ax = fig.add_subplot(gs[i // NCOL, i % NCOL])
    w = pd.concat([(1+rs[t]).rolling(5).apply(np.prod, raw=True)-1, (1+gavg).rolling(5).apply(np.prod, raw=True)-1], axis=1).dropna().iloc[::5]*100
    x, y = w.iloc[:, 1], w.iloc[:, 0]; r = x.corr(y); b = np.polyfit(x, y, 1)
    ax.scatter(x, y, s=14, alpha=.5, color=STOCK_COLORS[t]); xx = np.array([x.min(), x.max()]); ax.plot(xx, np.polyval(b, xx), color="#cc0000", lw=2)
    ax.axhline(0, c="#999", lw=.6); ax.axvline(0, c="#999", lw=.6)
    ax.set_title(f"{t}: r = {r:+.2f} (n={len(w)})", fontsize=11, loc="left"); ax.set_xlabel("GPU avg weekly return %"); 
    if i % NCOL == 0: ax.set_ylabel("Stock weekly return %")
# 2 rolling
ax = fig.add_subplot(gs[NSC, :])
for t in tick: ax.plot(rs[t].rolling(90).corr(gavg), color=STOCK_COLORS[t], label=t, lw=1.8)
ax.axhline(0, c="#555", lw=1); ax.set_ylim(-1, 1); ax.set_ylabel("90-day rolling correlation\n(daily returns)"); ax.legend(ncol=NCOL, frameon=False)
ax.set_title("Is the relationship stable over time? (stays near 0 = no relationship)", loc="left"); ax.grid(axis="y", c="#e5e5e5")
# 3 lead-lag
ax = fig.add_subplot(gs[NSC + 1, :]); lags = range(-20, 21); wd = .8 / len(tick)
ok = rs[tick].join(gavg.rename("_g")).dropna()                       # rows with every series
scan = scan_summary(ok[tick].to_numpy(), ok["_g"].to_numpy(), list(lags))
for k, t in enumerate(tick):
    ax.bar(np.array(list(lags)) + (k - (len(tick) - 1) / 2) * wd, [rs[t].corr(gavg.shift(l)) for l in lags], width=wd, color=STOCK_COLORS[t], label=t)
n = rs.dropna().shape[0]; band = 1.96/np.sqrt(n); ax.axhspan(-band, band, color="#ddd", alpha=.6, label="±95% band, one test")
fw = scan["simulated_fw_band"]
for y in (fw, -fw): ax.axhline(y, color="#cc0000", ls="--", lw=1.2, label=f"±95% band, all {scan['n_tests']} tests (simulated)" if y > 0 else None)
lim = 1.15 * max(fw, scan["observed_max_abs_r"]); ax.set_ylim(-lim, lim)   # keep both bands in view
ax.set_xlabel("Lag in trading days (positive = GPU price change comes first)"); ax.set_ylabel("Correlation"); ax.legend(ncol=6, frameon=False)
ax.set_title("Does one lead the other? EXPLORATORY scan: only bars past the red dashed band survive the multiple-testing correction", loc="left")
for a in fig.axes:
    for s in ("top", "right"): a.spines[s].set_visible(False)
fig.suptitle("Stock returns vs GPU price changes: correlation tests (GPU data is FAKE placeholder)", fontsize=15, fontweight="bold", x=.01, ha="left")
(HERE/"outputs").mkdir(exist_ok=True)
fig.tight_layout(); fig.savefig(HERE/"outputs"/"correlation_tests.png", dpi=200)
for t in tick:
    print(t, "daily r=%.3f" % rs[t].corr(gavg), "best lag r=%.3f at %d" % max(((rs[t].corr(gavg.shift(l)), l) for l in lags), key=lambda z: abs(z[0])))
print(f"95 pct noise band (one test): +-{band:.3f}")
print(f"Exploratory scan, {scan['n_tests']} correlations: max |r| = {scan['observed_max_abs_r']:.3f}; "
      f"family-wise 95% band simulated +-{fw:.3f}, Bonferroni +-{scan['bonferroni_band']:.3f}; "
      f"p(max |r| this large by chance) = {scan['p_max']:.2f}")
pd.DataFrame([{"scan": "make_correlation lead-lag", "timing_rule": PRIMARY_RULE, "gpu_series": "GPU average",
               "stocks": len(tick), "lags": f"{min(lags)}..{max(lags)}", "n_tests": scan["n_tests"],
               "n_obs": scan["n_obs"], "pointwise_band": scan["pointwise_band"],
               "bonferroni_band": scan["bonferroni_band"], "simulated_fw_band": fw,
               "observed_max_abs_r": scan["observed_max_abs_r"], "p_max": scan["p_max"]}]
             ).round(4).to_csv(HERE/"outputs"/"leadlag_scan_test.csv", index=False)
