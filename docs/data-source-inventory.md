# Data Source Inventory

> Minimum 5 candidate datasets, each scored against the Dataset Assessment
> Rubric. Adopt only if total ≥ 10/14. Reject low scorers — that's the point
> of the rubric.

**Project:** Krakow Air Quality & Urban Form  
**Team:** Rim, Martina, Rashi, Bhavana  
**Date:** 04/05/26

---

## How to use this file

1. List at least 5 candidate datasets. Don't stop at the first match — survey
   the landscape across the 6 categories (remote sensing optical, remote
   sensing thermal/radar, climate reanalysis, in-situ sensors, biodiversity,
   built environment).
2. For each, fill out provider, access method, and the rubric scoring table.
3. Write a one-paragraph plain-English description.
4. Issue a verdict: **Adopt / Reject / Investigate further.**
5. Only "Adopt" datasets get a full datasheet (`datasheets/<slug>.md`).

## The Dataset Assessment Rubric

| Axis | 0 | 1 | 2 |
|---|---|---|---|
| **Provenance** | Source unclear | Source documented | Documented + cited in peer-reviewed work |
| **Resolution match** | Coarser than decision unit | Roughly matches | ≥2× finer than decision unit |
| **Coverage** | Major gaps over our place/time | Minor gaps | Full coverage |
| **License** | Unclear / restrictive | Permissive with attribution | Public domain / CC0 |
| **Access reliability** | Manual scraping, fragile | API but rate-limited or unstable | Stable API or stable bulk download |
| **Bias clarity** | Unknown biases | Some documented | Biases fully documented + quantified |
| **Maintenance** | Stale, no updates | Updated irregularly | Actively maintained, contact available |

**Our decision unit:** 100m × 100m grid cells (neighborhood planning scale)  
**Our place/time:** Krakow, Poland / 2019–2024

---

## 1. AQICN (World Air Quality Index) - Krakow PM2.5

- **Provider:** AQICN.org (aggregates official WIOŚ/GIOŚ Poland government data)
- **Access method (URL / API / portal):** https://aqicn.org/city/krakow + REST API (https://aqicn.org/api/)
- **Category:** in-situ-sensors

### Rubric scoring (0–2 per axis)

| Axis | Score | Justification |
|---|---|---|
| Provenance | 2 | Aggregates official Polish government monitoring (WIOŚ Krakow → GIOŚ → EEA → AQICN). Chain documented, cited in 100+ air quality studies. |
| Resolution match | 1 | Point measurements at ~10-12 stations. Must interpolate to 100m grid. Sparse but usable. |
| Coverage | 1 | Full Krakow coverage but only ~10 stations for 327 km². Major gaps in suburbs (>2km from any station = 40% of city). |
| License | 2 | Public data, free API access with attribution. CC BY 4.0 equivalent. |
| Access reliability | 2 | Stable REST API, running since 2007. Rate limits exist (1000 req/min) but sufficient for our use. |
| Bias clarity | 2 | Station placement bias documented (traffic-focused, regulatory compliance). ±15% measurement uncertainty published (EU standard). |
| Maintenance | 2 | Live hourly updates, historical archives maintained, active community support. |
| **TOTAL** | **12/14** | |

### One-paragraph description

AQICN aggregates hourly PM2.5 measurements from ~10-12 official monitoring stations across Krakow (WIOŚ regional environmental agency). Each measurement is a point reading (µg/m³) at a specific location and time. Temporal resolution is hourly, spatial resolution is station locations only (~1 per 30 km²). Good for: training pollution prediction models at station locations, validating 100m grid predictions via interpolation. Cannot tell us: pollution levels between stations (must interpolate), sub-hourly fluctuations (too noisy), building-scale patterns (<100m resolution impossible with 10 points).

### Verdict

**Adopt.** Best available PM2.5 data for Krakow. Sparse spatial coverage is a known limitation but acceptable for 100m grid modeling with documented uncertainty in station-sparse areas.

---

## 2. Sentinel-2 Multispectral Imagery (Google Earth Engine)

- **Provider:** European Space Agency (ESA) Copernicus program, accessed via Google Earth Engine
- **Access method:** Google Earth Engine Python/JavaScript API (https://developers.google.com/earth-engine)
- **Category:** remote-sensing-optical

### Rubric scoring

| Axis | Score | Justification |
|---|---|---|
| Provenance | 2 | ESA Copernicus mission, Sen2Cor atmospheric correction peer-reviewed, cited in 10,000+ papers. |
| Resolution match | 2 | 10m native resolution (10× finer than our 100m decision unit). Bands B2-B4-B8 all 10m. |
| Coverage | 1 | Full Krakow coverage but 70% cloud cover Dec-Feb. Only ~30% of winter images usable. Minor temporal gaps. |
| License | 2 | Copernicus Open Access Data Policy - fully open, no restrictions. |
| Access reliability | 2 | GEE hosts full Sentinel-2 archive (2015-present), stable API, petabyte-scale infrastructure. |
| Bias clarity | 1 | Atmospheric haze bias documented (polluted air reduces NDVI) but not fully quantified for our use case. |
| Maintenance | 2 | Active mission (2015-2030+), new images every 5 days, ESA support available. |
| **TOTAL** | **12/14** | |

### One-paragraph description

Sentinel-2 provides 10-meter resolution multispectral satellite imagery of Krakow every 5 days (two satellites: 2A + 2B). An instance is one image covering ~100 km × 100 km with 13 spectral bands. We'll calculate NDVI (vegetation index), NDBI (built-up index), NDWI (water index) from bands B2-B4-B8-B11. Temporal resolution is 5-day revisit, cloud filtering reduces to ~monthly composites. Good for: measuring greenness, built-up density, land cover at 10m scale across entire Krakow. Cannot tell us: pollution levels directly (it's a camera, not an air quality sensor), conditions under dense clouds (winter gaps), sub-10m features (individual trees, small gardens).

### Verdict

**Adopt.** Essential for urban form features (greenness, buildings). Winter cloud gaps are annoying but manageable via seasonal composites. Atmospheric bias (haze affecting NDVI) is a known risk we'll test for.

---

## 3. OpenStreetMap (Road Network & Buildings)

- **Provider:** OpenStreetMap Foundation (crowdsourced)
- **Access method:** Overpass API (https://overpass-api.de/) or OSMnx Python library
- **Category:** built-environment

### Rubric scoring

| Axis | Score | Justification |
|---|---|---|
| Provenance | 1 | Crowdsourced (variable contributor expertise). Used in academic studies but not peer-reviewed data source itself. |
| Resolution match | 2 | Vector data - exact building footprints and road centerlines (sub-meter precision). Far exceeds 100m requirement. |
| Coverage | 2 | ~95% of Krakow buildings mapped (validated against municipal cadastre). Roads >99% complete. |
| License | 2 | ODbL (Open Database License) - open with share-alike, attribution required. |
| Access reliability | 2 | Stable Overpass API, OSMnx library widely used. Data mirrors available if main server fails. |
| Bias clarity | 1 | Mapper bias toward roads > buildings documented generally, but not quantified for Krakow specifically. |
| Maintenance | 1 | Continuously updated by volunteers, but no formal QA process. Updates irregular (not guaranteed timely). |
| **TOTAL** | **11/14** | |

### One-paragraph description

OpenStreetMap provides vector geometries (polygons, lines) for all roads and buildings in Krakow. An instance is a single feature (one building polygon, one road segment). Spatial resolution is exact (sub-meter coordinates), no temporal resolution (snapshot, not time series). Good for: calculating road density (km/km²), building footprint coverage (% of area), distance to major roads. Cannot tell us: building heights for most structures (~70% missing height tags), historical changes (no timestamps on most features), traffic volumes (roads exist but usage data not in OSM).

### Verdict

**Adopt.** Critical for urban form features. Crowdsourced nature is a limitation but Krakow mapping quality is high (verified via spot checks). Missing building heights documented as known gap.

---

## 4. ERA5-Land Climate Reanalysis

- **Provider:** European Centre for Medium-Range Weather Forecasts (ECMWF) via Copernicus Climate Data Store
- **Access method:** CDS API (https://cds.climate.copernicus.eu/)
- **Category:** climate-reanalysis

### Rubric scoring

| Axis | Score | Justification |
|---|---|---|
| Provenance | 2 | ECMWF gold standard for climate reanalysis, peer-reviewed methods, cited in 5000+ papers. |
| Resolution match | 0 | 9km grid (90× coarser than our 100m decision unit). Entire Krakow = 1-2 grid cells. Massive spatial mismatch. |
| Coverage | 2 | Full global coverage, hourly 1950-present, no gaps for Krakow 2019-2024. |
| License | 2 | Copernicus C3S open license - fully open. |
| Access reliability | 1 | CDS API works but slow (queues during peak times), bulk downloads can take hours. |
| Bias clarity | 2 | Uncertainty estimates provided for all variables. Urban heat island effect documented as limitation. |
| Maintenance | 2 | Continuously updated (5-day lag), active ECMWF support team. |
| **TOTAL** | **11/14** | |

### One-paragraph description

ERA5-Land provides hourly weather variables (temperature, wind speed, boundary layer height, pressure) at 9km resolution globally. An instance is one grid cell at one hour. Temporal resolution is hourly, spatial resolution is 9km (too coarse for spatial features but fine for temporal controls). Good for: filtering high-inversion days (when pollution spikes everywhere due to weather), adding monthly temperature/wind as model control variables. Cannot tell us: spatial weather patterns within Krakow (entire city looks uniform at 9km), urban heat island effects (averaged out), local wind channeling (street-scale phenomena).

### Verdict

**Adopt (with restriction).** Only use for TEMPORAL deconfounding (monthly averages, high-inversion flags), NOT as spatial features in the model. 9km is way too coarse for 100m grid predictions but acceptable for time controls.

---

## 5. Copernicus Urban Atlas (Land Cover Classification)

- **Provider:** European Environment Agency (EEA) / Copernicus Land Monitoring Service
- **Access method:** Bulk download (https://land.copernicus.eu/local/urban-atlas)
- **Category:** remote-sensing-optical (derived product)

### Rubric scoring

| Axis | Score | Justification |
|---|---|---|
| Provenance | 2 | EU Copernicus program, peer-reviewed methodology, cited in 500+ urban studies. |
| Resolution match | 1 | 50m minimum mapping unit (half our 100m decision unit). Acceptable but not ideal. |
| Coverage | 1 | Full Krakow coverage but 2018 version (6-year lag). Urban form may have changed since then. |
| License | 2 | Copernicus open data policy - fully open. |
| Access reliability | 2 | Stable bulk downloads (GeoPackage format), EEA servers reliable. |
| Bias clarity | 2 | 85% classification accuracy published, confusion matrix available. Known issues with small parks (<0.25 ha) documented. |
| Maintenance | 1 | Updated every ~6 years (slow). 2018 → next expected 2024 but not yet released. |
| **TOTAL** | **11/14** | |

### One-paragraph description

Urban Atlas classifies land cover into 17 categories (residential, industrial, green urban areas, forests, water, etc.) at 50m minimum mapping unit for European cities. An instance is a polygon with a land cover class. Spatial resolution is 50m MMU, temporal resolution is snapshot per update cycle (~6 years). Good for: identifying land cover type (residential vs industrial), calculating % green space within 500m radius, contextualizing station environments. Cannot tell us: recent changes (2018-2024 gap), fine-scale green spaces (<0.25 ha minimum), building heights or density (classification only, not 3D).

### Verdict

**Adopt.** Useful for land cover context despite 2018 lag. We can update green space changes with 2024 Sentinel-2 NDVI to partially address staleness.

---

## 6. WIOŚ Krakow Air Quality Portal (REJECTED)

- **Provider:** Wojewódzki Inspektorat Ochrony Środowiska w Krakowie (Regional Environmental Protection)
- **Access method:** Web portal (https://monitoring.krakow.pios.gov.pl/)
- **Category:** in-situ-sensors

### Rubric scoring

| Axis | Score | Justification |
|---|---|---|
| Provenance | 2 | Official Polish government monitoring, regulatory compliance data. |
| Resolution match | 1 | Point measurements at ~10 stations (same as AQICN). |
| Coverage | 1 | Same stations as AQICN (it's the original source). |
| License | 1 | Public data but unclear reuse terms, no explicit license statement. |
| Access reliability | 0 | Web portal only, no bulk download API. Would require web scraping (fragile). |
| Bias clarity | 2 | EU monitoring standards, ±15% uncertainty documented. |
| Maintenance | 2 | Live updates, official government service. |
| **TOTAL** | **9/14** | |

### One-paragraph description

WIOŚ operates the physical monitoring stations that AQICN aggregates. Portal shows real-time readings but lacks bulk historical download. Same data as AQICN but harder to access programmatically.

### Verdict

**Reject.** AQICN provides the exact same data (it pulls from WIOŚ → GIOŚ → EEA chain) with a far better API. No benefit to using WIOŚ portal directly. Stick with AQICN.

---

## 7. Kaggle "Poland PM2.5 2023 Hourly" Dataset (REJECTED)

- **Provider:** User upload on Kaggle
- **Access method:** Kaggle Datasets (https://www.kaggle.com/datasets/wisekinder/poland-cities-quality-pm2-5-level-2023-every-hour)
- **Category:** in-situ-sensors (repackaged)

### Rubric scoring

| Axis | Score | Justification |
|---|---|---|
| Provenance | 1 | Unclear - appears to be scraped GIOŚ data but no documentation of methodology. |
| Resolution match | 1 | Point measurements if Krakow included (listing says "Poland cities" generically). |
| Coverage | 0 | 2023 only (1 year). Doesn't cover our 2019-2024 range. Unclear if Krakow even included. |
| License | 0 | Kaggle default license unclear. User upload, not official source. |
| Access reliability | 0 | Requires Kaggle account (login wall). Dataset could be removed by uploader anytime. |
| Bias clarity | 0 | No metadata about station selection, QA procedures, or biases. |
| Maintenance | 0 | User upload from 2023, no updates since. Stale. |
| **TOTAL** | **2/14** | |

### One-paragraph description

Kaggle user upload claiming hourly PM2.5 for Polish cities in 2023. No documentation of source, methodology, or which cities are included. Appears to be repackaged GIOŚ data but unverified.

### Verdict

**Reject.** Fails on access reliability (login required), coverage (1 year only), provenance (unclear source), and license (ambiguous). AQICN provides same underlying data with better documentation and API.

---

## 8. Zabierzów Air Quality Station (REJECTED)

- **Provider:** AQICN.org
- **Access method:** https://aqicn.org/city/poland/malopolska/zabierzow--ul.-wapienna/
- **Category:** in-situ-sensors

### Rubric scoring

| Axis | Score | Justification |
|---|---|---|
| Provenance | 2 | Same as AQICN Krakow (official WIOŚ data). |
| Resolution match | 1 | Point measurement (1 station). |
| Coverage | 0 | Zabierzów is a separate town 15km northwest of Krakow. Not representative of Krakow urban conditions. |
| License | 2 | Same as AQICN (open with attribution). |
| Access reliability | 2 | Same AQICN API. |
| Bias clarity | 2 | WIOŚ standards. |
| Maintenance | 2 | Live updates. |
| **TOTAL** | **11/14** | But wrong location |

### One-paragraph description

AQICN station in Zabierzów, a suburban town 15km from Krakow city center. Same data quality as Krakow AQICN but geographically separate municipality.

### Verdict

**Reject.** Wrong location. Zabierzów is not Krakow. Air quality in a suburban town 15km away is not representative of Krakow's dense urban core or industrial zones. Only use Krakow city stations.

---

## 9. ICOS Carbon Portal (REJECTED)

- **Provider:** Integrated Carbon Observation System (ICOS)
- **Access method:** https://meta.icos-cp.eu/
- **Category:** in-situ-sensors (greenhouse gases)

### Rubric scoring

| Axis | Score | Justification |
|---|---|---|
| Provenance | 2 | Research infrastructure, peer-reviewed network. |
| Resolution match | 1 | Point measurements at tower locations. |
| Coverage | 0 | No PM2.5 data. ICOS measures CO₂, CH₄, N₂O (greenhouse gases), not particulate matter. |
| License | 2 | Open data with CC BY 4.0. |
| Access reliability | 2 | Stable portal, REST API available. |
| Bias clarity | 2 | Measurement protocols documented. |
| Maintenance | 2 | Active research network. |
| **TOTAL** | **11/14** | But wrong pollutant |

### One-paragraph description

ICOS operates a network of atmospheric monitoring towers measuring greenhouse gases (CO₂, CH₄, N₂O) for climate research. High-quality data but focused on carbon cycle, not air quality pollutants.

### Verdict

**Reject.** Wrong pollutant. We need PM2.5 (particulate matter), not CO₂ (greenhouse gas). ICOS doesn't measure what we're studying.

---

## 10. Krakow Low Emission Zone Website (REJECTED)

- **Provider:** Krakow city government (ZTP)
- **Access method:** https://ztp.krakow.pl/en/lez/air-quality-status
- **Category:** (unclear - appears to be informational portal)

### Rubric scoring

| Axis | Score | Justification |
|---|---|---|
| Provenance | 1 | City government website. |
| Resolution match | 0 | Not a dataset - informational portal showing current status. |
| Coverage | 0 | 403 Forbidden error when accessed. Site may be restricted or broken. |
| License | 0 | Not applicable (not a data source). |
| Access reliability | 0 | 403 error - inaccessible. |
| Bias clarity | 0 | N/A |
| Maintenance | 0 | Uncertain (can't access). |
| **TOTAL** | **1/14** | |

### One-paragraph description

City website for Low Emission Zone information. Appears to show current air quality status but is not a data download source. Returns 403 Forbidden error when accessed (may be geoblocked or authentication required).

### Verdict

**Reject.** Not a dataset (just an informational website), and currently inaccessible (403 error). Even if accessible, appears to be live dashboard only, not historical data source.

---

## Summary

### Adopted (5 datasets, all scored ≥10/14):

1. **AQICN Krakow PM2.5** (12/14) - Primary target variable, ~10 stations, 2019-2024
2. **Sentinel-2 via GEE** (12/14) - Primary spatial features (NDVI, NDBI), 10m resolution
3. **OpenStreetMap** (11/14) - Secondary (road/building density), vector precision
4. **ERA5-Land** (11/14) - Secondary (weather controls, temporal only), 9km resolution
5. **Copernicus Urban Atlas** (11/14) - Secondary (land cover context), 50m MMU, 2018

### Rejected (5 datasets):

1. **WIOŚ Portal** (9/14) - Same data as AQICN but worse access (no API)
2. **Kaggle Poland PM2.5** (2/14) - Login wall, unclear provenance, 1 year only, likely repackaged GIOŚ data
3. **Zabierzów Station** (11/14) - Wrong location (different town 15km away)
4. **ICOS Carbon Portal** (11/14) - Wrong pollutant (CO₂ not PM2.5)
5. **Krakow LEZ Website** (1/14) - Not a dataset, 403 error, informational only

### Under investigation:

None. All candidates evaluated and verdict issued.

### Coverage gaps:

**What we're missing (and accepting as limitations):**

1. **Traffic volume data** - We have road locations (OSM) but not vehicle counts. Road density is a proxy but imperfect (roads don't pollute, cars do).

2. **Building heights** - OSM has footprints but ~70% missing height tags. Can't model "street canyon" effect (tall buildings trapping pollution).

3. **Industrial emissions inventory** - No spatial data on factory/plant emissions. Krakow has ArcelorMittal steel plant and other sources but we can't attribute pollution to specific point sources.

4. **Dense low-cost sensor network** - Only 10 official stations. Ideally would have 50-100 low-cost sensors (e.g., PurpleAir) for better spatial coverage. Not available for Krakow.

**Sub-questions affected:**
- Q1 (Where is pollution worst?) - Partial coverage only, high uncertainty >2km from stations
- Q3 (Effect sizes) - Missing confounders (traffic, industrial) will inflate uncertainty
- Q4 (Intervention ranking) - No cost data to rank by cost-effectiveness (impact only)

**Mitigation strategies:**
- Document uncertainty maps showing confidence by distance to nearest station
- Use road density as traffic proxy (imperfect but correlated)
- Exclude cost-benefit from scope, rank interventions by predicted impact only
- Be transparent in model card about missing data and resulting limitations
