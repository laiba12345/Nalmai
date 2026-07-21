# ClassBank local data

ClassBank transcripts and media are not redistributed in this repository. They require a free TalkBank account and remain subject to the [TalkBank Ground Rules](https://talkbank.org/share/rules.html) and each corpus's citation requirements.

## Acquire TIMSS-Math

1. Register or sign in at [ClassBank](https://talkbank.org/class/).
2. Open the [TIMSS-Math corpus](https://talkbank.org/class/access/TIMSS-Math/TIMSS-Math.html).
3. Download one country's CHAT transcripts and, if needed, the corresponding media.
4. Place transcripts under `data/classbank/raw/` and media under `data/classbank/media/`.

The TIMSS-Math corpus requires citation of Stigler, J. W., Gallimore, R., and Hiebert, J. (2000), *Using video surveys to compare classrooms and teaching across cultures: Examples and lessons from the TIMSS and TIMSS-R video studies*.

## Import

```powershell
py scripts/import_classbank.py data/classbank/raw --concept mathematics --media-dir data/classbank/media
```

Imported JSON is written to `data/classbank/processed/`. Restart Nalmai; imported lessons then appear beside the authored demos and replay using their recorded CHAT timestamps. Their events are marked with source `classbank` and retain corpus, media, access, and citation metadata.

The importer does not upload recordings. Do not commit raw media, protected transcripts, imported JSON, student identifiers, or credentials.
