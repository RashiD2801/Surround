# Conclusions Brief — Krakow PM2.5 Spatial Regression

- **Analysis:** Krakow PM2.5 prediction from urban land use and ERA5 weather features
- **Version:** v2 (ERA5 iteration, Session 5)
- **Produced by:** Rim, Martina, Rashi, Bhavana
- **Notebook:** `notebooks/03-modelling.ipynb`
- **Validity audit:** `docs/session 5/failure-gallery.md` (Track A equivalent)

---

## 1 · The decision this serves

- **User:** Krakow Municipal Planning Office analyst reviewing a development application that requires an air quality impact assessment.
- **Decision:** Whether to require green-infrastructure conditions (tree planting, setbacks, road closures) on a new development based on predicted monthly mean PM2.5 at the site location.
- **Cadence / horizon:** Weekly — one to two planning applications per month. Monthly PM2.5 prediction horizon (not event-level).

---

## 2 · The data & systems it rests on

- **Sources:**
  - PM2.5 daily measurements: 7 GIOŚ monitoring stations in Krakow, 2019–2024 (`data/raw/`)
  - Land use: Urban Atlas 2018 at 500m radius buffer per station (`data/output/krakow_spatial_features.csv`)
  - Weather: ERA5-Land hourly temperature and boundary layer height via Open-Meteo historical API, aggregated to monthly means (`data/training/era5_monthly.csv`)

- **What you computed vs what was given:**
  - Given: daily PM2.5 readings, raw land use polygons, ERA5 hourly reanalysis
  - Computed: monthly mean PM2.5 per station, land use percentage coverage at 500m radius, monthly mean temperature and BLH per station, LOSO train/val/test split, Random Forest model

- **Coverage & gaps:**
  - 7 stations, all within ~15 km of Krakow city centre
  - 2019–2024 (72 months); 471 station-months after aggregation
  - 37/471 BLH values are NaN (Open-Meteo gaps); filled with median imputation
  - No stations outside central Krakow — rural, peri-urban, and outer-district typologies are unrepresented

- **The out-of-sample slice:**
  - Test set: nowa_huta + zloty_rog (138 station-months) — held out from all modelling decisions until final evaluation
  - These stations were never seen during training or hyperparameter choices

---

## 3 · The claims

> **Claim 1:** A Random Forest model trained on ERA5 weather features and Urban Atlas land use can predict monthly mean PM2.5 at held-out Krakow monitoring stations with R²=0.850 and MAE=6.48 µg/m³.
> - **Evidence:** test set evaluation on nowa_huta + zloty_rog (138 station-months); seasonal baseline MAE = 10.24 µg/m³ for comparison; 36.7% improvement over seasonal mean
> - **Robustness:** LOSO-CV MAE = 11.15 ± 1.46 µg/m³ across 5 folds; val set (kurdwanow) R²=0.904, MAE=4.99 µg/m³; test metrics computed once on the sacred split
> - **Threats ruled out:** data leakage — LOSO group split ensures no station appears in both train and test; temporal leakage — monthly aggregation used, no lag features that require knowing previous PM2.5
> - **Confidence & caveats:** ~85% — strong overall performance but weather (ERA5) drives 96.3% of the signal; land use contributes 2.3%; the model predicts PM2.5 well but does not strongly establish urban form as the cause

> **Claim 2:** When ERA5 weather is controlled for, urban land use features contribute only 2.3% of the model's predictive signal in a 7-station Krakow dataset.
> - **Evidence:** feature importance analysis — `mean_temp_monthly` 72.7%, `blh_monthly` 23.6%, all 13 land use features combined 2.3%
> - **Robustness:** in v1 (no ERA5), land use appeared at 6.4% — the drop to 2.3% in v2 confirms the v1 estimate was inflated by `month` proxying for weather effects that co-vary with urban form
> - **Threats ruled out:** the reduction is not a modelling artefact — it held after retraining with identical hyperparameters on an expanded feature set
> - **Confidence & caveats:** this is a finding about 7 stations within 15 km sharing the same meteorological regime; it does not rule out detectable urban form effects in a dataset with greater spatial diversity

---

## 4 · What we are NOT claiming

- **Not claiming land use causes PM2.5 levels.** The model is correlational. "More urban green → less PM2.5" is an observed association across 7 stations, not a causal finding.
- **Not claiming the model works for unmeasured grid cells reliably.** Trained on 4 stations; extrapolation to the 32,700 unmeasured grid cells across Krakow, especially >2 km from any training station, is speculative.
- **Not claiming deployment-ready uncertainty intervals.** The 90% tree-quantile intervals cover only 72.5% of test outcomes (target ≥ 85%). They must not be reported to planning analysts without a disclaimer.
- **Not claiming strong urban form–PM2.5 correlation.** The project's core hypothesis (urban planning correlates with air pollution) is supported weakly — 2.3% land use signal is real but too small to drive planning decisions alone. More diverse stations are needed to test this robustly.
- **Not claiming individual-event prediction.** The model predicts monthly means. An analyst cannot use it to assess a specific pollution episode.

---

## 5 · Ethical considerations & caveats

- **Whose data / whose neighbourhoods are represented?** All 7 stations are within Krakow's built-up area. Nowa Huta (industrial east) and Zloty Rog (residential south) are in the test set. Training stations represent central, residential, and mixed-use typologies. Outer suburban and peri-urban areas have no representation.

- **Who is missing, and could the gap misdirect resources?** Lower-income districts in outer Krakow — where older housing stock and coal/wood heating is more prevalent — have no monitoring stations and are not represented in the training data. If this model were used to allocate green-infrastructure investment, it would systematically under-serve areas outside its spatial coverage. Any deployment must flag predictions far from training stations as unreliable.

- **Correlational, not causal.** The model cannot be used to predict the effect of a specific intervention (e.g., "if we plant 500 trees here, PM2.5 will drop by X µg/m³"). It observes associations across existing station typologies; it does not model intervention effects.

- **Snapshot.** The Urban Atlas land use data is from 2018; the ERA5 data covers 2019–2024. The model does not capture recent urban changes (new developments, demolitions, changed heating infrastructure after Poland's coal-reduction policies). Predictions more than 2–3 years after the training period should be treated with extra caution.

---

## Sign-off

- **Brief written by:** Rim, Martina, Rashi, Bhavana
- **Reviewed by another team:** [reviewer team] on [date]
- **Last updated:** 2026-06-08
