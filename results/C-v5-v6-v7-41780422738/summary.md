arms run https://github.com/YoussefChouj/px4-mrac-sim/actions/runs/41780422738 wave **C-v5-v6-v7** on `main` finished: **plan success, build success, fly success**, 124/190 flights pass, 19 decks.

| deck | n | pass | track rms m | hold max m | tilt max deg | att rms deg | track vs alone |
|---|---|---|---|---|---|---|---|
| v5-dly20-alone | 10 | 10 | 0.069 | 0.128 | 5.570 | 0.763 |  |
| v5-dly20-g05 | 10 | 10 | 0.067 | 0.108 | 5.024 | 0.492 |  |
| v5-dly20-g2 | 10 | 10 | 0.071 | 0.117 | 4.424 | 0.312 |  |
| v5-dly30-alone | 10 | 10 | 0.072 | 0.120 | 6.039 | 0.771 |  |
| v5-dly30-g05 | 10 | 4 | 0.071 | 0.137 | 5.729 | 1.219 |  |
| v5-dly30-g2 | 10 | 0 | 0.109 | 0.307 | 10.251 | 1.587 |  |
| v5-dly45-alone | 10 | 0 | 0.084 | 0.165 | 13.202 | 2.290 |  |
| v5-dly45-g05 | 10 | 0 | 0.083 | 0.166 | 17.560 | 3.124 |  |
| v5-dly45-g2 | 10 | 0 | 0.078 | 0.152 | 17.591 | 3.170 |  |
| v6-circmass-lqr-set0 | 10 | 10 | 0.352 | 0.173 | 5.557 | 0.458 |  |
| v6-circmass-lqr-set4 | 10 | 10 | 0.137 | 0.086 | 5.451 | 0.528 |  |
| v6-circmass-pid-default | 10 | 10 | 0.357 | 0.148 | 5.067 | 0.412 |  |
| v6-circmass-pid-tuned | 10 | 10 | 0.143 | 0.072 | 5.096 | 0.481 |  |
| v6-wind-lqr-set0 | 10 | 10 | - | 0.877 | 15.733 | 0.477 |  |
| v6-wind-lqr-set4 | 10 | 10 | - | 0.371 | 16.591 | 0.712 |  |
| v6-wind-pid-default | 10 | 10 | - | 0.702 | 15.554 | 0.453 |  |
| v6-wind-pid-tuned | 10 | 10 | - | 0.296 | 15.946 | 0.726 |  |
| v7-dly78-alone | 10 | 0 | 0.896 | 1.437 | 69.895 | 8.600 |  |
| v7-dly78-g01-tau02 | 10 | 0 | 0.178 | 0.811 | 43.614 | 6.749 |  |

Medians over runs (n = flights that reported). "track vs alone": median track rms of a plus-mrac deck divided by its alone deck, below 1 = MRAC better.

Files: https://github.com/YoussefChouj/px4-mrac-sim/tree/results/results/C-v5-v6-v7-41780422738
