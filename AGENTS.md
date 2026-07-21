# AGENTS.md — Nalmai Build

## What this project is
Nalmai detects when students are getting confused during a live online
class and nudges the teacher in real time on how to fix it, while tracking
each student's evolving mastery per concept. Full design reference:
the project design document in this repo — read it once for context,
but the scope below is what actually gets built first.

## Scope discipline — read this before doing anything else
Scope is deliberately cut down from the full design doc to a buildable
first version. Do not build anything outside "In scope" below unless
explicitly asked in a task prompt, even if the design doc describes it.

## In scope for this build
1. Simulated live transcript stream (teacher speech-to-text + student chat,
   pre-scripted with timestamps, played back as if live — this stands in
   for real audio capture, which is out of scope here)
2. CCS (Confusion Confidence Score) engine — fuses sentiment, keyword
   flags, response latency, and poll-miss rate into one live score
3. BKT (Bayesian Knowledge Tracing) engine — per-student, per-concept
   mastery tracking, pure deterministic code, no LLM calls inside it
4. Live nudge generation — fires when CCS crosses a threshold, uses
   GPT-5.6 to draft the re-explanation suggestion
5. Dashboard UI — the single screen that ties all of the above together
   live: transcript feed, CCS indicator, nudge alerts, mastery table
6. Browser camera/microphone capture with chunked streaming speech-to-text
   and speaker diarization
7. Teacher explanation-risk analysis, nudge decisions, and observed
   next-poll outcome tracking

## Explicitly OUT of scope — do not build these
- Teacher Memory Agent persistence across multiple sessions
- End-of-session demo lesson generator
- Multi-teacher or multi-class support
- Any database beyond in-memory or SQLite

If a task prompt doesn't mention one of these, assume it's still out of
scope — ask rather than build it speculatively.

## Tech stack (keep consistent across all tasks)
- Backend: Python (FastAPI) — pick this and don't switch mid-build
- Frontend: plain HTML/JS or a minimal React app — no build-heavy framework
- LLM calls: OpenAI Responses API, model `gpt-5.6`, Structured Outputs
  (JSON schema, strict mode) for every classification call — never parse
  freeform text from a model response
- Data: in-memory Python objects or SQLite — no external services

## Conventions for every task
- **Tests first.** For each function with defined behavior (especially the
  BKT and CCS math), write the test, confirm it fails, then implement
  until it passes. Don't modify a test to make it pass — fix the code.
- Deterministic math (BKT updates, CCS fusion formula) is plain code, not
  an LLM call. LLM calls are only for classification/generation tasks
  (sentiment, style tagging, nudge text).
- Every LLM call uses Structured Outputs with an explicit JSON schema.
- Commit after each task completes, with a message describing what was
  built and why.
- Keep the whole thing runnable with one command (e.g. `./run_demo.sh`)
  that starts backend + frontend + the simulated transcript stream.

## Definition of done for the full build
- One command launches the whole demo end-to-end, no manual steps
- Dashboard shows, live: transcript scrolling in, CCS score per current
  concept, a nudge alert box when triggered, and a per-student mastery
  table updating in real time
- All tests pass
- README explains setup, what's simulated vs. real, and where Codex was
  used for which part
