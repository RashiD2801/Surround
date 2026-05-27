# Instructions: How to Run the Session 3 Data Cleaning Pipeline

Two separate cleaning scripts were built in Session 3. This document explains
what each does, when to use it, and how to run it.

---

## Overview

| Script | Input | Output | Use when |
|---|---|---|---|
| `clean_multistation.py` | 8 AQICN station CSVs | `krakow_multistation_CLEANED.csv` | Primary pipeline — 8-station air quality cleaning |
| `spatial_features_pipeline.py` | Urban Atlas `.fgb` + OSM | `krakow_spatial_features.csv` + `krakow_final_dataset.csv` | After cleaning — extract spatial features and merge |
| `clean_krakow_dataset.py` | `krakow_ml_dataset.csv` (single station) | `krakow_ml_dataset_CLEANED.csv` | Single-station earlier pipeline (reference only) |

**For ML modeling, use `krakow_final_dataset.csv` — this is the merged, ML-ready output.**

---

## Quick Start

```powershell
# From the session 3/ folder:

# Step 1: Clean and combine the 8 station CSVs
python scripts/clean_multistation.py

# Step 2: Extract spatial features + merge with AQ data
python scripts/spatial_features_pipeline.py
```

Total runtime: ~5-10 minutes.

---

## Prerequisites

### Python packages

```powershell
pip install pandas numpy geopandas pyproj shapely osmnx
```

On Windows, if geopandas fails:
```powershell
conda install -c conda-forge geopandas osmnx
```

### Required files

Place these before running:

| File | Where | How to get |
|---|---|---|
| 8 station CSVs | `session 3/data/raw/` | Download from AQICN (see `session 3/DATA SOURCES.md`) |
| Urban Atlas FlatGeobuf | `session 3/` root | Download from Copernicus portal (see `session 3/DATA SOURCES.md`) |

---

## Script 1: `clean_multistation.py`

### What it does (10 steps)

| Step | Action | Rows affected |
|---|---|---|
| 1 | Load 8 station CSVs, tag with station metadata | — |
| 2 | Filter to 2019-2024 | Pre-2019 data removed |
| 3 | Remove duplicate (station, date) pairs | Rare |
| 4 | Drop rows with missing PM2.5; clip negatives to 0 | ~25-30% missing |
| 5 | Exclude COVID period (Mar 15 – May 31 2020) | ~390 rows |
| 6 | Drop columns >50% missing | CO typically dropped |
| 7 | Impute remaining pollutants with per-station median | Fills remaining gaps |
| 8 | Flag extreme PM2.5 values (>200 µg/m³) — keep, don't drop | Real winter events |
| 9 | Add temporal features (month, cyclical, season, lags) | Adds ~15 columns |
| 10 | Drop lag cold-start rows; reset index | First 7 days per station |

### Expected output

```
data/processed/krakow_multistation_CLEANED.csv
Shape: ~13,000-14,000 rows × 27 columns
Stations: 8
Missing PM2.5: 0
```

### Console output includes:

```
KRAKOW MULTI-STATION AIR QUALITY CLEANING
...
STEP 0: FILE DISCOVERY — Found 8 air-quality CSV file(s)
STEP 1: LOAD AND TAG STATIONS
  Loaded: Nowa Huta     | 2196 rows | PM2.5 missing: 521 (23.7%)
  ...
STEP 2: FILTER DATE RANGE — filtered to 2019-2024
STEP 5: EXCLUDE COVID PERIOD — removed 390 rows
...
CLEANING SUMMARY
Stations loaded: 8
Final rows: 13,597
Final columns: 27
```

### Validation checks

The script automatically runs 6 checks after cleaning:

```
PASS: No missing PM2.5 values
PASS: Date range correct (2019-2024)
PASS: Multiple stations present (8 stations)
PASS: No negative PM2.5 values
PASS: Sufficient sample size (13,597 rows)
PASS: Spatial variation in PM2.5 present
```

---

## Script 2: `spatial_features_pipeline.py`

### What it does

Extracts land use (Copernicus Urban Atlas) and building/road density (OpenStreetMap)
features at each of the 8 station locations, then merges with the cleaned AQ data.

| Step | Action | Output |
|---|---|---|
| 1 | Land use features from Urban Atlas at 4 buffer radii (0.5/1/2/5 km) | 53 columns per station |
| 2 | OSM building + road features at 3 radii (0.5/1/2 km) | 9 columns per station |
| 3 | Merge spatial features with AQ time series on `station_id` | Full ML dataset |

### Expected outputs

```
data/output/krakow_spatial_features.csv
  Shape: 8 rows × 53 columns (one row per station)

data/output/krakow_final_dataset.csv
  Shape: same rows as krakow_multistation_CLEANED.csv × (27 + 53) columns
  USE THIS FOR MODEL TRAINING
```

### Configuration options

In `spatial_features_pipeline.py`:

```python
# Set False to skip OSM (faster, works offline — land use features only)
FETCH_OSM = True

# Buffer radii
RADII_KM     = [0.5, 1.0, 2.0, 5.0]  # land use
OSM_RADII_KM = [0.5, 1.0, 2.0]       # OSM
```

If the Overpass API is blocked on your network:
```python
FETCH_OSM = False
```
This still produces land use features from Urban Atlas; OSM columns will be absent.

---

## Troubleshooting

### "FGB file not found"

```
ERROR: FGB file not found at: ...CLMS_UA_LCU...KRAKOW...fgb
```

**Fix:** Download the Urban Atlas FlatGeobuf file from the Copernicus portal
and place it in `session 3/` root. See `session 3/DATA SOURCES.md` for the exact URL.

### "No air-quality CSV files found"

```
ERROR: No air-quality CSV files found in this folder.
```

**Fix:** Make sure 8 station CSVs are in `session 3/data/raw/`. Files must have
`air-quality` in the name (AQICN download format).

### OSM fetch fails (SSL error or timeout)

```
Attempt 1 failed (SSL error). Retrying in 10s...
```

**Fix:** The script tries 3 Overpass servers automatically. If all fail, set
`FETCH_OSM = False` in `spatial_features_pipeline.py` and run from a different
network (home WiFi works; some university/corporate networks block Overpass).

### "No module named 'geopandas'"

```powershell
# If pip fails:
conda install -c conda-forge geopandas osmnx pyproj shapely
```

---

## Checking the outputs

```python
import pandas as pd

# Cleaned AQ data
aq = pd.read_csv("session 3/data/processed/krakow_multistation_CLEANED.csv")
print(aq.shape)                        # (~13,597, 27)
print(aq["station_id"].nunique())      # 8
print(aq["pm25"].isna().sum())         # 0

# Spatial features
sf = pd.read_csv("session 3/data/output/krakow_spatial_features.csv")
print(sf.shape)                        # (8, 53+)
print(sf["station_id"].tolist())       # 8 station IDs

# Final ML dataset
final = pd.read_csv("session 3/data/output/krakow_final_dataset.csv")
print(final.shape)                     # (~13,597, 80+)
print(final.columns.tolist())          # AQ cols + luse_* + osm_* cols
```

---

## Next steps for modeling (Session 4)

Once you have `krakow_final_dataset.csv`:

```python
# Time-based train/test split (NEVER random for time series!)
train = final[final["year"] <= 2023]
test  = final[final["year"] == 2024]

# Leave-one-station-out cross-validation
from sklearn.model_selection import LeaveOneGroupOut
logo = LeaveOneGroupOut()
groups = final["station_id"]
# ... (see Session 4 scaffold)
```

Target validation metric: **R² ≥ 0.40** (from `problem-brief-v2.md`).
