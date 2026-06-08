# Evaluation Report — Krakow PM2.5 Spatial Regression

- **Track:** A — model
- **Maintainer:** Rim, Martina, Rashi, Bhavana
- **Last updated:** 2026-06-08
- **Verdict (one line):** ITERATE — R² and MAE criteria met, but the model is 93.6% a seasonal predictor; land use signal is too weak to support planning decisions at ~75% confidence.

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

| # | Criterion | Target | Result | Verdict | Evidence |
|---|---|---|---|---|---|
| 1 | R² on held-out stations | ≥ 0.40 | **0.639** on test | **met** | `03-modelling.ipynb` cell c19 |
| 2 | Beat seasonal baseline | Model MAE < 10.24 | **9.96 µg/m³** (2.7% gain) | **partial** — technically met, margin is negligible | `03-modelling.ipynb` cell c19 |
| 3 | MAE < 12 µg/m³ | < 12 µg/m³ | **9.96 µg/m³** | **met** | `03-modelling.ipynb` cell c19 |

**Summary:** met 2 of 3 criteria fully; criterion 2 is partial — the model beats the seasonal baseline but by only 0.28 µg/m³ (2.7%), which is below the margin needed to claim it is learning urban form rather than re-discovering that January is polluted.

---

## 3 · Compared to what

- Dumb-mean baseline test MAE: **18.24 µg/m³**
- Seasonal-mean baseline test MAE: **10.24 µg/m³**
- RF model test MAE: **9.96 µg/m³**
- Improvement over seasonal: **0.28 µg/m³ (2.7%)**
- Improvement over dumb-mean: **8.28 µg/m³ (45%)**

The model substantially beats the unconditional mean but barely beats the seasonal calendar. A planning analyst who simply looks up "what is the average PM2.5 for Krakow in month X" would be nearly as accurate. The land use features (Urban Atlas 500m buffer) add only 2.7% improvement — the urban form signal is real but marginal with 7 stations.

**Effort vs value:** the model is not yet worth deploying as the sole input to a planning decision. The seasonal component is well-captured; the spatial differentiation by urban form is the gap.

---

## 4 · Where it fails

Summary of `failure-gallery.md`:

| Failing slice / case | Metric | Diagnosis | Type |
|---|---|---|---|
| Winter months (Dec–Feb) | MAE **16.28 µg/m³** vs 9.96 aggregate | Model lacks weather/BLH features; heating season inversions push PM2.5 above what month-mean predicts | systematic — 36 rows |
| Uncertainty intervals | 90% coverage **45.7%** vs 85% target | Tree-quantile spread too narrow; only 265 training rows, 4 stations → trees agree too much | systematic — all predictions |
| Land use signal | month = **93.6%** feature importance | 7 stations insufficient to separate spatial from seasonal signal | systematic — all predictions |
| zloty_rog over-prediction | MAE **10.97** driven by Nov 2023 error 30.28 µg/m³ | Sheltered placement bias: sensor reads 20–30% low; model predicts urban form, not sensor placement | one-off + systematic bias |
| ul_dietla LOSO-CV | MAE **13.10** (worst fold, +17% above CV mean) | Only 57 station-months — fewest in the dataset; RF generalises poorly from limited data | station-level |

---

## 5 · Confidence

- **90% interval coverage on test:** 45.7% (target ≥ 85%) — intervals are severely overconfident
- **LOSO-CV spread:** 11.15 ± 1.46 µg/m³ MAE across 5 folds — spread is moderate; ul_dietla worst at 13.10
- **Systematic bias:** mean residual −1.16 µg/m³ (slight under-prediction); worst in winter (−1.61 µg/m³)
- **Distribution shift fragility:** dropping `month` raises MAE to 22.46 (+126%); forcing all-winter raises MAE to 29.32 (+194%)
- **Overall confidence in verdict:** ~75% — the R² and MAE numbers are real and reproducible, but the model's reliance on the seasonal signal means the land use component is not yet independently validated. Adding ERA5 weather features (BLH, temperature) in Session 5 iteration would increase confidence substantially.

---

## 6 · What we are NOT claiming

- **Not claiming the model explains urban form.** `month` carries 93.6% of the predictive signal. Land use features explain only 6.4%. The model is primarily a seasonal predictor with a marginal spatial correction.
- **Not claiming deployment-ready uncertainty.** The 90% prediction intervals cover only 45.7% of test outcomes. Reporting these intervals to a planning analyst would be misleading — they imply far more precision than the model has.
- **Not claiming it generalises to unmeasured grid cells reliably.** Trained on 4 stations; the 32,700 grid cells span urban typologies far beyond what 4 training points can characterise. Extrapolation to cells >2km from any training station is speculative.
- **Not claiming winter predictions are trustworthy.** Winter MAE = 16.28 µg/m³ — above the 12 µg/m³ informal threshold. Using this model to assess heating-season planning applications risks systematic under-prediction.
- **Not claiming causality.** The model is correlational. "More urban green → less PM2.5" is an observed association across 7 stations, not a causal claim.

---

## 7 · Recommendation — ITERATE

- **Verdict:** ITERATE
- **Because:** the model meets the R² and aggregate MAE criteria, but the land use signal is too weak (2.7% improvement over seasonal baseline, 6.4% feature importance) to support planning decisions about urban form interventions. The uncertainty intervals are unreliable. Both are fixable.
- **Confidence:** ~75%
- **The one specific fix:** add ERA5-Land monthly `mean_temp_monthly` and `blh_monthly` (boundary layer height) to FEATURE_COLS. These were planned in the Session 4 modelling log Decision #4 but not available in the current training data. BLH captures inversion intensity — the primary driver of winter PM2.5 spikes — which would free the land use features from carrying seasonal confound.
- **Secondary fix:** implement conformal prediction (replace tree-quantile intervals) once training data has ≥ 10 stations.
- **What S6 should show:** spatial PM2.5 map with wide uncertainty zones flagged visibly; refuse to show winter predictions without an explicit "heating-season caveat" banner; do not show as a standalone number without the seasonal-vs-spatial breakdown.
- **What S6 should hide:** point predictions without uncertainty intervals; any claim that the model predicts urban form effects; predictions >3km from any training station without an "extrapolation" flag.

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
