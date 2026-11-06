"""Compare cumulative % change of tech stocks vs GPU compute prices.

Usage:  python make_chart.py [--stocks PATH] [--gpu-dir DIR] [--start YYYY-MM-DD]
                             [--end YYYY-MM-DD] [--no-average] [--out-dir DIR]

Inputs (defaults, relative to this script):
  data/prices/stock_closing_prices_trading_days.csv   date,NVDA,MSFT,ORCL,KO  (daily, trading days, unadjusted Close)
  data/ornn_FAKE/*.csv                                 one file per GPU: date, index in USD/GPU-hr (daily, calendar days)

Method: common window = latest first date .. earliest last date over all series (override with
--start/--end). GPU prices are sampled on stock trading days (the coarser frequency; the last GPU
print on or before each trading day). Every series is rebased to 0% at the first common date.
"""
import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import plotly.graph_objects as go

HERE = Path(__file__).resolve().parent
STOCK_COLORS = {"NVDA": "#08519c", "MSFT": "#2171b5", "ORCL": "#4292c6", "KO": "#9ecae1"}  # blues
GPU_COLORS = ["#7f2704", "#a63603", "#d94801", "#f16913", "#fd8d3c", "#fdae6b"]  # oranges
AVG_COLOR = "#cc0000"


def load_stocks(path):
    df = pd.read_csv(path, parse_dates=["date"]).set_index("date").sort_index()
    return df


def load_gpus(folder):
    out = {}
    for f in sorted(Path(folder).glob("*.csv")):
        g = pd.read_csv(f, parse_dates=[0])
        name = g.columns[1].split(" index")[0]  # "H100 index (USD/GPU-hr)" -> "H100"
        s = g.set_index(g.columns[0])[g.columns[1]].sort_index()
        s = s[~s.index.duplicated(keep="last")]
        s.index = s.index.tz_localize(None) if s.index.tz else s.index
        out[name] = s
    return pd.DataFrame(out)


def build(stocks, gpus, start=None, end=None):
    first = max([stocks.index.min()] + [gpus[c].first_valid_index() for c in gpus])
    last = min([stocks.index.max()] + [gpus[c].last_valid_index() for c in gpus])
    first = pd.Timestamp(start) if start else first
    last = pd.Timestamp(end) if end else last
    # Coarser frequency = stock trading days. Sample GPU on those days (last print on/before).
    days = stocks.index[(stocks.index >= first) & (stocks.index <= last)]
    gpu_d = gpus.sort_index().ffill().reindex(days, method="ffill")
    # Reindex with method= on a ffilled frame: also guard series that begin after `first`.
    both = pd.concat([stocks.reindex(days), gpu_d], axis=1)
    both = both.dropna(axis=1, how="all")
    both = both.dropna(how="any")
    cum = (both / both.iloc[0] - 1) * 100
    return cum, list(stocks.columns), [c for c in gpus.columns if c in cum.columns]


def spread_labels(ys, min_gap):
    """Nudge label y-positions apart so end labels don't overlap."""
    order = sorted(range(len(ys)), key=lambda i: ys[i])
    pos = [ys[i] for i in order]
    for k in range(1, len(pos)):
        pos[k] = max(pos[k], pos[k - 1] + min_gap)
    shift = (sum(ys) - sum(pos)) / len(pos)
    res = [0] * len(ys)
    for k, i in enumerate(order):
        res[i] = pos[k] + shift
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stocks", default=HERE / "data/prices/stock_closing_prices_trading_days.csv")
    ap.add_argument("--gpu-dir", default=HERE / "data/ornn_FAKE")
    ap.add_argument("--start")
    ap.add_argument("--end")
    ap.add_argument("--no-average", action="store_true")
    ap.add_argument("--out-dir", default=HERE)
    a = ap.parse_args()

    stocks, gpus = load_stocks(a.stocks), load_gpus(a.gpu_dir)
    cum, tickers, gnames = build(stocks, gpus, a.start, a.end)
    series = {t: ("stock", cum[t]) for t in tickers}
    series.update({g: ("gpu", cum[g]) for g in gnames})
    if len(gnames) > 1 and not a.no_average:
        # Average of rebased % changes (each GPU weighted equally; raw $ levels differ by type).
        series["GPU average"] = ("avg", cum[gnames].mean(axis=1))

    t0, t1 = cum.index[0], cum.index[-1]
    fake = "FAKE" in str(a.gpu_dir)
    src = (f"Sources: Yahoo Finance daily Close (split-adjusted, NOT dividend-adjusted); "
           f"Ornn GPU price index{' (FAKE placeholder data)' if fake else ''}. "
           f"Period: {t0:%b %d, %Y} to {t1:%b %d, %Y}, {len(cum)} trading days; all series rebased to 0% at start.")

    # ---- Matplotlib PNG ----
    fig, ax = plt.subplots(figsize=(13, 7.5))
    ax.axhline(0, color="#555", lw=1, zorder=1)
    ends = {}
    for i, (name, (kind, s)) in enumerate(series.items()):
        if kind == "stock":
            kw = dict(color=STOCK_COLORS.get(name, "#2171b5"), ls="-", lw=2)
        elif kind == "gpu":
            kw = dict(color=GPU_COLORS[gnames.index(name) % len(GPU_COLORS)], ls="--", lw=1.8)
        else:
            kw = dict(color=AVG_COLOR, ls="--", lw=3)
        ax.plot(s.index, s.values, label=name + (" (stock)" if kind == "stock" else " (GPU price)" if kind == "gpu" else ""), **kw)
        ends[name] = (s.iloc[-1], kw["color"])
    yr = ax.get_ylim()
    ypos = spread_labels([v for v, _ in ends.values()], (yr[1] - yr[0]) * 0.032)
    for (name, (v, c)), y in zip(ends.items(), ypos):
        ax.annotate(f"{name} {v:+.1f}%", xy=(t1, v), xytext=(t1 + (t1 - t0) * 0.015, y),
                    color=c, fontsize=10, fontweight="bold", va="center", annotation_clip=False,
                    arrowprops=dict(arrowstyle="-", color=c, lw=0.6))
    ax.set_title("Tech stocks vs. GPU compute prices: cumulative % change", fontsize=16, fontweight="bold", loc="left")
    ax.set_xlabel("Date", fontsize=12)
    ax.set_ylabel("Cumulative % change since start", fontsize=12)
    ax.yaxis.set_major_formatter(lambda v, _: f"{v:.0f}%")
    ax.grid(axis="y", color="#e5e5e5", lw=0.8)
    ax.set_axisbelow(True)
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    ax.legend(loc="upper left", frameon=False, fontsize=10, ncol=2)
    fig.text(0.01, 0.01, src, fontsize=8.5, color="#555", wrap=True)
    fig.subplots_adjust(left=0.07, right=0.84, top=0.93, bottom=0.12)
    png = Path(a.out_dir) / "stocks_vs_gpu.png"
    fig.savefig(png, dpi=300)

    # ---- Plotly HTML ----
    pf = go.Figure()
    for name, (kind, s) in series.items():
        c = STOCK_COLORS.get(name, "#2171b5") if kind == "stock" else AVG_COLOR if kind == "avg" else GPU_COLORS[gnames.index(name) % len(GPU_COLORS)]
        pf.add_trace(go.Scatter(x=s.index, y=s.values, name=name, mode="lines",
                                line=dict(color=c, dash="solid" if kind == "stock" else "dash", width=3 if kind == "avg" else 2),
                                hovertemplate="%{x|%b %d, %Y}: %{y:.1f}%<extra>" + name + "</extra>"))
        pf.add_annotation(x=t1, y=s.iloc[-1], text=f"{s.iloc[-1]:+.1f}%", showarrow=False, xanchor="left",
                          xshift=6, font=dict(color=c, size=12))
    pf.add_hline(y=0, line_color="#555", line_width=1)
    pf.update_layout(title="Tech stocks vs. GPU compute prices: cumulative % change", template="plotly_white",
                     xaxis_title="Date", yaxis_title="Cumulative % change since start", yaxis_ticksuffix="%",
                     margin=dict(r=90, b=110), hovermode="x unified",
                     annotations=list(pf.layout.annotations) + [dict(text=src, xref="paper", yref="paper", x=0, y=-0.2,
                                                                      showarrow=False, align="left", font=dict(size=10, color="#555"))])
    html = Path(a.out_dir) / "stocks_vs_gpu.html"
    pf.write_html(html, include_plotlyjs="cdn")

    # ---- Summary ----
    summ = pd.DataFrame({"type": {n: k for n, (k, _) in series.items()},
                         "start": {n: s.index[0].date() for n, (_, s) in series.items()},
                         "end": {n: s.index[-1].date() for n, (_, s) in series.items()},
                         "total_%_change": {n: round(s.iloc[-1], 1) for n, (_, s) in series.items()}})
    print(summ.to_string())
    print(f"\nSaved {png}\nSaved {html}")


if __name__ == "__main__":
    main()
