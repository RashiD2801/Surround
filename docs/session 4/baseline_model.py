"""
baseline_model.py — baselines + first model for Krakow PM2.5 spatial prediction.

Reads the train / val parquets produced by `src/split_data.py`, fits two
baselines and one Random Forest model, prints an honest metrics table, and
saves the final model as a single sklearn Pipeline.

Run from project root:
    python src/baseline_model.py

Or import individual functions:
    from src.baseline_model import train_baseline_model, predict_with_uncertainty

Modelling decisions are documented in `docs/modelling-log.md`.

Target:   pm25_mean  (µg/m³ — monthly mean PM2.5 at a station)
Problem:  spatial regression — predict monthly mean PM2.5 from urban form +
          weather features at the station location. Generalises to unmeasured
          locations (32,700 100m Krakow grid cells).
"""

from __future__ import annotations

from pathlib import Path
from typing import NamedTuple

import joblib
import numpy as np
import pandas as pd
from sklearn.dummy import DummyRegressor
from sklearn.ensemble import RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

# ── Paths ────────────────────────────────────────────────────────────────────
SPLIT_DIR  = Path("data/processed/")
MODEL_PATH = Path("models/baseline.joblib")
SLUG       = "aqicn-monthly"

# ── Constants ─────────────────────────────────────────────────────────────────
RANDOM_SEED = 42
TARGET      = "pm25_mean"

# Urban form + weather features agreed in Session 3 pipeline design.
# "month" is derived from year_month and serves as the seasonal control.
# Without it, the model conflates urban form signal with heating-season signal.
FEATURE_COLS = [
    "ndvi",                  # vegetation index (Sentinel-2 summer composite)
    "ndbi",                  # built-up index (Sentinel-2)
    "road_density_500m",     # km road per km² within 500m buffer (OSM)
    "building_density_500m", # % building footprint within 500m (OSM)
    "pct_green_500m",        # % green land cover within 500m (Urban Atlas)
    "mean_temp_monthly",     # monthly mean 2m temperature °C (ERA5-Land)
    "blh_monthly",           # monthly mean boundary layer height m (ERA5-Land)
    "month",                 # 1–12 — seasonal control variable
]

# Random Forest hyperparameters — see modelling-log.md decision #6.
N_TREES  = 300
MIN_LEAF = 3


class FitResult(NamedTuple):
    """The trained pipeline plus a tidy metrics report."""
    pipeline: Pipeline
    metrics:  pd.DataFrame


# ── Feature engineering ───────────────────────────────────────────────────────

def add_month_feature(df: pd.DataFrame) -> pd.DataFrame:
    """Extract integer month (1–12) from year_month string ('YYYY-MM')."""
    out = df.copy()
    out["month"] = out["year_month"].str[5:7].astype(int)
    return out


# ── Baselines ─────────────────────────────────────────────────────────────────

def fit_dumb_baseline(X_train: pd.DataFrame, y_train: pd.Series) -> DummyRegressor:
    """Predict the training-set mean pm25_mean for every input.

    The floor. A model that can't beat this is useless.
    Expected val MAE: ~15–18 µg/m³ (Krakow annual mean ≈ 35 µg/m³,
    seasonal std ≈ 17 µg/m³).
    """
    dumb = DummyRegressor(strategy="mean")
    dumb.fit(X_train, y_train)
    return dumb


def fit_seasonal_baseline(train: pd.DataFrame) -> dict[int, float]:
    """Predict the training-set month-specific mean pm25_mean.

    Captures the Krakow seasonal signal (winter coal heating → PM2.5 ~55 µg/m³
    in January; summer background → ~12 µg/m³ in August) without any spatial
    features. A model that can't beat this isn't learning urban form — it's
    just learning the calendar.

    Returns:
        dict mapping month (1–12) → mean pm25_mean from training data.
    """
    return train.groupby("month")[TARGET].mean().to_dict()


def predict_seasonal(month_means: dict[int, float], df: pd.DataFrame) -> pd.Series:
    """Apply the seasonal-mean lookup to df['month']."""
    overall_mean = np.mean(list(month_means.values()))
    return df["month"].map(month_means).fillna(overall_mean)


def predict_spatial_nearest(
    train: pd.DataFrame,
    df: pd.DataFrame,
    k: int = 2,
) -> pd.Series:
    """Predict pm25_mean as the month-matched mean of the k nearest train stations.

    For each row in df, find the k training stations closest in lat/lon and
    share the same year_month. Computes Euclidean distance in degree space
    (acceptable for a ~20km × 20km city where 1° lat ≈ 111km, 1° lon ≈ 75km).

    This is the strongest pre-model baseline for a spatial problem — it
    tests whether simply knowing what the neighbours measured beats our model.

    Args:
        train: Training dataframe with lat, lon, year_month, pm25_mean.
        df:    Val or test dataframe.
        k:     Number of nearest training stations to average over.

    Returns:
        Series of predicted pm25_mean values aligned with df's index.
    """
    station_locs = (
        train.groupby("station_id")[["lat", "lon"]].first().reset_index()
    )

    preds = []
    for _, row in df.iterrows():
        dists = np.sqrt(
            (station_locs["lat"] - row["lat"]) ** 2
            + (station_locs["lon"] - row["lon"]) ** 2
        )
        nearest_ids = station_locs.loc[dists.nsmallest(k).index, "station_id"]
        same_month = train[
            (train["station_id"].isin(nearest_ids))
            & (train["year_month"] == row["year_month"])
        ]
        if len(same_month) == 0:
            # Fallback: any month from these stations
            same_month = train[train["station_id"].isin(nearest_ids)]
        preds.append(same_month[TARGET].mean())

    return pd.Series(preds, index=df.index)


# ── Model ─────────────────────────────────────────────────────────────────────

def build_pipeline(random_state: int = RANDOM_SEED) -> Pipeline:
    """Construct an unfitted sklearn Pipeline: impute → scale → RandomForest.

    Wrapped in a Pipeline so that the same preprocessing runs at predict time
    as at train time. Eliminates train-vs-serve skew.

    Why Random Forest:
    - Problem shape: regression from 8 mixed numeric features, N≈420 rows.
    - Size: small enough that RF trains in seconds; too small for deep learning.
    - Explainability: SHAP values are interpretable for planners (session 7).
    - Handles nonlinear feature interactions (seasonal × urban form).
    - Provides uncertainty via tree-quantile intervals (no extra library).

    Returns:
        Unfitted Pipeline ready for .fit(X, y).
    """
    return Pipeline(steps=[
        ("impute", SimpleImputer(strategy="median")),
        ("scale",  StandardScaler()),
        ("model",  RandomForestRegressor(
            n_estimators=N_TREES,
            min_samples_leaf=MIN_LEAF,
            random_state=random_state,
            n_jobs=-1,
        )),
    ])


def train_baseline_model(
    X_train: pd.DataFrame,
    y_train: pd.Series,
) -> Pipeline:
    """Fit the Pipeline on train data and return the fitted estimator.

    Args:
        X_train: Training features. Must contain all FEATURE_COLS.
        y_train: Training target (pm25_mean).

    Returns:
        Fitted sklearn Pipeline.

    Raises:
        ValueError: If any FEATURE_COLS are missing from X_train.

    Example:
        >>> p = train_baseline_model(X_train, y_train)
        >>> preds = p.predict(X_val)
        >>> preds.shape == y_val.shape
        True
    """
    missing = set(FEATURE_COLS) - set(X_train.columns)
    if missing:
        raise ValueError(f"Missing feature columns: {missing}")

    pipeline = build_pipeline()
    pipeline.fit(X_train[FEATURE_COLS], y_train)
    return pipeline


# ── Evaluation ────────────────────────────────────────────────────────────────

def compute_metrics_table(
    pipeline:      Pipeline,
    train:         pd.DataFrame,
    val:           pd.DataFrame,
    month_means:   dict[int, float],
    test:          pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Build the honest metrics table — splits × models × MAE and R².

    Test is computed ONLY if `test` is explicitly provided (model locked).
    Default call omits test. This makes accidental test peeking impossible
    at the module level.

    Args:
        pipeline:    Fitted sklearn Pipeline.
        train:       Training dataframe (must have FEATURE_COLS + 'month').
        val:         Validation dataframe.
        month_means: Seasonal baseline lookup from fit_seasonal_baseline().
        test:        Optional test dataframe — pass only when model is locked.

    Returns:
        DataFrame with columns [split, model, MAE, R2].
    """
    rows = []

    def _append(split_name, model_name, y_true, y_pred):
        rows.append({
            "split": split_name,
            "model": model_name,
            "MAE":   round(mean_absolute_error(y_true, y_pred), 3),
            "R2":    round(r2_score(y_true, y_pred), 3),
        })

    dumb = fit_dumb_baseline(train[FEATURE_COLS], train[TARGET])

    for split_name, part in [("train", train), ("val", val)]:
        _append(split_name, "dumb-mean",    part[TARGET], dumb.predict(part[FEATURE_COLS]))
        _append(split_name, "seasonal",     part[TARGET], predict_seasonal(month_means, part))
        _append(split_name, "RF (ours)",    part[TARGET], pipeline.predict(part[FEATURE_COLS]))

    if test is not None:
        _append("test", "dumb-mean",  test[TARGET], dumb.predict(test[FEATURE_COLS]))
        _append("test", "seasonal",   test[TARGET], predict_seasonal(month_means, test))
        _append("test", "RF (ours)",  test[TARGET], pipeline.predict(test[FEATURE_COLS]))

    return pd.DataFrame(rows)


def run_loso_cv(train_val: pd.DataFrame) -> pd.DataFrame:
    """Leave-one-station-out cross-validation on train+val to get mean ± std.

    Each fold holds out one station, trains on the rest. Reports fold-level
    MAE and R². The spread (std across folds) tells us how stable the model
    is across different urban typologies.

    Args:
        train_val: Combined train+val dataframe (do NOT include test).

    Returns:
        DataFrame with one row per station fold.
    """
    from split_data import make_loso_folds  # noqa: local import to avoid circular

    train_val = add_month_feature(train_val) if "month" not in train_val.columns else train_val
    folds = make_loso_folds(train_val)

    fold_rows = []
    for fold_train, fold_val in folds:
        held_station = fold_val["station_id"].iloc[0]
        p = build_pipeline()
        p.fit(fold_train[FEATURE_COLS], fold_train[TARGET])
        preds = p.predict(fold_val[FEATURE_COLS])
        fold_rows.append({
            "held_out_station": held_station,
            "n_val":            len(fold_val),
            "MAE":              round(mean_absolute_error(fold_val[TARGET], preds), 3),
            "R2":               round(r2_score(fold_val[TARGET], preds), 3),
        })

    results = pd.DataFrame(fold_rows)
    print(f"\nLOSO-CV results ({len(results)} folds):")
    print(results.to_markdown(index=False))
    print(f"\nCV MAE:  {results['MAE'].mean():.3f} ± {results['MAE'].std():.3f}")
    print(f"CV R²:   {results['R2'].mean():.3f} ± {results['R2'].std():.3f}")
    return results


def predict_with_uncertainty(
    pipeline: Pipeline,
    X:        pd.DataFrame,
    lo:       int = 5,
    hi:       int = 95,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return (point, lo, hi) predictions using tree quantiles of the forest.

    Cheap, calibration-free uncertainty from the existing Random Forest.
    Each tree votes independently; the inter-tree spread reflects the model's
    epistemic uncertainty. For Krakow: expect wider intervals in industrial
    zones and suburban areas far from training stations.

    Args:
        pipeline: Fitted sklearn Pipeline with RF as the final step.
        X:        Feature dataframe (must have FEATURE_COLS).
        lo:       Lower percentile for the prediction interval.
        hi:       Upper percentile.

    Returns:
        (point_prediction, lower_bound, upper_bound) — all shape (N,).
    """
    forest = pipeline.named_steps["model"]
    Xt = pipeline[:-1].transform(X[FEATURE_COLS])
    all_tree_preds = np.stack([t.predict(Xt) for t in forest.estimators_])
    return (
        all_tree_preds.mean(axis=0),
        np.percentile(all_tree_preds, lo, axis=0),
        np.percentile(all_tree_preds, hi, axis=0),
    )


# ── Persistence (save / load) ─────────────────────────────────────────────────

def save_pipeline(
    pipeline: Pipeline,
    X_val:    pd.DataFrame,
    path:     Path = MODEL_PATH,
) -> None:
    """Save the fitted Pipeline and run a round-trip predict check.

    Raises AssertionError if the loaded model doesn't reproduce in-memory
    predictions — the saved artifact would otherwise be fiction.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(pipeline, path)

    loaded   = joblib.load(path)
    expected = pipeline.predict(X_val[FEATURE_COLS])
    actual   = loaded.predict(X_val[FEATURE_COLS])
    assert np.allclose(expected, actual), \
        "saved pipeline doesn't reproduce in-memory predictions"

    print(f"saved {path} ({path.stat().st_size / 1024:.1f} KB)")
    print("round-trip predictions match in-memory: ✓")


# ── Entry point ───────────────────────────────────────────────────────────────

def main() -> None:
    train = pd.read_parquet(SPLIT_DIR / f"{SLUG}-train.parquet")
    val   = pd.read_parquet(SPLIT_DIR / f"{SLUG}-val.parquet")
    # NB — test is NOT loaded here. Final test metric is computed in the
    # notebook ONCE the model is locked (see notebooks/03-modelling.ipynb).

    train = add_month_feature(train)
    val   = add_month_feature(val)

    X_train, y_train = train[FEATURE_COLS], train[TARGET]
    X_val,   y_val   = val[FEATURE_COLS],   val[TARGET]

    print("fitting seasonal baseline…")
    month_means = fit_seasonal_baseline(train)

    print("fitting Pipeline on train…")
    np.random.seed(RANDOM_SEED)
    pipeline = train_baseline_model(X_train, y_train)

    print("\nMetrics (train + val — test NOT included):")
    report = compute_metrics_table(pipeline, train, val, month_means, test=None)
    print(report.to_markdown(index=False))

    save_pipeline(pipeline, val, MODEL_PATH)


if __name__ == "__main__":
    main()
