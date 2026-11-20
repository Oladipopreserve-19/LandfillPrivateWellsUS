# Private wells near US municipal landfills

A national screen of how many people on private domestic wells live near US municipal solid waste landfills, and where they coincide with older landfills and permeable aquifers.

**Author:** Oladipo Preserve Oluwadimimu, University of Ilorin · ORCID [0009-0008-3770-1704](https://orcid.org/0009-0008-3770-1704)
**Preprint:** [link to be added when posted on EarthArXiv]

## Main results (2010 population, conterminous US, 2,265 landfills)

| Radius | Private-well users (no double counting) | Landfills with ≥100 users |
|---|---|---|
| 1 km | 73,556 | 202 |
| 2 km | 342,911 | 926 |
| 5 km | 2,287,862 | 1,849 |

* Median landfill: 65 private-well users within 2 km; 35 landfills have more than 1,000.
* Closed landfills (median 100) and landfills opened before the 1993 federal liner rules (median 80) have more nearby well users than open (42) and newer (34) sites.
* **213 priority landfills** in 31 states: opened before 1993, over sand-and-gravel or carbonate aquifers, with at least 100 well users within 2 km (`data/priority_landfills.csv`).

These are counts of people who could be affected, not of contamination. The list shows where private-well testing would be most informative.

## Reproduce

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
# Download into data/:
#   EPA LMOP landfill-level data (Sept 2024): https://www.epa.gov/lmop/landfill-technical-data  -> data/lmop_landfills.xlsx
#   USGS domestic wells 2010 REM raster: https://doi.org/10.5066/P9FSLU3B                    -> data/REM_map_2010.tif
#   USGS principal aquifers: https://water.usgs.gov/GIS/dsdl/aquifers_us.zip                  -> unzip to data/aquifers/
.venv/bin/python -I code/01_exposure.py   # well users within 1, 2, 5 km of each landfill; aquifer; flags
.venv/bin/python -I code/02_summary.py    # national totals (no double counting) and breakdowns
.venv/bin/python -I code/03_figures.py    # figures
```

## Contents

* `code/` analysis scripts, run in order
* `data/landfill_exposure.csv` every landfill with well users at 1, 2 and 5 km, aquifer type and flags
* `data/priority_landfills.csv`, `data/top20_landfills.csv`, `data/summary_*.csv` results tables
* `figures/` figures 1 to 5 (300 dpi)

## Data and licence

Inputs are US government public-domain data (EPA LMOP; USGS, Johnson and Belitz 2019, doi:10.5066/P9FSLU3B; USGS principal aquifers) and are not redistributed here. Code: MIT licence. Results tables and figures: CC BY 4.0.

## Use of AI tools

Claude (Anthropic) assisted with writing code and text. The author designed the study, chose the criteria and checked all results.
