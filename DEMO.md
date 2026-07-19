# ClassPulse demo script (3–4 minutes)

## Start

Run `./run_demo.ps1`. The browser opens and the Fractions class begins automatically. Point to the intelligence badge: it honestly identifies GPT‑5.6 or the deterministic demo fallback.

## Watch the stream

Teacher speech, student chat, response latency, and a poll arrive in timestamp order. Explain that this simulates an online-class transcript and poll feed; raw audio is deliberately out of scope.

## Show confusion detection

As several students express denominator confusion and miss the poll, the CCS gauge rises. Its four component bars expose sentiment, keyword, latency, and poll evidence. The score is deterministic and bounded by a weighted sigmoid.

## Show the nudge

At `CCS ≥ 0.60`, one alert recommends equal-sized fraction bars. Expand “Why this fired” to show signal counts and limitations. Note that the spike gate prevents repeat alerts while confusion remains high.

## Show student mastery

The poll updates each student explicitly, while CCS supplies weaker soft evidence. The BKT table changes without refresh and exposes evidence counts and confidence.

## Switch scenarios

Choose Photosynthesis or Forces. The stream restarts with a different concept and deliberate confusion moment. Finish with: “ClassPulse helps the teacher see confusion, understand the evidence, and act before the lesson moves on.”
