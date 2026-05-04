# Data → Decision Map

> The bridge from your problem brief to your data inventory. For each
> sub-question in the brief, which dataset answers it, and at what
> confidence?
>
> If any sub-question has NO data backing it, you have two choices:
> 1. Find a new source.
> 2. Revise the brief (`problem-brief-v2.md`).
>
> There is no third option called "we'll figure it out later."
>
> Save as `docs/data-to-decision-map.md` in your repo.

---

## The map

| Brief sub-question | Primary data source | Secondary source | Confidence (H/M/L) | Notes |
|---|---|---|---|---|
| Sub-Q 1: Where is PM2.5 pollution worst in Krakow's residential districts? | AQICN (~10 stations, 2019-2024) | Sentinel-2 NDVI (visual sanity check) | **MEDIUM** | Only 10 points for 327 km². Must interpolate (kriging). Uncertainty ±30% >2km from stations. Suburbs weak. |
| Sub-Q 2: Which urban form features (greenness, road density, building density) correlate with measured PM2.5? | Sentinel-2 (NDVI, NDBI) | OpenStreetMap (roads, buildings), Urban Atlas (land cover) | **MEDIUM** | Haze bias risk: polluted air can reduce NDVI readings (backwards causation). Must test before trusting correlations. |
| Sub-Q 3: By how much does each feature predict PM2.5? (effect sizes with uncertainty bounds) | AQICN + Sentinel-2 + OSM (train regression model) | ERA5-Land (weather controls) | **MEDIUM** | Can estimate correlations. Cannot prove causation (observational data, not experiments). Need wide confidence intervals. |
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

- [ ] Find a new source — list candidates here:
  - Traffic volume data (Krakow transport authority) - would improve Sub-Q 2 and 3 by deconfounding road density from actual vehicle counts. Not critical for MVP.
  - Building heights (municipal cadastre or LiDAR) - would improve Sub-Q 2 by modeling street canyon effects. Low priority.
  - Before/after intervention data (PM2.5 measurements around new parks opened 2019-2024) - would upgrade Sub-Q 4 from LOW to MEDIUM by enabling quasi-experimental design. Worth investigating if city has data.

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
**Last updated:** 2024-12-15
