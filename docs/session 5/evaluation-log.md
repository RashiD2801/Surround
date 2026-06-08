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

---

> **Test 11:** ERA5 iteration — v2 model test evaluation (2026-06-08)
> - **What I tested — and why:** after adding `mean_temp_monthly` and `blh_monthly` from Open-Meteo ERA5-Land to the training dataset, re-ran the full split + model + test evaluation to see if the ITERATE recommendation was productive.
> - **What it showed:** test R² = **0.850** (v1: 0.639), test MAE = **6.48 µg/m³** (v1: 9.96), seasonal improvement = **36.7%** (v1: 2.7%), winter MAE = **9.12 µg/m³** (v1: 16.28), uncertainty coverage = **72.5%** (v1: 45.7%). Val R² = 0.904, Val MAE = 4.99. Feature importances: `mean_temp_monthly` 72.7%, `blh_monthly` 23.6%, `month` 1.4%, all land use 2.3%.
> - **What I concluded:** ITERATE was productive. All three S1 criteria are now met. ERA5 fixed the winter failure and the seasonal over-reliance. However, land use importance dropped further (6.4% → 2.3%) when weather was properly controlled — the urban form signal is even weaker than v1 suggested. This is the honest finding: weather dominates PM2.5 in Krakow; urban form adds ~2%.
> - **What it changed in the verdict:** upgraded from ITERATE to CONDITIONAL DEPLOY. The model is deployable as a weather-controlled PM2.5 estimator but not as a land-use attribution model.

---

> **Test 12:** Feature importance shift — land use signal with ERA5 control
> - **What I tested:** whether adding proper weather controls would raise or lower land use feature importance.
> - **What it showed:** land use dropped from 6.4% (v1) to 2.3% (v2). The v1 land use importance was inflated because `month` was proxying for weather effects that co-vary with urban form. With real weather controls, the residual land use signal is 2.3%.
> - **What I concluded:** this is a key scientific finding: when temperature and atmospheric mixing are controlled, Krakow's 7 stations show very little spatial variation attributable to land use. The stations are all within 15 km and share the same meteorological regime. Urban form effects, if they exist, are too small to detect with 7 stations.
> - **What it changed in the verdict:** added to §6 ("not claiming strong land use–PM2.5 correlation"); v2 failure gallery Case 3 updated.

---

## Tests we did NOT run — and why

| Test we skipped | Why | What downstream needs to know |
|---|---|---|
| Per-district analysis (Śródmieście vs Nowa Huta) | Only 7 stations total; Nowa Huta = test station (sacred until test touched). Post-test district analysis not prioritised in S5 | S6 should run district breakdown once retraining includes more stations |
| Conformal prediction calibration | Requires ≥ 10 stations for calibration set; we have 7 | S5 ITERATE task: implement conformal prediction after adding ERA5 features and ideally more station data |
| Temporal drift test (2019–2024 year-by-year) | Monthly aggregation across all years; year-by-year breakdown would need ~12 rows per station-year. Low statistical power | S6: flag if model is applied to 2025 data without revalidation |
| Adding ERA5 features (BLH, temperature) | ~~Data not yet in the training dataset~~ | **Done in S5 iteration — see Test 11** |

---

## Cumulative effect — one paragraph

**v1 verdict (before ERA5 iteration):** The test that most changed the v1 verdict was Test 3 (feature importance): `month` = 93.6% revealed the model was primarily a seasonal predictor. The worst single finding was uncertainty coverage at 45.7%. Confidence: ~75%. Verdict: ITERATE.

**v2 verdict (after ERA5 iteration, Tests 11–12):** ERA5 features transformed the model — R² 0.639 → 0.850, MAE 9.96 → 6.48, winter MAE 16.28 → 9.12, uncertainty coverage 45.7% → 72.5%. All three S1 criteria are now met. The key finding is that proper weather controls (ERA5) reduced land use importance from 6.4% → 2.3%, confirming that within Krakow, weather patterns rather than land use drive PM2.5 spatial variation at 7-station resolution. Confidence: ~85%. Verdict: CONDITIONAL DEPLOY.

---

## Sign-off

- [ ] Every number in `evaluation-report.md` traces to an entry here.
- [x] At least one entry **weakened or killed** a claim (Tests 2, 3, 4, 5 all weakened the verdict).
- [x] The verdict in the report matches the cumulative effect above (ITERATE).
- [ ] A fresh clone + `Run all` of `05-evaluation.ipynb` reproduces every logged number.

**Evaluated by:** Rim, Martina, Rashi, Bhavana
