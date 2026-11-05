arms run https://github.com/YoussefChouj/px4-mrac-sim/actions/runs/42106790422 wave **P-highfidelity** on `claude/collect-landed` finished: **plan success, build success, fly success**, 97/240 flights pass, 8 decks.

| deck | n | pass | track rms m | hold max m | tilt max deg | att rms deg | track vs alone |
|---|---|---|---|---|---|---|---|
| hf-alone | 30 | 16 | 0.939 | 1.066 | 37.428 | 0.877 |  |
| hf-l1r6 | 30 | 8 | 0.763 | 0.675 | 43.232 | 2.733 |  |
| hf-l1r6t | 30 | 11 | 0.721 | 0.777 | 41.267 | 2.762 |  |
| hf-mrac | 30 | 10 | 0.885 | 0.606 | 37.243 | 2.655 |  |
| hff-alone | 30 | 17 | 0.954 | 0.812 | 36.621 | 0.953 |  |
| hff-l1r6 | 30 | 10 | 0.749 | 0.618 | 42.481 | 2.187 |  |
| hff-l1r6t | 30 | 13 | 0.763 | 0.678 | 40.981 | 2.280 |  |
| hff-mrac | 30 | 12 | 0.880 | 0.515 | 38.044 | 2.764 |  |

Medians over runs (n = flights that reported). "track vs alone": median track rms of a plus-mrac deck divided by its alone deck, below 1 = MRAC better.

Files: https://github.com/YoussefChouj/px4-mrac-sim/tree/results/results/P-highfidelity-42106790422
