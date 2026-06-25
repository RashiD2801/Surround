# 05 · Evaluation Notebook — Scaffold

> Copy each cell into `notebooks/05-evaluation.ipynb`.
> Must be runnable end-to-end from a clean kernel.
> Every number it prints must match `docs/session 5/evaluation-report.md`.
> **Track A only** — cells B1–B5 (Track B) are not applicable.

---

## Cell 1 — Markdown: title & purpose

```markdown
# Evaluation — Krakow PM2.5 Spatial Regression

**Purpose:** judge the Random Forest model from Session 4 against the
success criteria from the Session 1 problem brief. Produce a defensible
verdict — deploy, iterate, or stop — with the evidence behind it.

**Track:** A — model

**Inputs:**
- `models/baseline.joblib` — the locked Random Forest Pipeline
- `data/processed/krakow-pm25-test.csv` — the sacred test set (nowa_huta + zloty_rog)
- `data/processed/krakow-pm25-train.csv` — for baseline refitting
- `data/processed/krakow-pm25-val.csv` — for uncertainty checks

**Outputs:**
- `docs/session 5/evaluation-report.md` — the verdict
- `docs/session 5/failure-gallery.md` — 6 diagnosed failure cases
- `docs/session 5/evaluation-log.md` — every test run
```

---

## Cell 2 — Imports & config

```python
import sys
sys.path.insert(0, "../src")

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
import joblib
from sklearn.metrics import mean_absolute_error, r2_score

from baseline_model import FEATURE_COLS, TARGET, predict_seasonal, fit_seasonal_baseline, predict_with_uncertainty

RANDOM_SEED = 42
np.random.seed(RANDOM_SEED)

SPLIT_DIR  = Path("../data/processed/")
MODEL_PATH = Path("../models/baseline.joblib")
```

---

## Cell 3 — Markdown: success criteria

```markdown
## The bar we set in Session 1

| # | Success criterion | How it's measured | The bar |
|---|---|---|---|
| 1 | Establish land use–PM2.5 relationship | R² on held-out test stations | ≥ 0.40 |
| 2 | Beat naive baseline | Model MAE vs seasonal-mean baseline | Model MAE < seasonal MAE |
| 3 | Practically useful for planning | MAE in µg/m³ | < 12 µg/m³ |
```

---

## Cell 4 — Results-vs-criteria table

```python
# Fill from actual test metrics (computed in cells below)
criteria = pd.DataFrame([
    {"criterion": "R² ≥ 0.40",            "target": "≥ 0.40",      "result": "0.639",          "verdict": "met"},
    {"criterion": "Beat seasonal baseline", "target": "MAE < 10.24", "result": "9.96 (Δ=2.7%)",  "verdict": "partial"},
    {"criterion": "MAE < 12 µg/m³",        "target": "< 12 µg/m³",  "result": "9.96 µg/m³",    "verdict": "met"},
])
print(criteria.to_markdown(index=False))
```

---

## Cell A1 — Load model and test set

```python
model = joblib.load(MODEL_PATH)
train = pd.read_csv(SPLIT_DIR / "krakow-pm25-train.csv")
val   = pd.read_csv(SPLIT_DIR / "krakow-pm25-val.csv")
test  = pd.read_csv(SPLIT_DIR / "krakow-pm25-test.csv")

X_test, y_test = test[FEATURE_COLS], test[TARGET]
y_pred = model.predict(X_test)

month_means = fit_seasonal_baseline(train)

test_mae = mean_absolute_error(y_test, y_pred)
test_r2  = r2_score(y_test, y_pred)
seas_mae = mean_absolute_error(y_test, predict_seasonal(month_means, test))
dumb_mae = mean_absolute_error(y_test, [train[TARGET].mean()] * len(test))

print(f"test rows: {len(test):,}  (stations: {sorted(test['station_id'].unique())})")
print(f"dumb-mean MAE:  {dumb_mae:.2f} µg/m³")
print(f"seasonal  MAE:  {seas_mae:.2f} µg/m³")
print(f"RF model  MAE:  {test_mae:.2f} µg/m³   R²: {test_r2:.3f}")
print(f"Improvement over seasonal: {(seas_mae - test_mae) / seas_mae:.1%}")
```

---

## Cell A2 — Per-segment error (where does it break?)

```python
test_aug = test.assign(pred=y_pred, abs_err=np.abs(y_pred - y_test))

# Per-station
print("Per-station MAE on test:")
print(test_aug.groupby("station_id")["abs_err"].agg(["mean","count"])
      .rename(columns={"mean":"MAE","count":"n"}).round(2))

# Per-season
test_aug["season"] = test_aug["month"].map({
    12:"Winter",1:"Winter",2:"Winter",
    3:"Spring",4:"Spring",5:"Spring",
    6:"Summer",7:"Summer",8:"Summer",
    9:"Autumn",10:"Autumn",11:"Autumn"
})
print("\nPer-season MAE on test:")
print(test_aug.groupby("season")["abs_err"].agg(["mean","count"])
      .rename(columns={"mean":"MAE","count":"n"}).round(2))

# Worst individual predictions
print("\nTop 5 worst predictions:")
print(test_aug.nlargest(5,"abs_err")[["station_id","year","month","pm25","pred","abs_err"]].round(2).to_string(index=False))
```

---

## Cell A3 — Stress tests

```python
X_test_orig = test[FEATURE_COLS]
base_mae = mean_absolute_error(y_test, model.predict(X_test_orig))
print(f"Baseline MAE (no stress): {base_mae:.2f}\n")

stresses = {
    "drop month":           lambda X: X.assign(month=np.nan),
    "20% NaN urban_pct":    lambda X: X.assign(**{"luse_r005_urban_pct": X["luse_r005_urban_pct"].where(
                                np.random.rand(len(X)) > 0.2, np.nan)}),
    "force all-winter":     lambda X: X.assign(month=12),
    "land-use shift +0.1":  lambda X: X.assign(**{c: (X[c]+0.1).clip(0,1) for c in FEATURE_COLS if c.startswith("luse")}),
}

for name, fn in stresses.items():
    try:
        X_s = fn(X_test_orig.copy())
        mae = mean_absolute_error(y_test, model.predict(X_s))
        status = "OK" if mae < base_mae * 1.1 else f"DEGRADED +{mae-base_mae:.2f}"
        print(f"{name:25s}  MAE {mae:.2f}  [{status}]")
    except Exception as e:
        print(f"{name:25s}  CRASHED: {type(e).__name__}")
```

---

## Cell A4 — Confidence / uncertainty intervals

```python
point, lo, hi = predict_with_uncertainty(model, test)
coverage = float(np.mean((y_test.values >= lo) & (y_test.values <= hi)))
width = (hi - lo).mean()
print(f"90% interval coverage on test: {coverage:.1%}  (target ≥ 85%)")
print(f"Mean interval width: {width:.1f} µg/m³")
if coverage < 0.85:
    print("WARNING: Under-coverage — intervals are overconfident. Do NOT show in dashboard.")
```

---

## Cell A5 — Feature importance

```python
importances = pd.Series(
    model.named_steps["model"].feature_importances_,
    index=FEATURE_COLS
).sort_values(ascending=False)
print("Feature importances (RF MDI):")
print(importances.round(3).to_string())
print(f"\nmonth importance: {importances['month']:.1%}")
print(f"All land use:     {importances.drop('month').sum():.1%}")
```

---

## Cell A6 — Systematic bias

```python
residuals = y_test.values - y_pred
print(f"Mean residual: {residuals.mean():.2f} µg/m³  (+ means under-prediction)")
print(f"Std residual:  {residuals.std():.2f} µg/m³")
test_aug["residual"] = residuals
print("\nMean residual by season:")
print(test_aug.groupby("season")["residual"].mean().round(2))
```

---

## Cell S1 — Markdown: the verdict

```markdown
## The verdict

- **Result vs criteria:** met 2 of 3 · criterion 2 (beat seasonal) partial — 2.7% margin
- **Where it fails:** winter MAE 16.28 µg/m³ (1.6× aggregate) · uncertainty intervals 45.7% coverage
- **Compared to what:** RF 9.96 vs seasonal 10.24 (+2.7%) vs dumb-mean 18.24 (+45%)
- **Confidence:** 90% coverage 45.7% · LOSO-CV 11.15 ± 1.46 µg/m³ · ~75% overall
- **Recommendation:** ITERATE — add ERA5 BLH + temperature to FEATURE_COLS
- **What we are NOT claiming:** causal; winter reliable; uncertainty intervals usable; land use drives the prediction
```

---

## Cell S2 — Review the process

```markdown
## What would we redo if we started over Monday?

- **Weakest link:** starting from daily data — the aggregation to monthly was done after the fact; should have been designed at S3.
- **The shortcut:** using Urban Atlas land use only (no ERA5 weather); the modelling log planned ERA5 features in S4 but they weren't in the final training data.
- **Untested assumption:** that 7 stations are sufficient to learn spatial PM2.5 patterns. Feature importance (93.6% month) suggests they are not.
- **The thing we avoided looking at:** year-by-year drift (is 2024 different from 2019 post-coal-ban?). Check before S6 retraining.
```

---

## Reproducibility check

1. Restart kernel → Run All — no errors
2. Every number in `evaluation-report.md` matches what this notebook prints
3. Read "what we are NOT claiming" aloud — list four without checking
4. State verdict in one sentence with confidence
