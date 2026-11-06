# Analysis plan: which stocks are exposed to GPU prices?

This is the plan, written before the analysis code (like the HW5 "one row of the final dataset" exercise). Teammates: please review this before we build `analysis.py`.

## Status of the inputs

| Input | Status | File |
|---|---|---|
| GPU prices (Ornn) | **Blocked.** Our two real exports have 1 row each. Full history requested; see `ORNN_DATA_REQUEST.md`. | `data/ornn/` (private), `data/ornn_FAKE/` (committed, same format) |
| Stock returns, 76 names + benchmarks | Done. Daily from 2019-01-02 | `universe.csv` → `python pull_universe.py` → `data/prices/returns_long.csv` |
| Market return | SPY total return (adjusted close). ^GSPC pulled as a cross-check | same |
| Risk-free | ^IRX (13-week T-bill), converted to a daily rate. This avoids the 1–2 month lag in Ken French's file | same |

## 1. One row of the final dataset

**One row = one stock on one trading day.**

| column | meaning | source |
|---|---|---|
| `date` | NYSE trading day | yfinance calendar (SPY) |
| `ticker` | stock | `universe.csv` |
| `group` | seller / buyer / power_infra / ai_adjacent / control | `universe.csv` |
| `ret` | stock's total return, close to close | yfinance adjusted close |
| `mkt_ret` | SPY total return, same day | yfinance |
| `rf` | daily T-bill rate | ^IRX / 100 / 252 |
| `gpu_series` | which Ornn index (H100 SXM, A100, …) | Ornn |
| `gpu_obs_ts` | timestamp of the Ornn price used (last one at or before 4pm ET) | Ornn |
| `d_gpu` | log change in the GPU price since the previous trading day's close | Ornn |
| `is_stale` | no new Ornn observation since the previous trading day | derived |

Real example rows: stock and market columns are **real**, and the GPU column is **FAKE** (H100 SXM from `data/ornn_FAKE/`):

| date | ticker | group | ret | mkt_ret | rf | gpu_obs_ts | d_gpu (FAKE) | is_stale |
|---|---|---|---|---|---|---|---|---|
| 2025-06-02 | NVDA | seller | 0.0167 | 0.0056 | 0.0002 | 2025-06-02 19:00Z | −0.0212 | False |
| 2025-06-02 | CRWV | seller | 0.0799 | 0.0056 | 0.0002 | 2025-06-02 19:00Z | −0.0212 | False |
| 2025-06-02 | META | buyer | 0.0362 | 0.0056 | 0.0002 | 2025-06-02 19:00Z | −0.0212 | False |
| 2025-06-02 | VST | power_infra | 0.0430 | 0.0056 | 0.0002 | 2025-06-02 19:00Z | −0.0212 | False |
| 2025-06-02 | KO | control | −0.0014 | 0.0056 | 0.0002 | 2025-06-02 19:00Z | −0.0212 | False |

Every stock shares the same `mkt_ret` and `d_gpu` on a given day. Only `ret` varies across stocks. That's why the exposure has to be estimated from variation **over time**, stock by stock.

### Timing rule (the most likely way to get this wrong)

- Ornn timestamps are in UTC. Our two real exports are stamped 17:00Z and 19:00Z, so prices may be set during US trading hours.
- The GPU price for trading day *t* is the **last Ornn observation at or before 4pm ET on t**. Anything later belongs to *t+1*. This avoids look-ahead.
- `d_gpu` on Monday covers Friday close → Monday close, so weekend GPU moves roll into Monday. Same after holidays.
- If Ornn carries prices forward on weekends, or only updates once a day, many `d_gpu` values will be exactly 0. `ornn_audit.py` reports `share_unchanged_vs_prev`. If it's high, we should go straight to weekly returns (Section 4).

## 2. Core regression (one per stock)

For each stock *i*, using every trading day where both the stock and the GPU series exist:

```
ret_i,t − rf_t  =  a_i  +  b_mkt,i · (mkt_ret_t − rf_t)  +  b_gpu,i · d_gpu_t  +  e_i,t
```

- **`b_gpu,i` is stock i's exposure to GPU prices.** Read it as: a 1% rise in GPU rental prices goes with a `b_gpu`% move in the stock, holding the market fixed.
- Standard errors: Newey-West with 5 lags (returns and GPU changes may be autocorrelated).
- Primary GPU series: **H100 SXM**. It's the most-traded chip with the longest liquid history. A100 is a robustness check with a longer history, and H200/B200 are short-sample checks.
- Sample: each stock enters when both series exist. CRWV (Mar 2025) and NBIS (Oct 2024 relisting) will have the shortest samples. We report `n` for every regression.
- Winsorize `ret` at 1% / 99% within stock as a robustness check. There are 12 stock-days with |ret| ≥ 60% (SYM, SERV, APLD, SOUN de-SPAC/uplisting days).

Output: `outputs/gpu_betas.csv`, one row per stock × spec: `ticker, group, spec, gpu_series, b_gpu, se, t, b_mkt, r2, n, start, end, gpu_source`.

## 3. Compare exposures across groups

Expected signs from `universe.csv`:

| Group | Expected `b_gpu` | Why |
|---|---|---|
| seller (chipmakers, neoclouds, hyperscalers, server makers) | **+** | Higher rental prices = scarcer compute = more pricing power and revenue |
| buyer (AI-heavy software, META) | **−** | Compute is a cost; higher prices squeeze margins |
| power_infra (IPPs, utilities, DC REITs, electrical/cooling) | **+, weaker** | Exposed through demand: tight GPU markets signal more datacenter build-out and power demand |
| ai_adjacent (lasers/optics, networking, robotics) | optics/networking **+**, robotics **−** | Optics and networking sell into GPU clusters. Robotics firms are compute users |
| control (KO, PG, PEP, JNJ, MCD, WMT, XOM, CL) | **0** | Placebo. If these show "exposure", our measure is picking up something else |

Tests:
1. **Group means:** average `b_gpu` by group, with a cross-sectional t-test, and a bar chart with 95% CIs.
2. **Sellers vs. buyers:** test whether the mean seller `b_gpu` is greater than the mean buyer `b_gpu`. This is the headline test.
3. **Pooled regression** (more power): stack all stock-days and interact `d_gpu` with group dummies, with standard errors clustered by date (every stock shares the same `d_gpu` each day, so stock-level SEs would be far too small).
4. **Placebo check:** control-group betas should be indistinguishable from zero. If they aren't, stop and check timing.
5. **Multiple testing:** with 76 stocks, about 4 will look "significant" at 5% by chance. We lead with group results, not the single most-exposed stock.

## 4. Optional extensions

- **Weekly returns:** GPU prices may be noisy or sticky day to day. Re-run with Friday-to-Friday returns (stocks, SPY, and GPU), which also absorbs any timing mismatch inside the week. If `b_gpu` is much larger weekly than daily, GPU prices are slow to reflect news (or the daily series is stale).
- **Rolling exposures:** 252-day rolling `b_gpu` for each group's average. Does exposure rise through the AI build-out (2023→)? Does it flip for the hyperscalers as they shift from selling to buying?
- **Is it just a tech factor?** Add QQQ or SMH as a third regressor. If `b_gpu` disappears, the "GPU exposure" was tech or semiconductor beta in disguise.
- **Lead-lag:** add `d_gpu` at t−1 and t+1. A significant lag means GPU prices move first.

## Threats to validity

- **Short, single-regime sample.** H100 rental history covers mostly the AI boom, so results may not generalize.
- **Spurious trends:** we always use changes (`d_gpu`), never price levels.
- **Hyperscaler sign is ambiguous.** MSFT, AMZN, and GOOGL both sell and buy compute. We keep them in `seller` per the assignment, but flag them, and META sits in `buyer`.
- **Survivorship:** the universe is today's names. Firms that failed (or were acquired) since 2019 are missing.
- **Relisted tickers:** NBIS (formerly YNDX) and CORZ (post-bankruptcy) only have post-relisting history in yfinance.
