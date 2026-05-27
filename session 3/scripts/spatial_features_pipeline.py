"""
Krakow Spatial Features Pipeline — All 8 Stations
===================================================
Extracts land use (CLMS Urban Atlas) and OSM (buildings + roads)
features for each of the 8 monitoring stations, then merges them
with the cleaned air quality dataset.

This is a refactored version of krakow_pipeline.py that:
  - Loops over all 8 stations instead of hardcoding one
  - Produces a spatial features lookup table (one row per station)
  - Merges with krakow_multistation_CLEANED.csv on station_id

Inputs:
    krakow_multistation_CLEANED.csv          (from clean_multistation.py)
    CLMS_UA_LCU_...KRAKOW...fgb              (Urban Atlas land use file)

Outputs:
    krakow_spatial_features.csv              (one row per station, 8 rows)
    krakow_final_dataset.csv                 (merged ML-ready dataset)

Run:
    python spatial_features_pipeline.py
"""

import geopandas as gpd
import pandas as pd
import numpy as np
import pyproj
from pathlib import Path
from shapely.geometry import Point

# =============================================================================
# CONFIGURATION — edit paths here
# =============================================================================

# Resolve all paths relative to THIS script's own folder, not wherever
# PowerShell happens to be running from. All files just need to be in
# the same folder as this script.
HERE = Path(__file__).parent.resolve()

# Input: your cleaned multistation air quality CSV
AQ_CSV = str(HERE.parent / "data" / "processed" / "krakow_multistation_CLEANED.csv")

# Input: CLMS Urban Atlas land use .fgb file (stays in session 3 root)
FGB_PATH = str(HERE.parent / "CLMS_UA_LCU_S2021_V025ha_PL003L2_KRAKOW_03035_V01_R00_20241025.fgb")

# Outputs
SPATIAL_FEATURES_OUT = str(HERE.parent / "data" / "output" / "krakow_spatial_features.csv")
FINAL_DATASET_OUT    = str(HERE.parent / "data" / "output" / "krakow_final_dataset.csv")

# Buffer radii for land-use aggregation (kilometres)
RADII_KM = [0.5, 1.0, 2.0, 5.0]

# OSM buffer radii (smaller — fetching takes time)
OSM_RADII_KM = [0.5, 1.0, 2.0]

# Set False to skip OSM (faster, offline-safe — land use features only)
FETCH_OSM = True

# =============================================================================
# STATION REGISTRY
# Must match station_id values in krakow_multistation_CLEANED.csv
# =============================================================================

STATIONS = [
    {"station_id": "nowa_huta",         "station_name": "Nowa Huta",          "lat": 50.0683, "lon": 20.0530},
    {"station_id": "kurdwanow",          "station_name": "Kurdwanow",          "lat": 50.0076, "lon": 19.9742},
    {"station_id": "zloty_rog",          "station_name": "Zloty Rog",          "lat": 50.0647, "lon": 19.9450},
    {"station_id": "telimeny",           "station_name": "Ul. Telimeny",       "lat": 50.0094, "lon": 19.9617},
    {"station_id": "os_wadow",           "station_name": "Os. Wadow",          "lat": 50.0783, "lon": 19.8950},
    {"station_id": "os_piastow",         "station_name": "Os. Piastow",        "lat": 50.0519, "lon": 19.8850},
    {"station_id": "ul_dietla",          "station_name": "Ul. Dietla",         "lat": 50.0566, "lon": 19.9442},
    {"station_id": "aleja_krasinskiego", "station_name": "Aleja Krasinskiego", "lat": 50.0573, "lon": 19.9100},
]

# =============================================================================
# COORDINATE HELPERS
# =============================================================================

to_3035 = pyproj.Transformer.from_crs("EPSG:4326", "EPSG:3035", always_xy=True)

def latlon_to_3035(lat, lon):
    """Convert WGS84 lat/lon to EPSG:3035 projected point."""
    x, y = to_3035.transform(lon, lat)
    return Point(x, y), x, y

# =============================================================================
# LAND USE CATEGORY HELPERS (from krakow_pipeline.py — unchanged)
# =============================================================================

def categorize_code(code):
    """Map CLMS Urban Atlas 5-digit code to broad category."""
    c = str(code)
    if c.startswith("111"): return "urban_continuous"
    if c.startswith("112"): return "urban_discontinuous"
    if c.startswith("113"): return "urban_isolated"
    if c.startswith("12"):  return "urban_industrial"
    if c.startswith("13"):  return "urban_infrastructure"
    if c.startswith("14"):  return "urban_green"
    if c.startswith("2"):   return "agriculture"
    if c.startswith("3"):   return "forest_natural"
    if c.startswith("4"):   return "wetland"
    if c.startswith("5"):   return "water"
    return "other"

SEAL_DENSITY = {
    "11100": 1.00, "11210": 0.65, "11220": 0.40,
    "11230": 0.20, "11240": 0.05, "11300": 0.30,
}

LAND_USE_CATS = [
    "urban_continuous", "urban_discontinuous", "urban_isolated",
    "urban_industrial", "urban_infrastructure", "urban_green",
    "agriculture", "forest_natural", "wetland", "water",
]

# =============================================================================
# STEP 1 — LAND USE FEATURES (per station)
# =============================================================================

def load_fgb_around_station(fgb_path, sx, sy, max_r_m):
    """
    Load Urban Atlas FGB clipped to a bounding box around the station.
    Returns a GeoDataFrame in EPSG:3035.
    """
    gdf = gpd.read_file(
        fgb_path,
        bbox=(sx - max_r_m, sy - max_r_m, sx + max_r_m, sy + max_r_m)
    )
    gdf = gdf.to_crs("EPSG:3035")
    gdf["category"]     = gdf["code_2021"].apply(categorize_code)
    gdf["seal_density"] = gdf["code_2021"].astype(str).map(SEAL_DENSITY).fillna(0)
    return gdf


def compute_landuse_features_for_station(station, gdf):
    """
    Compute land use percentage features at all buffer radii for one station.
    Returns a flat dict of features (one row worth of data).
    """
    pt, sx, sy = latlon_to_3035(station["lat"], station["lon"])
    features = {"station_id": station["station_id"]}

    for r_km in RADII_KM:
        r_m    = r_km * 1000
        prefix = f"luse_r{int(r_km * 10):03d}_"
        buf    = pt.buffer(r_m)
        circle_area = buf.area

        clipped = gdf.copy()
        clipped["geometry"] = gdf.geometry.intersection(buf)
        clipped = clipped[~clipped.geometry.is_empty].copy()
        clipped["clip_area"] = clipped.geometry.area

        # Individual category percentages
        for cat in LAND_USE_CATS:
            area = clipped.loc[clipped["category"] == cat, "clip_area"].sum()
            features[f"{prefix}{cat}_pct"] = area / circle_area

        # Composite: sealing density (weighted average)
        features[f"{prefix}seal_density"] = (
            (clipped["seal_density"] * clipped["clip_area"]).sum() / circle_area
        )

        # Composite: green cover (urban_green + forest + agriculture)
        green_cats = ["urban_green", "forest_natural", "agriculture"]
        features[f"{prefix}green_pct"] = (
            clipped.loc[clipped["category"].isin(green_cats), "clip_area"].sum() / circle_area
        )

        # Composite: total urban cover
        urban_cats = ["urban_continuous", "urban_discontinuous", "urban_isolated",
                      "urban_industrial", "urban_infrastructure", "urban_green"]
        features[f"{prefix}urban_pct"] = (
            clipped.loc[clipped["category"].isin(urban_cats), "clip_area"].sum() / circle_area
        )

    return features


def compute_all_landuse_features(fgb_path):
    """
    Loop over all 8 stations and compute land use features for each.
    Returns a DataFrame with one row per station.
    """
    print("\n" + "="*80)
    print("STEP 1: LAND USE FEATURES (CLMS Urban Atlas)")
    print("="*80)

    if not Path(fgb_path).exists():
        print(f"  ERROR: FGB file not found at: {fgb_path}")
        print("  Skipping land use features.")
        return pd.DataFrame([{"station_id": s["station_id"]} for s in STATIONS])

    all_features = []

    for station in STATIONS:
        print(f"\n  Processing: {station['station_name']} "
              f"(lat={station['lat']}, lon={station['lon']})")

        try:
            pt, sx, sy = latlon_to_3035(station["lat"], station["lon"])
            max_r_m = max(RADII_KM) * 1000

            # Load FGB clipped to this station's max buffer
            gdf = load_fgb_around_station(fgb_path, sx, sy, max_r_m)
            print(f"    Loaded {len(gdf)} land use patches")

            features = compute_landuse_features_for_station(station, gdf)

            # Print summary for key radii
            for r_km in [0.5, 2.0]:
                prefix = f"luse_r{int(r_km * 10):03d}_"
                print(f"    r={r_km}km: "
                      f"green={features.get(f'{prefix}green_pct', 0):.1%}, "
                      f"urban={features.get(f'{prefix}urban_pct', 0):.1%}, "
                      f"seal={features.get(f'{prefix}seal_density', 0):.2f}")

            all_features.append(features)

        except Exception as e:
            print(f"    ERROR for {station['station_name']}: {e}")
            # Add a row with NaNs so the station still appears in output
            all_features.append({"station_id": station["station_id"]})

    df_features = pd.DataFrame(all_features)
    print(f"\n  Land use features computed: {df_features.shape[1] - 1} features per station")
    return df_features


# =============================================================================
# STEP 2 — OSM BUILDING & ROAD FEATURES (per station)
# =============================================================================

def osm_fetch_with_retry(fetch_fn, max_retries=3, wait_seconds=10):
    """Retry an OSM fetch up to max_retries times on network errors."""
    import time
    for attempt in range(1, max_retries + 1):
        try:
            return fetch_fn()
        except Exception as e:
            if attempt < max_retries:
                print(f"      Attempt {attempt} failed ({e}). Retrying in {wait_seconds}s...")
                time.sleep(wait_seconds)
            else:
                raise


# Alternative Overpass servers to try if the default one is blocked
# osmnx will try them in order
OVERPASS_ENDPOINTS = [
    "https://overpass-api.de/api/interpreter",
    "https://maps.mail.ru/osm/tools/overpass/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
]

def configure_osmnx():
    """Point osmnx to the first reachable Overpass server."""
    import osmnx as ox
    import urllib.request
    for endpoint in OVERPASS_ENDPOINTS:
        try:
            urllib.request.urlopen(endpoint, timeout=5)
            ox.settings.overpass_url = endpoint
            print(f"  Using Overpass server: {endpoint}")
            return True
        except Exception:
            print(f"  Server unreachable: {endpoint}")
    print("  WARNING: No Overpass server reachable. OSM features will be NaN.")
    return False


def compute_osm_features_for_station(station):
    """
    Fetch OSM buildings and road network for one station.
    Retries up to 3 times on SSL/network errors.
    Returns a flat dict of features.
    """
    try:
        import osmnx as ox
    except ImportError:
        print("  osmnx not installed — run: pip install osmnx")
        return {"station_id": station["station_id"]}

    features = {"station_id": station["station_id"]}
    pt, sx, sy = latlon_to_3035(station["lat"], station["lon"])

    for r_km in OSM_RADII_KM:
        r_m             = r_km * 1000
        prefix          = f"osm_r{int(r_km * 10):03d}_"
        circle_area_km2 = np.pi * r_km ** 2
        buf             = pt.buffer(r_m)

        # ── Buildings ──
        try:
            def fetch_buildings():
                return ox.features_from_point(
                    (station["lat"], station["lon"]),
                    tags={"building": True},
                    dist=r_m
                )
            bldgs = osm_fetch_with_retry(fetch_buildings)
            bldgs = bldgs[bldgs.geometry.geom_type.isin(["Polygon", "MultiPolygon"])]
            bldgs_proj = bldgs.to_crs("EPSG:3035")
            bldgs_proj["clip_area"] = bldgs_proj.geometry.intersection(buf).area
            total_bldg_area = bldgs_proj["clip_area"].sum()
            features[f"{prefix}building_coverage"]      = total_bldg_area / buf.area
            features[f"{prefix}building_count_per_km2"] = len(bldgs) / circle_area_km2
            print(f"      r={r_km}km buildings: {len(bldgs)}, "
                  f"coverage={features[f'{prefix}building_coverage']:.1%}")
        except Exception as e:
            print(f"      r={r_km}km buildings FAILED after retries: {e}")
            features[f"{prefix}building_coverage"]      = np.nan
            features[f"{prefix}building_count_per_km2"] = np.nan

        # ── Roads ──
        try:
            def fetch_roads():
                return ox.graph_from_point(
                    (station["lat"], station["lon"]),
                    dist=r_m,
                    network_type="drive"
                )
            G = osm_fetch_with_retry(fetch_roads)
            _, edges = ox.graph_to_gdfs(G)
            edges_proj = edges.to_crs("EPSG:3035")
            edges_proj["clip_length"] = edges_proj.geometry.intersection(buf).length
            total_road_len_km = edges_proj["clip_length"].sum() / 1000
            features[f"{prefix}road_density_km_per_km2"] = total_road_len_km / circle_area_km2
            print(f"      r={r_km}km road density: "
                  f"{features[f'{prefix}road_density_km_per_km2']:.1f} km/km2")
        except Exception as e:
            print(f"      r={r_km}km roads FAILED after retries: {e}")
            features[f"{prefix}road_density_km_per_km2"] = np.nan

    return features


def compute_all_osm_features():
    """
    Loop over all 8 stations and compute OSM features.
    Returns a DataFrame with one row per station.
    """
    print("\n" + "="*80)
    print("STEP 2: OSM BUILDING & ROAD FEATURES")
    print("="*80)

    # Find a working Overpass server before starting
    server_ok = configure_osmnx()
    if not server_ok:
        print("  Skipping OSM — no server reachable. Re-run later or use FETCH_OSM=False.")
        return pd.DataFrame([{"station_id": s["station_id"]} for s in STATIONS])

    all_features = []

    for station in STATIONS:
        print(f"\n  Processing: {station['station_name']}")
        try:
            features = compute_osm_features_for_station(station)
            all_features.append(features)
        except Exception as e:
            print(f"    ERROR for {station['station_name']}: {e}")
            all_features.append({"station_id": station["station_id"]})

    df_features = pd.DataFrame(all_features)
    n_osm_cols = df_features.shape[1] - 1
    print(f"\n  OSM features computed: {n_osm_cols} features per station")
    return df_features


# =============================================================================
# STEP 3 — MERGE SPATIAL FEATURES WITH AIR QUALITY DATA
# =============================================================================

def merge_with_air_quality(df_spatial, aq_csv_path):
    """
    Merge the spatial features table (8 rows x N features)
    with the air quality time series (many rows x M columns)
    on station_id.

    Since spatial features are STATIC (land use doesn't change daily),
    each station row is broadcast to all time rows for that station.
    """
    print("\n" + "="*80)
    print("STEP 3: MERGE SPATIAL + AIR QUALITY DATA")
    print("="*80)

    if not Path(aq_csv_path).exists():
        print(f"  ERROR: Air quality CSV not found at: {aq_csv_path}")
        print("  Run clean_multistation.py first.")
        return None

    df_aq = pd.read_csv(aq_csv_path)
    print(f"  Air quality data loaded: {df_aq.shape}")
    print(f"  Spatial features loaded: {df_spatial.shape}")
    print(f"  Stations in AQ data:      {sorted(df_aq['station_id'].unique())}")
    print(f"  Stations in spatial data: {sorted(df_spatial['station_id'].unique())}")

    # Check all stations are present in both
    aq_stations = set(df_aq["station_id"].unique())
    sp_stations = set(df_spatial["station_id"].unique())
    missing_in_spatial = aq_stations - sp_stations
    if missing_in_spatial:
        print(f"  WARNING: These stations are in AQ but missing spatial features: "
              f"{missing_in_spatial}")

    # Merge: each station's spatial features broadcast to all its time rows
    df_merged = df_aq.merge(df_spatial, on="station_id", how="left")

    # Check merge quality
    spatial_cols = [c for c in df_spatial.columns if c != "station_id"]
    missing_after_merge = df_merged[spatial_cols[0]].isna().sum() if spatial_cols else 0
    pct_missing = missing_after_merge / len(df_merged) * 100

    print(f"\n  Merged shape: {df_merged.shape}")
    print(f"  Rows with spatial features: "
          f"{len(df_merged) - missing_after_merge:,} ({100 - pct_missing:.1f}%)")

    if missing_after_merge > 0:
        missing_stations = df_merged[df_merged[spatial_cols[0]].isna()]["station_id"].unique()
        print(f"  Stations without spatial features: {missing_stations}")

    return df_merged


# =============================================================================
# MAIN
# =============================================================================

def main():
    print("\n" + "="*80)
    print("KRAKOW SPATIAL FEATURES PIPELINE")
    print("="*80)
    print(f"  Air quality input:  {AQ_CSV}")
    print(f"  Land use file:      {FGB_PATH}")
    print(f"  Fetch OSM:          {FETCH_OSM}")
    print(f"  Output (spatial):   {SPATIAL_FEATURES_OUT}")
    print(f"  Output (final):     {FINAL_DATASET_OUT}")

    # ── STEP 1: Land use features ──────────────────────────────────────────
    df_landuse = compute_all_landuse_features(FGB_PATH)

    # ── STEP 2: OSM features ───────────────────────────────────────────────
    if FETCH_OSM:
        df_osm = compute_all_osm_features()
        # Merge land use + OSM into one spatial features table
        df_spatial = df_landuse.merge(df_osm, on="station_id", how="left")
    else:
        print("\n  OSM skipped (FETCH_OSM=False)")
        df_spatial = df_landuse

    # Save the spatial features table (useful for inspection/debugging)
    df_spatial.to_csv(SPATIAL_FEATURES_OUT, index=False)
    print(f"\n  Saved spatial features: {SPATIAL_FEATURES_OUT}")
    print(f"  Shape: {df_spatial.shape}  (one row per station)")

    # Print summary table
    print("\n  SPATIAL FEATURES SUMMARY (green_pct at 1km radius):")
    print(f"  {'Station':25s} | {'green_1km':>9} | {'urban_1km':>9} | {'seal_1km':>8}")
    print(f"  {'-'*60}")
    for station in STATIONS:
        sid = station["station_id"]
        row = df_spatial[df_spatial["station_id"] == sid]
        if len(row) == 0:
            continue
        green = row["luse_r010_green_pct"].values[0] if "luse_r010_green_pct" in row.columns else float("nan")
        urban = row["luse_r010_urban_pct"].values[0] if "luse_r010_urban_pct" in row.columns else float("nan")
        seal  = row["luse_r010_seal_density"].values[0] if "luse_r010_seal_density" in row.columns else float("nan")
        print(f"  {station['station_name']:25s} | {green:>8.1%} | {urban:>8.1%} | {seal:>8.2f}")

    # ── STEP 3: Merge with air quality data ────────────────────────────────
    df_final = merge_with_air_quality(df_spatial, AQ_CSV)

    if df_final is None:
        print("\n  ERROR: Merge failed. Check that krakow_multistation_CLEANED.csv exists.")
        return

    # Save final merged dataset
    df_final.to_csv(FINAL_DATASET_OUT, index=False)
    print(f"\n  Saved final dataset: {FINAL_DATASET_OUT}")
    print(f"  Final shape: {df_final.shape}")

    # Column summary
    aq_cols      = [c for c in df_final.columns if c in pd.read_csv(AQ_CSV).columns]
    landuse_cols = [c for c in df_final.columns if c.startswith("luse_")]
    osm_cols     = [c for c in df_final.columns if c.startswith("osm_")]

    print(f"\n  COLUMN BREAKDOWN:")
    print(f"    Air quality + temporal:  {len(aq_cols):>3} columns")
    print(f"    Land use features:       {len(landuse_cols):>3} columns")
    print(f"    OSM features:            {len(osm_cols):>3} columns")
    print(f"    Total:                   {df_final.shape[1]:>3} columns")

    print(f"\n{'='*80}")
    print("DONE — your final ML dataset is ready.")
    print(f"{'='*80}")
    print(f"  Use '{FINAL_DATASET_OUT}' for model training.")
    print(f"  Next step: leave-one-station-out cross-validation (target R2 >= 0.40)")


if __name__ == "__main__":
    main()