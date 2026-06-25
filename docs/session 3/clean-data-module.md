# `src/clean_data.py` — Module Template
# Krakow Air Quality & Urban Form — AQICN PM2.5 Cleaning Pipeline

> Copy this file as the skeleton of `src/clean_data.py` in your repo.
> This is the **promoted** version of your `02-data-cleaning.ipynb` —
> the same logic, lifted out of the notebook into named, typed,
> documented, testable functions.
>
> Run from project root:
>     python src/clean_data.py
>
> Or import individual functions:
>     from src.clean_data import clean_aqicn_dataset

---

## The full template

Save the block below as `src/clean_data.py`:

```python
"""
clean_data.py — deterministic cleaning pipeline for AQICN Krakow PM2.5.

Reads raw hourly measurements from `data/raw/aqicn/`, applies the cleaning
logic settled on in `notebooks/02-data-cleaning.ipynb`, and writes the
cleaned monthly aggregated data to `data/processed/aqicn_monthly.csv`.

Run from project root:
    python src/clean_data.py

Or import individual functions:
    from src.clean_data import clean_aqicn_dataset

Cleaning decisions are documented in `docs/data-cleaning-log.md`.
Issues surfaced by: Rim (API download), Martina (spatial validation),
Rashi (anomaly detection), Bhavana (fitness-for-brief assessment).
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

# ── Paths ────────────────────────────────────────────────────────────────────
RAW_PATH = Path("data/raw/aqicn/krakow_pm25_2019_2024.csv")
OUT_PATH = Path("data/processed/aqicn_monthly.csv")

# ── Cleaning constants ────────────────────────────────────────────────────────
# Time window
STUDY_START = "2019-01-01"
STUDY_END   = "2024-12-31"

# COVID lockdown exclusion — traffic -40%, PM2.5 -30%, not representative
COVID_EXCLUDE_START = "2020-03-15"
COVID_EXCLUDE_END   = "2020-05-31"

# PM2.5 validity
PM25_VALID_MAX = 500.0  # µg/m³ — WHO emergency ceiling
MAX_PARSE_FAIL_FRACTION = 0.01  # >1% timestamp failures = abort

# Flatline detection — rolling std dev window and threshold
FLATLINE_WINDOW_HOURS = 24
FLATLINE_TOLERANCE    = 0.1  # µg/m³

# Aggregation
MIN_MONTHLY_COMPLETENESS = 0.75  # drop station-months with <75% hourly coverage

# Station coordinate corrections — verified against WIOŚ portal by Martina
COORD_CORRECTIONS: dict[str, dict[str, float]] = {
    "aleja_krasinskiego": {"lat": 50.0572, "lon": 19.9216},
    "ul_dietla":          {"lat": 50.0552, "lon": 19.9423},
}

# Stations known to have placement bias (Rashi's anomaly analysis)
SHELTERED_STATIONS = {"zloty_rog"}

# ── Final output schema ───────────────────────────────────────────────────────
FINAL_COLUMNS = [
    "station_id",
    "year_month",
    "lat",
    "lon",
    "station_type",
    "pm25_mean",
    "pm25_min",
    "pm25_max",
    "pm25_std",
    "pm25_count",
    "pm25_completeness",
    "n_negative_clipped",
    "station_bias_flag",
]


# ── Transform functions ───────────────────────────────────────────────────────

def parse_timestamps(df: pd.DataFrame) -> pd.DataFrame:
    """Parse timestamp column to UTC datetime, preserving the raw string.

    AQICN API always returns UTC. Confusion arises when mixing with the
    WIOŚ portal (which uses CET/CEST). Standardise to UTC here so all
    downstream joins and groupbys use a single timezone.

    Adds:
        timestamp_raw — original string preserved for traceability.
        timestamp     — parsed UTC datetime (NaT on failure).

    Raises:
        ValueError: If >MAX_PARSE_FAIL_FRACTION of timestamps fail to parse.

    Example:
        >>> df_parsed = parse_timestamps(df_raw)
        >>> df_parsed["timestamp"].dtype
        datetime64[ns, UTC]
    """
    out = df.copy()
    out["timestamp_raw"] = out["timestamp"]
    out["timestamp"] = pd.to_datetime(out["timestamp"], utc=True, errors="coerce")

    n_failed = out["timestamp"].isna().sum()
    if n_failed > len(out) * MAX_PARSE_FAIL_FRACTION:
        raise ValueError(
            f"Too many timestamp parse failures: {n_failed} / {len(out)} "
            f"(>{MAX_PARSE_FAIL_FRACTION:.1%}). Check raw data encoding."
        )
    print(f"parse_timestamps: {n_failed} parse failures out of {len(out):,}")
    return out


def exclude_covid_window(df: pd.DataFrame) -> pd.DataFrame:
    """Remove rows from the COVID lockdown period (Mar 15 – May 31 2020).

    During lockdown, traffic dropped ~40% and PM2.5 dropped ~30% below
    typical levels. Including this period would bias the model toward
    lower pollution than the urban form predicts under normal conditions.

    The excluded window is stored in COVID_EXCLUDE_START / COVID_EXCLUDE_END.

    Args:
        df: Dataframe with a UTC-parsed 'timestamp' column.

    Returns:
        Dataframe with COVID lockdown rows removed.

    Example:
        >>> df_no_covid = exclude_covid_window(df_parsed)
    """
    before = len(df)
    covid_mask = df["timestamp"].between(
        pd.Timestamp(COVID_EXCLUDE_START, tz="UTC"),
        pd.Timestamp(COVID_EXCLUDE_END, tz="UTC"),
    )
    out = df[~covid_mask].copy()
    print(f"exclude_covid_window: {before - len(out):,} rows removed "
          f"({COVID_EXCLUDE_START} – {COVID_EXCLUDE_END})")
    return out


def clip_negative_pm25(df: pd.DataFrame) -> pd.DataFrame:
    """Clip physically impossible negative PM2.5 to zero; flag and preserve raw.

    Cause: sensor calibration drift in extreme cold (−18°C, Jan 2023,
    Aleja Krasińskiego). Found 5 instances during Session 2 audit.
    Clipping to 0 rather than dropping — the event (extreme cold) is
    worth keeping in the temporal record.

    Adds:
        pm25_raw           — original value before clipping.
        pm25_negative_flag — bool, True where value was originally <0.

    Example:
        >>> df_clipped = clip_negative_pm25(df)
        >>> (df_clipped["pm25"] >= 0).all()
        True
    """
    out = df.copy()
    out["pm25"] = pd.to_numeric(out["pm25"], errors="coerce")
    out["pm25_raw"] = out["pm25"]
    out["pm25_negative_flag"] = out["pm25"] < 0

    n_neg = out["pm25_negative_flag"].sum()
    out["pm25"] = out["pm25"].clip(lower=0.0, upper=PM25_VALID_MAX)

    print(f"clip_negative_pm25: {n_neg:,} values clipped to 0")
    assert (out["pm25"] >= 0).all() | out["pm25"].isna(), \
        "pm25 still has negative values after clipping"
    return out


def drop_flatline_periods(
    df: pd.DataFrame,
    window_hours: int = FLATLINE_WINDOW_HOURS,
    tolerance: float = FLATLINE_TOLERANCE,
) -> pd.DataFrame:
    """Drop consecutive-hour blocks where PM2.5 is stuck (frozen sensor).

    A stuck sensor shows near-zero standard deviation over a long window
    despite changing weather at nearby stations. Identified at Kurdwanów:
    36 consecutive hours at 38.0 ± 0.1 µg/m³ (Dec 15-16 2022) while
    three neighbouring stations showed +/- 15 µg/m³ variation.

    Drops flatline rows rather than imputing — wrong data that looks right
    is worse than missing data.

    Args:
        df:           Dataframe sorted by station_id and timestamp.
        window_hours: Rolling window length for std dev calculation.
        tolerance:    µg/m³ std dev below which readings are flagged.

    Returns:
        Dataframe with flatline rows removed.

    Example:
        >>> df_no_flatline = drop_flatline_periods(df, window_hours=24)
    """
    required = {"station_id", "timestamp", "pm25"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    out = df.sort_values(["station_id", "timestamp"]).copy()

    def _flag(group: pd.DataFrame) -> pd.Series:
        rolling_std = group["pm25"].rolling(window_hours, min_periods=window_hours).std()
        return rolling_std < tolerance

    flat_mask = out.groupby("station_id", group_keys=False).apply(_flag)
    out["pm25_flatline_flag"] = flat_mask.values

    n_flagged = out["pm25_flatline_flag"].sum()
    out = out[~out["pm25_flatline_flag"]].copy()
    print(f"drop_flatline_periods: {n_flagged:,} rows removed "
          f"(window={window_hours}h, tol={tolerance} µg/m³)")
    return out


def correct_station_coordinates(df: pd.DataFrame) -> pd.DataFrame:
    """Apply verified coordinate corrections for 2 stations with AQICN entry errors.

    Martina validated all 10 station coordinates against Google Maps and
    the official WIOŚ portal. Found 2 stations off by ~100m (manual entry
    error in AQICN database). Spatial feature extraction at station locations
    requires correct coordinates — a 100m error shifts the extraction point
    into a different urban morphology class.

    Corrected stations: aleja_krasinskiego, ul_dietla
    Corrections stored in COORD_CORRECTIONS constant.

    Adds:
        lat_original — original AQICN coordinate (preserved for auditing).
        lon_original — original AQICN coordinate.

    Example:
        >>> df_corrected = correct_station_coordinates(df)
        >>> df_corrected.loc[df_corrected['station_id'] == 'aleja_krasinskiego', 'lat'].iloc[0]
        50.0572
    """
    out = df.copy()
    out["lat_original"] = out["lat"]
    out["lon_original"] = out["lon"]

    n_corrected_rows = 0
    for station_id, coords in COORD_CORRECTIONS.items():
        mask = out["station_id"] == station_id
        out.loc[mask, "lat"] = coords["lat"]
        out.loc[mask, "lon"] = coords["lon"]
        n_corrected_rows += mask.sum()

    print(f"correct_station_coordinates: corrected {len(COORD_CORRECTIONS)} stations "
          f"({n_corrected_rows:,} rows updated)")

    assert out["lat"].between(-90, 90).all(), "lat out of range after correction"
    assert out["lon"].between(-180, 180).all(), "lon out of range after correction"
    return out


def aggregate_to_monthly(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate hourly PM2.5 to monthly means per station, with completeness guard.

    Monthly aggregation is the right temporal unit for our model because:
    - Urban form (NDVI, road density) is static — it explains mean exposure,
      not hour-to-hour spikes.
    - Hour-to-hour variation is ~90% driven by weather (inversions, wind),
      not urban form.
    - Monthly means smooth weather noise and let urban form signal dominate.

    Station-months with <MIN_MONTHLY_COMPLETENESS of expected hourly readings
    are dropped (see data-cleaning-log.md Transform 7 for affected periods).

    Args:
        df: Cleaned hourly dataframe.

    Returns:
        Monthly aggregated dataframe with one row per (station_id, year_month).

    Example:
        >>> df_monthly = aggregate_to_monthly(df_clean)
        >>> df_monthly.columns.tolist()  # includes pm25_mean, pm25_completeness
    """
    out = df.copy()
    out["year_month"] = out["timestamp"].dt.to_period("M").astype(str)
    out["hours_in_month"] = out["timestamp"].dt.days_in_month * 24

    monthly = out.groupby(["station_id", "year_month"]).agg(
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

    before = len(monthly)
    monthly = monthly[monthly["pm25_completeness"] >= MIN_MONTHLY_COMPLETENESS].copy()
    print(f"aggregate_to_monthly: {before:,} → {len(monthly):,} station-months "
          f"(dropped {before - len(monthly):,} with <{MIN_MONTHLY_COMPLETENESS:.0%} completeness)")
    return monthly


def flag_station_bias(df: pd.DataFrame) -> pd.DataFrame:
    """Flag stations with documented placement bias in station_bias_flag column.

    Złoty Róg reads 20-30% lower than neighbouring stations under identical
    weather conditions. Rashi's anomaly analysis confirmed this is structural
    (sheltered by trees and buildings on three sides, not a malfunctioning
    sensor). The data is kept — it's real and useful for training — but
    flagged so the cross-validation step can exclude it from the lead fold.

    Args:
        df: Monthly aggregated dataframe with station_id column.

    Returns:
        Dataframe with station_bias_flag column added.

    Example:
        >>> df_flagged = flag_station_bias(df_monthly)
        >>> df_flagged.loc[df_flagged['station_id'] == 'zloty_rog', 'station_bias_flag'].unique()
        array(['sheltered_placement'], dtype=object)
    """
    out = df.copy()
    out["station_bias_flag"] = out["station_id"].apply(
        lambda sid: "sheltered_placement" if sid in SHELTERED_STATIONS else None
    )
    n_flagged = out["station_bias_flag"].notna().sum()
    print(f"flag_station_bias: {n_flagged:,} station-months flagged "
          f"({SHELTERED_STATIONS})")
    return out


def assert_clean_invariants(df: pd.DataFrame) -> None:
    """Assert every property the downstream model depends on.

    Run this at the END of the full pipeline. Failures here mean the
    cleaning invariants have drifted — fix the cleaning before proceeding.

    Checks:
        - No null timestamps
        - No negative PM2.5
        - All PM2.5 below physical ceiling
        - Coordinates in valid geographic ranges
        - All FINAL_COLUMNS present
        - No COVID lockdown rows remain
        - Completeness values in [0, 1]

    Raises:
        AssertionError: If any invariant is violated.
    """
    assert df["timestamp"].notna().all() if "timestamp" in df.columns else True, \
        "timestamp has nulls after cleaning"
    assert (df["pm25_mean"] >= 0).all(), "pm25_mean has negative values"
    assert (df["pm25_mean"] <= PM25_VALID_MAX).all(), \
        f"pm25_mean exceeds {PM25_VALID_MAX} µg/m³ ceiling"
    assert df["lat"].between(-90, 90).all(), "lat out of valid range"
    assert df["lon"].between(-180, 180).all(), "lon out of valid range"
    assert df["pm25_completeness"].between(0, 1).all(), \
        "completeness values outside [0, 1]"
    assert set(FINAL_COLUMNS).issubset(df.columns), \
        f"Missing columns: {set(FINAL_COLUMNS) - set(df.columns)}"

    # COVID lockdown should be excluded
    if "year_month" in df.columns:
        covid_months = {"2020-03", "2020-04", "2020-05"}
        overlap = set(df["year_month"].unique()) & covid_months
        assert not overlap, \
            f"COVID lockdown months present in cleaned data: {overlap}"

    print("assert_clean_invariants: all invariants passed")


def clean_aqicn_dataset(df_raw: pd.DataFrame) -> pd.DataFrame:
    """Full AQICN cleaning pipeline: raw hourly dataframe → cleaned monthly dataframe.

    Composition order matters — DON'T reorder without re-validating:
    1. parse_timestamps         — must come first (all downstream uses UTC datetime)
    2. exclude_covid_window     — needs parsed timestamps
    3. clip_negative_pm25       — coerce types before flagging
    4. drop_flatline_periods    — needs numeric pm25 and sorted timestamps
    5. correct_station_coordinates — independent of pm25, order flexible
    6. aggregate_to_monthly     — must come AFTER row-level cleaning
    7. flag_station_bias        — operates on aggregated data

    Args:
        df_raw: As-loaded raw CSV dataframe from AQICN download.

    Returns:
        Cleaned monthly dataframe with FINAL_COLUMNS.
    """
    df = (
        df_raw
        .pipe(parse_timestamps)
        .pipe(exclude_covid_window)
        .pipe(clip_negative_pm25)
        .pipe(drop_flatline_periods)
        .pipe(correct_station_coordinates)
        .pipe(aggregate_to_monthly)
        .pipe(flag_station_bias)
    )
    df = df[FINAL_COLUMNS].copy()
    assert_clean_invariants(df)
    return df


def main() -> None:
    """Run the cleaning pipeline from the command line."""
    print(f"Loading {RAW_PATH}…")
    df_raw = pd.read_csv(RAW_PATH)
    print(f"Raw shape: {df_raw.shape}")

    df_clean = clean_aqicn_dataset(df_raw)
    print(f"Cleaned shape: {df_clean.shape}")

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    df_clean.to_csv(OUT_PATH, index=False)
    print(f"Wrote {OUT_PATH} ({OUT_PATH.stat().st_size / 1024:.1f} KB)")
    print(f"Station-months in output: {len(df_clean):,}")


if __name__ == "__main__":
    main()
```

---

## Why this structure

### One function = one transform
Every function takes a dataframe in, returns a dataframe out. No
side-effects (except `print`). The pipeline composes with `.pipe(fn)` and
each function is unit-testable in isolation with a small synthetic dataframe.

### Constants at the top
`COVID_EXCLUDE_START`, `MIN_MONTHLY_COMPLETENESS`, `COORD_CORRECTIONS` —
every magic value is named and documented. When the team changes the
completeness threshold from 75% to 70%, they change one constant.

### `assert_clean_invariants` at the end
The most important function. It encodes every property the Session 4 model
depends on. If future cleaning changes break something silently (e.g., a
new station with impossible coordinates), the assertion fires loudly.

### `if __name__ == "__main__"` guard
Lets the module be both imported (`from src.clean_data import clean_aqicn_dataset`)
AND run from terminal (`python src/clean_data.py`). No code duplication.

---

## What to actually adapt

When you use this template, you'll need to change:

| You change | Why |
|---|---|
| `RAW_PATH` / `OUT_PATH` | Your actual file paths once downloaded |
| `COORD_CORRECTIONS` | Update with the exact corrected lat/lon values from WIOŚ |
| `FLATLINE_WINDOW_HOURS` / `FLATLINE_TOLERANCE` | Tune based on how the Kurdwanów flatline appears in your data |
| `clean_aqicn_dataset` pipe chain | Add or remove steps as cleaning evolves |
| `assert_clean_invariants` | Add any invariants you discover during Session 4 model training |
| `FINAL_COLUMNS` | Add columns if the model needs additional metadata |

The structure stays. The contents become yours.
