# Held-out confusion evaluation

Status: **annotation workflow tested; authentic held-out educator annotations
not yet collected**.

Export a physically separate, authorized and de-identified batch:

`py scripts/heldout_confusion.py export heldout-windows.json annotation-packet.json`

Each educator returns labels (`calm`, `possible_confusion`,
`confirmed_confusion`, or `insufficient_context`) with a rater code, evidence
source, and optional concept note. Evaluate without resolving disagreements:

`py scripts/heldout_confusion.py evaluate annotation-packet.json annotations.json heldout-report.json`

The exporter freezes a hash of production CCS parameters and refuses demo or
calibration fixture paths, TalkMoves proxy provenance, and windows containing a
future poll outcome. The evaluator refuses a hash mismatch. It reports primary
confusion matrices, precision, recall, F1, false alerts, insufficient-context
exclusions, pre-poll metrics, overlap agreement, disagreements, provenance, and
limitations. No deployment-accuracy claim is supported until authentic held-out
annotations exist.
