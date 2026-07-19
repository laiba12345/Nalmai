# ClassPulse

ClassPulse is a focused real-time teaching copilot. It replays a simulated online class, fuses live confusion signals into a Confusion Confidence Score (CCS), updates per-student concept mastery with Bayesian Knowledge Tracing (BKT), and produces one concrete teacher nudge when confusion crosses a threshold.

This repository follows `AGENTS.md` and implements Tasks 1–5 in `TASK_BRIEFS.md`. The broader earlier ClassroomOS simulator is intentionally not part of this scoped build.

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
3. CCS combines confused sentiment, keyword flags, response latency, and poll-miss rate with a deterministic weighted sigmoid.
4. Explicit poll correctness updates BKT strongly. CCS contributes lower-weight soft evidence.
5. When CCS first crosses `0.60`, the nudge engine calls GPT‑5.6 with strict Structured Outputs. It does not fire again until the score falls below the reset threshold.
6. The single dashboard updates through Server-Sent Events without refresh: transcript, CCS gauge/components, nudge, and mastery table.

## GPT‑5.6 configuration

Set `OPENAI_API_KEY` before launching. With a key, `CLASSPULSE_LLM_MODE=auto` selects the real Responses API adapter using model `gpt-5.6` and strict JSON schemas for both sentiment and nudge calls.

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
- `app/llm.py`: strict schemas, OpenAI Responses adapter, and labeled demo provider.
- `app/nudges.py`: threshold crossing and once-per-spike suppression.
- `app/runtime.py`: coherent event-to-CCS-to-BKT-to-nudge loop.
- `app/main.py`: FastAPI, SSE endpoint, health/catalog APIs, and static dashboard.
- `public/`: responsive single-screen live product UI.
- `data/classes/`: three scripted classes with deliberate confusion moments.

## Testing

```powershell
py -m pytest
```

The suite verifies event order/timestamps, all three fixtures, calm/confused CCS, sigmoid bounds, BKT correctness and CCS soft-evidence weighting, both strict OpenAI schemas, one nudge per spike, calm suppression, full runtime integration, SSE delivery, APIs, and required dashboard surfaces.

## Simulated versus real

| Component | Status |
|---|---|
| Teacher speech-to-text, student chat, poll timing | Pre-scripted simulation |
| Sentiment and nudge generation | Real GPT‑5.6 when configured; visibly labeled deterministic fallback otherwise |
| Keyword, latency, poll, CCS fusion | Real deterministic computation |
| BKT mastery | Real deterministic probabilistic computation |
| Browser updates | Real SSE stream |
| Raw audio, database, multiple classes/teachers, memory agent | Out of scope |

## Limitations

- Fixtures replace real audio and platform integrations.
- Initial CCS weights and BKT parameters are expert defaults, not trained on deployment data.
- CCS observes language, latency, and polls, not tone, facial expression, or silence quality.
- Mastery is an estimate based on current evidence, never a diagnosis or fixed student trait.
- Automated tests mock the Responses transport; a live GPT‑5.6 call requires the user’s valid API key and account access.

Codex was used to implement the FastAPI/SSE service, deterministic math, typed OpenAI boundary, test suite, fixtures, dashboard, launch scripts, and documentation.
