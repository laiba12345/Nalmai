# AhaLoop — three-minute presentation

## Before recording

1. Put an OpenAI API key in `.env` and run `./run_demo.ps1`.
2. Confirm the badge says **GPT-5.6 · Structured Outputs**.
3. Press **Present demo** immediately before recording.

## 0:00–0:25 — Problem and promise

Say:

> Teachers usually discover confusion after the lesson has moved on. AhaLoop listens to live classroom evidence, detects when understanding breaks down, recommends a teaching move, and checks whether that move worked.

Point to the four-step guide and add: “This is not a chatbot. It is a closed intervention-feedback loop.”

## 0:25–0:55 — Live input

Point to the transcript as the fraction lesson begins.

> The production input is chunked microphone audio with speech-to-text and speaker diarization. For a reliable three-minute demo, this scenario replays the same typed teacher, student, latency, and poll events at live timestamps.

Point to the intelligence badge:

> GPT-5.6 classifies student language and teacher explanation risks through strict Structured Outputs. No free-form model response is parsed.

## 0:55–1:25 — Detect confusion

When student messages arrive, point to the CCS panel.

> AhaLoop combines student language, confusion keywords, response latency, breadth across learners, and poll misses. The score is deterministic and exposes its evidence. It is a class intervention signal, not a diagnosis or an automatic penalty to every student.

Briefly point to mastery: “Individual mastery changes only from evidence belonging to that learner.”

## 1:25–2:05 — Recommend and decide

When the nudge appears, point to its strategy and evidence.

> Once corroborated confusion crosses the threshold, GPT-5.6 drafts one short, strategy-specific re-explanation. Here it recommends a visual model instead of simply repeating the rule.

Click **Applied**.

> The teacher remains in control. AhaLoop records whether the suggestion was applied or dismissed; showing a nudge is not treated as success.

## 2:05–2:35 — Observe the outcome

When the final poll arrives, scroll to **Observed outcomes** if necessary.

> AhaLoop links the applied teaching move to the next poll. Understanding rises from the earlier poll to the follow-up check. This is observational session evidence—not a causal claim—but it gives the system evidence about which strategy to try next.

## 2:35–2:55 — Why it is credible

> The application has 83 automated tests, held-out annotation and blinded educator-evaluation workflows, and language ingestion validated against more than 30,000 TalkMoves utterance pairs. CCS and Bayesian Knowledge Tracing are deterministic; GPT-5.6 is used where language reasoning and generation are needed.

## 2:55–3:00 — Finish

> AhaLoop helps a teacher see confusion, act before the lesson moves on, and learn which intervention works best.

Stop recording. Do not add a second scenario, architecture tour, or live microphone experiment to the submitted video.
