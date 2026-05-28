# `src/split_data.py` — Module Template

> Copy this file as the skeleton of `src/split_data.py` in your repo.
> This is the **promoted** version of your split logic — typed,
> documented, with assertions that make leakage impossible to ship
> silently.
>
> **Why this matters for non-CS students:** the split is the single
> highest-leverage decision in modelling. Putting it in its own module
> with explicit assertions means the decision is reviewable, testable,
> and impossible to break by accident in S5–S7.

---

## The full template

Save the block below as `src/split_data.py`:

```python
"""
split_data.py — leakage-safe train / val / test split for [dataset name].

Reads the cleaned parquet from `data/processed/`, applies the splitting
strategy chosen in `notebooks/03-modelling.ipynb`, writes three parquets,
and asserts there is no leakage between the sets.

Run from project root:
    python src/split_data.py

Or import the splitter directly:
    from src.split_data import make_splits

Splitting strategy is documented in `docs/modelling-log.md` decision #1.
"""

from __future__ import annotations

from pathlib import Path
from typing import NamedTuple

import numpy as np
import pandas as pd

# Paths — relative to project root.
CLEAN_PATH = Path("data/processed/your-dataset-clean.parquet")
OUT_DIR = Path("data/processed/")

# Splitting constants — every cutoff lives here, not inline.
RANDOM_SEED = 42
TRAIN_END = pd.Timestamp("2023-08-01", tz="UTC")
VAL_END = pd.Timestamp("2023-09-01", tz="UTC")

# The group column (used only for spatial / entity splits — None for pure temporal).
GROUP_COL = None  # e.g. "station_id" if doing GroupKFold

# Columns the split must preserve (sanity check).
REQUIRED_COLS = ["timestamp", "station_id", "lat", "lon", "temp_c"]


class SplitResult(NamedTuple):
    """Three dataframes with a guarantee of no leakage between them."""

    train: pd.DataFrame
    val: pd.DataFrame
    test: pd.DataFrame


def make_splits(
    df: pd.DataFrame,
    train_end: pd.Timestamp = TRAIN_END,
    val_end: pd.Timestamp = VAL_END,
) -> SplitResult:
    """Split df into train / val / test by a temporal cutoff.

    The cutoffs are exclusive on the upper end: train < train_end ≤ val
    < val_end ≤ test. Two leakage assertions run before return — if either
    fires, the split is rejected loudly.

    Args:
        df: Cleaned dataframe with a `timestamp` column (UTC datetime).
        train_end: All rows with timestamp < train_end go to train.
        val_end: Rows in [train_end, val_end) go to val. Rest to test.

    Returns:
        A SplitResult with three disjoint, time-ordered dataframes.

    Raises:
        AssertionError: If any leakage assertion fires.

    Example:
        >>> df = pd.read_parquet("data/processed/your-dataset-clean.parquet")
        >>> result = make_splits(df)
        >>> result.train["timestamp"].max() < result.val["timestamp"].min()
        True
    """
    missing = set(REQUIRED_COLS) - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    df = df.sort_values("timestamp").reset_index(drop=True)

    train = df[df["timestamp"] < train_end].copy()
    val = df[(df["timestamp"] >= train_end) & (df["timestamp"] < val_end)].copy()
    test = df[df["timestamp"] >= val_end].copy()

    _assert_no_temporal_leak(train, val, test)
    _assert_nonempty(train, val, test)

    print(
        f"split sizes — train: {len(train):,} · val: {len(val):,} "
        f"· test: {len(test):,} "
        f"(retention {len(train) + len(val) + len(test):,} of {len(df):,})"
    )
    return SplitResult(train=train, val=val, test=test)


def make_group_splits(
    df: pd.DataFrame,
    group_col: str,
    n_train: int,
    n_val: int,
    random_state: int = RANDOM_SEED,
) -> SplitResult:
    """Split df so each value of group_col appears in exactly one set.

    Used when generalization to new entities (stations, buildings,
    patients) is what matters. Falls back to GroupKFold-style assignment
    on the unique groups.
    """
    if group_col not in df.columns:
        raise ValueError(f"group_col {group_col!r} not in df")

    rng = np.random.default_rng(random_state)
    groups = df[group_col].dropna().unique()
    rng.shuffle(groups)

    train_g = set(groups[:n_train])
    val_g = set(groups[n_train : n_train + n_val])
    test_g = set(groups[n_train + n_val :])

    train = df[df[group_col].isin(train_g)].copy()
    val = df[df[group_col].isin(val_g)].copy()
    test = df[df[group_col].isin(test_g)].copy()

    _assert_no_group_leak(train, val, test, group_col)
    _assert_nonempty(train, val, test)

    print(
        f"group split — train: {len(train_g)} groups · val: {len(val_g)} "
        f"· test: {len(test_g)}"
    )
    return SplitResult(train=train, val=val, test=test)


def _assert_no_temporal_leak(
    train: pd.DataFrame, val: pd.DataFrame, test: pd.DataFrame
) -> None:
    """Fail loudly if any timestamp from a later set appears in an earlier one."""
    assert train["timestamp"].max() < val["timestamp"].min(), (
        f"temporal leak: train extends to {train['timestamp'].max()} "
        f"≥ val starts at {val['timestamp'].min()}"
    )
    assert val["timestamp"].max() < test["timestamp"].min(), (
        f"temporal leak: val extends to {val['timestamp'].max()} "
        f"≥ test starts at {test['timestamp'].min()}"
    )


def _assert_no_group_leak(
    train: pd.DataFrame,
    val: pd.DataFrame,
    test: pd.DataFrame,
    group_col: str,
) -> None:
    """Fail loudly if any group value appears in more than one set."""
    train_g, val_g, test_g = (
        set(train[group_col]),
        set(val[group_col]),
        set(test[group_col]),
    )
    assert not (train_g & val_g), f"group leak train↔val: {train_g & val_g}"
    assert not (train_g & test_g), f"group leak train↔test: {train_g & test_g}"
    assert not (val_g & test_g), f"group leak val↔test: {val_g & test_g}"


def _assert_nonempty(
    train: pd.DataFrame, val: pd.DataFrame, test: pd.DataFrame
) -> None:
    assert len(train) > 0, "train set is empty — check cutoffs"
    assert len(val) > 0, "val set is empty — check cutoffs"
    assert len(test) > 0, "test set is empty — check cutoffs"


def write_splits(result: SplitResult, slug: str, out_dir: Path = OUT_DIR) -> None:
    """Write the three dataframes to parquet with consistent naming."""
    out_dir.mkdir(parents=True, exist_ok=True)
    for name, part in (("train", result.train), ("val", result.val), ("test", result.test)):
        path = out_dir / f"{slug}-{name}.parquet"
        part.to_parquet(path, index=False)
        print(f"wrote {path} ({path.stat().st_size / 1024:.0f} KB)")


def main() -> None:
    print(f"Loading {CLEAN_PATH}…")
    df = pd.read_parquet(CLEAN_PATH)
    print(f"Shape: {df.shape}")

    result = make_splits(df)
    write_splits(result, slug="your-dataset")


if __name__ == "__main__":
    main()
```

---

## Why this structure

### One function = one split strategy
`make_splits` is temporal. `make_group_splits` is entity-grouped. If your
data needs both stacked (most environmental data does), write a third
function that composes them — never overload one function with a flag.

### Constants at the top
The cutoffs `TRAIN_END` and `VAL_END` are constants. If you change the
split, you change them in one place — not buried mid-function.

### Assertions are the contract
`_assert_no_temporal_leak` and `_assert_no_group_leak` are the entire
point of having this module. If they ever fire, the evaluation downstream
is fiction. They run at split time so failure is loud and local.

### A `NamedTuple` return
`SplitResult` is a typed return with three named dataframes. Calling
code accesses `result.train`, `result.val`, `result.test` — never
unpacks a 3-tuple by position. Position-based unpacking is where
"oh we swapped val and test" bugs come from.

### `if __name__ == "__main__"` guard
Lets the module be both imported (from `03-modelling.ipynb`) AND run
from the command line. No code duplication.

---

## What to actually adapt

When you copy this template, you'll need to change:

| You change | Why |
|---|---|
| `CLEAN_PATH`, `OUT_DIR` | Your file paths |
| `TRAIN_END`, `VAL_END` | Your dataset's cutoffs |
| `GROUP_COL` | Set if using `make_group_splits` |
| `REQUIRED_COLS` | Columns your model needs |
| Pick one of `make_splits` / `make_group_splits` / write a stacked one | Match your leakage structure |
| `slug="your-dataset"` in `main()` | Your dataset's filename slug |

The assertions stay. The constants change. The contract is the same.

---

## Common adaptations

### Spatial split — bucket by clusters, then GroupKFold

```python
from sklearn.cluster import KMeans

# Bucket stations into 5 spatial clusters.
station_xy = df.groupby("station_id")[["lat", "lon"]].mean()
kmeans = KMeans(n_clusters=5, random_state=RANDOM_SEED, n_init=10)
station_xy["cluster"] = kmeans.fit_predict(station_xy)
df["spatial_cluster"] = df["station_id"].map(station_xy["cluster"])

result = make_group_splits(df, group_col="spatial_cluster", n_train=3, n_val=1)
```

### Stacked split — temporal first, group within

```python
# Step 1: temporal cutoff to remove the past from val/test.
# Step 2: within each set, drop entities that overlap with another set.
# (Implementation depends on your domain — log the reasoning in modelling-log.md.)
```

### Forward-chaining CV (for hyperparameter tuning)

```python
from sklearn.model_selection import TimeSeriesSplit

tscv = TimeSeriesSplit(n_splits=5)
for fold, (tr_idx, te_idx) in enumerate(tscv.split(train_df)):
    ...
```

---

## Pre-commit check

Before you push:

- [ ] `python src/split_data.py` runs without error.
- [ ] The three parquet sizes are reasonable (~70 / 15 / 15 split).
- [ ] All four assertions in the module pass on your data.
- [ ] The split strategy is logged in `docs/modelling-log.md` decision #1.
- [ ] You did NOT open the test parquet in any cell after writing it.
