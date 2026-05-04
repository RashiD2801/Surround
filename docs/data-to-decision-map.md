# Data-to-Decision Map — Krakow Air Quality Project

**The decision:** Krakow Planning Office ranks urban interventions (green corridors, traffic calming, green roofs) to attach as conditions when approving new residential developments.

**Last updated:** December 2024

---

## How This Map Works

Each question below is something we must answer to support that decision. For each one, we show:
- Which datasets we'll use
- How confident we are (High/Medium/Low)
- What could go wrong
- Plan B if it doesn't work

---

## Question 1: Where is pollution worst right now?

**Why it matters:** Planning office needs to know which areas to prioritize for interventions.

**Data sources:**
| Dataset | What we get from it | Confidence |
|---|---|---|
| AQICN PM2.5 | Ground truth measurements at 10 stations | Medium |
| Sentinel-2 | Visual check (is area actually green/built-up as claimed?) | Medium |
| ERA5-Land | Weather control (filter out high-inversion days that spike pollution everywhere) | Low |

**How we'll do it:**
1. Take AQICN monthly averages (2019-2024) for each station
2. Apply spatial interpolation (kriging or inverse distance weighting) to create 100m grid
3. Overlay on Sentinel-2 imagery to sanity-check (do high-pollution areas look like we'd expect?)

**Confidence: Medium**

**What could go wrong:**
- Interpolation assumes smooth gradients. Reality has sharp edges (highway = pollution spike, park = clean).
- Only 10 stations for 327 km². Kriging in suburbs is basically guessing.
- Weather variations: Pollution on calm, cold days ≠ pollution on windy, warm days.

**Plan B if this fails:**
- Don't interpolate. Just show the 10 station values as points on a map.
- Add disclaimer: "High confidence within 1km of stations, low confidence beyond."

---

## Question 2: What urban features correlate with pollution?

**Why it matters:** Need to know which levers planners can pull (add green space? Reduce road density?).

**Data sources:**
| Dataset | What we extract | Confidence |
|---|---|---|
| Sentinel-2 | NDVI (greenness), NDBI (built-up), NDWI (water) | Medium |
| OpenStreetMap | Road density (km/km²), building density (% footprint coverage) | High |
| Copernicus Urban Atlas | Land cover type (residential, industrial, green, etc.) | Medium |

**How we'll do it:**
1. For each of the 10 AQICN station locations, extract features:
   - NDVI in 100m cell around station (from Sentinel-2)
   - Road density within 500m radius (from OSM)
   - Building footprint % (from OSM)
   - Land cover class (from Urban Atlas)
2. Calculate correlations: Does high NDVI → low PM2.5? Does high road density → high PM2.5?
3. Visualize with scatter plots

**Confidence: Medium**

**What could go wrong:**
- **Atmospheric bias:** Polluted days have haze → Sentinel-2 NDVI looks lower even if vegetation unchanged. Could create backwards correlation (pollution causes low NDVI reading, not low vegetation causes pollution).
- **Confounding:** Green parks might be in wealthy neighborhoods with less traffic. Is it greenness or wealth?
- **Temporal mismatch:** Sentinel-2 monthly composites vs AQICN hourly data. Aggregation might wash out signal.

**Plan B if this fails:**
- Use only summer Sentinel-2 data (minimal haze, cloud-free) and validate on winter PM2.5 measurements.
- Add ERA5 boundary layer height as control variable to partial out weather effects.
- Switch from "correlation" to "supervised learning" (random forest) - don't need to interpret individual features, just predict.

---

## Question 3: How much difference does each feature make?

**Why it matters:** Planning office needs numbers. "Add green corridor" is vague. "Green corridor → 4.2 µg/m³ reduction [95% CI: 2-6]" is actionable.

**Data sources:**
- All of the above (AQICN + Sentinel-2 + OSM) → train regression model

**How we'll do it:**
1. Build model: `PM2.5 = f(NDVI, road_density, building_density, land_cover, weather)`
2. Use random forest or linear regression
3. Extract feature importances or coefficients
4. Translate to plain language: "10% increase in NDVI associated with X µg/m³ decrease in PM2.5"

**Confidence: Medium**

**What could go wrong:**
- **Model doesn't work:** R² < 0.40 (explains <40% of variation). Not useful for predictions.
- **Overfitting:** Model memorizes the 10 training locations but fails on new locations.
- **Extrapolation:** Model trained on existing conditions (0.2 < NDVI < 0.6). Predictions for "add dense forest" (NDVI=0.9) are outside training range.

**Plan B if this fails:**
- Report correlations instead of effect sizes: "Greener areas have lower PM2.5" not "Adding green will reduce PM2.5 by X."
- Provide wide confidence intervals: "Effect could be anywhere from 1 to 8 µg/m³" (honest but not that useful).
- Recommend field experiments: "Plant park, measure before/after" (outside our scope but suggest to city).

---

## Question 4: Which interventions should we rank highest?

**Why it matters:** Planning office has limited leverage. They want the biggest bang for buck.

**Data sources:**
- Model from Question 3 → scenario predictions
- (Missing: cost data - we don't have this)

**How we'll do it:**
1. Define interventions:
   - Scenario A: Add 1-hectare park (NDVI +0.3 in 10 grid cells)
   - Scenario B: Green corridor along road (NDVI +0.2 in 50 cells)
   - Scenario C: Traffic calming (road_density -30%)
   - Scenario D: Green roofs (NDVI +0.1 in dense areas)
2. For each scenario, predict PM2.5 change using model
3. Rank by pollution reduction (descending)
4. Manually add cost tier (Low/Medium/High) based on rough estimates

**Confidence: Low**

**What could go wrong:**
- **No cost data:** Can rank by impact but not by cost-effectiveness (€ per µg/m³).
- **Interventions are counterfactuals:** Model trained on "what is" not "what if." Predicting outcomes of adding new parks is extrapolation.
- **Implementation feasibility:** "Add 5-hectare park" might require demolishing buildings. Politically infeasible.

**Plan B if this fails:**
- Rank by impact only (not cost-benefit).
- Provide 3 tiers: "Low-cost/high-impact," "Medium-cost/medium-impact," "High-cost/unknown-impact."
- Caveat heavily: "These are estimated associations, not proven interventions. Pilot tests recommended."

---

## Question 5: How confident should planning office be?

**Why it matters:** Developers will challenge predictions in public hearings. Need defensible uncertainty.

**Data sources:**
- AQICN (for cross-validation)
- Model predictions (for uncertainty quantification)

**How we'll do it:**
1. Cross-validation: Leave one station out, train on 9, predict on 1. Repeat 10 times.
2. Compute errors: R², MAE (mean absolute error), RMSE (root mean squared error)
3. Uncertainty map: Show prediction interval width for each 100m cell (wider intervals = less confident)

**Confidence: High** (for this specific task - we can definitely quantify uncertainty)

**What could go wrong:**
- **Cross-validation underestimates real error:** 10 stations might not be representative. Real-world new locations might be harder to predict.
- **Spatial correlation:** Nearby locations are similar. Cross-validation assumes independence but that's violated.

**Plan B if this fails:**
- Report only aggregate error: "Model MAE is 6 µg/m³" without spatial breakdown.
- Use conservative approach: "All predictions have ±30% uncertainty" (safe but not informative).

---

## Summary: Data → Questions → Decision

```
AQICN PM2.5          →  Q1: Where is worst?        ↘
Sentinel-2 NDVI      →  Q2: What correlates?        → Q4: Rank interventions → DECISION
OpenStreetMap        →  Q3: How much difference?   ↗
ERA5-Land weather    →  Q5: How confident?        ↗
```

**Overall confidence in supporting the decision: B**

Can deliver:
- ✓ Pollution hotspot map (with documented uncertainty)
- ✓ Urban feature correlations
- ✓ Intervention ranking (by impact, not cost)
- ✓ Uncertainty quantification

Cannot deliver:
- ✗ Causal proof (correlation only)
- ✗ Cost-benefit analysis (no cost data)
- ✗ Fine-resolution predictions (data too sparse)

---

## What We're Missing (And Why)

**Traffic volume data:** Would let us separate "high road density" from "high traffic." Roads don't pollute; cars do.  
**Impact:** Model will be less precise. But road density is still a decent proxy.

**Building heights:** Would let us model "street canyons" (tall buildings trapping pollution).  
**Impact:** Model will underestimate pollution in dense downtown cores.

**Before/after intervention data:** Would let us estimate causal effects.  
**Impact:** Can only show correlations, not prove interventions work.

**Dense low-cost sensor network:** Would let us validate suburban predictions.  
**Impact:** High uncertainty in 40% of city area with no nearby stations.

**Is that OK?** Yes, for an MVP (minimum viable product). Won't be perfect but will be useful. Planning office can start using it and we can improve with more data later.

---

## Next Steps (Session 3)

**Rim:** Download all AQICN data, process to monthly averages  
**Martina:** Extract Sentinel-2 NDVI + OSM features for station locations  
**Rashi:** Train model, run cross-validation, target R² ≥ 0.40  
**Bhavana:** Design intervention ranking table and uncertainty visualization

**First milestone:** Get basic correlation plot (NDVI vs PM2.5) working. If that shows signal, continue. If not, rethink approach.
