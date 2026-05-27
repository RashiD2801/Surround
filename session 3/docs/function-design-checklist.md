# Function Design Checklist
# Krakow Air Quality & Urban Form — src/clean_data.py

> Before you commit a function to `src/clean_data.py` (or any module), it
> passes this checklist. No exceptions.
>
> Use as a working reference; not a committed artifact.

---

## The minimum bar — every function

A function ready to commit answers all eight questions in writing,
inside the function itself or its docstring:

- [ ] **Does the function name say what it does as a verb?**
  `parse_timestamps`, `clip_negative_pm25`, `drop_flatline_periods` — good.
  `process`, `clean`, `handle_data` — no. Verbs that describe the *specific*
  transform, not just "cleaning."

- [ ] **Does the function do ONE thing?**
  If you're tempted to use "and" in the docstring summary, split.
  `clip_and_aggregate` is two functions: `clip_negative_pm25` and `aggregate_to_monthly`.

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
  `assert_clean_invariants` at the end of the pipeline. At minimum:
  - `clip_negative_pm25`: assert pm25 ≥ 0 after clipping
  - `correct_station_coordinates`: assert lat/lon in valid ranges
  - `aggregate_to_monthly`: assert completeness ∈ [0, 1]

- [ ] **Is it testable without the full 440k-row AQICN CSV?**
  If your function needs the real data to test, it's doing too much.
  Create a 5-row synthetic dataframe in the test. Example:
  ```python
  def test_clip_negative_pm25():
      df = pd.DataFrame({"pm25": [10.0, -1.5, 0.0, 35.2, -0.3]})
      out = clip_negative_pm25(df)
      assert (out["pm25"] >= 0).all()
      assert out["pm25_negative_flag"].sum() == 2
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
# BAD — what clean_data.py looked like before session 3
def clean(df):
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df = df[~df["timestamp"].between("2020-03-15", "2020-05-31")]
    df["pm25"] = df["pm25"].clip(0, 500)
    rolling_std = df.groupby("station_id")["pm25"].transform(
        lambda s: s.rolling(24).std()
    )
    df = df[rolling_std >= 0.1]
    df["year_month"] = df["timestamp"].dt.to_period("M")
    df = df.groupby(["station_id", "year_month"])["pm25"].mean().reset_index()
    df.to_csv("aqicn_monthly.csv", index=False)
    return df
```

**Why it's wrong:**
- Six different responsibilities (parse, filter, clip, detect, aggregate, save)
- Hidden side-effect (writes to CSV) inside a "clean" function
- No type hints, no docstring, no example
- Completely untestable — must provide the real CSV to test any of the logic
- The function name lies — it does much more than clean

**Refactor:** seven separate functions, each doing one thing, chained with `.pipe()`.

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

### The flag-soup signature

```python
# BAD
def clean(df, parse_ts, exclude_covid, clip_neg, drop_flat, aggregate, write_csv):
    if parse_ts:
        ...
    if exclude_covid:
        ...
```

**Why it's wrong:** booleans are configuration in disguise. This is seven
functions in one, controlled by flags. Adding an eighth flag means touching
every call site.

**Fix:** seven functions, composed by the caller with `.pipe()`.

### The undocumented constant

```python
# BAD
df = df[df["pm25_completeness"] >= 0.75]  # magic number — why 75%?
```

**Fix:** `MIN_MONTHLY_COMPLETENESS = 0.75` at the top of the file with a
comment explaining the rationale. Then `df[df["pm25_completeness"] >= MIN_MONTHLY_COMPLETENESS]`.

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
out["pm25_raw"] = out["pm25"]       # before clipping
out["lat_original"] = out["lat"]    # before coordinate correction
out["timestamp_raw"] = out["timestamp"]  # before parsing
```

The cleaning log's reversibility column is only as good as this discipline.
Without `pm25_raw`, the data-cleaning-log entry "reversibility: yes" is a lie.

### Print row counts at every filter

Every function that removes rows must print before and after:
```python
before = len(out)
out = out[~covid_mask]
print(f"exclude_covid_window: {before - len(out):,} rows removed")
```

This is how the cleaning log gets populated with real numbers. Without it,
"~18,000 rows removed" is an estimate. With it, it's a fact.

### The COVID window constant must be in the constant block

Never write:
```python
df = df[~df["timestamp"].between("2020-03-15", "2020-05-31")]
```

Write:
```python
df = df[~df["timestamp"].between(COVID_EXCLUDE_START, COVID_EXCLUDE_END)]
```

If we ever need to adjust the COVID window boundaries (e.g., to capture
the second lockdown), we change two constants, not hunt through code.

---

## When to promote from notebook → module

Lift a notebook cell into a function when:

- [ ] You've stopped iterating on its logic (flatline threshold is settled at 24h/0.1µg/m³).
- [ ] It's used more than once (monthly aggregation is called in notebook AND in potential future scripts).
- [ ] Its inputs and outputs are clear (dataframe in, dataframe out).
- [ ] You want the type checker and tests to verify it.

Keep it in the notebook (for now) when:

- [ ] It's a one-off exploration ("what does the Kurdwanów flatline look like?").
- [ ] You're still changing it (adjusting the flatline window from 6h to 24h).
- [ ] It's tied to interactive output (a histogram, a `df.head()`).

The arrow only goes one direction: notebook → module. Once promoted,
the notebook **imports** the function instead of duplicating it:

```python
# After promotion: replace notebook cells with:
from src.clean_data import clip_negative_pm25, drop_flatline_periods
df = clip_negative_pm25(df)
df = drop_flatline_periods(df)
```

---

## The LLM working loop applied to functions

When you ask an LLM to write a cleaning function for you:

1. **Specify** — input column names and types, expected output columns, the
   specific audit finding it addresses, and the assertion that proves it worked.
   Not "make a cleaning function." Yes: "given a df with columns [station_id,
   timestamp (UTC datetime), pm25 (float)], detect and drop rows where the
   24-hour rolling std dev of pm25 within a station is below 0.1 µg/m³,
   which indicates a stuck sensor. Assert that Kurdwanów December 2022 rows
   are absent from the output."

2. **Direct** — paste the function template above and ask the LLM to fill
   in the body. Reference the specific constants from `src/clean_data.py`.

3. **Verify** — read the body LINE BY LINE. Does `group_keys=False` in the
   `groupby().apply()` match the pandas version you're using? Does the
   rolling window use the right column? Run the example on a 5-row
   synthetic dataframe before touching the full dataset.

4. **Iterate** — if the function fails the checklist, ask for a refactor.
   "It works on my machine" is not "it passes all eight items in the checklist."

If the function passes the checklist, it goes in `src/`. If it doesn't,
it stays in the notebook until it does.
