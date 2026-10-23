"""Small helpers shared by the numbered scripts."""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import config  # noqa: E402


def selected_tickers():
    """Firms to run: the proof-of-concept list, or all 30 if POC_TICKERS is None."""
    all_firms = [t for group in config.FIRMS.values() for t in group]
    assert len(all_firms) == len(set(all_firms)), "a ticker appears in two groups"
    if config.POC_TICKERS is None:
        return all_firms
    missing = set(config.POC_TICKERS) - set(all_firms)
    assert not missing, f"POC tickers not in FIRMS: {missing}"
    return list(config.POC_TICKERS)


def write_provenance(path, source, **details):
    """Save where a raw file came from and when we pulled it, next to the file."""
    meta = {"file": Path(path).name, "source": source,
            "pulled_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"), **details}
    Path(str(path) + ".provenance.json").write_text(json.dumps(meta, indent=2))


def check(df, keys, name):
    """ABCD: print shape, key uniqueness, missing values, and a few rows."""
    dupes = df.duplicated(keys).sum()
    print(f"[{name}] shape={df.shape}  duplicate {keys}={dupes}")
    print(f"[{name}] missing values:\n{df.isna().sum()[df.isna().sum() > 0].to_string() or '  none'}")
    print(df.head(3).to_string(), "\n")
    assert dupes == 0, f"{name}: duplicate keys {keys}"
