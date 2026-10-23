"""Download Ken French's daily Fama-French 3 factors (plus RF).

Reads:  Ken French data library (zip)
Writes: data/raw/ff3_daily.csv (+ .provenance.json) in DECIMALS (French publishes percent)
"""
import io
import urllib.request
import zipfile

import pandas as pd

from common import check, config, write_provenance

URL = ("https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/"
       "F-F_Research_Data_Factors_daily_CSV.zip")
out = config.RAW / "ff3_daily.csv"

if out.exists() and not config.FORCE["factors"]:
    print(f"Reusing {out.relative_to(config.ROOT)}")
    ff = pd.read_csv(out, parse_dates=["date"])
else:
    with urllib.request.urlopen(URL, timeout=60) as resp:
        zf = zipfile.ZipFile(io.BytesIO(resp.read()))
    text = zf.read(zf.namelist()[0]).decode("latin-1")
    # Keep only lines that start with an 8-digit date (drops headers and the copyright footer)
    lines = [ln for ln in text.splitlines() if ln[:8].strip().isdigit() and len(ln.split(",")) == 5]
    ff = pd.read_csv(io.StringIO("\n".join(lines)), header=None,
                     names=["date", "mkt_rf", "smb", "hml", "rf"])
    ff["date"] = pd.to_datetime(ff["date"].astype(str).str.strip(), format="%Y%m%d")
    ff[["mkt_rf", "smb", "hml", "rf"]] /= 100       # percent -> decimal
    ff.to_csv(out, index=False)
    write_provenance(out, URL, note="converted from percent to decimal")

check(ff, ["date"], "03 factors")
print("factor dates:", ff["date"].min().date(), "to", ff["date"].max().date())
print("NOTE: French's daily file lags by ~1-2 months; days after its last date drop out of the panel.")
