arms run https://github.com/YoussefChouj/px4-mrac-sim/actions/runs/42112117524 wave **P-highfidelity** on `claude/collect-landed` finished: **plan success, build success, fly success**, 152/240 flights pass, 8 decks.

| deck | n | pass | track rms m | hold max m | tilt max deg | att rms deg | track vs alone |
|---|---|---|---|---|---|---|---|
| hf-alone | 30 | 27 | 0.888 | 1.547 | 40.323 | 1.999 |  |
| hf-l1r6 | 30 | 13 | 0.741 | 1.028 | 46.442 | 2.158 |  |
| hf-l1r6t | 30 | 20 | 0.725 | 0.979 | 42.943 | 2.161 |  |
| hf-mrac | 30 | 16 | 0.844 | 0.518 | 37.959 | 4.036 |  |
| hff-alone | 30 | 26 | 0.896 | 1.619 | 38.499 | 1.885 |  |
| hff-l1r6 | 30 | 15 | 0.751 | 0.791 | 43.865 | 1.992 |  |
| hff-l1r6t | 30 | 22 | 0.721 | 0.898 | 41.349 | 2.072 |  |
| hff-mrac | 30 | 13 | 1.259 | 0.530 | 39.626 | 4.138 |  |

Medians over runs (n = flights that reported). "track vs alone": median track rms of a plus-mrac deck divided by its alone deck, below 1 = MRAC better.

Files: https://github.com/YoussefChouj/px4-mrac-sim/tree/results/results/P-highfidelity-42112117524
