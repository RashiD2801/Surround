# 02 · Data Cleaning Notebook — Scaffold
# Krakow Air Quality & Urban Form — Session 3

> Reference scaffold for the Session 3 cleaning work.
>
> The actual cleaning was implemented in two scripts:
> - `session 3/scripts/clean_multistation.py` — AQICN 8-station cleaning
> - `session 3/scripts/spatial_features_pipeline.py` — Urban Atlas + OSM features
>
> The notebook `session 3/02-data-cleaning.ipynb` contains the exploratory
> version of this work.

---

## What this scaffold covers

This is the sequence of cleaning steps applied to the AQICN 8-station PM2.5
data in Session 3. Use it as a reference when extending or debugging the pipeline.

---

## Config block (mirrors `clean_multistation.py`)

```python
from pathlib import Path
import pandas as pd
import numpy as np

# Resolve paths relative to session 3 folder
HERE          = Path("session 3")  # adjust as needed
RAW_DIR       = HERE / "data" / "raw"
PROCESSED_DIR = HERE / "data" / "processed"
OUTPUT_DIR    = HERE / "data" / "output"
REPORTS_DIR   = HERE / "reports"

OUTPUT_FILE = PROCESSED_DIR / "krakow_multistation_CLEANED.csv"
REPORT_FILE = REPORTS_DIR / "multistation_cleaning_report.txt"

# Cleaning constants (from clean_multistation.py)
PROJECT_START_YEAR       = 2019
PROJECT_END_YEAR         = 2024
COVID_START              = "2020-03-15"
COVID_END                = "2020-05-31"
HIGH_MISSING_THRESHOLD   = 0.50   # drop columns with > 50% missing
EXTREME_THRESHOLD        = 200    # µg/m³ — flag but keep above this

# Station registry (station_id → display_name, lat, lon)
# Coordinates corrected for Aleja Krasińskiego and Ul. Dietla (WIOŚ portal)
STATIONS = {
    "nowa-huta":   ("nowa_huta",         "Nowa Huta",          50.0683, 20.0530),
    "kurdwan":     ("kurdwanow",          "Kurdwanow",          50.0076, 19.9742),
    "zloty":       ("zloty_rog",          "Zloty Rog",          50.0647, 19.9450),
    "telimeny":    ("telimeny",           "Ul. Telimeny",       50.0094, 19.9617),
    "wadow":       ("os_wadow",           "Os. Wadow",          50.0783, 19.8950),
    "piastow":     ("os_piastow",         "Os. Piastow",        50.0519, 19.8850),
    "dietla":      ("ul_dietla",          "Ul. Dietla",         50.0566, 19.9442),
    "aleja":       ("aleja_krasinskiego", "Aleja Krasinskiego", 50.0573, 19.9100),
}
```

---

## Step 0 — File discovery

```python
csv_files = sorted(RAW_DIR.glob("*air-quality*.csv"))
print(f"Found {len(csv_files)} station CSV files:")
for f in csv_files:
    print(f"  {f.name}")
# Expected: 8 files (one per station)
```

---

## Step 1 — Load + tag all stations

```python
all_frames = []
for fpath in csv_files:
    # Keyword match filename → station info
    station_info = detect_station(str(fpath))  # from clean_multistation.py
    if station_info is None:
        print(f"  WARNING: No match for {fpath.name}")
        continue

    station_id, station_name, lat, lon = station_info
    df = load_station_csv(str(fpath))
    df["station_id"]   = station_id
    df["station_name"] = station_name
    df["station_lat"]  = lat
    df["station_lon"]  = lon
    all_frames.append(df)

df = pd.concat(all_frames, ignore_index=True)
print(f"Combined shape: {df.shape}")
print(f"Stations: {df['station_id'].nunique()}")
# Expected: 8 stations
```

---

## Step 2 — Date range filter (2019-2024)

```python
before = len(df)
df["year"] = df["date"].dt.year
df = df[(df["year"] >= PROJECT_START_YEAR) & (df["year"] <= PROJECT_END_YEAR)].copy()
print(f"Date filter: {before:,} → {len(df):,} rows ({before - len(df):,} removed)")
```

**Why 2019-2024:** aligns with problem-brief-v2.md scope; 2019 is the first full
year after the coal heating ban (September 2019). Pre-2019 data represents a
different pollution regime.

---

## Step 3 — Remove duplicate (station, date) pairs

```python
before = len(df)
df = df.drop_duplicates(subset=["station_id", "date"]).copy()
print(f"Dedup: {before:,} → {len(df):,} rows ({before - len(df):,} removed)")
```

---

## Step 4 — Drop rows with missing PM2.5 (target variable)

```python
# Show per-station missing rate before dropping
missing_by_station = df.groupby("station_name")["pm25"].apply(
    lambda x: f"{x.isna().sum()} / {len(x)} ({x.isna().mean()*100:.1f}%)"
)
print("Missing PM2.5 per station:")
print(missing_by_station.to_string())

before = len(df)
df = df.dropna(subset=["pm25"]).copy()
print(f"Dropped missing PM2.5: {before:,} → {len(df):,} rows")

# Clip negatives
neg_count = (df["pm25"] < 0).sum()
if neg_count > 0:
    print(f"Clipping {neg_count} negative values to 0")
    df["pm25"] = df["pm25"].clip(lower=0)

assert (df["pm25"] >= 0).all(), "pm25 still has negative values"
```

**Why drop, not impute:** cannot impute the target variable. A model trained on
imputed PM2.5 values would be learning from invented data.

---

## Step 5 — Exclude COVID period (2020-03-15 – 2020-05-31)

```python
before = len(df)
covid_mask = (df["date"] >= COVID_START) & (df["date"] <= COVID_END)
df = df[~covid_mask].copy()
print(f"COVID exclusion: {before:,} → {len(df):,} rows ({before - len(df):,} removed)")
```

**Why exclude:** traffic dropped ~40%, PM2.5 dropped ~30% — not representative
of urban form effects under normal conditions.

---

## Step 6 — Drop high-missingness feature columns

```python
pollutant_cols = [c for c in ["pm10", "o3", "no2", "so2", "co"] if c in df.columns]
dropped = []
for col in pollutant_cols:
    pct_missing = df[col].isna().sum() / len(df)
    if pct_missing > HIGH_MISSING_THRESHOLD:
        df = df.drop(columns=[col])
        dropped.append(col)
        print(f"  DROPPED '{col}': {pct_missing*100:.1f}% missing")

print(f"Dropped columns: {dropped}")
```

---

## Step 7 — Impute remaining pollutants with per-station median

```python
remaining = [c for c in ["pm10", "o3", "no2", "so2", "co"] if c in df.columns]
for col in remaining:
    missing = df[col].isna().sum()
    if missing > 0:
        df[col] = df.groupby("station_id")[col].transform(
            lambda x: x.fillna(x.median())
        )
        # Fallback: global median for any station with all-NaN
        df[col] = df[col].fillna(df[col].median())
        print(f"  Imputed '{col}': {missing:,} values with per-station median")
```

**Why per-station:** each station has its own baseline (industrial stations have
higher NO2 than background stations). Global median would mask this variation.

---

## Step 8 — Add temporal features

```python
df = df.sort_values(["station_id", "date"]).reset_index(drop=True)

df["month"]       = df["date"].dt.month
df["day_of_year"] = df["date"].dt.dayofyear
df["weekday"]     = df["date"].dt.dayofweek
df["is_weekend"]  = (df["weekday"] >= 5).astype(int)

# Cyclical encoding (preserves periodicity: Dec and Jan are adjacent)
df["month_sin"] = np.sin(2 * np.pi * df["month"] / 12)
df["month_cos"] = np.cos(2 * np.pi * df["month"] / 12)
df["doy_sin"]   = np.sin(2 * np.pi * df["day_of_year"] / 365)
df["doy_cos"]   = np.cos(2 * np.pi * df["day_of_year"] / 365)

# Season dummies
season_map = {12:"winter",1:"winter",2:"winter",
              3:"spring",4:"spring",5:"spring",
              6:"summer",7:"summer",8:"summer",
              9:"autumn",10:"autumn",11:"autumn"}
df["season"] = df["month"].map(season_map)
df = pd.get_dummies(df, columns=["season"], prefix="season", dtype=int)

# Per-station lag features (never bleed across stations)
for lag in [1, 3, 7]:
    df[f"pm25_lag{lag}"] = df.groupby("station_id")["pm25"].shift(lag)
df["pm25_roll7d"] = df.groupby("station_id")["pm25"].transform(
    lambda x: x.shift(1).rolling(7).mean()
)

print("Added temporal features: month, day_of_year, weekday, is_weekend")
print("Added cyclical features: month_sin/cos, doy_sin/cos")
print("Added season dummies, PM2.5 lags (1/3/7d), rolling 7d mean")
```

---

## Step 9 — Final cleanup

```python
# Drop lag cold-start rows (pm25_lag7 is NaN for first 7 rows per station)
before = len(df)
df = df.dropna(subset=["pm25_lag7"]).copy()
print(f"Dropped cold-start rows: {before - len(df):,}")

# Drop raw date column (year and temporal features retained)
df = df.drop(columns=["date"])
df = df.reset_index(drop=True)

print(f"Final shape: {df.shape}")
```

---

## Validation checks (mirrors `validate()` in `clean_multistation.py`)

```python
# 1. No missing PM2.5
assert df["pm25"].isna().sum() == 0, "Missing PM2.5 values remain"

# 2. Date range
assert df["year"].min() >= PROJECT_START_YEAR
assert df["year"].max() <= PROJECT_END_YEAR

# 3. Multiple stations
assert df["station_id"].nunique() >= 4, "Too few stations for spatial modeling"

# 4. No negative PM2.5
assert (df["pm25"] >= 0).all(), "Negative PM2.5 remains"

# 5. Sufficient sample size
assert len(df) >= 1000, f"Sample too small: {len(df)}"

# 6. Spatial variation
station_means = df.groupby("station_id")["pm25"].mean()
assert station_means.std() > 1.0, "Very low spatial variation — check data"

print(f"ALL VALIDATION CHECKS PASSED")
print(f"Stations: {df['station_id'].nunique()}")
print(f"Rows per station:\n{df.groupby('station_name').size().to_string()}")
```

---

## Output

```python
df.to_csv(OUTPUT_FILE, index=False)
print(f"Saved: {OUTPUT_FILE}")
print(f"Shape: {df.shape}")
```

**Expected output:** `data/processed/krakow_multistation_CLEANED.csv`  
**Expected shape:** ~13,000-14,000 rows × 27 columns  
**Expected stations:** 8

---

## Next steps

After `krakow_multistation_CLEANED.csv` is produced:

1. Run `spatial_features_pipeline.py` to extract Urban Atlas + OSM features
2. Check `data/output/krakow_spatial_features.csv` has 8 rows (one per station)
3. Check `data/output/krakow_final_dataset.csv` — this is the ML-ready dataset
4. Proceed to Session 4: leave-one-station-out cross-validation, target R² ≥ 0.40
