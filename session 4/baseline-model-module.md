# `src/baseline_model.py` — Module Template

> Copy this file as the skeleton of `src/baseline_model.py` in your repo.
> This is the **promoted** version of your modelling code — typed,
> documented, with the `sklearn.Pipeline` as the artifact.
>
> **Why this matters for non-CS students:** in S5 you'll wrap this model
> in orchestration. In S6 you'll stress-test it. In S7 you'll load it
> behind a UI. All three sessions read this file. If it's a tangle of
> notebook cells, every downstream session breaks.

---

## The full template

Save the block below as `src/baseline_model.py`:

```python
"""
baseline_model.py — baselines + first model for [dataset name].

Reads the train / val / test parquets produced by `src/split_data.py`,
fits at least two baselines and one defensible model, prints an honest
metrics table, and saves the model as a single sklearn Pipeline.

Run from project root:
    python src/baseline_model.py

Or import the training function:
    from src.baseline_model import train_baseline_model

Modelling decisions are documented in `docs/modelling-log.md`.
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

# Paths — relative to project root.
SPLIT_DIR = Path("data/processed/")
MODEL_PATH = Path("models/baseline.joblib")
SLUG = "your-dataset"

# Constants — every magic number named here.
RANDOM_SEED = 42
TARGET = "temp_c"
FEATURE_COLS = [
    "hour_of_day",
    "month",
    "lat",
    "lon",
    "temp_anomaly_c_vs_station_median",
]
N_TREES = 200
MIN_LEAF = 5


class FitResult(NamedTuple):
    """The trained pipeline plus a tidy metrics report."""

    pipeline: Pipeline
    metrics: pd.DataFrame


# ----------------------------------------------------------------------
# Baselines
# ----------------------------------------------------------------------

def fit_dumb_baseline(X_train: pd.DataFrame, y_train: pd.Series) -> DummyRegressor:
    """Predict the training-set mean for every input.

    The floor. Anything not beating this is worse than guessing.
    """
    dumb = DummyRegressor(strategy="mean")
    dumb.fit(X_train, y_train)
    return dumb


def persistence_predict(df_part: pd.DataFrame, target: str = TARGET) -> pd.Series:
    """Predict y_t = y_{t-1}, within each station.

    Returns a Series aligned with df_part's index. NaN where t-1 doesn't
    exist (first row per station).
    """
    sorted_part = df_part.sort_values("timestamp")
    return sorted_part.groupby("station_id")[target].shift(1).reindex(df_part.index)


# ----------------------------------------------------------------------
# Model
# ----------------------------------------------------------------------

def build_pipeline(random_state: int = RANDOM_SEED) -> Pipeline:
    """Construct the unfit sklearn Pipeline.

    Same Pipeline shape gets re-used for CV folds and for the final fit
    on train. Re-building per fold avoids accidental state leakage.

    Returns:
        An unfitted sklearn Pipeline ready for `.fit(X, y)`.
    """
    return Pipeline(
        steps=[
            ("impute", SimpleImputer(strategy="median")),
            ("scale", StandardScaler()),
            (
                "model",
                RandomForestRegressor(
                    n_estimators=N_TREES,
                    min_samples_leaf=MIN_LEAF,
                    random_state=random_state,
                    n_jobs=-1,
                ),
            ),
        ]
    )


def train_baseline_model(
    X_train: pd.DataFrame, y_train: pd.Series
) -> Pipeline:
    """Fit the Pipeline on train. Return the fitted estimator.

    Args:
        X_train: Training features. No NaNs in `FEATURE_COLS` ideally;
            the imputer is the safety net.
        y_train: Training target.

    Returns:
        A fitted sklearn Pipeline ready for `.predict(X)`.

    Example:
        >>> p = train_baseline_model(X_train, y_train)
        >>> preds = p.predict(X_val)
        >>> preds.shape == y_val.shape
        True
    """
    if set(FEATURE_COLS) - set(X_train.columns):
        missing = set(FEATURE_COLS) - set(X_train.columns)
        raise ValueError(f"Missing feature columns: {missing}")

    pipeline = build_pipeline()
    pipeline.fit(X_train[FEATURE_COLS], y_train)
    return pipeline


# ----------------------------------------------------------------------
# Evaluation
# ----------------------------------------------------------------------

def compute_metrics_table(
    pipeline: Pipeline,
    train: pd.DataFrame,
    val: pd.DataFrame,
    test: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Build the honest metrics table — splits × models × spread.

    Test split is computed ONLY if `test` is provided AND the model is
    locked. Call once at the very end of your workflow.
    """
    rows = []

    # Dumb baseline
    dumb = fit_dumb_baseline(train[FEATURE_COLS], train[TARGET])
    rows.append({"split": "train", "model": "dumb-mean",   "MAE": mean_absolute_error(train[TARGET], dumb.predict(train[FEATURE_COLS]))})
    rows.append({"split": "val",   "model": "dumb-mean",   "MAE": mean_absolute_error(val[TARGET],   dumb.predict(val[FEATURE_COLS]))})

    # Persistence baseline (val only — train persistence is uninteresting)
    pers_val = persistence_predict(val)
    mask = pers_val.notna()
    rows.append({"split": "val", "model": "persistence", "MAE": mean_absolute_error(val.loc[mask, TARGET], pers_val[mask])})

    # The model
    rows.append({"split": "train", "model": "ours", "MAE": mean_absolute_error(train[TARGET], pipeline.predict(train[FEATURE_COLS]))})
    rows.append({"split": "val",   "model": "ours", "MAE": mean_absolute_error(val[TARGET],   pipeline.predict(val[FEATURE_COLS]))})
    rows.append({"split": "val",   "model": "ours-R2", "MAE": r2_score(val[TARGET], pipeline.predict(val[FEATURE_COLS]))})

    if test is not None:
        # Touched ONCE — model must be locked.
        rows.append({"split": "test", "model": "dumb-mean",   "MAE": mean_absolute_error(test[TARGET], dumb.predict(test[FEATURE_COLS]))})
        pers_test = persistence_predict(test)
        m_t = pers_test.notna()
        rows.append({"split": "test", "model": "persistence", "MAE": mean_absolute_error(test.loc[m_t, TARGET], pers_test[m_t])})
        rows.append({"split": "test", "model": "ours",        "MAE": mean_absolute_error(test[TARGET], pipeline.predict(test[FEATURE_COLS]))})

    return pd.DataFrame(rows)


def predict_with_uncertainty(
    pipeline: Pipeline, X: pd.DataFrame, lo: int = 5, hi: int = 95
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return (point, lo, hi) predictions using the trees of the forest.

    Cheap, defensible uncertainty: poll every tree, take quantiles.
    For non-tree models, swap for conformal prediction or bootstrap.
    """
    forest = pipeline.named_steps["model"]
    Xt = pipeline[:-1].transform(X[FEATURE_COLS])
    all_preds = np.stack([t.predict(Xt) for t in forest.estimators_])
    return (
        all_preds.mean(axis=0),
        np.percentile(all_preds, lo, axis=0),
        np.percentile(all_preds, hi, axis=0),
    )


# ----------------------------------------------------------------------
# Persistence (save / load)
# ----------------------------------------------------------------------

def save_pipeline(pipeline: Pipeline, X_val: pd.DataFrame, path: Path = MODEL_PATH) -> None:
    """Save the fitted Pipeline and run a round-trip predict check.

    Raises if the loaded model doesn't reproduce in-memory predictions.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(pipeline, path)

    loaded = joblib.load(path)
    expected = pipeline.predict(X_val[FEATURE_COLS])
    actual = loaded.predict(X_val[FEATURE_COLS])
    assert np.allclose(expected, actual), \
        "saved pipeline doesn't reproduce in-memory predictions"

    print(f"saved {path} ({path.stat().st_size / 1024:.1f} KB)")
    print("round-trip predictions match in-memory: ✓")


# ----------------------------------------------------------------------
# Entry point
# ----------------------------------------------------------------------

def main() -> None:
    train = pd.read_parquet(SPLIT_DIR / f"{SLUG}-train.parquet")
    val   = pd.read_parquet(SPLIT_DIR / f"{SLUG}-val.parquet")
    # NB — test is NOT loaded here. The script computes train + val metrics
    # only. Final test metric is computed by the notebook ONCE the model
    # is locked, or by passing `test=...` explicitly to compute_metrics_table.

    X_train, y_train = train[FEATURE_COLS], train[TARGET]
    X_val,   y_val   = val[FEATURE_COLS],   val[TARGET]

    print("fitting Pipeline on train…")
    pipeline = train_baseline_model(X_train, y_train)

    print("\nMetrics (train + val):")
    report = compute_metrics_table(pipeline, train, val, test=None)
    print(report.to_markdown(index=False))

    save_pipeline(pipeline, val, MODEL_PATH)


if __name__ == "__main__":
    main()
```

---

## Why this structure

### One Pipeline per model
The whole preprocess-plus-model lives in one `sklearn.Pipeline`. Save it,
load it, predict — the same imputation and scaling that ran at train
time run at predict time. This kills the most common train-vs-serve skew.

### Baselines as first-class functions
`fit_dumb_baseline` and `persistence_predict` are named, importable, and
testable. They're not throwaway notebook cells. They will be re-imported
in S6 when you stress-test, and in S7 when you fall back to the baseline
on out-of-scope inputs.

### `compute_metrics_table` returns a `DataFrame`
A tidy table is the right shape for the model card. The function is
intentionally written so test metrics are opt-in — the default skips
test. You can't accidentally compute test by importing the module.

### `save_pipeline` runs the round-trip
The round-trip predict check is non-negotiable. If the loaded model
doesn't match the in-memory one, your saved artifact is fiction. Catch
that here, not in S7 when deployment breaks.

### `predict_with_uncertainty` is its own function
Uncertainty is a discipline, not an afterthought. Having a dedicated
function makes it obvious which model can emit intervals and which can't.

---

## Adapting for your problem

### Classification

Swap the model + metrics:

```python
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix

# In build_pipeline:
("model", RandomForestClassifier(n_estimators=N_TREES, random_state=RANDOM_SEED))

# In compute_metrics_table — return precision / recall / F1 per class.
```

### Forecasting (h-step ahead)

```python
# Reframe as supervised: features at t, target at t+h.
df = df.sort_values("timestamp")
df["temp_c_t_plus_24h"] = df.groupby("station_id")["temp_c"].shift(-24)
df = df.dropna(subset=["temp_c_t_plus_24h"])
TARGET = "temp_c_t_plus_24h"
```

### When the data is imbalanced

```python
from sklearn.metrics import precision_recall_curve, average_precision_score

# Always use PR-AUC for imbalanced classification, not ROC-AUC.
```

### When you want explainability

```python
import shap

# After training:
explainer = shap.TreeExplainer(pipeline.named_steps["model"])
# Pre-transform features for the explainer.
Xt = pipeline[:-1].transform(X_val[FEATURE_COLS])
shap_values = explainer.shap_values(Xt)
shap.summary_plot(shap_values, Xt, feature_names=FEATURE_COLS)
```

---

## Pre-commit check

Before you push:

- [ ] `python src/baseline_model.py` runs without error.
- [ ] The round-trip check prints `✓`.
- [ ] The metrics table shows at least two baselines and the model.
- [ ] The model beats persistence on val. *(If not — write a modelling-log
      entry explaining why, and either swap the model or accept the
      finding.)*
- [ ] You did NOT compute test metrics in this run.
- [ ] All modelling decisions in this file are logged in
      `docs/modelling-log.md`.
