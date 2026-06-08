# Data Quality Audit — AQICN Krakow PM2.5 Data

> Honest assessment of whether we can actually use this data for our project.
> Not a generic quality report - specifically asking "will this work for predicting pollution from urban features?"

---

## Dataset under audit

- **Dataset:** AQICN PM2.5 measurements, Krakow stations, 2019-2024
- **Profiling notebook:** `notebooks/01-data-profiling.ipynb`
- **Audit performed by:** Rim, Martina, Rashi, Bhavana
- **Date:** 04-05-2026

---

## Gaps

### Temporal gaps

Specific periods where data is missing or unreliable:

- **COVID lockdown (March 15 - May 31, 2020):** Data exists but pollution levels ~30% lower than normal due to reduced traffic. Not representative of typical conditions we're trying to model.

- **Winter 2020-2021 (December 2020 - February 2021):** Three stations (Aleja Krasińskiego, Kurdwanów, Nowa Huta) had intermittent outages. Completeness dropped to ~55% during this period (vs normal 70-75%).

- **Random hourly gaps throughout:** Missing ~25-30% of expected hourly measurements. Most gaps are 1-6 hour blocks (sensor calibration, power cuts). Longer gaps (>24 hours) rare but happen occasionally.

### Spatial gaps

Locations with missing or sparse coverage:

- **Western suburbs** (Bronowice, Krowodrza): Only 1 station for ~80 km². Can't validate predictions there.

- **Green spaces:** Zero stations in Planty Park, Błonia meadow, or Wolski Forest. Makes it impossible to validate model predictions in low-pollution green areas.

- **Eastern industrial zone** (around ArcelorMittal steel plant): Only 1 industrial-type station despite significant pollution sources.

- **Southern residential areas** (Podgórze, Płaszów): Sparse coverage, ~1 station for 50 km².

**Overall:** ~40% of Krakow's 327 km² is >2 km from nearest station. These areas have no direct validation data.

### Field-level gaps

Which variables are incomplete or unreliable:

| Field | % missing | Pattern | Impact |
|---|---|---|---|
| PM2.5 concentration | 25% | Higher in winter (30% missing) vs summer (20% missing) | Seasonal bias - underweights winter heating pollution |
| PM10 | 18% | Correlates with PM2.5 gaps (same sensors) | Not critical (we're using PM2.5 as primary) |
| Temperature | 60% | Only 4 of 10 stations report weather | Have to use ERA5-Land instead |
| Humidity | 65% | Same as temperature | Use ERA5-Land |
| Station coordinates | 0% | Complete but 2 stations have ±100m error | Must manually correct |
| Station type metadata | Not in API | Have to scrape from WIOŚ portal separately | Annoying but doable |

**Note:** The AQICN API doesn't include station type (traffic/background/industrial) - that's only on the WIOŚ website. We had to manually match station IDs to get this metadata.

---

## Anomalies found during profiling

Things that looked wrong and what we did about them:

| # | Anomaly | Diagnosis | Action taken |
|---|---|---|---|
| 1 | **5 negative PM2.5 values** (-0.5 to -2.1 µg/m³) at Aleja Krasińskiego, Jan 2023 | Sensor drift in extreme cold (-18°C overnight). Physically impossible. | Clipped to 0. Flagged Jan 2023 data from this station as lower confidence. |
| 2 | **Flat readings** - Kurdwanów showed PM2.5 = 38 µg/m³ ± 0.1 for 36 hours straight (Dec 15-16, 2022) | Sensor stuck/frozen. No variation despite wind speed changes shown by nearby stations. | Dropped this 36-hour block. Marked as invalid. |
| 3 | **Extreme spike** - Nowa Huta went from 45 → 287 → 41 µg/m³ in 3 consecutive hours (Feb 2, 2024) | Checked news: Nearby factory had incident that day. Real event, not sensor error. | Kept the data. Real pollution episode. |
| 4 | **Suspiciously low** - Złoty Róg readings consistently 20-30% lower than other stations in same weather | Station in park-like setting, sheltered by trees. Not representative of typical exposure. | Kept data but noted bias in station metadata. |
| 5 | **Timezone confusion** - Some timestamps in API response were UTC, others seemed local | AQICN always uses UTC. Confusion was on our end mixing with WIOŚ portal (which uses CET/CEST). | Standardized everything to UTC in our processing. |

---

## Bias check

Which biases apply to this dataset:

- **Selection bias:**  
  **YES - significant.** Stations placed for regulatory compliance (EU Air Quality Directive), not for scientific representativeness.  
  
  Bias toward:
  - Traffic hotspots (5 of 10 stations are "traffic" type, <10m from major roads)
  - City center (7 of 10 stations within 5km of Old Town Square)
  - Areas with power + internet infrastructure
  
  Undersampled:
  - Suburbs, peri-urban areas
  - Wealthy western neighborhoods (ironically - they probably have cleaner air but less monitoring)
  - Green spaces (parks, forests)
  
  **Impact:** Our model will be better at predicting pollution near roads and downtown, worse in suburbs and green areas. We won't even know if predictions are good in those places because no validation data.

- **Measurement bias:**  
  **MINOR.** EU standard measurement uncertainty is ±15% for PM2.5. That's acceptable.  
  
  There's a small systematic bias: sensors underestimate PM2.5 in very humid conditions (~5%) because water vapor makes particles bigger (measured as PM10 instead of PM2.5).  
  
  **Impact:** Winter readings (high humidity) might be slightly biased low, but error is small compared to other problems.

- **Coverage bias:**  
  **YES - see Spatial Gaps section above.**  
  40% of city area has no validation data. Also, wealthier areas have slightly better coverage than working-class areas.  
  
  **Impact:** Can't validate model in large chunks of the city. Spatial interpolation in those areas is pure guesswork.

- **Temporal drift / non-stationarity:**  
  **YES.** Two major changes during our study period (2019-2024):
  
  1. **Coal heating ban** (September 2019): Krakow banned residential coal burning. Average PM2.5 dropped ~15% in winter months after ban vs before.
  
  2. **COVID lockdown** (Mar-May 2020): Traffic dropped 40%, PM2.5 dropped 30%. Temporary but huge anomaly.
  
  3. **Low Emission Zone** (started Jan 2024): Too new to see effect yet but will change future trends.
  
  **Impact:** Model trained on 2019-2024 data captures "post-coal-ban but pre-LEZ" regime. Won't generalize to other Polish cities still burning coal. Won't predict future if LEZ significantly changes traffic patterns.

- **Label bias:**  
  **NOT APPLICABLE.** This is measurement data (sensors), not human-labeled data. No labels to be biased.

---

## Fitness for OUR brief

Can this dataset answer our specific questions?

- **Sub-question 1:** Where is PM2.5 pollution worst in Krakow?
  - **Answer:** **Partial**
  - **Why:** We know pollution levels at 10 specific points (station locations). We can interpolate to create a continuous map, but accuracy degrades fast with distance from stations. Can say "this station measured highest" but can't confidently say "this 100m grid cell is worst" if it's far from any station. Suburban/peri-urban areas (40% of city) have weak or no validation.

- **Sub-question 2:** Which urban features (NDVI, road density, building density) correlate with high PM2.5?
  - **Answer:** **Yes**
  - **Why:** Enough variation across stations to detect correlations. Stations range from high-green (parks: NDVI ~0.6) to low-green (downtown: NDVI ~0.2). Road density ranges from 1 km/km² (residential) to 6 km/km² (traffic corridors). PM2.5 annual averages range from 15 µg/m³ (cleanest station) to 38 µg/m³ (most polluted). Sufficient signal for regression modeling.

- **Sub-question 3:** What's the effect size? (How much does 10% more greenness reduce PM2.5?)
  - **Answer:** **Partial**
  - **Why:** Can estimate *correlations* from current data (observational). Cannot estimate *causal effects* (what happens if we ADD green space where there currently isn't any) without experimental data. Our "effect sizes" will be associations, not interventions. Have to caveat heavily: "Areas with 10% more green HAVE 3 µg/m³ lower PM2.5" NOT "ADDING 10% green WILL REDUCE PM2.5 by 3 µg/m³". Different claims.

- **Sub-question 4:** Which interventions are most cost-effective for the Planning Office?
  - **Answer:** **No (from this dataset alone)**
  - **Why:** This dataset has pollution levels. It has zero information about costs. Can rank interventions by predicted pollution reduction, but can't compute € per µg/m³ reduced without external cost data (civil engineering estimates for green corridors, traffic calming, etc.). That's out of scope.

- **Sub-question 5:** How uncertain are our predictions?
  - **Answer:** **Yes**
  - **Why:** With 10 stations, we can do leave-one-station-out cross-validation (train on 9, test on 1, repeat 10 times). This will give realistic error estimates for "predicting PM2.5 at a new location." Can also do uncertainty quantification via bootstrap or quantile regression. 10 stations is borderline (would prefer 15-20) but usable.

---

## Decisions

- **What we WILL use this dataset for:**
  
  1. **Model training:** PM2.5 monthly averages as the target variable (what we're trying to predict from urban features)
  2. **Model validation:** Cross-validation to estimate how well predictions generalize to new locations
  3. **Current pollution assessment:** Which areas currently have high PM2.5 based on interpolation from stations
  4. **Correlation analysis:** Do greener/less dense areas have lower PM2.5? (observational, not causal)

- **What we will NOT use this dataset for:** *(at least 2 specific things)*
  
  1. **Sub-hourly forecasting:** Data too noisy (hour-to-hour swings driven by weather, not urban form). Can't predict "PM2.5 will be 45 µg/m³ at 2pm tomorrow."
  
  2. **Building-scale predictions (<100m):** Stations too sparse. Can't say "This side of the street has higher pollution than that side." Only neighborhood-scale patterns.
  
  3. **Personal exposure assessment:** Stations measure outdoor ambient averages. People spend time indoors, commute through different areas. Can't use this for "Should I wear a mask today when walking to work?"
  
  4. **Attributing pollution to specific sources:** Sensors measure total PM2.5, don't distinguish traffic vs heating vs industrial emissions. Can't say "30% comes from trucks, 40% from coal stoves."
  
  5. **Causal proof of interventions:** This is observational data (passive monitoring). Can show correlations but can't prove that building a park will reduce pollution without quasi-experimental design (e.g., before-after comparisons).

- **What additional source(s) we'd need to fill the gaps:**
  
  1. **Traffic volume data** (Krakow transport authority) - to separate "high road density" from "high traffic volume" (roads don't pollute; vehicles do)
  
  2. **Denser sensor network** (e.g., 50-100 low-cost sensors like PurpleAir) - to validate suburban predictions and get building-scale resolution
  
  3. **Industrial emissions inventory** (GIOŚ registry) - to identify pollution from factories vs traffic vs heating
  
  4. **Before/after intervention data** (e.g., PM2.5 measurements before and after new parks opened) - to estimate causal effects, not just correlations

---

## Implications for the brief

Does this audit force changes to our problem brief?

**YES - Made 3 changes:**

1. **Added uncertainty caveat to Success Criterion:**
   - **Original:** "Predictions at 10-meter resolution"
   - **Revised:** "Predictions at 10-meter resolution aggregated to 100m grid. Predictions >2km from stations documented with ±30% uncertainty."
   - **Why:** Only 10 stations can't validate 100m resolution everywhere. Have to be honest about spatial gaps.

2. **Clarified correlation vs causation:**
   - **Original (implied):** "Effect sizes for interventions"
   - **Revised:** "Association strengths for urban features (correlation, not causal intervention effects)"
   - **Why:** Observational data can't support causal claims. Don't want to mislead planning office.

3. **Excluded COVID period:**
   - **New out-of-scope item:** "March-May 2020 data excluded (COVID lockdown, not representative of normal traffic)"
   - **Why:** Temporal drift identified. Including anomalous period would bias model.

**Changes documented in:** `problem-brief-v2.md` (already done, no edits needed)

---

## Per-team-member contributions

### Rim

I set up the AQICN API connection and downloaded PM2.5 data for all Krakow stations from 2019-2024. Found ~440k raw hourly measurements. The trickiest part was dealing with rate limits (free API tier maxes at 1000 requests/min) - had to batch the historical downloads and cache everything locally. 

I also discovered the timezone confusion issue - AQICN returns UTC timestamps but I initially thought they were local time because some Kaggle datasets claim to use local. Verified by spot-checking against WIOŚ portal: AQICN is consistently UTC. Also found the negative PM2.5 values (5 instances at Aleja Krasińskiego in Jan 2023) - clipped them to zero since negative concentration is physically impossible.

### Martina

I did the spatial coverage analysis by mapping all 10 station locations and calculating Voronoi cells (which area is closest to each station). Found that 6 stations are crammed into the central 30 km² while 40% of the city (suburbs) is >2km from any station. Cross-referenced with census data - wealthier western districts have slightly better coverage than working-class eastern districts, which is a coverage bias we need to document.

I also validated coordinates by comparing AQICN API responses to Google Maps. Found 2 stations where the coordinates were off by ~100m (probably manually entered wrong in the database at some point). Got correct coords from WIOŚ portal and manual fix is in our preprocessing script.

### Rashi

I ran the anomaly detection analysis - wrote a Python script to flag: (1) negative values, (2) flatlines (stddev <0.1 for >24 hours), (3) extreme outliers (>3 standard deviations from monthly mean), (4) suspiciously low stations (consistently <70% of nearby station readings). Caught the Kurdwanów stuck sensor (36 hours of identical readings in Dec 2022) and the Złoty Róg sheltered-location bias.

For the bias check, I calculated station-type distribution (5 traffic, 4 urban background, 1 industrial) and compared to Krakow land use patterns. Clear oversampling of traffic locations relative to residential/green spaces. Also ran temporal stationarity tests - confirmed significant drop in PM2.5 post-coal-ban (Sept 2019) and during COVID lockdown (Mar-May 2020).

### Bhavana

I led the fitness-for-brief assessment by mapping each sub-question to the dataset and rating Yes/Partial/No based on what we actually found in the data. Also wrote the "What we will NOT use" section - critical to set boundaries early so we don't overpromise.

Worked with Rim to identify the 3 changes needed to the problem brief (uncertainty caveat, correlation vs causation, COVID exclusion). These come directly from audit findings - the audit revealed limits, so the brief had to acknowledge them. Also drafted the "What additional sources we'd need" list based on gaps we can't fill with current data.

