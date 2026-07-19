# TalkMoves real-data validation subset

Source: [SumnerLab/TalkMoves](https://github.com/SumnerLab/TalkMoves)  
Paper: [The TalkMoves Dataset](https://arxiv.org/abs/2204.09652)  
License: **CC BY-NC-SA 4.0**; the complete license text is included as `LICENSE`.

This directory contains the official, unmodified public test TSVs:

- `test_teacher.tsv`: teacher utterance pairs and teacher talk-move labels.
- `test_student.tsv`: student utterance pairs and student talk-move labels.

AhaLoop uses them to validate ingestion of real, anonymized K–12 mathematics classroom language and report talk-move coverage. They do **not** contain CCS confusion labels, poll correctness, response latency, or mastery ground truth. Synthetic fixtures remain necessary for deterministic end-to-end confusion demonstrations.

When redistributing or adapting these files, retain attribution, noncommercial use, and share-alike terms required by the source license.
