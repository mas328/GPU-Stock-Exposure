"""Streamlit app for GPU-Stock-Exposure.
Run poc.py first (creates final_rows.csv), then: streamlit run app.py
GPU data is FAKE until Ornn data arrives - the app says so while that is true."""
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.api as sm
import streamlit as st

st.set_page_config(page_title="GPU Stock Exposure", layout="wide")


@st.cache_data
def load(path="final_rows.csv"):
    return pd.read_csv(path, parse_dates=["date"])


def betas(d):
    rows = []
    for t, g in d.groupby("ticker"):
        if len(g) < 10:
            continue
        m = sm.OLS(g["ex_ret"], sm.add_constant(g[["mkt_rf", "d_gpu"]])).fit(cov_type="HC1")
        rows.append({"ticker": t, "n": int(m.nobs), "b_mkt": m.params["mkt_rf"],
                     "b_gpu": m.params["d_gpu"], "t_gpu": m.tvalues["d_gpu"],
                     "p_gpu": m.pvalues["d_gpu"], "r2": m.rsquared})
    return pd.DataFrame(rows)


try:
    df = load()
except FileNotFoundError:
    st.error("final_rows.csv not found. Run `python poc.py` first.")
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
rises, firms that **sell** compute (e.g. NVDA, ORCL) may benefit, while firms that **buy** it
(e.g. MSFT, heavy cloud users) may see costs rise. This project asks whether a stock's daily
return is related to the daily change in the GPU rental price, after controlling for the market.

**Firms studied:** {", ".join(all_tickers)} (KO is a control: it should have little compute exposure).
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
| Market factor (Mkt-RF) and risk-free rate | Ken French daily factors | Real |
| GPU rental price ($/GPU-hour) | Ornn (pending) | **FAKE** placeholder |
""")
    st.subheader("Timing: which day can a GPU price affect?")
    st.markdown("""
A stock can only react once a price is public, and the market closes at 4:00 pm ET:
- Price set **at or before 4:00 pm ET on a trading day** maps to that day.
- Price set **after 4:00 pm ET, or on a weekend/holiday**, maps to the **next trading day**.
- If several prices land on one trading day, the **latest** is used.

`d_gpu` is the percent change of that price from the previous trading day. Ornn's real pricing
time is unknown, so the placeholder is 17:00 ET (`GPU_PRICE_TIME_ET` in `poc.py`).
""")
    st.subheader("Model")
    st.latex(r"r_{i,t} - r^f_t = \alpha_i + \beta^{mkt}_i \,(R^m_t - r^f_t) + \beta^{gpu}_i \,\Delta GPU_t + \varepsilon_{i,t}")
    st.markdown("""
Estimated separately for each firm by OLS with heteroskedasticity-robust (HC1) standard errors.
**β_gpu** is the compute beta. A lead/lag check correlates stock excess returns on day *t* with
GPU changes on day *t+k*: negative *k* means GPU leads the stock, positive *k* means the stock leads.
""")

# ------------------------------------------------------------------ Results
with tab_results:
    st.header("Results")
    if is_fake:
        st.info("Placeholder results: with a random-walk GPU series, compute betas should be "
                "statistically indistinguishable from zero. That is a useful sanity check of the pipeline.")
    res = betas(df)
    st.subheader("Same-day compute betas")
    st.dataframe(res.round(3), hide_index=True,
                 column_config={"b_mkt": "Market beta", "b_gpu": "Compute beta",
                                "t_gpu": "t-stat", "p_gpu": "p-value", "r2": "R²"})
    sig = res[res["p_gpu"] < 0.05]["ticker"].tolist()
    st.markdown(f"**Significant at 5%:** {', '.join(sig) if sig else 'none'}")

    fig, ax = plt.subplots(figsize=(7, 3.5))
    ax.bar(res["ticker"], res["b_gpu"], yerr=1.96 * res["b_gpu"] / res["t_gpu"].replace(0, np.nan),
           capsize=4, color="C0")
    ax.axhline(0, c="k", lw=0.8)
    ax.set_ylabel("Compute beta (95% CI)")
    fig.tight_layout()
    st.pyplot(fig)

    st.subheader("Lead/lag correlations (k from -5 to +5)")
    lags = list(range(-5, 6))
    ll = {}
    for t, g in df.groupby("ticker"):
        g = g.set_index("date")
        ll[t] = [g["ex_ret"].corr(g["d_gpu"].shift(-k)) for k in lags]
    st.dataframe(pd.DataFrame(ll, index=lags).rename_axis("k").round(3))
    st.caption(f"95% noise band: ±{1.96 / np.sqrt(df.groupby('ticker').size().iloc[0]):.3f}")

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
        st.caption("k < 0: GPU change comes before the stock move. k > 0: stock moves first. "
                   "Dotted = 95% noise band.")
        lags = list(range(-max_lag, max_lag + 1))
        cols = st.columns(len(tickers))
        for col, t in zip(cols, tickers):
            g = d[d["ticker"] == t].set_index("date")
            r = [g["ex_ret"].corr(g["d_gpu"].shift(-k)) for k in lags]
            band = 1.96 / np.sqrt(len(g))
            fig, ax = plt.subplots(figsize=(4, 3.6))
            ax.bar(lags, r, color=["C3" if k == 0 else "C0" for k in lags])
            ax.axhline(band, ls=":", c="gray")
            ax.axhline(-band, ls=":", c="gray")
            ax.set_title(t)
            ax.set_xlabel("k")
            fig.tight_layout()
            col.pyplot(fig)

    elif view == "Betas":
        st.dataframe(betas(d).round(3), hide_index=True)

    else:
        st.dataframe(d, hide_index=True)
        st.download_button("Download CSV", d.to_csv(index=False), "gpu_stock_panel.csv", "text/csv")
