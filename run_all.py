"""Run the full analysis in order. Usage: python run_all.py"""

import subprocess
import sys
from pathlib import Path

scripts = sorted((Path(__file__).resolve().parent / "scripts").glob("0*.py"))
for script in scripts:
    print(f"\n===== {script.name} =====")
    subprocess.run([sys.executable, str(script)], check=True)
print("\nDone. Tables are in results/tables and figures in results/figures.")
