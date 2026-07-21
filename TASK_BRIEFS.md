# Codex Task Briefs — paste these in order, one per session/task

Do these in order. Each one should end with passing tests and a commit
before you start the next. Read AGENTS.md first if Codex hasn't already.

---

## Task 1 — Project scaffold + simulated live transcript stream

**Goal:** Set up the repo skeleton and a simulated live transcript feed
that plays back a pre-scripted class as if it's happening in real time.

**Context:** No real audio/speech-to-text — this is a scripted transcript
(teacher lines + student chat lines + timestamps + occasional poll
results) replayed on a timer to simulate a live stream. This is the input
every other component consumes.

**Constraints:**
- Python/FastAPI backend per AGENTS.md
- Write 2-3 sample scripted "classes" as JSON fixtures, each with at
  least one deliberate confusion moment (a concept where several student
  lines show confusion) so later components have something real to detect
- Expose the stream over a simple endpoint (WebSocket or SSE) that other
  components can subscribe to

**Definition of done:**
- Running the service replays a scripted class line-by-line with realistic
  timing
- At least one test confirms the stream emits lines in correct order with
  correct timestamps

---

## Task 2 — CCS (Confusion Confidence Score) engine

**Goal:** Build the live confusion-scoring engine described in
the original project design document §4.1.

**Context:** For each transcript window, compute a CCS score from:
sentiment (via GPT-5.6, Structured Outputs), keyword flags (simple rule
list), response latency (from timestamps), and poll-miss rate. Combine
with a weighted sum through a sigmoid, per the formula in §4.1.

**Constraints:**
- Sentiment classification is one Structured Outputs call per transcript
  line: `{"sentiment": "confused"|"neutral"|"positive", "confidence": 0-1}`
- Keyword flagging and latency/poll-miss math are plain code, no LLM
- Fusion formula and weights are plain code — hardcode reasonable initial
  weights, they don't need to be ML-trained for the demo
- Write the test first: e.g. "given a window with 3 confused-sentiment
  lines and 2 poll misses, CCS should be above 0.6"; "given a calm window
  with no confusion signals, CCS should be below 0.3"

**Definition of done:**
- CCS score computed and printed/logged live as the Task 1 stream plays
- Tests for at least: a clearly-confused window, a clearly-calm window,
  and the sigmoid bounds (never outputs outside [0,1])

---

## Task 3 — BKT (Bayesian Knowledge Tracing) engine

**Goal:** Build the per-student, per-concept mastery tracker from §4.2.

**Context:** Standard BKT update rules (given in §4.2) plus the CCS-as-
soft-evidence extension. Pure deterministic code — no LLM involved here.

**Constraints:**
- Implement `update_mastery(student_id, concept, correct: bool | None,
  ccs: float | None)` — either correctness evidence, CCS evidence, or both
  can be passed for a given update
- Explicit evidence (correct/incorrect) should move the estimate more than
  CCS soft evidence, per the λ weighting described in §4.2

**Definition of done (write these tests first):**
- Given 10 correct answers on a concept, mastery increases
- Given a repeated pattern of incorrect answers, mastery decreases and
  stays low
- Given sustained high CCS with no graded evidence yet, mastery estimate
  dips modestly (not as much as an explicit wrong answer would move it)
- All tests pass before moving to Task 4

---

## Task 4 — Live nudge generation

**Goal:** When CCS crosses a threshold for a concept, generate a short,
concrete re-explanation suggestion for the teacher.

**Context:** Uses GPT-5.6 with Structured Outputs. Should reference which
concept triggered it and why (cite the actual signals — e.g. "3 students
showed confusion language and 2 missed the poll question").

**Constraints:**
- Output schema: `{"concept": str, "trigger_reason": str, "suggested_
  reframing": str}`
- Trigger only once per confusion spike, not repeatedly every window
  while CCS stays high (avoid spamming the teacher)

**Definition of done:**
- A test simulating a CCS spike produces exactly one nudge with a
  non-generic, concept-specific suggestion
- A test simulating calm CCS produces no nudge

---

## Task 5 — Dashboard UI (this is the "coherent product experience" piece)

**Goal:** One screen tying everything together live: transcript feed, CCS
indicator, nudge alerts, per-student mastery table.

**Context:** This is what gets demoed — it needs to
look and feel like a real product, not a debug console. Keep it simple but
polished: a clean layout, a visible confusion-score gauge or line chart, a
clearly visible alert when a nudge fires, and a live-updating table of
student mastery per concept.

**Constraints:**
- Plain HTML/JS or minimal React, per AGENTS.md
- Connects to the backend stream from Task 1-4 and updates live, no manual
  refresh
- Should be presentable on camera for the demo video with zero setup
  beyond the one-command launch

**Definition of done:**
- `./run_demo.sh` (or equivalent) starts backend + frontend + the
  simulated class, and the dashboard updates live end-to-end with no
  manual steps
- Looks intentional, not like a debug page

---

## Task 6 — Backtest CCS/BKT against authored ground truth

**Goal:** Turn the hand-picked CCS weights and BKT priors from a plausible
heuristic into a validated-against-something claim, using data that
already exists in this repo.

**Context:** Each fixture in `data/classes/*.json` has at least one
deliberate confusion moment authored into the script — that's a known
ground-truth window. We haven't ever checked whether CCS actually crosses
threshold there and stays below it elsewhere. We also have poll results
after each confusion moment, which give a weak proxy label: did elevated
CCS actually predict the next poll miss in the same fixture?

**Constraints:**
- New script `scripts/backtest_ccs.py`, no changes to the deterministic
  math in `app/ccs.py` or `app/bkt.py` unless the backtest reveals a clear
  bug (don't retune weights just to make the backtest look good — report
  what's true)
- For each fixture: replay it, record CCS over time, compare against the
  authored confusion window (precision/recall — did it cross 0.6 inside
  the window, stay below outside it)
- Report whether a CCS spike predicted the subsequent poll miss in the
  same fixture, across all three fixtures
- Output a short markdown or JSON summary, not just console prints

**Definition of done:**
- Running the script against all three fixtures prints/writes a
  precision/recall style summary per fixture
- README gets a short "Validation" note linking to the summary, replacing
  the unqualified "hand-picked, not validated" limitation with what was
  actually checked and what still isn't (this is still not accuracy
  against real confusion labels — say so)

---

## Task 7 — Persist mastery across sessions (Teacher Memory Agent, scoped)

**Goal:** Answer "what happens next class" — mastery and nudge history
should survive a restart instead of resetting every run.

**Context:** `AGENTS.md` explicitly allows SQLite. `BKTTracker.states` in
`app/bkt.py` is in-memory only and dies with the process. This also
covers the original stretch idea of a Teacher Memory Agent (§4.3, style-tag
stats across sessions) but scoped down to what's demoable: persisted
mastery, not a separate style-tagging subsystem.

**Constraints:**
- New `app/memory.py` wrapping a SQLite file (e.g. `data/classpulse.db`),
  storing `(student_id, concept) -> MasteryState` plus a timestamp per
  update
- `BKTTracker` loads prior state on construction and `memory.py` persists
  on every `update_mastery` call (or on a short flush interval — pick
  whichever keeps `update_mastery`'s signature and return value unchanged)
- Dashboard mastery table shows a small delta/trend indicator ("+0.08
  since last session") when prior-session data exists for that student/
  concept; shows nothing extra on a first-ever run
- Must not break existing BKT tests — add new tests for load/persist
  round-trip instead of modifying `tests/test_bkt.py`'s existing cases

**Definition of done:**
- Running the same fixture twice in a row (restarting the server between
  runs) shows the second run's mastery table starting from the first
  run's ending values, with the delta visible in the UI
- Tests cover: state persists across a `BKTTracker` restart, and a
  first-ever run behaves identically to the current in-memory-only
  behavior

---

## Task 8 — Live (non-scripted) student input channel

**Goal:** Let the CCS pipeline run on at least one real, non-scripted
input stream during a live demo, without touching real audio/STT (still
out of scope).

**Context:** Teacher speech stays scripted — that's a separate, solved
problem, not this project's contribution. Student chat is the cheap real
part: a person can type live messages during the demo and they should
flow through the exact same `SignalWindow` / CCS path as replayed fixture
chat lines.

**Constraints:**
- Add a WebSocket (or POST) input endpoint in `app/main.py` that accepts
  `{student_id, text, timestamp}` and feeds it into the same event queue
  `app/runtime.py` already reads from — do not fork the CCS/BKT pipeline,
  live and replayed events must be indistinguishable downstream
- Dashboard gets a minimal "type as a student" input box, off by default,
  toggled on per session so scripted-only demos are unaffected
- Live-typed lines must be visually tagged in the transcript feed (e.g.
  "live" badge) so it's never confused with the scripted replay in a demo
  recording

**Definition of done:**
- With the live input box open, typed messages appear in the transcript,
  affect CCS, and can trigger a nudge exactly like scripted lines
- A test confirms a live-submitted event reaches the same CCS computation
  as a replayed one (same function, same code path)

---

## Task 9 — Multiple concurrent class sessions

**Goal:** Support more than one class running at once, so the product
story is "a school," not "one classroom on one screen."

**Context:** `runtime.py` and `main.py` currently assume a single global
running class. This task parameterizes that by `session_id` so multiple
independent replays (or live sessions from Task 8) can run side by side.

**Constraints:**
- `RuntimeLoop` (or equivalent in `app/runtime.py`) takes a `session_id`;
  `app/main.py` keeps a `dict[str, RuntimeLoop]` instead of one instance
- New routes: `POST /api/sessions` (start a session from a fixture),
  `GET /stream/{session_id}` (SSE for that session), `GET /api/sessions`
  (list active sessions with current CCS/concept for each)
- Add a landing page (or a mode on the existing one) listing active
  sessions with a mini CCS indicator per session, linking into the
  existing single-session dashboard unchanged
- Existing single-session behavior (`run_demo.ps1`/`.sh`) must keep
  working with zero extra steps — auto-create one default session if
  none specified, so the one-command demo path in `README.md` doesn't
  change

**Definition of done:**
- Two fixtures can be replayed concurrently in two browser tabs with
  independent CCS/mastery state and no cross-talk
- `./run_demo.sh` still launches straight into a single working dashboard
  with no manual session setup required
- Existing tests pass unchanged; new tests cover session isolation (two
  sessions' CCS/BKT state never leak into each other)

---

## Task 10 — Expand the CCS/BKT backtest fixture set

**Goal:** Strengthen the Task 6 backtest, whose precision/recall numbers
currently rest on only three authored fixtures.

**Context:** Both `README.md` and `validation/CCS_BACKTEST.md` already flag
this as the project's main open risk: "three authored fixtures... too
small for calibration, fairness, or deployment claims." Adding fixture
diversity doesn't prove real-world generalization, but it does test
whether the CCS thresholds hold up across more varied authored confusion
patterns than the current three.

**Constraints:**
- Add 5-10 new fixtures under `data/classes/` (or a validation-only
  fixture directory `scripts/backtest_ccs.py` can also load) covering
  scenarios not yet represented: slow-building confusion spread across
  many lines instead of one spike; false-alarm keyword use ("I'm not
  confused, right?"); confusion signaled only through poll misses with no
  confused-language chat; a fully calm lesson with no confusion window at
  all (a true-negative fixture)
- No changes to CCS/BKT weights unless the expanded backtest reveals a
  clear bug — same rule as Task 6: report what's true, don't retune to
  make the numbers look better
- Extend `scripts/backtest_ccs.py`'s existing precision/recall machinery
  to run across the full fixture set and report per-fixture and aggregate
  numbers; don't fork a second backtest script

**Definition of done:**
- `validation/CCS_BACKTEST.md` regenerated against the full fixture set
  (old 3-fixture numbers superseded, not silently dropped)
- README's CCS validation section and fixture-count caveat updated to
  match the new fixture count
- New fixtures pass the same fixture-catalog validation the existing
  three already have (per Task 1's stream tests); existing tests unchanged

---

## Task 11 — Cross-check the sentiment classifier against TalkMoves labels

**Goal:** Move the TalkMoves dataset from "proves the classifier runs on
realistic classroom language" to "the classifier's confused/neutral/
positive output is consistent with human-annotated discourse-move labels
on real transcripts."

**Context:** `app/real_data.py` already loads and validates the TalkMoves
TSVs (30,401 pairs). The README is explicit that this currently validates
language realism and ingestion, not classifier accuracy, because TalkMoves
carries discourse-move labels (e.g., student reasoning, making a claim),
not confusion labels. This task builds the closest available proxy check
without claiming more than the data supports.

**Constraints:**
- Pick a defensible mapping from a subset of TalkMoves' student talk-move
  labels to an expected sentiment direction (e.g., a label indicating
  uncertainty/clarification-seeking maps loosely to "confused"; a label
  indicating a confident claim maps loosely to "positive"). Document the
  mapping and its limitations up front in the script and the README — it
  is a proxy, not ground truth, and must be labeled as such everywhere
  it's reported
- Run `DemoStructuredProvider` (and `OpenAIStructuredProvider` if a key is
  available) over a sample of TalkMoves student utterances, compare
  against the proxy-mapped expected label, and report an **agreement
  rate** — not "accuracy," since the mapping itself is a judgment call
- New script `scripts/talkmoves_sentiment_check.py`, separate from the
  CCS/BKT backtest path; does not modify `classify_sentiment`'s behavior

**Definition of done:**
- Script outputs an agreement-rate report with the proxy mapping shown
  alongside the numbers so the caveat can't be missed
- README's "Real classroom data validation" section gains one paragraph
  distinguishing the existing ingestion/language-realism validation from
  this new proxy sentiment-agreement check, in the same non-overclaiming
  register as the rest of the doc

---

## Task 12 — Calibrate the CCS confidence score

**Goal:** Check whether `CCSEngine`'s confidence number actually tracks
empirical precision, using Task 10's expanded fixture set — and either fix
it or clearly flag it as still uncalibrated.

**Context:** `CCSResult.confidence` in `app/ccs.py` is currently
`min(.96, .5 + evidence_points * .05)` — a plausible-looking formula that
has never been checked against whether a "high confidence" score is
actually more often correct than a "low confidence" one.

**Constraints:**
- Using the Task 10 fixture set, bucket each confirmed/warning state by
  its reported confidence value and compute empirical precision within
  each bucket (a basic calibration table, not a full reliability diagram)
- If the current formula already tracks empirical precision reasonably,
  leave `app/ccs.py` unchanged and document the check. If it doesn't,
  adjust the formula's inputs (still using only fields already available,
  e.g. counting distinct signal types rather than raw evidence count) and
  re-run the Task 6/10 backtest to confirm precision/recall don't regress
- Add the calibration check as a repeatable script (or extend
  `scripts/backtest_ccs.py`) — don't hand-verify once and discard the method

**Definition of done:**
- A calibration table is produced and saved under `validation/`
- README states plainly whether confidence is calibrated or still a
  heuristic, replacing any precision the current unqualified formula implies
- Existing CCS tests (sigmoid bounds, weighting) pass unchanged

---

## Task 13 — Outcome-linked nudge validation

**Goal:** Check the one claim the project has never tested: does acting on
a nudge actually improve the next poll's correctness? Tasks 6/10 validate
*detection* timing; this validates whether the *response* helps.

**Context:** This is the gap flagged in the education-track review — CCS
and the nudge trigger are validated against authored ground truth, but
nothing in the repo checks whether following through on a nudge's
suggested reframing changes the outcome that follows it.

**Constraints:**
- There's no real classroom to run this against, so author matched
  fixture pairs under a new `data/outcome_pairs/` directory (don't touch
  the existing three demo fixtures or Task 10's set): for at least 2 of
  the 3 concepts, a **control** variant (unchanged) and a **reframed**
  variant where, right after the nudge-trigger point, the teacher line is
  rewritten to reflect the kind of reframing `generate_nudge` would
  produce for that concept, followed by an improved poll result at the
  same point in the timeline
- New script `scripts/backtest_nudge_outcome.py`: replay both arms of
  each pair, record poll correctness immediately following the
  nudge-trigger point, and report the control-vs-reframed delta per pair
  and in aggregate
- This is a small-n authored-script comparison, not a causal experiment —
  say so explicitly in both the script's output and the README, the same
  way Task 6/10 scope their claims
- Add a `nudge_applied` boolean to the replayed event/session data so the
  runtime and dashboard can visibly mark which arm is playing — useful
  scaffolding for a future live A/B on real sessions, not required to be
  wired into the live UI for this task

**Definition of done:**
- At least 2 matched control/reframed fixture pairs exist and replay
  cleanly through the existing runtime unchanged
- Running the script prints/writes per-pair and aggregate poll-correctness
  deltas
- README gets a short "Outcome validation" section stating exactly what
  was checked (does a scripted reframing change the next poll's
  correctness in these authored pairs) and what it does not establish
  (real teacher behavior, real student learning, a causal effect at scale)
- Existing fixtures, tests, and the one-command demo path are unchanged

---

## Task 14 — Import recorded live-class lessons from ClassBank

**Goal:** Let AhaLoop operate on authentic recorded classroom
transcripts rather than only authored demo fixtures, while preserving the
existing one-command demo and respecting ClassBank access rules.

**Context:** ClassBank TIMSS-Math provides real classroom video linked to
human transcripts in TalkBank CHAT format. The corpus requires a free
TalkBank account, compliance with the TalkBank Ground Rules, and the
corpus citation. Protected transcripts and media must not be redistributed
through this repository. This task integrates locally downloaded data; it
does not yet implement microphone capture or streaming speech-to-text.

**Constraints:**
- Parse time-aligned CHAT (`.cha`) transcripts without adding a heavyweight
  dependency; preserve teacher/student roles and millisecond media timing
- Import locally downloaded transcripts into `data/classbank/processed/`
  and discover them automatically alongside the three curated demos
- Retain corpus, media, citation, access URL, and source metadata on every
  imported lesson/session; visibly mark replayed turns as recorded
  ClassBank data rather than live microphone input
- Keep `data/classbank/raw/`, `data/classbank/media/`, and generated
  processed lessons ignored by Git; never commit protected classroom data,
  student identifiers, credentials, or media
- Imported turns must enter the existing runtime, CCS, BKT, session, and
  nudge path rather than creating a parallel analysis pipeline
- The original three-class API catalog and one-command demo must behave
  exactly as before when no local ClassBank files have been imported

**Definition of done:**
- `scripts/import_classbank.py` accepts CHAT files/directories, a concept,
  and an optional directory of matching audio/video files
- Imported lessons appear in the dashboard selector after restart and
  replay using recorded CHAT timestamps with `source=classbank`
- Transcript turns display a `RECORDED CLASSBANK` marker, while session
  data exposes source and provenance metadata
- `data/classbank/README.md` documents account registration, TIMSS-Math
  acquisition, citation, privacy, folders, and the import command
- Automated tests cover CHAT parsing, participant roles, timestamps,
  media metadata, conversion, and compatibility with `ScriptedClass`
- Real-server smoke test confirms an imported lesson is discovered and
  completes through SSE without changing the default demo catalog

**Implementation checkpoint:** Complete in commit `f75dd2d`; 48 tests
pass. The importer and replay integration are complete, but the protected
TIMSS-Math files themselves are not bundled and must be downloaded by an
authorized user.

---

## Task 15 — Live browser speech-to-text

Capture camera and microphone in the dashboard, record standalone six-second
audio windows, and send each window through the OpenAI Audio transcription API.
A live session stays open until the teacher stops capture. The API key remains
server-side and live turns use the same CCS/BKT/nudge runtime as replays.

## Task 16 — Speaker diarization

Use `gpt-4o-transcribe-diarize` with `diarized_json` and automatic chunking.
Map the configured speaker ID to Teacher; treat other identified speakers as
student transcript input. Preserve segment start/end offsets and speaker IDs.

## Task 17 — Teacher explanation-risk schema

Analyze every teacher transcript segment using GPT-5.6 Structured Outputs with
a strict schema for factual risk, clarity risk, possible issue, evidence, and a
suggested check. The deterministic demo provider implements the same type.

## Task 18 — Applied/dismissed nudge controls

Give every nudge an ID and show Applied/Dismissed controls. Persist the decision
in the in-memory session outcome tracker and expose it through the session API.

## Task 19 — Observed live outcome evaluation

Link each nudge to the first subsequent poll for the same concept, reporting
baseline correctness, next-poll correctness, and observed delta. Present this
as observational session evidence, not a causal claim.

**Implementation checkpoint:** Complete together as the live lecture extension;
the automated suite covers schemas, transcription payloads, diarized event
routing, decision validation, outcome linkage, API behavior, and live sessions.

---

## Winning-differentiation phase (complete in order)

These tasks strengthen the product itself, not the submission video or Devpost
packaging. They are deliberately narrower than the out-of-scope ClassroomOS
vision. Do not add a generic chatbot, lesson generator, cross-teacher memory,
or unvalidated claims merely to make the feature list longer.

## Task 20 — Close the intervention feedback loop

**Goal:** Make AhaLoop improve which kind of intervention it recommends
from the teacher's decision and the next observed poll, rather than only
recording those outcomes after the fact.

**Why this matters:** The distinctive product claim should be: AhaLoop not
only detects confusion and suggests an intervention; it records whether the
teacher applied it and whether the next check improved, then uses that evidence
when choosing a later intervention strategy in the same session.

**Constraints:**
- Define a small, explicit intervention taxonomy such as `visual_model`,
  `worked_example`, `contrast_case`, `analogy`, and `student_explanation`;
  put the selected `strategy` in the strict nudge Structured Output schema
- Keep strategy scoring deterministic and inspectable; GPT-5.6 writes the
  strategy-specific wording but does not calculate outcome statistics or pick
  winners from opaque free-form history
- Update strategy evidence only when a teacher has explicitly marked a nudge
  Applied or Dismissed and a later poll has been observed; pending nudges,
  dismissed nudges, and missing baselines must not be treated as successful
- Use within-session, per-concept evidence only. Do not build the out-of-scope
  cross-session Teacher Memory Agent or imply that one observation proves a
  strategy is effective
- With sparse or tied evidence, use a documented neutral/default exploration
  rule; never label a strategy "best" without sufficient observations
- Tests first, including applied/improved, applied/worse, dismissed, no-next-
  poll, sparse-data, and session-isolation cases

**Definition of done:**
- Every generated nudge has a typed strategy and a concise explanation of why
  that strategy was selected
- The outcome tracker exposes per-strategy attempts and observed deltas without
  causal language
- A second confusion spike can select a strategy using earlier valid evidence,
  and a deterministic integration test proves the full feedback loop
- The dashboard shows the selected strategy and a small "session evidence"
  summary that distinguishes exploration from evidence-informed selection

---

## Task 21 — Build a blinded educator nudge-evaluation workflow

**Goal:** Replace developer opinion about nudge quality with a reproducible way
for real educators to rate whether interventions are useful, safe, specific,
and feasible during a live lesson.

**Constraints:**
- Create an export script that produces a de-identified, randomized evaluation
  packet containing the concept, necessary transcript window, evidence, and
  nudge; hide provider name and whether the nudge came from GPT-5.6 or the
  deterministic baseline
- Use a fixed 1–5 rubric for instructional usefulness, specificity, factual
  correctness, classroom feasibility, and risk of harmful student labeling;
  include an optional short comment and an overall use/reject decision
- Create a separate import/report script for completed ratings. Report sample
  size, number of raters, per-dimension distributions, use rate, and inter-rater
  agreement when at least two educators rate overlapping items
- Never fabricate educator identities, ratings, quotes, or agreement. The agent
  may build and test the workflow with fixtures clearly labeled `synthetic_test`,
  but real results remain "not yet collected" until supplied by real reviewers
- Store no student names or protected classroom text in exported packets; use
  authored fixtures or properly authorized/de-identified excerpts only
- Do not make a network survey service or add authentication; portable JSON/CSV
  plus a simple local HTML rating form is sufficient

**Definition of done:**
- One command exports a randomized blinded packet and opens/runs a lightweight
  local rating form; another command validates and summarizes returned ratings
- Automated tests cover randomization reproducibility, provider blinding,
  schema validation, missing values, aggregation, and privacy-safe export
- `validation/EDUCATOR_NUDGE_EVALUATION.md` clearly separates workflow smoke-
  test results from authentic educator results
- README explains exactly how an educator can complete the evaluation in under
  ten minutes and how new real results should be regenerated

---

## Task 22 — Add held-out confusion annotation and evaluation

**Goal:** Create a credible path from authored-fixture behavior tests to
educator-labeled confusion evaluation on transcript windows the CCS developer
did not use while tuning thresholds.

**Constraints:**
- Build an annotation schema and local tool for educators to label transcript
  windows as `calm`, `possible_confusion`, `confirmed_confusion`, or
  `insufficient_context`, plus the evidence source and optional concept note
- Keep the held-out set physically and logically separate from calibration
  fixtures. The production thresholds must be frozen before evaluating a
  held-out batch; record the configuration hash in the report
- Exclude `insufficient_context` from primary precision/recall while reporting
  its count. Report confusion matrices, precision, recall, F1, false-alert
  timelines, and pre-poll performance without poll-result leakage
- Support agreement reporting for overlapping educator annotations and retain
  disagreements rather than silently resolving them in favor of the model
- Do not convert TalkMoves discourse labels into confusion ground truth and do
  not generate synthetic "human" labels. If no authentic annotations have
  been collected, ship the tested workflow and state that evaluation is pending
- Avoid committing protected transcripts or personally identifying information

**Definition of done:**
- Annotation export/import and evaluation commands are documented and tested
- The evaluator refuses calibration fixtures, malformed labels, leaked future
  poll outcomes, or a configuration hash mismatch
- A generated report labels the dataset provenance, rater count, held-out
  status, exclusions, metrics, limitations, and whether results are synthetic
  smoke tests or authentic educator annotations
- No deployment-accuracy or efficacy claim appears until authentic held-out
  annotations support it

---

## Task 23 — Harden educational-model validity and live reliability

**Goal:** Remove remaining modeling and runtime choices that could undermine
judge confidence even when the dashboard appears to work.

**Constraints:**
- Preserve the corrected evidence boundary: an individual chat may softly
  update only that speaker's mastery, an answer may update only that respondent,
  and class-wide CCS may trigger a class intervention but must never directly
  reduce every student's BKT state
- Do not lower mastery for positive or effectively neutral language merely
  because `confusion_probability` is nonzero; define and test a neutral zone or
  signed/thresholded student-language update with an explicit rationale
- Audit repeated soft updates so one utterance is applied exactly once and a
  persistent class-wide spike cannot compound individual mastery without new
  evidence from that student
- Move synchronous GPT-5.6 classification/generation work off the FastAPI event
  loop or use an async client, while preserving event order per session and
  isolation across concurrent sessions
- Add bounded timeout/error handling for sentiment, explanation-risk,
  transcription, and nudge generation. A failed optional model call must be
  visibly reported and must not fabricate a successful GPT-5.6 result
- Rename displayed CCS `confidence` to "evidence quality" everywhere unless
  Task 22 produces authentic calibration sufficient to justify probability-like
  language

**Definition of done:**
- Focused tests prove student-specific, once-only mastery updates for confused,
  neutral, positive, absent, and poll evidence
- A concurrency test proves one slow provider call does not freeze unrelated
  sessions, and timeout/provider-error tests prove honest degraded behavior
- Existing 0.40 warning and 0.60 confirmed behavior remains reproducible or any
  deliberate change is accompanied by regenerated validation reports
- Full automated suite and a real-server live-session smoke test pass

---

## Task 24 — Establish a distinctive product identity

**Goal:** Avoid confusion with the pre-existing Devpost education project named
the former working name and make the closed intervention-feedback loop recognizable in one
sentence.

**Blocking user decision:** Before implementation, present 3–5 researched,
available candidate names and concise positioning lines. Do not rename files,
UI, package metadata, or documentation until the user explicitly chooses one.

**Constraints:**
- Search Devpost, GitHub, common package registries, and the public web for each
  candidate; document collisions and treat this as a practical naming screen,
  not legal trademark clearance
- The positioning must foreground the differentiator delivered by Task 20:
  detect confusion, recommend an evidence-backed teaching move, observe the
  next check, and improve strategy selection
- Once approved, update product-facing text consistently without renaming the
  internal Python `app` package or breaking API paths unnecessarily
- Preserve dataset attribution and do not copy visual identity or language from
  another education product

**Definition of done:**
- User-approved name and one-sentence positioning replace the former name across UI,
  README, demo fixtures' presentation metadata, API title, and launch docs
- A repository search finds no stale user-facing former-name branding except a
  migration note acknowledging the former name
- All tests and the one-command demo pass after the rename

---

## Task 25 — Verify nudge implementation and extend the judged demo

**Goal:** Distinguish displaying a suggestion from observing that the teacher
actually used it, and give the presenter enough time to demonstrate the full
closed loop.

**Requirements:**
- Add a longer curated presentation fixture with baseline confusion, a nudge,
  subsequent teacher speech that implements the move, and a follow-up poll
- Verify subsequent teacher speech against the exact suggested strategy using
  GPT-5.6 Structured Outputs
- Return an implementation status, confidence, supporting transcript quote,
  and rationale; never infer success merely because the nudge was displayed
- Keep teacher confirmation/correction controls because automatic verification
  is evidence, not final authority
- Treat implementation verification and next-poll outcome as separate facts
- Expose the verification in the live event stream, nudge panel, and outcome table

**Definition of done:**
- The extended fixture emits a nudge, verified implementation, baseline poll,
  follow-up poll, and observed delta
- A model failure is visible and does not fabricate implementation
- Full tests, JavaScript checks, and a real-server presentation smoke test pass

---

## Task 26 — Add a two-person live demonstration call

**Goal:** Let one teacher and one student join the same browser call so the live
audio pipeline can be demonstrated without an external meeting product.

**Requirements:**
- Use browser-native WebRTC for peer-to-peer media and a FastAPI WebSocket only
  for offer/answer/ICE signaling
- Enforce a hard maximum of two participants per in-memory room
- Provide teacher room creation, student join-by-code, local/remote video, call
  status, and leave controls
- Mix both call audio streams into the existing chunked transcription path in
  the teacher browser; do not create a separate analysis implementation
- Document localhost/HTTPS, privacy, authentication, and TURN limitations

**Definition of done:**
- Two signaling clients exchange messages and a third participant is rejected
- The teacher can start the existing live lecture analysis after the peer joins
- Full tests, JavaScript checks, and a real WebSocket server smoke test pass

---

## Task 27 — Separate the live meeting from the analytics dashboard

**Goal:** Give the two-person class its own meeting page and keep real-time
teacher guidance visible alongside the call.

**Requirements:**
- Move call creation/join/video controls from the main dashboard to `/call`
- Keep the main dashboard linked to the meeting without embedding it
- Show teacher-only live transcript, CCS, mastery, explanation risk, nudges,
  implementation verification, and poll controls beside the videos
- Give the student role a call-focused layout without teacher guidance
- Reuse the existing live session, audio chunk, SSE, decision, and poll APIs

**Definition of done:**
- `/` contains a call link but no embedded call controls
- `/call` contains the two-person meeting and teacher insight surfaces
- Full tests, frontend syntax checks, and a fresh-server route smoke pass

---

## Task 28 — Generate and administer learning checks with GPT-5.6

**Goal:** Remove teacher-authored poll composition from the live loop while
preserving a measurable baseline and follow-up outcome.

**Requirements:**
- Use GPT-5.6 Structured Outputs to create a three-option conceptual baseline
  check when a nudge fires and a transfer check after verified implementation
- Require exactly one correct answer, an explanation, and a statement of what
  the item checks
- Relay options to the student call view without exposing the correct index
- Grade the student's selection in the teacher browser and submit correctness
  through the existing poll/BKT/outcome API
- Show generated questions, stage, provider, response, and explanation to the teacher
- Remove manual poll-composer controls from both live product surfaces

**Definition of done:**
- Neither `/` nor `/call` asks the teacher to write a poll question
- Student responses enter the existing deterministic outcome pipeline
- Structured-schema, runtime-event, signaling, UI, and full-suite tests pass

---

## Task 29 — Deploy the two-person demo on a free HTTPS host

**Goal:** Make the teacher/student call reachable from separate physical devices
without charging for the web host.

**Requirements:**
- Deploy the FastAPI UI, API, SSE, and WebSocket signaling as one Render service
- Select the free instance and bind Uvicorn to Render's `$PORT`
- Keep `OPENAI_API_KEY` in host-managed secrets, never in source control
- Use the existing origin-relative HTTPS/WSS browser connections
- Document free-tier cold starts, ephemeral state, OpenAI usage cost, and the
  STUN-only connectivity limitation

**Definition of done:**
- A checked-in Blueprint defines build, start, health-check, secret, and free plan
- Tests protect the deployment command and secure-WebSocket behavior
- README gives teacher/student deployment and joining instructions
- Full tests and a local health/route smoke test pass

---

## Task 30 — Package AhaLoop for AWS ECS

**Goal:** Run the complete live-call application as a secure production
container suitable for a single-task ECS service.

**Requirements:**
- Build from a slim pinned Python base and install locked application requirements
- Run Uvicorn as a non-root user on container port 8000
- Include the application, browser assets, fixtures, and real-data evidence
- Exclude local secrets, databases, protected downloads, and development files
- Provide an application-aware container health check
- Document ECS port mapping, ALB HTTPS/WebSockets, secrets, persistence, outbound
  access, and the current single-task constraint

**Definition of done:**
- `Dockerfile` and `.dockerignore` are checked in and covered by tests
- The image never embeds `OPENAI_API_KEY`
- Full application tests pass
- If Docker is unavailable locally, that unverified image-build boundary is
  reported explicitly

---

## Stretch tasks (only if Tasks 1-30 are done and fully working with time left)

- §4.2b Independent Outcome Verification: one follow-up check question,
  graded separately from CCS, feeding a real evidence point into BKT
- Full Teacher Memory Agent (§4.3): style-tag stats across sessions,
  beyond the mastery persistence already covered by Task 7

Do not start these until the core tasks are solid — a fully working
core loop beats a partially working full system for judging.
