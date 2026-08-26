# Panel-draw sensitivity of the reference-count floor

Draws pooled: **10** (seeds [20260826, 11, 22, 33, 44, 55, 66, 77, 88, 99], primary 20260826).  
Cells per budget per draw: 90. Pooled: **900**.

Post-hoc robustness analysis. No hypothesis, threshold, or verdict of the frozen protocol is changed.

## Pooled over all draws

| N | cells | worst nRMSE ratio | worst MAE ratio | inverted | >5× | >3× | >2× | >2× MAE | mean ratio | median ratio |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 0 | 900 | 1.00 | 1.00 | 0 | 0 | 0 | 0 | 0 | 1.000 | 1.000 |
| 2 | 900 | 44.53 | 50.99 | 3 | 3 | 7 | 48 | 67 | 1.169 | 1.017 |
| 3 | 900 | 4.68 | 4.41 | 0 | 0 | 4 | 25 | 34 | 1.012 | 0.988 |
| 4 | 900 | 4.54 | 4.27 | 0 | 0 | 2 | 10 | 11 | 0.908 | 0.930 |
| 5 | 900 | 4.60 | 4.27 | 0 | 0 | 2 | 8 | 10 | 0.880 | 0.905 |
| 6 | 900 | 3.53 | 3.52 | 0 | 0 | 2 | 5 | 6 | 0.841 | 0.880 |
| 8 | 900 | 3.13 | 2.99 | 0 | 0 | 2 | 3 | 3 | 0.799 | 0.849 |
| 10 | 900 | 2.63 | 2.36 | 0 | 0 | 0 | 3 | 3 | 0.779 | 0.831 |
| 20 | 900 | 1.64 | 1.70 | 0 | 0 | 0 | 0 | 0 | 0.748 | 0.810 |
| 50 | 900 | 1.23 | 1.22 | 0 | 0 | 0 | 0 | 0 | 0.727 | 0.795 |

## Per-draw floor, 2× nRMSE

| seed | floor N |
|---|---:|
| 20260826 (primary) | 4 |
| 11 | 6 |
| 22 | 4 |
| 33 | 20 |
| 44 | 20 |
| 55 | 4 |
| 66 | 4 |
| 77 | 5 |
| 88 | 8 |
| 99 | 4 |

## Pooled floor by endpoint and threshold

| endpoint and threshold | no draw exceeds it from |
|---|---:|
| nRMSE>1.5x | N = 50 |
| nRMSE>2.0x | N = 20 |
| nRMSE>3.0x | N = 10 |
| nRMSE>5.0x | N = 3 |
| MAE>1.5x | N = 50 |
| MAE>2.0x | N = 20 |
| MAE>3.0x | N = 8 |
| MAE>5.0x | N = 3 |
