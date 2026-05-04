# System Sketch v0 — Krakow Air Quality Project

**What this shows:** How data flows from download → processing → model → decision support tool

**Last updated:** December 2024

---

## The Big Picture (In One Sentence)

Download PM2.5 measurements and satellite images → Calculate urban features → Train model to predict pollution from features → Apply to entire Krakow grid → Rank interventions → Give to planning office.

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    DATA SOURCES                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  AQICN API          Sentinel-2         OpenStreetMap       │
│  (PM2.5 data)       (GEE satellite)    (roads/buildings)   │
│      ↓                   ↓                    ↓             │
│   ~440k hourly       90 monthly          Vector data       │
│   measurements       composites          (Krakow bbox)     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│              DATA PROCESSING PIPELINE                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Step 1: DOWNLOAD                                           │
│  • script: 01_download_data.py                              │
│  • output: data/raw/                                        │
│                                                             │
│  Step 2: CALCULATE FEATURES                                 │
│  • script: 02_calculate_features.py                         │
│  • NDVI from Sentinel-2                                     │
│  • Road density from OSM                                    │
│  • Building density from OSM                                │
│  • output: data/processed/features_100m_grid.tif            │
│                                                             │
│  Step 3: AGGREGATE TIME                                     │
│  • script: 03_aggregate_temporal.py                         │
│  • AQICN hourly → monthly means                             │
│  • Filter out invalid/missing data                          │
│  • output: data/processed/aqicn_monthly.csv                 │
│                                                             │
│  Step 4: SPATIAL JOIN                                       │
│  • script: 04_spatial_join.py                               │
│  • Extract features at each station location                │
│  • output: data/processed/training_data.csv                 │
│    (10 stations × 60 months = ~600 training samples)        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│                    MODELING                                 │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Step 5: TRAIN MODEL                                        │
│  • script: 05_train_model.py                                │
│  • Algorithm: Random Forest Regression                      │
│  • Features: NDVI, road_density, building_density, etc.     │
│  • Target: PM2.5 monthly mean                               │
│  • output: models/rf_model.pkl                              │
│                                                             │
│  Step 6: VALIDATE                                           │
│  • script: 06_cross_validate.py                             │
│  • Method: Leave-one-station-out CV                         │
│  • Metrics: R², MAE, RMSE                                   │
│  • output: results/cv_scores.json                           │
│  • Target: R² ≥ 0.40                                        │
│                                                             │
│  Step 7: PREDICT GRID                                       │
│  • script: 07_predict_grid.py                               │
│  • Apply model to all 32,700 grid cells (100m × 100m)       │
│  • Include uncertainty (prediction intervals)               │
│  • output: outputs/predictions_100m.tif                     │
│                                                             │
│  Step 8: RANK INTERVENTIONS                                 │
│  • script: 08_rank_interventions.py                         │
│  • Scenarios: green corridor, traffic calming, green roofs  │
│  • Predict PM2.5 change for each scenario                   │
│  • output: outputs/intervention_ranking.csv                 │
│                                                             │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│                USER INTERFACE                               │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  DASHBOARD (Streamlit web app)                              │
│  • Interactive map: Click location → See PM2.5 prediction   │
│  • Intervention table: Sort by impact                       │
│  • Uncertainty visualization                                │
│  • "Generate Report" button → PDF download                  │
│                                                             │
│  PDF REPORT (for planning committee)                        │
│  • Page 1: Site map + current PM2.5                         │
│  • Page 2: Top 3 interventions + expected reductions        │
│  • Page 3: Model card (limitations)                         │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## File Organization

```
krakow-air-quality/
├── data/
│   ├── raw/                          # Never commit (too big, in .gitignore)
│   │   ├── aqicn/
│   │   │   └── krakow_2019-2024.csv  (~100 MB)
│   │   ├── sentinel2/
│   │   │   └── monthly_ndvi/         (~2 GB)
│   │   └── osm/
│   │       ├── krakow_roads.geojson  (~20 MB)
│   │       └── krakow_buildings.geojson (~80 MB)
│   │
│   ├── processed/                    # Commit small samples only
│   │   ├── aqicn_monthly.csv         (~500 KB)
│   │   ├── features_100m_grid.tif    (~10 MB)
│   │   └── training_data.csv         (~50 KB, 600 rows)
│   │
│   └── samples/                      # <5 MB test data (DO commit)
│       └── krakow_sample_2024-01.csv (~500 KB)
│
├── scripts/
│   ├── 01_download_data.py           # AQICN API + GEE + OSM
│   ├── 02_calculate_features.py      # NDVI, road/building density
│   ├── 03_aggregate_temporal.py      # Hourly → monthly
│   ├── 04_spatial_join.py            # Features at station locations
│   ├── 05_train_model.py             # Random forest
│   ├── 06_cross_validate.py          # LOSO-CV
│   ├── 07_predict_grid.py            # Apply to 100m grid
│   └── 08_rank_interventions.py      # Scenario modeling
│
├── notebooks/
│   └── 01-data-profiling.ipynb       # Explore AQICN data
│
├── models/
│   └── rf_model.pkl                  # Trained model
│
├── results/
│   ├── cv_scores.json                # Cross-validation metrics
│   └── feature_importance.png        # Which features matter most
│
├── outputs/
│   ├── predictions_100m.tif          # Pollution predictions
│   ├── uncertainty_100m.tif          # Prediction intervals
│   ├── intervention_ranking.csv      # Ranked interventions
│   ├── dashboard.py                  # Streamlit app
│   └── generate_pdf.py               # PDF report generator
│
├── docs/
│   ├── problem-brief-v2.md
│   ├── data-source-inventory.md
│   ├── datasheets/
│   ├── data-quality-audit.md
│   ├── data-to-decision-map.md
│   ├── system-sketch-v0.md           # This file
│   └── output-sketch-v0.md
│
├── environment.yml                   # Conda environment
├── requirements.txt                  # Pip packages
└── README.md
```

---

## Key Technologies

| Component | Tool | Why |
|---|---|---|
| Language | Python 3.10+ | Standard for data science |
| Geospatial | GeoPandas, Rasterio | Handle shapefiles + rasters |
| Satellite | Google Earth Engine (Python API) | Access Sentinel-2 |
| Machine learning | scikit-learn | Random forest, cross-validation |
| Visualization | Matplotlib, Folium | Maps + plots |
| Dashboard | Streamlit | Quick web app, no frontend coding |
| Environment | Conda | Reproducible dependencies |

---

## Pipeline Runtime Estimates

Running on a typical laptop (8 GB RAM, no GPU):

| Step | Time | Can parallelize? |
|---|---|---|
| 1. Download AQICN | 30 min | No (API rate limits) |
| 1. Download Sentinel-2 | 1-2 hours | Partially (GEE queues) |
| 1. Download OSM | 5 min | No |
| 2. Calculate features | 15 min | Yes (per band) |
| 3. Aggregate temporal | 2 min | No |
| 4. Spatial join | 1 min | No |
| 5. Train model | 5 min | Yes (Random Forest n_jobs=-1) |
| 6. Cross-validate | 50 min → 10 min | Yes (parallel folds) |
| 7. Predict grid | 3 min | No |
| 8. Rank interventions | 10 min | Yes (per scenario) |
| **TOTAL** | **3-4 hours** | (with parallelization) |

**Reproducibility target:** <30 minutes (per success criteria)

**How we'll hit that:**
- Cache intermediate results (don't re-download every time)
- Pre-process data once, commit small samples to repo
- User only runs steps 5-8 (modeling) on first run
- Subsequent runs use cached model: <5 minutes

---

## Data Flow Details

### Step 1-2: Feature Extraction

For each 100m grid cell in Krakow (32,700 cells total):

```python
# Sentinel-2
ndvi = (NIR - Red) / (NIR + Red)  # B8, B4
ndbi = (SWIR - NIR) / (SWIR + NIR)  # B11, B8

# OpenStreetMap
road_density_100m = total_road_length_km / cell_area_km2
road_density_500m = total_road_length_km / (0.785 km2)  # 500m radius
building_density = building_footprint_area / cell_area
distance_to_major_road = euclidean_distance(cell, nearest_highway)

# Result: 7-band raster, 100m resolution
features = [ndvi, ndbi, road_density_100m, road_density_500m, 
            building_density, distance_to_major_road, land_cover_type]
```

### Step 4: Spatial Join

For each of 10 AQICN stations × 60 months (2019-2024):

```python
# Get station location
lat, lon = station_coordinates

# Extract features at that location
features_at_station = features_100m_grid[lat, lon]

# Get PM2.5 for that month
pm25 = aqicn_monthly[station_id, year_month]

# Create training row
training_data.append({
    'station_id': station_id,
    'year_month': year_month,
    'pm25': pm25,
    'ndvi': features_at_station['ndvi'],
    'road_density': features_at_station['road_density_500m'],
    # ... etc
})
```

Result: ~600 rows (10 stations × 60 months, minus missing data)

### Step 5-6: Model Training + Validation

```python
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import LeaveOneGroupOut

# Features (X) and target (y)
X = training_data[['ndvi', 'road_density', 'building_density', ...]]
y = training_data['pm25']
groups = training_data['station_id']  # For LOSO-CV

# Train
model = RandomForestRegressor(n_estimators=500, max_depth=10)
model.fit(X, y)

# Cross-validate (leave-one-station-out)
cv = LeaveOneGroupOut()
scores = []
for train_idx, test_idx in cv.split(X, y, groups):
    model.fit(X[train_idx], y[train_idx])
    score = model.score(X[test_idx], y[test_idx])  # R²
    scores.append(score)

print(f"Mean R²: {np.mean(scores):.2f}")  # Target: ≥0.40
```

### Step 7: Grid Predictions

```python
# Apply model to all 32,700 cells
predictions = model.predict(features_100m_grid)

# Reshape to grid
predictions_grid = predictions.reshape(327, 100)  # Adjust to actual Krakow bbox

# Export as GeoTIFF
rasterio.write('outputs/predictions_100m.tif', predictions_grid)
```

---

## Error Handling

**If AQICN API goes down:**
```python
try:
    data = requests.get(aqicn_url)
except:
    # Fallback to cached data
    data = pd.read_csv('data/samples/krakow_sample.csv')
    warnings.warn("Using cached sample data, not live")
```

**If Sentinel-2 download fails:**
```python
# GEE exports to Google Drive
# If export fails, check GEE tasks page
# Manual download fallback available
```

**If model R² < 0.40:**
```python
if r2_score < 0.40:
    print("Model doesn't meet target. Trying:")
    print("1. Feature engineering (add interaction terms)")
    print("2. Hyperparameter tuning")
    print("3. Try different algorithm (XGBoost)")
    # Continue with best available model but flag low confidence
```

---

## Deployment Plan

**Phase 1 (MVP - Session 3):**
- Scripts run locally on team laptops
- Manual execution (python script.py)
- Outputs saved to files
- No web deployment yet

**Phase 2 (Future work):**
- Containerize with Docker
- Deploy dashboard on Streamlit Cloud (free tier)
- Automated monthly updates (GitHub Actions cron job)
- Public URL: krakow-air-quality.streamlit.app

---

## Security & Privacy

**What data we collect:**
- None. We query public APIs and public satellites.

**What data we store:**
- Aggregated pollution measurements (already public)
- Satellite imagery (already public)
- Model predictions (derived data, not personal)

**What we share:**
- Everything. All outputs are open.

**No privacy concerns:** No personal data, no tracking, no user accounts.

---

## Next Steps (Session 3)

**Rim:**
- Implement scripts 01-03 (download + feature extraction)
- Test AQICN API with rate limiting
- Verify GEE access working

**Martina:**
- Implement script 04 (spatial join)
- Validate coordinate systems match (EPSG:4326 vs EPSG:32634)
- Create feature visualization plots

**Rashi:**
- Implement scripts 05-06 (model + validation)
- Experiment with hyperparameters if R² < 0.40
- Generate feature importance chart

**Bhavana:**
- Implement scripts 07-08 (predictions + interventions)
- Sketch dashboard UI (Streamlit mockup)
- Draft PDF report template

**First integration point:** End of Step 4, we should have training_data.csv ready for modeling.

**Success check:** If NDVI vs PM2.5 scatter plot shows negative correlation (more green = less pollution), we're on track. If not, rethink features.
