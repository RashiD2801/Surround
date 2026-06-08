# Evaluation Log — Krakow PM2.5 Spatial Regression

- **Track:** A — model
- **Maintainer:** Rim, Martina, Rashi, Bhavana
- **Last updated:** 2026-06-08

---

> **Test 1:** Per-station MAE on test set
> - **What I tested — and why it could break the result:** the aggregate test MAE of 9.96 µg/m³ meets the S1 bar, but nowa_huta (industrial) and zloty_rog (sheltered bias) are very different station types. If one station drives a very high MAE, the aggregate hides a failure.
> - **What it showed:** nowa_huta MAE = 8.98 µg/m³ (n=70); zloty_rog MAE = 10.97 µg/m³ (n=68). The gap is 2 µg/m³. zloty_rog is worse, consistent with its documented sheltered placement bias.
> - **What I concluded:** held — the aggregate MAE is not hiding a catastrophic single-station failure. zloty_rog is worse but the mechanism (sensor bias, not model failure) is documented.
> - **What it changed in the verdict:** added a caveat to evaluation-report.md §5: zloty_rog test MAE includes sensor placement bias, not only model error.

---

> **Test 2:** Per-season MAE on test set
> - **What I tested — and why it could break the result:** the aggregate hides seasonal variation. Krakow's heating season (Nov–Mar) creates PM2.5 spikes the model may not capture. If winter MAE is very high, the model is not safe for planning applications submitted in winter.
> - **What it showed:** Winter MAE = **16.28 µg/m³** (1.6× aggregate). Summer MAE = 4.56 µg/m³. Spring = 9.21. Autumn = 9.40.
> - **What I concluded:** **weakened the verdict.** Winter is a systematic failure. The model is unreliable for the heating season — precisely when Krakow's air quality is worst and planning decisions most consequential.
> - **What it changed in the verdict:** downgraded recommendation from DEPLOY to ITERATE; added "not for heating-season predictions" to out-of-scope uses; added winter case as Case 1 in failure-gallery.md.

---

> **Test 3:** Feature importance analysis
> - **What I tested — and why it could break the result:** if `month` dominates importance, the model is a seasonal predictor, not a land-use regression. The project brief is to establish land use–PM2.5 correlation.
> - **What it showed:** `month` = **93.6%** importance. All 13 land use features combined = 6.4%. Top land use feature: `luse_r005_urban_discontinuous_pct` at 1.3%.
> - **What I concluded:** **weakened the verdict significantly.** The model barely learns urban form. It answers "what month is it?" rather than "what is the urban density?"
> - **What it changed in the verdict:** criterion 2 (beat seasonal baseline) downgraded to "partial"; added Case 3 to failure gallery; the ITERATE recommendation cites ERA5 feature addition as the fix.

---

> **Test 4:** Seasonal baseline comparison
> - **What I tested — and why it could break the result:** the model must beat a seasonal mean baseline to claim it learns anything beyond the calendar. If the margin is negligible, the land use features are adding no real signal.
> - **What it showed:** seasonal baseline test MAE = 10.24 µg/m³; RF model = 9.96 µg/m³. Improvement = **0.28 µg/m³ (2.7%)**.
> - **What I concluded:** **weakened the verdict.** The model technically beats the seasonal baseline but by a margin that would not be actionable in practice. A planning analyst using the seasonal mean would be nearly as accurate.
> - **What it changed in the verdict:** criterion 2 verdict changed to "partial"; confirms ITERATE recommendation.

---

> **Test 5:** Uncertainty interval coverage on test
> - **What I tested — and why it could break the result:** the 90% tree-quantile intervals should cover ≥ 85% of true test values. Under-coverage means the model's uncertainty output misleads users into false confidence.
> - **What it showed:** 90% coverage on test = **45.7%** (target ≥ 85%). Mean interval width = 16.3 µg/m³ on val.
> - **What I concluded:** **killed the uncertainty claim.** The intervals cannot be reported to planning analysts. They are severely overconfident — 54.3% of true values fall outside the stated 90% band.
> - **What it changed in the verdict:** added Case 2 to failure gallery; added "not for uncertainty intervals in current form" to out-of-scope uses; S6 refuse-to-show rule added.

---

> **Test 6:** Stress test — drop `month` feature
> - **What I tested — and why it could break the result:** what happens if the month feature is missing at prediction time (e.g., a serving pipeline bug)? Given its 93.6% importance, the model may crash or degrade severely.
> - **What it showed:** MAE jumps from 9.96 to **22.46 µg/m³** (+126%). Model does not crash (imputer fills NaN with median month).
> - **What I concluded:** **confirmed fragility.** The model is 93.6% dependent on a single feature. A serving-time bug that drops the month column would double the error without raising an exception.
> - **What it changed in the verdict:** added to stress-test table in failure-gallery.md; recommendation to add an assertion in the serving pipeline that `month` is always present and within [1, 12].

---

> **Test 7:** Stress test — force all inputs to month=12 (distribution shift)
> - **What I tested — and why it could break the result:** what if the model is used in a context where seasonal distribution shifts (e.g., all predictions requested in December)? Does it extrapolate gracefully?
> - **What it showed:** MAE jumps to **29.32 µg/m³** (+194%). This is 2.9× the aggregate MAE.
> - **What I concluded:** **confirmed distribution shift brittleness.** The model is calibrated for the full seasonal distribution. Predicting only in winter months — a realistic scenario for a planning application submitted in January — produces predictions three times less accurate.
> - **What it changed in the verdict:** added to stress-test table; winter caveat strengthened.

---

> **Test 8:** Stress test — 20% NaN injection in `luse_r005_urban_pct`
> - **What I tested — and why it could break the result:** in production, GIS land-use data may have gaps (unmapped parcels, new developments). Does the pipeline handle missing land use values gracefully?
> - **What it showed:** MAE remains **9.96 µg/m³** — identical to baseline. Model does not crash.
> - **What I concluded:** **held.** The median imputer in the sklearn Pipeline handles missing land use values gracefully. This is a positive finding for deployment robustness.
> - **What it changed in the verdict:** no change to verdict; noted as a robustness positive in evaluation-report.md §5.

---

> **Test 9:** Stress test — land-use distribution shift (+0.1 to all features)
> - **What I tested — and why it could break the result:** simulates a "greenification intervention" scenario where urban land use shifts (e.g., a park is built). Does the model respond sensibly to a perturbation in land use features?
> - **What it showed:** MAE changes from 9.96 to **10.63 µg/m³** (+6.7%). Model does not crash.
> - **What I concluded:** **held with caveat.** A small feature shift produces a proportionally small MAE change — the model is not wildly unstable for land use perturbations. However, since land use only contributes 6.4% of signal, this response is mostly meaningless: the model barely knows the land use changed.
> - **What it changed in the verdict:** no change to verdict; noted as insufficient evidence for use in intervention scenario modelling.

---

> **Test 10:** Systematic bias check (residual analysis)
> - **What I tested — and why it could break the result:** does the model systematically over- or under-predict? A biased model is dangerous for planning because it consistently misleads the analyst in one direction.
> - **What it showed:** mean residual = **−1.16 µg/m³** (slight under-prediction overall). By season: Autumn −0.49, Spring −1.41, Summer −1.15, Winter −1.61. Bias is consistent direction but small magnitude.
> - **What I concluded:** **held.** The model has a small systematic under-prediction bias (1.16 µg/m³), strongest in winter (1.61 µg/m³). For a planning tool this is conservative (under-predicting pollution means erring toward flagging fewer sites for intervention), which is the less dangerous direction.
> - **What it changed in the verdict:** noted in confidence section; no verdict change.

---

## Tests we did NOT run — and why

| Test we skipped | Why | What downstream needs to know |
|---|---|---|
| Per-district analysis (Śródmieście vs Nowa Huta) | Only 7 stations total; Nowa Huta = test station (sacred until test touched). Post-test district analysis not prioritised in S5 | S6 should run district breakdown once retraining includes more stations |
| Conformal prediction calibration | Requires ≥ 10 stations for calibration set; we have 7 | S5 ITERATE task: implement conformal prediction after adding ERA5 features and ideally more station data |
| Temporal drift test (2019–2024 year-by-year) | Monthly aggregation across all years; year-by-year breakdown would need ~12 rows per station-year. Low statistical power | S6: flag if model is applied to 2025 data without revalidation |
| Adding ERA5 features (BLH, temperature) | Data not yet in the training dataset | The primary ITERATE fix — S5 task |

---

## Cumulative effect — one paragraph

The test that most changed the verdict was Test 3 (feature importance): discovering that `month` carries 93.6% of the model's signal revealed that the RF is primarily a seasonal predictor, not the land-use regression the project brief calls for. The worst single finding is Case 2 in the failure gallery — the uncertainty intervals covering only 45.7% of test outcomes, which makes the model's confidence output unusable. The result is not for: heating-season individual-event prediction, intervention scenario modelling, or any use requiring spatial differentiation across urban typologies. Confidence in the ITERATE verdict is ~75% — the core metrics (R² = 0.639, MAE = 9.96) are reproducible and meet the brief's stated thresholds, but the land use signal is too marginal to justify deployment without ERA5 weather features added.

---

## Sign-off

- [ ] Every number in `evaluation-report.md` traces to an entry here.
- [x] At least one entry **weakened or killed** a claim (Tests 2, 3, 4, 5 all weakened the verdict).
- [x] The verdict in the report matches the cumulative effect above (ITERATE).
- [ ] A fresh clone + `Run all` of `05-evaluation.ipynb` reproduces every logged number.

**Evaluated by:** Rim, Martina, Rashi, Bhavana
