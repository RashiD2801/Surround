# Evaluation Checklist

> Before you report a metric — to a reviewer, to your model card, to a
> teammate, to me — it passes this checklist.
>
> Use as a working reference; not a committed artifact.

---

## The bar

**An honest metric reports three axes:**

1. **Splits** — train · val · test, each separately.
2. **Models** — at least one baseline alongside your model.
3. **Spread** — cross-fold mean ± standard deviation.

If your report is missing any axis, it's a slogan, not an evaluation.

---

## The pre-metric checks

Before you even compute a number:

- [ ] **The split is leakage-safe.** All assertions in `src/split_data.py`
      pass. If you can't list which leakage type the split controls for,
      stop and read `modelling-log.md` decision #1.
- [ ] **The test set is sacred.** You haven't opened it, plotted it, or
      `.head()`'d it since it was written.
- [ ] **A Pipeline holds preprocessing.** Imputation, scaling, encoding
      all live inside the `sklearn.Pipeline` — fit only on train.
      Otherwise scaling parameters leak val statistics into the model.
- [ ] **The random seed is set.** `np.random.seed`, `random_state=` on
      every estimator and splitter.

If any of those fail, your metric is fiction. Don't proceed.

---

## The metric-choice rubric

For each metric you report, you should be able to answer:

- [ ] **What decision does this metric serve?** "R²" is not an answer.
      "How much the planner can trust the predicted reduction" is.
- [ ] **What does this metric hide?** Every metric hides something.
      Write it down. Pair the metric with another that exposes what was
      hidden.
- [ ] **Is the metric in interpretable units?** MAE in µg/m³ is
      interpretable. R² is comparative. Both have a role; lead with the
      interpretable one.

Common choices by problem shape:

| Problem | Lead with | Always pair with |
|---|---|---|
| Regression | MAE in real units | R² + persistence-relative MAE |
| Classification · balanced | Accuracy | Confusion matrix + per-class F1 |
| Classification · imbalanced | PR-AUC | Per-class precision and recall |
| Forecasting | MAE per horizon | Persistence-relative error per horizon |
| Ranking | NDCG@k | Per-query NDCG distribution |

---

## The three-axis table

The minimum table to ship:

|         | dumb-mean | persistence | ours | ours (CV mean ± std) |
|---|---|---|---|---|
| **train** | X | X | X | — |
| **val** | X | X | X | X ± X |
| **test** | X | X | X | — |

- [ ] Three rows — one per split.
- [ ] At least three columns — two baselines + the model.
- [ ] CV column for val with mean ± standard deviation.
- [ ] Test row computed exactly once. If you re-tune, you need a new
      test set.

---

## Per-segment evaluation (the bridge to S6)

Aggregate metrics hide the part that's broken. Surface it.

For each factor named in the model card's section 3, compute the same
metric per slice:

- [ ] Per season / per month
- [ ] Per station / per region
- [ ] Per class (if classification)
- [ ] Per regime (e.g. lockdown vs not lockdown for our Krakow dataset)

For each slice, flag:

- [ ] **Where performance is > 50% worse than the aggregate** — these
      slices are out-of-scope candidates and S6's first failure-gallery
      entries.
- [ ] **Where the slice has < 30 samples** — variance dominates; mark
      "low confidence" in the table.

---

## Uncertainty checks

If your output is a point prediction:

- [ ] **Add intervals.** Tree quantiles, conformal prediction, or
      bootstrap — pick one and document.
- [ ] **Compute coverage** of the nominal interval (e.g. fraction of
      true values inside the 90% interval). Aim for ≥ 85% on val.
- [ ] **Plot a calibration curve.** Predicted-vs-actual on val. The
      diagonal is honest; systematic deviation is bias.

If your output is a class probability:

- [ ] **Plot a reliability diagram.** Predicted probability vs observed
      frequency.
- [ ] **Compute expected calibration error (ECE).** A model with great
      accuracy and bad calibration overconfides — dangerous.

---

## The "did we fool ourselves" smell test

Before claiming a result, answer these:

- [ ] **Does the model beat persistence?** If no — you don't have a
      model, you have a worse inertia detector. Either reframe the
      problem or accept the finding in the log.
- [ ] **Is the train-vs-val gap suspicious?** Train MAE 1.2, val MAE
      8.4 → severe overfit. Train MAE 8.2, val MAE 2.1 → leakage somewhere.
- [ ] **Did the number change when we re-ran?** If it changed, the seed
      isn't set everywhere. Fix before reporting.
- [ ] **Could this metric be 'right for the wrong reason'?** E.g. an
      imbalanced classifier with 95% accuracy because it always predicts
      the majority class.
- [ ] **Is the val→test drop reasonable?** A small drop is expected. A
      big drop means we over-tuned to val. Document.

---

## The "we re-ran on test" trap

If you legitimately need a different test set:

- [ ] **Re-split.** Use a new random seed for the split (or a new
      cutoff). Document in `modelling-log.md` why.
- [ ] **Re-fit everything from scratch.** No carrying-over of
      hyperparameters chosen against the previous test set without
      stating that they were so chosen.
- [ ] **Note both numbers in the card.** "Test MAE: 2.55 (split v1);
      2.62 (split v2)." Hiding either is dishonest.

---

## What to include in the modelling log

Every metric you report has a backing entry in `docs/modelling-log.md`:

- The metric chosen.
- Why this metric and not the alternative.
- The number.
- The spread.
- What it hides (and which other metric exposes that).

---

## What to include in the model card

The card's section 7 is the metric output. The minimum:

- The three-axis table (above).
- The per-segment table (above).
- The uncertainty result (coverage of nominal interval).
- One paragraph: what the numbers mean for the intended user.

If the card has one number, it's a marketing slide.

---

## When the checklist fails

| Failure | Likely cause | Fix |
|---|---|---|
| Val MAE ≪ train MAE | Leakage into val (or scaling fit on full data) | Audit pipeline; ensure fit on train only |
| Test MAE ≫ val MAE | Tuned too hard against val | Lock val choices earlier; consider new test set if re-tuning |
| CV spread is huge | Sample size per fold too small, or unstable model | More folds or different model class |
| Coverage way below nominal | Model overconfident — intervals too narrow | Switch to conformal prediction |
| Persistence beats the model | Features don't carry the signal; or problem is mostly inertial | Re-frame, swap features, or accept and document |
| Model card has one number | Report missing axes | Add splits × models × spread |
