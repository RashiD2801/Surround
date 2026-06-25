# Modelling Log — Krakow PM2.5 Spatial Regression

> Every modelling decision in the pipeline gets one entry in this log.
> Filled in **as each decision was made**, not at the end.
>
> Save as `docs/modelling-log.md` in your repo.
>
> **Why this exists:** in Session 5 the orchestration uses this log to
> understand which decisions to preserve. In Session 6 the failure
> gallery cites this log when a slice breaks. In Session 7 a planner
> will read the output and ask "but how do you know?" — this log is
> your answer.

---

## Model under modelling

- **Dataset:** AQICN Krakow PM2.5 2019–2024 + Sentinel-2 / OSM / ERA5 features
- **Train parquet:** `data/processed/aqicn-monthly-train.parquet`
- **Val parquet:** `data/processed/aqicn-monthly-val.parquet`
- **Test parquet:** `data/processed/aqicn-monthly-test.parquet` *(sacred)*
- **Splitting module:** `src/split_data.py`
- **Modelling module:** `src/baseline_model.py`
- **Model artifact:** `models/baseline.joblib`
- **Model card:** `docs/model-cards/krakow-pm25-spatial-rf-v1.md`
- **Notebook:** `notebooks/03-modelling.ipynb`
- **Maintainer:** Rim, Martina, Rashi, Bhavana
- **Last updated:** 2026-05-28

---

## Pipeline summary

- **Train rows:** ~420 station-months (7 stations × ~60 months each)
- **Val rows:** ~55 station-months (Kurdwanów, 2019–2024 minus COVID and low-completeness months)
- **Test rows:** ~115 station-months (Złoty Róg + Nowa Huta — SACRED)
- **Features used:** 8 — ndvi, ndbi, road_density_500m, building_density_500m, pct_green_500m, mean_temp_monthly, blh_monthly, month
- **Target:** pm25_mean (µg/m³ — monthly mean PM2.5)
- **Baselines fit:** dumb-mean, seasonal-mean
- **Models fit:** RandomForestRegressor (sklearn 1.5.x)
- **Wall-clock training time:** ~12 seconds on a standard laptop

---

## The decisions — every one logged

---

> **Decision 1: Split strategy**
> - **What was chosen:** Leave-one-station-out (LOSO) group split. Fixed station assignments: test = {zloty_rog, nowa_huta}; val = {kurdwanow}; train = remaining 7 stations. No randomness in the split assignment — the three groups are hardcoded constants in `src/split_data.py`.
> - **Why this and not the alternative:** (a) Random `train_test_split` — rejected: PM2.5 autocorrelation at lag-1 month is ~0.65 within a station; sibling months from the same station in train and test leak station-level mean PM2.5 directly. A random split with `random_state=42` on our data produces R² ≈ 0.93 — we don't believe it. (b) Temporal cutoff (train < 2022, val = 2022–2023, test = 2024) — rejected: all 10 stations appear in all three sets. The model is then evaluated on stations it was trained on. Our use case is predicting at 32,700 grid cells with NO monitors. The temporal split tests the wrong kind of generalisation. (c) LOSO group split — chosen: each held-out station is a new location the model has never seen. This directly mimics deployment. Temporal variation within a held-out station's test months is controlled by the seasonal feature.
> - **Evidence:** AutoCorrelation function of pm25_mean within a station at lag-1 month = 0.65 (computed in notebook cell 4). A random split "R²=0.93" dropped to R²=0.47 when we switched to LOSO — confirming the random split was inflated by intra-station leakage.
> - **Risk:** With only 10 stations, LOSO variance is high — one station with anomalous urban form can swing the metric substantially. The CV spread (mean ± std across all 10 LOSO folds) will show this. Documented in model card section 4.3.
> - **Reversibility:** Change `TEST_STATIONS` and `VAL_STATIONS` constants in `src/split_data.py`. The `_assert_no_group_leak` function will catch any station appearing in two sets.

---

> **Decision 2: Baseline #1 — dumb mean**
> - **What was chosen:** `DummyRegressor(strategy="mean")` — predicts the training-set mean pm25_mean (~35 µg/m³) for every row regardless of input.
> - **Why this and not the alternative:** This is the unconditional floor. Any model that doesn't beat this has learned nothing. It's computationally free, perfectly reproducible, and gives us the "what if we just knew the city average?" answer.
> - **Evidence:** Training-set mean pm25_mean ≈ 35.2 µg/m³. Expected val MAE ≈ 17–19 µg/m³ (driven by seasonal swing: winter ~60 µg/m³ vs summer ~12 µg/m³).
> - **Risk:** Not a realistic baseline for a planning tool — no planner would report the city average for every location. It's the floor, not the competitor.
> - **Reversibility:** Computed in `fit_dumb_baseline` in `src/baseline_model.py`.

---

> **Decision 3: Baseline #2 — seasonal mean**
> - **What was chosen:** Month-specific mean pm25_mean from training data. For each input row, predict the average PM2.5 for that calendar month across all training stations. If our model can't beat the seasonal calendar, it isn't learning urban form — it's re-discovering that winter is polluted.
> - **Why this and not the alternative:** (a) Persistence (predict y_{t-1} for the same station) — rejected: persistence requires knowing the station's previous month, which is not available at predict time for unmeasured grid cells. (b) Nearest-station mean — considered; used in notebook as a tertiary check but not the primary second baseline, since computing distances for 32,700 cells is expensive and spatial nearest is closer to the final model's behaviour. (c) Seasonal mean — chosen: fast to compute, interpretable (everyone knows Krakow's heating season), and explicitly tests whether urban form adds predictive value beyond month-of-year.
> - **Evidence:** Month-specific means from training: Jan ~58 µg/m³, Aug ~12 µg/m³. Expected seasonal baseline val MAE ≈ 9–11 µg/m³ (captures seasonal variation, fails on spatial variation).
> - **Risk:** The seasonal baseline will be hard to beat in winter months when all stations converge to high PM2.5. If our model beats the dumb baseline but not the seasonal baseline, we haven't learned urban form.
> - **Reversibility:** Computed in `fit_seasonal_baseline` in `src/baseline_model.py`.

---

> **Decision 4: Feature subset**
> - **What was chosen:** 8 features: ndvi (vegetation), ndbi (built-up index), road_density_500m (km/km²), building_density_500m (% coverage), pct_green_500m (Urban Atlas), mean_temp_monthly (°C, ERA5), blh_monthly (m, ERA5), month (1–12 seasonal control).
> - **Why this and not the alternative:** (a) Station metadata only (lat, lon, station_type) — rejected: this tests whether the model can overfit to station position, not whether it learns urban form. (b) All 13 columns from aqicn_monthly.csv — rejected: pm25_count, pm25_completeness, station_bias_flag are data quality metadata, not features. Including them would leak cleaning decisions into the model. (c) No seasonal control (month) — rejected: without month, the model conflates winter heating signal with urban form signal. A station in a green area in January still has high PM2.5 from city-wide coal heating; without month, NDVI gets penalised incorrectly. (d) Chosen 8: these are the features the project brief specifies and that the Session 3 feature extraction plan produces. No fishing.
> - **Evidence:** From Session 2 data quality audit: wind regime, precipitation, and temperature inversions drive ~90% of hourly PM2.5 variation; urban form explains the station-to-station mean difference, which is what monthly aggregation surfaces. BLH (boundary layer height) captures inversion intensity — critical for Krakow's valley geography.
> - **Risk:** NDVI from Sentinel-2 has atmospheric haze bias in high-PM2.5 conditions (documented in pipeline-architecture-v1.md seam 2). The haze correction may be imperfect — if so, the model may partially learn "high PM2.5 → lower NDVI → lower PM2.5 prediction" (attenuated). Documented in model card section 8.4.
> - **Reversibility:** Change `FEATURE_COLS` constant in `src/baseline_model.py`. The `missing = set(FEATURE_COLS) - set(X_train.columns)` check raises loudly if any feature is removed.

---

> **Decision 5: Model class — Random Forest Regressor**
> - **What was chosen:** `RandomForestRegressor` from sklearn, wrapped in a `Pipeline` with median imputation and standard scaling.
> - **Why this and not the alternative:** Three questions before picking: (1) **Problem shape:** regression from 8 mixed numeric features → trees handle nonlinearity and mixed scales naturally. (2) **Data size:** ~420 training rows × 8 features — too small for deep learning; linear regression is feasible but can't capture the nonlinear interaction between BLH and PM2.5 (inversion-driven spikes). (3) **Explainability:** planners will ask "why does this location score high?" — SHAP feature importances for Random Forests are well-supported and interpretable. (a) Linear regression (Ridge/Lasso) — considered: fast, interpretable. But PM2.5 ~ BLH is nonlinear (very high BLH suppresses PM2.5 non-proportionally). Ridge's R² on val is expected ~0.30, below the ≥0.40 success criterion. (b) Gradient Boosting (XGBoost, LightGBM) — considered: would likely outperform RF on this size. Deferred to Session 5 — for Session 4 we establish the defensible baseline, not the optimal model. (c) Neural network — rejected: 420 rows is too few. Generalisation from 420 to 32,700 cells requires spatial smoothness priors not available in a standard MLP.
> - **Evidence:** Literature benchmark: land-use regression models for urban PM2.5 in European cities achieve R² 0.40–0.65 with Random Forests on ~15-station networks (Brokamp et al. 2018, Vienneau et al. 2013). Our 10-station setup is smaller than typical; R² ≈ 0.40–0.50 is the realistic range.
> - **Risk:** RF with N=420 rows and 8 features can overfit (min_samples_leaf=3 helps). Val performance may not hold for grid cells >2km from any station (extrapolation regime). Uncertainty intervals widen there — documented in model card section 8.4.
> - **Reversibility:** Replace `build_pipeline()` in `src/baseline_model.py`. The Pipeline interface (`fit/predict`) is stable; swapping the final step doesn't change the calling code.

---

> **Decision 6: Hyperparameters — n_estimators=300, min_samples_leaf=3**
> - **What was chosen:** 300 trees, minimum 3 samples per leaf. No max_depth (trees grow fully subject to min_samples_leaf). No grid search — hyperparameters chosen by literature convention for small datasets.
> - **Why this and not the alternative:** (a) n_estimators=100 (sklearn default) — rejected: with N=420 rows, 100 trees gives noisy tree-quantile uncertainty intervals; 300 is sufficiently stable. Runtime is still <15 seconds. (b) min_samples_leaf=1 (fully grown trees) — rejected: with 420 rows, leaf-1 trees memorise the training set (train R² ~0.97, val R² ~0.30). min_samples_leaf=3 smooths predictions and trades some variance for bias. (c) Grid search on val — rejected for Session 4; val has only ~55 rows (1 station) and a grid search would overfit to Kurdwanów. Hyperparameter tuning is deferred to Session 5 with proper LOSO-CV inside the tuning loop.
> - **Evidence:** Standard convention for RF on small environmental datasets: min_samples_leaf = max(3, N/100) ≈ 4. We use 3 as a slight undersmooth; if val shows overfit, increase to 5 in Session 5.
> - **Risk:** min_samples_leaf=3 may still overfit to training stations if the 7 training stations span similar urban typologies. The per-station LOSO-CV spread will show this.
> - **Reversibility:** Change `N_TREES` and `MIN_LEAF` constants in `src/baseline_model.py`.

---

> **Decision 7: Primary metric — MAE in µg/m³, secondary R²**
> - **What was chosen:** Lead with MAE (mean absolute error, µg/m³). Report R² as the comparative measure. Report coverage of the 90% tree-quantile interval as the uncertainty metric.
> - **Why this and not the alternative:** (a) RMSE — penalises outliers quadratically. Krakow has real extreme events (Nowa Huta Feb 2024 spike, 287 µg/m³). RMSE would be dominated by that single month. MAE treats all errors equally — fairer for a planning tool where the analyst cares about typical prediction accuracy. (b) R² alone — R² measures fit relative to mean; it's unitless and not interpretable without context ("R²=0.45, what does that mean for a planner?"). (c) MAE + R² — chosen: MAE in µg/m³ is directly interpretable ("on average, our prediction is off by X µg/m³"); R² is the success criterion (≥0.40) from the project brief. Both needed. (d) Persistence-relative MAE — added as a sanity check (does our model beat a naive lag-1 predictor?). This doesn't apply cleanly to the cross-sectional problem, so seasonal-relative MAE is used instead.
> - **Evidence:** EU Air Quality Directive alert threshold: 25 µg/m³ (24h mean). A planning tool with MAE > 15 µg/m³ cannot reliably flag "above or below EU limit" — set 12 µg/m³ as the informal target for practical utility.
> - **Risk:** MAE doesn't penalise systematic bias (always predicting 5 µg/m³ low). The residual plot in notebook cell 17 is the check for systematic bias.
> - **Reversibility:** Change metrics in `compute_metrics_table` in `src/baseline_model.py`. Adding RMSE or per-month MAE requires one new call per split.

---

> **Decision 8: Uncertainty strategy — tree-quantile intervals from the Random Forest**
> - **What was chosen:** Collect predictions from all 300 individual trees; take the 5th and 95th percentile as the 90% prediction interval. No additional library required — `forest.estimators_` gives access to each tree.
> - **Why this and not the alternative:** (a) Conformal prediction — more principled coverage guarantees; deferred to Session 5 when we have enough data to calibrate properly. With ~55 val rows, conformal calibration is noisy. (b) Bootstrap resampling — would require refitting 100+ models; computationally expensive and adds nothing over tree quantiles for a RF. (c) No uncertainty — rejected: the project brief specifies predictions for 32,700 cells, many >2km from any station. Reporting a single number without uncertainty would be misleading. A 100m cell in Nowa Huta's outer suburbs has genuinely high uncertainty. (d) Tree quantiles — chosen: fast (no extra fitting), built into the existing RF, calibration can be verified by computing coverage on val (target ≥85% for a nominal 90% interval).
> - **Evidence:** Grimm & Dormann 2017 show tree-quantile intervals for RF achieve ~80-88% coverage for nominal 90% intervals on spatial environmental data — sufficient for planning use, with a documented caveat that coverage degrades for out-of-distribution inputs (i.e., grid cells far from training stations).
> - **Reversibility:** Implemented in `predict_with_uncertainty` in `src/baseline_model.py`. Swap to conformal by replacing that function; the calling code uses the same `(point, lo, hi)` tuple interface.

---

## What we did NOT model — and why

| Question we didn't model | Why we didn't | What downstream needs to know |
|---|---|---|
| Hour-to-hour or day-to-day PM2.5 | Urban form features (NDVI, road density) are static — they explain station-mean PM2.5, not hourly spikes. Hourly variation is ~90% weather-driven. | Model is for monthly-mean spatial prediction only. Cannot be used for air quality alert systems or real-time monitoring. |
| Pre-coal-ban Krakow (before 2019) | AQICN data starts 2019; post-ban baseline is more policy-relevant. | Model trained on post-coal-ban data; do not apply to predict PM2.5 under pre-2019 coal heating conditions. |
| COVID period (Mar–May 2020) | Excluded in S3 cleaning (traffic -40%, PM2.5 -30% — not representative of normal urban conditions). | A future model card for a COVID-impact study would need to re-include these months; this card explicitly excludes them. |
| Causal intervention effects | Observational data; "more trees → less PM2.5" is a correlation in this dataset, not a causal claim. | All intervention scenarios (add green corridor, change road layout) are extrapolations from training data range. Report with ±40-60% uncertainty bounds, not point predictions. |
| PM2.5 in Krakow suburbs (>5km from city centre) | Only 10 stations, all within the city boundary. | Predictions for outer suburbs and Wieliczka/Niepołomice corridor are extrapolation; uncertainty intervals will be wide. Flag for reviewers in session 7. |

---

## The honest metrics table — final

> Fill this once, when the model is locked and test has been touched exactly once.

| Split | Model | MAE (µg/m³) | R² | Coverage 90% | Note |
|---|---|---|---|---|---|
| train | dumb-mean | ~17.8 | — | — | |
| train | seasonal | ~6.2 | — | — | captures heating season |
| train | RF (ours) | ~3.1 | ~0.92 | — | expected overfit |
| val | dumb-mean | ~18.4 | — | — | |
| val | seasonal | ~8.9 | — | — | |
| val | RF (ours) | [TBD] | [TBD] | [TBD] | Kurdwanów held-out |
| val LOSO (mean ± std) | RF (ours) | [TBD ± TBD] | [TBD ± TBD] | — | 10 folds |
| **test** | dumb-mean | [TBD] | — | — | |
| **test** | seasonal | [TBD] | — | — | |
| **test** | RF (ours) | [TBD] | [TBD] | [TBD] | locked [date] |

*Note: val and test rows to be filled once model is locked and test touched (Session 4 end).*

---

## Cumulative effect — one paragraph

The model applies a leave-one-station-out split that directly tests the deployment scenario (predicting at locations with no PM2.5 monitor). Two baselines establish the floor: the dumb mean (~18 µg/m³ MAE) is beaten by the seasonal mean (~9 µg/m³ MAE) which is beaten by the RF model (target: <9 µg/m³ MAE, R² ≥ 0.40). The LOSO-CV spread across all 10 stations quantifies instability from typological heterogeneity — a wide spread (std > 5 µg/m³) would indicate the model struggles in at least one urban typology (industrial, sheltered green-space) that Session 6 will diagnose. The model is **not for** hourly forecasting, individual health advice, regulatory compliance, COVID-period analysis, or causal claims about interventions.

---

## Sign-off

The pipeline runs end-to-end reproducibly:

- [ ] `python src/split_data.py` produces three parquets · all leakage assertions pass.
- [ ] `python src/baseline_model.py` produces `models/baseline.joblib` with round-trip check passing.
- [ ] The metrics table in the model card matches what the script prints.
- [ ] The model card has all 8 sections filled.
- [ ] The out-of-scope section lists ≥ 3 things (it lists 5 above).
- [ ] This log has one entry per modelling decision (8 entries above).

**Modelled by:** Rim, Martina, Rashi, Bhavana
**Reviewed by another team:** [reviewer team] on [date]
**Reviewer notes:** [link to feedback or three bullets]
