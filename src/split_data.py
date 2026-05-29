"""
split_data.py — leakage-safe station-group split for Krakow PM2.5.

Reads the final cleaned daily dataset from `data/output/krakow_final_dataset.csv`,
applies a leave-one-station-out group split so the model is evaluated on stations
it has never seen during training, and writes three CSVs.

Run from project root:
    python src/split_data.py

Or import directly:
    from src.split_data import make_station_splits

Splitting strategy documented in docs/modelling-log.md decision #1.

WHY GROUP SPLIT, NOT TEMPORAL:
The model predicts PM2.5 at 32,700 unmeasured grid cells across Krakow.
Holding out whole stations at test time is the only split that tests
the right generalisation: from trained stations to unseen locations.
A temporal split puts all 8 stations in test — the model is then
evaluated on stations it was trained on, which proves nothing about
spatial generalisation.

NOTE ON LAG FEATURES (pm25_lag1, pm25_lag3, pm25_lag7, pm25_roll7d):
These columns exist in the dataset but are NOT included in FEATURE_COLS
because lag features require knowing the previous PM2.5 at the target
location — unavailable for unmeasured grid cells at deployment time.
They are kept in the split CSVs for reference only.
"""

from __future__ import annotations

from pathlib import Path
from typing import NamedTuple

import numpy as np
import pandas as pd

# ── Paths ─────────────────────────────────────────────────────────────────────
CLEAN_PATH = Path("data/output/krakow_final_dataset.csv")
OUT_DIR    = Path("data/processed/")
SLUG       = "krakow-pm25"

# ── Constants ─────────────────────────────────────────────────────────────────
RANDOM_SEED = 42

# Station assignments — fixed for reproducibility.
# Zloty Rog: sheltered placement bias (reads 20-30% low) — test caveat in card.
# Nowa Huta: only industrial-zone station — critical for industrial generalisation.
TEST_STATIONS = frozenset({"zloty_rog", "nowa_huta"})

# Kurdwanow: background/industrial mix, well-characterised from S2 audit.
VAL_STATIONS = frozenset({"kurdwanow"})

# Train: remaining 5 stations.

# Columns the split must preserve (sanity check against schema drift).
REQUIRED_COLS = ["station_id", "pm25", "year", "month", "day_of_year",
                 "station_lat", "station_lon"]


class SplitResult(NamedTuple):
    """Three dataframes with a guarantee of no station-group leakage."""
    train: pd.DataFrame
    val:   pd.DataFrame
    test:  pd.DataFrame


def make_station_splits(df: pd.DataFrame) -> SplitResult:
    """Split df by station_id so no station appears in more than one set.

    Station assignment is fixed (not randomised) to ensure reproducibility.
    The three sets are disjoint by station_id:
        test  — zloty_rog + nowa_huta   (~3,400 daily rows)
        val   — kurdwanow               (~1,700 daily rows)
        train — remaining 5 stations    (~8,500 daily rows)

    Args:
        df: Final cleaned daily dataframe with REQUIRED_COLS present.

    Returns:
        SplitResult — three disjoint dataframes.

    Raises:
        ValueError: If required columns or expected stations are missing.
        AssertionError: If any station appears in more than one set.

    Example:
        >>> df = pd.read_csv("data/output/krakow_final_dataset.csv")
        >>> result = make_station_splits(df)
        >>> set(result.train["station_id"]) & set(result.test["station_id"])
        set()
    """
    missing_cols = set(REQUIRED_COLS) - set(df.columns)
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")

    all_stations  = set(df["station_id"].unique())
    unknown_test  = TEST_STATIONS - all_stations
    unknown_val   = VAL_STATIONS  - all_stations
    if unknown_test:
        raise ValueError(f"TEST_STATIONS not found in data: {unknown_test}")
    if unknown_val:
        raise ValueError(f"VAL_STATIONS not found in data: {unknown_val}")

    train_stations = all_stations - TEST_STATIONS - VAL_STATIONS

    train = df[df["station_id"].isin(train_stations)].copy().reset_index(drop=True)
    val   = df[df["station_id"].isin(VAL_STATIONS)].copy().reset_index(drop=True)
    test  = df[df["station_id"].isin(TEST_STATIONS)].copy().reset_index(drop=True)

    _assert_no_group_leak(train, val, test, "station_id")
    _assert_nonempty(train, val, test)

    print(
        f"station split — "
        f"train: {len(train_stations)} stations ({len(train):,} rows) · "
        f"val: {len(VAL_STATIONS)} station ({len(val):,} rows) · "
        f"test: {len(TEST_STATIONS)} stations ({len(test):,} rows)"
    )
    print(f"  train stations: {sorted(train_stations)}")
    print(f"  val stations:   {sorted(VAL_STATIONS)}")
    print(f"  test stations:  {sorted(TEST_STATIONS)}  <- SACRED until model locked")
    return SplitResult(train=train, val=val, test=test)


def make_loso_folds(df: pd.DataFrame) -> list[tuple[pd.DataFrame, pd.DataFrame]]:
    """Yield all leave-one-station-out folds for cross-validation.

    Each fold holds out one station as val; trains on the rest.
    Call with train+val combined (never include test).

    Args:
        df: Combined train+val dataframe.

    Returns:
        List of (train_fold, val_fold) tuples — one per unique station.
    """
    stations = df["station_id"].unique()
    return [
        (df[df["station_id"] != s].copy(), df[df["station_id"] == s].copy())
        for s in stations
    ]


def _assert_no_group_leak(
    train: pd.DataFrame, val: pd.DataFrame, test: pd.DataFrame, col: str
) -> None:
    tg, vg, eg = set(train[col]), set(val[col]), set(test[col])
    assert not (tg & vg),  f"station leak train<->val:  {tg & vg}"
    assert not (tg & eg),  f"station leak train<->test: {tg & eg}"
    assert not (vg & eg),  f"station leak val<->test:   {vg & eg}"


def _assert_nonempty(train, val, test) -> None:
    assert len(train) > 0, "train set is empty — check station assignments"
    assert len(val)   > 0, "val set is empty — check VAL_STATIONS"
    assert len(test)  > 0, "test set is empty — check TEST_STATIONS"


def write_splits(result: SplitResult, slug: str = SLUG, out_dir: Path = OUT_DIR) -> None:
    """Write the three split dataframes to CSV."""
    out_dir.mkdir(parents=True, exist_ok=True)
    for name, part in (("train", result.train), ("val", result.val), ("test", result.test)):
        path = out_dir / f"{slug}-{name}.csv"
        part.to_csv(path, index=False)
        print(f"wrote {path} ({len(part):,} rows · {path.stat().st_size / 1024:.0f} KB)")


def main() -> None:
    print(f"Loading {CLEAN_PATH}...")
    df = pd.read_csv(CLEAN_PATH)
    print(f"Shape: {df.shape}")
    print(f"Stations: {sorted(df['station_id'].unique())}")

    result = make_station_splits(df)
    write_splits(result)
    print("\nAll leakage assertions passed. Splits written.")
    print("Do NOT open the test CSV until the model is locked.")


if __name__ == "__main__":
    main()
