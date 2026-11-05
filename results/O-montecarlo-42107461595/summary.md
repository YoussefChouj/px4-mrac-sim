arms run https://github.com/YoussefChouj/px4-mrac-sim/actions/runs/42107461595 wave **O-montecarlo** on `claude/collect-landed` finished: **plan success, build success, fly success**, 198/240 flights pass, 8 decks.

| deck | n | pass | track rms m | hold max m | tilt max deg | att rms deg | track vs alone |
|---|---|---|---|---|---|---|---|
| mc-alone | 30 | 29 | 0.843 | 1.253 | 36.955 | 1.910 |  |
| mc-l1r6 | 30 | 27 | 0.736 | 0.816 | 39.706 | 2.042 |  |
| mc-l1r6t | 30 | 29 | 0.727 | 0.832 | 37.798 | 2.002 |  |
| mc-mrac | 30 | 11 | 0.811 | 0.769 | 46.608 | 8.536 |  |
| mcf-alone | 30 | 30 | 0.837 | 1.257 | 37.089 | 1.933 |  |
| mcf-l1r6 | 30 | 28 | 0.744 | 0.792 | 40.142 | 2.021 |  |
| mcf-l1r6t | 30 | 29 | 0.776 | 0.780 | 37.844 | 2.004 |  |
| mcf-mrac | 30 | 15 | 0.819 | 0.643 | 44.988 | 6.802 |  |

Medians over runs (n = flights that reported). "track vs alone": median track rms of a plus-mrac deck divided by its alone deck, below 1 = MRAC better.

Files: https://github.com/YoussefChouj/px4-mrac-sim/tree/results/results/O-montecarlo-42107461595
