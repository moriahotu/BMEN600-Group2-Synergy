from pathlib import Path
import textwrap
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter

folder = Path(r"C:\Users\asksa\Downloads\601 project")

data = pd.read_csv(
    folder / "breast_implant_merged_2025.csv",
    dtype=str,
    keep_default_na=False,
    encoding="utf-8-sig",
)

dictionary = pd.read_csv(
    folder / "breast_implant_problem_dictionary.csv",
    dtype=str,
    keep_default_na=False,
    encoding="utf-8-sig",
)

if data["MDR_REPORT_KEY"].duplicated().any():
    raise ValueError("Duplicate report IDs found. Check the merge first.")

# Keep the two comparison groups.
comparison = data[
    data["IMPLANT_TYPE"].isin(["Silicone", "Saline"])
].copy()

# Denominator: reports with at least one nonblank problem code.
has_codes = pd.to_numeric(
    comparison["HAS_NONBLANK_PROBLEM_CODE"], errors="raise"
).eq(1)

print("Reports excluded because no usable problem codes were available:")
print(
    comparison.loc[~has_codes, "IMPLANT_TYPE"]
    .value_counts()
    .reindex(["Silicone", "Saline"], fill_value=0)
)

analysis = comparison.loc[has_codes].copy()

group_sizes = (
    analysis["IMPLANT_TYPE"]
    .value_counts()
    .reindex(["Silicone", "Saline"], fill_value=0)
)

if (group_sizes == 0).any():
    raise ValueError("Both implant groups must have reports to compare.")

# Exclude these status codes from the plotted problems.
# Reports with these codes remain in the denominator.
excluded_codes = {"4580", "4581", "4582"}

dictionary["PROBLEM_CODE"] = dictionary["PROBLEM_CODE"].str.strip()

plot_dictionary = dictionary[
    ~dictionary["PROBLEM_CODE"].isin(excluded_codes)
].copy()

plot_dictionary = plot_dictionary[
    plot_dictionary["INDICATOR_COLUMN"].isin(analysis.columns)
]

if plot_dictionary["INDICATOR_COLUMN"].duplicated().any():
    raise ValueError("Duplicate problem definitions found in dictionary.")

problem_columns = plot_dictionary["INDICATOR_COLUMN"].tolist()

if not problem_columns:
    raise ValueError("No problem indicator columns found.")

indicators = analysis[problem_columns].apply(
    pd.to_numeric, errors="raise"
)

if indicators.isna().any().any():
    raise ValueError("Unexpected blank indicators in reports with codes.")

if not indicators.isin([0, 1]).all().all():
    raise ValueError("Problem indicators must contain only 0 or 1.")

# Select the top 10 by combined report count across both groups.
combined_counts = indicators.sum().sort_values(ascending=False)
top_columns = combined_counts[combined_counts > 0].head(10).index.tolist()

if not top_columns:
    raise ValueError("No coded problems remain after exclusions.")

names = plot_dictionary.set_index(
    "INDICATOR_COLUMN"
)["PROBLEM_DESCRIPTION"].to_dict()

codes = plot_dictionary.set_index(
    "INDICATOR_COLUMN"
)["PROBLEM_CODE"].to_dict()

# Build the exact table used for plotting.
rows = []

for column in top_columns:
    row = {
        "Problem code": codes[column],
        "Problem": names.get(column) or column,
        "Combined reports": int(combined_counts[column]),
    }

    for group in ["Silicone", "Saline"]:
        count = int(
            indicators.loc[
                analysis["IMPLANT_TYPE"].eq(group), column
            ].sum()
        )
        denominator = int(group_sizes[group])

        row[f"{group} reports"] = count
        row[f"{group} denominator"] = denominator
        row[f"{group} percent"] = 100 * count / denominator

    rows.append(row)

summary = pd.DataFrame(rows)

summary.to_csv(
    folder / "top10_problems_comparison_2025.csv",
    index=False,
    encoding="utf-8-sig",
)

# ---------- Draw the chart ----------

plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 11,
})

fig, ax = plt.subplots(figsize=(13, 9))
fig.subplots_adjust(left=0.30, right=0.94, top=0.82, bottom=0.17)

y = list(range(len(summary)))
bar_height = 0.34

silicone_bars = ax.barh(
    [position - bar_height / 2 for position in y],
    summary["Silicone percent"],
    height=bar_height,
    color="#376A9B",
    label=f"Silicone (n = {group_sizes['Silicone']:,} reports)",
)

saline_bars = ax.barh(
    [position + bar_height / 2 for position in y],
    summary["Saline percent"],
    height=bar_height,
    color="#D98947",
    label=f"Saline (n = {group_sizes['Saline']:,} reports)",
)

labels = [
    textwrap.fill(name, width=30)
    for name in summary["Problem"]
]

ax.set_yticks(y)
ax.set_yticklabels(labels)
ax.invert_yaxis()

ax.bar_label(silicone_bars, fmt="%.1f%%", padding=4, fontsize=9)
ax.bar_label(saline_bars, fmt="%.1f%%", padding=4, fontsize=9)

maximum = summary[
    ["Silicone percent", "Saline percent"]
].to_numpy().max()

ax.set_xlim(0, max(5, maximum * 1.20))
ax.xaxis.set_major_formatter(PercentFormatter(xmax=100))
ax.set_xlabel("Percentage of reports within each implant group", labelpad=12)

ax.set_axisbelow(True)
ax.grid(axis="x", alpha=0.20)
ax.tick_params(axis="y", length=0)

for spine in ["top", "right", "left"]:
    ax.spines[spine].set_visible(False)

fig.suptitle(
    "Most frequently coded problems in breast implant reports",
    fontsize=17,
    fontweight="bold",
    y=0.97,
)

fig.text(
    0.5, 0.925,
    "FDA MAUDE • Reports received in 2025 • Top 10 across both groups",
    ha="center",
    fontsize=11,
    color="#555555",
)

handles, legend_labels = ax.get_legend_handles_labels()
fig.legend(
    handles,
    legend_labels,
    loc="upper center",
    bbox_to_anchor=(0.60, 0.90),
    ncol=2,
    frameon=False,
    fontsize=10,
)

fig.text(
    0.04, 0.035,
    "Denominator: reports with at least one nonblank problem code in each implant group.\n"
    "Codes 4580, 4581 and 4582 are excluded from the ranking; those reports remain in denominators.\n"
    "Reports may contain multiple problems. Percentages describe reporting patterns, not patient risk.",
    fontsize=9,
    color="#555555",
    linespacing=1.5,
)

png_path = folder / "top10_problems_silicone_vs_saline_2025.png"
pdf_path = folder / "top10_problems_silicone_vs_saline_2025.pdf"

fig.savefig(png_path, dpi=300, facecolor="white")
fig.savefig(pdf_path, facecolor="white")

print("\nReports included in graph:")
print(group_sizes.to_string())

print("\nPlotted results:")
print(
    summary[
        ["Problem", "Silicone percent", "Saline percent"]
    ].round(2).to_string(index=False)
)

print(f"\nGraph saved: {png_path}")
print(f"PDF saved: {pdf_path}")
print("Table saved: top10_problems_comparison_2025.csv")

plt.show()