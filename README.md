# AhaLoop

AhaLoop is a real-time teaching copilot that detects confusion, recommends an evidence-informed teaching move, observes the next check, and improves strategy selection within the live lesson.

> Naming note: AhaLoop was formerly developed under the name **ClassPulse**. Internal compatibility identifiers may retain the former lowercase name so existing data and environment configuration continue to work.

This repository follows `AGENTS.md` and the staged tasks in `TASK_BRIEFS.md`.

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

1. A curated lesson replays teacher speech, unsolicited student chat, and polls using original relative timestamps; the extended presentation fixture detects confusion during an ordinary explanation before any teacher question or poll.
2. Every transcript line passes through the typed sentiment-provider boundary.
3. CCS combines structured learning-state classification, keyword flags, response latency, unique-student breadth, and poll-miss rate with deterministic weighted sigmoids. Evidence decays with age instead of accumulating forever.
4. Explicit poll correctness updates BKT strongly. A student's own confused language can provide lower-weight soft evidence only for that student; class-wide CCS does not change individual mastery.
5. A language-only early warning appears at `0.40`; when confirmed CCS first crosses `0.60`, the nudge engine calls GPT‑5.6 with strict Structured Outputs. It does not fire again until the score falls below the reset threshold.
6. The single dashboard updates through Server-Sent Events without refresh: transcript, CCS gauge/components, nudge, and mastery table.
7. BKT state is persisted to SQLite after every update. A restarted session begins from the previous ending mastery and shows the change since that prior session.
8. An optional “Live student” drawer accepts non-scripted chat during replay. Those events enter the same runtime queue and processing function as fixture events and are visibly tagged.
9. Every replay has its own session ID and isolated CCS, BKT, queue, and nudge state. The active-classes strip exposes simultaneous sessions without mixing their events.
10. After a nudge, GPT-5.6 checks subsequent teacher speech for observable implementation evidence. The dashboard shows status, confidence, and a supporting transcript quote; the teacher can confirm or correct it.
11. The next poll is tracked separately as an observed outcome, preserving the distinction between “the strategy was implemented” and “student performance changed afterward.”

## GPT‑5.6 configuration

Put `OPENAI_API_KEY` in the repository's `.env` file before launching. The file is loaded automatically and ignored by Git. With a key, `CLASSPULSE_LLM_MODE=auto` selects the real Responses API adapter using model `gpt-5.6` and strict JSON schemas for student learning state, explanation risk, nudge generation, and implementation verification.

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

## Live lecture pipeline

1. For a solo lecture, choose the closest lesson/concept and click **Start live lecture**.
2. Open the dedicated **Live call** tab at `/call`. The teacher clicks **Create as teacher**, shares the
   six-character room code, and the student enters it in a second browser and
   clicks **Join as student**. The room rejects a third participant.
3. Once both videos appear, the teacher clicks **Start live lecture**. The
   browser mixes teacher and student call audio into standalone six-second
   windows uploaded to FastAPI; WebRTC video/audio remains peer-to-peer.
4. The server calls `gpt-4o-transcribe-diarize` with `diarized_json`. Set the
   teacher speaker ID (normally `speaker_0`) in the dashboard; all other speaker
   segments enter the student-signal path.
5. Teacher text is checked by GPT-5.6 against the strict explanation-risk
   schema. Student text updates CCS and BKT through the existing runtime.
6. Subsequent teacher speech is checked for evidence that the nudge was
   implemented. The teacher can confirm or correct the model judgment, and a
   later poll is reported separately as an observed outcome.

The teacher call view keeps the confusion score, class mastery, explanation
risk, transcript, teaching suggestions, implementation verification, and live
poll controls visible beside the videos. The student role sees only the call.

For the most reliable local demonstration, open `/call` in two browser windows on the same
computer. Camera/microphone access from a second
physical device normally requires serving AhaLoop over HTTPS because browsers
restrict media capture on non-secure network origins.

The API key stays in `.env` on the server. The capture path requires
`OPENAI_API_KEY`; deterministic demo mode still supports scripted replays but
cannot transcribe audio. Transcription is near-real-time and chunked, so output
arrives after each audio window plus API latency. Speaker labels are model
estimates and the teacher ID may need changing. Outcome deltas are observational
and do not establish that a nudge caused learning.

## Reliability and evidence boundaries

- Class-wide CCS affects intervention timing only; it never directly changes
  every learner's BKT state.
- A poll updates only its respondents. Individual language updates only its
  speaker and only when classified confused with probability at least `0.50`;
  positive and neutral language is a no-op for mastery.
- Event IDs are deduplicated, preventing one utterance from being applied twice.
- Sentiment, explanation-risk, and nudge calls run off the event loop with an
  eight-second bound. Transcription has a configurable 30-second bound
  (`CLASSPULSE_TRANSCRIPTION_TIMEOUT`). Failures emit `model_error` SSE events
  or an explicit HTTP error; no successful model result is fabricated.
- Legacy persisted mastery created under the former class-wide CCS rule is
  invalidated once because its individual states cannot be reconstructed.
- CCS exposes **evidence quality**, not confidence or probability.

## Architecture

### Repository layout

```text
app/          FastAPI service and CCS, BKT, LLM, session, and persistence modules
data/classes/ Authored live-class fixtures and confusion ground truth
data/validation_classes/ Additional authored benchmark-only scenarios
data/outcome_pairs/ Matched authored control/reframed outcome scenarios
data/classbank/ Local-only authenticated ClassBank transcripts and media
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
- `app/ccs.py`: deterministic class-level signal features and bounded sigmoid fusion; CCS drives nudges but never changes every student's mastery.
- `app/classbank.py`: time-aligned TalkBank CHAT parsing and AhaLoop conversion.
- `app/bkt.py`: deterministic BKT with explicit and soft evidence.
- `app/memory.py`: SQLite mastery repository with timestamped upserts and restart-safe loading.
- `app/llm.py`: strict schemas, OpenAI Responses adapter, and labeled demo provider.
- `app/nudges.py`: threshold crossing and once-per-spike suppression.
- `app/runtime.py`: coherent event-to-CCS-to-BKT-to-nudge loop.
- `app/sessions.py`: concurrent session registry and per-class runtime isolation.
- `app/main.py`: FastAPI, SSE endpoint, health/catalog APIs, and static dashboard.
- `public/`: responsive single-screen live product UI.
- `data/classes/`: three curated live-demo classes.
- `data/validation_classes/`: six benchmark-only classes spanning slow-build, poll-only, latency-only, recovery, false-alarm, and calm patterns.

## Testing

```powershell
py -m pytest
```

The suite verifies event order/timestamps, all nine fixtures, calm/confused CCS, sigmoid bounds, BKT correctness and CCS soft-evidence weighting, both strict OpenAI schemas, one nudge per spike, calm suppression, full runtime integration, live input, persistence, concurrent-session isolation, SSE delivery, APIs, and required dashboard surfaces.

## Blinded educator nudge evaluation

Prepare a JSON list of authored or authorized/de-identified nudge items, then:

```powershell
py scripts/educator_nudge_evaluation.py source-items.json packet.json
```

Open `validation/educator_rating_form.html`, load `packet.json`, enter an
anonymous rater code, and rate the packet. A small packet should take under ten
minutes. After downloading `educator-ratings.json`, regenerate results:

```powershell
py scripts/report_educator_ratings.py educator-ratings.json educator-report.json
```

The packet hides provider identity and rejects direct identifier fields. Never
export protected classroom text without authorization and de-identification.
Authentic educator results are not yet collected; synthetic fixtures validate
the workflow only. See `validation/EDUCATOR_NUDGE_EVALUATION.md`.

## Held-out confusion annotation

Task 22 adds a frozen-configuration annotation and evaluation path for educator
labels that were not used to tune CCS. Run `py scripts/heldout_confusion.py
export ...` and `py scripts/heldout_confusion.py evaluate ...`; see
`validation/HELDOUT_CONFUSION_EVALUATION.md`. The workflow refuses calibration
fixtures, future-poll leakage, configuration mismatches, and TalkMoves labels as
confusion truth. Authentic held-out results remain pending.

## CCS validation

Run the reproducible authored-fixture backtest with:

```powershell
py scripts/backtest_ccs.py
```

Across nine authored fixtures, confirmed alerts reach **0.875 precision** and **0.269 recall**. The poll-independent early-warning path reaches **0.750 precision**, **0.577 recall**, and predicts **6 of 11** poll outcomes from the previous event without result leakage. Expanding beyond the original three scenarios exposes materially weaker recall, especially for poll-only and latency-only confusion. These are authored-fixture results, not proof of generalization; thresholds require validation on educator-labeled held-out lessons.

See [validation/CCS_BACKTEST.md](./validation/CCS_BACKTEST.md) for per-fixture timelines and machine-readable detail. This is fixture behavior validation, not accuracy against real classroom confusion labels.

### Confidence calibration

Run `py scripts/calibrate_ccs_confidence.py` to bucket warning/confirmed events by displayed evidence quality and compare each bucket with empirical authored-window precision. The formula rewards distinct signal types, student breadth, and confirmed state rather than repeated raw evidence counts. The current authored-fixture check is explicitly uncalibrated: evidence quality is a heuristic, not a probability that an alert is correct. See [validation/CCS_CONFIDENCE_CALIBRATION.md](./validation/CCS_CONFIDENCE_CALIBRATION.md).

## Outcome validation

Run `py scripts/backtest_nudge_outcome.py` to replay two matched control/reframed pairs for fractions and forces. Both arms trigger at the same point and measure the immediately following poll; events and session metadata carry `nudge_applied`. In these authored pairs, mean next-poll correctness is **0.250 control** versus **1.000 reframed**, an authored **+0.750 delta**. This verifies outcome-linking and A/B scaffolding only. The improved responses were written into the scenarios, so this is **not a causal experiment** and does not establish effects on real teacher behavior or student learning. See [validation/NUDGE_OUTCOME_BACKTEST.md](./validation/NUDGE_OUTCOME_BACKTEST.md).

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

AhaLoop validates:

- **30,401** annotated utterance pairs;
- **23,250** teacher pairs across seven teacher talk-move labels;
- **7,151** student pairs across five student talk-move labels;
- required TSV schema, non-empty response coverage, speaker roles, and full label distributions;
- API and dashboard presentation of provenance, examples, metrics, and limitations.

This strengthens real-language and ingestion validation. It does not establish CCS accuracy because TalkMoves supplies discourse labels rather than confusion labels, latency, polls, or mastery outcomes. The synthetic scenarios retain known confusion ground truth for end-to-end validation.

### TalkMoves sentiment proxy agreement

Run `py scripts/talkmoves_sentiment_check.py` to compare classifier output with a deliberately limited discourse-to-sentiment proxy: asking for information → confused, making a claim → neutral, and providing evidence → positive. Labels without a defensible direction are excluded. On a balanced 15-utterance sample, the deterministic fallback agreed on **6/15 (0.400)** and GPT‑5.6 agreed on **10/15 (0.667)**. This is **agreement with a judgment-call proxy, not accuracy and not confusion ground truth**. See [validation/TALKMOVES_SENTIMENT_PROXY.md](./validation/TALKMOVES_SENTIMENT_PROXY.md) for the mapping, per-label results, sampled utterances, and limitations.

Source: [SumnerLab/TalkMoves](https://github.com/SumnerLab/TalkMoves). Dataset paper: [Suresh et al.](https://arxiv.org/abs/2204.09652). See [`data/real/talkmoves/DATASET.md`](./data/real/talkmoves/DATASET.md) for attribution and usage boundaries.

## Recorded live-class lessons with ClassBank

AhaLoop can import authentic ClassBank TIMSS-Math CHAT transcripts and replay them through the same runtime at their recorded utterance timestamps. Imported teacher and student turns appear in the normal transcript and CCS pipeline with a visible `RECORDED CLASSBANK` marker; session metadata retains the corpus citation and optional local media path.

ClassBank requires registration, and its transcript/media server was not reachable from this build environment, so protected lessons are **not bundled or redistributed**. After downloading through your TalkBank account, run:

```powershell
py scripts/import_classbank.py data/classbank/raw --concept mathematics --media-dir data/classbank/media
```

Restart the demo and imported lessons appear in the lesson selector. See [data/classbank/README.md](./data/classbank/README.md) for acquisition, citation, privacy, and folder instructions. This integration replays human transcripts from recorded live classes; the separate browser microphone path provides chunked speech-to-text for new live sessions.

## Limitations

- Fixtures replace real audio and platform integrations.
- ClassBank imports use authentic recorded-lesson transcripts, but AhaLoop does not redistribute the protected media or yet transcribe its audio itself.
- Live typed messages have no trustworthy response-latency value, so their latency contribution is zero; language and subsequent poll signals still apply normally.
- Initial CCS weights and BKT parameters are expert defaults. CCS has been backtested against nine diverse authored fixtures, but it is not trained on deployment data; expanded-set confirmed recall is only 0.269 and displayed evidence quality remains uncalibrated.
- CCS observes language, latency, and polls, not tone, facial expression, or silence quality.
- Mastery is an estimate based on current evidence, never a diagnosis or fixed student trait.
- SQLite persistence is local to this demo instance and has no authentication, roster reconciliation, or school data-retention policy.
- Concurrent sessions share one local process and SQLite file; this is a demo of state isolation, not a horizontally scalable deployment.
- Two-person call rooms are in-memory, unauthenticated demo signaling with a
  hard capacity of two. They are not a replacement for Zoom/Teams, and a public
  deployment requires HTTPS, authenticated room access, TURN infrastructure,
  consent, and an institutional privacy policy.
- Automated tests mock the Responses transport; a live GPT‑5.6 call requires the user’s valid API key and account access.
- TalkMoves is restricted to attribution, noncommercial use, and share-alike redistribution under its source license.

## How I collaborated with Codex

I used Codex as an implementation and evaluation partner, not as the source of the product idea or the final authority on educational claims. I supplied the AhaLoop goal, the staged task briefs, scope constraints, technology choices, and acceptance criteria. Codex inspected those instructions, implemented each bounded task, ran the application and tests, surfaced failures, and committed completed tasks separately so I could review the progression.

### Prompts and task briefs I used

The collaboration started with direct prompts such as:

> “I have an instruction file for the project. Build the project end to end. Make sure to test every aspect of it.”

> “Implement everything; test if it’s correct.”

> “Add real data to the project for greater impact and validation.”

> “Push each task as a separate commit.”

I then used the more precise briefs in [`TASK_BRIEFS.md`](./TASK_BRIEFS.md). Representative examples included:

- Build a deterministic CCS engine from structured sentiment, keyword, latency, and poll signals, with calm/confused tests written first.
- Implement BKT per student and concept without putting an LLM inside the mathematical update.
- Route typed live-student messages through exactly the same queue and CCS/BKT path as replayed events.
- Support isolated concurrent sessions while preserving the zero-setup single-class demo.
- Expand the CCS backtest without retuning weights merely to improve reported numbers.
- Compare TalkMoves discourse labels with a documented sentiment proxy and report “agreement,” never “accuracy.”
- Check evidence-quality calibration and explicitly avoid a probability claim when authentic held-out evidence does not support one.
- Add matched nudge-outcome scenarios while stating that authored improvements are not a causal experiment.
- Import authenticated ClassBank CHAT transcripts without redistributing protected classroom data.

These task briefs made desired behavior, exclusions, test expectations, and claim boundaries explicit before implementation.

### What Codex implemented

Codex implemented and iteratively verified:

- The FastAPI service, SSE event stream, session registry, compatibility routes, and static dashboard delivery.
- The asynchronous classroom runtime shared by authored fixtures, typed live input, and imported ClassBank transcript turns.
- Deterministic CCS fusion, early-warning and confirmed states, time decay, unique-student breadth, evidence reporting, and alert gating.
- Deterministic BKT updates and SQLite persistence with prior-session mastery deltas.
- GPT‑5.6 Responses API adapters using strict Structured Outputs for learning-state classification and teaching nudges, plus an honestly labeled deterministic fallback.
- The live dashboard: transcript, CCS components, warning state, nudge panel, mastery table, live-input controls, active-session cards, and recorded-ClassBank labels.
- TalkMoves ingestion and provenance reporting, expanded authored validation fixtures, evidence-quality analysis, matched nudge-outcome fixtures, and ClassBank CHAT import tooling.
- Windows and Unix one-command launch scripts, `.env` loading, documentation, evaluation reports, and the separate task-level Git history.

Codex also diagnosed issues found during integration rather than hiding them—for example, a session compatibility regression, a nudge-outcome poll linked before the reframe, duplicate anonymized ClassBank participant names, and the expanded fixture set’s substantially weaker recall.

### What I decided, constrained, or rejected

I retained responsibility for the product and evidence decisions:

- I chose the core product goal: help a teacher notice developing confusion and receive a concise re-explanation suggestion while tracking concept mastery.
- I chose Python/FastAPI, a lightweight browser UI, SQLite, GPT‑5.6 Structured Outputs, deterministic CCS/BKT math, and separate task commits.
- I required the demo to distinguish simulated, typed-live, recorded-live-class, and genuinely model-generated data instead of presenting all inputs as live audio.
- I rejected the idea that TalkMoves proxy agreement could be called sentiment “accuracy,” because its human labels describe discourse moves rather than confusion.
- I rejected post-hoc CCS retuning solely to make three authored fixtures look better. The expanded nine-fixture benchmark therefore reports the weaker recall it actually found.
- I rejected displaying CCS evidence quality as a probability after the authored-fixture bucket analysis remained non-monotonic.
- I rejected treating the +0.750 authored nudge-outcome delta as evidence that nudges cause learning; it validates linkage and A/B scaffolding only.
- I decided to use ClassBank/TIMSS-Math as the path toward authentic recorded lessons, while keeping protected transcripts and media local and out of Git.
- I chose a dual input strategy: browser microphone capture with chunked speech-to-text for the live path, plus deterministic timestamped replay for a reliable judged demo. ClassBank imports remain transcript replays and do not claim that protected source media was transcribed here.

### Tests and evaluation Codex helped construct

Codex helped build the current 96-test suite, including:

- Fixture schema, event ordering, original timestamps, and asynchronous replay.
- Calm, confused, bounded, early-warning, breadth, and time-decay CCS behavior.
- BKT correct/incorrect evidence, CCS soft evidence, SQLite round trips, restart loading, and session deltas.
- Strict GPT‑5.6 model selection and JSON schemas for both classification and nudge generation.
- One nudge per spike, calm suppression, and end-to-end runtime emission.
- Live input using the shared processor, API validation, SSE behavior, and visible UI tagging.
- Concurrent-session lifecycle and no-cross-talk checks.
- TalkMoves schema, counts, provenance, and sentiment proxy-agreement reporting.
- Nine-fixture CCS precision/recall and leakage-free pre-poll evaluation.
- Confidence-bucket calibration and explicit heuristic labeling.
- Matched control/reframed outcome linkage and `nudge_applied` propagation.
- ClassBank CHAT participants, time alignment, media metadata, conversion, catalog discovery, and production-runtime compatibility.

Codex also ran real-server smoke tests outside the in-process test client, exercised a configured GPT‑5.6 lesson replay, ran the TalkMoves sample through GPT‑5.6, checked JavaScript syntax, and regenerated the reports under [`validation/`](./validation/). I reviewed the reported boundaries rather than using passing tests as evidence of real-world classroom efficacy.

### Required Codex feedback reference

The Codex `/feedback` session ID for this collaboration is:

```text
019f6582-86b0-7f50-8b6a-9c00b666eff6
```

This ID identifies the Codex thread used for the implementation and evaluation collaboration described above.
