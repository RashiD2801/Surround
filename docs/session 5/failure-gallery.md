# Failure Gallery — krakow-pm25-spatial-rf-v1 · TRACK A

- **Model:** `krakow-pm25-spatial-rf-v1`
- **Artifact:** `models/baseline.joblib`
- **Evaluated on:** `data/processed/krakow-pm25-test.csv` (nowa_huta + zloty_rog — 138 station-months)
- **Maintainer:** Rim, Martina, Rashi, Bhavana
- **Last updated:** 2026-06-08

---

## Case 1: Winter heating-season systematic under-prediction

- **The input — what made it hard:** December, January, and February station-months across both test stations. Krakow's heating season drives PM2.5 above 100 µg/m³ via coal/gas boiler combustion and temperature inversions trapping pollutants near ground level. The model has only `month` as its weather proxy — no boundary layer height (BLH), no temperature inversion signal.
- **Predicted vs actual:** worst single case — nowa_huta February 2021: predicted 77.97 µg/m³, actual 118.04 µg/m³, error **40.07 µg/m³**. Second worst: zloty_rog February 2021: predicted 83.17, actual 120.50, error 37.33 µg/m³.
- **Diagnosis — the mechanism that broke:** `month = 2` maps to the training mean for February (~85 µg/m³). In inversion years, actual PM2.5 spikes far above the monthly mean. Without BLH or temperature data the model cannot distinguish a normal February from an inversion February. Systematic under-prediction in all winter rows.
- **Class:** systematic — all 36 winter test rows. Winter MAE = **16.28 µg/m³** vs aggregate test MAE 9.96 µg/m³ (1.6× worse). This is the single worst slice.
- **→ Becomes:** out-of-scope use in model card ("not for heating-season individual-event prediction"); S6 must show a "heating-season caveat" banner on all Nov–Mar outputs.

---

## Case 2: Uncertainty interval collapse

- **The input — what made it hard:** all 138 test inputs. The 90% tree-quantile prediction intervals (5th–95th percentile across 300 trees) are expected to cover ≥ 85% of true values.
- **Predicted vs actual:** 90% interval covers only **45.7%** of test outcomes (target ≥ 85%). Mean interval width = 16.3 µg/m³ on val — the intervals are not too wide, they are centred in the wrong place.
- **Diagnosis — the mechanism that broke:** with only 265 training rows across 4 stations, all trees in the forest see very similar training data. The inter-tree spread reflects data scarcity noise rather than genuine epistemic uncertainty about unseen locations. With 7 stations having similar seasonal patterns, the forest under-estimates its own ignorance about new urban typologies.
- **Class:** systematic — every prediction in the model is affected. The model's uncertainty output cannot be trusted.
- **→ Becomes:** uncertainty intervals must NOT be shown in the S6 dashboard until replaced by conformal prediction (Session 5 iteration task). Showing tree-quantile intervals to a planning analyst would suggest false confidence.

---

## Case 3: Month feature dominance — model is a seasonal predictor, not a land-use model

- **The input — what made it hard:** any input. Feature importance analysis reveals `month` = **93.6%** of the model's predictive signal. All 13 land use features combined = 6.4%.
- **Predicted vs actual:** seasonal-mean baseline test MAE = 10.24 µg/m³; RF model test MAE = 9.96 µg/m³. Improvement = **0.28 µg/m³ (2.7%)**. Stress test — drop `month` entirely: MAE jumps from 9.96 to **22.46 µg/m³** (+126%).
- **Diagnosis — the mechanism that broke:** with only 7 stations and static land use features (same value for every month at the same station), PM2.5 variance is overwhelmingly seasonal. The model correctly learns that January is always more polluted than August — but cannot distinguish a green station from an industrial one beyond the monthly mean. The spatial differentiation signal is buried under seasonal noise.
- **Class:** systematic — the land use component of every prediction is marginal. The model answers "what month is it?" far more than "what is the urban form?"
- **→ Becomes:** the primary ITERATE reason in the evaluation report. Fix: add ERA5 BLH and temperature to FEATURE_COLS to separate weather from urban form.

---

## Case 4: zloty_rog sheltered placement bias over-predictions

- **The input — what made it hard:** zloty_rog station is surrounded by trees and buildings on three sides, systematically measuring 20–30% lower PM2.5 than its urban context predicts. The model was trained on stations without this bias and predicts what the urban form "should" produce — not what this sheltered sensor reads.
- **Predicted vs actual:** worst single case — zloty_rog November 2023: predicted 86.08 µg/m³, actual 55.80 µg/m³, over-prediction error **30.28 µg/m³**. Overall zloty_rog test MAE = **10.97 µg/m³** vs nowa_huta test MAE = 8.98 µg/m³.
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
- **Predicted vs actual:** summer PM2.5 is tightly clustered across all stations (range 32–55 µg/m³, std ≈ 6). The model simply predicts the summer mean ± small correction, and that is enough.
- **Diagnosis — the mechanism that broke:** this is a right-answer-for-the-wrong-reason failure. Summer success reflects low variance in the target, not land-use discrimination. All stations have similar summer PM2.5 regardless of urban form (coal heating is off; background pollution dominates). The model earns a low MAE without having to differentiate urban typologies at all.
- **Class:** systematic — summer performance flatters the aggregate metrics. A model that only knows "summer PM2.5 is low" could achieve similar summer MAE.
- **→ Becomes:** evaluation caveat: the aggregate test MAE of 9.96 µg/m³ is pulled down by the excellent summer performance. The planning-relevant season (heating season, when mitigation decisions matter most) has MAE 16.28 µg/m³.

---

## Stress-test results

| Stress | What it simulates | MAE (µg/m³) | Verdict | Notes |
|---|---|---|---|---|
| Baseline (no stress) | — | 9.96 | — | Reference |
| Drop `month` feature | month goes missing at serving time | 22.46 | **DEGRADED** (+126%) | Model is 93.6% dependent on this one feature |
| 20% NaN in `luse_r005_urban_pct` | sensor/GIS gap in urban coverage data | 9.96 | OK | Median imputer handles gracefully |
| Force all inputs to month=12 | extreme winter distribution shift | 29.32 | **DEGRADED** (+194%) | Model extrapolates badly outside training distribution |
| Land-use shift +0.1 (all features) | greenification intervention scenario | 10.63 | OK (+6.7%) | Small perturbation, model robust |

---

## Summary — what the gallery changes

- **New out-of-scope uses for the model card:** (1) not for heating-season individual-event prediction; (2) not with uncertainty intervals in current form; (3) not for urban-core dense typologies without caveat.
- **Refuse-to-show rules for S6:** winter outputs without heating-season caveat banner; any prediction from tree-quantile uncertainty intervals; zloty_rog outputs without sensor-placement caveat.
- **The verdict's "where it fails" row:** winter months — MAE 16.28 µg/m³, systematic under-prediction, root cause is missing BLH/weather features.

---

## Sign-off

- **Gallery built by:** Rim, Martina, Rashi, Bhavana
- **Reviewed by another team:** [reviewer team] on [date]
- **Entries:** 6 (≥ 5 required ✓)
