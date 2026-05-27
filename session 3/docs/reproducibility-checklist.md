# Reproducibility Checklist
# Krakow Air Quality & Urban Form — Session 3

> Before you commit and call cleaning "done", run through this checklist.
> If any item fails, the cleaning is not done.
>
> Use as a working reference; not a committed artifact.

---

## The bar

**Reproducibility means:** a teammate clones your repo on a new machine,
follows your README, and produces the same `aqicn_monthly.csv` you
produced — byte-for-byte (or row-for-row at minimum, since CSV float
formatting can vary by platform).

If that's not true, the cleaning isn't done. It's a sketch of cleaning.

---

## The five disciplines

### 1. Determinism

- [ ] Random seed set in `src/clean_data.py` (`np.random.seed(RANDOM_SEED)`
      at the top of `main()`). Even though this pipeline doesn't currently
      use randomness, seed it anyway — future imputation or augmentation steps will.
- [ ] Sort order is deterministic. After `groupby`, results are sorted by
      `["station_id", "year_month"]` — a stable key. Don't rely on insertion order.
- [ ] No `datetime.now()` or `time.time()` in cleaning logic.
- [ ] The `COVID_EXCLUDE_START` / `COVID_EXCLUDE_END` constants in `src/clean_data.py`
      are hardcoded strings, not computed from `datetime.now() - timedelta(...)`.
- [ ] The `MIN_MONTHLY_COMPLETENESS` threshold is a named constant (0.75),
      not an inline magic number that might drift between notebook and module.

### 2. Pinned dependencies

- [ ] `requirements.txt` pins exact versions:
      ```
      pandas==2.2.3
      numpy==1.26.4
      matplotlib==3.9.0
      geopandas==1.0.1
      pyarrow==16.1.0
      requests==2.32.3
      ```
      Not `pandas` — `pandas==2.2.3`. Generate by running `pip freeze > requirements.txt`
      after your pipeline runs cleanly. Delete dev packages (jupyter, ipykernel, etc.)
      from the requirements list if they're not needed to run `src/clean_data.py`.
- [ ] Python version noted in `README.md` (e.g., "Python 3.11.x" — check with `python --version`).
- [ ] Google Earth Engine authentication method documented (service account vs personal account).
      This step is interactive — document it explicitly so teammates can reproduce.

### 3. Path discipline

- [ ] All paths are constants at the top of `src/clean_data.py`:
      `RAW_PATH = Path("data/raw/aqicn/krakow_pm25_2019_2024.csv")`
      `OUT_PATH = Path("data/processed/aqicn_monthly.csv")`
      Never inline `"data/raw/aqicn/krakow_pm25_2019_2024.csv"` mid-function.
- [ ] All paths use `pathlib.Path`, not `os.path.join` strings.
- [ ] All paths are **relative to the project root**.
      `data/raw/aqicn/x.csv` — yes.
      `/Users/rim/Documents/surround/data/raw/aqicn/x.csv` — NO.
      `../data/raw/aqicn/x.csv` — OK in notebook cells (relative to `notebooks/`), but not in `src/`.
- [ ] The `data/raw/` directory is in `.gitignore`. Raw data (>5 MB) is not committed.
      Teammates must run `scripts/00_download_raw.py` or follow "Get the data" in README.

### 4. The "runs from scratch" test

Open a terminal in the project root and run, in order:

```bash
# 1. Fresh virtual environment
python -m venv .venv
source .venv/bin/activate       # Mac/Linux
# .venv\Scripts\activate        # Windows PowerShell

# 2. Install pinned dependencies
pip install -r requirements.txt

# 3. Confirm raw AQICN data is present
ls data/raw/aqicn/
# Expected: krakow_pm25_2019_2024.csv

# 4. Run the cleaning pipeline
python src/clean_data.py

# 5. Confirm the cleaned output exists
ls -lh data/processed/aqicn_monthly.csv
# Expected: ~40–60 KB, ~600 rows

# 6. Check output is deterministic (run twice, compare)
cp data/processed/aqicn_monthly.csv /tmp/run1.csv
python src/clean_data.py
diff data/processed/aqicn_monthly.csv /tmp/run1.csv
# Expected: no diff (empty output = identical)
```

- [ ] Steps 1–5 complete without error.
- [ ] Step 6 diff is empty (pipeline is deterministic).
- [ ] Total runtime from step 4: under 2 minutes on a standard laptop.
      If it's slower, check whether the Sentinel-2 download is accidentally
      triggered inside `src/clean_data.py` (it should not be — that belongs
      in `notebooks/03-feature-extraction.ipynb`).

### 5. Documentation as artifact

- [ ] `README.md` has a "How to reproduce" section with the exact commands above.
- [ ] `docs/data-cleaning-log.md` has one entry per transform (8 transforms logged).
- [ ] `docs/pipeline-architecture-v1.md` shows every implemented AQICN cleaning
      box with a file path and function name.
- [ ] `datasheets/aqicn-pm25.md` Section 4 "Preprocessing & cleaning" is filled
      with what YOU did (not the generic template text): clip negatives, drop flatlines,
      COVID exclusion, monthly aggregation, coordinate correction.
- [ ] The `COORD_CORRECTIONS` dictionary in `src/clean_data.py` matches the values
      that Martina documented from the WIOŚ portal. Verify by spot-checking:
      `df.loc[df['station_id']=='aleja_krasinskiego', ['lat','lon']].iloc[0]`
      should print `(50.0572, 19.9216)`.

---

## The pre-commit ritual

Right before you push:

1. **Restart kernel** in `02-data-cleaning.ipynb`.
2. **Run all** — every cell runs, no errors.
3. **Run** `python src/clean_data.py` from terminal — no errors.
4. **Confirm** the output of step 2 (notebook) and step 3 (script) produce
   the same CSV:
   ```python
   import pandas as pd
   notebook_out = df_out.reset_index(drop=True)
   script_out   = pd.read_csv("data/processed/aqicn_monthly.csv")
   pd.testing.assert_frame_equal(notebook_out, script_out, check_like=True)
   ```
5. **Re-run** `01-data-profiling.ipynb` on the cleaned data — confirm:
   - `df['pm25'].min() >= 0` (no negatives)
   - Kurdwanów Dec 2022 gap is visible in the temporal plot
   - COVID period (Mar–May 2020) gap is visible
   - Completeness histogram shows all values ≥ 0.75
6. **Inspect** `git status` — only the files you intended to change are staged.
   In particular, check that `data/raw/aqicn/*.csv` is in `.gitignore` and
   is NOT staged.
7. **Commit** with a message that says what changed and why:
   - Good: `"add COVID exclusion to clean_data.py — 18k rows removed"`
   - Bad: `"updates"`, `"cleaning"`, `"wip"`

---

## What NOT to commit

- [ ] Raw AQICN CSV (`data/raw/aqicn/*.csv`) — >50 MB, gitignored.
- [ ] Sentinel-2 GeoTIFF files (`data/raw/sentinel2/*.tif`) — very large.
- [ ] `data/processed/aqicn_monthly.csv` — your call: commit if <10 MB and
      useful as a "freeze point" checkpoint for teammates who can't run the
      AQICN download; otherwise gitignore and document how to regenerate.
- [ ] Virtual env (`.venv/`).
- [ ] `__pycache__/`, `.ipynb_checkpoints/`.
- [ ] `data/raw/aqicn/` API token file or `.env` with AQICN_TOKEN.

If a teammate clones the repo and can't get the raw AQICN data, your README
needs a "Get the data" section:
```
## Get the data
1. Register for a free AQICN API token at https://aqicn.org/api/
2. Set environment variable: export AQICN_TOKEN=your_token_here
3. Run: python scripts/00_download_raw.py
   (downloads 2019–2024 for all Krakow stations, ~15 minutes)
```

---

## When the checklist fails

Any failure is a real failure. Don't push. Common causes and fixes:

| Failure | Cause | Fix |
|---|---|---|
| Different row count two runs in a row | `dropna` or `groupby` on unsorted data | Sort by `["station_id", "timestamp"]` before dropping; `groupby(sort=True)` |
| "Module not found" on teammate's machine | Missing pin in `requirements.txt` | `pip freeze > requirements.txt`, re-commit |
| Notebook runs but script crashes | Notebook has hidden state (e.g., `df` from a previous cell) | Restart kernel + Run All — if it fails, the notebook is broken, not just stale |
| CSV has different float rounding two runs in a row | Pandas float formatting changed | Pin `pandas==x.y.z`; use `check_exact=False` in `assert_frame_equal` |
| COVID months appear in cleaned output | Timestamp parsing issue (NaT rows escape the filter) | Ensure `exclude_covid_window` runs *after* `parse_timestamps`; check that the timestamp comparison uses UTC-aware datetimes |
| Coordinate correction not applied | `station_id` in data doesn't match key in `COORD_CORRECTIONS` | Print `df["station_id"].unique()` and compare against `COORD_CORRECTIONS` keys — check for whitespace or case differences |
| Flatline drop removes too many rows | `FLATLINE_WINDOW_HOURS` set too short (e.g., 6h catches normal variation) | Set to 24h minimum; cross-check against data-quality-audit finding (confirmed 36h block) |
| `assert_clean_invariants` fails after a teammate's refactor | A transform was reordered and now produces out-of-range values | Never reorder the `.pipe()` chain in `clean_aqicn_dataset` without re-running all assertions; document reorder in cleaning log |
