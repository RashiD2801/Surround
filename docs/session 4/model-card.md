# Model Card — krakow-pm25-spatial-rf-v1

> Save as `docs/model-cards/krakow-pm25-spatial-rf-v1.md` in your repo.
>
> Structure follows **Mitchell et al. 2019** — "Model Cards for Model
> Reporting." Eight sections. All eight matter.

---

## 1 · Model details

- **Model name:** `krakow-pm25-spatial-rf-v1`
- **Version:** v1.0 · 2026-05-28
- **Type:** Random Forest Regressor, sklearn 1.5.x, wrapped in `sklearn.Pipeline`
- **Developed by:** Rim, Martina, Rashi, Bhavana (Surround seminar, Session 4)
- **Trained on:** 2026-05-28 (training data covers 2019–2024, COVID window excluded)
- **Pipeline artifact:** `models/baseline.joblib`
- **Code:** `src/baseline_model.py`
- **Training notebook:** `notebooks/03-modelling.ipynb`
- **License of code:** MIT
- **Contact:** team repo — `docs/model-cards/krakow-pm25-spatial-rf-v1.md`

---

## 2 · Intended use

### 2.1 Primary intended uses

- **User:** Planning analyst at Krakow Municipal Planning Office, reviewing a developer's application or a green-infrastructure proposal on Thursday morning before the weekly zoning variance meeting.
- **Decision:** Which green-infrastructure interventions (urban tree planting, road closure, building setback) to require as conditions of development approval. The model provides the "expected PM2.5 level" column on the recommendation sheet.
- **Decision frequency:** Weekly — one or two planning applications per month that trigger an air quality impact assessment.
- **Decision time scale:** The analyst has 2–3 days to review an application; the model output is one input among several. The planner also reads the site inspection report, traffic study, and community feedback before deciding.

*Example use:* A developer proposes a mixed-use building at Aleja Słowackiego. The analyst enters the parcel coordinates into the dashboard, reads the model's predicted monthly PM2.5 for that location (e.g., 42 µg/m³), checks the uncertainty interval (±12 µg/m³), and uses this to anchor a discussion about requiring a 20m green buffer along the street frontage.

### 2.2 Primary intended users

- Krakow Municipal Planning Office staff (land-use and transport planning)
- Municipal environmental department (air quality monitoring and reporting)
- Academic researchers studying urban PM2.5 gradients in post-coal-transition cities

### 2.3 Out-of-scope uses

**The most important subsection in this card.**

- **Not for real-time or daily air quality forecasting.** The model predicts monthly means from static urban form features. It has no knowledge of today's weather, wind speed, or traffic event. Using it to warn residents of tomorrow's air quality is incorrect.
- **Not for individual health risk advice.** The model speaks to neighbourhood-level monthly mean PM2.5. An individual's actual exposure depends on time spent outdoors, indoor ventilation, route taken, and dozens of factors not in this model.
- **Not for regulatory compliance assessments.** EU Air Quality Directive measurements must use certified reference instruments with specific QA/QC protocols. This model uses AQICN monitoring data (indicative quality) and cannot substitute for a legally accredited measurement.
- **Not for predictions in areas far from training stations (>3km from nearest station).** The model was trained on 10 stations within the city boundary. Predictions for Wieliczka, Niepołomice, or the Nowa Huta outer periphery extrapolate beyond training data. Uncertainty intervals will be wide; treat with caution.
- **Not for causal attribution.** "This area has low NDVI and high PM2.5" is a correlation. "Planting trees here will reduce PM2.5 by X µg/m³" is a causal extrapolation outside the model's training regime. Intervention scenarios should be reported with ±40–60% uncertainty bands and explicit caveats.

---

## 3 · Factors

> Relevant conditions along which performance is expected to vary — these
> are the slices to dig into in Session 6's failure gallery.

- **Station type (traffic / background / industrial):** Traffic stations are directly influenced by road proximity; urban-form features (road_density_500m) explain more variance there. Background stations in parks are influenced by city-wide heating; the model may over-predict there in winter if the spatial features don't capture the sheltered micro-climate. Why it matters: different station types will show different MAEs in the per-segment table.
- **Season (winter vs summer):** PM2.5 swings 3–4× between winter (coal heating, temperature inversions) and summer (background levels). The `month` feature and `blh_monthly` (boundary layer height) capture this. Why it matters: if the model systematically under-predicts January at industrial stations, the failure is in the inversion proxy (BLH), not the urban form features.
- **District (Śródmieście / Nowa Huta / suburban):** Śródmieście stations are in dense, mixed-use urban fabric; Nowa Huta is a heavy-industrial eastern district; suburbs are low-density. The 10 training stations sample these unequally (6 central, 2 industrial, 2 background). Why it matters: predictions for undersampled districts will have wider intervals.
- **Placement bias — Złoty Róg:** This station reads 20–30% lower than expected from its urban context (sheltered by trees and buildings on three sides). It is in the test set. Test MAE for Złoty Róg should be interpreted with this caveat: the model is predicting what PM2.5 "should be" for its urban form; the sensor systematically underreports. See `docs/data-cleaning-log.md` Transform 7.
- **Atmospheric haze / NDVI bias:** During high-PM2.5 episodes, atmospheric scattering reduces measured NDVI from Sentinel-2. Correlated predictor and confound — greenness and pollution affect each other. The summer cloud-masked composite reduces but does not eliminate this bias.

---

## 4 · Metrics

### 4.1 Chosen metrics + why

| Metric | What it measures | Why it's the right choice |
|---|---|---|
| MAE (µg/m³) | Mean absolute error in target units | Directly interpretable: "on average, our prediction is off by X µg/m³." Robust to the Nowa Huta Feb 2024 outlier spike (287 µg/m³) that would inflate RMSE. |
| R² | Proportion of PM2.5 variance explained by urban form features | The project brief's success criterion (R² ≥ 0.40). Comparative: did we explain more variance than the seasonal baseline? |
| Seasonal-relative MAE | Model MAE ÷ seasonal-mean baseline MAE | Tests whether urban form features add signal beyond knowing the calendar. A ratio < 1.0 means we beat the seasonal clock. |
| Coverage of 90% tree-quantile interval | Fraction of true val values inside [p5, p95] of tree predictions | Uncertainty calibration. Target ≥ 85% on val; if below, intervals are overconfident. |

### 4.2 Decision thresholds

The model output (monthly mean PM2.5, µg/m³) is compared to EU reference levels in the dashboard:

- Output > 25 µg/m³ → flag for human review (EU annual mean limit value)
- Output > 15 µg/m³ → WHO 2021 guideline exceeded — note in recommendation
- Output < 10 µg/m³ → within WHO guideline range — no flag

These thresholds are applied to model predictions, not regulatory measurements. The dashboard must display this caveat.

### 4.3 Variation and uncertainty

- Cross-fold spread reported as **mean ± standard deviation** across 10 LOSO folds (one held-out station per fold).
- Point predictions accompanied by 90% tree-quantile intervals (5th–95th percentile across 300 trees). Coverage target: ≥ 85% on val.
- Expected coverage degrades for grid cells >2km from any training station — this is the "extrapolation warning zone" noted in the dashboard.

---

## 5 · Evaluation data

- **Source:** `data/processed/aqicn-monthly-{train,val,test}.parquet`
- **Splitting strategy:** Leave-one-station-out group split. No station appears in more than one set. See `src/split_data.py` and `docs/modelling-log.md` decision #1.
- **Train set:** 7 stations — Aleja Krasińskiego, ul. Dietla, Bujaka, Piastów, Złoty Róg (NB: Złoty Róg is in TEST — to be corrected in actual split), Kraków-Balice, Wadów, Swoszowice *(exact list from `split_data.py`)*
- **Val set:** Kurdwanów station — 2019-01 to 2024-12 (minus COVID window, minus low-completeness months). ~55 station-months.
- **Test set:** Złoty Róg + Nowa Huta — SACRED. Touched once on [date to fill when model locked].
- **Preprocessing:** See `src/clean_data.py` and `docs/data-cleaning-log.md`. Key decisions: COVID window excluded (Mar–May 2020), 5 negative PM2.5 clipped, Kurdwanów Dec 2022 flatline removed, coordinate corrections applied for 2 stations.
- **Known limitations:** Złoty Róg reads 20–30% low (sheltered placement bias). Nowa Huta has one verified extreme event (Feb 2024, 287 µg/m³) that is real data kept in the dataset. Both stations are in the test set — these caveats affect interpretation of test MAE.

---

## 6 · Training data

- **Source:** Same as evaluation, train split only (7 stations, ~420 station-months).
- **Distribution caveats:** Training stations skewed toward central Krakow (Śródmieście district, 5 of 7 stations). Only one industrial-zone station (training) — heavy-industrial Nowa Huta is in the test set. One suburban station (Balice/Kraków airport area). The model may underfit industrial zones.
- **Documented biases that propagate:** NDVI haze bias (Sentinel-2 summer composite reduces NDVI during high-PM2.5 conditions — attenuated correlation with target). OSM building heights missing for ~70% of buildings (street-canyon effect unmodelled). See `docs/datasheets/aqicn-pm25.md` section 5.

---

## 7 · Quantitative analyses

### 7.1 Aggregate performance

| Split | Model | MAE (µg/m³) | R² | 90% coverage |
|---|---|---|---|---|
| train | dumb-mean | ~17.8 | — | — |
| train | seasonal | ~6.2 | — | — |
| train | RF (ours) | ~3.1 | ~0.92 | — |
| val | dumb-mean | ~18.4 | — | — |
| val | seasonal | ~8.9 | — | — |
| val | RF (ours) | [TBD] | [TBD] | [TBD] |
| val LOSO (mean ± std) | RF (ours) | [TBD ± TBD] | [TBD ± TBD] | — |
| **test (final)** | dumb-mean | [TBD] | — | — |
| **test (final)** | seasonal | [TBD] | — | — |
| **test (final)** | RF (ours) | [TBD] | [TBD] | [TBD] |

*[TBD] cells to be filled when model is locked and test is touched once.*

### 7.2 Disaggregated performance

> Performance broken down by the factors in section 3. Average hides the part that's broken.

#### By season (on val — Kurdwanów)

| Season | Months | MAE (expected) | Note |
|---|---|---|---|
| Winter (heating) | Nov–Mar | Higher | Inversion-driven peaks, BLH is key feature |
| Summer (background) | Jun–Aug | Lower | Low PM2.5, smaller absolute errors |
| Shoulder | Apr–May, Sep–Oct | Intermediate | Coal ban transition effect visible |

#### By station (LOSO-CV — one row per held-out station)

| Held-out station | Type | Expected MAE direction | Note |
|---|---|---|---|
| Złoty Róg | Background (sheltered) | Higher | Sensor reads 20-30% low vs urban form prediction |
| Nowa Huta | Industrial | Higher | Only industrial station in test; training set has one industrial station |
| Kurdwanów | Background/industrial mix | [Val station — MAE from val split] | Dec 2022 flatline dropped from training |
| Other 7 stations | Various | [From LOSO-CV folds] | |

> Highlight any slice where performance is >50% worse than aggregate — first entries in Session 6's failure gallery.

---

## 8 · Ethical considerations & caveats

### 8.1 Data considerations

- **Whose data is in the training set?** Publicly funded municipal air quality monitoring network (AQICN / WIOŚ). No individuals. Satellite imagery (Copernicus/Sentinel-2) is open data. ERA5-Land reanalysis is ECMWF open data. OSM is CC-BY-SA.
- **Whose data is missing?** Krakow's low-income and outer suburban areas (Nowa Huta periphery, Bieżanów-Prokocim) have no monitoring stations. Private monitoring and low-cost sensors (e.g., AirVisual community network) were not included.
- **Could missing data systematically harm anyone?** The model underrepresents outer Krakow suburbs and Nowa Huta. Planning decisions using this model could underestimate pollution exposure for residents in those areas — the people often most affected by poor air quality and least represented in policy discussions. Mitigation: document uncertainty zones explicitly; do not use model output as sole basis for approvals in areas far from training stations.

### 8.2 Mitigation strategies

- Uncertainty intervals widen for locations >2km from any training station — these are shown in the dashboard with an explicit "extrapolation warning" badge.
- Złoty Róg's `station_bias_flag = "sheltered_placement"` prevents it from being used as a lead validation fold. Test metrics at Złoty Róg carry a written caveat in this card.
- The model card is rendered in the Session 7 UI alongside every prediction — the planner always sees the out-of-scope list before acting on the output.

### 8.3 Caveats and recommendations

- **The model is correlational, not causal.** Saying "tree planting here will reduce PM2.5 by 5 µg/m³" requires a causal study design (e.g., difference-in-differences before/after an intervention), not a cross-sectional regression. All intervention scenarios should be labelled "association, not prediction."
- **The model is a post-coal-ban snapshot.** Trained on 2019–2024 data, after Krakow's 2019 coal-burning ban. It does not apply to pre-ban conditions. The Low Emission Zone (started January 2024) may change the traffic-PM2.5 relationship further — re-validate when 2024–2025 data accumulates.
- **The model is one input among several.** Do not use as the sole basis for a zoning approval, health assessment, or community consultation outcome.
- **Re-validate on an 18-month cycle.** PM2.5 trends, urban development, and station network changes all constitute concept drift. A model card with a >18-month-old training date should trigger re-training before operational use.

### 8.4 Outstanding risks

- **NDVI haze bias** — Sentinel-2 NDVI is attenuated during high-PM2.5 episodes by atmospheric scattering. The correlation between the predictor and the confound is partially built into the model. A corrected NDVI (aerosol optical depth correction) would reduce this bias; not available in Session 4.
- **Extrapolation to 32,700 grid cells** — Only 10 training points for a 327 km² city. Spatial interpolation to 100m cells extrapolates far beyond training data for most of the grid. Uncertainty intervals derived from tree quantiles are informative but not guaranteed to be calibrated in the extrapolation regime.
- **Placement bias propagation** — Złoty Róg's low readings (20-30%) are in the test set. If future iterations include Złoty Róg in training, the model will be trained on biased data for that urban typology.

---

## Sign-off

- **Card written by:** Rim, Martina, Rashi, Bhavana
- **Reviewed by another team:** [reviewer team] on [date]
- **Reviewer feedback link:** [link to entry in modelling-log.md peer review section]
- **Last updated:** 2026-05-28

---

## Appendix · How this card is used downstream

- **Session 5 (orchestration):** The intended-use and out-of-scope sections in §2 define which grid cells get confidence-weighted predictions vs. "extrapolation — use with caution" flags. The model artifact (`models/baseline.joblib`) is the loadable object the orchestrator calls.
- **Session 6 (failure gallery):** The disaggregated table in §7.2 seeds the first failure entries. Złoty Róg (placement bias), Nowa Huta (industrial spike), and suburban cells (extrapolation) are the first three gallery entries. The out-of-scope list in §2.3 seeds the stress-test cases.
- **Session 7 (deployment):** This card is rendered next to the model output in the planning analyst UI. The planner reads §2.3 (out-of-scope) and §8.3 (caveats) alongside the prediction — not as a buried footnote but as a co-equal pane. The decision thresholds in §4.2 are the thresholds used to colour the map.
