# ClassPulse

ClassPulse is a focused real-time teaching copilot. It replays a simulated online class, fuses live confusion signals into a Confusion Confidence Score (CCS), updates per-student concept mastery with Bayesian Knowledge Tracing (BKT), and produces one concrete teacher nudge when confusion crosses a threshold.

This repository follows `AGENTS.md` and implements Tasks 1–9 in `TASK_BRIEFS.md`. The broader earlier ClassroomOS simulator is intentionally not part of this scoped build.

## One-command demo

Windows PowerShell:

```powershell
.\run_demo.ps1
```

The script opens `http://127.0.0.1:8000` and starts FastAPI. On macOS/Linux:

```sh
./run_demo.sh
```

If dependencies have not been installed:

```powershell
py -m pip install -r requirements.txt
```

## What happens live

1. One of three JSON class fixtures replays teacher speech, student chat, and polls using original relative timestamps.
2. Every transcript line passes through the typed sentiment-provider boundary.
3. CCS combines structured learning-state classification, keyword flags, response latency, unique-student breadth, and poll-miss rate with deterministic weighted sigmoids. Evidence decays with age instead of accumulating forever.
4. Explicit poll correctness updates BKT strongly. CCS contributes lower-weight soft evidence.
5. A language-only early warning appears at `0.40`; when confirmed CCS first crosses `0.60`, the nudge engine calls GPT‑5.6 with strict Structured Outputs. It does not fire again until the score falls below the reset threshold.
6. The single dashboard updates through Server-Sent Events without refresh: transcript, CCS gauge/components, nudge, and mastery table.
7. BKT state is persisted to SQLite after every update. A restarted session begins from the previous ending mastery and shows the change since that prior session.
8. An optional “Live student” drawer accepts non-scripted chat during replay. Those events enter the same runtime queue and processing function as fixture events and are visibly tagged.
9. Every replay has its own session ID and isolated CCS, BKT, queue, and nudge state. The active-classes strip exposes simultaneous sessions without mixing their events.

## GPT‑5.6 configuration

Put `OPENAI_API_KEY` in the repository's `.env` file before launching. The file is loaded automatically and ignored by Git. With a key, `CLASSPULSE_LLM_MODE=auto` selects the real Responses API adapter using model `gpt-5.6` and strict JSON schemas for both sentiment and nudge calls.

```powershell
$env:OPENAI_API_KEY = "your-key"
.\run_demo.ps1
```

To require OpenAI and fail instead of falling back:

```powershell
$env:CLASSPULSE_LLM_MODE = "openai"
```

Without a key, the dashboard visibly reports **Deterministic demo fallback**. That offline provider implements the same validated Pydantic contracts so the demo and tests remain reproducible; it never claims its output came from GPT‑5.6.

The implementation follows the official [Responses API](https://developers.openai.com/api/docs/guides/migrate-to-responses) and [GPT‑5.6 model documentation](https://developers.openai.com/api/docs/models/gpt-5.6-sol).

## Architecture

### Repository layout

```text
app/          FastAPI service and CCS, BKT, LLM, session, and persistence modules
data/classes/ Authored live-class fixtures and confusion ground truth
data/real/    Licensed TalkMoves classroom-language validation data
public/       Dependency-free dashboard assets
scripts/      Reproducible evaluation utilities
tests/        Unit, integration, API, UI-contract, and persistence tests
validation/   Generated benchmark reports
```

The backend intentionally lives directly in `app/`; there is no parallel `src/` tree. All automated tests live in `tests/`.
An empty `.agents/` folder may be recreated by the local Codex environment; it is ignored and is not part of the application.

```text
JSON fixture → timed async replay → FastAPI SSE → dashboard transcript
                         │
                         ├→ structured sentiment ─┐
                         ├→ keyword flags         │
                         ├→ response latency      ├→ weighted sigmoid → CCS gauge
                         └→ poll misses ──────────┘                    │
                                                                      ├→ spike-gated GPT‑5.6 nudge
poll correctness ────────────────────────→ deterministic BKT ← CCS soft evidence
                                                                      │
                                                                      └→ mastery table
```

- `app/stream.py`: validated fixture catalog and ordered asynchronous replay.
- `app/ccs.py`: deterministic signal features and bounded sigmoid fusion.
- `app/bkt.py`: deterministic BKT with explicit and soft evidence.
- `app/memory.py`: SQLite mastery repository with timestamped upserts and restart-safe loading.
- `app/llm.py`: strict schemas, OpenAI Responses adapter, and labeled demo provider.
- `app/nudges.py`: threshold crossing and once-per-spike suppression.
- `app/runtime.py`: coherent event-to-CCS-to-BKT-to-nudge loop.
- `app/sessions.py`: concurrent session registry and per-class runtime isolation.
- `app/main.py`: FastAPI, SSE endpoint, health/catalog APIs, and static dashboard.
- `public/`: responsive single-screen live product UI.
- `data/classes/`: three scripted classes with deliberate confusion moments.

## Testing

```powershell
py -m pytest
```

The suite verifies event order/timestamps, all three fixtures, calm/confused CCS, sigmoid bounds, BKT correctness and CCS soft-evidence weighting, both strict OpenAI schemas, one nudge per spike, calm suppression, full runtime integration, live input, persistence, concurrent-session isolation, SSE delivery, APIs, and required dashboard surfaces.

## CCS validation

Run the reproducible authored-fixture backtest with:

```powershell
py scripts/backtest_ccs.py
```

Confirmed-alert results remain **0.857 precision** and **0.500 recall**. The new poll-independent early-warning path reaches **0.818 precision**, **0.750 recall**, and predicts **3 of 4** poll outcomes from the previous event without result leakage. These are improvements on three authored fixtures, not proof of generalization; thresholds require validation on educator-labeled held-out lessons.

See [validation/CCS_BACKTEST.md](./validation/CCS_BACKTEST.md) for per-fixture timelines and machine-readable detail. This is fixture behavior validation, not accuracy against real classroom confusion labels.

## Simulated versus real

| Component | Status |
|---|---|
| Teacher speech-to-text, student chat, poll timing | Pre-scripted simulation |
| Sentiment and nudge generation | Real GPT‑5.6 when configured; visibly labeled deterministic fallback otherwise |
| Keyword, latency, poll, CCS fusion | Real deterministic computation |
| BKT mastery | Real deterministic probabilistic computation |
| Mastery across restarts | SQLite persistence in `data/classpulse.db` |
| Browser updates | Real SSE stream |
| Student chat typed during demo | Real input through the shared runtime queue |
| Concurrent simulated classes | Real isolated runtime sessions |
| Raw audio, multi-teacher accounts, memory agent | Out of scope |

## Real classroom data validation

The repository includes the official TalkMoves public test splits under `data/real/talkmoves/`, licensed **CC BY-NC-SA 4.0** and preserved without content changes. TalkMoves contains human-transcribed, anonymized K–12 mathematics classroom language with teacher and student discourse-move annotations.

ClassPulse validates:

- **30,401** annotated utterance pairs;
- **23,250** teacher pairs across seven teacher talk-move labels;
- **7,151** student pairs across five student talk-move labels;
- required TSV schema, non-empty response coverage, speaker roles, and full label distributions;
- API and dashboard presentation of provenance, examples, metrics, and limitations.

This strengthens real-language and ingestion validation. It does not establish CCS accuracy because TalkMoves supplies discourse labels rather than confusion labels, latency, polls, or mastery outcomes. The synthetic scenarios retain known confusion ground truth for end-to-end validation.

Source: [SumnerLab/TalkMoves](https://github.com/SumnerLab/TalkMoves). Dataset paper: [Suresh et al.](https://arxiv.org/abs/2204.09652). See [`data/real/talkmoves/DATASET.md`](./data/real/talkmoves/DATASET.md) for attribution and usage boundaries.

## Limitations

- Fixtures replace real audio and platform integrations.
- Live typed messages have no trustworthy response-latency value, so their latency contribution is zero; language and subsequent poll signals still apply normally.
- Initial CCS weights and BKT parameters are expert defaults. CCS has been backtested against three authored windows, but it is not trained or calibrated on deployment data and showed only 0.500 recall.
- CCS observes language, latency, and polls, not tone, facial expression, or silence quality.
- Mastery is an estimate based on current evidence, never a diagnosis or fixed student trait.
- SQLite persistence is local to this demo instance and has no authentication, roster reconciliation, or school data-retention policy.
- Concurrent sessions share one local process and SQLite file; this is a demo of state isolation, not a horizontally scalable deployment.
- Automated tests mock the Responses transport; a live GPT‑5.6 call requires the user’s valid API key and account access.
- TalkMoves is restricted to attribution, noncommercial use, and share-alike redistribution under its source license.

Codex was used to implement the FastAPI/SSE service, deterministic math, typed OpenAI boundary, test suite, fixtures, dashboard, launch scripts, and documentation.
