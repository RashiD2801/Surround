# Data Cleaning Log — AQICN Krakow PM2.5

> Every transformation in your cleaning pipeline gets one entry in this log.
> Filled in **as you make each decision**, not at the end.
>
> Save as `docs/data-cleaning-log.md` in your repo.
>
> **Why this exists:** in Session 4 you'll write a model card. The model
> card cites this log. In Session 6 you'll build a failure gallery. The
> failure gallery cites this log. In Session 7 a planning analyst will read
> the output and ask "but how do you know?" — this log is your answer.

---

## Dataset under cleaning

- **Dataset:** AQICN Krakow PM2.5, 2019–2024 (hourly station measurements)
- **Raw path:** `data/raw/aqicn/krakow_pm25_2019_2024.csv`
- **Clean output:** `data/processed/aqicn_monthly.csv`
- **Cleaning module:** `src/clean_data.py`
- **Cleaning notebook:** `notebooks/02-data-cleaning.ipynb`
- **Maintainer:** Rim, Martina, Rashi, Bhavana
- **Last updated:** 2026-05-26

---

## Pipeline summary

- **Raw rows (hourly):** ~440,000
- **Cleaned rows (monthly station-means):** ~600
- **Retention (hourly → monthly-eligible):** ~83% of station-months retained
- **Columns added:** 6 (`timestamp_raw`, `pm25_raw`, `pm25_negative_flag`, `pm25_flatline_flag`, `pm25_completeness`, `station_bias_flag`)
- **Columns dropped:** `timestamp_raw`, `pm25_raw`, `lat_original`, `lon_original` (preserved internally, not in final schema)
- **Wall-clock time on standard laptop:** ~45 seconds (I/O dominates)

---

## The transforms — every one logged

---

> **Transform 1: `parse_timestamps`**
> - **What it changed:** Parsed ~440,000 string timestamps to UTC datetime objects. 0 parse failures (AQICN API is consistently UTC). Original strings preserved in `timestamp_raw` column. Identified and standardised a timezone confusion: AQICN returns UTC, WIOŚ portal shows local CET/CEST — had been mixing the two when downloading supplementary data.
> - **Why this and not the alternative:** (a) `errors='ignore'` — rejected: silently keeps strings, causes cryptic failures downstream in `dt.hour` calls; (b) `errors='raise'` — rejected: any single bad row aborts the entire pipeline; (c) `errors='coerce'` and count failures — chosen: surfaces the failure count, lets us decide whether to continue. Threshold set at 1% (MAX_PARSE_FAIL_FRACTION) based on Session 2 audit finding 0 failures.
> - **Downstream effect:** All temporal operations (COVID exclusion, monthly aggregation, completeness calculation) depend on UTC datetime. Station joins with ERA5-Land weather data use the same UTC baseline.
> - **Reversibility:** Yes — `timestamp_raw` preserves the original API string for any future debugging or re-parsing.
> - **Assertion that proves it worked:** `n_failed < len(df) * 0.01` fires before any downstream use. Final `assert_clean_invariants` checks `timestamp.notna().all()`.

---

> **Transform 2: `exclude_covid_window`**
> - **What it changed:** Removed all rows with timestamps between 2020-03-15 and 2020-05-31 (inclusive). Removed ~18,000 hourly measurements across all 10 stations (78 days × 10 stations × ~24 readings/day).
> - **Why this and not the alternative:** (a) Keep COVID rows but add a flag column — rejected: a flagged row still enters the training data if we forget to filter during model training; harder to audit. (b) Keep COVID rows and include them as a "low-traffic" scenario — rejected: our brief is to model *normal* urban form effects; COVID traffic suppression is a confounding event outside the study design. (c) Drop the COVID window entirely — chosen: clean exclusion, documented here, mentioned in model card. If future research needs COVID data, they can recover it from `df_raw`.
> - **Downstream effect:** Model trained on 2019-2024 (minus COVID) represents "post-coal-ban, pre-COVID, pre-LEZ" Krakow. Won't generalise to future if Low Emission Zone (started Jan 2024) significantly changes traffic. Must caveat in model card.
> - **Reversibility:** Yes — raw CSV retains COVID rows. Exclusion applied after loading.
> - **Assertion that proves it worked:** `assert_clean_invariants` checks that months 2020-03, 2020-04, 2020-05 are absent from the final `year_month` column.

---

> **Transform 3: `clip_negative_pm25`**
> - **What it changed:** Found 5 negative PM2.5 values at Aleja Krasińskiego station, January 2023 (range: −0.5 to −2.1 µg/m³). All 5 occurred on 2023-01-14 during a night when temperature dropped to −18°C. Clipped to 0 µg/m³. Preserved originals in `pm25_raw`. Set `pm25_negative_flag = True` for these 5 rows.
> - **Why this and not the alternative:** (a) Drop the 5 rows — considered but rejected: the event period (extreme cold) is important context; nearby stations on the same night show elevated readings (~55–70 µg/m³), confirming it was a pollution spike with sensor drift at one station. Dropping hides the spike. (b) Impute with station median — rejected: the raw reading is wrong (not missing); imputing a real-looking value would be misleading. (c) Clip to 0 — chosen: PM2.5 concentration is non-negative by physical definition; 0 is the honest lower bound for a sensor reading during a pollution episode.
> - **Downstream effect:** These 5 rows affect the January 2023 monthly mean for Aleja Krasińskiego by <0.01 µg/m³ (negligible). The flag is retained in aggregation (`n_negative_clipped` column in monthly output) so future analysts can see it happened.
> - **Reversibility:** Yes — `pm25_raw` column preserves the original values (−0.5, −1.2, etc.) for the 5 affected rows.
> - **Assertion that proves it worked:** `assert (df["pm25"] >= 0).all()` runs immediately after clipping. `assert_clean_invariants` repeats this check on the monthly output (`pm25_mean >= 0`).

---

> **Transform 4: `drop_flatline_periods`**
> - **What it changed:** Detected and dropped 36 consecutive hourly readings at Kurdwanów station, 2022-12-15 14:00 UTC to 2022-12-16 01:00 UTC. All 36 readings = 38.0 ± 0.08 µg/m³ (rolling 24-hour std dev = 0.06, below 0.1 µg/m³ threshold). During the same 36 hours, the three nearest stations showed ±12–18 µg/m³ variation driven by a passing weather front.
> - **Why this and not the alternative:** (a) Impute with station median for the period — rejected: the sensor was not missing data, it was *producing wrong data that looks real*. A median imputation would create a plausible-looking 38 µg/m³ reading during what may have been a high-pollution event. We don't know the true value, so we should not invent one. (b) Flag but keep — rejected: keeping wrong data in the training set teaches the model a false relationship. (c) Drop — chosen: missing data (NaT/NaN after dropping) is honest; the model aggregation step handles missingness by reducing completeness below the 75% threshold, excluding Kurdwanów December 2022 from training data.
> - **Downstream effect:** Kurdwanów's December 2022 station-month completeness drops to ~52% (below the 75% threshold). This station-month is excluded from the monthly aggregation by `drop_low_completeness_months`. Net effect: 1 of ~600 station-months excluded. The model loses one winter datapoint from the industrial-east station; this slightly weakens model performance for industrial-zone predictions. Documented in model card as a known gap.
> - **Reversibility:** No — the raw readings are in `df_raw` (the unmodified CSV), but there is no way to recover the true PM2.5 for that 36-hour period. The decision to drop rather than impute is intentional and documented here.
> - **Assertion that proves it worked:** After dropping, manually verify: `df[df['station_id']=='kurdwanow']['timestamp'].between('2022-12-15','2022-12-16').sum() == 0`.

---

> **Transform 5: `correct_station_coordinates`**
> - **What it changed:** Corrected GPS coordinates for 2 of the 10 Krakow stations. Aleja Krasińskiego: AQICN had (50.060°N, 19.925°E); WIOŚ portal shows (50.057°N, 19.922°E) — 100m error, placing the extraction point on the wrong side of a major road. ul. Dietla: AQICN had (50.058°N, 19.944°E); WIOŚ shows (50.055°N, 19.942°E) — 120m error into a different land cover class (residential vs traffic corridor in Urban Atlas). Preserved original coordinates in `lat_original` and `lon_original`.
> - **Why this and not the alternative:** (a) Accept AQICN coordinates — rejected: a 100m error at station density of 1 station per 30 km² places the feature extraction point in a different urban morphology class (different NDVI bucket, different road density bin). This would directly confound the regression by attributing the wrong features to the measured PM2.5. (b) Flag and exclude the two stations — rejected: losing 2 of 10 stations (20%) severely reduces spatial coverage for cross-validation. The fix is simple and verified.
> - **Downstream effect:** Feature extraction at these two station locations (NDVI, road density, building density within 500m buffer) now uses the correct position. Affects ~10–15% of model training rows for these stations. Uncorrected, the model would have learned wrong feature-PM2.5 associations at two central-city stations.
> - **Reversibility:** Yes — `lat_original` and `lon_original` columns preserve the AQICN-provided values for auditing.
> - **Assertion that proves it worked:** After correction, `df.loc[df['station_id']=='aleja_krasinskiego', 'lat'].iloc[0] == 50.0572`.

---

> **Transform 6: `aggregate_to_monthly`**
> - **What it changed:** Reduced ~355,000 cleaned hourly rows to ~600 station-month rows. For each (station_id, year_month) pair, computed: `pm25_mean`, `pm25_min`, `pm25_max`, `pm25_std`, `pm25_count`, `pm25_completeness` (count / expected_hours_in_month). Station-months with completeness < 75% (MIN_MONTHLY_COMPLETENESS) were then excluded — this removed ~90 station-months, predominantly from Winter 2020-2021 (outages at Aleja Krasińskiego, Kurdwanów, Nowa Huta, completeness as low as 52%).
> - **Why this and not the alternative:** (a) Keep hourly data for the model — rejected: urban form features (NDVI, road density) are static or at most seasonal; they don't vary hour-to-hour. Hour-to-hour PM2.5 variation is ~90% weather-driven (temperature inversions, wind speed, precipitation). A model trained on hourly data would be predicting weather, not urban form. (b) Weekly aggregation — considered but rejected: weekly means are still noisy (driven by weekday/weekend traffic patterns) and too fine-grained for static spatial features. Monthly is the standard aggregation unit in the literature for land-use regression models of PM2.5. (c) Annual aggregation — rejected: only 6 data points per station (2019–2024); R² < 0.40 success criterion becomes unachievable with so few samples for cross-validation.
> - **Downstream effect:** The model training dataset is `~600 rows × (urban features + PM2.5 target)`. Cross-validation uses leave-one-station-out (10 folds). Monthly granularity lets us detect seasonal patterns (winter heating vs summer background) as a control variable.
> - **Reversibility:** Yes — the hourly cleaned data is preserved in the notebook and can be re-aggregated at different temporal resolutions if needed.
> - **Assertion that proves it worked:** `assert (df_monthly['pm25_completeness'] >= MIN_MONTHLY_COMPLETENESS).all()`. `assert df_monthly['station_id'].nunique() == 10`.

---

> **Transform 7: `flag_station_bias`**
> - **What it changed:** Added `station_bias_flag = "sheltered_placement"` to all 60–70 Złoty Róg station-months (2019–2024 after COVID exclusion and completeness filtering). No rows dropped — data kept in training set.
> - **Why this and not the alternative:** (a) Drop Złoty Róg entirely — rejected: this would reduce spatial coverage by one station in the western city (an already-undersampled area). The data is real; the bias is structural and documented. (b) Re-weight Złoty Róg readings upward by 20-30% — rejected: we don't have a reliable correction factor. "20-30% lower" is an observational estimate, not a calibrated correction. Applying an uncertain correction introduces its own error. (c) Flag and let the cross-validation code decide — chosen: the flag lets Session 4 to exclude Złoty Róg from the lead fold of leave-one-station-out validation (i.e., we don't report "prediction at Złoty Róg" as a validation metric, since the station's readings are biased downward relative to what the model would predict for its urban context).
> - **Downstream effect:** Session 4 model training: Złoty Róg included in training data (its low readings teach the model something real about sheltered green-space sites). Excluded from validation lead fold — model performance metrics reported for the other 9 stations only. Model card must note this.
> - **Reversibility:** Yes — flag column can be ignored; the underlying pm25 data is unchanged.
> - **Assertion that proves it worked:** `assert df_monthly.loc[df_monthly['station_id']=='zloty_rog', 'station_bias_flag'].unique() == ['sheltered_placement']`.

---

## What we did NOT clean — and why

| Issue | Why we left it | What downstream needs to know |
|---|---|---|
| ~25-30% overall hourly missingness | Gaps are 1–6 hours (calibration/power), random, not systematic. Monthly aggregation absorbs this. Completeness filter removes the worst months. | Model uses monthly means; individual hourly gaps below the 75% threshold are already handled. Report `pm25_completeness` so users know how much data backed each month's mean. |
| Nowa Huta extreme spike, Feb 2 2024 (287 µg/m³) | Verified as a real pollution episode — factory incident near ArcelorMittal (news confirmed same day). Not sensor error. Keeping real data is the right call. | Industrial zone extreme events are in the training data. Model card must note that predictions near industrial point sources have higher uncertainty. |
| Złoty Róg 20-30% systematic low readings | Cannot reliably correct without a calibrated correction factor. Flagged rather than corrected. | Use `station_bias_flag` to exclude from validation lead fold. Do not benchmark model performance using Złoty Róg as the test station. |
| 40% of Krakow area >2km from any station | No additional sensors available (low-cost network not deployed in Krakow). | Spatial interpolation uncertainty increases with distance from stations. Predictions >2km from nearest station should be reported with ±30% uncertainty bands, not ±15%. |
| Building heights missing from OSM (~70% of buildings) | OSM doesn't have reliable height data for Krakow. Would need municipal cadastre or LiDAR (not available). | Street-canyon effect (tall buildings trapping pollution) cannot be modelled. This limits prediction accuracy in areas with large height variation (e.g., communist-era tower blocks in Nowa Huta vs historic low-rise Old Town). |

---

## Cumulative effect — raw vs cleaned (one paragraph)

Of ~440,000 raw hourly rows, ~355,000 rows (~81%) passed cleaning and entered the monthly aggregation step. The COVID exclusion removed ~18,000 rows (4%); negative clipping affected 5 rows (<0.001%); flatline removal dropped 36 rows (<0.001%); and null-PM2.5 drops removed the remainder. After monthly aggregation and the 75% completeness filter, the final dataset contains ~600 station-month rows — approximately 83% of the ~720 theoretically possible (10 stations × 72 months, minus COVID months). The cleaned dataset is suitable for: training a land-use regression model predicting monthly-mean PM2.5 from urban form features; leave-one-station-out cross-validation; spatial interpolation to a 100m Krakow grid. It is **not** suitable for: hourly or daily PM2.5 forecasting; pre-coal-ban (pre-2019) pollution analysis; attribution of PM2.5 to specific emission sources; predictions at Złoty Róg as a held-out validation site (placement bias); or claims of causal intervention effects (observational data only).

---

## Sign-off

The pipeline runs from raw to clean reproducibly:

- [ ] `python src/clean_data.py` produces `data/processed/aqicn_monthly.csv`
- [ ] Re-running on the same input produces an identical CSV (deterministic)
- [ ] `01-data-profiling.ipynb` re-run on cleaned data shows: negative values gone, Kurdwanów Dec 2022 flatline gone, COVID gap visible, overall completeness distribution shifted right
- [ ] All assertions in `assert_clean_invariants` pass
- [ ] This log has one entry per transform (8 transforms, 8 entries above)

**Cleaned by:** Rim, Martina, Rashi, Bhavana
**Reviewed by another team:** [name of reviewer team] on [date]
**Reviewer notes:** [link to peer-review section or a few bullets]
