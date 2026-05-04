# Datasheet: Sentinel-2 Satellite Imagery (Krakow)

**Dataset:** Copernicus Sentinel-2 Level-2A Surface Reflectance  
**Access:** Google Earth Engine (GEE)  
**Resolution:** 10 meters  
**Created by:** Martina  
**Date:** December 2024

---

## What This Is

Sentinel-2 is the EU's free satellite that takes pictures of Earth every 5 days at 10-meter resolution. Think of it like Google Earth, but:
- Updated constantly (new images every few days)
- Multiple "colors" beyond what our eyes see (infrared, water-sensitive bands)
- Free and fully open

We'll use it to calculate:
- **NDVI** (vegetation index) - How green is this area?
- **NDBI** (built-up index) - How much concrete/buildings?
- **NDWI** (water index) - Where are wet surfaces, rivers?

---

## Where It Comes From

**Who runs it:** European Space Agency (ESA)  
**Who pays:** EU taxpayers (~€500 million per satellite)  
**Satellites:** Sentinel-2A (launched 2015) + Sentinel-2B (launched 2017)  
**Orbit:** 786 km above Earth, passes over Krakow every 5 days

**Data processing:**
1. Satellite takes raw images
2. ESA applies atmospheric correction (removes haze/clouds effect)
3. Google Earth Engine mirrors the data (makes it easier to use)
4. We query GEE for Krakow area

**Format:** We'll download monthly "composites" (median of all cloud-free pixels in each month) instead of individual images.

---

## What's In Each Image

**Spectral bands** (different "colors"):
- **B2** (Blue), **B3** (Green), **B4** (Red) → True color images
- **B8** (Near-Infrared) → Vegetation (plants reflect IR strongly)
- **B11** (Shortwave Infrared) → Buildings, soil moisture
- Plus several others we won't use

**Resolution:**
- B2, B3, B4, B8 → 10 meters per pixel
- Other bands → 20 meters or 60 meters
- **We'll stick to 10m bands**

**Krakow coverage:**
- Tile ID: 34UFA (covers all of Krakow + some surrounding areas)
- Image size: ~100 km × 100 km
- Pixels: ~10 million per band

**Quality masks:**
- Cloud mask (which pixels are clouds)
- Shadow mask
- Snow/ice mask
- Scene classification (cloud, vegetation, water, etc.)

---

## What We'll Calculate

**NDVI (Normalized Difference Vegetation Index):**
```
NDVI = (NIR - Red) / (NIR + Red)
     = (B8 - B4) / (B8 + B4)
```
- Range: -1 to +1
- <0 = water
- 0-0.2 = bare soil, buildings
- 0.2-0.5 = sparse vegetation
- 0.5-0.8 = healthy vegetation
- >0.8 = very dense vegetation (forests)

**NDBI (Normalized Difference Built-up Index):**
```
NDBI = (SWIR - NIR) / (SWIR + NIR)
     = (B11 - B8) / (B11 + B8)
```
- Range: -1 to +1
- High values = buildings, concrete, roads
- Low values = vegetation, water

**NDWI (Normalized Difference Water Index):**
```
NDWI = (Green - NIR) / (Green + NIR)
     = (B3 - B8) / (B3 + B8)
```
- Range: -1 to +1
- High values = water bodies
- Useful for detecting Vistula River, wetlands

---

## The Cloud Problem

**Winter in Krakow = cloudy**

Average cloud cover by month (rough estimates):
- Dec-Feb: 70-80% (only 2-3 usable images per month)
- Mar-May: 50-60%
- Jun-Aug: 30-40% (best season)
- Sep-Nov: 50-60%

**Impact:**
- Can't build monthly NDVI time series for winter
- Will use seasonal composites instead (DJF, MAM, JJA, SON)
- Bias: Summer overrepresented in our "clean" data

**Solution approach:**
Instead of individual images, we'll compute monthly medians:
1. Take all images from January 2024
2. Remove cloudy pixels (using cloud mask)
3. For each 10m pixel, take median of all cloud-free values
4. Result: One cloud-free composite image per month

---

## Gaps & Issues

**Temporal gaps:**
- Winter months have fewer usable images
- Sometimes entire months are cloudy (rare but happens)
- Data starts 2015 (Krakow urban form before that not available)

**Spatial gaps:**
- Clouds block ground even with masking (some pixels never cloud-free in winter)
- Dense tree canopy in Wolski Forest blocks ground in summer
- Shadows from tall buildings (Old Town, downtown high-rises)

**Known problems:**

**1. Haze contamination**  
Atmospheric correction (Sen2Cor algorithm) struggles in polluted air. High PM2.5 days → haze → NDVI looks lower even if vegetation unchanged.

**This is a BIG problem for our project:**  
Polluted days have lower NDVI not because less green space, but because haze blocks the signal. Could create spurious correlation (haze makes it look like less vegetation = more pollution, when causation is backwards).

**Mitigation:** Use only clear-sky days. Compare NDVI on high-PM2.5 vs low-PM2.5 days to check for bias.

**2. Shadow artifacts**  
Tall buildings cast shadows. Shadow pixels have low reflectance → misclassified as dark impervious surface.

**3. Seasonal vegetation**  
Krakow's parks are deciduous (leaves fall in winter). NDVI in Planty Park:
- Summer: 0.7-0.8 (dense green)
- Winter: 0.2-0.3 (bare branches)

Not a "problem" but need to account for it. Winter low NDVI doesn't mean "no vegetation" - just dormant.

---

## Accuracy & Validation

**Geometric accuracy:** ±10 meters (about 1 pixel)  
**Radiometric accuracy:** ±5% reflectance

**What this means:**
- A building's location might be off by 1 pixel (10m) - acceptable
- NDVI value of 0.5 might actually be 0.48-0.52 - acceptable

**Validation we did:**
- Compared 10 random Krakow locations with Google Street View
- NDVI high where we see parks → ✓
- NDVI low where we see concrete → ✓
- NDBI high in downtown dense buildings → ✓

---

## What We'll Use It For

**YES - good for:**
- Identifying green vs built-up areas
- Calculating "% green within 500m radius" around each air quality station
- Creating vegetation maps of Krakow
- Detecting changes over time (e.g., new park construction)

**NO - not good for:**
- Measuring air pollution directly (Sentinel-2 sees ground, not atmosphere)
- Identifying specific tree species (resolution too coarse)
- Winter vegetation health (deciduous trees dormant)
- Sub-10m features (individual trees, small gardens)

---

## How to Get It

**Google Earth Engine approach:**

```python
import ee

# Initialize GEE
ee.Initialize()

# Get Sentinel-2 collection for Krakow tile
s2 = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED') \
    .filterBounds(ee.Geometry.Point(19.95, 50.06))  # Krakow coords \
    .filterDate('2024-01-01', '2024-12-31') \
    .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 30))

# Calculate monthly NDVI composites
def add_ndvi(image):
    ndvi = image.normalizedDifference(['B8', 'B4']).rename('NDVI')
    return image.addBands(ndvi)

s2_ndvi = s2.map(add_ndvi)
monthly = s2_ndvi.select('NDVI').median()  # Median composite

# Export to Google Drive or download
task = ee.batch.Export.image.toDrive(
    image=monthly,
    description='krakow_ndvi_2024',
    scale=10,  # 10m resolution
    region=krakow_bbox
)
task.start()
```

**Requirements:**
- Google account
- GEE access (free for research/education)
- Python with `earthengine-api` library

**Data size:**
- One month, one band, 10m, Krakow area: ~50 MB
- Full 2019-2024 monthly NDVI stack: ~3 GB

---

## License

**License:** Free and open (Copernicus data policy)

**Attribution required:** "Contains modified Copernicus Sentinel data [year]"

**Can we publish results?** Yes  
**Can we redistribute processed data?** Yes (but cite source)  
**Commercial use?** Allowed

---

## Limitations (Be Honest)

**What Sentinel-2 CAN'T tell us:**

**1. Pollution levels**  
It measures reflected light from the ground. It does NOT measure air quality. We're using NDVI as a *proxy* (greener areas might have less pollution) but it's not a direct measurement.

**2. Sub-10m features**  
Can't see individual street trees, small rooftop gardens, narrow alleys. 10m pixels average everything in that square.

**3. Real-time conditions**  
5-day revisit, plus cloud delays. If a park was built last week, we won't see it until next clear-sky image (could be weeks in winter).

**4. Nighttime**  
Sentinel-2 is optical (visible/infrared light). Only works during daytime passes (~10:30 AM local time).

**5. Indoor/underground**  
Can't see underground parking, interior courtyards with overhangs, etc.

---

## Comparison With Other Data

**Sentinel-2 vs OpenStreetMap:**
- OSM: Exact building outlines but crowdsourced (some gaps)
- S2: Complete coverage but 10m blur, can't distinguish building from parking lot

**We'll use both:**
- OSM for building footprints (where are buildings?)
- S2 for vegetation (how green is the area?)

**Sentinel-2 vs Landsat:**
- Landsat: 30m resolution (coarser)
- Sentinel-2: 10m resolution (better for cities)
- We're using Sentinel-2

**Sentinel-2 vs drones/aircraft:**
- Drones: 0.05m resolution but expensive, limited coverage
- Sentinel-2: 10m but free and covers entire Krakow every 5 days
- We're using Sentinel-2 (fits our budget: €0)

---

## Team Notes

**Martina's workflow:**
1. Downloaded all 2019-2024 images for tile 34UFA with <30% cloud cover
2. Calculated NDVI, NDBI, NDWI for each image
3. Created monthly composites (median of cloud-free pixels)
4. Result: 72 monthly images (6 years × 12 months)
5. Actually usable after cloud filtering: ~55 monthly composites

**Storage:**
- Raw GEE exports: 2.8 GB
- Stored in `data/processed/sentinel2/monthly/`
- Individual files: `krakow_ndvi_2024-01.tif`, etc.

**Issues found:**
- December 2022: Entirely cloudy, no usable images. Used Nov+Jan average as proxy.
- Shadow masking imperfect in dense downtown (Old Town). Manually inspected, acceptable.
- Some edge pixels outside Krakow boundary - will crop to city limits.

---

## The Atmospheric Bias Risk

**This is our #1 data quality concern.**

High pollution → haze → lower NDVI  
Not because vegetation changed  
But because atmosphere blocked the signal

**Test we'll do:**
1. Find days with high PM2.5 + clear sky (rare but exists)
2. Find days with low PM2.5 + clear sky
3. Compare NDVI at same location on both days
4. If NDVI significantly different → we have a haze problem

**If haze bias confirmed:**
- Option A: Use only lowest-PM2.5 days (summer, good weather) - but then lose winter signal
- Option B: Include boundary layer height (ERA5-Land) as control variable to partial out haze effect
- Option C: Document it heavily in limitations and reduce confidence in predictions

**Status:** Test not done yet. Rim + Martina will run this in Session 3.

---

## Bottom Line

**Is this good enough for our project?**  
**Yes, with caveats.**

10m resolution is perfect for 100m grid cells (10× finer than decision unit).  
Free access via GEE is a massive win.  
Cloud cover is annoying but manageable (monthly composites work).

The atmospheric bias risk is real and we need to test for it. If NDVI is contaminated by haze, our whole "green space → low pollution" hypothesis could be backwards causation.

**Confidence level: B**  
Good spatial data, serious temporal limitations (winter gaps), critical bias risk (haze).

**Next step:** Run haze bias test before trusting NDVI-pollution correlations.
