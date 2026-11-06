arms run https://github.com/YoussefChouj/px4-mrac-sim/actions/runs/42174790900 wave **R2-tilt-source** on `claude/collect-landed` finished: **plan success, build success, fly success**, 133/150 flights pass, 5 decks.

| deck | n | pass | track rms m | hold max m | tilt max deg | att rms deg | track vs alone |
|---|---|---|---|---|---|---|---|
| hf3-alone | 30 | 28 | 0.876 | 1.558 | 39.385 | 2.002 |  |
| hf3-alone-t37 | 30 | 27 | 0.878 | 1.546 | 35.267 | 1.848 |  |
| hf3-l1bd | 30 | 20 | 0.744 | 1.028 | 43.502 | 2.186 |  |
| hf3-l1bd-t37 | 30 | 29 | 0.723 | 0.989 | 38.130 | 2.000 |  |
| hf3-l1obd | 30 | 29 | 0.718 | 1.063 | 39.005 | 2.176 |  |

Medians over runs (n = flights that reported). "track vs alone": median track rms of a plus-mrac deck divided by its alone deck, below 1 = MRAC better.

Files: https://github.com/YoussefChouj/px4-mrac-sim/tree/results/results/R2-tilt-source-42174790900
