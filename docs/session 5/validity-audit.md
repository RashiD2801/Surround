# Validity Audit — Krakow PM2.5 Spatial Regression

- **Analysis:** Random Forest regression — monthly PM2.5 from ERA5 weather + Urban Atlas land use
- **The claim under audit:** A model trained on ERA5 temperature, boundary layer height, and Urban Atlas land use features can predict monthly mean PM2.5 at held-out Krakow stations (R²=0.850, MAE=6.48 µg/m³), and urban land use contributes a detectable but small signal (2.3% feature importance) once weather is controlled.
- **Data drawn from:** GIOŚ PM2.5 monitoring (7 stations, 2019–2024), Urban Atlas 2018, ERA5-Land via Open-Meteo
- **Maintainer:** Rim, Martina, Rashi, Bhavana
- **Last updated:** 2026-06-08

---

## The four threats

### 1 · Confounding — a third thing drives both

- **Present?** Yes — partially mitigated in v2, residual concern remains.
- **Test:** Feature importance analysis before and after adding ERA5. In v1 (no ERA5): `month` = 93.6% importance, land use = 6.4%. In v2 (with ERA5 `mean_temp_monthly` + `blh_monthly`): weather = 96.3%, land use = 2.3%. The drop in land use importance when weather was properly controlled reveals that v1's 6.4% was partly a confound — `month` was proxying for weather that also co-varies with urban form.
- **Verdict:** Weather is the dominant confounder and is now explicitly modelled. Residual confound: all 7 stations are in Krakow and share the same weather regime, so station-to-station PM2.5 differences are small relative to seasonal swings. Urban form effects cannot be cleanly separated from any remaining unmodelled local factors (traffic, industry, heating type) with only 7 stations.

---

### 2 · Selection bias — your data isn't who you think

- **Present?** Yes — significant spatial selection bias.
- **Test:** All 7 stations are regulatory compliance monitors, sited to represent "worst-case" or "background" conditions in their local zone — not a random spatial sample of Krakow. They are all within the built-up urban core (~15 km range). No stations in outer suburbs, peri-urban areas, or rural fringe. The model's training distribution is therefore biased toward central, established urban typologies (dense continuous fabric, mixed-use, industrial).
- **Verdict:** The model's spatial coverage claim is restricted to typologies similar to the 7 training/test stations. Predictions for outer-district grid cells with different land use patterns (low-density residential, greenfield) are extrapolations outside the training distribution. The LOSO split mitigates temporal leakage but cannot fix spatial selection bias — it only tests generalisation to the same biased station set.

---

### 3 · Spurious correlation — something lined up by chance

- **Present?** Low risk — but flagged for one specific case.
- **Test:** With only 7 stations and 471 station-months, overfitting is possible. Three checks applied: (1) LOSO-CV MAE = 11.15 ± 1.46 µg/m³ — moderate spread, no single fold collapses; (2) test set was genuinely held out until model was locked — no iterative peeking; (3) summer performance (MAE 3.71 µg/m³) is suspiciously good, but the mechanism is understood: low variance in summer PM2.5 across all stations, not spurious fit.
- **Flagged case:** `blh_monthly` at 23.6% importance is plausible meteorologically (boundary layer height directly controls pollutant dispersion), but with 7 stations all sharing the same BLH values (ERA5 grid resolution ~9 km, so all stations may pull from the same or adjacent grid cell), this feature may be capturing city-wide weather variation rather than station-specific mixing. It is not spurious, but it is not station-specific.
- **Verdict:** Low risk of spurious correlation. The dominant features (temperature, BLH) have a clear physical mechanism. The test set was held out cleanly.

---

### 4 · Cherry-picking — the story chose the data

- **Present?** Mild risk — one threshold set after seeing data.
- **Test:** The S1 success criteria (R² ≥ 0.40, MAE < 12 µg/m³, beat seasonal baseline) were set in Session 1 before any modelling. The model is graded against these pre-set bars. The 12 µg/m³ MAE threshold was set informally in Session 4 after reviewing PM2.5 data distributions — this is acknowledged as a mild post-hoc risk.
- **Cuts that did not support it:** (1) Land use feature importance is 2.3% — the project's core hypothesis (urban form drives PM2.5) is not strongly supported; this is documented, not hidden. (2) Winter MAE = 9.12 µg/m³ (v2) — the worst season, reported explicitly. (3) Uncertainty intervals cover only 72.5% of test outcomes, below the 85% target — reported in both the failure gallery and checklist. (4) zloty_rog MAE (7.48) is worse than nowa_huta (5.52) — the station bias is documented, not averaged away.
- **Verdict:** No cherry-picking detected. All negative findings are included in the evaluation report and failure gallery. The one mild risk (12 µg/m³ threshold set in S4) is explicitly flagged in the rigor checklist.

---

## Robustness / sensitivity table

| Cut / choice | Effect | Holds? | Note |
|---|---|---|---|
| All data (headline) | R²=0.850, MAE=6.48 | — | Reference — v2 model |
| Worst season (Winter) | MAE=9.12 µg/m³ | Yes | Still below 12 µg/m³ threshold; was 16.28 in v1 |
| Worst station (zloty_rog) | MAE=7.48 µg/m³ | Yes | Gap vs nowa_huta (5.52) is sensor placement bias, not model failure |
| Without ERA5 features (v1) | R²=0.639, MAE=9.96 | Yes | Performance holds but weakly; ERA5 is critical for winter |
| LOSO-CV fold spread | 11.15 ± 1.46 µg/m³ | Yes | Moderate spread; ul_dietla worst fold (13.10) |
| Drop `mean_temp_monthly` | Not tested on v2 | Unknown | v2 fragility point — now 72.7% importance; recommend stress test in S6 |
| Out-of-sample slice | nowa_huta + zloty_rog (138 rows) | Yes | Sacred split; test touched once |

---

## Summary

- **Threats that remain:** spatial selection bias (7 central Krakow stations only); BLH not station-specific at ERA5 resolution; 12 µg/m³ threshold mild post-hoc risk.
- **Conditions the conclusion is restricted to:** monthly aggregation; Krakow urban core typologies; 2019–2024 weather regime; stations within ~15 km of each other sharing the same meteorological regime.
- **The verdict's "where it fails" row:** land use signal is 2.3% with proper weather controls — the urban form–PM2.5 correlation claim requires more spatially diverse stations to validate robustly.

---

## Sign-off

- **Audit by:** Rim, Martina, Rashi, Bhavana
- **Reviewed by another team:** [reviewer team] on [date]
- **Threats addressed:** all four — yes
