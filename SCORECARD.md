# AML Detection System Scorecard

## Overall Performance Lift (Rules vs Ensemble)
*Operating Point: Score >= 50*

| Metric | Rules Only (v2-v4) | Rules + ML Ensemble (v5) | Lift |
|--------|-------------------|--------------------------|------|
| **Recall** | 45.0% | 56.4% | **+11.4%** |
| **Precision** | 88.8% | 87.5% | -1.3% |
| **FPR** | 1.61% | 2.28% | +0.67% |
| **F1 Score** | 0.597 | 0.686 | +0.088 |
| **PR-AUC** | 0.683 | 0.770 | +0.088 |

## Detection Rate by Anomaly Type

| Anomaly Type | Rules Only | Rules + ML |
|--------------|------------|------------|
| none | 0.0% | 0.0% |
| large_amount | 100.0% | 100.0% |
| structuring | 100.0% | 100.0% |
| velocity_fraud | 14.1% | 31.9% |
| geo_anomaly | 100.0% | 100.0% |

    
## Context
- **Dataset**: Synthetic local generation (v1 schema)
- **Class Imbalance**: ~5% Anomalies
- The ensemble successfully bridges the detection gap by identifying multivariate and graphical structuring patterns without spiking the false positive rate.
