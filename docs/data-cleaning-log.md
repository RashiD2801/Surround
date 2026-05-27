# Data Cleaning Log — Krakow Air Quality & Urban Form

> Every transformation in the cleaning pipeline gets one entry in this log.
> Filled in **as each decision was made**, not at the end.
>
> **Why this exists:** in Session 4 we'll write a model card. The model
> card cites this log. In Session 6 we'll build a failure gallery. The
> failure gallery cites this log.

---

## Datasets cleaned in Session 3

| Dataset | Script | Input | Output |
|---|---|---|---|
| AQICN 8-station CSVs | `session 3/scripts/clean_multistation.py` | 8 individual station CSVs in `data/raw/` | `data/processed/krakow_multistation_CLEANED.csv` |
| Urban Atlas + OSM spatial features | `session 3/scripts/spatial_features_pipeline.py` | Urban Atlas `.fgb` + OSM (via osmnx) | `data/output/krakow_spatial_features.csv` + `data/output/krakow_final_dataset.csv` |

**Team:** Rim, Martina, Rashi, Bhavana  
**Last updated:** 2026-05-26

---

## Pipeline A: `clean_multistation.py` — AQICN 8-station cleaning

### Summary

- **Raw input:** 8 individual station CSV files (one per station, downloaded from AQICN station pages)
- **Output:** `data/processed/krakow_multistation_CLEANED.csv` — daily rows per station, 2019-2024
- **Stations:** Nowa Huta, Kurdwanów, Złoty Róg, Ul. Telimeny, Os. Wadów, Os. Piastów, Ul. Dietla, Aleja Krasińskiego
- **Retention:** ~81% of rows retained through cleaning steps
- **Columns added:** year, month, day_of_year, weekday, is_weekend, month_sin/cos, doy_sin/cos, season dummies, pm25_lag1/3/7, pm25_roll7d, station_id, station_name, station_lat, station_lon

---

> **Transform 1: `load_station_csv` / file discovery**
> - **What it changed:** Loaded 8 individual station CSV files from `data/raw/`. Each file was matched to a known station via keyword lookup in the filename (e.g. "nowa-huta" → nowa_huta station). Added station metadata columns (`station_id`, `station_name`, `station_lat`, `station_lon`) to each loaded dataframe. Parsed date column from `YYYY/M/D` format (no zero-padding). Coerced all pollutant columns to numeric.
> - **Why this and not the alternative:** (a) Single combined CSV — rejected: raw downloads from AQICN come as one file per station; restructuring before cleaning adds a manual step. (b) Glob all CSVs and detect station from filename — chosen: robust to filename variation (handles both Polish diacritics and ASCII versions via keyword matching). (c) Manual rename — rejected: error-prone, not reproducible.
> - **Downstream effect:** All 8 stations tagged with station_id before any cleaning; allows per-station operations (lag features, median imputation, etc.) to be applied correctly in subsequent steps.
> - **Reversibility:** Yes — raw CSV files are preserved in `data/raw/`.
> - **Assertion:** Script prints each loaded station with row count and PM2.5 missing %; any unmatched file is flagged as a warning.

---

> **Transform 2: `filter_date_range` — project scope 2019-2024**
> - **What it changed:** Removed all rows with dates outside 2019-2024 (inclusive). Pre-2019 data from some stations predates the coal heating ban (September 2019) and would represent a different pollution regime.
> - **Why this and not the alternative:** (a) Keep all years and add year as a feature — rejected: pre-2019 data comes from a different coal-heavy regime; mixing regimes confounds the urban-form signal we're trying to extract. (b) 2019-2024 filter — chosen: aligns with `problem-brief-v2.md` scope and covers post-coal-ban conditions.
> - **Downstream effect:** Model trained on 2019-2024 represents Krakow after the coal ban but before the Low Emission Zone (Jan 2024). Won't generalise to other Polish cities still burning coal.
> - **Reversibility:** Yes — raw CSVs retain all years.
> - **Assertion:** Script prints before/after row counts and % removed.

---

> **Transform 3: `remove_duplicates`**
> - **What it changed:** Removed duplicate `(station_id, date)` pairs. Duplicates can appear when AQICN downloads overlap at the edges (e.g. the same day downloaded twice during different API sessions).
> - **Why this and not the alternative:** Keep first occurrence — chosen (pandas default). Any duplicate pair would bias the monthly mean by double-counting.
> - **Downstream effect:** Negligible — duplicates were rare.
> - **Reversibility:** Yes — raw CSVs are unchanged.

---

> **Transform 4: `handle_target_variable` — drop missing PM2.5, clip negatives**
> - **What it changed:** (a) Dropped all rows where `pm25` is NaN — cannot train without the target variable. (b) Found and clipped negative PM2.5 values to 0. Negative values are physically impossible; they result from sensor calibration drift in extreme cold (confirmed at Aleja Krasińskiego, Jan 2023, temperature −18°C). Preserved originals: `pm25_raw` would be the pattern to follow, but here negatives were clipped directly.
> - **Why this and not the alternative:** (a) Impute missing PM2.5 — rejected: the target variable cannot be imputed; doing so would teach the model an invented value. (b) Drop rows with missing PM2.5 — chosen: honest and necessary. (c) Clip negatives to 0 — chosen: PM2.5 concentration is non-negative by physical definition; 0 is the honest lower bound.
> - **Downstream effect:** ~25-30% of rows had missing PM2.5 (sensor gaps, calibration, power cuts). These are dropped. Negative-clipped rows (5 instances) are retained with corrected value.
> - **Reversibility:** Row drops not reversible; negative clipping can be reversed from raw CSVs.
> - **Assertion:** Script logs missing PM2.5 % per station before dropping; final dataset has 0 missing PM2.5.

---

> **Transform 5: `exclude_covid_period` — Mar 15 – May 31 2020**
> - **What it changed:** Removed all rows for all 8 stations during the COVID lockdown period. During this period, traffic dropped ~40% and PM2.5 dropped ~30% below typical seasonal levels — not representative of normal urban form effects.
> - **Why this and not the alternative:** (a) Keep COVID rows but add a flag column — rejected: a flagged row still enters the training data if we forget to filter during model training. (b) Keep COVID rows and include them as a "low-traffic" scenario — rejected: our brief models *normal* urban form effects; COVID traffic suppression is a confounding event outside the study design. (c) Drop the COVID window entirely — chosen: clean exclusion, documented here and in model card.
> - **Downstream effect:** Model trained on 2019-2024 (minus COVID) represents "post-coal-ban, COVID-excluded" Krakow.
> - **Reversibility:** Yes — raw CSVs retain COVID rows.
> - **Assertion:** Script logs number of rows removed and date range.

---

> **Transform 6: `drop_high_missing_columns`**
> - **What it changed:** Dropped any pollutant column (PM10, O3, NO2, SO2, CO) where >50% of values are missing across the combined dataset. Applied threshold `HIGH_MISSING_THRESHOLD = 0.50` as defined in `clean_multistation.py` constants.
> - **Why this and not the alternative:** (a) Impute all missing columns — rejected: if >50% is missing, the imputed values dominate and add more noise than signal. (b) Drop high-missing columns — chosen: consistent with standard practice; the remaining columns are imputed per station median in the next step.
> - **Downstream effect:** Some pollutant feature columns are dropped. PM2.5 (the target) is never dropped — it was handled separately in Transform 4.
> - **Reversibility:** Yes — raw CSVs have all columns.

---

> **Transform 7: `impute_remaining_pollutants` — per-station median**
> - **What it changed:** For remaining pollutant columns with <50% missing, filled NaN values with the per-station median (not global median). If a station had all-NaN for a column, fell back to global median.
> - **Why this and not the alternative:** (a) Global median — rejected: each station has its own baseline (industrial stations have higher NO2 than background stations); global median would mask this. (b) Per-station median — chosen: each station's gaps are filled with that station's typical values. (c) Forward-fill — rejected: assumes temporal continuity that isn't guaranteed with our sparse data.
> - **Downstream effect:** Remaining pollutant columns have 0 missing values. The per-station imputation preserves inter-station variation.
> - **Reversibility:** Not at row level — raw CSVs show original missing values.

---

> **Transform 8: `add_temporal_features`**
> - **What it changed:** Added the following columns derived from the date:
>   - `month`, `day_of_year`, `weekday`, `is_weekend`
>   - `month_sin`, `month_cos`, `doy_sin`, `doy_cos` (cyclical encoding)
>   - `season_spring`, `season_summer`, `season_autumn`, `season_winter` (one-hot dummies)
>   - `pm25_lag1`, `pm25_lag3`, `pm25_lag7` (lagged PM2.5 per station)
>   - `pm25_roll7d` (7-day rolling mean per station)
> - **Why this and not the alternative:** (a) Raw month/weekday as integers — rejected: month 12 and month 1 are far apart numerically but adjacent temporally; cyclical encoding preserves this. (b) Cyclical encoding — chosen: standard for periodic time features in ML. (c) Lag features per station — critical: lags computed across station boundaries would leak information between stations. The `groupby("station_id")` ensures shifts happen only within each station's time series.
> - **Downstream effect:** Temporal features allow the model to control for seasonal variation in PM2.5 (winter heating, summer background). Lag features let the model account for autocorrelation.
> - **Reversibility:** Yes — derived from `date` which is retained.

---

> **Transform 9: `final_cleanup` — drop lag cold-start rows**
> - **What it changed:** Dropped rows where `pm25_lag7` is NaN (the first 7 days for each station have no valid 7-day lag). Dropped the raw `date` column (year and temporal features retained). Reset index.
> - **Why this and not the alternative:** (a) Keep cold-start rows with NaN lags — rejected: NaN features during model training require special handling; dropping is cleaner. (b) Fill cold-start lags with station median — rejected: lags are temporal features; their value depends on the actual historical sequence.
> - **Downstream effect:** First ~7 days per station are removed (minor data loss). The final dataset has no missing values in any feature column.
> - **Reversibility:** Yes — raw CSVs are unchanged.
> - **Assertion:** Final `validate()` function in script checks: no missing PM2.5, correct date range, ≥4 stations, no negative PM2.5, ≥1000 rows, spatial variation in PM2.5 across stations.

---

## Pipeline B: `spatial_features_pipeline.py` — Urban Atlas + OSM features

### Summary

- **Raw input:** `CLMS_UA_LCU_S2021_V025ha_PL003L2_KRAKOW_03035_V01_R00_20241025.fgb` + OSM via overpass API
- **Output:** `data/output/krakow_spatial_features.csv` (8 rows × 53 columns) and `data/output/krakow_final_dataset.csv`
- **Buffer radii:** Land use at 0.5, 1.0, 2.0, 5.0 km; OSM at 0.5, 1.0, 2.0 km

---

> **Transform 10: `compute_landuse_features_for_station` — Urban Atlas**
> - **What it changed:** For each of the 8 stations, loaded the Urban Atlas FlatGeobuf clipped to a bounding box around the station (avoids loading the full 150 MB file). Computed land use percentage features at 4 radii (0.5, 1.0, 2.0, 5.0 km): `green_pct`, `urban_pct`, `seal_density`, and individual category percentages (urban_continuous, urban_discontinuous, urban_green, forest_natural, etc.).
> - **Why this and not the alternative:** (a) Single radius — rejected: land use at different spatial scales captures different mechanisms (local street-level vs neighbourhood-scale effects). (b) Rasterize to 100m grid — planned for future session; station-level features are sufficient for initial model training.
> - **Downstream effect:** 53 land use feature columns per station. These are static (land use doesn't change daily) and are broadcast to all time rows for each station during the merge step.
> - **Reversibility:** Yes — FGB file is unchanged; features can be recomputed from it.
> - **Assertion:** Script prints `green_pct` and `urban_pct` summary per station for spot-checking.

---

> **Transform 11: `compute_osm_features_for_station` — building and road density**
> - **What it changed:** Fetched building footprints and road network from OpenStreetMap via `osmnx` for each of the 8 stations at 3 radii (0.5, 1.0, 2.0 km). Computed: building coverage (footprint area / circle area), building count per km², road density (km of road per km²).
> - **Why this and not the alternative:** (a) Urban Atlas for buildings — rejected: Urban Atlas gives land cover class (residential, industrial) but not precise building footprint geometry or counts. OSM gives exact building polygons. (b) OSM via direct Overpass API query — chosen via osmnx library which handles retries, server selection, and geometry processing.
> - **Downstream effect:** 9 OSM feature columns per station (3 metrics × 3 radii). Combined with land use features in `krakow_spatial_features.csv`.
> - **Reversibility:** Yes — OSM features can be re-fetched. Note: OSM data changes over time; features represent the state at time of fetching.
> - **Assertion:** Script prints building count and road density per station/radius for spot-checking.

---

> **Transform 12: `merge_with_air_quality` — broadcast spatial to temporal**
> - **What it changed:** Merged the spatial features table (8 rows, one per station) with the cleaned air quality time series (many rows, daily) on `station_id`. Since spatial features are STATIC (land use doesn't change day-to-day), each station's spatial row is broadcast to all its time rows via a left join.
> - **Why this and not the alternative:** (a) Inner join — rejected: would drop any AQ rows for stations without spatial features. (b) Left join — chosen: keeps all AQ time rows; any station missing spatial features will have NaN in those columns (detectable and auditable).
> - **Downstream effect:** `krakow_final_dataset.csv` has one row per (station, day) with both temporal features and static spatial features. This is the ML-ready training dataset.
> - **Reversibility:** Yes — both input files are preserved.
> - **Assertion:** Script checks that merged row count equals AQ row count, and prints how many rows have spatial features.

---

## What we did NOT clean — and why

| Issue | Why we left it | What downstream needs to know |
|---|---|---|
| Zlatý Róg 20-30% systematic low readings | Cannot reliably correct without a calibrated correction factor. Flagged in `data-quality-audit.md`. | Exclude from lead fold of leave-one-station-out validation. Do not benchmark model performance using Złoty Róg as the sole test station. |
| ~25-30% overall daily missingness (after dropping NaN PM2.5) | Gaps are seasonal/random; handled by dropping rows with missing target. | Model trained on available days only. Seasonal gaps (more in winter) may introduce slight bias. |
| Nowa Huta extreme spike, Feb 2 2024 (287 µg/m³) | Verified as a real pollution episode (factory incident). Not sensor error. | Industrial zone extreme events are in the training data. Model card must note that predictions near industrial point sources have higher uncertainty. |
| Building heights missing from OSM | OSM doesn't have reliable height data for Krakow. | Street-canyon effect cannot be modelled. Limits prediction accuracy in areas with large building height variation. |
| Sentinel-2 NDVI not yet computed | Not implemented in Session 3. Planned for future session. | NDVI (actual vegetation signal) is not a feature in the current model. Urban Atlas land use categories are used as greenness proxy. |
| ERA5-Land weather controls not integrated | Not implemented in Session 3. Planned for future session. | Temporal weather deconfounding (temperature inversion, wind) not yet in dataset. |

---

## Sign-off

Pipeline A (`clean_multistation.py`):
- [x] Script runs without errors from `session 3/` folder
- [x] Output `krakow_multistation_CLEANED.csv` has 0 missing PM2.5
- [x] All 8 stations present
- [x] COVID period excluded
- [x] Temporal features and lag features added

Pipeline B (`spatial_features_pipeline.py`):
- [x] Output `krakow_spatial_features.csv` has 8 rows (one per station)
- [x] Land use features computed at 4 radii
- [x] OSM building and road features computed at 3 radii
- [x] Final merged dataset `krakow_final_dataset.csv` produced

Still to complete (future sessions):
- [ ] Sentinel-2 NDVI feature extraction
- [ ] ERA5-Land weather controls integration
- [ ] Rasterize Urban Atlas to 100m city-wide grid
