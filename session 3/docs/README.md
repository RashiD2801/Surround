# Session 3 Templates — Data Preparation (CRISP-DM Phase 3)
# Krakow Air Quality & Urban Form

Drop these into your team repo at the start of Session 3. By 4 PM today,
every file should be filled in and committed.

> **The frame for today:** cleaning is not janitor work. Every transformation
> is a design decision with downstream consequences. Document them as
> rigorously as you'd document a wall section.

---

## Where to put them in your repo

```
your-repo/
├── docs/
│   ├── problem-brief.md                (S1)
│   ├── problem-brief-v2.md             (S2)
│   ├── data-source-inventory.md        (S2)
│   ├── datasheets/aqicn-pm25.md        (S2 — UPDATE section 4 today)
│   ├── datasheets/sentinel2-imagery.md (S2 — UPDATE section 4 today)
│   ├── datasheets/copernicus-urban-atlas.md (S2 — UPDATE section 4 today)
│   ├── data-quality-audit.md           (S2)
│   ├── data-to-decision-map.md         (S2)
│   ├── system-sketch-v0.md             (S2)
│   ├── output-sketch-v0.md             (S2)
│   ├── data-cleaning-log.md            (NEW — every transform justified)
│   └── pipeline-architecture-v1.md     (NEW — system sketch evolved)
├── notebooks/
│   ├── 01-data-profiling.ipynb         (S2 — RE-RUN on cleaned data today)
│   └── 02-data-cleaning.ipynb          (NEW — exploratory cleaning)
├── src/
│   └── clean_data.py                   (NEW — promoted module)
├── data/
│   ├── raw/
│   │   └── aqicn/                      (gitignored — don't commit large files)
│   └── processed/
│       ├── aqicn_monthly.csv           (NEW — cleaned + aggregated PM2.5)
│       └── training_data.csv           (NEW — features joined to station monthly data)
└── requirements.txt                    (UPDATE — pin actual versions used)
```

---

## The 9 artifacts you owe by 4 PM

| # | File | Why it exists |
|---|---|---|
| 1 | `notebooks/02-data-cleaning.ipynb` | Exploratory AQICN + feature cleaning — raw → processed, with thinking visible |
| 2 | `src/clean_data.py` | The **promoted module** — AQICN cleaning logic lifted into named, typed, testable functions |
| 3 | `data/processed/aqicn_monthly.csv` | The **deterministic output** — monthly PM2.5 per station, cleaned and ready for model training |
| 4 | `docs/data-cleaning-log.md` | Every transformation with a justification (the design diary) |
| 5 | `datasheets/aqicn-pm25.md` | Section 4 "Preprocessing & cleaning" filled with what *you* did (clip negatives, drop flatlines, COVID exclusion, monthly aggregation) |
| 6 | `notebooks/01-data-profiling.ipynb` | **Re-run on cleaned data** — confirms fixes landed; shows raw vs cleaned |
| 7 | ≥1 documented function | Docstring + types + ≥1 assertion (defensive programming) |
| 8 | `requirements.txt` | Pinned versions actually used (not `pandas` — `pandas==2.2.3`) |
| 9 | `docs/pipeline-architecture-v1.md` | System sketch evolved with **real boxes** now that cleaning is real code |

---

## The frame — cleaning is design

You'd never accept a wall section that said "concrete, somehow." You'd
demand: which mix, what depth, why this and not the alternative. Same
applies to data.

For every transformation in your pipeline, you should be able to answer:

1. **What did this transform change?**
2. **Why this transform and not the alternative?**
3. **What downstream effect does it have?**
4. **What does it preserve from raw — i.e. is it reversible?**

If you can't answer all four, the transform is undocumented. The cleaning
log is where you answer them.

---

## The phase 3 spine — five tasks (applied to this project)

1. **Select** — which stations, which time window (2019–2024 excluding COVID). Filter to Krakow stations only. Every filter has a reason; every reason gets logged.
2. **Clean** — clip negative PM2.5, drop flatline sensor periods, fix station coordinates, standardize UTC timestamps. Reversibility matters: keep raw column, derive cleaned.
3. **Construct** — aggregate hourly → monthly means per station. Derive `pm25_completeness` per station-month. Compute feature buffer aggregations (NDVI, road density, building density within 500m radius of each station).
4. **Integrate** — join monthly AQICN data with spatial features extracted at station locations. Keys: `station_id` + `year_month`. Assert row count preserved.
5. **Format** — final schema for `data/processed/training_data.csv`. Document column units. Write parquet for large rasters.

---

## What Session 3 does NOT do

- ✗ Train any model (Phase 4 / Session 4)
- ✗ Compute model metrics or cross-validation (Phase 4 / Session 4)
- ✗ Synthetic data generation (Phase 5 / Session 5)
- ✗ Stress-test or build a failure gallery (Phase 6 / Session 6)
- ✗ Build the Streamlit dashboard (Phase 7 / Session 7)

Cleaning ends when raw → clean is reproducible from one command and the
result has been re-profiled. Not before.

---

## The pre-commit ritual (every team, by 3:55 PM)

1. **Restart kernel** in `02-data-cleaning.ipynb`.
2. **Run all** — confirm no errors.
3. **Run** `python src/clean_data.py` — confirm `data/processed/aqicn_monthly.csv` regenerates identically.
4. **Confirm** output matches what the notebook produced (use `pd.testing.assert_frame_equal`).
5. **Re-run** `01-data-profiling.ipynb` on the cleaned output — confirm negative values gone, flatlines gone, COVID gap excluded.
6. `git log --oneline` — show the commits since 1:00 PM.
7. Push.

---

## Reading order — fill the templates in this order

1. **`02-data-cleaning-scaffold.md`** — copy structure into your notebook, start cleaning AQICN data
2. **`function-design-checklist.md`** — read before promoting any code into `src/clean_data.py`
3. **`clean-data-module.md`** — copy as the skeleton of `src/clean_data.py`
4. **`data-cleaning-log.md`** — log every transform as you make it (don't batch this at the end)
5. **`reproducibility-checklist.md`** — work through before committing
6. **`pipeline-architecture-v1.md`** — fill once your cleaning is stable
