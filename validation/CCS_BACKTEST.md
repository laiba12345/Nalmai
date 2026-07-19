# CCS Backtest

Generated from the three authored ClassPulse fixtures using the production CCS path and deterministic demo sentiment provider.

| Fixture | Confirmed Precision | Confirmed Recall | Early Precision | Early Recall |
|---|---:|---:|---:|---:|
| Balanced Forces and Motion | 1.000 | 0.500 | 1.000 | 0.750 |
| Comparing Fractions | 0.667 | 0.500 | 0.600 | 0.750 |
| Where Plant Mass Comes From | 1.000 | 0.500 | 1.000 | 0.750 |

## Aggregate

- Confirmed-confusion precision: **0.857**
- Confirmed-confusion recall: **0.500**
- Early-warning precision: **0.818**
- Early-warning recall: **0.750**
- Confirmed pre-poll majority-miss prediction: **0/4**
- Early-warning pre-poll prediction: **3/4**
- Confirmed confusion matrix: `{'tp': 6, 'fp': 1, 'tn': 4, 'fn': 6}`
- Early-warning confusion matrix: `{'tp': 9, 'fp': 2, 'tn': 3, 'fn': 3}`

## Interpretation

This is fixture backtesting, not real-world confusion accuracy. Authored windows test whether the current threshold behaves as intended in known demo moments. Poll prediction uses only the CCS from the previous event, preventing poll-result leakage. The sample is three deliberately constructed lessons and is too small for calibration, fairness, or deployment claims.

## Machine-readable detail

```json
[
  {
    "fixture": "forces-live",
    "title": "Balanced Forces and Motion",
    "confusion_window": {
      "start": 4,
      "end": 14
    },
    "window_precision": 1.0,
    "window_recall": 0.5,
    "early_warning_precision": 1.0,
    "early_warning_recall": 0.75,
    "confusion_points": 4,
    "confusion_matrix": {
      "tp": 2,
      "fp": 0,
      "tn": 1,
      "fn": 2
    },
    "early_warning_matrix": {
      "tp": 3,
      "fp": 0,
      "tn": 1,
      "fn": 1
    },
    "polls": 1,
    "poll_prediction_accuracy": 0.0,
    "poll_predictions": [
      {
        "at": 10,
        "pre_poll_ccs": 0.393,
        "predicted_miss": false,
        "pre_poll_early_score": 0.527,
        "predicted_miss_early": true,
        "poll_miss_rate": 0.75,
        "actual_majority_miss": true,
        "score_source": "previous_event"
      }
    ],
    "timeline": [
      {
        "at": 0,
        "event_type": "teacher",
        "score": 0.1,
        "early_score": 0.142,
        "state": "calm",
        "ground_truth_confused": false
      },
      {
        "at": 4,
        "event_type": "chat",
        "score": 0.135,
        "early_score": 0.2,
        "state": "calm",
        "ground_truth_confused": true
      },
      {
        "at": 7,
        "event_type": "chat",
        "score": 0.393,
        "early_score": 0.527,
        "state": "warning",
        "ground_truth_confused": true
      },
      {
        "at": 10,
        "event_type": "poll",
        "score": 0.677,
        "early_score": 0.48,
        "state": "confirmed",
        "ground_truth_confused": true
      },
      {
        "at": 14,
        "event_type": "chat",
        "score": 0.601,
        "early_score": 0.455,
        "state": "confirmed",
        "ground_truth_confused": true
      }
    ]
  },
  {
    "fixture": "fractions-live",
    "title": "Comparing Fractions",
    "confusion_window": {
      "start": 4,
      "end": 13
    },
    "window_precision": 0.667,
    "window_recall": 0.5,
    "early_warning_precision": 0.6,
    "early_warning_recall": 0.75,
    "confusion_points": 4,
    "confusion_matrix": {
      "tp": 2,
      "fp": 1,
      "tn": 2,
      "fn": 2
    },
    "early_warning_matrix": {
      "tp": 3,
      "fp": 2,
      "tn": 1,
      "fn": 1
    },
    "polls": 2,
    "poll_prediction_accuracy": 0.0,
    "poll_predictions": [
      {
        "at": 10,
        "pre_poll_ccs": 0.323,
        "predicted_miss": false,
        "pre_poll_early_score": 0.451,
        "predicted_miss_early": true,
        "poll_miss_rate": 0.75,
        "actual_majority_miss": true,
        "score_source": "previous_event"
      },
      {
        "at": 20,
        "pre_poll_ccs": 0.635,
        "predicted_miss": true,
        "pre_poll_early_score": 0.515,
        "predicted_miss_early": true,
        "poll_miss_rate": 0.0,
        "actual_majority_miss": false,
        "score_source": "previous_event"
      }
    ],
    "timeline": [
      {
        "at": 0,
        "event_type": "teacher",
        "score": 0.1,
        "early_score": 0.142,
        "state": "calm",
        "ground_truth_confused": false
      },
      {
        "at": 4,
        "event_type": "chat",
        "score": 0.132,
        "early_score": 0.196,
        "state": "calm",
        "ground_truth_confused": true
      },
      {
        "at": 7,
        "event_type": "chat",
        "score": 0.323,
        "early_score": 0.451,
        "state": "warning",
        "ground_truth_confused": true
      },
      {
        "at": 10,
        "event_type": "poll",
        "score": 0.614,
        "early_score": 0.412,
        "state": "confirmed",
        "ground_truth_confused": true
      },
      {
        "at": 13,
        "event_type": "chat",
        "score": 0.724,
        "early_score": 0.584,
        "state": "confirmed",
        "ground_truth_confused": true
      },
      {
        "at": 17,
        "event_type": "teacher",
        "score": 0.635,
        "early_score": 0.515,
        "state": "confirmed",
        "ground_truth_confused": false
      },
      {
        "at": 20,
        "event_type": "poll",
        "score": 0.451,
        "early_score": 0.469,
        "state": "warning",
        "ground_truth_confused": false
      }
    ]
  },
  {
    "fixture": "photosynthesis-live",
    "title": "Where Plant Mass Comes From",
    "confusion_window": {
      "start": 4,
      "end": 14
    },
    "window_precision": 1.0,
    "window_recall": 0.5,
    "early_warning_precision": 1.0,
    "early_warning_recall": 0.75,
    "confusion_points": 4,
    "confusion_matrix": {
      "tp": 2,
      "fp": 0,
      "tn": 1,
      "fn": 2
    },
    "early_warning_matrix": {
      "tp": 3,
      "fp": 0,
      "tn": 1,
      "fn": 1
    },
    "polls": 1,
    "poll_prediction_accuracy": 0.0,
    "poll_predictions": [
      {
        "at": 10,
        "pre_poll_ccs": 0.327,
        "predicted_miss": false,
        "pre_poll_early_score": 0.455,
        "predicted_miss_early": true,
        "poll_miss_rate": 0.75,
        "actual_majority_miss": true,
        "score_source": "previous_event"
      }
    ],
    "timeline": [
      {
        "at": 0,
        "event_type": "teacher",
        "score": 0.1,
        "early_score": 0.142,
        "state": "calm",
        "ground_truth_confused": false
      },
      {
        "at": 4,
        "event_type": "chat",
        "score": 0.123,
        "early_score": 0.184,
        "state": "calm",
        "ground_truth_confused": true
      },
      {
        "at": 7,
        "event_type": "chat",
        "score": 0.327,
        "early_score": 0.455,
        "state": "warning",
        "ground_truth_confused": true
      },
      {
        "at": 10,
        "event_type": "poll",
        "score": 0.618,
        "early_score": 0.416,
        "state": "confirmed",
        "ground_truth_confused": true
      },
      {
        "at": 14,
        "event_type": "chat",
        "score": 0.679,
        "early_score": 0.54,
        "state": "confirmed",
        "ground_truth_confused": true
      }
    ]
  }
]
```
