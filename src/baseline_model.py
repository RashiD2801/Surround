"""
baseline_model.py — baselines + first model for Krakow PM2.5 spatial prediction.

Reads the train/val CSVs produced by src/split_data.py, fits two baselines
and one Random Forest model, prints an honest metrics table, and saves the
model as a single sklearn Pipeline.

Run from project root:
    python src/baseline_model.py

Or import individual functions:
    from src.baseline_model import train_baseline_model, predict_with_uncertainty

Modelling decisions documented in docs/modelling-log.md.

Target:   pm25  (µg/m³ — daily PM2.5 at a station)
Input:    data/processed/krakow-pm25-{train,val,test}.csv

Feature strategy:
    Only land-use and temporal features are used — NOT lag features
    (pm25_lag1, pm25_lag3, etc.). Lag features require knowing the
    previous PM2.5 at the target location, which is unavailable for
    the 32,700 unmeasured grid cells at deployment time.
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

# ── Paths ─────────────────────────────────────────────────────────────────────
SPLIT_DIR  = Path("data/processed/")
MODEL_PATH = Path("models/baseline.joblib")
SLUG       = "krakow-pm25"

# ── Constants ─────────────────────────────────────────────────────────────────
RANDOM_SEED = 42
TARGET      = "pm25"

# Land use (500m radius) + seasonal control — all available at unmeasured grid cells.
# r005 = 500m buffer from Urban Atlas. r010+ deferred to Session 5 validation.
# month is the seasonal control: without it the model conflates winter heating
# signal with urban form signal (see modelling-log.md decision #4).
FEATURE_COLS = [
    "luse_r005_urban_continuous_pct",
    "luse_r005_urban_discontinuous_pct",
    "luse_r005_urban_isolated_pct",
    "luse_r005_urban_industrial_pct",
    "luse_r005_urban_infrastructure_pct",
    "luse_r005_urban_green_pct",
    "luse_r005_agriculture_pct",
    "luse_r005_forest_natural_pct",
    "luse_r005_wetland_pct",
    "luse_r005_water_pct",
    "luse_r005_seal_density",
    "luse_r005_green_pct",
    "luse_r005_urban_pct",
    "month",
    "mean_temp_monthly",
    "blh_monthly",
]

N_TREES  = 300
MIN_LEAF = 5


class FitResult(NamedTuple):
    """The trained pipeline plus a tidy metrics report."""
    pipeline: Pipeline
    metrics:  pd.DataFrame


# ── Baselines ─────────────────────────────────────────────────────────────────

def fit_dumb_baseline(X_train: pd.DataFrame, y_train: pd.Series) -> DummyRegressor:
    """Predict the training-set mean pm25 for every input — the unconditional floor."""
    dumb = DummyRegressor(strategy="mean")
    dumb.fit(X_train, y_train)
    return dumb


def fit_seasonal_baseline(train: pd.DataFrame) -> dict[int, float]:
    """Predict the training-set month-specific mean pm25.

    Captures Krakow's heating-season swing (Jan ~58 µg/m³ vs Aug ~12 µg/m³).
    A model that can't beat this isn't learning land use — it's re-discovering
    that January is polluted.

    Returns:
        dict mapping month (1-12) -> mean pm25 from training data.
    """
    return train.groupby("month")[TARGET].mean().to_dict()


def predict_seasonal(month_means: dict[int, float], df: pd.DataFrame) -> pd.Series:
    """Apply the seasonal-mean lookup to df['month']."""
    overall = np.mean(list(month_means.values()))
    return df["month"].map(month_means).fillna(overall)


# ── Model ─────────────────────────────────────────────────────────────────────

def build_pipeline(random_state: int = RANDOM_SEED) -> Pipeline:
    """Construct an unfitted sklearn Pipeline: impute -> scale -> RandomForest.

    Why Random Forest:
    - ~8,500 training rows x 13 features: large enough for RF, too small for DL.
    - Handles nonlinear land-use x season interactions.
    - Tree-quantile uncertainty available without extra libraries.
    - SHAP feature importances interpretable for planning analysts (Session 7).

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


def train_baseline_model(X_train: pd.DataFrame, y_train: pd.Series) -> Pipeline:
    """Fit the Pipeline on training data and return the fitted estimator.

    Args:
        X_train: Training features — must contain all FEATURE_COLS.
        y_train: Training target (pm25 in µg/m³).

    Returns:
        Fitted sklearn Pipeline.

    Raises:
        ValueError: If any FEATURE_COLS are missing from X_train.

    Example:
        >>> p = train_baseline_model(X_train, y_train)
        >>> preds = p.predict(X_val)
        >>> preds.shape == (len(X_val),)
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
    pipeline:    Pipeline,
    train:       pd.DataFrame,
    val:         pd.DataFrame,
    month_means: dict[int, float],
    test:        pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Build the honest metrics table — splits x models x MAE and R².

    Test rows are only computed if test is explicitly passed (model locked).
    Default call omits test — accidental test peeking is impossible at module level.
    """
    rows = []

    def _row(split, model, y_true, y_pred):
        rows.append({
            "split": split,
            "model": model,
            "MAE":   round(mean_absolute_error(y_true, y_pred), 2),
            "R2":    round(r2_score(y_true, y_pred), 3),
        })

    dumb = fit_dumb_baseline(train[FEATURE_COLS], train[TARGET])

    for split_name, part in [("train", train), ("val", val)]:
        _row(split_name, "dumb-mean",  part[TARGET], dumb.predict(part[FEATURE_COLS]))
        _row(split_name, "seasonal",   part[TARGET], predict_seasonal(month_means, part))
        _row(split_name, "RF (ours)",  part[TARGET], pipeline.predict(part[FEATURE_COLS]))

    if test is not None:
        _row("test", "dumb-mean",  test[TARGET], dumb.predict(test[FEATURE_COLS]))
        _row("test", "seasonal",   test[TARGET], predict_seasonal(month_means, test))
        _row("test", "RF (ours)",  test[TARGET], pipeline.predict(test[FEATURE_COLS]))

    return pd.DataFrame(rows)


def run_loso_cv(train_val: pd.DataFrame) -> pd.DataFrame:
    """Leave-one-station-out cross-validation on train+val to get mean +/- std.

    Args:
        train_val: Combined train+val dataframe (never include test).

    Returns:
        DataFrame with one row per station fold: held_out, n_val, MAE, R2.
    """
    from src.split_data import make_loso_folds

    folds = make_loso_folds(train_val)
    fold_rows = []
    for fold_train, fold_val in folds:
        held = fold_val["station_id"].iloc[0]
        p = build_pipeline()
        p.fit(fold_train[FEATURE_COLS], fold_train[TARGET])
        preds = p.predict(fold_val[FEATURE_COLS])
        fold_rows.append({
            "held_out": held,
            "n_val":    len(fold_val),
            "MAE":      round(mean_absolute_error(fold_val[TARGET], preds), 2),
            "R2":       round(r2_score(fold_val[TARGET], preds), 3),
        })

    results = pd.DataFrame(fold_rows).sort_values("MAE", ascending=False)
    print(f"\nLOSO-CV ({len(results)} folds):")
    print(results.to_string(index=False))
    print(f"\nCV MAE: {results['MAE'].mean():.2f} +/- {results['MAE'].std():.2f} µg/m³")
    print(f"CV R²:  {results['R2'].mean():.3f} +/- {results['R2'].std():.3f}")
    return results


def predict_with_uncertainty(
    pipeline: Pipeline,
    X: pd.DataFrame,
    lo: int = 5,
    hi: int = 95,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return (point, lower, upper) predictions using tree quantiles.

    Args:
        pipeline: Fitted sklearn Pipeline with RandomForest as final step.
        X: Feature dataframe with FEATURE_COLS.
        lo: Lower percentile for the prediction interval.
        hi: Upper percentile.

    Returns:
        Tuple of (point_prediction, lower_bound, upper_bound).
    """
    forest = pipeline.named_steps["model"]
    Xt = pipeline[:-1].transform(X[FEATURE_COLS])
    all_preds = np.stack([t.predict(Xt) for t in forest.estimators_])
    return (
        all_preds.mean(axis=0),
        np.percentile(all_preds, lo, axis=0),
        np.percentile(all_preds, hi, axis=0),
    )


# ── Persistence (save / load) ─────────────────────────────────────────────────

def save_pipeline(pipeline: Pipeline, X_val: pd.DataFrame, path: Path = MODEL_PATH) -> None:
    """Save the fitted Pipeline and run a round-trip predict check."""
    path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(pipeline, path)

    loaded   = joblib.load(path)
    expected = pipeline.predict(X_val[FEATURE_COLS])
    actual   = loaded.predict(X_val[FEATURE_COLS])
    assert np.allclose(expected, actual), \
        "saved pipeline doesn't reproduce in-memory predictions"

    print(f"saved {path} ({path.stat().st_size / 1024:.1f} KB)")
    print("round-trip predictions match in-memory: OK")


# ── Entry point ───────────────────────────────────────────────────────────────

def main() -> None:
    train = pd.read_csv(SPLIT_DIR / f"{SLUG}-train.csv")
    val   = pd.read_csv(SPLIT_DIR / f"{SLUG}-val.csv")
    # NB — test is NOT loaded here. Final test score computed in notebook once locked.

    print(f"train: {train.shape}  |  val: {val.shape}")

    print("\nFitting seasonal baseline...")
    month_means = fit_seasonal_baseline(train)

    print("Fitting Pipeline on train...")
    np.random.seed(RANDOM_SEED)
    pipeline = train_baseline_model(train[FEATURE_COLS], train[TARGET])

    print("\nMetrics (train + val — test NOT included):")
    report = compute_metrics_table(pipeline, train, val, month_means, test=None)
    print(report.to_string(index=False))

    save_pipeline(pipeline, val, MODEL_PATH)


if __name__ == "__main__":
    main()
