## The map

| Brief sub-question | Primary data source | Secondary source | Confidence (H/M/L) | Notes |
|---|---|---|---|---|
| Sub-Q 1: Where is PM2.5 pollution worst in Krakow's residential districts? | AQICN (~10 stations, 2019-2024) | Sentinel-2 NDVI (visual sanity check) | **MEDIUM** | Only 10 points for 327 km². Must interpolate (kriging). Uncertainty ±30% >2km from stations. Suburbs weak. |
| Sub-Q 2: Which urban form features (greenness, road density, building density) correlate with measured PM2.5? | Urban Atlas (land cover categories) + OSM (buildings, roads) | Sentinel-2 NDVI (planned — not yet implemented) | **MEDIUM** | Session 3 used Urban Atlas land use % and OSM building/road density as greenness/density proxies. Sentinel-2 NDVI will add a direct vegetation signal in a future session. Haze bias risk noted — test required before using NDVI. |
| Sub-Q 3: By how much does each feature predict PM2.5? (effect sizes with uncertainty bounds) | AQICN + Urban Atlas + OSM (train regression model) | ERA5-Land (weather controls — not yet implemented), Sentinel-2 NDVI (planned) | **MEDIUM** | Can estimate correlations. Cannot prove causation (observational data, not experiments). ERA5-Land and Sentinel-2 will be added before model training. Need wide confidence intervals. |
| Sub-Q 4: Which 2-3 interventions (green corridors, traffic calming, green roofs) reduce pollution most? | Model from Sub-Q 3 (scenario predictions) | None | **LOW** | Interventions are counterfactuals (outside training data range). No cost data to rank by cost-effectiveness. Impact estimates only. |
| Sub-Q 5: What's the prediction uncertainty? (for defending in public hearings) | AQICN (leave-one-station-out cross-validation) | Model predictions (quantile regression) | **HIGH** | 10 stations sufficient for cross-validation. Can compute prediction intervals. This part we can do well. |

### Confidence scale

- **HIGH** — adopted dataset(s) directly answer the question at appropriate
  resolution and coverage. We can defend this in front of a reviewer.
- **MEDIUM** — adopted dataset(s) answer the question with caveats
  (resolution mismatch, gap, proxy required). Defensible with documentation.
- **LOW** — partial answer only; will require synthesis, modeling
  assumptions, or proxies. Mark as a known limitation.
- **NONE** — no data backing exists. Either find a new source or revise
  the brief.

---

## Coverage check

- **Sub-questions with HIGH confidence:**
  - Sub-Q 5 (uncertainty quantification) - we have the validation data and methods for this

- **Sub-questions with MEDIUM confidence:**
  - Sub-Q 1 (where is worst) - spatial gaps but usable with interpolation
  - Sub-Q 2 (what correlates) - atmospheric bias risk but testable
  - Sub-Q 3 (effect sizes) - observational only, not causal, but can quantify associations

- **Sub-questions with LOW confidence:**
  - Sub-Q 4 (rank interventions) - extrapolation + no cost data

- **Sub-questions with NO data backing:**
  - None. All questions have at least partial data support.

---

## What this means for the brief

*If any sub-question has NONE or LOW confidence, what's the plan?*

- [x] Find a new source — decision recorded for each candidate:
  - **Traffic volume data** (Krakow transport authority) — **Defer.** Would improve Sub-Q 2/3 but not critical for MVP. Road density (OSM) is an acceptable proxy. Revisit if R² < 0.40 after first model run.
  - **Building heights** (municipal cadastre or LiDAR) — **Defer.** Low priority; street canyon effect is a real gap but outside 100m-cell planning scale. Document as known limitation in model card.
  - **Before/after intervention data** (PM2.5 around new parks opened 2019-2024) — **Investigate in Session 4.** This is the only candidate that could upgrade Sub-Q 4 from LOW to MEDIUM confidence. Action: Rashi to contact Krakow Municipal Planning Office (BPP) to ask if pre/post-park PM2.5 records exist. Deadline: before model training begins.

- [x] Revise the brief — describe the change here, then commit it to
      `problem-brief-v2.md`:
  - **Change made:** Added caveat to Sub-Q 4 that interventions will be ranked by predicted impact only, not cost-effectiveness (no cost data available). Changed wording from "most cost-effective" to "reduce pollution most."
  - **Rationale:** None of our 5 adopted datasets include intervention costs. Planning office will need to add their own cost estimates if they want cost-benefit ranking.

- [x] Accept LOW confidence as a documented limitation — write the
      limitation statement here, then add it to `data-quality-audit.md`
      and to the future model card:
  - **Limitation for Sub-Q 4:** "Intervention rankings are based on predicted pollution reduction (correlation-based estimates), not proven causal effects. Rankings show impact only, not cost per µg/m³ reduced. Interventions are counterfactuals (adding green space where none currently exists) which extrapolates outside model training range. Prediction uncertainty for interventions is ±40-60% (wider than current conditions ±30%)."
  - **Added to:** data-quality-audit.md "What we will NOT use this dataset for" section.
  - **Will add to:** Model card in Session 6.

---

## Sign-off

**Team:** Rim, Martina, Rashi, Bhavana  
**Last updated:** 04/05/26

