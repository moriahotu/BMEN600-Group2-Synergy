"""
Step 3: Read the reason for reoperation from report narratives.

Why this step exists
--------------------
Patient-problem codes capture biological problems well (for example
capsular contracture) but say little about what physically happened to
the implant. "Rupture" is coded in about 2% of silicone reports, and
there is no deflation code in the saline reports at all. Saline
failures appear under the general code "Failure of Implant".

Many manufacturer reports include a standard sentence in the narrative:

    "REASON FOR REOPERATION: RUPTURE."
    "REASON FOR DEVICE EXPLANT AND/OR REOPERATION: DEFLATION."

This script finds that sentence and sorts the reason into categories.

Why not just search the whole narrative for "rupture"?
Because many narratives repeat warning text from the instructions for
use ("rupture can occur at any time...") or cite papers about rupture.
A whole-text keyword search would count those as ruptures. Reading only
the reason sentence avoids most of that, but every rule still has to be
checked by people. This script therefore also writes a random sample of
reports for two team members to label by hand.

Outputs
-------
results/tables/table3_coded_vs_text_reason_<YEARS>.csv
results/tables/table4_reason_statement_by_manufacturer_<YEARS>.csv
data/processed/validation_sample_<YEARS>.csv   (narrative text, kept out of GitHub)

Run after step 1:
    python scripts/03_reoperation_reason_text.py
"""

import re

import pandas as pd

from config import LABEL, RAW, PROCESSED, TABLES, NARRATIVE_FILE

GROUPS = ["Silicone", "Saline"]
SAMPLE_PER_GROUP = 100
SEED = 600  # fixed so the same validation sample is drawn every time
TABLES.mkdir(parents=True, exist_ok=True)

# The standard sentence. The pattern allows the spelling variants seen in
# the data, then captures everything up to the next full stop.
REASON = re.compile(
    r"REASON FOR (?:DEVICE )?(?:EXPLANT AND/?\s?OR )?REOPERATION(?: IS)?\s*:\s*([^.]*)"
)

# Categories applied to the captured reason text only.
CATEGORIES = {
    "rupture": r"RUPTUR",
    "deflation": r"DEFLAT",
    "leak": r"LEAK",
    "capsular_contracture": r"CONTRACTUR|BAKER",
}
MECHANICAL = ["rupture", "deflation", "leak"]

report = pd.read_csv(PROCESSED / f"report_table_{LABEL}.csv", dtype=str, keep_default_na=False)
report = report[report["IMPLANT_TYPE"].isin(GROUPS)
                & report["N_PROBLEM_CODES"].astype(int).gt(0)].copy()

narratives = pd.read_csv(RAW / NARRATIVE_FILE, dtype=str,
                         keep_default_na=False, encoding="utf-8-sig",
                         usecols=["MDR_REPORT_KEY", "FOI_TEXT"])
narratives = narratives[narratives["MDR_REPORT_KEY"].isin(report["MDR_REPORT_KEY"])]

# One block of text per report (a report can have several narrative rows).
text = narratives.groupby("MDR_REPORT_KEY")["FOI_TEXT"].agg(" ".join).str.upper()
reasons = text.apply(lambda t: " | ".join(REASON.findall(t)))

report["NARRATIVE_PRESENT"] = report["MDR_REPORT_KEY"].map(text).fillna("").str.strip().ne("").astype(int)
report["REASON_TEXT"] = report["MDR_REPORT_KEY"].map(reasons).fillna("")
report["REASON_STATEMENT"] = report["REASON_TEXT"].str.strip().ne("").astype(int)

for name, pattern in CATEGORIES.items():
    report[f"TEXT_{name.upper()}"] = report["REASON_TEXT"].str.contains(pattern, regex=True).astype(int)
report["TEXT_MECHANICAL"] = report[[f"TEXT_{m.upper()}" for m in MECHANICAL]].max(axis=1)
# Does the narrative say the report covers one breast of a bilateral case?
# If so, the same patient may have a second report for the other implant,
# so reports cannot be treated as independent patients.
SIDE = r"THIS RECORD IS FOR THE (?:LEFT|RIGHT)|ONE OF TWO|BILATERAL|BOTH BREASTS|LEFT AND RIGHT|RIGHT AND LEFT"
report["NARRATIVE_SIDE_OR_BILATERAL"] = report["MDR_REPORT_KEY"].map(text).fillna("").str.contains(SIDE, regex=True).astype(int)
# For comparison only: "rupture" anywhere in the narrative, including warning text.
report["ANYWHERE_RUPTURE"] = report["MDR_REPORT_KEY"].map(text).fillna("").str.contains("RUPTUR").astype(int)
report["CODE_RUPTURE"] = report.get("PROBLEM_2208", "0").astype(int)
report["CODE_FAILURE"] = report.get("PROBLEM_1924", "0").astype(int)
report["CODE_CONTRACTURE"] = report.get("PROBLEM_1761", "0").astype(int)

group = report["IMPLANT_TYPE"]
n = group.value_counts().reindex(GROUPS)


def cell(col, subset=None):
    out = []
    for g in GROUPS:
        m = group.eq(g) if subset is None else group.eq(g) & subset
        denom = int(m.sum())
        c = int(report.loc[m, col].sum())
        out.append(f"{c:,} / {denom:,} ({100 * c / denom:.1f}%)" if denom else "n/a")
    return out


has_reason = report["REASON_STATEMENT"].eq(1)
table3 = pd.DataFrame(
    [
        ["Narrative text present"] + cell("NARRATIVE_PRESENT"),
        ["Narrative refers to one side or a bilateral case"] + cell("NARRATIVE_SIDE_OR_BILATERAL"),
        ["Reason-for-reoperation statement present"] + cell("REASON_STATEMENT"),
        ["Coded: Rupture (2208)"] + cell("CODE_RUPTURE"),
        ["Coded: Failure of Implant (1924)"] + cell("CODE_FAILURE"),
        ["Coded: Capsular Contracture (1761)"] + cell("CODE_CONTRACTURE"),
        ["Whole narrative mentions rupture (any context)"] + cell("ANYWHERE_RUPTURE"),
        ["Reason text: rupture"] + cell("TEXT_RUPTURE"),
        ["Reason text: deflation"] + cell("TEXT_DEFLATION"),
        ["Reason text: any mechanical (rupture, deflation or leak)"] + cell("TEXT_MECHANICAL"),
        ["Reason text: capsular contracture"] + cell("TEXT_CAPSULAR_CONTRACTURE"),
        ["Among reports with a reason statement: mechanical"] + cell("TEXT_MECHANICAL", has_reason),
        ["Mechanical in reason text but NOT coded Rupture"]
        + cell("TEXT_MECHANICAL", report["CODE_RUPTURE"].eq(0)),
        ["Coded Failure of Implant: reason text mechanical"]
        + cell("TEXT_MECHANICAL", report["CODE_FAILURE"].eq(1)),
    ],
    columns=["Measure (all report counts)"] + GROUPS,
)
table3.to_csv(TABLES / f"table3_coded_vs_text_reason_{LABEL}.csv", index=False)
print(table3.to_string(index=False))

# Which manufacturers use the standard sentence? If coverage depends on
# the manufacturer, the text method will miss some groups of reports.
by_maker = (report.assign(MAKER=report["MANUFACTURER_G1_NAME"].str.strip().replace("", "(blank)"))
            .groupby("MAKER")
            .agg(reports=("MDR_REPORT_KEY", "size"),
                 silicone=("IMPLANT_TYPE", lambda s: int((s == "Silicone").sum())),
                 saline=("IMPLANT_TYPE", lambda s: int((s == "Saline").sum())),
                 with_reason_statement=("REASON_STATEMENT", lambda s: int(s.astype(int).sum())))
            .sort_values("reports", ascending=False))
by_maker["percent_with_statement"] = (100 * by_maker["with_reason_statement"] / by_maker["reports"]).round(1)
by_maker.to_csv(TABLES / f"table4_reason_statement_by_manufacturer_{LABEL}.csv")
print("\n", by_maker.head(8).to_string())

# Random sample for manual labelling (same sample every run because of SEED).
sample = pd.concat([report[group.eq(g)].sample(SAMPLE_PER_GROUP, random_state=SEED)
                    for g in GROUPS])
sample = sample.assign(NARRATIVE=sample["MDR_REPORT_KEY"].map(text),
                       REVIEWER_1_MECHANICAL="", REVIEWER_1_CONTRACTURE="",
                       REVIEWER_2_MECHANICAL="", REVIEWER_2_CONTRACTURE="", NOTES="")
keep = ["MDR_REPORT_KEY", "IMPLANT_TYPE", "MANUFACTURER_G1_NAME", "REASON_TEXT",
        "TEXT_MECHANICAL", "TEXT_CAPSULAR_CONTRACTURE", "CODE_RUPTURE", "CODE_FAILURE",
        "CODE_CONTRACTURE", "NARRATIVE", "REVIEWER_1_MECHANICAL", "REVIEWER_1_CONTRACTURE",
        "REVIEWER_2_MECHANICAL", "REVIEWER_2_CONTRACTURE", "NOTES"]
sample[keep].to_csv(PROCESSED / f"validation_sample_{LABEL}.csv", index=False)
print(f"\nValidation sample saved: data/processed/validation_sample_{LABEL}.csv ({len(sample)} reports)")

# Are the main measures stable from one year to the next?
rows = []
for (year, g), d in report.groupby(["REPORT_YEAR", "IMPLANT_TYPE"]):
    rows.append({"Year": year, "Group": g, "Reports": len(d),
                 "Reason statement %": round(100 * d["REASON_STATEMENT"].mean(), 1),
                 "Coded rupture %": round(100 * d["CODE_RUPTURE"].mean(), 1),
                 "Reason text mechanical %": round(100 * d["TEXT_MECHANICAL"].mean(), 1),
                 "Coded capsular contracture %": round(100 * d["CODE_CONTRACTURE"].mean(), 1),
                 "Reason text capsular contracture %": round(100 * d["TEXT_CAPSULAR_CONTRACTURE"].mean(), 1)})
by_year = pd.DataFrame(rows)
by_year.to_csv(TABLES / f"table5_key_measures_by_year_{LABEL}.csv", index=False)
print("\n", by_year.to_string(index=False))
