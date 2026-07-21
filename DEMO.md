# Nalmai — three-minute presentation

## Before recording

1. Put an OpenAI API key in `.env` and run `./run_demo.ps1`.
2. Confirm the badge says **GPT-5.6 · Structured Outputs**.
3. Press **Present demo** immediately before recording.

## 0:00–0:25 — Problem and promise

Say:

> Teachers usually discover confusion after the lesson has moved on. Nalmai listens to live classroom evidence, detects when understanding breaks down, recommends a teaching move, and checks whether that move worked.

Point to the four-step guide and add: “This is not a chatbot. It is a closed intervention-feedback loop.”

## 0:25–0:55 — Live input

Point to the transcript as the teacher gives a normal explanation without asking students a question.

> The production input is chunked microphone audio with speech-to-text and speaker diarization. For a reliable three-minute demo, this scenario replays the same typed events at live timestamps. Notice that the teacher has not asked a question—students begin expressing confusion spontaneously while the explanation continues.

Point to the intelligence badge:

> GPT-5.6 classifies student language and teacher explanation risks through strict Structured Outputs. No free-form model response is parsed.

## 0:55–1:25 — Detect confusion

First point to **Teacher Explanation Risk** when the unsupported rule is detected. Then, as unsolicited student messages arrive before any poll, point to the CCS panel.

> Nalmai first identifies that the explanation may create confusion because a rule was stated without conceptual support. Student language then independently confirms a problem before any formal check. The later poll corroborates the signal; it does not create it. CCS is deterministic and exposes its evidence.

Briefly point to mastery: “Individual mastery changes only from evidence belonging to that learner.”

## 1:25–2:05 — Recommend and decide

When the nudge appears, point to its strategy and evidence.

> Once corroborated confusion crosses the threshold, GPT-5.6 drafts one short, strategy-specific re-explanation. Here it recommends a visual model instead of simply repeating the rule.

Do not click either decision button yet. Wait for the next teacher segment.

> Showing a nudge is not treated as success. Nalmai checks subsequent teacher speech for observable evidence that the recommended strategy was actually used.

When **Implementation: implemented** appears, point to its evidence quote and confidence:

> GPT-5.6 found the recommended fraction-bar strategy in the teacher's later explanation. The teacher can confirm or correct this judgment, so the model is not the final authority.

## 2:05–2:35 — Observe the outcome

When the final poll arrives, scroll to **Observed outcomes** if necessary.

> Nalmai separately links the verified teaching move to the next poll. Understanding rises from the earlier poll to the follow-up check. Implementation evidence answers “did the teacher do it?”; the poll answers “what happened next?” This remains observational evidence, not a causal claim.

## 2:35–2:55 — Why it is credible

> The application has 104 automated tests, held-out annotation and blinded educator-evaluation workflows, and language ingestion validated against more than 30,000 TalkMoves utterance pairs. CCS and Bayesian Knowledge Tracing are deterministic; GPT-5.6 is used where language reasoning and generation are needed.

## 2:55–3:00 — Finish

> Nalmai helps a teacher see confusion, act before the lesson moves on, and learn which intervention works best.

Stop recording. Do not add a second scenario, architecture tour, or live microphone experiment to the submitted video.

## Optional two-person live-call rehearsal

Use this for a live judge conversation, not the deterministic submitted video:

1. Open the dedicated call page in two browser windows at `http://127.0.0.1:8004/call`.
2. In the teacher window, click **Create as teacher**. A six-character room code appears.
3. Enter that code in the second window and click **Join as student**.
4. Wait until both windows show the remote participant and `2/2 participants`.
5. Use headphones to prevent speaker echo.
6. In the teacher window only, click **Start analysis**. Both call audio streams now enter the existing transcription and diarization pipeline. Keep the teacher insight column visible: it shows CCS, mastery, explanation risk, transcript, and GPT-5.6 suggestions during the meeting.
7. Let the teacher explain normally. The student should interrupt naturally with “Wait, I am confused about why a larger denominator makes a smaller piece.”
8. When the nudge fires, GPT-5.6 automatically creates a baseline check in the student window. Let the student answer, teach the suggested strategy, and let the student answer the automatically generated transfer check.
9. Use **Leave** in both windows when finished.

For two physical devices, deploy behind HTTPS first; browser camera and microphone access is normally blocked on a non-localhost HTTP origin.
