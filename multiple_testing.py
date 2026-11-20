"""How big a correlation can the lag scans produce by chance alone? (instructor audit A2)

The lead/lag figures compute many correlations (stocks x lags) and the eye goes to the largest.
The usual +/-1.96/sqrt(n) band is for ONE correlation; across hundreds, some cross it by luck.

max_abs_r_null() simulates the largest |r| across the whole grid when the GPU series has NO
relationship with stocks: it circularly shifts the GPU series by a random offset (keeping its
own autocorrelation and the stocks' cross-correlation intact, but breaking any alignment with
stock returns) and records max |r| over every stock x lag. The 95th percentile is the
family-wise 5% threshold: a correlation above it is unlikely to be the luck of the scan.
Bonferroni gives a cruder analytic threshold for comparison.
"""
import numpy as np
from scipy.stats import norm


def lagged_corrs(R, g, lags):
    """corr(R[t, j], g[t - lag]) for every stock j and lag; R is n x S, g is n. Returns L x S."""
    out = np.empty((len(lags), R.shape[1]))
    for i, lag in enumerate(lags):
        if lag >= 0:
            a, b = R[lag:], g[:len(g) - lag]
        else:
            a, b = R[:lag], g[-lag:]
        a = a - a.mean(0); b = b - b.mean()
        out[i] = (a * b[:, None]).sum(0) / np.sqrt((a ** 2).sum(0) * (b ** 2).sum())
    return out


def max_abs_r_null(R, g, lags, n_sim=2000, seed=331, min_shift=30):
    """Simulated distribution of max |r| over the stock x lag grid under no relationship."""
    rng = np.random.default_rng(seed)
    n = len(g)
    shifts = rng.integers(min_shift, n - min_shift, size=n_sim)
    return np.array([np.abs(lagged_corrs(R, np.roll(g, k), lags)).max() for k in shifts])


def bonferroni_band(n_obs, n_tests, alpha=0.05):
    """|r| threshold for a two-sided test at alpha / n_tests (normal approximation)."""
    return norm.ppf(1 - alpha / (2 * n_tests)) / np.sqrt(n_obs)


def scan_summary(R, g, lags, n_sim=2000, seed=331):
    """Observed grid, pointwise band, Bonferroni band and simulated family-wise threshold."""
    obs = lagged_corrs(R, g, lags)
    null = max_abs_r_null(R, g, lags, n_sim, seed)
    n = len(g)
    return {"obs": obs, "n_obs": n, "n_tests": obs.size,
            "pointwise_band": 1.96 / np.sqrt(n),
            "bonferroni_band": bonferroni_band(n, obs.size),
            "simulated_fw_band": float(np.quantile(null, 0.95)),
            "observed_max_abs_r": float(np.abs(obs).max()),
            "p_max": float((null >= np.abs(obs).max()).mean())}
