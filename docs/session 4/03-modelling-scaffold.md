# 03 · Modelling Notebook — Scaffold

> Copy each cell into a new Jupyter notebook in your repo at
> `notebooks/03-modelling.ipynb`. Adapt to your dataset.
>
> Your final notebook must be runnable end-to-end from a clean kernel.
> The modelling logic you settle on here gets **promoted** into
> `src/split_data.py` and `src/baseline_model.py` once it's stable.

---

## Cell 1 — Markdown: title & purpose

```markdown
# Modelling — [primary dataset name]

**Purpose:** take the cleaned parquet from Session 3 and produce a
defensible baseline + one honest model, with a model card.

**Input:** `data/processed/<dataset>-clean.parquet` (S3 contract)
**Outputs:**
- `data/processed/<dataset>-{train,val,test}.parquet` (split outputs)
- `models/baseline.joblib` (saved sklearn Pipeline)
- `docs/model-cards/<model>.md` (the certificate)
- `docs/modelling-log.md` (every decision)

This notebook is the **exploratory** layer. The stable logic gets
promoted to `src/split_data.py` and `src/baseline_model.py`.
```

## Cell 2 — Imports & deterministic config

```python
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

import joblib
from sklearn.dummy import DummyRegressor
from sklearn.ensemble import RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import GroupKFold, TimeSeriesSplit
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

CLEAN_PATH = Path("../data/processed/your-dataset-clean.parquet")
SPLIT_DIR = Path("../data/processed/")
MODEL_PATH = Path("../models/baseline.joblib")
RANDOM_SEED = 42

MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
np.random.seed(RANDOM_SEED)
```

## Cell 3 — Load cleaned data + invariants

```python
df = pd.read_parquet(CLEAN_PATH)
print(f"Shape: {df.shape}")
print(f"Time range: {df['timestamp'].min()} → {df['timestamp'].max()}")
print(f"Unique stations: {df['station_id'].nunique()}")
df.head()
```

> **Discipline:** start every modelling notebook by re-stating the contract
> from S3. If anything looks off (rows changed, time range surprises you),
> stop and check `data-cleaning-log.md`.

---

## Task 1 — Split

### Cell 4 — Markdown: split plan

```markdown
## Task 1: Split

**Decision: which leakage type matters most for this dataset?**

- Temporal? (rows from the same day are nearly identical)
- Spatial? (rows from nearby locations are nearly identical)
- Group? (rows from the same entity are nearly identical)

**Chosen strategy:** [name + 1-sentence reason]
**Train window / set:** [...]
**Val window / set:** [...]
**Test window / set:** [...]
**Logged in:** `docs/modelling-log.md` decision #1.
```

### Cell 5 — Temporal split (example)

```python
df = df.sort_values("timestamp").reset_index(drop=True)

train_end = pd.Timestamp("2023-08-01", tz="UTC")
val_end   = pd.Timestamp("2023-09-01", tz="UTC")

train = df[df["timestamp"] < train_end].copy()
val   = df[(df["timestamp"] >= train_end) & (df["timestamp"] < val_end)].copy()
test  = df[df["timestamp"] >= val_end].copy()

# Leakage assertions — these are the contract.
assert train["timestamp"].max() < val["timestamp"].min(), \
    "temporal leak: train extends into val"
assert val["timestamp"].max() < test["timestamp"].min(), \
    "temporal leak: val extends into test"

print(f"train: {len(train):,} rows · {train['timestamp'].min()} → {train['timestamp'].max()}")
print(f"val:   {len(val):,} rows · {val['timestamp'].min()} → {val['timestamp'].max()}")
print(f"test:  {len(test):,} rows · {test['timestamp'].min()} → {test['timestamp'].max()}")
```

> **Why the asserts:** if either ever fires, the evaluation downstream is
> fiction. They run at split time so failure is loud and local.

### Cell 6 — Write the split parquets

```python
for name, part in [("train", train), ("val", val), ("test", test)]:
    out = SPLIT_DIR / f"your-dataset-{name}.parquet"
    part.to_parquet(out, index=False)
    print(f"Wrote {out} ({len(part):,} rows · {out.stat().st_size / 1024:.0f} KB)")
```

> **The test parquet is now sacred.** Don't open it again until the model
> is locked. Don't peek. Don't plot. Don't `.head()`.

---

## Task 2 — Baselines (the floor)

### Cell 7 — Markdown: baseline plan

```markdown
## Task 2: Baselines

We compute at least TWO baselines before any "real" model:

1. **Dumb:** predict the training mean.
2. **Persistence:** predict y_{t-1} (only valid for time series).
3. **Spatial nearest:** mean of k nearest measured points.
4. **Domain heuristic:** [the rule of thumb your field already uses].

If our model can't beat persistence (or the domain heuristic), we don't
have a model — we have a worse inertia detector.
```

### Cell 8 — Define features + target

```python
TARGET = "temp_c"
FEATURE_COLS = [
    "hour_of_day", "month", "lat", "lon",
    "temp_anomaly_c_vs_station_median",
]

X_train, y_train = train[FEATURE_COLS], train[TARGET]
X_val,   y_val   = val[FEATURE_COLS],   val[TARGET]
X_test,  y_test  = test[FEATURE_COLS],  test[TARGET]
```

### Cell 9 — Dumb baseline (mean)

```python
dumb = DummyRegressor(strategy="mean")
dumb.fit(X_train, y_train)

dumb_train_mae = mean_absolute_error(y_train, dumb.predict(X_train))
dumb_val_mae   = mean_absolute_error(y_val,   dumb.predict(X_val))

print(f"dumb · train MAE = {dumb_train_mae:.3f}")
print(f"dumb · val   MAE = {dumb_val_mae:.3f}")
```

### Cell 10 — Persistence baseline (time series)

```python
# Within each station, shift y by 1 hour. Drop the first row per station.
def persistence_predict(df_part: pd.DataFrame) -> pd.Series:
    return df_part.sort_values("timestamp").groupby("station_id")[TARGET].shift(1)

val_pers = persistence_predict(val)
mask = val_pers.notna()
pers_val_mae = mean_absolute_error(y_val[mask], val_pers[mask])
print(f"persistence · val MAE = {pers_val_mae:.3f}  (on {mask.sum():,} of {len(val):,} rows)")
```

> **Discipline:** persistence drops the first row per group. The MAE is
> only computed where prediction is defined. Note the denominator.

---

## Task 3 — One defensible model

### Cell 11 — Markdown: model choice

```markdown
## Task 3: Model

**Three questions before picking a technique:**

1. **Problem shape:** [regression / classification / forecasting / ranking]
2. **Data size & dim:** [N rows × D features → start boring]
3. **Will I be asked to explain this?** [yes → linear / trees / GAM]

**Chosen technique:** [e.g. RandomForestRegressor]
**Why this and not the simpler alternative:** [...]
**Why this and not the deeper alternative:** [...]
**Logged in:** `docs/modelling-log.md` decision #2.
```

### Cell 12 — Build the Pipeline + fit on train

```python
pipeline = Pipeline([
    ("impute", SimpleImputer(strategy="median")),
    ("scale",  StandardScaler()),
    ("model",  RandomForestRegressor(
        n_estimators=200,
        min_samples_leaf=5,
        random_state=RANDOM_SEED,
        n_jobs=-1,
    )),
])

pipeline.fit(X_train, y_train)
```

> **Why a `Pipeline`:** preprocessing + model in one object. The same
> imputation and scaling run at predict time, eliminating the most
> common train-vs-serve skew.

### Cell 13 — Score model on train + val (NOT test yet)

```python
model_train_mae = mean_absolute_error(y_train, pipeline.predict(X_train))
model_val_mae   = mean_absolute_error(y_val,   pipeline.predict(X_val))
model_val_r2    = r2_score(y_val, pipeline.predict(X_val))

print(f"model · train MAE = {model_train_mae:.3f}")
print(f"model · val   MAE = {model_val_mae:.3f}")
print(f"model · val   R²  = {model_val_r2:.3f}")
```

### Cell 14 — Honest metrics table (train + val only)

```python
report = pd.DataFrame({
    "split":  ["train", "val", "val"],
    "metric": ["MAE",   "MAE", "MAE"],
    "what":   ["model", "model", "persistence"],
    "value":  [model_train_mae, model_val_mae, pers_val_mae],
})
print(report.to_markdown(index=False))
```

> **Discipline:** you do NOT compute test metrics yet. Test is sacred
> until the model is locked. Tune hyperparameters against val.

---

## Task 4 — Assess (the honest part)

### Cell 15 — Cross-validation with the right splitter

```python
# Use TimeSeriesSplit so each fold trains on the past, tests on the future.
tscv = TimeSeriesSplit(n_splits=5)

fold_maes = []
df_train_for_cv = train.reset_index(drop=True)
X_cv, y_cv = df_train_for_cv[FEATURE_COLS], df_train_for_cv[TARGET]

for fold, (tr_idx, te_idx) in enumerate(tscv.split(X_cv)):
    p = Pipeline([
        ("impute", SimpleImputer(strategy="median")),
        ("scale",  StandardScaler()),
        ("model",  RandomForestRegressor(
            n_estimators=200, min_samples_leaf=5,
            random_state=RANDOM_SEED, n_jobs=-1,
        )),
    ])
    p.fit(X_cv.iloc[tr_idx], y_cv.iloc[tr_idx])
    mae = mean_absolute_error(y_cv.iloc[te_idx], p.predict(X_cv.iloc[te_idx]))
    fold_maes.append(mae)
    print(f"fold {fold}: MAE = {mae:.3f}")

print(f"\ncv MAE = {np.mean(fold_maes):.3f} ± {np.std(fold_maes):.3f}")
```

### Cell 16 — Uncertainty intervals (from RandomForest trees)

```python
all_tree_preds = np.stack([t.predict(X_val) for t in pipeline.named_steps["model"].estimators_])
y_lo = np.percentile(all_tree_preds, 5, axis=0)
y_hi = np.percentile(all_tree_preds, 95, axis=0)

coverage = float(np.mean((y_val.values >= y_lo) & (y_val.values <= y_hi)))
print(f"Coverage of 90% interval on val: {coverage:.2%}")
```

> **Master's-level:** a model that outputs uncertainty is worth more than
> one that outputs only a point. Aim for ≥85% coverage on the 90% interval.

### Cell 17 — Per-segment performance (where does it break?)

```python
val_pred = pipeline.predict(X_val)
val_with_pred = val.assign(pred=val_pred, abs_err=np.abs(val_pred - y_val))

per_station = val_with_pred.groupby("station_id")["abs_err"].mean().sort_values(ascending=False)
print("Per-station MAE on val:")
print(per_station.head(10))
```

> **This is where Session 6 starts.** Note the worst stations now — they
> will become the failure gallery's first entries.

---

## Task 5 — Lock the model. Touch test ONCE.

### Cell 18 — Save the pipeline

```python
joblib.dump(pipeline, MODEL_PATH)

# Round-trip check.
loaded = joblib.load(MODEL_PATH)
assert np.allclose(loaded.predict(X_val), pipeline.predict(X_val)), \
    "saved pipeline doesn't reproduce in-memory predictions"
print(f"Saved {MODEL_PATH} ({MODEL_PATH.stat().st_size / 1024:.1f} KB)")
print("Round-trip predictions match in-memory: ✓")
```

### Cell 19 — Final test score (run this ONCE, at the very end)

```python
# Model is now locked. Hyperparameters chosen. Code committed.
# The next line is the only place we touch test in this notebook.

test_mae = mean_absolute_error(y_test, pipeline.predict(X_test))
test_pers_mae = mean_absolute_error(
    y_test[persistence_predict(test).notna()],
    persistence_predict(test).dropna(),
)

print(f"FINAL test MAE (model):       {test_mae:.3f}")
print(f"FINAL test MAE (persistence): {test_pers_mae:.3f}")
print(f"FINAL test improvement:       {(test_pers_mae - test_mae) / test_pers_mae:.1%}")
```

> **This is the number that goes in the model card.** If you re-run this
> cell with a tweak elsewhere, you've contaminated test. Be honest.

---

## Task 6 — Bridge to the modules

### Cell 20 — Markdown: what gets promoted

```markdown
## What gets promoted to `src/`?

Two modules emerge:

**`src/split_data.py`** — the splitting function, the leakage assertions,
and the parquet writes. Importable from this notebook.

**`src/baseline_model.py`** — the Pipeline factory, the training function,
the joblib save with round-trip check.

After promotion, this notebook calls `from src.split_data import
make_splits` and `from src.baseline_model import train_baseline_model`
instead of duplicating the logic.
```

---

## Reproducibility check (before committing)

1. `Restart kernel` in `03-modelling.ipynb`.
2. `Run all` — every cell should run without error.
3. From terminal: `python src/split_data.py` — confirm parquets regenerate
   identically.
4. From terminal: `python src/baseline_model.py` — confirm joblib regenerates.
5. Confirm:
   ```python
   import joblib
   model = joblib.load("models/baseline.joblib")
   pred = model.predict(X_val)  # should produce the same values as in the notebook
   ```
6. Re-read the model card. Are the metrics in the card the same as the
   notebook's printed metrics?

If any step fails, the modelling is not done.
