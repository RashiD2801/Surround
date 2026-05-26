# Datasheet: Copernicus Urban Atlas (Krakow)

**Dataset:** Copernicus Land Monitoring Service — Urban Atlas 2018  
**Provider:** European Environment Agency (EEA)  
**Resolution:** 50m minimum mapping unit  
**Created by:** Rim, Martina, Bhavana, Rashi  
**Date:** 18-05-2026

---

## What This Is

Urban Atlas classifies every patch of land in 785 European cities into one of 17 categories: residential (low/medium/high density), industrial, commercial, airports, fast transit, urban green, forests, wetlands, water, etc. Think of it as a labelled zoning map derived from satellite imagery and ancillary data, updated roughly every 6 years.

We'll use it to:
- Assign a **land cover class** to each 100m grid cell (e.g. "high-density residential", "green urban area", "industrial")
- Calculate **% green urban area within a 500m radius** around each point — a second greenness feature alongside Sentinel-2 NDVI

---

## Where It Comes From

**Who produces it:** Copernicus Land Monitoring Service (managed by EEA, funded by EU)  
**How it's made:** Photo-interpretation of Sentinel-2 imagery + aerial photos, supplemented by national topographic data  
**Update cycle:** ~6 years (2006 → 2012 → 2018; 2024 edition not yet released as of May 2026)  
**Krakow coverage:** Full city extent, 2018 reference year

**Data flow:**
1. ESA provides Sentinel-2 imagery
2. EEA contractors photo-interpret and classify land cover
3. Quality control against national cadastral data
4. Published as GeoPackage (vector polygons, EPSG:3035)

---

## What's In The Dataset

**Each feature = one polygon with a land cover label**

Example:
```
Feature ID: PL001_KRK_024891
Class: 11100 (Continuous urban fabric, >80% impervious)
Area: 4,200 m²
Location: ul. Floriańska, Old Town
```

**The 17 land cover classes (grouped):**

| Group | Classes relevant to us |
|---|---|
| Urban fabric | 11100 continuous (>80% sealed), 11210 discontinuous dense (50-80%), 11220 medium (30-50%), 11230 low density (<30%) |
| Industrial / commercial | 12100 industrial, 12210 commercial |
| Green urban areas | 14100 green urban areas (parks, gardens), 14200 sports/leisure |
| Forests & semi-natural | 31000 forests, 32000 scrubland |
| Water | 50000 water bodies |

**What we'll actually use:**
- `pct_green_500m`: % of 500m radius classified as 14100 (green urban) or 31000 (forests)
- `land_cover_class`: majority class within each 100m grid cell (for model feature)

---

## What's Missing

**Temporal gap:**
- 2018 reference year. Anything built, demolished, or greened between 2019-2024 is not captured.
- Krakow has added parks and built new residential areas since 2018.
- **Mitigation:** Use Sentinel-2 NDVI (2024) as the primary greenness signal; Urban Atlas provides structural land cover context.

**Minimum mapping unit:**
- 50m MMU means patches smaller than 50m × 50m are not mapped.
- Small rooftop gardens, tree-lined streets, pocket parks (<0.25 ha) are missing.
- **Impact:** Green space slightly underestimated in dense areas.

**No 3D information:**
- Polygons are flat. No building heights, no canopy height.
- Can't model street canyon effect.

**No temporal resolution:**
- Single snapshot. Can't see seasonal change or year-on-year trends.

---

## Accuracy

**Overall classification accuracy:** 85% (published by EEA, validated against reference samples)

**Known confusion matrix issues:**
- Low-density residential vs. green urban areas: ~8% confusion (gardens inside residential properties misclassified as urban green)
- Industrial vs. commercial: ~5% confusion (light industrial buildings look similar to warehouses)

**What this means for us:**
- `pct_green_500m` may be slightly underestimated in residential areas with large gardens
- Not a major concern at 100m resolution — errors average out across the cell

---

## What We'll Use It For

**YES — good for:**
- Distinguishing residential from industrial areas as a contextual model feature
- Calculating % formal green space within 500m (complements NDVI which measures actual greenness signal)
- Identifying feasible locations for green corridor interventions (cells currently classified as roads or parking, adjacent to green urban areas)
- Cross-checking Sentinel-2 NDVI: if NDVI is high but Urban Atlas says industrial → flag as potential haze artifact

**NO — not good for:**
- Detecting green space changes after 2018
- Sub-50m features (individual trees, small gardens)
- Building density (use OSM building footprints instead)
- Any quantitative measure of tree canopy cover (use NDVI for that)

---

## How to Get It

**Download (bulk):**
```
URL: https://land.copernicus.eu/local/urban-atlas/urban-atlas-2018
Format: GeoPackage (.gpkg), EPSG:3035
File for Poland: PL_UA2018.gpkg (~180 MB)
Krakow layer: extract by bounding box [19.79, 49.97, 20.22, 50.13]
```

No API required — single bulk download, no login needed (free Copernicus account for EEA portal).

**Processing steps:**
```python
import geopandas as gpd

ua = gpd.read_file("PL_UA2018.gpkg", layer="Urban_Atlas_2018")
krakow = ua.cx[19.79:20.22, 49.97:50.13]  # Bounding box clip
krakow = krakow.to_crs("EPSG:32634")       # Reproject to match other layers

# Rasterize to 100m grid
# -> land_cover_class: majority class per cell
# -> pct_green_500m: % area with class 14100 or 31000 within 500m radius
```

**Data size:** ~180 MB raw GeoPackage; Krakow subset ~8 MB

---

## License

**License:** Copernicus open data policy — fully open, no restrictions  
**Attribution:** "© European Union, Copernicus Land Monitoring Service [year], European Environment Agency (EEA)"  
**Can we publish results?** Yes  
**Can we redistribute the processed raster?** Yes, with attribution

---

## Limitations

**What Urban Atlas CAN'T tell us:**

1. **Post-2018 changes** — Any park built or demolished after 2018 is invisible. Use Sentinel-2 for current greenness.
2. **Small green patches** — 50m MMU excludes pocket parks, street trees, private gardens. These matter at building scale but are less critical at our 100m planning scale.
3. **Pollution levels** — It's a land cover map. It tells us what the land *is*, not what the air *contains*.
4. **Causal intervention effects** — Reclassifying a cell from "residential" to "green urban" in the model predicts the *associated* PM2.5 change, not a proven causal reduction.

---

## Relationship to Other Datasets

| Dataset | How it relates to Urban Atlas |
|---|---|
| Sentinel-2 NDVI | Measures actual vegetation signal; Urban Atlas gives structural category. Use both — NDVI for "how green" and UA for "what type of land" |
| OpenStreetMap | OSM gives precise building footprints; UA gives land cover class. Use OSM for building density, UA for land cover type |
| AQICN PM2.5 | Target variable. UA land cover class is one predictor of PM2.5 in the model |

---

## Team Notes

**Status:** Downloaded, not yet processed into 100m raster grid.

**To do before model training:**
- [ ] Download PL_UA2018.gpkg from Copernicus portal
- [ ] Clip to Krakow bounding box
- [ ] Reproject to EPSG:32634
- [ ] Rasterize: land_cover_class (majority per 100m cell) + pct_green_500m (zonal stats)
- [ ] Spot-check against Google Maps for 10 known locations (Planty Park, Old Town, Nowa Huta)
- [ ] Add two output bands to `features_100m.tif`

**Known issue:** 2018 reference year is stale for the 2019-2024 model training period. Document as limitation in model card; do not attempt to "update" UA manually — use Sentinel-2 NDVI for temporal greenness signal instead.

---

## Bottom Line

**Is this good enough for our project?**  
**Yes, as a secondary structural feature.**

Urban Atlas doesn't replace Sentinel-2 (which gives actual greenness measurements) or OSM (which gives precise geometries). It adds something neither provides: a semantic label for what kind of urban environment each area is — which is useful both as a model feature and as a sanity check on other data.

The 2018 staleness is a real limitation, documented above. At our planning scale (100m cells, city-wide patterns), the structural land cover hasn't changed radically enough to invalidate the dataset.

**Confidence level: B**  
Useful contextual features, acceptable accuracy, manageable staleness.
