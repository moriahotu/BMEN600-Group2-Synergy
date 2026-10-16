# BMEN 600 Group 2: Synergy

**Team:** Asma Sadia Khan, Neriah Otu, Ukeme Inyang, Nazanin Askari

## Research question

How do reported mechanical and biological complications differ between silicone-filled and saline-filled breast implants, and can standardized text-based classification improve the identification of these complications in FDA MAUDE?

MAUDE holds submitted adverse-event reports, not a record of everyone who received an implant. All results describe patterns among reports. They are not complication rates or comparative safety estimates.

## Data

**Source:** U.S. FDA Manufacturer and User Facility Device Experience (MAUDE) database, downloaded as Medical Device Reporting (MDR) data files:
https://www.fda.gov/medical-devices/medical-device-reporting-mdr-how-report-medical-device-problems/mdr-data-files

**Breast implant reports** are identified by FDA product code on the device record: `FTR` (silicone gel-filled) and `FWM` (saline-filled). Reports listing both codes are kept apart from the two-group comparison.

**Study period:** reports received from 2020 through 2025 (master `DATE_RECEIVED`). The current preliminary analysis covers 2024 and 2025. Records for 2020 to 2023 will be added with the same scripts.

**Unit of analysis:** one report (`MDR_REPORT_KEY`). Follow-up submissions share the key of the original report, so they do not create extra rows. One patient can still produce more than one report, for example one per breast.

The FDA files and our extracted CSVs are not stored here. The narrative file alone is about 150 MB, and narrative text is reviewed before any of it is shared. To run the code, place these extracted files in `data/raw/` (team members can copy them from the team OneDrive folder `Synergy - BMEN 600/Data Sets`):

| File | One row per | Used by |
|---|---|---|
| `breast_implant_master.csv` | report | step 1 |
| `breast_implant_devices_2024_2025.csv` | device on a report | step 1 |
| `breast_implant_problems.csv` | patient-problem code on a report | step 1 |
| `breast_implant_narratives_2024_2025.csv` | narrative text block | step 3 |
| `breast_implant_merged_2025.csv` (optional) | report | step 1 cross-check |

The file names and study years are set in `scripts/config.py`.

**Access for reviewers:** the extracted CSV files are available from the team on request. They can also be rebuilt from the FDA files `mdrfoithru2025.zip`, `device2024.zip`, `device2025.zip`, `patientthru2025.zip`, `patientproblemcode_thru2025.zip` and `foitext2024.zip`/`foitext2025.zip` by keeping records whose device product code is `FTR` or `FWM` and linking them by `MDR_REPORT_KEY`.

## Where the midterm report's outputs come from

| Output in the report | Produced by | File |
|---|---|---|
| Bar chart of the 10 most frequently coded patient problems, silicone vs saline | `scripts/02_problem_code_comparison.py` | `results/figures/figure1_top10_problem_codes_2024-2025.png` (numbers in `results/tables/table2_top10_problem_codes_2024-2025.csv`) |
| Table comparing problem codes with the narrative reason-for-reoperation statement | `scripts/03_reoperation_reason_text.py` | `results/tables/table3_coded_vs_text_reason_2024-2025.csv` |
| Report characteristics quoted in the text (reporting source, event type, missing dates) | `scripts/02_problem_code_comparison.py` | `results/tables/table1_report_characteristics_2024-2025.csv` |
| Reason-statement use by manufacturer and year-to-year stability | `scripts/03_reoperation_reason_text.py` | `results/tables/table4_...csv`, `results/tables/table5_...csv` |

File names in `results/` are fixed by the code, so their numbers do not always match the figure and table numbers in the report.

## How to run

1. Install Python 3.10 or newer.
2. Open a terminal in this folder and install the packages:
   ```
   pip install -r requirements.txt
   ```
3. Put the CSV files listed above in `data/raw/`.
4. Run everything in order:
   ```
   python run_all.py
   ```
   or run one step at a time, for example `python scripts/02_problem_code_comparison.py`.

To change the study years, edit `YEARS` in `scripts/config.py`. Output files are named after the years, for example `table2_top10_problem_codes_2024-2025.csv`.

## What each file does

| Path | Purpose |
|---|---|
| `scripts/config.py` | Study years, folder locations and input file names shared by all scripts |
| `scripts/01_build_report_table.py` | Joins the master, device and problem files into one row per report, assigns silicone or saline, and checks each year against the matching `breast_implant_merged_<year>.csv` when it is available |
| `scripts/02_problem_code_comparison.py` | Report characteristics (Table 1), top 10 coded patient problems with 95% confidence intervals (Table 2) and Figure 1 |
| `scripts/03_reoperation_reason_text.py` | Extracts the "reason for reoperation" statement from narratives, compares it with the problem codes (Table 3), checks which manufacturers use it (Table 4), compares the main measures by year (Table 5) and draws a 200-report sample for manual validation |
| `run_all.py` | Runs the three steps in order |
| `results/tables/` | Output tables (CSV) |
| `results/figures/` | Output figures (PNG and PDF) |
| `data/raw/`, `data/processed/` | Local data folders. Their contents are not uploaded to GitHub |
| `plot_problems.py`, `top10_problems_*` | First version of the preliminary analysis (9 October). Step 2 reproduces these numbers with portable file paths |

## Software

Python 3.13 with pandas, NumPy and matplotlib (versions in `requirements.txt`). Runs in any Python environment, including Jupyter or Google Colab.

## Project history

### Candidate Project 1: Endometriosis Fibrosis and Macrophage–Fibroblast Signalling


We want to investigate which macrophage–fibroblast signalling pathways are reproducibly dysregulated across independent human single-cell endometriosis datasets.

#### Datasets

GSE213216: https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE213216

GSE179640: https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE179640

#### Biggest Uncertainty

Our biggest uncertainty is whether comparable macrophage and fibroblast populations are represented across both datasets well enough to independently validate the same signalling pathways.

### Candidate Project 2: Breast Implants and MAUDE Data Quality

#### Possible Research Question

We want to investigate whether missing patient demographic information in FDA MAUDE breast implant adverse-event reports differs systematically by event type, manufacturer, and reporting source.

#### Datasets

FDA MAUDE Database: https://www.accessdata.fda.gov/scripts/cdrh/cfdocs/cfmaude/textsearch.cfm

openFDA Device Event API: https://open.fda.gov/apis/device/event/

#### Biggest Uncertainty

Our biggest uncertainty is whether demographic fields are captured consistently enough across reporting pathways and years to distinguish meaningful missingness patterns from changes in MAUDE reporting practices.

### Current decision 

We are currently leaning toward the endometriosis study because, based on our preliminary research, the datasets appear more accessible and easier to navigate.


### Project Decision (Oct 2)

**REVISE.** The overall project works, but we need to change our research question.

We have moved from the endometriosis study to Candidate Project 2, breast implant adverse-event reports in the FDA MAUDE database. The topic and data source are settled. The research question is not final yet. We will inspect the data first (available fields, missing values, duplicate reports, and what counts as one independent case) and then choose one focused question the data can support before the Midterm Research Plan on Oct 16.

### Team Plan (Oct 2)

Every task has leads and reviewers, and each member leads some tasks and reviews others. This is a draft that we will adjust once the research question is final.

| Task | Lead(s) | Collaborators and Reviewers | What does the whole team need to understand? |
|---|---|---|---|
| Literature Review and Background Research | Ukeme, Neriah | Asma and Nazanin add and check sources in their areas | What is known about breast implant adverse events and what is unresolved |
| Dataset Interpretation | Nazanin | Ukeme | What one MAUDE report represents and why report counts are not incidence |
| Dataset Cleaning and Preprocessing | Nazanin, Asma | Neriah | Inclusion criteria, duplicate reports, and how missing values are handled |
| Analysis | Ukeme, Nazanin | Asma | What each analysis step does and why we chose it |
| Validation and Evaluation | Asma | Neriah and Ukeme independently check the outputs | How we confirm the results are not misleading |
| Interpretation | Neriah, Ukeme | Nazanin, Asma | The biological and clinical meaning of the results and the limits of surveillance data |
| Documentation and Reproducibility | Asma, Neriah | Nazanin | How to get from the raw FDA data to our figures using this repository |

### 9 October 2026 — Preliminary analysis

- Created an initial comparison of the top 10 coded problems in silicone-only and saline-only breast implant reports received by FDA MAUDE in 2025.
- Uploaded the plotting script, comparison table, and graph in PNG and PDF formats.
- Selected the top 10 problems across both implant groups combined. Percentages use reports with at least one nonblank problem code within each group.
- Excluded information-status codes from the ranking and reports involving both implant types from the comparison.

**Interpretation:** Results describe submitted reports, not complication risks among implant recipients. Each report can include multiple problems.

**Next steps:** Review the graph and data quality, examine related literature, and refine the final research question.

### 15 October 2026 — Reproducible pipeline

- Added numbered scripts that run from the repository folder on any computer.
- Step 1 rebuilds the report-level table from the separate FDA extract files and matches the 9 October merged file exactly (40,245 reports: 31,387 silicone, 8,858 saline).
- Added 95% confidence intervals to the problem-code comparison.
- Added the narrative "reason for reoperation" extraction and a validation sample.

### 15 October 2026 — Study period and midterm outputs

- Study period set to reports received from 2020 to 2025. Preliminary results now cover 2024 and 2025 (79,982 reports: 61,673 silicone, 18,309 saline).
- Study years moved into `scripts/config.py`.
- Added the year-by-year comparison (Table 5).
