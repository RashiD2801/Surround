# Evaluation Report — Krakow PM2.5 Spatial Regression

- **Track:** A — model
- **Maintainer:** Rim, Martina, Rashi, Bhavana
- **Last updated:** 2026-06-08
- **Model version:** v2 (ERA5 iteration complete)
- **Verdict (one line):** CONDITIONAL DEPLOY — all three performance criteria met after ERA5 iteration (R²=0.850, MAE=6.48 µg/m³); land use contributes only 2.3%, so deploy as weather-controlled PM2.5 predictor, not as a standalone urban-form model.

---

## 1 · The question & the success criteria (from Session 1)

- **The decision this serves:** Krakow Municipal Planning Office analyst, reviewing a development application that requires an air quality impact assessment. Uses predicted monthly mean PM2.5 to decide whether to require green-infrastructure conditions (tree planting, setbacks, road closures). Weekly cadence — one to two applications per month.
- **The cost of being wrong:** Under-predicting PM2.5 at a high-pollution location → no green-infrastructure requirement imposed → residents exposed to harmful air quality without mitigation.

| # | Success criterion (S1) | How it's measured | The bar |
|---|---|---|---|
| 1 | Establish a relationship between urban form and PM2.5 | R² on held-out stations | ≥ 0.40 |
| 2 | Beat a naive baseline | Model MAE vs seasonal-mean baseline | Model MAE < seasonal MAE |
| 3 | Practically useful for planning | MAE in µg/m³ vs EU/WHO thresholds | MAE < 12 µg/m³ (informal target) |

---

## 2 · Result vs criteria

| # | Criterion | Target | v1 result | v2 result (ERA5) | Verdict |
|---|---|---|---|---|---|
| 1 | R² on held-out stations | ≥ 0.40 | 0.639 | **0.850** | **met** |
| 2 | Beat seasonal baseline | Model MAE < 10.24 | 9.96 (2.7% gain) | **6.48 µg/m³ (36.7% gain)** | **met** |
| 3 | MAE < 12 µg/m³ | < 12 µg/m³ | 9.96 µg/m³ | **6.48 µg/m³** | **met** |

Evidence for all v2 numbers: `src/baseline_model.py` run 2026-06-08 + manual test-set evaluation (same sacred split).

**Summary:** all 3 criteria met in v2. ERA5 iteration (adding `mean_temp_monthly` + `blh_monthly`) raised test R² from 0.639 → 0.850 and cut MAE from 9.96 → 6.48 µg/m³. Seasonal improvement went from 2.7% → 36.7%. The remaining caveat: land use features dropped from 6.4% → 2.3% importance when proper weather controls were added, indicating the model is a weather-integrated PM2.5 predictor rather than a land-use regression.

---

## 3 · Compared to what

- Dumb-mean baseline test MAE: **18.24 µg/m³**
- Seasonal-mean baseline test MAE: **10.24 µg/m³**
- RF v2 model test MAE: **6.48 µg/m³**
- Improvement over seasonal: **3.76 µg/m³ (36.7%)**
- Improvement over dumb-mean: **11.76 µg/m³ (64.5%)**

The v2 model now clearly beats both the unconditional mean and the seasonal calendar. The ERA5 weather features (temperature + BLH) supply the decisive signal that v1 lacked. The model answers "what month is it + how cold/inverted is the atmosphere?" — and does so accurately. Land use adds a further 2.3% on top of that.

**Effort vs value:** the model is worth deploying for weather-integrated monthly PM2.5 estimation. The caveat is scope: it is a weather-controlled prediction model, not a land-use attribution model. A planning analyst should treat it as "given this month's weather patterns, what PM2.5 is expected at this urban location" rather than "does this site's land use cause high PM2.5."

---

## 4 · Where it fails

Summary of `failure-gallery.md`:

| Failing slice / case | v1 metric | v2 metric | Diagnosis | Type |
|---|---|---|---|---|
| Winter months (Dec–Feb) | MAE 16.28 µg/m³ | MAE **9.12 µg/m³** | ERA5 BLH captures inversion intensity — significant improvement; still worst season | systematic — 36 rows |
| Uncertainty intervals | 90% coverage 45.7% | 90% coverage **72.5%** | Improved but still below 85% target | systematic — all predictions |
| Land use signal | month 93.6%, land use 6.4% | temp+BLH **96.3%**, land use **2.3%** | ERA5 absorbed the residual seasonal confound; land use contribution is even smaller when weather is controlled | systematic — all predictions |
| zloty_rog over-prediction | MAE 10.97 | MAE **7.48** | Sheltered placement bias persists; improved overall but mechanism unchanged | one-off + systematic bias |
| ul_dietla LOSO-CV | MAE 13.10 (worst fold) | Not re-run on v2 | Sparse data issue unchanged; 57 station-months | station-level |

---

## 5 · Confidence

- **90% interval coverage on test:** 72.5% (target ≥ 85%) — improved from 45.7% but still below target; cannot publish intervals to planning analysts
- **LOSO-CV spread (v1):** 11.15 ± 1.46 µg/m³ MAE — spread is moderate; v2 LOSO not re-run on this iteration
- **Distribution shift fragility:** reduced — model is now temp+BLH dominant; `month` is 1.4% (no longer single-point-of-failure)
- **Val performance (v2):** MAE 4.99 µg/m³, R² = 0.904 — strong generalisation on kurdwanow
- **Overall confidence in verdict:** ~85% — all three criteria met, ERA5 features fixed the winter failure and seasonal over-reliance; residual concern is the 2.3% land use signal and below-target uncertainty intervals

---

## 6 · What we are NOT claiming

- **Not claiming the model explains urban form.** `mean_temp_monthly` + `blh_monthly` carry 96.3% of the predictive signal. Land use features explain only 2.3%. The model is a weather-controlled PM2.5 predictor with a marginal urban-form correction. It does not answer "does land use cause pollution."
- **Not claiming deployment-ready uncertainty.** The 90% prediction intervals cover only 72.5% of test outcomes (target ≥ 85%). Reporting these intervals to a planning analyst would be misleading — they imply more precision than the model has.
- **Not claiming it generalises to unmeasured grid cells reliably.** Trained on 4 stations; the 32,700 grid cells span urban typologies far beyond what 4 training points can characterise. Extrapolation to cells >2km from any training station is speculative.
- **Not claiming causality.** The model is correlational. "More urban green → less PM2.5" is an observed association across 7 stations, not a causal claim.
- **Not claiming strong land use–PM2.5 correlation.** Adding proper weather controls (ERA5) reduced land use importance from 6.4% → 2.3%. The original Session 1 goal ("establish a relationship between urban form and PM2.5") requires more diverse stations to test with weather controlled.

---

## 7 · Recommendation — CONDITIONAL DEPLOY

- **Verdict:** CONDITIONAL DEPLOY
- **Because:** all three S1 performance criteria are met in v2 (R²=0.850, MAE=6.48, 36.7% over seasonal). The ERA5 iteration fixed winter failure (MAE 16.28 → 9.12) and the seasonal over-reliance (month 93.6% → 1.4%). The model is reliable as a weather-controlled monthly PM2.5 estimator.
- **The condition:** deploy with explicit scope — this is a weather-integrated PM2.5 predictor, not a land-use attribution model. Land use contributes 2.3% of signal. Planning decisions about urban form interventions must not rely solely on this model's land-use features.
- **Confidence:** ~85%
- **Remaining iteration for S6:** implement conformal prediction to replace tree-quantile uncertainty intervals (72.5% coverage → target ≥ 85%). Gather data from more diverse-typology stations to raise land use signal above noise.
- **What S6 should show:** spatial PM2.5 map with ERA5 weather context visible; uncertainty zones flagged; winter predictions allowed (now below 12 µg/m³ threshold) but labelled.
- **What S6 should hide:** point predictions without uncertainty intervals; any claim that land use alone predicts PM2.5; predictions >3km from any training station without an "extrapolation" flag.

---

## Sign-off

- **Evaluated by:** Rim, Martina, Rashi, Bhavana
- **Reviewed by another team:** [reviewer team] on [date]
- **Reviewer feedback:** [link to entry in `evaluation-log.md`]
- **Reproducible:** fresh clone + `Run all` of `05-evaluation.ipynb` reproduces every number — [to confirm after notebook is written]

---

## Appendix · How this report is used downstream

- **Session 6 (deployment):** the verdict (ITERATE) seeds the re-training with ERA5 features. Section 6 ("what we are NOT claiming") is the UI's refuse-to-show list.
- **Session 7 (presentation):** verdict sentence (top of this file) is the opening line; sections 2 and 4 are the two core slides.
