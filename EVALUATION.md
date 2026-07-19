# ClassPulse evaluation

## Automated coverage of behavior

The Python test suite covers:

- three fixture files, ordered timestamps, and poll confusion moments;
- clearly confused and clearly calm CCS windows;
- CCS range guarantees;
- ten correct BKT updates, repeated incorrect updates, soft CCS evidence, and combined evidence;
- GPT‑5.6 model selection and strict sentiment/nudge JSON schemas;
- exactly one concept-specific nudge per spike and no calm nudge;
- complete runtime production of transcript, CCS, mastery, and nudge messages;
- FastAPI health/catalog endpoints, SSE delivery, static dashboard delivery;
- presence of the live transcript, CCS gauge, nudge panel, mastery table, and EventSource client.

Latest implementation checkpoint: **19 passed, 0 failed** in 0.98 seconds. Four deprecation warnings originate inside FastAPI under Python 3.14; no ClassPulse warning or failure was emitted.

## Real-server smoke test

Uvicorn was launched on a real localhost socket and verified independently of FastAPI’s in-process test client:

- `GET /api/health`: 200, `status=ok`
- `GET /`: 200
- `GET /static/styles.css`: 200
- `GET /api/stream/fractions-live?speed=10000`: 200
- SSE contained `event`, `ccs`, `mastery`, `nudge`, and `complete` message types
- Provider was honestly reported as `deterministic-demo-fallback` because no API credential was supplied

## Interpretation boundaries

This evaluates functional correctness and deterministic math on known scripted scenarios. It does not establish classroom efficacy, fairness, sentiment-model accuracy, or mastery calibration. A pilot should add educator-labeled transcript windows, CCS calibration curves, nudge usefulness ratings, and BKT predictive log loss.
