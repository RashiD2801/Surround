# Session 3 Guide — Data Preparation (CRISP-DM Phase 3)
# Krakow Air Quality & Urban Form

> **The frame for Session 3:** cleaning is not janitor work. Every
> transformation is a design decision with downstream consequences. Document
> them as rigorously as you'd document a wall section.

---

## What was built in Session 3

| Artifact | Location | Status |
|---|---|---|
| `clean_multistation.py` | `session 3/scripts/` | ✅ Done |
| `spatial_features_pipeline.py` | `session 3/scripts/` | ✅ Done |
| `krakow_multistation_CLEANED.csv` | `session 3/data/processed/` | ✅ Done (not in repo — too large) |
| `krakow_spatial_features.csv` | `session 3/data/output/` | ✅ Done (committed to repo root) |
| `krakow_final_dataset.csv` | `session 3/data/output/` | ✅ Done (not in repo — too large) |
| `02-data-cleaning.ipynb` | `session 3/` | ✅ Done |
| `DATA SOURCES.md` | `session 3/` | ✅ Done |
| `docs/data-cleaning-log.md` | `docs/` | ✅ Done |
| `docs/pipeline-architecture-v1.md` | `docs/` | ✅ Done |

---

## How to reproduce Session 3 outputs from scratch

### Prerequisites

```powershell
pip install pandas numpy geopandas pyproj shapely osmnx
```

On Windows if geopandas fails:
```powershell
conda install -c conda-forge geopandas osmnx
```

### Step 1 — Get the raw data

Follow `session 3/DATA SOURCES.md`:

1. Download 8 station CSVs from AQICN (one per station) → place in `session 3/data/raw/`
2. Download Urban Atlas FlatGeobuf from Copernicus portal → place in `session 3/` root
   - File: `CLMS_UA_LCU_S2021_V025ha_PL003L2_KRAKOW_03035_V01_R00_20241025.fgb`

### Step 2 — Run the cleaning pipeline

```powershell
cd "session 3"

# Clean and combine the 8 station CSVs
python scripts/clean_multistation.py
# Output: data/processed/krakow_multistation_CLEANED.csv

# Extract spatial features + merge
python scripts/spatial_features_pipeline.py
# Output: data/output/krakow_spatial_features.csv
#         data/output/krakow_final_dataset.csv
```

**Total runtime:** ~5-10 minutes (longer if OSM is slow).

### Step 3 — Verify outputs

```python
import pandas as pd

aq = pd.read_csv("session 3/data/processed/krakow_multistation_CLEANED.csv")
print(f"AQ cleaned: {aq.shape}")
print(f"Stations: {aq['station_id'].nunique()}")  # Expected: 8
print(f"Missing PM2.5: {aq['pm25'].isna().sum()}")  # Expected: 0

spatial = pd.read_csv("session 3/data/output/krakow_spatial_features.csv")
print(f"Spatial features: {spatial.shape}")  # Expected: 8 rows × 53+ columns

final = pd.read_csv("session 3/data/output/krakow_final_dataset.csv")
print(f"Final ML dataset: {final.shape}")  # Expected: same rows as aq cleaned
```

---

## What Session 3 does NOT do

- ✗ Train any model (Phase 4 / Session 4)
- ✗ Compute model metrics or cross-validation (Phase 4 / Session 4)
- ✗ Compute Sentinel-2 NDVI (planned future session)
- ✗ Integrate ERA5-Land weather controls (planned future session)
- ✗ Rasterize to 100m city-wide grid (planned future session)
- ✗ Build the Streamlit dashboard (Phase 7 / Session 7)

---

## Reference documents (in `docs/`)

| Document | Purpose |
|---|---|
| `pipeline-architecture-v1.md` | Full pipeline diagram — implemented vs planned |
| `data-cleaning-log.md` | Every transform with justification (12 transforms total) |
| `02-data-cleaning-scaffold.md` | Step-by-step code scaffold for the cleaning pipeline |
| `clean-data-module.md` | Reference for `clean_multistation.py` functions |
| `reproducibility-checklist.md` | Checklist before committing |
| `function-design-checklist.md` | Standards for any new function added to scripts |
| `data-quality-audit.md` | Honest assessment of AQICN data quality and limitations |
| `data-source-inventory.md` | All 10 candidate datasets scored and verdicted |
| `data-to-decision-map.md` | Which data sources answer which sub-questions |
| `system-sketch-v0.md` | Original aspirational system sketch (Session 2) |
| `datasheets/aqicn-pm25.md` | AQICN dataset datasheet (updated for 8 stations) |
| `datasheets/copernicus-urban-atlas.md` | Urban Atlas datasheet (updated with Session 3 status) |
| `datasheets/sentinel2-imagery.md` | Sentinel-2 datasheet (not yet implemented) |

---

## The CRISP-DM phase 3 spine (applied to this project)

1. **Select** — which stations (8), which time window (2019–2024 excluding COVID).
   Every filter documented in `data-cleaning-log.md`.
2. **Clean** — clip negative PM2.5, drop missing targets, remove duplicates,
   drop high-missing columns, impute per-station median.
3. **Construct** — derive temporal features (cyclical encoding, season dummies,
   PM2.5 lags). Compute spatial features at station locations (Urban Atlas, OSM).
4. **Integrate** — join monthly air quality data with spatial features on `station_id`.
5. **Format** — final schema for `krakow_final_dataset.csv`. Column types documented.

---

## For every transform, be able to answer:

1. **What did this transform change?**
2. **Why this transform and not the alternative?**
3. **What downstream effect does it have?**
4. **What does it preserve from raw — is it reversible?**

If you can't answer all four, the transform is undocumented.
The cleaning log (`docs/data-cleaning-log.md`) is where you answer them.
