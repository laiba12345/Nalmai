# AhaLoop demo script (3–4 minutes)

## Start

Run `./run_demo.ps1`. The browser opens and the Fractions class begins automatically. Point to the intelligence badge: it honestly identifies GPT‑5.6 or the deterministic demo fallback.

## Watch the stream

Teacher speech, student chat, response latency, and a poll arrive in timestamp order. Explain that this simulates an online-class transcript and poll feed; raw audio is deliberately out of scope.

Open **Live student**, type a message such as “I’m confused about why eight is not bigger,” and send it. The visibly tagged message enters the same sentiment, CCS, BKT, and nudge path as scripted chat—this part of the input is genuinely live.

## Show confusion detection

As several students express denominator confusion and miss the poll, the CCS gauge rises. Its four component bars expose sentiment, keyword, latency, and poll evidence. The score is deterministic and bounded by a weighted sigmoid.

## Show the nudge

At `CCS ≥ 0.60`, one alert recommends equal-sized fraction bars. Expand “Why this fired” to show signal counts and limitations. Note that the spike gate prevents repeat alerts while confusion remains high.

## Show student mastery

The poll updates each student explicitly, while CCS supplies weaker soft evidence. The BKT table changes without refresh and exposes evidence counts and confidence. Replay the class or restart the server: mastery begins from the SQLite-persisted ending state and shows a “since last session” trend.

## Switch scenarios

Choose Photosynthesis or Forces. The stream restarts with a different concept and deliberate confusion moment.

Open the dashboard in a second tab and start another scenario. The **Active classes** strip shows both session IDs, concepts, CCS values, and status. Each tab streams only its own transcript and mastery state.

## Show real-data evidence

Scroll to **Real-data validation**. Show that AhaLoop loads 30,401 official TalkMoves teacher/student utterance pairs and their discourse annotations. Point out the source license and boundary: real classroom language validates ingestion and discourse coverage, while the scripted streams provide known confusion, latency, and poll ground truth.

Finish with: “AhaLoop helps the teacher see confusion, understand the evidence, act before the lesson moves on, and learn which intervention works best.”
