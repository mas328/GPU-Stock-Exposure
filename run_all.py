"""Run the whole pipeline in order: python run_all.py"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
STEPS = ["00_make_fake_ornn.py", "01_firm_universe.py", "02_returns.py", "03_factors.py",
         "04_gpu_prices.py", "05_build_panel.py", "06_compute_betas.py"]

for step in STEPS:
    print(f"\n{'=' * 70}\n>>> {step}\n{'=' * 70}")
    result = subprocess.run([sys.executable, str(ROOT / "code" / step)], cwd=ROOT)
    if result.returncode != 0:
        sys.exit(f"\nSTOPPED: {step} failed (exit code {result.returncode}). Fix it and rerun.")
print("\nDone. Results in outputs/; panel in data/processed/ (git-ignored).")
