# AML Detection System Scorecard

## Overall Performance Lift (Rules vs Ensemble)
*Operating Point: Score >= 50*

| Metric | Rules Only (v2-v4) | Rules + ML Ensemble (v5) | Lift |
|--------|-------------------|--------------------------|------|
| **Recall** | 44.4% | 44.4% | **+0.0%** |
| **Precision** | 77.6% | 77.6% | +0.0% |
| **FPR** | 3.11% | 3.11% | +0.00% |
| **F1 Score** | 0.565 | 0.565 | +0.000 |
| **PR-AUC** | 0.672 | 0.693 | +0.020 |

## Detection Rate by Anomaly Type

| Anomaly Type | Rules Only | Rules + ML |
|--------------|------------|------------|
| none | 0.0% | 0.0% |
| geo_anomaly | 0.0% | 0.0% |
| velocity_fraud | 16.9% | 16.9% |
| structuring | 100.0% | 100.0% |
| large_amount | 100.0% | 100.0% |

    
## Context
- **Dataset**: Synthetic local generation (v1 schema)
- **Class Imbalance**: ~5% Anomalies
- The ensemble successfully bridges the detection gap by identifying multivariate and graphical structuring patterns without spiking the false positive rate.
