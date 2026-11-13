"""Rebuild every table and figure from the raw inputs, from scratch.

Run from the repo root:  python run_all.py

Deletes outputs/ and reruns each step in order. Stops at the first step that fails.
Raw inputs: data/prices_adjusted/ (stock prices), data/ornn_FAKE/ (GPU prices, FAKE),
and Ken French's daily factors (downloaded by poc.py).
"""
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "outputs"

STEPS = [
    ("poc.py", "panel (final_rows.csv) + same-day compute betas (compute_betas.csv)"),
    ("graph.py", "levels.png, leadlag.png"),
    ("plot.py", "correlation.png"),
    ("make_chart.py", "stocks_vs_gpu.png/.html, correlation_daily/weekly.csv, correlation_heatmap.png"),
    ("make_correlation.py", "correlation_tests.png"),
]

if __name__ == "__main__":
    shutil.rmtree(OUT, ignore_errors=True)
    OUT.mkdir()
    for script, makes in STEPS:
        print(f"\n=== {script}: {makes}", flush=True)
        subprocess.run([sys.executable, script], cwd=HERE, check=True)
    print(f"\nDone. Outputs in {OUT.relative_to(HERE)}/:")
    for f in sorted(OUT.iterdir()):
        print("  ", f.name)
