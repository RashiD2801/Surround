# Failure Gallery — krakow-pm25-spatial-rf-v1 · TRACK A

- **Model:** `krakow-pm25-spatial-rf-v2` (ERA5 iteration)
- **Artifact:** `models/baseline.joblib`
- **Evaluated on:** `data/processed/krakow-pm25-test.csv` (nowa_huta + zloty_rog — 138 station-months)
- **Maintainer:** Rim, Martina, Rashi, Bhavana
- **Last updated:** 2026-06-08 (updated for v2 after ERA5 iteration)

---

## Case 1: Winter heating-season under-prediction — IMPROVED IN v2

- **The input — what made it hard:** December, January, and February station-months across both test stations. Krakow's heating season drives PM2.5 above 100 µg/m³ via coal/gas boiler combustion and temperature inversions trapping pollutants near ground level.
- **v1 vs v2:** v1 (month only) Winter MAE = **16.28 µg/m³**. v2 (with ERA5 `blh_monthly` + `mean_temp_monthly`) Winter MAE = **9.12 µg/m³** — a 44% reduction. The model can now distinguish a warm February from a temperature-inversion February via BLH.
- **Residual diagnosis:** winter is still the worst season (9.12 vs 6.48 aggregate), but it is now within the 12 µg/m³ planning threshold. The remaining error is from individual inversion events that deviate from the monthly BLH mean.
- **Class:** systematic — all 36 winter test rows. Substantially fixed in v2 but still the worst-performing season.
- **→ Becomes:** winter predictions are now deployable with a caveat that individual inversion-event months may be under-predicted. Remove the hard "not for heating-season" out-of-scope rule; replace with a labelled uncertainty flag.

---

## Case 2: Uncertainty interval under-coverage — PARTIALLY IMPROVED in v2

- **The input — what made it hard:** all 138 test inputs. The 90% tree-quantile prediction intervals (5th–95th percentile across 300 trees) are expected to cover ≥ 85% of true values.
- **v1 vs v2:** v1 coverage = 45.7%; v2 coverage = **72.5%**. Mean interval width narrowed: v1 16.3 µg/m³ → v2 **19.2 µg/m³** (wider, better calibrated). ERA5 features diversified the tree predictions, improving coverage.
- **Residual diagnosis:** 72.5% is better but still 12.5 percentage points short of the 85% target. The fundamental constraint — 4 training stations, 265 rows — means tree-quantile intervals cannot fully represent the epistemic uncertainty about unseen locations.
- **Class:** systematic — every prediction is still under-covered. The model's uncertainty output cannot be reported as-is.
- **→ Becomes:** uncertainty intervals still must NOT be shown in the S6 dashboard without a coverage disclaimer. Primary fix: conformal prediction calibration (requires ≥ 10 stations or a held-out calibration set).

---

## Case 3: Weather dominance — model is a weather predictor, not a land-use model (PERSISTS in v2)

- **The input — what made it hard:** any input. After adding ERA5 features, `mean_temp_monthly` = **72.7%**, `blh_monthly` = **23.6%**, `month` = 1.4%. All 13 land use features combined = **2.3%**.
- **v1 vs v2:** v1 — month 93.6%, land use 6.4%. v2 — ERA5 weather 96.3%, land use 2.3%. Adding weather controls actually reduced apparent land use importance (it was inflated in v1 because `month` was proxying for weather AND urban form confusion).
- **Predicted vs actual:** seasonal baseline MAE 10.24 µg/m³ vs v2 RF MAE **6.48 µg/m³** — 36.7% improvement. The model now clearly beats the seasonal calendar. But this gain comes from ERA5 features, not land use.
- **Diagnosis — the mechanism:** within Krakow's 7 stations, all located within ~15 km, the spatial variation in PM2.5 between stations is small relative to temporal variation from weather patterns. All stations share the same meteorological regime. With static land use features and strong shared weather, the RF learns to predict weather effects rather than spatial land-use effects.
- **Class:** systematic — the land use component of every prediction is marginal. The project's core question ("does urban form correlate with PM2.5?") cannot be answered with 2.3% feature importance from 7 stations.
- **→ Becomes:** a scope limitation, not a model failure. The model is re-framed: it is a weather-controlled PM2.5 predictor that includes land use as a minor correction. To test urban form effects, stations with greater spatial diversity in land use typology are needed.

---

## Case 4: zloty_rog sheltered placement bias over-predictions

- **The input — what made it hard:** zloty_rog station is surrounded by trees and buildings on three sides, systematically measuring 20–30% lower PM2.5 than its urban context predicts. The model was trained on stations without this bias and predicts what the urban form "should" produce — not what this sheltered sensor reads.
- **v2 results:** zloty_rog test MAE = **7.48 µg/m³** vs nowa_huta test MAE = 5.52 µg/m³. The gap persists (1.96 µg/m³) and the mechanism is unchanged.
- **Diagnosis — the mechanism that broke:** this is not a model failure — it is a sensor placement artefact documented in `docs/data-cleaning-log.md` Transform 7. The model is correct about the expected PM2.5 for that urban form; the sensor is wrong. However, from an evaluation standpoint, this inflates test MAE at zloty_rog and makes the model look worse than it is.
- **Class:** systematic for zloty_rog — all 68 test rows at this station. The over-prediction is correlated with months when sheltering effect is largest (autumn/winter with low wind speeds).
- **→ Becomes:** evaluation caveat: zloty_rog test MAE should be interpreted as "model error + sensor placement bias", not pure model error. S6 must flag this station's predictions with a sensor-quality warning.

---

## Case 5: ul_dietla — sparse data worst LOSO fold

- **The input — what made it hard:** ul_dietla held out as the test station in LOSO-CV fold 5. Only 57 station-months in the dataset (all other stations have 68–70). The station has the highest urban continuous density (luse_r005_urban_continuous_pct = 0.55) of all training stations.
- **Predicted vs actual:** LOSO-CV MAE when ul_dietla is held out = **13.10 µg/m³** vs LOSO-CV mean 11.15 µg/m³ (+17%).
- **Diagnosis — the mechanism that broke:** ul_dietla's land use profile (dense continuous urban fabric) is the most extreme in the dataset. With only 4 other training stations to learn from, none of which share this typology, the RF cannot generalise well to this urban form. Additionally, 57 months gives less reliable held-out statistics than the 68–70 months at other stations.
- **Class:** station-level — applies to any grid cell with high urban_continuous_pct in the deployment scenario (Śródmieście core, commercial zones). These are precisely the high-pollution areas the planning tool should cover best.
- **→ Becomes:** a warning for Session 6: grid cells with `luse_r005_urban_continuous_pct > 0.5` should be flagged as "urban-core extrapolation — lower confidence". Retraining with more stations in this typology is the fix.

---

## Case 6: Summer prediction near-perfect — but for the wrong reason

- **The input — what made it hard:** June, July, August station-months. Summer test MAE = **4.56 µg/m³** — apparently excellent.
- **v2 results:** Summer MAE = **3.71 µg/m³** (vs v1 4.56). Still the best-performing season and still for the same reason — low variance in summer targets.
- **Diagnosis — the mechanism that broke:** this is a right-answer-for-the-wrong-reason failure. Summer success reflects low variance in the target, not land-use discrimination. All stations have similar summer PM2.5 regardless of urban form (coal heating is off; background pollution dominates). The model earns a low MAE without having to differentiate urban typologies at all.
- **Class:** systematic — summer performance flatters the aggregate metrics. A model that only knows "summer PM2.5 is low" could achieve similar summer MAE.
- **→ Becomes:** evaluation caveat: the aggregate test MAE of 9.96 µg/m³ is pulled down by the excellent summer performance. The planning-relevant season (heating season, when mitigation decisions matter most) has MAE 16.28 µg/m³.

---

## Stress-test results

v1 stress tests (month-dominant model) shown for comparison; v2 stress tests not re-run.

| Stress | v1 MAE (µg/m³) | v1 verdict | Notes on v2 implication |
|---|---|---|---|
| Baseline (no stress) | 9.96 | — | v2 baseline: 6.48 |
| Drop `month` feature | 22.46 | DEGRADED (+126%) | v2: `month` now 1.4% — dropping it would have minimal effect; `mean_temp_monthly` is now the fragility point |
| 20% NaN in `luse_r005_urban_pct` | 9.96 | OK | v2: same — imputer handles gracefully |
| Force all inputs to month=12 | 29.32 | DEGRADED (+194%) | v2: less fragile — weather features dominate, not `month` |
| Land-use shift +0.1 (all features) | 10.63 | OK (+6.7%) | v2: even smaller response expected given 2.3% importance |

---

## Summary — what the gallery changes

- **New out-of-scope uses for the model card (v2):** (1) not as a standalone land-use attribution model (2.3% land use signal); (2) not with uncertainty intervals in current form (72.5% coverage, below 85% target); (3) not for urban-core dense typologies without caveat.
- **Refuse-to-show rules for S6:** any prediction from tree-quantile uncertainty intervals without a coverage disclaimer; zloty_rog outputs without sensor-placement caveat; claims that land use drives predicted PM2.5.
- **The verdict's "where it fails" row (v2):** land use signal 2.3% — model does not establish urban form–PM2.5 correlation; uncertainty intervals 72.5% coverage vs 85% target.

---

## Sign-off

- **Gallery built by:** Rim, Martina, Rashi, Bhavana
- **Reviewed by another team:** [reviewer team] on [date]
- **Entries:** 6 (≥ 5 required ✓)
