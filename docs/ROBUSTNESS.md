# Robustness — 20 independent batches

Every row is a full end-to-end run on a freshly generated batch: new records, new failure mix, new policy decisions, new seals. Scored on the `holdout` split.

Reproduce with `python -m salvage sweep`.

| | mean | sd | min | max |
|---|---|---|---|---|
| Verified recovery rate | 44.1% | 12.8% | 19.8% | 63.7% |
| Naive agent's reported rate | 91.2% | 5.8% | 75.0% | 98.9% |
| Share of the naive claim that is fiction | 51.7% | 13.8% | 28.2% | 78.2% |

**The naive agent overstated recovery in 20 of 20 batches.**

The recovery rate moves with the batch — a single seed cannot carry it, and any submission quoting one number from one run of 48 records is quoting noise. What does not move is the gap: an agent that trusts its own success claim overstates every time, and the only thing that varies is by how much.

## Per-seed

| seed | verified | naive | fiction | gap |
|---|---|---|---|---|
| 1 | 63.7% | 88.7% | 28.2% | ₹19,075.45 |
| 2 | 52.8% | 95.4% | 44.7% | ₹69,648.23 |
| 3 | 26.0% | 91.7% | 71.6% | ₹79,610.57 |
| 4 | 47.9% | 79.7% | 39.8% | ₹42,981.48 |
| 5 | 28.0% | 75.0% | 62.7% | ₹33,087.51 |
| 6 | 44.6% | 93.2% | 52.1% | ₹71,680.42 |
| 7 | 53.0% | 92.6% | 42.7% | ₹43,996.41 |
| 8 | 56.6% | 89.8% | 37.0% | ₹45,253.21 |
| 9 | 58.0% | 93.1% | 37.7% | ₹47,193.56 |
| 10 | 56.3% | 98.9% | 43.0% | ₹67,651.82 |
| 11 | 55.6% | 92.4% | 39.8% | ₹62,790.19 |
| 12 | 30.3% | 96.2% | 68.5% | ₹112,591.36 |
| 13 | 49.2% | 96.7% | 49.2% | ₹50,792.93 |
| 14 | 31.3% | 89.6% | 65.1% | ₹66,855.68 |
| 15 | 33.4% | 87.4% | 61.7% | ₹81,351.39 |
| 16 | 50.3% | 97.2% | 48.3% | ₹91,664.68 |
| 17 | 49.2% | 88.3% | 44.2% | ₹49,376.37 |
| 18 | 19.8% | 90.7% | 78.2% | ₹97,782.80 |
| 19 | 45.4% | 91.3% | 50.3% | ₹65,479.61 |
| 20 | 30.0% | 97.1% | 69.1% | ₹70,660.33 |
