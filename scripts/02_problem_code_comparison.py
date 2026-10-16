"""
Step 2: Compare coded patient problems between silicone and saline reports.

What this script does
---------------------
For each patient-problem code, it calculates the share of reports in
each implant group that list that code, with a 95% confidence interval.

    share = reports in the group that list the code
            / reports in the group with at least one problem code

Why a confidence interval: a percentage from 8,858 reports is more
precise than one from 50. The interval shows that precision. It only
describes the uncertainty in the reported share. It is NOT a measure of
how often patients with implants have the problem, because MAUDE has no
count of all implanted patients.

We use the Wilson interval for each share, and Newcombe's method
(built from the two Wilson intervals) for the silicone minus saline
difference. Both behave well when a share is close to 0%.

Codes 4580, 4581 and 4582 describe how complete the report is
("Insufficient Information", etc.), not a clinical problem. They are
left out of the ranking but those reports stay in the denominator.

Outputs
-------
results/tables/table1_report_characteristics_<YEARS>.csv
results/tables/table2_top10_problem_codes_<YEARS>.csv
results/figures/figure1_top10_problem_codes_<YEARS>.png (and .pdf)

Run after step 1:
    python scripts/02_problem_code_comparison.py
"""

import textwrap

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.ticker import PercentFormatter

from config import LABEL, REPO, PROCESSED, TABLES, FIGURES, INFORMATION_STATUS_CODES

GROUPS = ["Silicone", "Saline"]
Z = 1.959964  # z value for a 95% interval
TABLES.mkdir(parents=True, exist_ok=True)
FIGURES.mkdir(parents=True, exist_ok=True)

report = pd.read_csv(PROCESSED / f"report_table_{LABEL}.csv", dtype=str,
                     keep_default_na=False)
dictionary = pd.read_csv(PROCESSED / "problem_code_dictionary.csv", dtype=str,
                         keep_default_na=False)
names = dict(zip(dictionary["PROBLEM_CODE"], dictionary["PROBLEM_DESCRIPTION"]))

# Two-group comparison only. "Both" reports (if any) are counted in Table 1.
n_both = int((report["IMPLANT_TYPE"] == "Both").sum())
report = report[report["IMPLANT_TYPE"].isin(GROUPS)].copy()

# Denominator: reports with at least one problem code.
report = report[report["N_PROBLEM_CODES"].astype(int) > 0]
group = report["IMPLANT_TYPE"]
n = group.value_counts().reindex(GROUPS)


def wilson(count, total):
    """95% Wilson interval for a proportion. Returns (low, high)."""
    p = count / total
    centre = (p + Z**2 / (2 * total)) / (1 + Z**2 / total)
    half = (Z / (1 + Z**2 / total)) * np.sqrt(p * (1 - p) / total + Z**2 / (4 * total**2))
    return centre - half, centre + half


def newcombe(c1, n1, c2, n2):
    """95% interval for the difference p1 - p2 (Newcombe hybrid score)."""
    p1, p2 = c1 / n1, c2 / n2
    l1, u1 = wilson(c1, n1)
    l2, u2 = wilson(c2, n2)
    d = p1 - p2
    return d - np.sqrt((p1 - l1) ** 2 + (u2 - p2) ** 2), d + np.sqrt((u1 - p1) ** 2 + (p2 - l2) ** 2)


# ---------------- Table 1: who and what is in each group ----------------
def share(mask):
    return [f"{int(mask[group == g].sum()):,} ({100 * mask[group == g].mean():.1f}%)" for g in GROUPS]

info_cols = [f"PROBLEM_{c}" for c in INFORMATION_STATUS_CODES if f"PROBLEM_{c}" in report]
only_info = report["N_CLINICAL_PROBLEM_CODES"].astype(int).eq(0)

table1 = pd.DataFrame(
    [
        ["Reports (n)"] + [f"{n[g]:,}" for g in GROUPS],
        ["Submitted by a manufacturer"] + share(report["REPORT_SOURCE_CODE"].eq("M")),
        ["Event type: injury"] + share(report["EVENT_TYPE"].eq("IN")),
        ["Event type: malfunction"] + share(report["EVENT_TYPE"].eq("M")),
        ["Includes at least one follow-up submission"] + share(report["TYPE_OF_REPORT"].str.contains("F")),
        ["Lists an information-status code (4580-4582)"] + share(report[info_cols].astype(int).sum(axis=1).gt(0)),
        ["Lists only information-status codes"] + share(only_info),
        ["Date of event missing"] + share(report["DATE_OF_EVENT"].str.strip().eq("")),
    ],
    columns=["Characteristic"] + GROUPS,
)
table1.to_csv(TABLES / f"table1_report_characteristics_{LABEL}.csv", index=False)
print(f"Reports listing both silicone and saline codes (excluded): {n_both}")
print(table1.to_string(index=False))

# ---------------- Table 2: top 10 clinical problem codes ----------------
problem_cols = [c for c in report.columns if c.startswith("PROBLEM_") and c[8:].isdigit()
                and c[8:] not in INFORMATION_STATUS_CODES]
indicators = report[problem_cols].astype(int)
top = indicators.sum().sort_values(ascending=False).head(10).index

rows = []
for col in top:
    code = col.replace("PROBLEM_", "")
    row = {"Problem code": code, "Problem": names.get(code, code)}
    counts = {}
    for g in GROUPS:
        c = int(indicators.loc[group == g, col].sum())
        lo, hi = wilson(c, n[g])
        counts[g] = c
        row[f"{g} reports"] = c
        row[f"{g} n"] = int(n[g])
        row[f"{g} %"] = 100 * c / n[g]
        row[f"{g} 95% CI low"] = 100 * lo
        row[f"{g} 95% CI high"] = 100 * hi
    d_lo, d_hi = newcombe(counts["Silicone"], n["Silicone"], counts["Saline"], n["Saline"])
    row["Difference (silicone - saline), points"] = row["Silicone %"] - row["Saline %"]
    row["Difference 95% CI low"] = 100 * d_lo
    row["Difference 95% CI high"] = 100 * d_hi
    rows.append(row)

table2 = pd.DataFrame(rows)
table2.round(2).to_csv(TABLES / f"table2_top10_problem_codes_{LABEL}.csv", index=False)
print("\n", table2[["Problem", "Silicone %", "Saline %",
                    "Difference (silicone - saline), points"]].round(1).to_string(index=False))

# ---------------- Figure 1 ----------------
colors = {"Silicone": "#2A6FB5", "Saline": "#C8702A"}
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10})
fig, ax = plt.subplots(figsize=(8, 5.2))
y = np.arange(len(table2))
h = 0.36

for i, g in enumerate(GROUPS):
    pos = y - h / 2 if i == 0 else y + h / 2
    pct = table2[f"{g} %"]
    err = [pct - table2[f"{g} 95% CI low"], table2[f"{g} 95% CI high"] - pct]
    bars = ax.barh(pos, pct, height=h * 0.92, color=colors[g],
                   label=f"{g} (n = {n[g]:,} reports)")
    ax.errorbar(pct, pos, xerr=err, fmt="none", ecolor="#333333", elinewidth=0.8, capsize=2)
    # Label each bar just past the end of its confidence interval.
    for yy, v, hi in zip(pos, pct, table2[f"{g} 95% CI high"]):
        ax.text(hi + 0.6, yy, f"{v:.1f}%", va="center", fontsize=8, color="#333333")

ax.set_yticks(y)
ax.set_yticklabels([textwrap.fill(p, 24) for p in table2["Problem"]])
ax.invert_yaxis()
ax.xaxis.set_major_formatter(PercentFormatter(xmax=100))
ax.set_xlim(0, max(table2[[f"{g} 95% CI high" for g in GROUPS]].max()) * 1.15)
ax.set_xlabel("Share of reports in each implant group (95% CI)")
ax.grid(axis="x", alpha=0.2)
ax.set_axisbelow(True)
ax.tick_params(axis="y", length=0)
for s in ["top", "right", "left"]:
    ax.spines[s].set_visible(False)
ax.legend(loc="lower right", frameon=False)
fig.tight_layout()
for ext in ["png", "pdf"]:
    fig.savefig(FIGURES / f"figure1_top10_problem_codes_{LABEL}.{ext}", dpi=300, facecolor="white")
print(f"\nSaved tables to {TABLES.relative_to(REPO)} and figure to {FIGURES.relative_to(REPO)}")
