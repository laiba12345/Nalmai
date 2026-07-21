# CCS Backtest

Generated from 9 authored Nalmai fixtures using the production CCS path and deterministic demo sentiment provider.

| Fixture | Confirmed Precision | Confirmed Recall | Early Precision | Early Recall |
|---|---:|---:|---:|---:|
| Solving Two-Step Equations | 1.000 | 0.200 | 0.800 | 0.800 |
| Comparing Decimals | 0.000 | 0.000 | 0.000 | 0.000 |
| Food Chains Review | 0.000 | 0.000 | 0.000 | 0.000 |
| Balanced Forces and Motion | 1.000 | 0.500 | 1.000 | 0.750 |
| Comparing Fractions | 0.667 | 0.500 | 0.600 | 0.750 |
| Area of Triangles | 0.000 | 0.000 | 0.000 | 0.000 |
| Where Plant Mass Comes From | 1.000 | 0.500 | 1.000 | 0.750 |
| Equivalent Ratios | 0.000 | 0.000 | 1.000 | 0.667 |
| Reading a Bar Chart | 0.000 | 0.000 | 0.000 | 0.000 |

## Aggregate

- Confirmed-confusion precision: **0.875**
- Confirmed-confusion recall: **0.269**
- Early-warning precision: **0.750**
- Early-warning recall: **0.577**
- Confirmed pre-poll majority-miss prediction: **4/11**
- Early-warning pre-poll prediction: **6/11**
- Confirmed confusion matrix: `{'tp': 7, 'fp': 1, 'tn': 25, 'fn': 19}`
- Early-warning confusion matrix: `{'tp': 15, 'fp': 5, 'tn': 21, 'fn': 11}`

## Interpretation

This is fixture backtesting, not real-world confusion accuracy. Authored windows test whether the current threshold behaves as intended in known demo moments. Poll prediction uses only the CCS from the previous event, preventing poll-result leakage. The sample is 9 deliberately constructed lessons—including slow-building, poll-only, false-alarm, latency-only, recovery, and calm patterns—and remains too small for fairness or deployment claims.

## Machine-readable detail

```json
[
  {
    "fixture": "algebra-slow-build",
    "title": "Solving Two-Step Equations",
    "confusion_window": {
      "start": 4,
      "end": 22
    },
    "window_precision": 1.0,
    "window_recall": 0.2,
    "early_warning_precision": 0.8,
    "early_warning_recall": 0.8,
    "confusion_points": 5,
    "confusion_matrix": {
      "tp": 1,
      "fp": 0,
      "tn": 2,
      "fn": 4
    },
    "early_warning_matrix": {
      "tp": 4,
      "fp": 1,
      "tn": 1,
      "fn": 1
    },
    "polls": 1,
    "poll_prediction_accuracy": 0.0,
    "poll_predictions": [
      {
        "at": 22,
        "pre_poll_ccs": 0.386,
        "predicted_miss": false,
        "pre_poll_early_score": 0.544,
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
        "evidence_quality": 0.45,
        "ground_truth_confused": false
      },
      {
        "at": 4,
        "event_type": "chat",
        "score": 0.31,
        "early_score": 0.42,
        "state": "warning",
        "evidence_quality": 0.72,
        "ground_truth_confused": true
      },
      {
        "at": 9,
        "event_type": "chat",
        "score": 0.319,
        "early_score": 0.445,
        "state": "warning",
        "evidence_quality": 0.75,
        "ground_truth_confused": true
      },
      {
        "at": 14,
        "event_type": "chat",
        "score": 0.264,
        "early_score": 0.393,
        "state": "calm",
        "evidence_quality": 0.77,
        "ground_truth_confused": true
      },
      {
        "at": 18,
        "event_type": "chat",
        "score": 0.386,
        "early_score": 0.544,
        "state": "warning",
        "evidence_quality": 0.79,
        "ground_truth_confused": true
      },
      {
        "at": 22,
        "event_type": "poll",
        "score": 0.66,
        "early_score": 0.48,
        "state": "confirmed",
        "evidence_quality": 0.92,
        "ground_truth_confused": true
      },
      {
        "at": 27,
        "event_type": "teacher",
        "score": 0.551,
        "early_score": 0.413,
        "state": "warning",
        "evidence_quality": 0.84,
        "ground_truth_confused": false
      }
    ]
  },
  {
    "fixture": "decimals-latency",
    "title": "Comparing Decimals",
    "confusion_window": {
      "start": 4,
      "end": 15
    },
    "window_precision": 0,
    "window_recall": 0.0,
    "early_warning_precision": 0,
    "early_warning_recall": 0.0,
    "confusion_points": 4,
    "confusion_matrix": {
      "tp": 0,
      "fp": 0,
      "tn": 2,
      "fn": 4
    },
    "early_warning_matrix": {
      "tp": 0,
      "fp": 0,
      "tn": 2,
      "fn": 4
    },
    "polls": 1,
    "poll_prediction_accuracy": 0.0,
    "poll_predictions": [
      {
        "at": 12,
        "pre_poll_ccs": 0.214,
        "predicted_miss": false,
        "pre_poll_early_score": 0.318,
        "predicted_miss_early": false,
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
        "evidence_quality": 0.45,
        "ground_truth_confused": false
      },
      {
        "at": 4,
        "event_type": "chat",
        "score": 0.205,
        "early_score": 0.294,
        "state": "calm",
        "evidence_quality": 0.56,
        "ground_truth_confused": true
      },
      {
        "at": 9,
        "event_type": "chat",
        "score": 0.214,
        "early_score": 0.318,
        "state": "calm",
        "evidence_quality": 0.59,
        "ground_truth_confused": true
      },
      {
        "at": 12,
        "event_type": "poll",
        "score": 0.49,
        "early_score": 0.296,
        "state": "calm",
        "evidence_quality": 0.66,
        "ground_truth_confused": true
      },
      {
        "at": 15,
        "event_type": "chat",
        "score": 0.546,
        "early_score": 0.391,
        "state": "calm",
        "evidence_quality": 0.76,
        "ground_truth_confused": true
      },
      {
        "at": 20,
        "event_type": "teacher",
        "score": 0.451,
        "early_score": 0.341,
        "state": "calm",
        "evidence_quality": 0.75,
        "ground_truth_confused": false
      }
    ]
  },
  {
    "fixture": "ecosystems-calm",
    "title": "Food Chains Review",
    "confusion_window": null,
    "window_precision": 0,
    "window_recall": 0,
    "early_warning_precision": 0,
    "early_warning_recall": 0,
    "confusion_points": 0,
    "confusion_matrix": {
      "tp": 0,
      "fp": 0,
      "tn": 5,
      "fn": 0
    },
    "early_warning_matrix": {
      "tp": 0,
      "fp": 0,
      "tn": 5,
      "fn": 0
    },
    "polls": 1,
    "poll_prediction_accuracy": 1.0,
    "poll_predictions": [
      {
        "at": 9,
        "pre_poll_ccs": 0.118,
        "predicted_miss": false,
        "pre_poll_early_score": 0.187,
        "predicted_miss_early": false,
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
        "evidence_quality": 0.45,
        "ground_truth_confused": false
      },
      {
        "at": 3,
        "event_type": "chat",
        "score": 0.109,
        "early_score": 0.165,
        "state": "calm",
        "evidence_quality": 0.48,
        "ground_truth_confused": false
      },
      {
        "at": 6,
        "event_type": "chat",
        "score": 0.118,
        "early_score": 0.187,
        "state": "calm",
        "evidence_quality": 0.51,
        "ground_truth_confused": false
      },
      {
        "at": 9,
        "event_type": "poll",
        "score": 0.116,
        "early_score": 0.182,
        "state": "calm",
        "evidence_quality": 0.5,
        "ground_truth_confused": false
      },
      {
        "at": 13,
        "event_type": "teacher",
        "score": 0.114,
        "early_score": 0.177,
        "state": "calm",
        "evidence_quality": 0.49,
        "ground_truth_confused": false
      }
    ]
  },
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
        "evidence_quality": 0.45,
        "ground_truth_confused": false
      },
      {
        "at": 4,
        "event_type": "chat",
        "score": 0.135,
        "early_score": 0.2,
        "state": "calm",
        "evidence_quality": 0.56,
        "ground_truth_confused": true
      },
      {
        "at": 7,
        "event_type": "chat",
        "score": 0.393,
        "early_score": 0.527,
        "state": "warning",
        "evidence_quality": 0.75,
        "ground_truth_confused": true
      },
      {
        "at": 10,
        "event_type": "poll",
        "score": 0.677,
        "early_score": 0.48,
        "state": "confirmed",
        "evidence_quality": 0.9,
        "ground_truth_confused": true
      },
      {
        "at": 14,
        "event_type": "chat",
        "score": 0.601,
        "early_score": 0.455,
        "state": "confirmed",
        "evidence_quality": 0.92,
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
        "evidence_quality": 0.45,
        "ground_truth_confused": false
      },
      {
        "at": 4,
        "event_type": "chat",
        "score": 0.132,
        "early_score": 0.196,
        "state": "calm",
        "evidence_quality": 0.56,
        "ground_truth_confused": true
      },
      {
        "at": 7,
        "event_type": "chat",
        "score": 0.323,
        "early_score": 0.451,
        "state": "warning",
        "evidence_quality": 0.75,
        "ground_truth_confused": true
      },
      {
        "at": 10,
        "event_type": "poll",
        "score": 0.614,
        "early_score": 0.412,
        "state": "confirmed",
        "evidence_quality": 0.9,
        "ground_truth_confused": true
      },
      {
        "at": 13,
        "event_type": "chat",
        "score": 0.724,
        "early_score": 0.584,
        "state": "confirmed",
        "evidence_quality": 0.92,
        "ground_truth_confused": true
      },
      {
        "at": 17,
        "event_type": "teacher",
        "score": 0.635,
        "early_score": 0.515,
        "state": "confirmed",
        "evidence_quality": 0.92,
        "ground_truth_confused": false
      },
      {
        "at": 20,
        "event_type": "poll",
        "score": 0.451,
        "early_score": 0.469,
        "state": "warning",
        "evidence_quality": 0.83,
        "ground_truth_confused": false
      }
    ]
  },
  {
    "fixture": "geometry-poll-only",
    "title": "Area of Triangles",
    "confusion_window": {
      "start": 10,
      "end": 14
    },
    "window_precision": 0,
    "window_recall": 0.0,
    "early_warning_precision": 0,
    "early_warning_recall": 0.0,
    "confusion_points": 2,
    "confusion_matrix": {
      "tp": 0,
      "fp": 0,
      "tn": 3,
      "fn": 2
    },
    "early_warning_matrix": {
      "tp": 0,
      "fp": 0,
      "tn": 3,
      "fn": 2
    },
    "polls": 1,
    "poll_prediction_accuracy": 0.0,
    "poll_predictions": [
      {
        "at": 10,
        "pre_poll_ccs": 0.118,
        "predicted_miss": false,
        "pre_poll_early_score": 0.187,
        "predicted_miss_early": false,
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
        "evidence_quality": 0.45,
        "ground_truth_confused": false
      },
      {
        "at": 4,
        "event_type": "chat",
        "score": 0.109,
        "early_score": 0.165,
        "state": "calm",
        "evidence_quality": 0.48,
        "ground_truth_confused": false
      },
      {
        "at": 7,
        "event_type": "chat",
        "score": 0.118,
        "early_score": 0.187,
        "state": "calm",
        "evidence_quality": 0.51,
        "ground_truth_confused": false
      },
      {
        "at": 10,
        "event_type": "poll",
        "score": 0.337,
        "early_score": 0.182,
        "state": "calm",
        "evidence_quality": 0.58,
        "ground_truth_confused": true
      },
      {
        "at": 14,
        "event_type": "teacher",
        "score": 0.294,
        "early_score": 0.177,
        "state": "calm",
        "evidence_quality": 0.57,
        "ground_truth_confused": true
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
        "evidence_quality": 0.45,
        "ground_truth_confused": false
      },
      {
        "at": 4,
        "event_type": "chat",
        "score": 0.123,
        "early_score": 0.184,
        "state": "calm",
        "evidence_quality": 0.56,
        "ground_truth_confused": true
      },
      {
        "at": 7,
        "event_type": "chat",
        "score": 0.327,
        "early_score": 0.455,
        "state": "warning",
        "evidence_quality": 0.75,
        "ground_truth_confused": true
      },
      {
        "at": 10,
        "event_type": "poll",
        "score": 0.618,
        "early_score": 0.416,
        "state": "confirmed",
        "evidence_quality": 0.9,
        "ground_truth_confused": true
      },
      {
        "at": 14,
        "event_type": "chat",
        "score": 0.679,
        "early_score": 0.54,
        "state": "confirmed",
        "evidence_quality": 0.92,
        "ground_truth_confused": true
      }
    ]
  },
  {
    "fixture": "ratios-recovery",
    "title": "Equivalent Ratios",
    "confusion_window": {
      "start": 4,
      "end": 12
    },
    "window_precision": 0,
    "window_recall": 0.0,
    "early_warning_precision": 1.0,
    "early_warning_recall": 0.667,
    "confusion_points": 3,
    "confusion_matrix": {
      "tp": 0,
      "fp": 0,
      "tn": 4,
      "fn": 3
    },
    "early_warning_matrix": {
      "tp": 2,
      "fp": 0,
      "tn": 4,
      "fn": 1
    },
    "polls": 2,
    "poll_prediction_accuracy": 1.0,
    "poll_predictions": [
      {
        "at": 12,
        "pre_poll_ccs": 0.366,
        "predicted_miss": false,
        "pre_poll_early_score": 0.497,
        "predicted_miss_early": true,
        "poll_miss_rate": 0.5,
        "actual_majority_miss": false,
        "score_source": "previous_event"
      },
      {
        "at": 34,
        "pre_poll_ccs": 0.261,
        "predicted_miss": false,
        "pre_poll_early_score": 0.267,
        "predicted_miss_early": false,
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
        "evidence_quality": 0.45,
        "ground_truth_confused": false
      },
      {
        "at": 4,
        "event_type": "chat",
        "score": 0.158,
        "early_score": 0.232,
        "state": "calm",
        "evidence_quality": 0.64,
        "ground_truth_confused": true
      },
      {
        "at": 8,
        "event_type": "chat",
        "score": 0.366,
        "early_score": 0.497,
        "state": "warning",
        "evidence_quality": 0.75,
        "ground_truth_confused": true
      },
      {
        "at": 12,
        "event_type": "poll",
        "score": 0.534,
        "early_score": 0.44,
        "state": "warning",
        "evidence_quality": 0.82,
        "ground_truth_confused": true
      },
      {
        "at": 24,
        "event_type": "teacher",
        "score": 0.341,
        "early_score": 0.316,
        "state": "calm",
        "evidence_quality": 0.8,
        "ground_truth_confused": false
      },
      {
        "at": 30,
        "event_type": "chat",
        "score": 0.261,
        "early_score": 0.267,
        "state": "calm",
        "evidence_quality": 0.81,
        "ground_truth_confused": false
      },
      {
        "at": 34,
        "event_type": "poll",
        "score": 0.198,
        "early_score": 0.247,
        "state": "calm",
        "evidence_quality": 0.81,
        "ground_truth_confused": false
      }
    ]
  },
  {
    "fixture": "statistics-false-alarm",
    "title": "Reading a Bar Chart",
    "confusion_window": null,
    "window_precision": 0,
    "window_recall": 0,
    "early_warning_precision": 0.0,
    "early_warning_recall": 0,
    "confusion_points": 0,
    "confusion_matrix": {
      "tp": 0,
      "fp": 0,
      "tn": 5,
      "fn": 0
    },
    "early_warning_matrix": {
      "tp": 0,
      "fp": 2,
      "tn": 3,
      "fn": 0
    },
    "polls": 1,
    "poll_prediction_accuracy": 1.0,
    "poll_predictions": [
      {
        "at": 10,
        "pre_poll_ccs": 0.293,
        "predicted_miss": false,
        "pre_poll_early_score": 0.416,
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
        "evidence_quality": 0.45,
        "ground_truth_confused": false
      },
      {
        "at": 4,
        "event_type": "chat",
        "score": 0.468,
        "early_score": 0.586,
        "state": "warning",
        "evidence_quality": 0.64,
        "ground_truth_confused": false
      },
      {
        "at": 7,
        "event_type": "chat",
        "score": 0.293,
        "early_score": 0.416,
        "state": "warning",
        "evidence_quality": 0.67,
        "ground_truth_confused": false
      },
      {
        "at": 10,
        "event_type": "poll",
        "score": 0.267,
        "early_score": 0.382,
        "state": "calm",
        "evidence_quality": 0.66,
        "ground_truth_confused": false
      },
      {
        "at": 14,
        "event_type": "teacher",
        "score": 0.238,
        "early_score": 0.342,
        "state": "calm",
        "evidence_quality": 0.65,
        "ground_truth_confused": false
      }
    ]
  }
]
```
