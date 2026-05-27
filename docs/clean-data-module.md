# `clean_multistation.py` — Module Reference
# Krakow Air Quality & Urban Form — AQICN 8-Station Cleaning Pipeline

> This is the reference document for `session 3/scripts/clean_multistation.py`.
>
> Run from the `session 3/` folder:
>     python scripts/clean_multistation.py
>
> Cleaning decisions are documented in `docs/data-cleaning-log.md`.

---

## What this script does

Reads 8 individual AQICN station CSV files from `data/raw/`, cleans and
combines them into one ML-ready dataset, and writes it to
`data/processed/krakow_multistation_CLEANED.csv`.

---

## Key constants (top of script)

```python
# Paths (resolved relative to script location)
HERE          = Path(__file__).parent.resolve()
RAW_DIR       = HERE.parent / "data" / "raw"
PROCESSED_DIR = HERE.parent / "data" / "processed"
OUTPUT_FILE   = PROCESSED_DIR / "krakow_multistation_CLEANED.csv"
REPORT_FILE   = REPORTS_DIR  / "multistation_cleaning_report.txt"

# Project scope (from problem-brief-v2.md)
PROJECT_START_YEAR = 2019
PROJECT_END_YEAR   = 2024

# COVID exclusion window
COVID_START = "2020-03-15"
COVID_END   = "2020-05-31"

# Column drop threshold
HIGH_MISSING_THRESHOLD = 0.50  # drop columns > 50% missing

# Extreme value flag (keep but log above this)
EXTREME_THRESHOLD = 200  # µg/m³

# Station registry — filename keyword → (station_id, display_name, lat, lon)
# Coordinates corrected for aleja and dietla (Martina, WIOŚ portal validation)
STATIONS = {
    "nowa-huta": ("nowa_huta",         "Nowa Huta",          50.0683, 20.0530),
    "kurdwan":   ("kurdwanow",          "Kurdwanow",          50.0076, 19.9742),
    "zloty":     ("zloty_rog",          "Zloty Rog",          50.0647, 19.9450),
    "złoty":    ("zloty_rog",          "Zloty Rog",          50.0647, 19.9450),
    "telimeny":  ("telimeny",           "Ul. Telimeny",       50.0094, 19.9617),
    "wadow":     ("os_wadow",           "Os. Wadow",          50.0783, 19.8950),
    "wadów":    ("os_wadow",           "Os. Wadow",          50.0783, 19.8950),
    "piastow":   ("os_piastow",         "Os. Piastow",        50.0519, 19.8850),
    "piastów":   ("os_piastow",         "Os. Piastow",        50.0519, 19.8850),
    "dietla":    ("ul_dietla",          "Ul. Dietla",         50.0566, 19.9442),
    "aleja":     ("aleja_krasinskiego", "Aleja Krasinskiego", 50.0573, 19.9100),
}
```

---

## Functions

### `detect_station(filepath: str) -> tuple | None`

Match a filename to a station entry using keyword lookup in `STATIONS`.

```python
station_info = detect_station("krakow-nowa-huta-air-quality.csv")
# Returns: ("nowa_huta", "Nowa Huta", 50.0683, 20.0530)
```

Returns `None` if no keyword matches. Unmatched files are skipped with a warning.

---

### `load_station_csv(filepath: str) -> pd.DataFrame`

Load a single station CSV. Handles:
- Leading/trailing whitespace in column names
- Date format `YYYY/M/D` (no zero-padding, from AQICN downloads)
- Numeric coercion for all pollutant columns

```python
df = load_station_csv("data/raw/nowa-huta, kraków, małopolska-air-quality.csv")
# Returns DataFrame with columns: date, pm25, pm10, o3, no2, so2, co
```

---

### `clean_multistation() -> tuple[pd.DataFrame, str]`

Full 10-step cleaning pipeline:

| Step | Action |
|---|---|
| 0 | Discover CSV files in `RAW_DIR` |
| 1 | Load + tag all 8 stations |
| 2 | Filter to 2019-2024 |
| 3 | Remove duplicate (station_id, date) pairs |
| 4 | Drop rows with missing PM2.5; clip negatives to 0 |
| 5 | Exclude COVID period (2020-03-15 – 2020-05-31) |
| 6 | Drop columns with >50% missing values |
| 7 | Impute remaining pollutants with per-station median |
| 8 | Check extreme PM2.5 values (flag, don't drop — real winter events) |
| 9 | Add temporal features (month, cyclical encoding, season dummies, lags) |
| 10 | Drop lag cold-start rows; drop raw date column; reset index |

Returns `(df_cleaned, report_text)`.

---

### `validate(df: pd.DataFrame) -> list[str]`

Run 6 automated validation checks on the cleaned dataset:

1. No missing PM2.5 values
2. Date range correct (2019-2024)
3. Multiple stations present (≥4)
4. No negative PM2.5 values
5. Sufficient sample size (≥1000 rows)
6. Spatial variation in PM2.5 (std > 1.0 across station means)

Returns a list of failed check messages (empty list = all passed).

---

## Output schema

`data/processed/krakow_multistation_CLEANED.csv`:

| Column | Type | Description |
|---|---|---|
| `station_id` | str | Station identifier slug (e.g. `nowa_huta`) |
| `station_name` | str | Display name |
| `station_lat` | float | Latitude (WGS84, corrected) |
| `station_lon` | float | Longitude (WGS84, corrected) |
| `year` | int | Year (2019-2024) |
| `pm25` | float | Daily PM2.5 µg/m³, ≥0, no missing |
| `pm10`, `o3`, `no2` | float | Co-pollutants (if not dropped) |
| `month`, `day_of_year`, `weekday` | int | Calendar features |
| `is_weekend` | int | 1/0 |
| `month_sin`, `month_cos` | float | Cyclical month encoding |
| `doy_sin`, `doy_cos` | float | Cyclical day-of-year encoding |
| `season_spring/summer/autumn/winter` | int | One-hot season dummies |
| `pm25_lag1`, `pm25_lag3`, `pm25_lag7` | float | Lagged PM2.5 per station |
| `pm25_roll7d` | float | 7-day rolling mean per station |

---

## How to run

```powershell
# From session 3/ folder
python scripts/clean_multistation.py

# Expected output:
# data/processed/krakow_multistation_CLEANED.csv
# reports/multistation_cleaning_report.txt
```

After cleaning, run the spatial features pipeline:

```powershell
python scripts/spatial_features_pipeline.py

# Expected outputs:
# data/output/krakow_spatial_features.csv   (8 rows × 53 columns)
# data/output/krakow_final_dataset.csv      (ML-ready merged dataset)
```

---

## Related files

| File | Role |
|---|---|
| `session 3/scripts/clean_multistation.py` | The actual implementation |
| `session 3/scripts/spatial_features_pipeline.py` | Feature extraction (Urban Atlas + OSM) |
| `docs/data-cleaning-log.md` | Every transform justified |
| `docs/pipeline-architecture-v1.md` | Full pipeline diagram |
| `session 3/DATA SOURCES.md` | Where to download raw data |
