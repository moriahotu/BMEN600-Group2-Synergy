# BMEN 600 Project

## Group 2: Synergy

## Team Members: Asma Sadia Khan, Neriah Otu, Ukeme Inyang, Nazanin Askari

## Candidate Project 1: Endometriosis Fibrosis and Macrophage–Fibroblast Signalling


We want to investigate which macrophage–fibroblast signalling pathways are reproducibly dysregulated across independent human single-cell endometriosis datasets.

### Datasets

GSE213216: https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE213216

GSE179640: https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE179640

### Biggest Uncertainty

Our biggest uncertainty is whether comparable macrophage and fibroblast populations are represented across both datasets well enough to independently validate the same signalling pathways.

## Candidate Project 2: Breast Implants and MAUDE Data Quality

### Possible Research Question

We want to investigate whether missing patient demographic information in FDA MAUDE breast implant adverse-event reports differs systematically by event type, manufacturer, and reporting source.

#### Datasets

FDA MAUDE Database: https://www.accessdata.fda.gov/scripts/cdrh/cfdocs/cfmaude/textsearch.cfm

openFDA Device Event API: https://open.fda.gov/apis/device/event/

### Biggest Uncertainty

Our biggest uncertainty is whether demographic fields are captured consistently enough across reporting pathways and years to distinguish meaningful missingness patterns from changes in MAUDE reporting practices.

## Current decision 

We are currently leaning toward the endometriosis study because, based on our preliminary research, the datasets appear more accessible and easier to navigate.


## Project Decision (Oct 2)

**REVISE.** The overall project works, but we need to change our research question.

We have moved from the endometriosis study to Candidate Project 2, breast implant adverse-event reports in the FDA MAUDE database. The topic and data source are settled. The research question is not final yet. We will inspect the data first (available fields, missing values, duplicate reports, and what counts as one independent case) and then choose one focused question the data can support before the Midterm Research Plan on Oct 16.

## Team Plan (Oct 2)

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
