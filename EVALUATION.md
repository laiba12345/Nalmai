# Nalmai evaluation

## Automated coverage of behavior

The Python test suite covers:

- nine fixture files, ordered timestamps, diverse confusion patterns, false-alarm language, and a calm true-negative lesson;
- clearly confused and clearly calm CCS windows;
- CCS range guarantees;
- correct and incorrect BKT updates, student-specific language evidence, and protection against class-wide CCS mastery penalties;
- SQLite round-trip persistence, timestamped updates, unchanged first-run behavior, restart loading, and prior-session deltas;
- GPT‑5.6 model selection and strict schemas for sentiment, nudge, explanation risk, and implementation verification;
- exactly one concept-specific nudge per spike and no calm nudge;
- complete runtime production of transcript, CCS, mastery, and nudge messages;
- live student submissions entering the same runtime queue and `process_event` path as scripted events, with SSE/API/UI tagging;
- concurrent sessions maintaining independent queues, CCS scores, mastery, stream URLs, and lifecycle status;
- TalkMoves sentiment proxy agreement, CCS evidence-quality buckets, and matched nudge-outcome arm linkage;
- ClassBank CHAT speaker parsing, millisecond timestamp preservation, media/provenance metadata, and existing-runtime compatibility;
- FastAPI health/catalog endpoints, SSE delivery, static dashboard delivery;
- presence of the live transcript, CCS gauge, nudge panel, mastery table, and EventSource client.
- automatic nudge-implementation verification from subsequent teacher speech, supporting evidence, manual override, visible provider failure, and separate next-poll outcomes;
- the 72-second extended presentation fixture producing a 25% baseline, verified visual-model implementation, 100% follow-up, and an observational +75-point delta.
- two-person WebRTC signaling room capacity, duplicate participant rejection,
  offer/answer relay, disconnect cleanup, and a real-Uvicorn smoke test that
  joined teacher and student while rejecting a third participant.
- a dedicated `/call` product surface with role-specific layouts: teacher video
  plus live CCS/mastery/risk/nudge/transcript/AI-poll surfaces, and a student call
  view without private teacher guidance.
- strict GPT-5.6 baseline/transfer poll schemas, generated-poll runtime events,
  correct-answer withholding from the student payload, response relay, and
  deterministic grading through the existing poll API.

The current automated suite contains **104 tests** and is rerun after each implementation task. Framework deprecation warnings under Python 3.14 are tracked separately from Nalmai failures. JavaScript syntax is also checked with Node.

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

## CCS evidence-quality check

Warning/confirmed event points were grouped by displayed evidence quality. Distinct signal types, student breadth, and confirmation state prevent repeated events from mechanically inflating this value. The authored-fixture buckets remain non-monotonic, so evidence quality is explicitly not an alert-correctness probability. Details are in [validation/CCS_CONFIDENCE_CALIBRATION.md](./validation/CCS_CONFIDENCE_CALIBRATION.md).

## Authored nudge-outcome linkage

Two matched pairs replay through the production runtime with explicit `nudge_applied` markers. Fractions and forces both show authored next-poll correctness changing from **0.250 control** to **1.000 reframed** (**+0.750** each and in aggregate). This validates trigger-to-next-poll linkage and matched-arm analysis. Because outcomes are authored by construction and there are no real participants or randomization, it is not evidence of a causal learning effect. Details are in [validation/NUDGE_OUTCOME_BACKTEST.md](./validation/NUDGE_OUTCOME_BACKTEST.md).

## Real-server smoke test

The Task 23 smoke test ran Uvicorn on `127.0.0.1:8877` in deterministic demo
mode. It created a persistent live session, consumed SSE, submitted one live
confused-language event and one live poll, observed `event`, `ccs`, and
`mastery` messages containing `evidence_quality`, stopped the session, and
received `complete`. This validates server lifecycle and live wiring, not
classroom efficacy or OpenAI latency.

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
