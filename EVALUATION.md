# ClassPulse evaluation

## Automated coverage of behavior

The Python test suite covers:

- nine fixture files, ordered timestamps, diverse confusion patterns, false-alarm language, and a calm true-negative lesson;
- clearly confused and clearly calm CCS windows;
- CCS range guarantees;
- ten correct BKT updates, repeated incorrect updates, soft CCS evidence, and combined evidence;
- SQLite round-trip persistence, timestamped updates, unchanged first-run behavior, restart loading, and prior-session deltas;
- GPT‑5.6 model selection and strict sentiment/nudge JSON schemas;
- exactly one concept-specific nudge per spike and no calm nudge;
- complete runtime production of transcript, CCS, mastery, and nudge messages;
- live student submissions entering the same runtime queue and `process_event` path as scripted events, with SSE/API/UI tagging;
- concurrent sessions maintaining independent queues, CCS scores, mastery, stream URLs, and lifecycle status;
- FastAPI health/catalog endpoints, SSE delivery, static dashboard delivery;
- presence of the live transcript, CCS gauge, nudge panel, mastery table, and EventSource client.

Final implementation checkpoint after the CCS upgrade: **39 passed, 0 failed**. Ten deprecation warnings originate inside FastAPI under Python 3.14; no ClassPulse warning or failure was emitted. `node --check public/app.js` also passed.

## Real-data validation

Official TalkMoves public test splits were loaded from the SumnerLab release:

| Measure | Result |
|---|---:|
| Total annotated utterance pairs | 30,401 |
| Teacher pairs | 23,250 |
| Teacher non-empty responses | 23,208 |
| Student pairs | 7,151 |
| Student non-empty responses | 6,994 |
| Teacher annotation categories | 7 |
| Student annotation categories | 5 |
| Schema errors | 0 |

This validates operation on real classroom language and authentic discourse annotations. TalkMoves has no confusion, latency, poll, or mastery labels, so it is not reported as a CCS accuracy benchmark.

A separate balanced 15-utterance proxy check mapped TalkMoves labels 2/3/4 to confused/neutral/positive directions. The deterministic fallback reached **0.400 agreement** and GPT‑5.6 reached **0.667 agreement**. These are proxy-agreement rates, not accuracy; the human labels annotate discourse function rather than learning-state sentiment.

## Authored-fixture CCS backtest

The production CCS path was replayed against confusion annotations in all nine scripted fixtures:

- Aggregate precision: **0.875**
- Aggregate recall: **0.269**
- Confusion matrix: TP 7, FP 1, TN 25, FN 19
- Pre-poll majority-miss prediction: **4/11**

The separate poll-independent early-warning path produced:

- Early-warning precision: **0.750**
- Early-warning recall: **0.577**
- Early-warning confusion matrix: TP 15, FP 5, TN 21, FN 11
- Pre-poll majority-miss prediction: **6/11**

The pre-poll calculation uses the score from the prior event, so the poll result cannot leak into its own prediction. The early score excludes poll outcomes, while confirmed CCS retains them. Evidence is time-decayed and student breadth is normalized against the active roster. Because this remains a tiny authored set used during development, the result may be overfit and must be replicated on held-out educator labels. Full timelines are in [validation/CCS_BACKTEST.md](./validation/CCS_BACKTEST.md).

## Real-server smoke test

Uvicorn was launched on a real localhost socket and verified independently of FastAPI’s in-process test client:

- `GET /api/health`: 200, `status=ok`
- `GET /`: 200
- `GET /static/styles.css`: 200
- `GET /api/stream/fractions-live?speed=10000`: 200
- SSE contained `event`, `ccs`, `mastery`, `nudge`, and `complete` message types
- Provider was honestly reported as `deterministic-demo-fallback` because no API credential was supplied
- two session IDs and stream URLs were unique, both SSE streams completed, and neither stream contained the other session ID
- live input to a specific session returned `202 Accepted`

## Interpretation boundaries

This evaluates functional correctness and deterministic math on known scripted scenarios. It does not establish classroom efficacy, fairness, sentiment-model accuracy, or mastery calibration. A pilot should add educator-labeled transcript windows, CCS calibration curves, nudge usefulness ratings, and BKT predictive log loss.
