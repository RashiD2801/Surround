# Surround

**Correlating urban planning variables with air pollution in Krakow using satellite data and machine learning.**

Surround builds a spatial regression model that predicts monthly mean PM2.5 concentrations across Krakow from urban land use features and ERA5 weather data. The model is designed for planning analysts assessing air quality impact at development sites — providing a predicted monthly PM2.5 value as one input in a green-infrastructure review.

---

## Results

| Metric | Seasonal baseline | Our model (v2) |
|---|---|---|
| Test MAE | 10.24 µg/m³ | **6.48 µg/m³** |
| Test R² | — | **0.850** |
| Improvement over seasonal | — | **36.7%** |

Validated on two held-out stations (Nowa Huta + Złoty Róg, 138 station-months) never seen during training or hyperparameter selection.

**Key finding:** When ERA5 weather is controlled for, urban land use features contribute 2.3% of predictive signal. The model is a weather-integrated PM2.5 predictor — ERA5 temperature and boundary layer height carry 96.3% of the signal. Correlations between urban form and PM2.5 require more spatially diverse station data to test robustly.

---

## How It Works

1. **Data collection** — Monthly PM2.5 means from 7 GIOŚ monitoring stations (2019–2024, COVID window excluded). Urban land use coverage (Urban Atlas 2018) computed at 500m radius per station. ERA5-Land monthly temperature and boundary layer height from Open-Meteo historical API.

2. **Feature engineering** — Land use percentages (residential, commercial, industrial, green, road density) combined with weather controls into a station-month feature matrix (`data/output/krakow_spatial_features.csv`).

3. **Modelling** — Random Forest Regressor (scikit-learn, 300 trees) trained on a leave-one-station-out group split to prevent data leakage across stations. Model artifact: `models/baseline.joblib`.

4. **Evaluation** — Performance measured against a seasonal-mean baseline. Uncertainty estimated via 90% tree-quantile intervals. Disaggregated by season, station type, and district.

5. **Interface** — Lightweight HTML dashboard (`interface/index.html`) overlays predicted PM2.5 values on a Krakow city grid with confidence zones.

---

## Project Structure

```
Surround/
├── data/
│   ├── raw/                  # GIOŚ PM2.5 station CSVs (7 stations, 2019–2024)
│   ├── processed/            # Cleaned train / val / test splits
│   ├── output/               # Spatial features + final merged dataset
│   └── training/             # ERA5 monthly weather + model-ready dataset
├── docs/
│   ├── datasheets/           # Source documentation (AQICN, Sentinel-2, Copernicus)
│   ├── model-cards/          # Model card (Mitchell et al. 2019 format)
│   └── session */            # Per-session logs, pipeline architecture, notebooks
├── interface/                # HTML prediction dashboard
├── models/
│   └── baseline.joblib       # Trained Random Forest pipeline
├── notebooks/
│   ├── 02-data-cleaning.ipynb
│   └── 03-modelling.ipynb
└── src/
    ├── clean_data.py          # Data cleaning pipeline
    ├── split_data.py          # LOSO group split
    └── baseline_model.py      # Model training + evaluation
```

---

## Setup

**Prerequisites:** Python 3.10+

```bash
git clone https://github.com/RashiD2801/Surround.git
cd Surround

python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS / Linux

pip install -r requirements.txt
```

### Run the pipeline

```bash
# 1. Clean and split data
python src/clean_data.py
python src/split_data.py

# 2. Train model and evaluate
python src/baseline_model.py
```

### Open the dashboard

Open `interface/index.html` in a browser. Predictions are loaded from `interface/predictions.json`.

---

## Data Sources

| Source | What it provides | License |
|---|---|---|
| GIOŚ / AQICN | PM2.5 daily measurements, 7 Krakow stations, 2019–2024 | Open (indicative quality) |
| Urban Atlas 2018 | Land use polygons at city scale | Copernicus Open Access |
| ERA5-Land via Open-Meteo | Monthly temperature + boundary layer height | CC BY 4.0 |
| Sentinel-2 (GEE) | NDVI summer composite for green cover estimation | Copernicus Open Access |
| OpenStreetMap | Road network density | ODbL |

---

## Tech Stack

| Layer | Technology |
|---|---|
| Modelling | scikit-learn (Random Forest), pandas, NumPy |
| Geospatial | Google Earth Engine, GeoPandas |
| Weather data | Open-Meteo historical API (ERA5-Land) |
| Analysis | Jupyter Notebooks |
| Interface | HTML / JavaScript |

---

## Limitations

- **Correlational, not causal.** The model does not predict the effect of urban interventions (e.g. tree planting). Associations observed at 7 stations are not substitutes for causal study designs.
- **Spatial coverage.** Trained on 7 stations within central Krakow. Predictions >2 km from any training station extrapolate beyond the training regime.
- **Not for regulatory use.** GIOŚ data is indicative quality and cannot substitute for EU Air Quality Directive certified measurements.
- **Uncertainty intervals.** 90% tree-quantile intervals cover 72.5% of test outcomes (target ≥ 85%) — they should not be reported without an explicit disclaimer.

See `docs/model-cards/krakow-pm25-spatial-rf-v1.md` for the full model card.

---

## Team

Built at [IAAC](https://iaac.net/) as part of the Surround data seminar.

| Name | Role |
|---|---|
| Rim Choufani | Data Science |
| Martina Simoni | Data Science |
| Rashi Desadla | Data Science |
| Bhavana | Data Science |
