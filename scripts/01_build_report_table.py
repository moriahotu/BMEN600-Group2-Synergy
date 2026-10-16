"""
Step 1: Build one row per MAUDE report.

What this script does
---------------------
The FDA splits each MAUDE report across several files. Our extracted
CSVs keep that structure:

    master   -> one row per report (dates, event type, reporter, manufacturer)
    devices  -> one row per device listed on a report (product code = implant type)
    problems -> one row per patient-problem code on a report

This script joins them on MDR_REPORT_KEY (the FDA's ID for a report) so
that every report becomes exactly one row. That matters because if we
joined without collapsing, a report with three problem codes would
appear three times and be counted three times.

Implant groups come from the FDA product code on the device record:
    FTR = silicone gel-filled breast implant
    FWM = saline-filled breast implant
A report listing both codes is labelled "Both" and kept out of the
two-group comparison.

Output
------
data/processed/report_table_<YEARS>.csv

If Asma's merged file for a year (breast_implant_merged_<YEAR>.csv) is in
data/raw, the script also checks that both files agree on the report IDs,
implant groups and problem codes for that year.

Run from the repository folder:
    python scripts/01_build_report_table.py
"""

import pandas as pd

from config import (YEARS, LABEL, REPO, RAW, PROCESSED, MASTER_FILE, DEVICE_FILE,
                    PROBLEM_FILE, INFORMATION_STATUS_CODES)

PROCESSED.mkdir(parents=True, exist_ok=True)


def read(name):
    """Read every column as text so IDs and codes keep their exact form."""
    return pd.read_csv(RAW / name, dtype=str, keep_default_na=False,
                       encoding="utf-8-sig")


master = read(MASTER_FILE)
devices = read(DEVICE_FILE)
problems = read(PROBLEM_FILE)

# ---------------- 1. Reports received in the study years ----------------
# Master dates look like 12/31/2025, so the year is the last four characters.
master["REPORT_YEAR"] = master["DATE_RECEIVED"].str[-4:]
master = master[master["REPORT_YEAR"].isin(YEARS)].copy()

if master["MDR_REPORT_KEY"].duplicated().any():
    raise ValueError("A report ID appears twice in the master file.")

# ---------------- 2. Implant group from device product codes ----------------
codes_per_report = (
    devices.groupby("MDR_REPORT_KEY")["DEVICE_REPORT_PRODUCT_CODE"]
    .agg(lambda s: "+".join(sorted(set(s.str.strip()))))
)
group_names = {"FTR": "Silicone", "FWM": "Saline", "FTR+FWM": "Both"}
implant_type = codes_per_report.map(group_names).fillna("Other")

device_rows = devices.groupby("MDR_REPORT_KEY").size()

report = master.copy()
report["IMPLANT_PRODUCT_CODES"] = report["MDR_REPORT_KEY"].map(codes_per_report)
report["IMPLANT_TYPE"] = report["MDR_REPORT_KEY"].map(implant_type)
report["DEVICE_ROW_COUNT"] = report["MDR_REPORT_KEY"].map(device_rows).fillna(0).astype(int)

if report["IMPLANT_TYPE"].isna().any():
    raise ValueError("Some reports have no breast implant device record.")

# ---------------- 3. Problem codes, counted once per report ----------------
problems["PROBLEM_CODE"] = problems["PROBLEM_CODE"].str.strip()
problems = problems[problems["MDR_REPORT_KEY"].isin(report["MDR_REPORT_KEY"])]
problems = problems[problems["PROBLEM_CODE"] != ""]

# The same code can be listed more than once for a report. Keep it once.
problems = problems.drop_duplicates(["MDR_REPORT_KEY", "PROBLEM_CODE"])

# Wide table: one column per code, 1 if the report lists it, 0 if not.
indicators = pd.crosstab(problems["MDR_REPORT_KEY"], problems["PROBLEM_CODE"])
indicators = (indicators > 0).astype(int)
indicators.columns = [f"PROBLEM_{c}" for c in indicators.columns]

report = report.merge(indicators, left_on="MDR_REPORT_KEY",
                      right_index=True, how="left")
problem_cols = list(indicators.columns)
report[problem_cols] = report[problem_cols].fillna(0).astype(int)
report = report.copy()  # tidies the table in memory after adding many columns

report["N_PROBLEM_CODES"] = report[problem_cols].sum(axis=1)
clinical_cols = [c for c in problem_cols
                 if c.replace("PROBLEM_", "") not in INFORMATION_STATUS_CODES]
report["N_CLINICAL_PROBLEM_CODES"] = report[clinical_cols].sum(axis=1)

if len(report) != report["MDR_REPORT_KEY"].nunique():
    raise ValueError("The join created duplicate report rows.")

# Problem-code dictionary (code -> description) for later scripts.
dictionary = (problems[["PROBLEM_CODE", "PROBLEM_DESCRIPTION"]]
              .drop_duplicates("PROBLEM_CODE").sort_values("PROBLEM_CODE"))
dictionary.to_csv(PROCESSED / "problem_code_dictionary.csv", index=False)

out = PROCESSED / f"report_table_{LABEL}.csv"
report.to_csv(out, index=False)

# ---------------- 4. Summary ----------------
print(f"Reports received in {LABEL}: {len(report):,}")
print(pd.crosstab(report["REPORT_YEAR"], report["IMPLANT_TYPE"], margins=True).to_string())
print(f"Reports with no problem code: {(report['N_PROBLEM_CODES'] == 0).sum():,}")
print(f"Saved: {out.relative_to(REPO)}")

# ---------------- 5. Cross-check against Asma's merged files ----------------
for year in YEARS:
    merged_path = RAW / f"breast_implant_merged_{year}.csv"
    if not merged_path.exists():
        continue
    asma = pd.read_csv(merged_path, dtype=str, keep_default_na=False,
                       encoding="utf-8-sig").set_index("MDR_REPORT_KEY")
    ours = report[report["REPORT_YEAR"] == year].set_index("MDR_REPORT_KEY")

    same_ids = set(asma.index) == set(ours.index)
    same_groups = same_ids and (asma["IMPLANT_TYPE"] == ours.loc[asma.index, "IMPLANT_TYPE"]).all()

    # Asma's file can include columns for codes not seen in this year's reports.
    # Those columns must be all zero. The shared columns must match exactly.
    asma_problem_cols = [c for c in asma.columns
                         if c.startswith("PROBLEM_") and c[8:].isdigit()]
    ours_used = [c for c in problem_cols if ours[c].sum() > 0]
    shared = sorted(set(asma_problem_cols) & set(problem_cols))
    asma_only = sorted(set(asma_problem_cols) - set(problem_cols))
    same_codes = (
        same_ids
        and set(ours_used) <= set(asma_problem_cols)
        and asma[asma_only].astype(int).sum().sum() == 0
        and (asma[shared].astype(int).values == ours.loc[asma.index, shared].values).all()
    )

    print(f"\nCross-check with breast_implant_merged_{year}.csv")
    print(f"  Same report IDs:     {same_ids}")
    print(f"  Same implant groups: {same_groups}")
    print(f"  Same problem codes:  {same_codes}")
    if not (same_ids and same_groups and same_codes):
        raise ValueError("Our table and the merged file disagree. Check before continuing.")
