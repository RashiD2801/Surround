# Datasheet: AQICN Krakow PM2.5 Data

**Dataset:** World Air Quality Index (AQICN) - Krakow stations  
**Pollutant:** PM2.5 (fine particulate matter)  
**Time period:** 2019-2024  
**Created by:** Martina 
**Date:** 04-05-2026

---

## What This Data Is

AQICN aggregates air quality measurements from official government monitoring stations worldwide. For Krakow, they pull data from WIOŚ (Wojewódzki Inspektorat Ochrony Środowiska) - Poland's Regional Environmental Protection agency.

**In plain terms:** These are the same official measurements the Polish government uses to check if air quality meets EU standards. AQICN just makes them easier to download.

---

## Where It Comes From

**Data flow:**
1. Physical sensors at ~10-12 stations across Krakow measure PM2.5 every hour
2. WIOŚ Krakow collects and validates the data
3. WIOŚ reports to GIOŚ (national environmental agency)
4. GIOŚ shares with European Environment Agency
5. AQICN pulls it all and makes it available via API

**Who funds it:** Polish government (WIOŚ/GIOŚ operations), EU (equipment co-funding)

**Who can use it:** Anyone - it's public data

---

## What's In The Dataset

**Each row = one hourly measurement at one station**

Example:
```
Station: Aleja Krasińskiego (downtown Krakow)
Time: 2024-01-15 14:00 UTC
PM2.5: 42.3 µg/m³
AQI: 118 (Unhealthy for sensitive groups)
```

**Krakow stations** (approximately 10-12, exact number varies as some go offline):
- Aleja Krasińskiego (city center, traffic)
- ul. Dietla (downtown)
- Kurdwanów (residential south)
- Nowa Huta (industrial east)
- Złoty Róg (west)
- Several others

**Time range:** Historical data back to ~2015, actively updated hourly

**Measurements:**
- PM2.5 concentration (µg/m³)
- PM10 (often from same station)
- Sometimes: NO₂, O₃, CO
- AQI (Air Quality Index - US EPA scale)
- Weather: temperature, humidity (not always available)

---

## What's Missing 

### Gaps we found:

**Spatial gaps:**
- Only ~10 stations for 327 km² of Krakow
- That's roughly 1 station per 30 km²
- Suburbs barely covered (most stations downtown)
- No stations in major parks (Planty, Błonia, Wolski Forest)

**Temporal gaps:**
- Winter 2020-2021: Some stations offline during COVID (maintenance delays)
- Random outages: Usually a few hours, occasionally days
- Overall completeness: ~70-75% (missing 25-30% of expected hourly readings)

**Field-level issues:**
- Weather data spotty (not all stations report it)
- Station coordinates sometimes imprecise (±50-100m)
- No metadata about station type (traffic vs background vs industrial) in API response - have to look that up separately

### Known problems:

**1. Winter bias**  
Sensors struggle in extreme cold (<-15°C). More failures in January-February when pollution is worst.

**2. Negative values**  
Found 3-5 instances of negative PM2.5 readings (physically impossible). Sensor calibration drift.  
**Fix:** Clip to 0.

**3. Suspiciously flat readings**  
One station had identical readings (±0.1 µg/m³) for 48 hours straight despite weather changes.  
**Fix:** Drop those periods.

**4. Unit confusion**  
AQICN consistently uses µg/m³, but we saw one Kaggle dataset claiming to be from same source using mg/m³. Always verify units.

---

## Accuracy & Uncertainty

**Measurement precision:** ±15% (EU standard for PM2.5 monitors)

**What this means:**  
If it reads 40 µg/m³, actual value is probably 34-46 µg/m³.

**Cross-checking:**  
We compared AQICN to the original WIOŚ portal for 5 random days. Perfect match - it's the same data.

**Biases:**

- **Placement bias:** Stations placed for compliance monitoring, not scientific sampling. More stations near roads and in city center than in suburbs or parks.

- **Temporal bias:** Data from 2019-2024 reflects Krakow AFTER coal heating ban (Sept 2019) and AFTER Low Emission Zone started (2024). Won't represent older "high-coal" period.

- **Weather dependence:** High pollution correlates with calm, cold weather (temperature inversions). If we only use days with Sentinel-2 satellite images (cloud-free = good weather), we'll undersample bad pollution days.

---

## What We'll Use It For

**YES - good for:**
- Training our prediction model (PM2.5 is the target variable we're trying to predict)
- Validating predictions at station locations
- Understanding which areas currently have high pollution
- Monthly/seasonal averages

**NO - not good for:**
- Predicting pollution at specific addresses (stations too sparse)
- Hour-to-hour forecasting (too noisy, weather-driven)
- Attributing pollution to specific sources (measures total, not source-specific)
- Personal exposure assessment (neighborhood averages, not individual)

---

## How to Get It

**API method (recommended):**
```python
import requests

# Get current data
url = "https://api.waqi.info/feed/krakow/?token=YOUR_TOKEN"
response = requests.get(url)
data = response.json()

# Get historical (have to loop through dates)
url = f"https://api.waqi.info/feed/@{station_id}/?token=YOUR_TOKEN"
```

**API token:** Free at aqicn.org/api - just register

**Rate limits:** 
- Free tier: 1000 requests/minute
- Enough for our project (we'll cache data, not query live constantly)

**Alternative:** WIOŚ Krakow portal (monitoring.krakow.pios.gov.pl) but harder to download bulk data

---

## License & Attribution

**License:** Public data, free to use

**Required attribution:**  
"Data from aqicn.org" + link to their site

**Can we publish our results?** Yes  
**Can we redistribute raw data?** Technically yes, but cite the source  
**Can we use commercially?** API terms allow research/education, commercial unclear - check if this matters

---

## Limitations (Be Honest)

**What this dataset CAN'T tell us:**

1. **Pollution levels between stations**  
   We have 10 points. Krakow is 327 km². We'll interpolate, but it's educated guessing in the gaps.

2. **Why pollution is high**  
   Sensors measure total PM2.5. They don't say "30% from traffic, 40% from heating, 30% from neighboring towns."

3. **Building-scale patterns**  
   Station spacing too wide to capture "this street is polluted but the next one over is fine."

4. **Future trends**  
   Historical data. Can't predict how Low Emission Zone (started 2024) will change things in 2025-2026.

---

## Things That Could Go Wrong

**If AQICN goes down:**  
Fall back to WIOŚ portal or EEA Airbase (same underlying data, different access point)

**If stations get moved:**  
Check station metadata before using historical data. Coordinates should be stable but verify.

**If API changes:**  
AQICN is a volunteer project. API could change without warning. Document the version/format we used.

**If data quality degrades:**  
Use the `aqi` field as a quality flag. If it's -1 or null, measurement is invalid.

---

## Related Datasets

This pairs with:
- **Sentinel-2** (satellite) - gives us urban form features (greenness, buildings)
- **OpenStreetMap** - gives us road network and building locations
- **ERA5-Land** - gives us weather to control for temperature inversions

See `data-source-inventory.md` for full list.

---

## Team Notes

**Rim's notes:**  
Downloaded 2019-2024 for 10 stations successfully. Total ~400k rows (after dropping invalids). Stored in `data/raw/aqicn/`.

**Issues found:**
- Station "Złoty Róg" has suspicious gap Dec 2022 - investigate
- Some stations report PM10 but not PM2.5 - filter carefully
- Coordinates for 2 stations don't match Google Maps - need to correct manually

**Martina's validation:**  
Spot-checked 20 random days against WIOŚ portal screenshots. 100% match on values, timestamps off by 1 hour (timezone - AQICN uses UTC, WIOŚ uses local time CET/CEST).

---

## Bottom Line

**Is this good enough for our project?**  
**Yes.** 

It's official government data accessed via a better interface. The spatial gaps are real (only 10 stations) but we knew that going in. We'll document uncertainty in areas far from stations.

The main risk is that we're extrapolating from 10 points to 32,700 grid cells (100m resolution). That's aggressive. But if we're transparent about uncertainty and use cross-validation to quantify errors, it's defensible.

**Confidence level: B+**  
Good enough to build the tool, but need to be very clear about limitations in the model card.
