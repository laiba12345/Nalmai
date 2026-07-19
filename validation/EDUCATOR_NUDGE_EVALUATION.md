# Educator nudge evaluation

Status: **workflow tested; authentic educator results not yet collected**.

The exporter randomizes items with a recorded seed, removes provider identity,
rejects direct identifier fields, and accepts only authored, synthetic-test, or
explicitly authorized/de-identified material. Educators rate usefulness,
specificity, factual correctness, classroom feasibility, and labeling safety
from 1–5, then make an overall use/reject decision.

Run `py scripts/educator_nudge_evaluation.py source-items.json packet.json`,
open `validation/educator_rating_form.html`, load the packet, and download the
completed ratings. Summarize with
`py scripts/report_educator_ratings.py educator-ratings.json report.json`.

Automated fixtures are marked `synthetic_test` and validate only the workflow.
No educator identities, quotes, ratings, quality claims, or agreement results
have been fabricated. Real results remain pending until actual educators return
completed packets.
