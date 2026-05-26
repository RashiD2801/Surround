"""
Krakow Multi-Station Air Quality Dataset Cleaning Script
=========================================================
Cleans and combines 8 individual station CSV files into one
ML-ready dataset with spatial variation across Krakow.

Stations:
  1. Nowa Huta
  2. Kurdwanow
  3. Zloty Rog
  4. Telimeny
  5. Os. Wadow
  6. Os. Piastow
  7. Ul. Dietla
  8. Aleja Krasinskiego

Run from the folder containing all 8 CSV files:
    python clean_multistation.py

Outputs:
    krakow_multistation_CLEANED.csv   (ML-ready, all stations combined)
    multistation_cleaning_report.txt  (audit trail)
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime

# =============================================================================
# CONFIGURATION
# =============================================================================

# Output files
OUTPUT_FILE = "krakow_multistation_CLEANED.csv"
REPORT_FILE = "multistation_cleaning_report.txt"

# Project date range (from problem-brief-v2.md)
PROJECT_START_YEAR = 2019
PROJECT_END_YEAR   = 2024

# COVID exclusion window (from data-cleaning-log.md)
COVID_START = "2020-03-15"
COVID_END   = "2020-05-31"

# High-missingness threshold: drop a column if missing > this %
HIGH_MISSING_THRESHOLD = 0.50

# PM2.5 physical plausibility cap (keep but flag above this)
EXTREME_THRESHOLD = 200  # ug/m3

# Station registry: filename keyword -> (station_id, display_name, lat, lon)
# Coordinates for each monitoring station in Krakow
STATIONS = {
    "nowa-huta":         ("nowa_huta",        "Nowa Huta",         50.0683,  20.0530),
    "kurdwan":           ("kurdwanow",         "Kurdwanow",         50.0076,  19.9742),
    "zloty":             ("zloty_rog",         "Zloty Rog",         50.0647,  19.9450),
    "telimeny":          ("telimeny",          "Ul. Telimeny",      50.0094,  19.9617),
    "wadow":             ("os_wadow",          "Os. Wadow",         50.0783,  19.8950),
    "piastow":           ("os_piastow",        "Os. Piastow",       50.0519,  19.8850),
    "dietla":            ("ul_dietla",         "Ul. Dietla",        50.0566,  19.9442),
    "aleja":             ("aleja_krasinskiego","Aleja Krasinskiego", 50.0573,  19.9100),
}

# =============================================================================
# HELPERS
# =============================================================================

def detect_station(filepath: str) -> tuple:
    """Match a filename to a station entry using keyword lookup."""
    name_lower = filepath.lower()
    for keyword, info in STATIONS.items():
        if keyword in name_lower:
            return info
    return None


def load_station_csv(filepath: str) -> pd.DataFrame:
    """
    Load a single station CSV. Handles:
    - Leading/trailing whitespace in column names and values
    - Date format YYYY/M/D (no zero-padding)
    - Numeric coercion for all pollutant columns
    """
    df = pd.read_csv(filepath, skipinitialspace=True)
    df.columns = df.columns.str.strip().str.lower()

    # Parse date
    df["date"] = pd.to_datetime(
        df["date"].astype(str).str.strip(),
        format="%Y/%m/%d",
        errors="coerce"
    )

    # Convert pollutants to numeric
    for col in ["pm25", "pm10", "o3", "no2", "so2", "co"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    return df


def section(title: str) -> str:
    return f"\n{'='*80}\n{title}\n{'='*80}"


# =============================================================================
# MAIN CLEANING PIPELINE
# =============================================================================

def clean_multistation():
    report = []
    report.append("KRAKOW MULTI-STATION AIR QUALITY CLEANING REPORT")
    report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append("=" * 80)

    # -------------------------------------------------------------------------
    # 0. DISCOVER FILES
    # -------------------------------------------------------------------------
    csv_files = sorted(Path(".").glob("*air-quality*.csv"))

    # Also catch any variant filenames (e.g. with underscores)
    if not csv_files:
        csv_files = sorted(Path(".").glob("*air_quality*.csv"))

    print(section("STEP 0: FILE DISCOVERY"))
    print(f"  Found {len(csv_files)} air-quality CSV file(s) in current folder:")
    for f in csv_files:
        print(f"    {f.name}")

    report.append(section("STEP 0: FILE DISCOVERY"))
    report.append(f"Found {len(csv_files)} file(s):")
    for f in csv_files:
        report.append(f"  {f.name}")

    if len(csv_files) == 0:
        msg = ("\n  ERROR: No air-quality CSV files found in this folder.\n"
               "  Make sure all 8 station files are in the same folder as this script.")
        print(msg)
        report.append(msg)
        with open(REPORT_FILE, "w", encoding="utf-8") as f:
            f.write("\n".join(report))
        return None

    # -------------------------------------------------------------------------
    # 1. LOAD + TAG ALL STATIONS
    # -------------------------------------------------------------------------
    print(section("STEP 1: LOAD AND TAG STATIONS"))
    report.append(section("STEP 1: LOAD AND TAG STATIONS"))

    all_frames = []
    unmatched  = []

    for fpath in csv_files:
        station_info = detect_station(str(fpath))

        if station_info is None:
            print(f"  WARNING: Could not match '{fpath.name}' to a known station. Skipping.")
            unmatched.append(fpath.name)
            continue

        station_id, station_name, lat, lon = station_info

        df = load_station_csv(str(fpath))

        # Tag with station metadata
        df["station_id"]   = station_id
        df["station_name"] = station_name
        df["station_lat"]  = lat
        df["station_lon"]  = lon

        rows_raw = len(df)
        pm25_missing = df["pm25"].isna().sum()

        all_frames.append(df)
        msg = (f"  Loaded: {station_name:25s} | "
               f"{rows_raw:>5} rows | "
               f"PM2.5 missing: {pm25_missing} ({pm25_missing/rows_raw*100:.1f}%)")
        print(msg)
        report.append(msg)

    if unmatched:
        report.append(f"\n  Unmatched files (skipped): {unmatched}")

    if not all_frames:
        print("\n  ERROR: No station files could be loaded.")
        return None

    # Combine all stations
    df = pd.concat(all_frames, ignore_index=True)
    print(f"\n  Combined shape: {df.shape}")
    report.append(f"\n  Combined shape after loading: {df.shape}")

    # -------------------------------------------------------------------------
    # 2. FILTER DATE RANGE (2019-2024)
    # -------------------------------------------------------------------------
    print(section("STEP 2: FILTER DATE RANGE"))
    report.append(section("STEP 2: FILTER DATE RANGE"))

    before = len(df)
    df["year"] = df["date"].dt.year
    df = df[(df["year"] >= PROJECT_START_YEAR) & 
            (df["year"] <= PROJECT_END_YEAR)].copy()
    removed = before - len(df)

    msg = (f"  Filtered to {PROJECT_START_YEAR}-{PROJECT_END_YEAR}\n"
           f"  Before: {before:,} rows\n"
           f"  After:  {len(df):,} rows\n"
           f"  Removed: {removed:,} rows ({removed/before*100:.1f}%)\n"
           f"  Reason: Outside project scope (pre-study data or future data)")
    print(msg)
    report.append(msg)

    # -------------------------------------------------------------------------
    # 3. REMOVE DUPLICATE ROWS PER STATION
    # -------------------------------------------------------------------------
    print(section("STEP 3: REMOVE DUPLICATES"))
    report.append(section("STEP 3: REMOVE DUPLICATES"))

    before = len(df)
    df = df.drop_duplicates(subset=["station_id", "date"]).copy()
    removed = before - len(df)

    msg = (f"  Removed duplicate (station, date) pairs\n"
           f"  Before: {before:,} rows\n"
           f"  After:  {len(df):,} rows\n"
           f"  Removed: {removed:,} duplicates")
    print(msg)
    report.append(msg)

    # -------------------------------------------------------------------------
    # 4. DROP ROWS WITH MISSING PM2.5 (TARGET VARIABLE)
    # -------------------------------------------------------------------------
    print(section("STEP 4: HANDLE TARGET VARIABLE (PM2.5)"))
    report.append(section("STEP 4: HANDLE TARGET VARIABLE (PM2.5)"))

    before = len(df)
    missing_by_station = df.groupby("station_name")["pm25"].apply(
        lambda x: f"{x.isna().sum()} missing ({x.isna().sum()/len(x)*100:.1f}%)"
    )
    print("  Missing PM2.5 per station:")
    report.append("  Missing PM2.5 per station:")
    for station, info in missing_by_station.items():
        print(f"    {station:25s}: {info}")
        report.append(f"    {station:25s}: {info}")

    df = df.dropna(subset=["pm25"]).copy()
    removed = before - len(df)

    # Clip negative values
    neg_count = (df["pm25"] < 0).sum()
    if neg_count > 0:
        df["pm25"] = df["pm25"].clip(lower=0)

    msg = (f"\n  Before: {before:,} rows\n"
           f"  After:  {len(df):,} rows\n"
           f"  Removed: {removed:,} rows\n"
           f"  Negative values clipped: {neg_count}\n"
           f"  Reason: Cannot train without target variable")
    print(msg)
    report.append(msg)

    # -------------------------------------------------------------------------
    # 5. EXCLUDE COVID PERIOD
    # -------------------------------------------------------------------------
    print(section("STEP 5: EXCLUDE COVID PERIOD"))
    report.append(section("STEP 5: EXCLUDE COVID PERIOD"))

    before = len(df)
    covid_mask = (df["date"] >= COVID_START) & (df["date"] <= COVID_END)
    df = df[~covid_mask].copy()
    removed = before - len(df)

    msg = (f"  Excluded {COVID_START} to {COVID_END}\n"
           f"  Before: {before:,} rows\n"
           f"  After:  {len(df):,} rows\n"
           f"  Removed: {removed:,} rows\n"
           f"  Reason: Traffic -40%, PM2.5 -30% during lockdown (not representative)")
    print(msg)
    report.append(msg)

    # -------------------------------------------------------------------------
    # 6. DROP HIGH-MISSINGNESS COLUMNS
    # -------------------------------------------------------------------------
    print(section("STEP 6: DROP HIGH-MISSING COLUMNS"))
    report.append(section("STEP 6: DROP HIGH-MISSING COLUMNS"))

    pollutant_cols = ["pm10", "o3", "no2", "so2", "co"]
    pollutant_cols = [c for c in pollutant_cols if c in df.columns]

    dropped_cols = []
    for col in pollutant_cols:
        missing_pct = df[col].isna().sum() / len(df)
        if missing_pct > HIGH_MISSING_THRESHOLD:
            df = df.drop(columns=[col])
            dropped_cols.append((col, missing_pct * 100))
            print(f"  DROPPED '{col}': {missing_pct*100:.1f}% missing")
            report.append(f"  DROPPED '{col}': {missing_pct*100:.1f}% missing")

    if not dropped_cols:
        print("  No columns dropped (all under 50% missing threshold)")
        report.append("  No columns dropped (all under 50% missing threshold)")

    # -------------------------------------------------------------------------
    # 7. IMPUTE REMAINING POLLUTANT FEATURES WITH MEDIAN
    # -------------------------------------------------------------------------
    print(section("STEP 7: IMPUTE REMAINING POLLUTANT FEATURES"))
    report.append(section("STEP 7: IMPUTE REMAINING POLLUTANT FEATURES"))

    # Impute per-station (not global median — each station has its own baseline)
    remaining_pollutants = [c for c in ["pm10", "o3", "no2", "so2", "co"]
                            if c in df.columns]
    total_imputed = 0

    for col in remaining_pollutants:
        missing = df[col].isna().sum()
        if missing > 0:
            # Per-station median imputation
            df[col] = df.groupby("station_id")[col].transform(
                lambda x: x.fillna(x.median())
            )
            # Fallback: global median for any station with all-NaN
            if df[col].isna().sum() > 0:
                df[col] = df[col].fillna(df[col].median())
            total_imputed += missing
            msg = f"  {col}: filled {missing:,} missing values with per-station median"
            print(msg)
            report.append(msg)

    if total_imputed == 0:
        print("  No imputation needed")
        report.append("  No imputation needed")

    # -------------------------------------------------------------------------
    # 8. CHECK EXTREME PM2.5 VALUES
    # -------------------------------------------------------------------------
    print(section("STEP 8: CHECK EXTREME PM2.5 VALUES"))
    report.append(section("STEP 8: CHECK EXTREME PM2.5 VALUES"))

    extreme = df[df["pm25"] > EXTREME_THRESHOLD]
    msg = (f"  Threshold: {EXTREME_THRESHOLD} ug/m3\n"
           f"  Extreme values found: {len(extreme)} rows across all stations\n")

    if len(extreme) > 0:
        by_station = extreme.groupby("station_name")["pm25"].agg(["count","max"])
        msg += "  Breakdown by station:\n"
        for stn, row in by_station.iterrows():
            msg += f"    {stn:25s}: {int(row['count'])} days, max={row['max']:.1f}\n"
        msg += "  Decision: KEPT (real winter pollution events in Krakow)"
    else:
        msg += "  No extreme values found — all PM2.5 within expected range"

    print(msg)
    report.append(msg)

    # -------------------------------------------------------------------------
    # 9. ADD TEMPORAL FEATURES
    # -------------------------------------------------------------------------
    print(section("STEP 9: ADD TEMPORAL FEATURES"))
    report.append(section("STEP 9: ADD TEMPORAL FEATURES"))

    df = df.sort_values(["station_id", "date"]).reset_index(drop=True)

    df["month"]      = df["date"].dt.month
    df["day_of_year"] = df["date"].dt.dayofyear
    df["weekday"]    = df["date"].dt.dayofweek
    df["is_weekend"] = (df["weekday"] >= 5).astype(int)

    # Cyclical encoding (preserves periodicity for ML)
    df["month_sin"] = np.sin(2 * np.pi * df["month"] / 12)
    df["month_cos"] = np.cos(2 * np.pi * df["month"] / 12)
    df["doy_sin"]   = np.sin(2 * np.pi * df["day_of_year"] / 365)
    df["doy_cos"]   = np.cos(2 * np.pi * df["day_of_year"] / 365)

    # Season
    season_map = {12:"winter",1:"winter",2:"winter",
                  3:"spring",4:"spring",5:"spring",
                  6:"summer",7:"summer",8:"summer",
                  9:"autumn",10:"autumn",11:"autumn"}
    df["season"] = df["month"].map(season_map)
    df = pd.get_dummies(df, columns=["season"], prefix="season", dtype=int)

    # Per-station lags (shift within each station — never bleed across stations)
    for lag in [1, 3, 7]:
        df[f"pm25_lag{lag}"] = (
            df.groupby("station_id")["pm25"]
              .shift(lag)
        )
    df["pm25_roll7d"] = (
        df.groupby("station_id")["pm25"]
          .transform(lambda x: x.shift(1).rolling(7).mean())
    )

    msg = ("  Added: month, day_of_year, weekday, is_weekend\n"
           "  Added: month_sin/cos, doy_sin/cos (cyclical encoding)\n"
           "  Added: season dummies (spring/summer/autumn/winter)\n"
           "  Added: pm25_lag1, pm25_lag3, pm25_lag7 (per-station)\n"
           "  Added: pm25_roll7d (7-day rolling mean per station)")
    print(msg)
    report.append(msg)

    # -------------------------------------------------------------------------
    # 10. FINAL CLEANUP
    # -------------------------------------------------------------------------
    print(section("STEP 10: FINAL CLEANUP"))
    report.append(section("STEP 10: FINAL CLEANUP"))

    # Drop rows where lag features are NaN (cold start)
    before_lag = len(df)
    df = df.dropna(subset=["pm25_lag7"]).copy()
    removed_lag = before_lag - len(df)

    # Drop the raw date column (keep year + temporal features)
    df = df.drop(columns=["date"])
    df = df.reset_index(drop=True)

    msg = (f"  Dropped lag cold-start rows: {removed_lag:,}\n"
           f"  Dropped raw 'date' column (year + temporal features retained)\n"
           f"  Reset index\n"
           f"  Final shape: {df.shape}")
    print(msg)
    report.append(msg)

    # -------------------------------------------------------------------------
    # SUMMARY
    # -------------------------------------------------------------------------
    rows_per_station = df.groupby("station_name").size()
    remaining_missing = df.isnull().sum()
    remaining_missing = remaining_missing[remaining_missing > 0]

    summary = f"\n{'='*80}\n"
    summary += "CLEANING SUMMARY\n"
    summary += f"{'='*80}\n"
    summary += f"Stations loaded:          {len(all_frames)}\n"
    summary += f"Final rows:               {len(df):,}\n"
    summary += f"Final columns:            {df.shape[1]}\n"
    summary += f"Date range:               {PROJECT_START_YEAR}-{PROJECT_END_YEAR} (COVID excluded)\n"
    summary += f"Target (PM2.5) missing:   0 (100% complete)\n"
    summary += f"\nROWS PER STATION:\n"
    for stn, count in rows_per_station.items():
        summary += f"  {stn:25s}: {count:,}\n"
    if len(remaining_missing) > 0:
        summary += f"\nREMAINING MISSING VALUES:\n"
        for col, count in remaining_missing.items():
            summary += f"  {col}: {count:,} ({count/len(df)*100:.2f}%)\n"
    else:
        summary += "\nREMAINING MISSING VALUES: None\n"

    print(summary)
    report.append(summary)

    return df, "\n".join(report)


# =============================================================================
# VALIDATION
# =============================================================================

def validate(df):
    print(section("VALIDATION CHECKS"))
    checks_passed = []
    checks_failed = []

    # 1. No missing PM2.5
    if df["pm25"].isna().sum() == 0:
        checks_passed.append("No missing PM2.5 values")
    else:
        checks_failed.append(f"{df['pm25'].isna().sum()} missing PM2.5 values remain")

    # 2. Date range
    if df["year"].min() >= PROJECT_START_YEAR and df["year"].max() <= PROJECT_END_YEAR:
        checks_passed.append(f"Date range correct ({PROJECT_START_YEAR}-{PROJECT_END_YEAR})")
    else:
        checks_failed.append(f"Date range incorrect: {df['year'].min()}-{df['year'].max()}")

    # 3. Multiple stations
    n_stations = df["station_id"].nunique()
    if n_stations >= 4:
        checks_passed.append(f"Multiple stations present ({n_stations} stations)")
    else:
        checks_failed.append(f"Too few stations ({n_stations}) — spatial modeling needs >=4")

    # 4. No negative PM2.5
    if (df["pm25"] >= 0).all():
        checks_passed.append("No negative PM2.5 values")
    else:
        checks_failed.append(f"{(df['pm25'] < 0).sum()} negative PM2.5 values remain")

    # 5. Sufficient rows
    if len(df) >= 1000:
        checks_passed.append(f"Sufficient sample size ({len(df):,} rows)")
    else:
        checks_failed.append(f"Sample size too small ({len(df):,} rows)")

    # 6. Spatial variation in PM2.5
    station_means = df.groupby("station_id")["pm25"].mean()
    variation = station_means.std()
    if variation > 1.0:
        checks_passed.append(f"Spatial variation in PM2.5 present (std={variation:.2f} across stations)")
    else:
        checks_failed.append(f"Very low spatial variation (std={variation:.2f}) — check data")

    for c in checks_passed:
        print(f"  PASS: {c}")
    for c in checks_failed:
        print(f"  FAIL: {c}")

    if not checks_failed:
        print(f"\n  ALL {len(checks_passed)} VALIDATION CHECKS PASSED")
        print("  Dataset is ready for spatial ML modeling.")
    else:
        print(f"\n  {len(checks_failed)} CHECK(S) FAILED — review before modeling")

    return checks_failed


# =============================================================================
# ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    print("\n" + "="*80)
    print("KRAKOW MULTI-STATION AIR QUALITY CLEANING")
    print("="*80)
    print(f"Output dataset: {OUTPUT_FILE}")
    print(f"Output report:  {REPORT_FILE}")

    result = clean_multistation()

    if result is None:
        print("\nCleaning failed — check report for details.")
        exit(1)

    df_cleaned, report_text = result

    # Save cleaned dataset
    df_cleaned.to_csv(OUTPUT_FILE, index=False)
    print(f"\nSaved cleaned dataset: {OUTPUT_FILE}")
    print(f"Shape: {df_cleaned.shape}")

    # Save report
    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        f.write(report_text)
    print(f"Saved cleaning report: {REPORT_FILE}")

    # Validate
    failures = validate(df_cleaned)

    if not failures:
        print(f"\n{'='*80}")
        print("NEXT STEPS")
        print(f"{'='*80}")
        print("  1. Run exploratory analysis on krakow_multistation_CLEANED.csv")
        print("  2. Merge with spatial features from krakow_pipeline.py (per station)")
        print("  3. Train with leave-one-station-out cross-validation")
        print("  4. Target: R2 >= 0.40 (from problem-brief-v2.md)")