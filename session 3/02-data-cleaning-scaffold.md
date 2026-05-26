# 02 · Data Cleaning Notebook — Scaffold
# Krakow Air Quality & Urban Form — AQICN PM2.5 Cleaning

> Copy each cell into a new Jupyter notebook in your repo at
> `notebooks/02-data-cleaning.ipynb`.
>
> Your final notebook must be runnable end-to-end from a clean kernel.
> The cleaning logic you settle on here gets **promoted** into
> `src/clean_data.py` once it's stable.

---

## Cell 1 — Markdown: title & purpose

```markdown
# Data Cleaning — AQICN Krakow PM2.5

**Purpose:** Apply the design decisions from Session 2's data-quality-audit
to produce a clean, reproducible monthly PM2.5 dataset ready for Phase 4 (modeling).

**Input:** `data/raw/aqicn/krakow_pm25_2019_2024.csv`
**Output:** `data/processed/aqicn_monthly.csv`
**Cleaning log:** `docs/data-cleaning-log.md` (every transform justified)

This notebook is the **exploratory** layer. The stable logic gets promoted
to `src/clean_data.py`.

Key issues identified in Session 2 data-quality-audit:
- 5 negative PM2.5 values (physically impossible — sensor drift in extreme cold)
- Kurdwanów flatline: 36 hours stuck at 38.0 µg/m³ (Dec 15-16 2022)
- COVID lockdown period (Mar 15 – May 31 2020): anomalously low traffic, not representative
- 2 station coordinates off by ~100m (manual entry error in AQICN database)
- ~25-30% hourly gaps across all stations — seasonal pattern (worse in winter)
- Złoty Róg station reads 20-30% low due to sheltered placement in trees
```

## Cell 2 — Imports & deterministic config

```python
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

RAW_PATH = Path("../data/raw/aqicn/krakow_pm25_2019_2024.csv")
OUT_PATH = Path("../data/processed/aqicn_monthly.csv")
RANDOM_SEED = 42

OUT_PATH.parent.mkdir(parents=True, exist_ok=True)

# Cleaning constants
STUDY_START = "2019-01-01"
STUDY_END   = "2024-12-31"
COVID_EXCLUDE_START = "2020-03-15"
COVID_EXCLUDE_END   = "2020-05-31"
PM25_VALID_MAX      = 500.0   # µg/m³ — WHO emergency ceiling
MIN_MONTHLY_COMPLETENESS = 0.75  # drop station-months with <75% hourly coverage
FLATLINE_WINDOW_HOURS    = 24    # consecutive identical hours = stuck sensor
FLATLINE_TOLERANCE       = 0.1   # µg/m³ std dev threshold for flatline detection

# Station coordinate corrections (AQICN API → correct from WIOŚ portal)
COORD_CORRECTIONS = {
    "aleja_krasinskiego": {"lat": 50.0572, "lon": 19.9216},
    "ul_dietla":          {"lat": 50.0552, "lon": 19.9423},
}

pd.set_option("display.max_columns", 50)
pd.set_option("display.precision", 4)
np.random.seed(RANDOM_SEED)
```

## Cell 3 — Load raw + initial shape check

```python
df_raw = pd.read_csv(RAW_PATH)
print(f"Raw shape: {df_raw.shape}")
print(f"Columns: {list(df_raw.columns)}")
df = df_raw.copy()  # never mutate raw
df.head()
```

> **Discipline:** never mutate `df_raw`. Always work on `df`. Lets you
> sanity-check at any point with `df_raw.head()` against `df.head()`.

```python
# Quick audit: expected ~440k rows (10 stations × 5 years × ~8760 hours/year)
print(f"Stations: {df['station_id'].nunique()}")
print(df['station_id'].value_counts())
print(f"\nDate range raw: {df['timestamp'].min()} to {df['timestamp'].max()}")
print(f"\nPM2.5 basic stats:\n{df['pm25'].describe()}")
```

---

## Task 1 — Select

### Cell 4 — Markdown: selection plan

```markdown
## Task 1: Select

Decide which rows we keep. Every filter has a reason. Every reason goes
in `data-cleaning-log.md`.

- **Stations kept:** All 10 Krakow AQICN stations (Aleja Krasińskiego,
  ul. Dietla, Kurdwanów, Nowa Huta, Złoty Róg, + 5 others)
- **Time window:** 2019-01-01 to 2024-12-31 (6 years)
- **Excluded window:** 2020-03-15 to 2020-05-31 (COVID lockdown — anomalous
  traffic, PM2.5 ~30% below normal, not representative of urban form effects)
- **Columns kept:** station_id, timestamp, pm25, lat, lon, station_type
```

### Cell 5 — Apply selection

```python
COLS_KEEP = ["station_id", "timestamp", "pm25", "lat", "lon", "station_type"]
df = df[COLS_KEEP].copy()

# Time window
before = len(df)
df = df[df["timestamp"].between(STUDY_START, STUDY_END)]
print(f"Time-window filter: {before:,} → {len(df):,} rows")

# Exclude COVID lockdown period
before = len(df)
covid_mask = df["timestamp"].between(COVID_EXCLUDE_START, COVID_EXCLUDE_END)
df = df[~covid_mask]
print(f"COVID exclusion ({COVID_EXCLUDE_START} – {COVID_EXCLUDE_END}): "
      f"{before:,} → {len(df):,} rows ({before - len(df):,} removed)")

print(f"After selection: {df.shape}")
```

---

## Task 2 — Clean

### Cell 6 — Markdown: cleaning plan

```markdown
## Task 2: Clean

For each issue surfaced by `data-quality-audit.md`:

| Issue | Strategy | Reversibility |
|---|---|---|
| Negative PM2.5 (5 rows) | Clip to 0, flag `pm25_negative_flag` | Yes — `pm25_raw` preserved |
| Flatline sensor readings (36h, Kurdwanów Dec 2022) | Drop the block, flag `has_flatline_drop` per station | No — bad data, no recovery |
| UTC/CET timestamp mix | Coerce all to UTC | Yes — `timestamp_raw` preserved |
| 2 station coordinates wrong | Correct in metadata join | Yes — documented in corrections dict |
| ~25-30% hourly gaps | Drop station-months with <75% completeness at aggregation step | Documented — not reversible at row level |
```

### Cell 7 — Timestamp parsing

```python
df["timestamp_raw"] = df["timestamp"]
df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True, errors="coerce")

n_failed = df["timestamp"].isna().sum()
print(f"Datetime parse failures: {n_failed:,}")
assert n_failed < len(df) * 0.01, f"Too many parse failures: {n_failed}"
```

> **Why `errors='coerce'`:** turns un-parseable strings into NaT, lets us
> count and decide. Don't use `errors='ignore'` — it silently keeps strings.

### Cell 8 — Type coercion + negative clipping

```python
df["pm25"] = pd.to_numeric(df["pm25"], errors="coerce")

# Flag before clipping
df["pm25_negative_flag"] = df["pm25"] < 0
n_neg = df["pm25_negative_flag"].sum()
print(f"Negative PM2.5 values found: {n_neg}")
print(df[df["pm25_negative_flag"]][["station_id", "timestamp", "pm25"]])

df["pm25_raw"] = df["pm25"]
df["pm25"] = df["pm25"].clip(lower=0.0, upper=PM25_VALID_MAX)

assert (df["pm25"] >= 0).all(), "pm25 has values below 0 after clipping"
assert (df["pm25"] <= PM25_VALID_MAX).all() | df["pm25"].isna(), \
    f"pm25 above {PM25_VALID_MAX} µg/m³ — check raw data"
```

### Cell 9 — Flatline detection and removal

```python
# Flatline: rolling std dev < tolerance over a window ≥ FLATLINE_WINDOW_HOURS
df = df.sort_values(["station_id", "timestamp"]).reset_index(drop=True)

def flag_flatlines(group, window=FLATLINE_WINDOW_HOURS, tol=FLATLINE_TOLERANCE):
    rolling_std = group["pm25"].rolling(window, min_periods=window).std()
    return rolling_std < tol

flatline_mask = df.groupby("station_id", group_keys=False).apply(flag_flatlines)
df["pm25_flatline_flag"] = flatline_mask.values

n_flatline = df["pm25_flatline_flag"].sum()
print(f"Flatline rows flagged: {n_flatline:,}")
print("Flatline periods by station:")
print(df[df["pm25_flatline_flag"]].groupby("station_id")["timestamp"].agg(["min", "max", "count"]))

before = len(df)
df = df[~df["pm25_flatline_flag"]].copy()
print(f"After dropping flatlines: {before:,} → {len(df):,} rows")
```

> **Why drop flatlines entirely, not impute:** a stuck sensor isn't missing
> data — it's wrong data that looks right. Imputing over it with the median
> would just average in a known instrument failure. Dropping is the only
> honest option here.

### Cell 10 — Station coordinate correction

```python
# Apply corrections from WIOŚ portal validation (Martina's work)
station_meta = pd.DataFrame([
    {"station_id": "aleja_krasinskiego", "lat_correct": 50.0572, "lon_correct": 19.9216},
    {"station_id": "ul_dietla",          "lat_correct": 50.0552, "lon_correct": 19.9423},
])

df = df.merge(station_meta, on="station_id", how="left")
df["lat_original"] = df["lat"]
df["lon_original"] = df["lon"]

corrected_mask = df["lat_correct"].notna()
df.loc[corrected_mask, "lat"] = df.loc[corrected_mask, "lat_correct"]
df.loc[corrected_mask, "lon"] = df.loc[corrected_mask, "lon_correct"]
df = df.drop(columns=["lat_correct", "lon_correct"])

n_corrected = corrected_mask.sum()
print(f"Coordinate-corrected rows: {n_corrected:,} (for 2 stations)")

assert df["lat"].between(-90, 90).all(), "Latitude out of range"
assert df["lon"].between(-180, 180).all(), "Longitude out of range"
```

### Cell 11 — Missing values summary before aggregation

```python
miss = df.isna().mean().sort_values(ascending=False)
print("Missing fractions after cleaning:")
print(miss[miss > 0])

# Drop rows with no PM2.5 reading (can't impute at hourly level — too noisy)
before = len(df)
df = df.dropna(subset=["timestamp", "pm25"])
print(f"Dropped {before - len(df):,} rows with null timestamp or PM2.5")
```

---

## Task 3 — Construct

### Cell 12 — Monthly aggregation with completeness guard

```python
df["year_month"] = df["timestamp"].dt.to_period("M").astype(str)

# Count expected hourly readings per station-month (≈720–744 per month)
df["hours_in_month"] = df["timestamp"].dt.days_in_month * 24

monthly = df.groupby(["station_id", "year_month"]).agg(
    pm25_mean=("pm25", "mean"),
    pm25_min=("pm25", "min"),
    pm25_max=("pm25", "max"),
    pm25_std=("pm25", "std"),
    pm25_count=("pm25", "count"),
    hours_in_month=("hours_in_month", "first"),
    lat=("lat", "first"),
    lon=("lon", "first"),
    station_type=("station_type", "first"),
    n_negative_clipped=("pm25_negative_flag", "sum"),
).reset_index()

monthly["pm25_completeness"] = monthly["pm25_count"] / monthly["hours_in_month"]

# Drop station-months with <75% completeness
before = len(monthly)
monthly = monthly[monthly["pm25_completeness"] >= MIN_MONTHLY_COMPLETENESS].copy()
print(f"Completeness filter (≥{MIN_MONTHLY_COMPLETENESS:.0%}): "
      f"{before:,} → {len(monthly):,} station-months")
print(f"Dropped {before - len(monthly):,} low-completeness station-months")

print(f"\nFinal monthly dataset: {monthly.shape}")
print(monthly.head())
```

> **Why monthly, not hourly:** our model predicts PM2.5 from static urban
> form features (NDVI, road density). These don't change hour-to-hour.
> Hour-to-hour variation is ~90% driven by weather (temperature inversions,
> wind), not urban form. Monthly averages smooth the weather noise and
> let urban form signal dominate.

### Cell 13 — Flag Złoty Róg bias

```python
# Złoty Róg reads 20-30% lower than neighbouring stations under identical
# conditions — confirmed by Rashi's anomaly analysis (sheltered by trees/buildings)
monthly["station_bias_flag"] = monthly["station_id"].map(
    lambda x: "sheltered_placement" if x == "zloty_rog" else None
)

n_flagged = (monthly["station_bias_flag"] == "sheltered_placement").sum()
print(f"Złoty Róg station-months flagged as sheltered: {n_flagged:,}")
```

---

## Task 4 — Integrate (join with spatial features)

### Cell 14 — Markdown: integration plan

```markdown
## Task 4: Integrate

We join monthly PM2.5 station data with pre-computed spatial features
extracted at each station's location.

- **Source 1:** `data/processed/aqicn_monthly.csv` (this notebook's output)
- **Source 2:** `data/processed/features_at_stations.csv` (from `notebooks/03-feature-extraction.ipynb`)
  - NDVI (Sentinel-2 summer composite), NDBI, road_density_500m,
    building_density, pct_green_500m, mean_temp_monthly, blh_monthly

- **Key:** station_id + year_month (many-to-one: many months per station,
  features are static or monthly averages)
- **Join type:** left join (keep all cleaned PM2.5 records)
- **Assertion:** row count must not change after join
```

### Cell 15 — Join (run after feature extraction notebook)

```python
# Load spatial features (created in notebooks/03-feature-extraction.ipynb)
features_path = Path("../data/processed/features_at_stations.csv")

if features_path.exists():
    df_features = pd.read_csv(features_path)
    
    before = len(monthly)
    df_model = monthly.merge(
        df_features,
        on=["station_id", "year_month"],
        how="left",
        validate="m:1"
    )
    print(f"After feature join: {before:,} → {len(df_model):,} rows")
    assert len(df_model) == before, \
        f"Cardinality changed unexpectedly — check the join (before: {before}, after: {len(df_model)})"
    
    n_missing_features = df_model["ndvi"].isna().sum()
    print(f"Station-months missing NDVI (cloud/gap): {n_missing_features:,}")
else:
    print("Feature file not yet created — run notebooks/03-feature-extraction.ipynb first")
    df_model = monthly.copy()
```

> **The cartesian-join trap:** ALWAYS print row count before and after a
> join. ALWAYS use `validate=` to assert the relationship type.
> A silent 1:m join is the most common silent bug in data prep.

---

## Task 5 — Format

### Cell 16 — Final schema check

```python
FINAL_COLS = [
    "station_id", "year_month", "lat", "lon", "station_type",
    "pm25_mean", "pm25_min", "pm25_max", "pm25_std",
    "pm25_count", "pm25_completeness",
    "n_negative_clipped", "station_bias_flag",
]

assert set(FINAL_COLS).issubset(monthly.columns), \
    f"Missing columns: {set(FINAL_COLS) - set(monthly.columns)}"

df_out = monthly[FINAL_COLS].copy()
print(f"Final schema: {df_out.shape}")
print(df_out.dtypes)
```

### Cell 17 — Write output

```python
df_out.to_csv(OUT_PATH, index=False)
print(f"Wrote {OUT_PATH} ({OUT_PATH.stat().st_size / 1024:.1f} KB)")
print(f"Station-months: {len(df_out):,}")
print(f"Stations: {df_out['station_id'].nunique()}")
print(f"Date range: {df_out['year_month'].min()} to {df_out['year_month'].max()}")
```

> **Why CSV here, not parquet:** this is a small file (~600 rows). CSV is
> fine for tabular data at this scale. The large raster files
> (`features_100m.tif`, `predictions_100m.tif`) are written as GeoTIFF.

---

## Task 6 — Verify (the back-half discipline)

### Cell 18 — Visualization 1: raw vs cleaned distribution

```python
fig, ax = plt.subplots(figsize=(10, 5))
ax.hist(df_raw["pm25"].dropna().clip(0, 200), bins=60, alpha=0.5, label="raw hourly")
ax.hist(df_out["pm25_mean"].dropna(), bins=30, alpha=0.7, label="cleaned monthly means")
ax.axvline(15, color="green", linestyle="--", label="WHO guideline (15 µg/m³)")
ax.axvline(25, color="orange", linestyle="--", label="EU annual limit (25 µg/m³)")
ax.set_xlabel("PM2.5 (µg/m³)")
ax.set_ylabel("count")
ax.legend()
ax.set_title("Raw hourly vs cleaned monthly means — Krakow PM2.5")
plt.tight_layout()
plt.show()
```

### Cell 19 — Visualization 2: data completeness over time

```python
completeness_pivot = monthly.pivot_table(
    index="year_month", columns="station_id", values="pm25_completeness"
)
fig, ax = plt.subplots(figsize=(14, 5))
completeness_pivot.plot(ax=ax, marker=".", linewidth=0.8)
ax.axhline(MIN_MONTHLY_COMPLETENESS, color="red", linestyle="--",
           label=f"Minimum threshold ({MIN_MONTHLY_COMPLETENESS:.0%})")
ax.set_title("Monthly completeness per station — gaps highlight COVID exclusion + winter 2020-21 outages")
ax.set_ylabel("fraction of expected hourly readings")
ax.legend(loc="lower right", fontsize=7)
plt.tight_layout()
plt.show()
```

### Cell 20 — Visualization 3: spatial distribution of cleaned annual means

```python
annual = df_out.groupby("station_id")["pm25_mean"].mean().reset_index()
annual = annual.merge(df_out[["station_id", "lat", "lon"]].drop_duplicates(), on="station_id")

fig, ax = plt.subplots(figsize=(8, 7))
sc = ax.scatter(annual["lon"], annual["lat"], c=annual["pm25_mean"],
                cmap="RdYlGn_r", s=200, vmin=10, vmax=45, zorder=5)
plt.colorbar(sc, ax=ax, label="Mean PM2.5 (µg/m³)")
for _, row in annual.iterrows():
    ax.annotate(f"{row['station_id']}\n{row['pm25_mean']:.1f}", 
                (row["lon"], row["lat"]), textcoords="offset points",
                xytext=(5, 5), fontsize=7)
ax.set_xlabel("Longitude")
ax.set_ylabel("Latitude")
ax.set_title("Cleaned annual-mean PM2.5 at Krakow monitoring stations")
plt.tight_layout()
plt.show()
```

### Cell 21 — Markdown: what changed

```markdown
## What did cleaning change?

1. **COVID exclusion** — 78 days (Mar 15 – May 31 2020) across all stations removed.
   Why: traffic dropped 40%, PM2.5 dropped ~30% — not representative of urban form effects.
   Downstream: model trained on post-COVID-ban, post-coal-ban "normal" regime 2019-2024.

2. **Negative clipping** — 5 rows clipped from 0 at Aleja Krasińskiego (Jan 2023, cold snap sensor drift).
   Why: physically impossible, sensor error. Downstream: negligible effect on monthly means.

3. **Flatline removal** — 36 rows at Kurdwanów (Dec 15-16 2022) dropped.
   Why: stuck/frozen sensor — wrong data that looks right. Downstream: 1 station-month
   completeness drops below 75%, excluded from training data.

4. **Completeness filter** — station-months with <75% hourly readings excluded from aggregation.
   Why: sparse months are unrepresentative. Downstream: ~12-15% of station-months dropped
   (mostly Winter 2020-2021 outages at 3 stations).

5. **Złoty Róg bias flag** — flagged, not dropped. 20-30% low vs neighbours.
   Why: real data, but biased due to sheltered placement. Downstream: kept in training
   but excluded from leave-one-station-out validation lead fold.

**Total rows raw → cleaned (hourly):** ~440,000 → ~355,000 (~81% retained)
**Station-months raw → cleaned:** ~720 → ~600 (83% retained)

**Implications for the model card (S4):**
- Dataset must NOT be used for: hourly forecasting, pre-coal-ban pollution estimates,
  COVID-era traffic studies, or building-scale (<100m) predictions.
- Confidence intervals must account for: spatial interpolation uncertainty (>2km from
  stations = ±30%), Złoty Róg bias, post-coal-ban regime shift.
```

---

## Task 7 — Bridge to the module

### Cell 22 — Markdown: what gets promoted

```markdown
## What gets promoted to `src/clean_data.py`?

The following logic is repeated, stable, and has a clear input→output contract:

| Function to promote | Input | Output |
|---|---|---|
| `parse_timestamps` | df with string `timestamp` | df with UTC datetime |
| `clip_negative_pm25` | df with `pm25` float | df with pm25 ≥ 0, `pm25_negative_flag`, `pm25_raw` |
| `drop_flatline_periods` | df sorted by station+time | df minus stuck-sensor blocks, `pm25_flatline_flag` |
| `exclude_covid_window` | df with UTC `timestamp` | df minus Mar 15 – May 31 2020 |
| `correct_station_coordinates` | df with lat/lon | df with corrected lat/lon, `lat_original` preserved |
| `drop_low_completeness_months` | df grouped by station-month | df minus station-months <75% complete |
| `aggregate_to_monthly` | hourly df | monthly means df with completeness column |
| `flag_station_bias` | monthly df | monthly df with `station_bias_flag` column |
| `assert_clean_invariants` | any stage df | raises ValueError if invariants broken |
| `clean_aqicn_dataset` | raw df | cleaned monthly df (full pipeline) |

This notebook stays as the **exploration**. The module becomes the
**production** path. After promotion, this notebook should call
`from src.clean_data import clean_aqicn_dataset` instead of
duplicating the logic.
```

---

## Reproducibility check (do before committing)

1. `Restart kernel` in `02-data-cleaning.ipynb`.
2. `Run all` — every cell should run without error.
3. From terminal: `python src/clean_data.py` — confirm `aqicn_monthly.csv` regenerates.
4. Confirm the output from the script matches the notebook's output:
   ```python
   import pandas as pd
   pd.testing.assert_frame_equal(
       pd.read_csv("data/processed/aqicn_monthly.csv"),
       df_out.reset_index(drop=True),
       check_like=True
   )
   ```
5. Re-run `01-data-profiling.ipynb` on the cleaned data — confirm:
   - No negative PM2.5 values
   - No flatline periods at Kurdwanów Dec 2022
   - Gap visible in 2020 (COVID exclusion)

If any of these fail, the cleaning is not done. Fix before committing.
