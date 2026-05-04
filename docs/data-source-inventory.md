# Data Source Inventory — Krakow Air Quality Project

**Last updated:** 04/05/26 
**Team:** Rim, Martina, Rashi, Bhavana

---

## What We're Looking For

We need PM2.5 air quality data for Krakow to answer: **Which urban features (roads, buildings, green space) predict pollution levels at 100-meter resolution?**

**Decision:** Krakow Planning Office will use our predictions to require green interventions (parks, green roofs) when approving new residential developments.

**Minimum requirements:**
- PM2.5 measurements (µg/m³)
- Krakow city coverage
- Recent data (2019 onwards preferred)
- Hourly or daily resolution
- Downloadable (not just live dashboards)

---

## Dataset Scoring Rubric

Score each dataset 0-2 on these criteria. **Need ≥10 out of 14 total to use it.**

| Criteria | 0 points | 1 point | 2 points |
|---|---|---|---|
| **Source trust** | Unknown source | Government/research org | Peer-reviewed/EU-regulated |
| **Spatial match** | Wrong city or too coarse | Krakow but sparse | Multiple Krakow stations |
| **Time coverage** | <1 year or outdated | 1-3 years | 3+ years recent |
| **License** | Unclear/restricted | Free with conditions | Fully open |
| **Download** | Manual only | API but unstable | Stable API or bulk file |
| **Documentation** | None | Basic metadata | Full technical docs |
| **Updates** | Dead/abandoned | Occasional | Active/maintained |

**Our baseline:** 100m grid cells across Krakow (our prediction targets)

---

## 1. WIOŚ Krakow (Regional Environmental Protection) ✅ ADOPT

**What it is:** Official Polish air quality monitoring data. WIOŚ (Wojewódzki Inspektorat Ochrony Środowiska) runs ~10-12 stations across Krakow measuring PM2.5, PM10, and other pollutants hourly.

**Source:** monitoring.krakow.pios.gov.pl (main portal) and powietrze.gios.gov.pl (national GIOŚ aggregator)

| Criteria | Score | Why |
|---|---|---|
| Source trust | 2 | Government regulatory agency, feeds into EU reporting |
| Spatial match | 1 | ~10-12 stations for Krakow (sparse but covers city) |
| Time coverage | 2 | Historical data back to 2015+, actively collecting |
| License | 1 | Public data but download process unclear |
| Download | 1 | Portal exists but no obvious bulk download API |
| Documentation | 1 | Station lists available, some metadata |
| Updates | 2 | Live hourly updates |

**Total: 10/14** ✅ **ADOPT**

**Why we need it:** This is the ground truth. These are the official stations the city uses for compliance monitoring.

**Main problem:** Getting the data out isn't straightforward. The portal shows real-time readings but bulk historical download requires some digging (or web scraping as last resort).

**Next steps:** 
- Check if GIOŚ national portal (powietrze.gios.gov.pl) has better export options
- If stuck, the World Air Quality Index (AQICN) aggregates this same data with an API

---

## 2. AQICN.org (World Air Quality Index) ✅ ADOPT

**What it is:** Global air quality aggregator that collects data from official sources worldwide, including WIOŚ Krakow. They provide historical data via API.

**Source:** aqicn.org/city/krakow 

| Criteria | Score | Why |
|---|---|---|
| Source trust | 2 | Aggregates official WIOŚ/GIOŚ data, widely used |
| Spatial match | 1 | Same ~10-12 stations as WIOŚ |
| Time coverage | 2 | Historical archives, multiple years |
| License | 2 | Free API access with attribution |
| Download | 2 | Clean REST API (`aqicn.org/api/`) |
| Documentation | 2 | API docs, station IDs, formats all documented |
| Updates | 2 | Real-time, hourly updates |

**Total: 13/14** ✅ **ADOPT as PRIMARY**

**Why we prefer this:** Much easier to download than wrestling with WIOŚ portal. It's the same underlying data (WIOŚ feeds into it), just with better access.

**API endpoint example:** `https://api.waqi.info/feed/krakow/?token=YOUR_TOKEN`

**Caveat:** Free tier has rate limits. For bulk historical, might need to loop through dates. Not a blocker, just means downloads take time.

---

## 3. OpenStreetMap (Building & Road Data) ✅ ADOPT

**What it is:** Crowdsourced map data. We need this to calculate urban features: road density, building footprints, distance to green space.

**Source:** openstreetmap.org via Overpass API or OSMnx library

| Criteria | Score | Why |
|---|---|---|
| Source trust | 1 | Crowdsourced, but Krakow well-mapped |
| Spatial match | 2 | Vector data, exact building/road locations |
| Time coverage | 1 | Current snapshot only (no historical tracking) |
| License | 2 | ODbL (open, attribution required) |
| Download | 2 | Overpass API, OSMnx Python library |
| Documentation | 2 | Extensive OSM wiki, tutorials everywhere |
| Updates | 2 | Constantly updated by volunteers |

**Total: 12/14** ✅ **ADOPT**

**Why we need it:** Can't calculate "road density" or "building density" without knowing where roads and buildings are. Satellite alone isn't enough.

**What we'll extract:**
- All roads (to calculate km/km² in each 100m cell)
- All buildings (to calculate % land covered)
- Parks and green spaces (to calculate distance to nearest park)

**Download approach:** OSMnx library in Python makes this trivial:
```python
import osmnx as ox
G = ox.graph_from_place("Krakow, Poland")
buildings = ox.geometries_from_place("Krakow, Poland", tags={"building": True})
```

---

## 4. Sentinel-2 Satellite Imagery (via Google Earth Engine) ✅ ADOPT

**What it is:** EU's free 10-meter resolution satellite. We'll calculate NDVI (greenness), NDBI (built-up areas), NDWI (water/moisture).

**Source:** Google Earth Engine (`COPERNICUS/S2_SR_HARMONIZED`)

| Criteria | Score | Why |
|---|---|---|
| Source trust | 2 | EU Copernicus program, scientific standard |
| Spatial match | 2 | 10m resolution (10× finer than our 100m grid) |
| Time coverage | 2 | 2015-present, 5-day revisit |
| License | 2 | Free, open (Copernicus policy) |
| Download | 2 | Google Earth Engine API (Python or JavaScript) |
| Documentation | 2 | Extensive GEE docs, community examples |
| Updates | 2 | New images every 5 days |

**Total: 14/14** ✅ **ADOPT** 

**Problem:** Winter in Krakow = lots of clouds. We'll get maybe 30% usable images Dec-Feb. Plan is to use monthly composites (cloud-free median) instead of individual images.

**What we'll calculate:**
- NDVI = (NIR - Red) / (NIR + Red) → Vegetation index (0 = no green, 1 = dense forest)
- NDBI = (SWIR - NIR) / (SWIR + NIR) → Built-up index (higher = more buildings/concrete)
- NDWI = (Green - NIR) / (Green + NIR) → Water bodies, wet surfaces

---

## 5. ERA5-Land Climate Reanalysis ⚠️ ADOPT (with limits)

**What it is:** ECMWF's weather reanalysis. Hourly temperature, wind, pressure. We need this to control for weather (pollution spikes on calm, cold days ≠ urban form).

**Source:** Copernicus Climate Data Store (cds.climate.copernicus.eu)

| Criteria | Score | Why |
|---|---|---|
| Source trust | 2 | ECMWF gold standard for climate data |
| Spatial match | 0 | 9km resolution (entire Krakow = 1-2 grid cells) |
| Time coverage | 2 | 1950-present |
| License | 2 | Free, open |
| Download | 1 | CDS API but slow, queues |
| Documentation | 2 | Extensive ECMWF docs |
| Updates | 2 | Near-real-time (5-day lag) |

**Total: 11/14** ✅ **ADOPT** (but only for temporal, not spatial features)

**The catch:** 9km resolution is way too coarse. All of Krakow looks like one weather cell. We'll use this for **time controls** ("Was Jan 15 a high-inversion day?") not spatial features.

**Variables we'll grab:**
- Temperature (2m height)
- Boundary layer height (affects pollution dispersion)
- Wind speed
- Pressure

---

## Datasets We Checked But REJECTED

### Zabierzów Station (aqicn.org/city/poland/malopolska/zabierzow--ul.-wapienna)

**Problem:** Zabierzów is a separate town 15km northwest of Krakow. Not representative of Krakow city conditions. **REJECT.**

### Kaggle "Poland PM2.5 2023" Dataset

**Status:** Can't access without Kaggle login, unclear if it includes Krakow specifically, appears to be repackaged GIOŚ data anyway. **REJECT** (use AQICN instead, same source data, better access).

### ICOS Carbon Portal

**Problem:** ICOS focuses on greenhouse gases (CO₂, CH₄). They don't do PM2.5 monitoring. Wrong pollutant type. **REJECT.**

### EEA Airbase (air.discomap.eea.europa.eu)

**Status:** This is the EU-wide aggregator. Poland reports to it. But AQICN is already pulling from the same chain (WIOŚ → GIOŚ → EEA → AQICN). No benefit to adding another source for the same stations. **SKIP** (use AQICN instead).

---

## What We're Missing (And Why It's Okay)

**1. Building heights**  
OSM has footprints but not heights for most buildings. This means we can't model "street canyons" (tall buildings trapping pollution). 

**Workaround:** Document in our model limitations. Maybe derive rough heights from Sentinel-2 shadow analysis if we have time.

**2. Traffic counts**  
We know where roads are (OSM) but not how many cars use them. Road density ≠ traffic volume.

**Workaround:** Road density is a decent proxy. Major roads = more traffic. Not perfect but probably good enough for R²≥0.40.

**3. Industrial emissions**  
No spatial data on which factories emit what. ArcelorMittal steel plant is huge but we don't have its emission rate.

**Workaround:** We're modeling residential areas primarily (that's where planning office makes decisions). Industrial zones are out of scope anyway.

---

## Summary: Final Data Stack

| Role | Dataset | Stations/Resolution | Time Span |
|---|---|---|---|
| **Target (PM2.5)** | AQICN (WIOŚ data) | ~10-12 stations | 2019-2024 |
| **Urban features** | Sentinel-2 | 10m pixels | 2019-2024 |
| **Roads/buildings** | OpenStreetMap | Vector (exact) | Current |
| **Weather control** | ERA5-Land | 9km (temporal only) | 2019-2024 |

**Total datasets: 4 (all scored ≥10/14)**

**Expected workflow:**
1. Download PM2.5 from AQICN for all Krakow stations (2019-2024)
2. For each station location, extract Sentinel-2 NDVI, OSM road density, OSM building density
3. Add ERA5 weather as monthly averages
4. Train model: Urban features → Predict PM2.5
5. Apply model to entire Krakow 100m grid
6. Rank interventions: Which urban changes reduce pollution most?

---

**Next:** Write full datasheets for AQICN and Sentinel-2 (our two primary sources).

