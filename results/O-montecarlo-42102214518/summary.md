arms run https://github.com/YoussefChouj/px4-mrac-sim/actions/runs/42102214518 wave **O-montecarlo** on `claude/collect-landed` finished: **plan success, build success, fly success**, 0/240 flights pass, 8 decks.

| deck | n | pass | track rms m | hold max m | tilt max deg | att rms deg | track vs alone |
|---|---|---|---|---|---|---|---|
| mc-alone | 30 | 0 | 0.825 | 0.898 | 35.138 | 1.741 |  |
| mc-l1r6 | 30 | 0 | 0.741 | 0.573 | 38.514 | 1.890 |  |
| mc-l1r6t | 30 | 0 | 0.730 | 0.561 | 36.904 | 1.894 |  |
| mc-mrac | 30 | 0 | 0.825 | 0.593 | 41.351 | 8.892 |  |
| mcf-alone | 30 | 0 | 0.861 | 0.982 | 35.645 | 1.701 |  |
| mcf-l1r6 | 30 | 0 | 0.745 | 0.555 | 38.702 | 1.819 |  |
| mcf-l1r6t | 30 | 0 | 0.727 | 0.538 | 36.154 | 1.788 |  |
| mcf-mrac | 30 | 0 | 0.825 | 0.686 | 42.532 | 9.092 |  |

Medians over runs (n = flights that reported). "track vs alone": median track rms of a plus-mrac deck divided by its alone deck, below 1 = MRAC better.

Files: https://github.com/YoussefChouj/px4-mrac-sim/tree/results/results/O-montecarlo-42102214518
