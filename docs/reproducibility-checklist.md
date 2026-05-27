# Reproducibility Checklist
# Krakow Air Quality & Urban Form — Session 3

> Before you call cleaning "done", run through this checklist.
> If any item fails, the cleaning is not done.

---

## The bar

**Reproducibility means:** a teammate clones your repo on a new machine,
downloads the raw data files, runs the scripts in order, and produces the
same output CSVs — row-for-row.

If that's not true, the cleaning isn't done. It's a sketch of cleaning.

---

## The five disciplines

### 1. Determinism

- [ ] Sort order is deterministic. `clean_multistation.py` sorts by `["station_id", "date"]` before adding lag features.
- [ ] No `datetime.now()` in cleaning logic.
- [ ] The `COVID_START` / `COVID_END` constants in `clean_multistation.py` are hardcoded strings (`"2020-03-15"`, `"2020-05-31"`).
- [ ] The `HIGH_MISSING_THRESHOLD` (0.50) and `EXTREME_THRESHOLD` (200) constants are named — not inline magic numbers.
- [ ] Station registry (`STATIONS` dict in `clean_multistation.py`) is the single source of truth for station IDs, names, and coordinates.

### 2. Pinned dependencies

- [ ] Dependencies for running the pipeline:
  ```
  pandas
  numpy
  geopandas
  pyproj
  shapely
  osmnx
  ```
  Verify versions with `pip freeze` after the pipeline runs cleanly.
- [ ] Python version: 3.10+ recommended (check with `python --version`).
- [ ] On Windows, if `geopandas` fails: `conda install -c conda-forge geopandas osmnx`.

### 3. Path discipline

- [ ] All paths in `clean_multistation.py` are resolved relative to the script's own folder:
  ```python
  HERE        = Path(__file__).parent.resolve()
  RAW_DIR     = HERE.parent / "data" / "raw"
  PROCESSED_DIR = HERE.parent / "data" / "processed"
  ```
- [ ] All paths use `pathlib.Path`, not string concatenation.
- [ ] All paths are **relative to the session 3 folder** — no absolute paths like `C:\Users\...`.
- [ ] Raw data CSVs and the Urban Atlas `.fgb` file are in `.gitignore`. Not committed (too large).

### 4. The "runs from scratch" test

Run these commands in order from the `session 3/` folder:

```powershell
# 1. Install dependencies
pip install pandas numpy geopandas pyproj shapely osmnx

# 2. Place raw data files:
#    - 8 station CSVs in session 3/data/raw/
#    - CLMS Urban Atlas .fgb in session 3/ root

# 3. Step 1 — clean and combine the 8 station CSVs
python scripts/clean_multistation.py
# Expected output: data/processed/krakow_multistation_CLEANED.csv
# Expected shape: ~13,597 rows (or similar), 27+ columns

# 4. Step 2 — extract spatial features and merge
python scripts/spatial_features_pipeline.py
# Expected outputs:
#   data/output/krakow_spatial_features.csv  (8 rows × 53 columns)
#   data/output/krakow_final_dataset.csv     (merged ML-ready dataset)

# 5. Confirm output files exist
ls data/processed/
ls data/output/
```

- [ ] Steps 3–4 complete without errors.
- [ ] `krakow_multistation_CLEANED.csv` has 0 missing PM2.5 values.
- [ ] `krakow_spatial_features.csv` has exactly 8 rows (one per station).
- [ ] `krakow_final_dataset.csv` has the same number of rows as `krakow_multistation_CLEANED.csv`.
- [ ] Total runtime: under 10 minutes (longer if OSM is fetched on slow connection).

### 5. Documentation as artifact

- [ ] `docs/data-cleaning-log.md` has one entry per transform step.
- [ ] `docs/pipeline-architecture-v1.md` shows implemented boxes with actual function names and file paths.
- [ ] `docs/datasheets/aqicn-pm25.md` Team Notes section reflects what was done (8 stations, not 10).
- [ ] `docs/datasheets/copernicus-urban-atlas.md` Team Notes section marked as implemented.
- [ ] `session 3/DATA SOURCES.md` (or `docs/`) explains where to download each raw file.
- [ ] Station registry in `clean_multistation.py` matches coordinates documented in audit (2 corrected stations: Aleja Krasińskiego, Ul. Dietla).

---

## The pre-commit ritual

Right before you push:

1. **Run** `python scripts/clean_multistation.py` from the `session 3/` folder — no errors.
2. **Run** `python scripts/spatial_features_pipeline.py` — no errors.
3. **Confirm** `krakow_final_dataset.csv` has non-null spatial features for all 8 stations.
4. **Check** `git status` — raw CSVs and `.fgb` file are NOT staged.
5. **Commit** with a message that says what changed and why:
   - Good: `"add COVID exclusion to clean_multistation.py — 390 rows removed"`
   - Bad: `"updates"`, `"cleaning"`, `"wip"`

---

## What NOT to commit

- [ ] Raw AQICN station CSVs (`data/raw/*.csv`) — gitignored.
- [ ] Urban Atlas `.fgb` file (~150 MB) — gitignored.
- [ ] Virtual env (`.venv/`).
- [ ] `__pycache__/`, `.ipynb_checkpoints/`.
- [ ] OSM cache files (`cache/` folder).

If a teammate clones the repo and needs to run from scratch, they follow
`session 3/DATA SOURCES.md` to download the raw files, then run the two scripts above.

---

## When the checklist fails

| Failure | Cause | Fix |
|---|---|---|
| Different row count two runs in a row | Unsorted data before lag features | `sort_values(["station_id", "date"])` before `groupby().shift()` |
| "Module not found" on teammate's machine | Missing package | `pip install geopandas osmnx pyproj shapely` |
| `spatial_features_pipeline.py` crashes — FGB not found | Urban Atlas file not placed in `session 3/` root | Download from Copernicus portal, place in `session 3/` |
| OSM features are all NaN | No Overpass server reachable | Set `FETCH_OSM = False` in `spatial_features_pipeline.py` and re-run |
| COVID months appear in cleaned output | Date filtering issue | Check `COVID_START` / `COVID_END` constants and the date column format |
| Lag features are all NaN | Cold-start rows not dropped | `clean_multistation.py` step 10 drops rows where `pm25_lag7` is NaN |
