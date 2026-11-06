"""
Step 4: Give every report several labels at once (multi-label classification).

Why this step exists
--------------------
Midterm feedback asked for more than one mechanical-or-biological split.
A single report can describe a ruptured implant, capsular contracture and
systemic symptoms together, and it can also carry context such as a
mammogram or a bilateral case. This script attaches a set of yes/no labels
to each report so outcomes can be counted alone and in combination.

Each label records where it came from:
    CODE  = the FDA patient-problem code on the report
    TEXT  = the narrative reason-for-reoperation statement
    NARR  = a keyword anywhere in the narrative (context labels only)
    PAT   = the patient record (age)

Labels
------
Mechanical (device):   rupture, deflation, leak
Biological (local):    capsular contracture, seroma, infection, granuloma,
                       hematoma, breast pain
Systemic:              any code for fatigue, joint pain, cognitive change,
                       hair loss, headache, rash, autoimmune disorder,
                       anxiety or depression
Cancer:                lymphoma or BIA-ALCL code
Context:               mammogram mentioned, one side or bilateral case,
                       age group

Outputs
-------
results/tables/table6_label_prevalence_<YEARS>.csv
results/tables/table7_label_combinations_<YEARS>.csv
data/processed/multilabel_reports_<YEARS>.csv   (kept out of GitHub)

Run after steps 1 to 3:
    python scripts/04_multilabel_classification.py
"""

import re

import pandas as pd

from config import LABEL, RAW, PROCESSED, TABLES, NARRATIVE_FILE

GROUPS = ["Silicone", "Saline"]

# Patient-problem codes grouped into labels (code numbers from the FDA dictionary).
CODE_LABELS = {
    "BIO_capsular_contracture": ["1761"],
    "BIO_seroma": ["2069"],
    "BIO_infection": ["1930", "2446", "1735", "1768", "1690"],
    "BIO_granuloma": ["1876"],
    "BIO_hematoma": ["1884"],
    "BIO_breast_pain": ["4504", "1994"],
    "SYS_systemic_symptoms": ["1849", "2355", "2551", "1958", "1877", "1880",
                              "2033", "1732", "2328", "2361", "2517"],
    "CAN_lymphoma_or_alcl": ["3263", "4549"],
}

# Reason-for-reoperation text (same pattern as step 3).
REASON = re.compile(
    r"REASON FOR (?:DEVICE )?(?:EXPLANT AND/?\s?OR )?REOPERATION(?: IS)?\s*:\s*([^.]*)"
)
TEXT_LABELS = {
    "MECH_rupture": r"RUPTUR",
    "MECH_deflation": r"DEFLAT",
    "MECH_leak": r"LEAK",
}
SIDE = r"THIS RECORD IS FOR THE (?:LEFT|RIGHT)|ONE OF TWO|BILATERAL|BOTH BREASTS|LEFT AND RIGHT|RIGHT AND LEFT"

report = pd.read_csv(PROCESSED / f"report_table_{LABEL}.csv", dtype=str, keep_default_na=False)
report = report[report["IMPLANT_TYPE"].isin(GROUPS)
                & report["N_PROBLEM_CODES"].astype(int).gt(0)].copy()

# ---- Labels from problem codes ----
for label, codes in CODE_LABELS.items():
    cols = [f"PROBLEM_{c}" for c in codes if f"PROBLEM_{c}" in report.columns]
    report[label] = report[cols].astype(int).max(axis=1) if cols else 0

# ---- Labels from the narrative ----
narr = pd.read_csv(RAW / NARRATIVE_FILE, dtype=str, keep_default_na=False,
                   encoding="utf-8-sig", usecols=["MDR_REPORT_KEY", "FOI_TEXT"])
narr = narr[narr["MDR_REPORT_KEY"].isin(report["MDR_REPORT_KEY"])]
text = narr.groupby("MDR_REPORT_KEY")["FOI_TEXT"].agg(" ".join).str.upper()
reason = text.apply(lambda t: " | ".join(REASON.findall(t)))
full = report["MDR_REPORT_KEY"].map(text).fillna("")
reason = report["MDR_REPORT_KEY"].map(reason).fillna("")

for label, pattern in TEXT_LABELS.items():
    report[label] = reason.str.contains(pattern, regex=True).astype(int)
# A coded rupture also counts as rupture.
report["MECH_rupture"] = report[["MECH_rupture"]].join(
    report.get("PROBLEM_2208", 0).astype(int).rename("c")).max(axis=1)
# Capsular contracture named in the reason statement also counts.
report["BIO_capsular_contracture"] = (report["BIO_capsular_contracture"].astype(int)
                                      | reason.str.contains(r"CONTRACTUR|BAKER").astype(int))

report["CTX_mammogram_mentioned"] = full.str.contains("MAMMOGR").astype(int)
report["CTX_side_or_bilateral"] = full.str.contains(SIDE, regex=True).astype(int)

# ---- Age group from the patient record ----
pat = pd.read_csv(RAW / "breast_implant_patients.csv", dtype=str, keep_default_na=False,
                  encoding="utf-8-sig").drop_duplicates("MDR_REPORT_KEY")
age_txt = report["MDR_REPORT_KEY"].map(dict(zip(pat["MDR_REPORT_KEY"], pat["PATIENT_AGE"]))).fillna("")
age = pd.to_numeric(age_txt.str.extract(r"^(\d+)\s*YR")[0], errors="coerce")
report["AGE_GROUP"] = pd.cut(age, [0, 29, 39, 49, 59, 120],
                             labels=["<30", "30-39", "40-49", "50-59", "60+"]).astype(str).replace("nan", "Missing")

# ---- Summary groups ----
mech = [c for c in report.columns if c.startswith("MECH_")]
bio = [c for c in report.columns if c.startswith("BIO_")]
report["ANY_MECHANICAL"] = report[mech].max(axis=1)
report["ANY_BIOLOGICAL"] = report[bio].max(axis=1)
report["ANY_SYSTEMIC"] = report["SYS_systemic_symptoms"]
report["N_LABELS"] = report[mech + bio + ["SYS_systemic_symptoms", "CAN_lymphoma_or_alcl"]].sum(axis=1)

label_cols = (mech + bio + ["SYS_systemic_symptoms", "CAN_lymphoma_or_alcl",
              "CTX_mammogram_mentioned", "CTX_side_or_bilateral",
              "ANY_MECHANICAL", "ANY_BIOLOGICAL"])

# ---- Table 6: how common each label is, by implant group ----
group = report["IMPLANT_TYPE"]
rows = []
for col in label_cols:
    row = {"Label": col}
    for g in GROUPS:
        m = group.eq(g)
        row[f"{g} n"] = int(report.loc[m, col].sum())
        row[f"{g} %"] = round(100 * report.loc[m, col].mean(), 1)
    rows.append(row)
for g in GROUPS:
    m = group.eq(g)
    rows.append({"Label": f"Reports with 2 or more clinical labels ({g})",
                 f"{g} n": int(report.loc[m, "N_LABELS"].ge(2).sum()),
                 f"{g} %": round(100 * report.loc[m, "N_LABELS"].ge(2).mean(), 1)})
table6 = pd.DataFrame(rows)
table6.to_csv(TABLES / f"table6_label_prevalence_{LABEL}.csv", index=False)

# ---- Table 7: most common combinations of mechanical / biological / systemic ----
combo = (report["ANY_MECHANICAL"].map({1: "Mechanical", 0: ""}) + "+"
         + report["ANY_BIOLOGICAL"].map({1: "Biological", 0: ""}) + "+"
         + report["ANY_SYSTEMIC"].map({1: "Systemic", 0: ""}))
combo = combo.str.strip("+").str.replace(r"\++", " + ", regex=True).replace("", "None of these")
table7 = (pd.crosstab(combo, group)[GROUPS]
          .assign(**{f"{g} %": lambda d, g=g: (100 * d[g] / d[g].sum()).round(1) for g in GROUPS})
          .sort_values("Silicone", ascending=False))
table7.index.name = "Label combination"
table7.to_csv(TABLES / f"table7_label_combinations_{LABEL}.csv")

keep = ["MDR_REPORT_KEY", "IMPLANT_TYPE", "REPORT_YEAR", "AGE_GROUP", "N_LABELS"] + label_cols
report[keep].to_csv(PROCESSED / f"multilabel_reports_{LABEL}.csv", index=False)

print(table6.to_string(index=False))
print("\n", table7.to_string())
print("\nAge group (share of reports):")
print((100 * pd.crosstab(report["AGE_GROUP"], group, normalize="columns")).round(1)[GROUPS].to_string())
