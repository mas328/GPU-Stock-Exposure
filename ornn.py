"""Load Ornn GPU price files (real or FAKE) and line them up with stock trading days.

Ornn's export format (from the files we have so far) is one CSV per GPU:

    GPU,Timestamp (UTC),H100 SXM hourly index (USD/GPU-hr)
    H100 SXM,2026-10-15T17:00:00Z,2.8402

The third column's name changes with the GPU, so we read it by position.

Real files live in data/ornn/ (git-ignored, private). If that folder has no CSVs we use
data/ornn_FAKE/, which has the exact same format with made-up prices.
"""
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
REAL_DIR = ROOT / "data" / "ornn"
FAKE_DIR = ROOT / "data" / "ornn_FAKE"
EXPECTED_COLS = ["GPU", "Timestamp (UTC)"]          # + one "<GPU> hourly index (USD/GPU-hr)" column
CLOSE_ET = "16:00"                                   # NYSE close; GPU price is taken as of this time


def load_ornn(prefer_real: bool = True) -> tuple[pd.DataFrame, str]:
    """Return (long DataFrame [gpu, ts_utc, price, index_name, file], source) for every Ornn file."""
    real = sorted(REAL_DIR.glob("*.csv")) if prefer_real else []
    files, source = (real, "REAL") if real else (sorted(FAKE_DIR.glob("*.csv")), "FAKE")
    assert files, f"No Ornn files in {REAL_DIR} or {FAKE_DIR}"
    frames = []
    for f in files:
        raw = pd.read_csv(f)
        assert list(raw.columns[:2]) == EXPECTED_COLS and len(raw.columns) == 3, \
            f"{f.name}: unexpected columns {list(raw.columns)}"
        frames.append(pd.DataFrame({
            "gpu": raw["GPU"].astype(str),
            "ts_utc": pd.to_datetime(raw["Timestamp (UTC)"], utc=True),
            "price": pd.to_numeric(raw.iloc[:, 2], errors="raise"),
            "index_name": raw.columns[2],
            "file": f.name,
        }))
    df = pd.concat(frames, ignore_index=True).sort_values(["gpu", "ts_utc"])
    assert df["price"].gt(0).all(), "Non-positive GPU price"
    df = df.drop_duplicates(["gpu", "ts_utc"], keep="last").reset_index(drop=True)
    return df, source


def gpu_on_trading_days(ornn: pd.DataFrame, gpu: str, trading_days) -> pd.DataFrame:
    """Price of one GPU series as of each trading day's 4pm ET close, and its log change.

    Timing rule: the price for trading day t is the last Ornn observation at or before
    4pm New York time on t. Weekend and holiday moves therefore roll into the next trading
    day. is_stale = no new Ornn observation since the previous trading day's close.
    """
    s = ornn.loc[ornn["gpu"] == gpu, ["ts_utc", "price"]].sort_values("ts_utc")
    assert len(s), f"No Ornn series named {gpu!r}; have {sorted(ornn['gpu'].unique())}"
    days = pd.DatetimeIndex(pd.to_datetime(trading_days)).normalize().unique().sort_values()
    cal = pd.DataFrame({"date": days})
    cal["close_utc"] = (cal["date"].astype(str) + " " + CLOSE_ET)
    cal["close_utc"] = pd.to_datetime(cal["close_utc"]).dt.tz_localize("America/New_York").dt.tz_convert("UTC")
    out = pd.merge_asof(cal, s.rename(columns={"ts_utc": "gpu_obs_ts"}),
                        left_on="close_utc", right_on="gpu_obs_ts", direction="backward")
    out = out.dropna(subset=["price"]).rename(columns={"price": "gpu_price"})
    out["d_gpu"] = np.log(out["gpu_price"]).diff()
    out["is_stale"] = out["gpu_obs_ts"].eq(out["gpu_obs_ts"].shift())
    return out.dropna(subset=["d_gpu"])[["date", "gpu_obs_ts", "gpu_price", "d_gpu", "is_stale"]]
