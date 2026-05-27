# Function Design Checklist
# Krakow Air Quality & Urban Form — session 3/scripts/

> Before you commit a function to any script in `session 3/scripts/`, it
> passes this checklist. No exceptions.

---

## The minimum bar — every function

A function ready to commit answers all eight questions in writing,
inside the function itself or its docstring:

- [ ] **Does the function name say what it does as a verb?**
  `detect_station`, `load_station_csv`, `clean_multistation`, `compute_landuse_features_for_station` — good.
  `process`, `clean`, `handle_data` — no. Verbs that describe the *specific*
  transform, not just "cleaning."

- [ ] **Does the function do ONE thing?**
  If you're tempted to use "and" in the docstring summary, split.
  `load_and_clean` is two functions: `load_station_csv` and `clean_multistation`.

- [ ] **Is it pure where possible?**
  No printing in helpers; no global state mutation. Side effects (file I/O,
  `print`) live at the boundaries (`main`, `load_*`, `save_*`). The one
  exception: `print` statements in pipeline functions are acceptable for
  progress reporting during long runs.

- [ ] **Does it have type hints?**
  `pd.DataFrame -> pd.DataFrame` is a fine starting point. Even imperfect
  types document intent. For thresholds: `float = FLATLINE_TOLERANCE`.

- [ ] **Does it have a docstring with `Args` and `Returns`?**
  Three lines minimum. The first line is a one-sentence summary in the
  imperative mood. The rest describe inputs and outputs, and — importantly
  for this project — **the audit finding that motivated the function**.

- [ ] **Does the docstring include an example?**
  At least one `>>>` line showing how to call it. This forces you to
  actually run it. Examples for this project:
  ```
  >>> df_clipped = clip_negative_pm25(df)
  >>> (df_clipped["pm25"] >= 0).all()
  True
  ```

- [ ] **Does it have at least one assertion?**
  Either inside the function (input validation or output check) or via
  validation checks at the end of the pipeline. At minimum:
  - negative clipping: assert pm25 ≥ 0 after clipping
  - coordinate correction: assert lat/lon in valid ranges
  - cleaning output: assert no missing PM2.5

- [ ] **Is it testable without the full dataset?**
  If your function needs the real data to test, it's doing too much.
  Create a 5-row synthetic dataframe in the test. Example:
  ```python
  def test_clip_negative_pm25():
      df = pd.DataFrame({"pm25": [10.0, -1.5, 0.0, 35.2, -0.3]})
      df["pm25"] = df["pm25"].clip(lower=0)
      assert (df["pm25"] >= 0).all()
  ```

---

## The structure — copy this template

```python
def transform_name(
    df: pd.DataFrame,
    threshold: float = DEFAULT_THRESHOLD,
) -> pd.DataFrame:
    """One-sentence imperative summary of what this does.

    Background context paragraph: which audit finding motivated this,
    what the root cause was, what alternatives were considered.

    Args:
        df: Dataframe with required columns [list them].
        threshold: What this parameter controls and its valid range.

    Returns:
        Transformed dataframe with [list added/changed columns].

    Raises:
        ValueError: If required columns are missing.

    Example:
        >>> df_clean = transform_name(df_raw, threshold=0.1)
        >>> df_clean["new_column"].notna().all()
        True
    """
    required = {"col_a", "col_b"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing columns: {missing}")

    out = df.copy()  # never mutate input

    # ... transform logic ...

    return out
```

---

## Anti-patterns to refuse

### The mega-function

```python
# BAD — everything in one block
def clean(df):
    df["date"] = pd.to_datetime(df["date"])
    df = df[df["year"] >= 2019]
    df["pm25"] = df["pm25"].clip(0, 500)
    df = df.dropna(subset=["pm25"])
    df.to_csv("cleaned.csv", index=False)
    return df
```

**Why it's wrong:**
- Five different responsibilities (parse, filter, clip, drop, save)
- Hidden side-effect (writes to CSV) inside a "clean" function
- No type hints, no docstring, no example
- Completely untestable without the real CSV
- The function name lies — it does much more than clean

**Refactor:** separate functions, each doing one thing.

### The mutating-input function

```python
# BAD
def clip_negative_pm25(df):
    df["pm25"] = df["pm25"].clip(lower=0)  # mutates the caller's df!
    return df
```

**Why it's wrong:** mutates the caller's dataframe. If the caller has `df_raw`
as their input, it's no longer raw after this runs. Silent corruption.

**Fix:** `out = df.copy()`, transform `out`, return `out`.

### The undocumented constant

```python
# BAD
df = df[(df["year"] >= 2019) & (df["year"] <= 2024)]  # magic numbers — why?
```

**Fix:** `PROJECT_START_YEAR = 2019` / `PROJECT_END_YEAR = 2024` at the top of the file with a
comment explaining the rationale.

### The non-specific assertion

```python
# BAD
assert df["pm25"].min() >= 0  # works, but doesn't say what to do when it fails
```

**Better:**
```python
n_neg = (df["pm25"] < 0).sum()
assert n_neg == 0, (
    f"clip_negative_pm25 failed: {n_neg} negative values remain. "
    f"Check raw data for new stations with sensor drift issues."
)
```

---

## Project-specific rules

### Always preserve raw before transforming

```python
df["pm25_raw"] = df["pm25"]       # before clipping
```

The cleaning log's reversibility column is only as good as this discipline.
Without `pm25_raw`, the data-cleaning-log entry "reversibility: yes" is a lie.

### Print row counts at every filter

Every function that removes rows must print before and after:
```python
before = len(df)
df = df[~covid_mask]
print(f"COVID exclusion: {before - len(df):,} rows removed")
```

This is how the cleaning log gets populated with real numbers.

### The COVID window constant must be in the constant block

Never write:
```python
df = df[~df["date"].between("2020-03-15", "2020-05-31")]
```

Write:
```python
df = df[~covid_mask]  # COVID_START / COVID_END defined at top of script
```

If we ever need to adjust the COVID window boundaries, we change two constants,
not hunt through code.

---

## When to promote from notebook → script

Lift a notebook cell into a function when:

- [ ] You've stopped iterating on its logic (flatline threshold is settled).
- [ ] It's used more than once.
- [ ] Its inputs and outputs are clear (dataframe in, dataframe out).
- [ ] You want the type checker and tests to verify it.

Keep it in the notebook (for now) when:

- [ ] It's a one-off exploration.
- [ ] You're still changing it.
- [ ] It's tied to interactive output (a histogram, a `df.head()`).

The arrow only goes one direction: notebook → script. Once promoted,
the notebook **imports** the function instead of duplicating it.

---

## Actual scripts in this project

| Script | Location | What it promotes |
|---|---|---|
| `clean_multistation.py` | `session 3/scripts/` | AQICN 8-station cleaning pipeline |
| `clean_krakow_dataset.py` | `session 3/scripts/` | Single-station krakow_ml_dataset cleaning |
| `spatial_features_pipeline.py` | `session 3/scripts/` | Urban Atlas + OSM feature extraction per station |
| `clean_data.py` | `session 3/scripts/` | Utility cleaning functions |
