# Session 4 — Continuation Notes
# Last updated: 2026-05-28

---

## What has been done

All session 4 template files have been filled with Krakow-specific content
and saved to `Surround/session 4/`:

| File | What it is | Status |
|---|---|---|
| `split_data.py` | Leakage-safe leave-one-station-out splitter | DONE |
| `baseline_model.py` | Dumb mean + seasonal baselines + RF pipeline + LOSO-CV + uncertainty | DONE |
| `modelling-log.md` | 8 modelling decisions fully logged | DONE |
| `model-card.md` | All 8 Mitchell et al. sections filled for krakow-pm25-spatial-rf-v1 | DONE |
| `pipeline-architecture-v2.md` | Mermaid diagram updated, all implemented boxes have file paths | DONE |
| `03-modelling.ipynb` | 20-cell Jupyter notebook following the scaffold | DONE |
| `evaluation-checklist.md` | Reference checklist — already project-agnostic, no filling needed | DONE |
| `README.md` | Session 4 overview — pre-existing, not modified | DONE |

---

## What still needs to be done

### 1. Push session 4 files to the repo

These files currently live only in the local `session 4/` folder.
They need to be copied into the correct repo directories and committed:

```
session 4/split_data.py          → src/split_data.py
session 4/baseline_model.py      → src/baseline_model.py
session 4/03-modelling.ipynb     → notebooks/03-modelling.ipynb
session 4/modelling-log.md       → docs/modelling-log.md
session 4/model-card.md          → docs/model-cards/krakow-pm25-spatial-rf-v1.md
session 4/pipeline-architecture-v2.md → docs/pipeline-architecture-v2.md
```

### 2. Feature extraction (Session 3 remainder — prerequisite for Session 4)

`split_data.py` and `baseline_model.py` both read from:
`data/processed/training_data.parquet`

This file does not exist yet. It requires:
- `notebooks/03-feature-extraction.ipynb` to be run (calculates NDVI, NDBI,
  road density, building density from Sentinel-2/OSM/ERA5)
- The spatial join of those features onto `aqicn_monthly.csv`

**Until feature extraction is done, the notebook and Python scripts will fail
at the data loading step.**

### 3. Fill in the [TBD] cells in model-card.md and modelling-log.md

Once the model is trained on real data, replace all `[TBD]` entries in:
- `docs/model-cards/krakow-pm25-spatial-rf-v1.md` — section 7.1 metrics table
- `docs/modelling-log.md` — the honest metrics table at the bottom

The values to fill in come from the notebook cell outputs (c13, c15, c19).

### 4. Run the pre-commit ritual

From project root, in order:
```powershell
python src/split_data.py           # produces three parquets
python src/baseline_model.py       # produces models/baseline.joblib
# open notebooks/03-modelling.ipynb → Restart Kernel → Run All
```

### 5. Peer review

Another team reviews `docs/model-cards/krakow-pm25-spatial-rf-v1.md`
and leaves 3 bullets in `docs/modelling-log.md` under "Reviewer notes".

---

## Key design decisions (do not change without re-reading modelling-log.md)

| Decision | What was chosen | Where to change it |
|---|---|---|
| Split type | Leave-one-station-out group split (NOT temporal, NOT random) | `TEST_STATIONS`, `VAL_STATIONS` in `src/split_data.py` |
| Test stations | Złoty Róg + Nowa Huta — SACRED | `TEST_STATIONS` constant |
| Val station | Kurdwanów | `VAL_STATIONS` constant |
| Baselines | Dumb mean + seasonal monthly mean | `baseline_model.py` — `fit_dumb_baseline`, `fit_seasonal_baseline` |
| Model | RandomForestRegressor(n_estimators=300, min_samples_leaf=3) | `N_TREES`, `MIN_LEAF` in `baseline_model.py` |
| Target | `pm25_mean` (µg/m³) | `TARGET` constant |
| Features | 8: ndvi, ndbi, road_density_500m, building_density_500m, pct_green_500m, mean_temp_monthly, blh_monthly, month | `FEATURE_COLS` constant |
| Primary metric | MAE (µg/m³) + R² | `compute_metrics_table` function |
| Uncertainty | Tree-quantile 90% interval from RF estimators | `predict_with_uncertainty` function |
| Success criterion | R² ≥ 0.40 on LOSO-CV (from project brief) | Model card section 4 |

---

## Files NOT to touch

- `data/processed/aqicn-monthly-test.parquet` — SACRED until model locked
- Any previously committed session 2 / session 3 files
- `src/clean_data.py` — cleaning pipeline is frozen

---

## Context for the next conversation

Project: Krakow Air Quality & Urban Form — predict monthly mean PM2.5
from urban form features (NDVI, road density, building density, ERA5 weather)
at 10 monitoring stations, then interpolate to 32,700 100m grid cells.

Team: Rim, Martina, Rashi, Bhavana

Session flow: S1 (brief) → S2 (data profiling) → S3 (cleaning + feature plan)
→ S4 (modelling — current) → S5 (orchestration) → S6 (failure gallery)
→ S7 (Streamlit dashboard for Krakow planning analysts)

Branch: Session-4 (on remote, reset from Session-2-V2 on 2026-05-28)

All session 3 files are in: `Surround/session 3/`
All session 4 files are in: `Surround/session 4/`
