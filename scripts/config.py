"""Settings shared by every analysis script. Change the study years here."""

from pathlib import Path

# Years the FDA received the report (master DATE_RECEIVED).
YEARS = ["2024", "2025"]
LABEL = f"{YEARS[0]}-{YEARS[-1]}" if len(YEARS) > 1 else YEARS[0]

REPO = Path(__file__).resolve().parent.parent
RAW = REPO / "data" / "raw"
PROCESSED = REPO / "data" / "processed"
TABLES = REPO / "results" / "tables"
FIGURES = REPO / "results" / "figures"

# Extracted FDA files (one breast implant subset per table).
MASTER_FILE = "breast_implant_master.csv"
DEVICE_FILE = "breast_implant_devices_2024_2025.csv"
PROBLEM_FILE = "breast_implant_problems.csv"
NARRATIVE_FILE = "breast_implant_narratives_2024_2025.csv"

# Codes that describe how complete a report is, not a clinical problem.
INFORMATION_STATUS_CODES = {"4580", "4581", "4582"}
