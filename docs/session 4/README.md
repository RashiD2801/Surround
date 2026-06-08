# Session 4 Templates — Modelling (CRISP-DM Phase 4)

Drop these into your team repo at the start of Session 4. By 4 PM today,
every file should be filled in and committed.

> **The frame for today:** a model is not an answer — it's a hypothesis the
> data tested. The split is the load case. The metric is the safety factor.
> The model card is the certificate. Without all three, you have a number,
> not an answer.

---

## Where to put them in your repo

```
your-repo/
├── docs/
│   ├── problem-brief.md                (S1)
│   ├── problem-brief-v2.md             (S2)
│   ├── data-source-inventory.md        (S2)
│   ├── datasheets/<slug>.md            (S2, updated S3)
│   ├── data-quality-audit.md           (S2)
│   ├── data-to-decision-map.md         (S2)
│   ├── system-sketch-v0.md             (S2)
│   ├── output-sketch-v0.md             (S2)
│   ├── data-cleaning-log.md            (S3)
│   ├── pipeline-architecture-v1.md     (S3 — REPLACED by v2 today)
│   ├── pipeline-architecture-v2.md     (NEW — v1 evolved with model boxes)
│   ├── modelling-log.md                (NEW — every modelling decision)
│   └── model-cards/
│       └── <model>.md                  (NEW — Mitchell et al. 2019)
├── notebooks/
│   ├── 01-data-profiling.ipynb         (S2)
│   ├── 02-data-cleaning.ipynb          (S3)
│   └── 03-modelling.ipynb              (NEW — exploratory modelling)
├── src/
│   ├── clean_data.py                   (S3)
│   ├── split_data.py                   (NEW — leakage-safe splitter)
│   └── baseline_model.py               (NEW — baselines + first model)
├── data/
│   ├── raw/                            (gitignored)
│   └── processed/
│       ├── <dataset>-clean.parquet     (S3)
│       ├── <dataset>-train.parquet     (NEW)
│       ├── <dataset>-val.parquet       (NEW)
│       └── <dataset>-test.parquet      (NEW — DON'T touch until model locked)
├── models/
│   └── baseline.joblib                 (NEW — saved sklearn Pipeline)
└── requirements.txt                    (UPDATE — sklearn, joblib pinned)
```

---

## The 9 artifacts you owe by 4 PM

| # | File | Why it exists |
|---|---|---|
| 1 | `notebooks/03-modelling.ipynb` | The exploration — clean parquet → split → baseline → first model, thinking visible |
| 2 | `src/split_data.py` | The **leakage-safe splitter** — temporal / spatial / group, with assertions |
| 3 | `data/processed/<dataset>-{train,val,test}.parquet` | The **three sets**. Test parquet is sacred — touched once |
| 4 | `src/baseline_model.py` | **At least two baselines + one defensible model**. All in named, typed, documented functions |
| 5 | `models/baseline.joblib` | The saved sklearn `Pipeline` — the model artifact that S5–S7 will load |
| 6 | `docs/model-cards/<model>.md` | The **model card** — Mitchell et al. 2019 — all 8 sections filled |
| 7 | `docs/modelling-log.md` | Every modelling decision justified (split / baseline / model / metric) |
| 8 | Honest metrics table in the card & notebook | Train · val · test × baseline · model × mean ± spread |
| 9 | `docs/pipeline-architecture-v2.md` | v1 evolved with the new split + train + model boxes |

---

## The frame — modelling is design

You'd never build a cantilever before checking the simple post-and-beam
holds on this site. You'd never ship a structural number without the load
case and the safety factor. Same applies to a model.

For every modelling decision in your pipeline, you should be able to
answer:

1. **What is the split testing?** What kind of generalization does this
   split prove? (Time? Space? Entity?)
2. **Which baselines did you beat?** And by how much? On which split?
3. **What is the model NOT for?** At least three out-of-scope uses.
4. **What does the spread look like?** Mean ± std across folds.

If you can't answer all four, the model is undocumented. The model card
and modelling log are where you answer them.

---

## The phase 4 spine — four tasks

1. **Split** — generate test design. Train / val / test, with leakage
   discipline. Temporal, spatial, group, or stacked — pick consciously.
2. **Baseline** — fit at least two baselines before any "real" model. Mean,
   persistence, spatial nearest, domain heuristic. The floor everything has
   to beat.
3. **Model** — pick ONE technique. Justify it with three questions
   (problem shape, data size, explainability). Wrap in `sklearn.Pipeline`.
4. **Assess** — honest metrics across three axes: splits × models × spread.
   Plus per-segment performance.

Cross-cutting moves applied to all four tasks:

- **Notebook → module** — every transform and every training function
  promoted to `src/`, typed, documented, tested.
- **The Pipeline IS the artifact** — preprocess + fit + predict in one
  `sklearn.Pipeline`. Saved with `joblib.dump`. Round-trip checked.
- **The test set is sacred** — written at split time, touched once at the
  end.
- **Reproducibility** — `RANDOM_SEED` set everywhere, parquet outputs
  deterministic, model loads identically from disk.
- **The model card** — eight sections, Mitchell et al. 2019. No model leaves
  the notebook without one.

---

## What Session 4 does NOT do

To protect the phase boundary in both directions:

- ❌ Generate synthetic data (Phase 5 / Session 5)
- ❌ Tune a second model to death (Phase 5 / Session 5)
- ❌ Build a failure gallery (Phase 6 / Session 6)
- ❌ Stress-test against distribution shifts (Phase 6 / Session 6)
- ❌ Build the final decision-facing UI (Phase 7 / Session 7)
- ❌ Hyperparameter sweeps "to push the number up"

Modelling ends when you have a defensible baseline, one honest model, and
a card the next session can read. Stop there.

---

## The pre-commit ritual (every team, by 3:55 PM)

1. **Restart kernel** in `03-modelling.ipynb`.
2. **Run all** — confirm no errors.
3. **Run** `python src/split_data.py` — confirm the three parquets
   regenerate identically.
4. **Run** `python src/baseline_model.py` — confirm `models/baseline.joblib`
   regenerates and the round-trip check passes.
5. **Confirm** the metrics table in the model card matches what the script
   prints.
6. **Read** the model card's "out-of-scope" section out loud. Can you list
   three things this model is NOT for, without checking?
7. `git log --oneline` — show the commits since 1:00 PM.
8. Push.

If any step fails, that's the fix-list before next Tuesday.

---

## Reading order — fill the templates in this order

1. **`03-modelling-scaffold.md`** — copy structure into your notebook
2. **`split-data-module.md`** — copy as the skeleton of `src/split_data.py`,
   run it first to produce the three parquets
3. **`baseline-model-module.md`** — copy as the skeleton of
   `src/baseline_model.py`, fit baselines first then the model
4. **`evaluation-checklist.md`** — work through before computing any metric
5. **`modelling-log.md`** — log every modelling decision as you make it
6. **`model-card.md`** — fill once your model is locked
7. **`pipeline-architecture-v2.md`** — update once everything is stable

---

## Banned phrases for the workshop

If you say any of these, the conversation restarts:

- "The R² is 0.97." *(no comparator, no split named, no spread)*
- "We used train_test_split with random_state=42." *(random splits lie for
  our data)*
- "It's a neural network." *(not an explanation)*
- "We'll add the baseline at the end." *(baselines come first)*
- "We re-ran on test to check." *(test is touched once)*

---

## The peer-review prompt (block 03)

You'll review another team's model card for ~10 minutes. Specifically:

1. Read all 8 sections of their card.
2. Explain — in one sentence — what their model is for. And one sentence on
   what it's NOT for.
3. Find their metrics table. Does the model beat the baselines? On which
   split? By how much? Is the spread reported?
4. **Open their `src/split_data.py` and hunt for leakage.** Is anything
   from the future in the past? Are entities split across train and test?
5. Leave three bullets of feedback at the bottom of their
   `docs/modelling-log.md`.

This is the second cross-team review of the seminar. Be specific. Be
useful. The leakage hunt is the most valuable thing reviewers do —
reviewers find leaks faster than authors. That's the whole point.
