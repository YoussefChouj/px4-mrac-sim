arms run https://github.com/YoussefChouj/px4-mrac-sim/actions/runs/42016856210 wave **N-l1-roles-iter** on `claude/collect-landed` finished: **plan success, build success, fly success**, 28/180 flights pass, 10 decks.

| deck | n | pass | track rms m | hold max m | tilt max deg | att rms deg | track vs alone |
|---|---|---|---|---|---|---|---|
| rw-alone | 18 | 6 | 0.887 | 0.988 | 35.760 | 1.931 |  |
| rw-l1r6 | 18 | 0 | 0.747 | 0.638 | 39.193 | 2.029 |  |
| rw-l1r6t | 18 | 0 | 0.745 | 0.601 | 37.324 | 2.018 |  |
| rw-l1r7m2 | 18 | 0 | 0.734 | 0.822 | 38.105 | 1.990 |  |
| rw-l1r7m2t | 18 | 0 | 0.773 | 0.876 | 37.164 | 1.973 |  |
| rwf-alone | 18 | 12 | 0.864 | 1.042 | 34.545 | 1.920 |  |
| rwf-l1r6 | 18 | 0 | 0.703 | 0.650 | 37.337 | 2.030 |  |
| rwf-l1r6t | 18 | 5 | 0.733 | 0.626 | 36.214 | 1.994 |  |
| rwf-l1r7m2 | 18 | 2 | 0.804 | 0.859 | 37.513 | 1.977 |  |
| rwf-l1r7m2t | 18 | 3 | 0.769 | 0.920 | 35.842 | 1.980 |  |

Medians over runs (n = flights that reported). "track vs alone": median track rms of a plus-mrac deck divided by its alone deck, below 1 = MRAC better.

Files: https://github.com/YoussefChouj/px4-mrac-sim/tree/results/results/N-l1-roles-iter-42016856210
