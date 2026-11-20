"""Streamlit app for GPU-Stock-Exposure.
Run `python run_all.py` first (creates outputs/), then: streamlit run app.py
Results tab: reads the pipeline's own tables (compute_betas.csv, leadlag_scan_test.csv), so the
dashboard shows exactly the numbers in outputs/, including the prespecified main test.
Explore tab: re-estimates on whatever tickers and dates the viewer picks (exploratory).
GPU data is FAKE until Ornn data arrives - the app says so while that is true."""
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.api as sm
import streamlit as st
from scipy.stats import norm

from multiple_testing import scan_summary

st.set_page_config(page_title="GPU Stock Exposure", layout="wide")


@st.cache_data
def load(path="outputs/final_rows.csv"):
    return pd.read_csv(path, parse_dates=["date"])


@st.cache_data
def load_betas(path="outputs/compute_betas.csv"):
    b = pd.read_csv(path)
    b["p_gpu"] = 2 * norm.sf(b["t_gpu"].abs())            # HC1, two-sided
    b["p_gpu_hac"] = 2 * norm.sf(b["t_gpu_hac"].abs())    # Newey-West, two-sided
    return b


@st.cache_data
def fw_band(wide_ret, gpu_chg, lags, n_sim=500):
    """Simulated 95% band for the largest |r| across this whole stocks x lags grid."""
    ok = wide_ret.join(gpu_chg.rename("_g")).dropna()
    if len(ok) < 40:
        return None
    return scan_summary(ok[wide_ret.columns].to_numpy(), ok["_g"].to_numpy(), lags, n_sim=n_sim)


def betas(d, controls=()):
    """Re-estimate on a selection (Explore tab). HC1 and Newey-West (5 lags) SEs."""
    rows = []
    for t, g in d.groupby("ticker"):
        if len(g) < 10:
            continue
        X = sm.add_constant(g[["mkt_rf", "d_gpu", *controls]])
        m = sm.OLS(g["ex_ret"], X).fit(cov_type="HC1")
        h = sm.OLS(g["ex_ret"], X).fit(cov_type="HAC", cov_kwds={"maxlags": 5})
        rows.append({"ticker": t, "n": int(m.nobs), "b_mkt": m.params["mkt_rf"],
                     "b_gpu": m.params["d_gpu"], "t_gpu": m.tvalues["d_gpu"],
                     "t_gpu_hac": h.tvalues["d_gpu"], "p_gpu_hac": h.pvalues["d_gpu"],
                     "r2": m.rsquared})
    return pd.DataFrame(rows)


def beta_chart(res, se_col, title):
    fig, ax = plt.subplots(figsize=(8, 3.6))
    colors = ["#969696" if t in ("KO", "PG") else "C0" for t in res["ticker"]]
    ax.bar(res["ticker"], res["b_gpu"], yerr=1.96 * res[se_col], capsize=4, color=colors)
    ax.axhline(0, c="k", lw=0.8)
    ax.set_ylabel("Compute beta (95% CI)")
    ax.set_title(title, fontsize=10, loc="left")
    fig.tight_layout()
    return fig


try:
    df = load()
except FileNotFoundError:
    st.error("outputs/final_rows.csv not found. Run `python run_all.py` first.")
    st.stop()

try:
    allb = load_betas()
except FileNotFoundError:
    st.error("outputs/compute_betas.csv not found. Run `python run_all.py` first.")
    st.stop()

is_fake = (df["gpu_source"] == "FAKE").any()
all_tickers = sorted(df["ticker"].unique())

st.title("GPU Stock Exposure")
st.caption("Do stocks move with the price of renting GPU compute?")
if is_fake:
    st.warning("The GPU price series is FAKE (a random-walk placeholder) until Ornn data is "
               "available. Every number below is a placeholder, not a finding.")

tab_intro, tab_method, tab_results, tab_explore = st.tabs(
    ["Introduction", "Methodology", "Results", "Explore"])

# ------------------------------------------------------------------ Introduction
with tab_intro:
    st.header("Introduction")
    st.markdown(f"""
AI demand has made GPU compute a scarce, priced input. If the hourly rental price of a GPU
rises, firms that **sell** compute (e.g. NVDA, AMD, ORCL, IREN) may benefit, while firms that **buy** it
(e.g. META, ADBE) may see costs rise. This project asks whether a stock's daily
return is related to the daily change in the GPU rental price, after controlling for the market
and the Nasdaq-100 (QQQ).

**Firms studied:** {", ".join(all_tickers)} (KO and PG are controls: they should have little compute exposure).
**Period:** {df["date"].min().date()} to {df["date"].max().date()} ({df["date"].nunique()} trading days).
**Key quantity:** the *compute beta*, the sensitivity of a stock's excess return to GPU price changes.

This is a proof of concept: the pipeline is real, but the GPU price column is a placeholder
until real data is available.
""")
    c1, c2, c3 = st.columns(3)
    c1.metric("Firms", len(all_tickers))
    c2.metric("Trading days", df["date"].nunique())
    c3.metric("Panel rows", len(df))

# ------------------------------------------------------------------ Methodology
with tab_method:
    st.header("Methodology")
    st.subheader("Data")
    st.markdown("""
| Variable | Source | Status |
|---|---|---|
| Stock returns | Yahoo Finance (`yfinance`), adjusted close | Real |
| QQQ (Nasdaq-100) and SMH (semiconductors) returns, as controls | Yahoo Finance, adjusted close | Real |
| Market factor (Mkt-RF) and risk-free rate | Ken French daily factors (pinned copy) | Real |
| GPU rental price ($/GPU-hour) | Ornn (pending) | **FAKE** placeholder |
""")
    st.subheader("Timing: which day can a GPU price affect?")
    st.markdown("""
A stock can only react once a price is public, and the market closes at 4:00 pm ET. One shared
function (`gpu_timing.py`) maps every GPU price to a trading day:
- **Same-day rule (used here):** a price dated D maps to day D's close if D is a trading day,
  otherwise to the next trading day. Ornn's real exports are stamped 17:00/19:00 UTC, before the close.
- **Next-day rule (robustness):** a price dated D maps to the first trading day after D.
- If several prices land on one trading day, the **latest** is used.

`d_gpu` is the percent change of that price from the previous trading day. Ornn has not yet
confirmed its pricing time, so `outputs/compute_betas.csv` reports betas under both rules.
""")
    st.subheader("Model")
    st.latex(r"r_{i,t} - r^f_t = \alpha_i + \beta^{mkt}_i \,(R^m_t - r^f_t) + \beta^{gpu}_i \,\Delta GPU_t + \beta^{qqq}_i \,(R^{QQQ}_t - r^f_t) + \varepsilon_{i,t}")
    st.markdown("""
**Main test (prespecified):** this regression, estimated separately for each firm by OLS, with
H100 as the GPU series and the same-day timing rule. **β_gpu** is the compute beta. The QQQ term is
there so a compute beta is not just the Nasdaq/AI factor in disguise. Standard errors are
heteroskedasticity-robust (HC1), with Newey–West (HAC, 5 lags) reported alongside because GPU rental
prices can be stale for days.

**Robustness:** the same beta without QQQ (market only), with SMH instead of QQQ, and under the
next-day timing rule. Every specification is logged in `specs_tried.md`.

**Lead/lag (exploratory):** A lead/lag check correlates stock excess returns on day *t* with
GPU changes on day *t − lag*: positive *lag* means the GPU change comes first (GPU leads), negative
*lag* means the stock moves first. Lead/lag results are exploratory, not tests.
""")

# ------------------------------------------------------------------ Results
with tab_results:
    st.header("Results")
    if is_fake:
        st.info("Placeholder results: with a made-up GPU series, compute betas should be "
                "statistically indistinguishable from zero. That is a useful sanity check of the pipeline.")
    cols = {"ticker": "Ticker", "n": "Days", "b_mkt": "Market beta", "b_ctrl": "QQQ beta",
            "b_gpu": "Compute beta", "se_gpu": "SE (HC1)", "t_gpu": "t (HC1)", "p_gpu": "p (HC1)",
            "se_gpu_hac": "SE (HAC)", "t_gpu_hac": "t (HAC)", "p_gpu_hac": "p (HAC)", "r2": "R²"}

    # --- 1. Main test, straight from outputs/compute_betas.csv
    main = allb[allb["primary"]].sort_values("ticker")
    st.subheader("Main test: compute betas (H100, same-day timing, market + QQQ controls)")
    st.dataframe(main[list(cols)].rename(columns=cols).round(3), hide_index=True)
    sig = main.loc[main["p_gpu"] < 0.05, "ticker"].tolist()
    sig_hac = main.loc[main["p_gpu_hac"] < 0.05, "ticker"].tolist()
    st.markdown(f"**Significant at 5%:** HC1: {', '.join(sig) or 'none'}; "
                f"HAC: {', '.join(sig_hac) or 'none'}. "
                f"Ten tests at 5% produce about one false positive by chance alone.")
    st.pyplot(beta_chart(main, "se_gpu", "Main test, 95% CI (HC1). Gray = controls KO, PG"))

    # --- 2. Robustness: any timing rule x specification
    st.subheader("Robustness: timing rule and controls")
    c1, c2, c3 = st.columns([1, 1, 1])
    rule = c1.radio("GPU timing rule", ["same_day", "next_day"], horizontal=True,
                    help="same_day: a price dated D moves day D's close (primary). "
                         "next_day: it moves the next trading day's close.")
    spec = c2.radio("Controls", ["+qqq", "base", "+smh"], horizontal=True,
                    format_func={"+qqq": "Market + QQQ", "base": "Market only",
                                 "+smh": "Market + SMH"}.get)
    se_kind = c3.radio("Standard errors", ["HC1", "HAC"], horizontal=True)
    sel = allb[(allb["timing_rule"] == rule) & (allb["spec"] == spec)].sort_values("ticker")
    tag = " (the main test)" if rule == "same_day" and spec == "+qqq" else ""
    st.pyplot(beta_chart(sel, "se_gpu" if se_kind == "HC1" else "se_gpu_hac",
                         f"{rule}, {spec}, 95% CI ({se_kind}){tag}"))

    piv = allb.pivot_table(index="ticker", columns=["timing_rule", "spec"], values="b_gpu")
    st.markdown("**Compute beta under every timing rule and specification**")
    st.dataframe(piv.round(3))
    base = allb[allb["spec"] == "base"].pivot(index="ticker", columns="timing_rule", values="b_gpu")
    flips = int((np.sign(base["same_day"]) != np.sign(base["next_day"])).sum())
    absorb = allb[(allb["spec"] == "+qqq") & (allb["timing_rule"] == "same_day")]
    st.markdown(
        f"- **Timing matters:** the market-only compute beta changes sign between the two timing "
        f"rules for **{flips} of {len(base)}** stocks. Ornn has not yet confirmed when its prices are set.\n"
        f"- **What QQQ absorbs:** adding QQQ moves the compute beta by "
        f"{absorb['b_gpu_change_vs_base'].abs().mean():.3f} on average (same-day rule), against an "
        f"average |compute beta| of {absorb['b_gpu_base'].abs().mean():.3f} without it.")

    # --- 3. Lead/lag, exploratory, with the multiple-testing band
    st.subheader("Lead/lag correlations (exploratory; positive lag = GPU leads)")
    lags = list(range(-5, 6))
    wide = df.pivot(index="date", columns="ticker", values="ex_ret")[all_tickers]
    gchg = df.drop_duplicates("date").set_index("date")["d_gpu"]
    ll = pd.DataFrame({t: [wide[t].corr(gchg.shift(lag)) for lag in lags] for t in all_tickers},
                      index=lags).rename_axis("lag")
    st.dataframe(ll.round(3))
    fw = fw_band(wide, gchg, lags, n_sim=2000)
    one = 1.96 / np.sqrt(len(wide))
    st.caption(f"95% band for ONE correlation: ±{one:.3f}. 95% band for the largest of all "
               f"{fw['n_tests']} correlations in this table (simulated): ±{fw['simulated_fw_band']:.3f}. "
               f"Largest |r| here: {fw['observed_max_abs_r']:.3f} (chance of one this large with no "
               f"relationship: p = {fw['p_max']:.2f}). Only values past the second band survive the "
               f"multiple-testing correction.")

# ------------------------------------------------------------------ Explore
with tab_explore:
    st.header("Explore")
    c1, c2, c3 = st.columns([2, 2, 1])
    tickers = c1.multiselect("Tickers", all_tickers, default=all_tickers)
    dmin, dmax = df["date"].min().date(), df["date"].max().date()
    rng = c2.date_input("Date range", (dmin, dmax), min_value=dmin, max_value=dmax)
    max_lag = c3.slider("Max lag", 1, 10, 5)
    if len(rng) != 2 or not tickers:
        st.info("Select at least one ticker and a start and end date.")
        st.stop()
    d = df[df["ticker"].isin(tickers) & df["date"].between(pd.Timestamp(rng[0]), pd.Timestamp(rng[1]))]
    if d.empty:
        st.info("No data in that range.")
        st.stop()

    view = st.radio("View", ["Levels", "Scatter", "Lead / lag", "Betas", "Data"], horizontal=True)

    if view == "Levels":
        fig, ax = plt.subplots(figsize=(11, 4.5))
        for t in tickers:
            g = d[d["ticker"] == t].set_index("date")
            ax.plot(g.index, 100 * (1 + g["ret"]).cumprod(), label=t, lw=1.2)
        gpu = d.drop_duplicates("date").set_index("date")["gpu_price"]
        ax.plot(gpu.index, 100 * gpu / gpu.iloc[0], "k--", lw=2,
                label="GPU price" + (" (FAKE)" if is_fake else ""))
        ax.set_ylabel("Rebased to 100")
        st.caption("DESCRIPTIVE ONLY: price levels, rebased. Two trending series can look related by chance; inference uses daily changes (compute_betas.csv), not levels.")
        ax.legend(ncol=5)
        fig.tight_layout()
        st.pyplot(fig)

    elif view == "Scatter":
        cols = st.columns(len(tickers))
        for col, t in zip(cols, tickers):
            g = d[d["ticker"] == t]
            fig, ax = plt.subplots(figsize=(4, 3.6))
            ax.scatter(g["d_gpu"], g["ex_ret"], s=10, alpha=0.5)
            if len(g) > 2:
                slope, icpt = np.polyfit(g["d_gpu"], g["ex_ret"], 1)
                xs = np.array([g["d_gpu"].min(), g["d_gpu"].max()])
                ax.plot(xs, icpt + slope * xs, color="red")
            ax.set_title(f"{t} (r = {g['d_gpu'].corr(g['ex_ret']):.2f})")
            ax.set_xlabel("GPU price change")
            ax.set_ylabel("Excess return")
            fig.tight_layout()
            col.pyplot(fig)

    elif view == "Lead / lag":
        lags = list(range(-max_lag, max_lag + 1))
        wide_d = d.pivot(index="date", columns="ticker", values="ex_ret")[tickers]
        fw = fw_band(wide_d, d.drop_duplicates("date").set_index("date")["d_gpu"], lags)
        st.caption("lag > 0: GPU change comes before the stock move (GPU leads). lag < 0: stock "
                   "moves first. Dotted gray = 95% band for ONE correlation. Dashed red = 95% band "
                   "for the largest of all the correlations shown (simulated), the one to use when "
                   "scanning. Exploratory.")
        cols = st.columns(len(tickers))
        for col, t in zip(cols, tickers):
            g = d[d["ticker"] == t].set_index("date")
            r = [g["ex_ret"].corr(g["d_gpu"].shift(lag)) for lag in lags]
            band = 1.96 / np.sqrt(len(g))
            fig, ax = plt.subplots(figsize=(4, 3.6))
            ax.bar(lags, r, color=["C3" if lag == 0 else "C0" for lag in lags])
            ax.axhline(band, ls=":", c="gray")
            ax.axhline(-band, ls=":", c="gray")
            if fw is not None:
                ax.axhline(fw["simulated_fw_band"], ls="--", c="C3", lw=1)
                ax.axhline(-fw["simulated_fw_band"], ls="--", c="C3", lw=1)
            ax.set_title(t)
            ax.set_xlabel("lag (+ = GPU leads)")
            fig.tight_layout()
            col.pyplot(fig)

    elif view == "Betas":
        st.caption("Re-estimated on your selection (same-day timing). Changing dates until something "
                   "looks significant is a search, so this view is exploratory; the main test is on "
                   "the Results tab.")
        with_qqq = st.checkbox("Control for QQQ (as in the main test)", value=True)
        st.dataframe(betas(d, ["ex_qqq"] if with_qqq else []).round(3), hide_index=True)

    else:
        st.dataframe(d, hide_index=True)
        st.download_button("Download CSV", d.to_csv(index=False), "gpu_stock_panel.csv", "text/csv")
