# TalkMoves sentiment proxy agreement

> **Proxy only—not confusion ground truth and not classifier accuracy.** TalkMoves annotates discourse moves, not learning-state sentiment. The mapping is a documented judgment used to check directional consistency.

## Proxy mapping

| TalkMoves student label | Expected direction | Rationale |
|---|---|---|
| Asking for more information (2) | confused | A clarification request can weakly proxy uncertainty. |
| Making a claim (3) | neutral | A claim alone does not establish understanding or confusion. |
| Providing evidence (4) | positive | An explanation can weakly proxy confident understanding. |

Labels 0 (no talk move) and 1 (relating to another student) are excluded because neither has a defensible sentiment direction.

## Results

| Provider | Samples | Agreements | Agreement rate |
|---|---:|---:|---:|
| deterministic-demo-fallback | 15 | 6 | 0.400 |
| gpt-5.6 | 15 | 10 | 0.667 |

### deterministic-demo-fallback

| TalkMoves label | Proxy | Agreement | Predictions |
|---|---|---:|---|
| Asking for more information | confused | 0.000 | `{"neutral": 5}` |
| Making a claim | neutral | 0.800 | `{"confused": 1, "neutral": 4}` |
| Providing evidence | positive | 0.400 | `{"neutral": 3, "positive": 2}` |

### gpt-5.6

| TalkMoves label | Proxy | Agreement | Predictions |
|---|---|---:|---|
| Asking for more information | confused | 1.000 | `{"confused": 5}` |
| Making a claim | neutral | 0.800 | `{"confused": 1, "neutral": 4}` |
| Providing evidence | positive | 0.200 | `{"confused": 2, "neutral": 2, "positive": 1}` |

## Interpretation limits

Agreement means the classifier output matched this proxy mapping. It does not mean the student was truly confused, neutral, or understanding; it does not measure classroom efficacy, calibration, subgroup fairness, or causal validity.

## Machine-readable detail

```json
[
  {
    "provider": "deterministic-demo-fallback",
    "samples": 15,
    "agreements": 6,
    "agreement_rate": 0.4,
    "by_label": {
      "2": {
        "talkmove_name": "Asking for more information",
        "proxy_expected": "confused",
        "samples": 5,
        "agreements": 0,
        "agreement_rate": 0.0,
        "predictions": {
          "neutral": 5
        }
      },
      "3": {
        "talkmove_name": "Making a claim",
        "proxy_expected": "neutral",
        "samples": 5,
        "agreements": 4,
        "agreement_rate": 0.8,
        "predictions": {
          "neutral": 4,
          "confused": 1
        }
      },
      "4": {
        "talkmove_name": "Providing evidence",
        "proxy_expected": "positive",
        "samples": 5,
        "agreements": 2,
        "agreement_rate": 0.4,
        "predictions": {
          "positive": 2,
          "neutral": 3
        }
      }
    },
    "comparisons": [
      {
        "talkmove_label": "2",
        "talkmove_name": "Asking for more information",
        "proxy_expected": "confused",
        "context": "If this is 25 Maddox what did you do to figure out what 55 would be",
        "utterance": "We need 25  the half of 25 so what should be 15",
        "predicted": "neutral",
        "confusion_probability": 0.15,
        "agrees": false
      },
      {
        "talkmove_label": "2",
        "talkmove_name": "Asking for more information",
        "proxy_expected": "confused",
        "context": "Rylee whats still confusing you",
        "utterance": "I just dont know how I got done",
        "predicted": "neutral",
        "confusion_probability": 0.15,
        "agrees": false
      },
      {
        "talkmove_label": "2",
        "talkmove_name": "Asking for more information",
        "proxy_expected": "confused",
        "context": "You should have some points that are exact that you are talking about",
        "utterance": "I had a question about number one",
        "predicted": "neutral",
        "confusion_probability": 0.15,
        "agrees": false
      },
      {
        "talkmove_label": "2",
        "talkmove_name": "Asking for more information",
        "proxy_expected": "confused",
        "context": "Is X5 a factor",
        "utterance": "Why do we synthetic division",
        "predicted": "neutral",
        "confusion_probability": 0.15,
        "agrees": false
      },
      {
        "talkmove_label": "2",
        "talkmove_name": "Asking for more information",
        "proxy_expected": "confused",
        "context": "Yes",
        "utterance": "Can you show how to solve that one Ms",
        "predicted": "neutral",
        "confusion_probability": 0.15,
        "agrees": false
      },
      {
        "talkmove_label": "3",
        "talkmove_name": "Making a claim",
        "proxy_expected": "neutral",
        "context": "60 times 800",
        "utterance": "804 80000 48000",
        "predicted": "neutral",
        "confusion_probability": 0.15,
        "agrees": true
      },
      {
        "talkmove_label": "3",
        "talkmove_name": "Making a claim",
        "proxy_expected": "neutral",
        "context": "Its 112 bigger than two thirds",
        "utterance": "A little bit",
        "predicted": "neutral",
        "confusion_probability": 0.15,
        "agrees": true
      },
      {
        "talkmove_label": "3",
        "talkmove_name": "Making a claim",
        "proxy_expected": "neutral",
        "context": "What are the dimensions of this rectangle",
        "utterance": "26 x 34",
        "predicted": "neutral",
        "confusion_probability": 0.15,
        "agrees": true
      },
      {
        "talkmove_label": "3",
        "talkmove_name": "Making a claim",
        "proxy_expected": "neutral",
        "context": "One two three",
        "utterance": "Three",
        "predicted": "neutral",
        "confusion_probability": 0.15,
        "agrees": true
      },
      {
        "talkmove_label": "3",
        "talkmove_name": "Making a claim",
        "proxy_expected": "neutral",
        "context": "What does that mean and why is that important",
        "utterance": "I think it means like how many inches they are",
        "predicted": "confused",
        "confusion_probability": 0.58,
        "agrees": false
      },
      {
        "talkmove_label": "4",
        "talkmove_name": "Providing evidence",
        "proxy_expected": "positive",
        "context": "Why not 80",
        "utterance": "Because 80 wouldnt work because theres 2 zeros added",
        "predicted": "positive",
        "confusion_probability": 0.08,
        "agrees": true
      },
      {
        "talkmove_label": "4",
        "talkmove_name": "Providing evidence",
        "proxy_expected": "positive",
        "context": "How many more is on subtraction",
        "utterance": "So if I know that how many its subtraction then I know how much is probably addition",
        "predicted": "neutral",
        "confusion_probability": 0.15,
        "agrees": false
      },
      {
        "talkmove_label": "4",
        "talkmove_name": "Providing evidence",
        "proxy_expected": "positive",
        "context": "I know",
        "utterance": "Right now Im saying yes because theres 30 and six divided by three is",
        "predicted": "positive",
        "confusion_probability": 0.08,
        "agrees": true
      },
      {
        "talkmove_label": "4",
        "talkmove_name": "Providing evidence",
        "proxy_expected": "positive",
        "context": "I did 300 plus 40 plus 2 because you said 342",
        "utterance": "300 plus 40 is 340 plus 2 is 342",
        "predicted": "neutral",
        "confusion_probability": 0.15,
        "agrees": false
      },
      {
        "talkmove_label": "4",
        "talkmove_name": "Providing evidence",
        "proxy_expected": "positive",
        "context": "Jayden would you start as our first teacher to share how did you think about what is one fifth of 15",
        "utterance": "First I drew  which is 15",
        "predicted": "neutral",
        "confusion_probability": 0.15,
        "agrees": false
      }
    ]
  },
  {
    "provider": "gpt-5.6",
    "samples": 15,
    "agreements": 10,
    "agreement_rate": 0.667,
    "by_label": {
      "2": {
        "talkmove_name": "Asking for more information",
        "proxy_expected": "confused",
        "samples": 5,
        "agreements": 5,
        "agreement_rate": 1.0,
        "predictions": {
          "confused": 5
        }
      },
      "3": {
        "talkmove_name": "Making a claim",
        "proxy_expected": "neutral",
        "samples": 5,
        "agreements": 4,
        "agreement_rate": 0.8,
        "predictions": {
          "neutral": 4,
          "confused": 1
        }
      },
      "4": {
        "talkmove_name": "Providing evidence",
        "proxy_expected": "positive",
        "samples": 5,
        "agreements": 1,
        "agreement_rate": 0.2,
        "predictions": {
          "confused": 2,
          "neutral": 2,
          "positive": 1
        }
      }
    },
    "comparisons": [
      {
        "talkmove_label": "2",
        "talkmove_name": "Asking for more information",
        "proxy_expected": "confused",
        "context": "If this is 25 Maddox what did you do to figure out what 55 would be",
        "utterance": "We need 25  the half of 25 so what should be 15",
        "predicted": "confused",
        "confusion_probability": 0.95,
        "agrees": true
      },
      {
        "talkmove_label": "2",
        "talkmove_name": "Asking for more information",
        "proxy_expected": "confused",
        "context": "Rylee whats still confusing you",
        "utterance": "I just dont know how I got done",
        "predicted": "confused",
        "confusion_probability": 0.96,
        "agrees": true
      },
      {
        "talkmove_label": "2",
        "talkmove_name": "Asking for more information",
        "proxy_expected": "confused",
        "context": "You should have some points that are exact that you are talking about",
        "utterance": "I had a question about number one",
        "predicted": "confused",
        "confusion_probability": 0.64,
        "agrees": true
      },
      {
        "talkmove_label": "2",
        "talkmove_name": "Asking for more information",
        "proxy_expected": "confused",
        "context": "Is X5 a factor",
        "utterance": "Why do we synthetic division",
        "predicted": "confused",
        "confusion_probability": 0.76,
        "agrees": true
      },
      {
        "talkmove_label": "2",
        "talkmove_name": "Asking for more information",
        "proxy_expected": "confused",
        "context": "Yes",
        "utterance": "Can you show how to solve that one Ms",
        "predicted": "confused",
        "confusion_probability": 0.86,
        "agrees": true
      },
      {
        "talkmove_label": "3",
        "talkmove_name": "Making a claim",
        "proxy_expected": "neutral",
        "context": "60 times 800",
        "utterance": "804 80000 48000",
        "predicted": "neutral",
        "confusion_probability": 0.03,
        "agrees": true
      },
      {
        "talkmove_label": "3",
        "talkmove_name": "Making a claim",
        "proxy_expected": "neutral",
        "context": "Its 112 bigger than two thirds",
        "utterance": "A little bit",
        "predicted": "neutral",
        "confusion_probability": 0.38,
        "agrees": true
      },
      {
        "talkmove_label": "3",
        "talkmove_name": "Making a claim",
        "proxy_expected": "neutral",
        "context": "What are the dimensions of this rectangle",
        "utterance": "26 x 34",
        "predicted": "neutral",
        "confusion_probability": 0.01,
        "agrees": true
      },
      {
        "talkmove_label": "3",
        "talkmove_name": "Making a claim",
        "proxy_expected": "neutral",
        "context": "One two three",
        "utterance": "Three",
        "predicted": "neutral",
        "confusion_probability": 0.01,
        "agrees": true
      },
      {
        "talkmove_label": "3",
        "talkmove_name": "Making a claim",
        "proxy_expected": "neutral",
        "context": "What does that mean and why is that important",
        "utterance": "I think it means like how many inches they are",
        "predicted": "confused",
        "confusion_probability": 0.58,
        "agrees": false
      },
      {
        "talkmove_label": "4",
        "talkmove_name": "Providing evidence",
        "proxy_expected": "positive",
        "context": "Why not 80",
        "utterance": "Because 80 wouldnt work because theres 2 zeros added",
        "predicted": "confused",
        "confusion_probability": 0.78,
        "agrees": false
      },
      {
        "talkmove_label": "4",
        "talkmove_name": "Providing evidence",
        "proxy_expected": "positive",
        "context": "How many more is on subtraction",
        "utterance": "So if I know that how many its subtraction then I know how much is probably addition",
        "predicted": "confused",
        "confusion_probability": 0.76,
        "agrees": false
      },
      {
        "talkmove_label": "4",
        "talkmove_name": "Providing evidence",
        "proxy_expected": "positive",
        "context": "I know",
        "utterance": "Right now Im saying yes because theres 30 and six divided by three is",
        "predicted": "neutral",
        "confusion_probability": 0.24,
        "agrees": false
      },
      {
        "talkmove_label": "4",
        "talkmove_name": "Providing evidence",
        "proxy_expected": "positive",
        "context": "I did 300 plus 40 plus 2 because you said 342",
        "utterance": "300 plus 40 is 340 plus 2 is 342",
        "predicted": "positive",
        "confusion_probability": 0.01,
        "agrees": true
      },
      {
        "talkmove_label": "4",
        "talkmove_name": "Providing evidence",
        "proxy_expected": "positive",
        "context": "Jayden would you start as our first teacher to share how did you think about what is one fifth of 15",
        "utterance": "First I drew  which is 15",
        "predicted": "neutral",
        "confusion_probability": 0.04,
        "agrees": false
      }
    ]
  }
]
```
