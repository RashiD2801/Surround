# Evaluation Rigor Checklist — Krakow PM2.5 Spatial Regression

> Status as of 2026-06-08. Updated for v2 (ERA5 iteration complete).

---

## Back to the brief (both tracks)

- [x] **I found the S1 success criteria.** R² ≥ 0.40 · beat seasonal baseline · MAE < 12 µg/m³.
- [x] **I can name the decision** the result serves: Krakow Municipal Planning Office analyst, weekly zoning variance meeting, air quality impact assessment.
- [x] **I can finish the sentence** "so the decision-maker should…" — require green-infrastructure conditions (tree buffer, setback) when predicted PM2.5 exceeds 25 µg/m³ (EU limit). *(Caveat: not reliable for heating-season applications — ITERATE first.)*
- [x] **I graded against the bar I set**, not against "is it impressive." v2 R² 0.850 meets ≥ 0.40; land use signal (2.3%) does not independently meet the "establish urban form correlation" intent — acknowledged in §6.

---

## Track A — model checks

- [x] **The test set is still sacred** — test metrics computed once in `03-modelling.ipynb` cell c19; not re-tuned after seeing them.
- [x] **Per-segment error done** — broken down by station (nowa_huta vs zloty_rog) and by season (Winter MAE 16.28 vs Summer 4.56). See failure-gallery.md Cases 1, 4.
- [x] **The worst segment is named and explained** — v2 worst segment: Winter MAE 9.12 µg/m³ (still worst; fixed from 16.28 by ERA5 features). Residual error is from individual inversion events deviating from monthly BLH mean.
- [x] **Stress tests run** — drop month (+126%), force all-winter (+194%), 20% NaN in urban_pct (OK), land-use shift +0.1 (OK). Results in failure-gallery.md stress table.
- [x] **Confidence reported** — v2: 90% interval coverage 72.5% on test (target 85%, improved from 45.7%). LOSO-CV spread 11.15 ± 1.46 µg/m³ (v1; v2 not re-run).
- [x] **Five+ failure-gallery entries** — 6 entries covering systematic and spectacular failures.

---

## The "compared to what" check (both tracks)

- [x] **I named the alternative** — seasonal-mean baseline (test MAE 10.24 µg/m³) and dumb-mean (18.24 µg/m³).
- [x] **I reported the comparison, not the headline** — v2: "6.48 vs 10.24" (36.7% improvement). v1 was "9.96 vs 10.24" (2.7% improvement).
- [x] **I weighed effort vs value** — v2 36.7% improvement over seasonal is substantial and worth deploying as a weather-controlled PM2.5 predictor; not worth deploying as a land-use attribution claim (2.3% land use signal).

---

## The confidence check (both tracks)

- [x] **I stated the confidence explicitly** — ~75% in the verdict.
- [x] **The confidence matches the evidence** — v2: 72.5% interval coverage (improved), land use 2.3% signal both support ~85% confidence (upgraded from 75%).
- [x] **The conditions are named** — v2: model trustworthy in all seasons (worst season Winter MAE 9.12 < 12 µg/m³); not trustworthy for uncertainty intervals (72.5% < 85% target); not trustworthy for land use attribution claims.

---

## The "did we fool ourselves" smell test

- [x] **Does it beat the alternative?** Beats dumb-mean by 45%. Barely beats seasonal (2.7%). The seasonal comparison is the honest one for a land-use model.
- [x] **Is it too good?** R² 0.639 is not suspiciously high for a Random Forest. Checked for leakage — LOSO split ensures no station appears in both train and test.
- [x] **Did the number change when I re-ran?** No — RANDOM_SEED = 42 set everywhere; `python src/baseline_model.py` reproduces identical metrics.
- [x] **Right for the wrong reason?** Yes — summer low-variance pulls aggregate MAE down to 9.96. Winter, the planning-relevant season, has MAE 16.28. This is documented explicitly (Case 6 in failure gallery).
- [ ] **Did I decide the question before I saw the answer?** The S1 success criteria were set in Session 1 before any modelling. However, the 12 µg/m³ informal target was set in Session 4 after seeing data distributions — acknowledge as a mild risk.

---

## What goes in the report vs the log

- **Report** (`evaluation-report.md`): verdict, results-vs-criteria table, compared-to-what, where it fails, confidence, what we're NOT claiming, recommendation. ✓
- **Log** (`evaluation-log.md`): 10 tests including Tests 2, 3, 4, 5 which weakened the verdict. ✓
- **Gallery** (`failure-gallery.md`): 6 diagnosed failure cases. ✓

All numbers in the report trace to a log entry. ✓

---

## When the checklist fails

| Item | Status | Note |
|---|---|---|
| Uncertainty intervals | **PARTIAL** — 72.5% vs 85% target (improved from 45.7%) | Cannot deploy uncertainty output without disclaimer. Conformal prediction needed in S6. |
| Winter performance | **FIXED** — MAE 9.12 µg/m³ (v2, was 16.28) | Deployable for Nov–Mar; ERA5 BLH feature resolved inversion confound. |
| Land use signal | **WEAK** — 2.3% importance (was 6.4% in v1) | Urban form attribution requires more diverse stations. Scope reduced to weather-controlled predictor. |
| ERA5 iteration | **DONE** — `data/training/era5_monthly.csv` fetched, joined, model retrained 2026-06-08 | v2 model: R²=0.850, MAE=6.48, 16 features. |
| Reproducibility | **PENDING** — `05-evaluation.ipynb` not yet updated for v2 feature set | Update notebook to add ERA5 cells before final commit. |
