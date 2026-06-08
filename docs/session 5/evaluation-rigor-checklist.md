# Evaluation Rigor Checklist — Krakow PM2.5 Spatial Regression

> Status as of 2026-06-08. Check each box before writing a single line of the verdict.

---

## Back to the brief (both tracks)

- [x] **I found the S1 success criteria.** R² ≥ 0.40 · beat seasonal baseline · MAE < 12 µg/m³.
- [x] **I can name the decision** the result serves: Krakow Municipal Planning Office analyst, weekly zoning variance meeting, air quality impact assessment.
- [x] **I can finish the sentence** "so the decision-maker should…" — require green-infrastructure conditions (tree buffer, setback) when predicted PM2.5 exceeds 25 µg/m³ (EU limit). *(Caveat: not reliable for heating-season applications — ITERATE first.)*
- [x] **I graded against the bar I set**, not against "is it impressive." R² 0.639 meets ≥ 0.40; land use signal does not independently meet the "establish urban form correlation" intent.

---

## Track A — model checks

- [x] **The test set is still sacred** — test metrics computed once in `03-modelling.ipynb` cell c19; not re-tuned after seeing them.
- [x] **Per-segment error done** — broken down by station (nowa_huta vs zloty_rog) and by season (Winter MAE 16.28 vs Summer 4.56). See failure-gallery.md Cases 1, 4.
- [x] **The worst segment is named and explained** — Winter months: MAE 16.28 µg/m³, mechanism is missing BLH/temperature inversion features, not noise.
- [x] **Stress tests run** — drop month (+126%), force all-winter (+194%), 20% NaN in urban_pct (OK), land-use shift +0.1 (OK). Results in failure-gallery.md stress table.
- [x] **Confidence reported** — 90% interval coverage 45.7% on test (target 85%). LOSO-CV spread 11.15 ± 1.46 µg/m³.
- [x] **Five+ failure-gallery entries** — 6 entries covering systematic and spectacular failures.

---

## The "compared to what" check (both tracks)

- [x] **I named the alternative** — seasonal-mean baseline (test MAE 10.24 µg/m³) and dumb-mean (18.24 µg/m³).
- [x] **I reported the comparison, not the headline** — "9.96 vs 10.24" (2.7% improvement), not just "9.96 µg/m³".
- [x] **I weighed effort vs value** — the 2.7% improvement over seasonal is not worth deploying as a land-use regression claim. The R² gain is real but partially driven by the seasonal component.

---

## The confidence check (both tracks)

- [x] **I stated the confidence explicitly** — ~75% in the verdict.
- [x] **The confidence matches the evidence** — wide uncertainty intervals (45.7% coverage), month dominance (93.6%) both support medium confidence, not high.
- [x] **The conditions are named** — model trustworthy in Apr–Oct (MAE 4–10 µg/m³); not trustworthy in Nov–Mar (MAE 16.28 µg/m³); not trustworthy anywhere for uncertainty intervals.

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
| Uncertainty intervals | **FAILED** — 45.7% vs 85% target | Cannot deploy uncertainty output. Conformal prediction needed. |
| Winter performance | **FAILED** — MAE 16.28 vs 12 µg/m³ target | Not deployable for Nov–Mar applications without ERA5 features. |
| Land use signal | **PARTIAL** — 2.7% over seasonal | ITERATE: add BLH + temperature. |
| Reproducibility | **PENDING** — `05-evaluation.ipynb` not yet Run All verified | Complete before committing evaluation report. |
