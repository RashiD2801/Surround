# Session 5 Templates — Evaluation (CRISP-DM Phase 5)

**Track: A — we built a model (Random Forest Regressor for Krakow PM2.5 spatial prediction)**

Drop these into your team repo at the start of Session 5. By 4 PM today,
every file should be filled in and committed.

> **The frame for today:** a result is not a verdict. Architects don't
> judge a building by the render — they do post-occupancy evaluation, go
> back after people move in, and check whether it actually works. Today
> you go back to the brief you wrote in week one and ask whether the
> thing you built actually serves the decision it was for.

---

## Two tracks — we are Track A

| | **Track A — we built a model** |
|---|---|
| The artifact | `models/baseline.joblib` — Random Forest Regressor |
| Core question | Does it generalise, and serve the planning decision? |
| The hunt | Leakage · overfitting · brittleness under shift |
| The verdict | Deploy / iterate / kill the model |
| Track-specific docs | `failure-gallery.md`, model-card eval sections |

---

## Where to put them in your repo

```
docs/
├── session 3/                          (moved from root — S3 teaching materials)
├── session 4/                          (moved from root — S4 teaching materials)
├── session 5/                          (this folder — S5 evaluation)
│   ├── README.md                       (this file)
│   ├── 05-evaluation-scaffold.md       (notebook scaffold — copy to notebooks/)
│   ├── evaluation-report.md            (the verdict)
│   ├── evaluation-log.md               (every test run)
│   ├── failure-gallery.md              (5+ cases the model gets wrong)
│   ├── evaluation-rigor-checklist.md   (pre-verdict checklist)
│   └── pipeline-architecture-v3.md    (v2 evolved with evaluation boxes)
├── model-cards/
│   └── krakow-pm25-spatial-rf-v1.md   (update eval sections today)
└── modelling-log.md                    (from S4 — reference)
```

---

## The 9 artifacts owed by 4 PM

| # | File | Why it exists |
|---|---|---|
| 1 | `notebooks/05-evaluation.ipynb` | The evidence — result vs criteria, failure analysis, reproducible top-to-bottom |
| 2 | `docs/session 5/evaluation-report.md` | The **verdict** — measured against S1 success criteria |
| 3 | `docs/session 5/failure-gallery.md` | **Where it breaks** — 5+ diagnosed cases |
| 4 | Stress / sensitivity results | Shift & missing-input tests — in notebook + report |
| 5 | Results-vs-criteria table | Each S1 criterion · met / partial / missed · with evidence |
| 6 | The recommendation | **deploy / iterate / stop** · with reason and stated confidence |
| 7 | "What we are NOT claiming" | The boundary of the verdict · at least three things |
| 8 | `docs/session 5/evaluation-log.md` | Every test run — including ones that made results look worse |
| 9 | `docs/session 5/pipeline-architecture-v3.md` | v2 evolved with evaluation boxes |

---

## Pre-commit ritual (by 3:55 PM)

1. Restart kernel in `05-evaluation.ipynb` → Run All — no errors
2. Every number in `evaluation-report.md` matches what the notebook prints
3. "What we are NOT claiming" — read aloud, list three without checking
4. State the verdict in one sentence with a confidence
5. `git log --oneline` — show commits since 1:00 PM
6. Push
