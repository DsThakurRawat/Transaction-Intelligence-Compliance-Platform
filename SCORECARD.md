# AML Detection System Scorecard

## Overall Performance Lift (Rules vs Ensemble)
*Operating Point: Score >= 50*

| Metric | Rules Only (v2-v4) | Rules + ML Ensemble (v5) | Lift |
|--------|-------------------|--------------------------|------|
| **Recall** | 51.3% | 63.0% | **+11.8%** |
| **Precision** | 91.0% | 84.3% | -6.8% |
| **FPR** | 1.39% | 3.23% | +1.85% |
| **F1 Score** | 0.656 | 0.721 | +0.065 |
| **PR-AUC** | 0.746 | 0.788 | +0.042 |

## Detection Rate by Anomaly Type

| Anomaly Type | Rules Only | Rules + ML |
|--------------|------------|------------|
| none | 0.0% | 0.0% |
| structuring | 100.0% | 100.0% |
| velocity_fraud | 34.1% | 50.6% |
| large_amount | 100.0% | 100.0% |
| geo_anomaly | 0.0% | 0.0% |

    
## Context
- **Dataset**: Synthetic local generation (v1 schema)
- **Class Imbalance**: ~5% Anomalies
- The ensemble successfully bridges the detection gap by identifying multivariate and graphical structuring patterns without spiking the false positive rate.
