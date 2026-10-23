"""Estimate each firm's compute beta, with and without tech-factor controls, plus leads/lags.

Reads:  data/processed/panel_firm_day.csv
Writes: outputs/compute_betas.csv  (one row per firm x spec; aggregate coefficients only)
        outputs/specs_run_log.csv  (every firm x spec we ran, for specs_tried.md / p-hacking audit)

Specs (all with Newey-West standard errors, HAC_LAGS lags):
  S1 same-day:    ex_ret ~ mkt_rf + d_gpu
  S2 + Nasdaq:    ex_ret ~ mkt_rf + ex_qqq + d_gpu      (is "compute beta" just tech beta?)
  S3 lead-lag:    ex_ret ~ mkt_rf + d_gpu_lag2..lag1 + d_gpu + d_gpu_lead1..lead2
"""
import pandas as pd
import statsmodels.api as sm

from common import config

panel = pd.read_csv(config.PROCESSED / "panel_firm_day.csv", parse_dates=["date"])
K = config.LEAD_LAG_K
leadlag = ([f"d_gpu_lag{k}" for k in range(K, 0, -1)] + ["d_gpu"]
           + [f"d_gpu_lead{k}" for k in range(1, K + 1)])
SPECS = {
    "S1_same_day": ["mkt_rf", "d_gpu"],
    "S2_plus_qqq": ["mkt_rf", "ex_qqq", "d_gpu"],
    "S3_lead_lag": ["mkt_rf"] + leadlag,
}

rows, log = [], []
for (ticker, group), df in panel.groupby(["ticker", "group"]):
    for spec, xs in SPECS.items():
        d = df.dropna(subset=["ex_ret"] + xs)
        entry = {"ticker": ticker, "group": group, "spec": spec, "n_obs": len(d),
                 "start": d.date.min(), "end": d.date.max(),
                 "gpu_source": ",".join(df.gpu_source.unique())}
        if len(d) < config.MIN_OBS:
            log.append({**entry, "status": "skipped: too few obs"})
            continue
        fit = sm.OLS(d["ex_ret"], sm.add_constant(d[xs])).fit(
            cov_type="HAC", cov_kwds={"maxlags": config.HAC_LAGS})
        out = {**entry, "r2": fit.rsquared, "alpha": fit.params["const"]}
        for x in xs:
            out[f"b_{x}"] = fit.params[x]
            out[f"se_{x}"] = fit.bse[x]
            out[f"t_{x}"] = fit.tvalues[x]
        rows.append(out)
        log.append({**entry, "status": "ok"})

res = pd.DataFrame(rows)
config.OUTPUTS.mkdir(exist_ok=True)
res.to_csv(config.OUTPUTS / "compute_betas.csv", index=False)
pd.DataFrame(log).to_csv(config.OUTPUTS / "specs_run_log.csv", index=False)

show = res[res.spec == "S1_same_day"][["ticker", "group", "n_obs", "b_mkt_rf", "b_d_gpu", "se_d_gpu", "t_d_gpu"]]
print("[06] Same-day compute betas (S1):")
print(show.sort_values("t_d_gpu", ascending=False).round(3).to_string(index=False))
print(f"\n[06] {len(res)} firm x spec regressions saved; GPU source: {sorted(res.gpu_source.unique())}")
if "FAKE" in "".join(res.gpu_source.unique()):
    print("[06] WARNING: GPU prices are FAKE. These betas are placeholders, not results.")
