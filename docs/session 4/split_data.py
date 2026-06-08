"""
split_data.py — leakage-safe station-group split for Krakow PM2.5.

Reads the joined training dataset (aqicn monthly means + spatial features)
from `data/processed/`, applies a leave-one-station-out group split to
ensure the model is evaluated on stations it has never seen, writes three
parquets, and asserts there is no entity leakage between the sets.

Run from project root:
    python src/split_data.py

Or import the splitter directly:
    from src.split_data import make_station_splits

Splitting strategy is documented in `docs/modelling-log.md` decision #1.

WHY GROUP SPLIT, NOT TEMPORAL:
Temporal autocorrelation in PM2.5 (lag-1 month r ≈ 0.65 within a station)
means a random or temporal split leaks the future into the past via sibling
rows. More critically, the model is used to PREDICT AT NEW LOCATIONS (32,700
grid cells), not at existing stations. Leave-one-station-out tests the
only generalisation that matters: from trained stations to unseen locations.
"""

from __future__ import annotations

from pathlib import Path
from typing import NamedTuple

import numpy as np
import pandas as pd

# ── Paths ────────────────────────────────────────────────────────────────────
CLEAN_PATH = Path("data/processed/training_data.parquet")
OUT_DIR    = Path("data/processed/")
SLUG       = "aqicn-monthly"

# ── Split constants ───────────────────────────────────────────────────────────
RANDOM_SEED = 42

# Station assignments — documented in modelling-log.md decision #1.
# Test stations are sacred: never opened until model is locked.
# Złoty Róg: sheltered placement bias (20-30% low) — test metrics caveat in card.
# Nowa Huta: industrial station — critical for industrial-zone generalization.
TEST_STATIONS = frozenset({"zloty_rog", "nowa_huta"})

# Val station used for hyperparameter selection.
# Kurdwanów: background/industrial mix, well-characterised from audit.
VAL_STATIONS = frozenset({"kurdwanow"})

# Train stations: remaining 7 (covers traffic, background, urban-centre types).
# Derived at runtime from what's not in TEST or VAL.

# Columns the split must preserve (sanity check against schema drift).
REQUIRED_COLS = [
    "station_id",
    "year_month",
    "lat",
    "lon",
    "pm25_mean",
    "pm25_completeness",
]


class SplitResult(NamedTuple):
    """Three dataframes with a guarantee of no station-group leakage."""
    train: pd.DataFrame
    val:   pd.DataFrame
    test:  pd.DataFrame


def make_station_splits(df: pd.DataFrame) -> SplitResult:
    """Split df by station_id so no station appears in more than one set.

    Station assignment is fixed (not randomised) to ensure reproducibility.
    The three sets are disjoint by station_id:
        test  — Złoty Róg + Nowa Huta (2 stations, ~120 station-months)
        val   — Kurdwanów (1 station, ~55 station-months)
        train — remaining 7 stations (~420 station-months)

    This mirrors the deployment scenario: the model predicts at 32,700 grid
    cells that have NO PM2.5 monitor. Holding out stations at test time is
    the only split that tests the right kind of generalisation.

    Args:
        df: Joined monthly dataframe with REQUIRED_COLS and feature columns.

    Returns:
        SplitResult — three disjoint dataframes.

    Raises:
        ValueError: If required columns are missing.
        AssertionError: If any station appears in more than one set.

    Example:
        >>> df = pd.read_parquet("data/processed/training_data.parquet")
        >>> result = make_station_splits(df)
        >>> set(result.train["station_id"]) & set(result.test["station_id"])
        set()
    """
    missing = set(REQUIRED_COLS) - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    all_stations = set(df["station_id"].unique())
    unknown_test = TEST_STATIONS - all_stations
    unknown_val  = VAL_STATIONS  - all_stations
    if unknown_test:
        raise ValueError(f"TEST_STATIONS not found in data: {unknown_test}")
    if unknown_val:
        raise ValueError(f"VAL_STATIONS not found in data: {unknown_val}")

    train_stations = all_stations - TEST_STATIONS - VAL_STATIONS

    train = df[df["station_id"].isin(train_stations)].copy()
    val   = df[df["station_id"].isin(VAL_STATIONS)].copy()
    test  = df[df["station_id"].isin(TEST_STATIONS)].copy()

    _assert_no_group_leak(train, val, test, "station_id")
    _assert_nonempty(train, val, test)

    print(
        f"station split — "
        f"train: {len(train_stations)} stations ({len(train):,} rows) · "
        f"val: {len(VAL_STATIONS)} stations ({len(val):,} rows) · "
        f"test: {len(TEST_STATIONS)} stations ({len(test):,} rows)"
    )
    print(f"  train stations: {sorted(train_stations)}")
    print(f"  val stations:   {sorted(VAL_STATIONS)}")
    print(f"  test stations:  {sorted(TEST_STATIONS)}  ← SACRED until model locked")
    return SplitResult(train=train, val=val, test=test)


def make_loso_folds(df: pd.DataFrame) -> list[tuple[pd.DataFrame, pd.DataFrame]]:
    """Yield all 10 leave-one-station-out (LOSO) folds for cross-validation.

    Used in the notebook for CV spread (mean ± std across folds).
    Each fold holds out one station as the test fold; trains on the other 9.

    Args:
        df: Full training dataframe (train + val only — never pass test here).

    Returns:
        List of (train_fold, val_fold) tuples, one per station.

    Example:
        >>> folds = make_loso_folds(train_val_df)
        >>> len(folds)
        8
    """
    stations = df["station_id"].unique()
    folds = []
    for held_out in stations:
        fold_train = df[df["station_id"] != held_out].copy()
        fold_val   = df[df["station_id"] == held_out].copy()
        folds.append((fold_train, fold_val))
    return folds


def _assert_no_group_leak(
    train: pd.DataFrame,
    val:   pd.DataFrame,
    test:  pd.DataFrame,
    group_col: str,
) -> None:
    """Fail loudly if any station appears in more than one split."""
    train_g = set(train[group_col])
    val_g   = set(val[group_col])
    test_g  = set(test[group_col])
    assert not (train_g & val_g),  f"station leak train↔val:  {train_g & val_g}"
    assert not (train_g & test_g), f"station leak train↔test: {train_g & test_g}"
    assert not (val_g   & test_g), f"station leak val↔test:   {val_g & test_g}"


def _assert_nonempty(
    train: pd.DataFrame,
    val:   pd.DataFrame,
    test:  pd.DataFrame,
) -> None:
    assert len(train) > 0, "train set is empty — check station assignments"
    assert len(val)   > 0, "val set is empty — check VAL_STATIONS"
    assert len(test)  > 0, "test set is empty — check TEST_STATIONS"


def write_splits(result: SplitResult, slug: str = SLUG, out_dir: Path = OUT_DIR) -> None:
    """Write the three split dataframes to parquet."""
    out_dir.mkdir(parents=True, exist_ok=True)
    for name, part in (("train", result.train), ("val", result.val), ("test", result.test)):
        path = out_dir / f"{slug}-{name}.parquet"
        part.to_parquet(path, index=False)
        print(f"wrote {path} ({len(part):,} rows · {path.stat().st_size / 1024:.0f} KB)")


def main() -> None:
    print(f"Loading {CLEAN_PATH}…")
    df = pd.read_parquet(CLEAN_PATH)
    print(f"Shape: {df.shape}")
    print(f"Stations: {sorted(df['station_id'].unique())}")

    result = make_station_splits(df)
    write_splits(result)
    print("\nAll leakage assertions passed. Splits written.")
    print("Do NOT open the test parquet until the model is locked.")


if __name__ == "__main__":
    main()
