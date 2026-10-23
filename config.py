"""All project settings live here. Scripts import this file; no magic numbers elsewhere."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent

# ---- Folders (relative to the repo root) ----
RAW = ROOT / "data" / "raw"
ORNN_REAL_DIR = RAW / "ornn"                   # real Ornn files go here. GIT-IGNORED. Never commit.
ORNN_FAKE_FILE = RAW / "ornn_FAKE.csv"          # committed fake file with the same columns
PROCESSED = ROOT / "data" / "processed"        # git-ignored: rebuilt by run_all.py
OUTPUTS = ROOT / "outputs"                     # aggregate results only (no raw Ornn prices)

# ---- Sample ----
START_DATE = "2024-10-01"   # ~2 years of daily data; match to Ornn's coverage once we have it
END_DATE = None             # None = today

# Proof of concept: run on a few firms first (one per group). Set to None for all 30.
POC_TICKERS = ["NVDA", "MSFT", "ORCL", "PLTR", "KO"]

# ---- Firm universe (MVP: 30 firms in 4 groups). Group choices are ours; see specs_tried.md ----
FIRMS = {
    "chipmaker": ["NVDA", "AMD", "AVGO", "TSM", "MU", "MRVL", "INTC", "ARM"],
    "cloud_provider": ["MSFT", "AMZN", "GOOGL", "ORCL", "CRWV", "NBIS", "IBM"],
    "ai_software": ["META", "PLTR", "CRM", "NOW", "SNOW", "ADBE", "AI"],
    "control": ["KO", "PG", "JNJ", "WMT", "XOM", "DUK", "MCD", "PEP"],
}

# Market proxies downloaded alongside firms (used as controls, not as firms)
BENCHMARKS = ["SPY", "QQQ", "SMH"]   # market, Nasdaq-100, semiconductor ETF

# ---- GPU price series used for the MVP (one series). Change once we see Ornn's columns ----
GPU_MODEL = "H100"
GPU_REGION = "US"
GPU_TERM = "on_demand"

# ---- Regression settings ----
HAC_LAGS = 5            # Newey-West lags for standard errors (daily data, ~1 week)
LEAD_LAG_K = 2          # leads and lags of the GPU price change: t-2 ... t+2
MIN_OBS = 120           # skip a firm-spec with fewer usable days than this

# ---- Reuse rules: False = reuse saved file if it exists ----
FORCE = {"returns": False, "factors": False}
