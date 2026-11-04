arms run https://github.com/YoussefChouj/px4-mrac-sim/actions/runs/41780473246 wave **D-p16-sihwind** on `main` finished: **plan success, build success, fly success**, 129/130 flights pass, 13 decks.

| deck | n | pass | track rms m | hold max m | tilt max deg | att rms deg | track vs alone |
|---|---|---|---|---|---|---|---|
| p16-sihwind-calm | 10 | 10 | - | 0.748 | 15.294 | 0.395 |  |
| p16-sihwind-lqr-alone | 10 | 10 | - | 0.891 | 16.415 | 0.468 |  |
| p16-sihwind-lqr-intwide | 10 | 10 | - | 0.844 | 17.172 | 0.485 |  |
| p16-sihwind-lqr-plus-mrac | 10 | 10 | - | 0.878 | 16.648 | 0.543 |  |
| p16-sihwind-lqr-set1 | 10 | 9 | - | 0.605 | 17.050 | 0.574 |  |
| p16-sihwind-lqr-set2 | 10 | 10 | - | 0.549 | 17.325 | 0.587 |  |
| p16-sihwind-lqr-set3 | 10 | 10 | - | 0.433 | 17.233 | 0.658 |  |
| p16-sihwind-lqr-set4 | 10 | 10 | - | 0.374 | 17.910 | 0.711 |  |
| p16-sihwind-mrac-set4 | 10 | 10 | - | 0.373 | 17.713 | 0.759 |  |
| p16-sihwind-mrac-umax40 | 10 | 10 | - | 0.854 | 16.517 | 0.526 |  |
| p16-sihwind-mrac-umax40-intwide | 10 | 10 | - | 0.863 | 17.291 | 0.511 |  |
| p16-sihwind-pid-alone | 10 | 10 | - | 0.814 | 15.972 | 0.463 |  |
| p16-sihwind-pid-tuned | 10 | 10 | - | 0.316 | 16.546 | 0.720 |  |

Medians over runs (n = flights that reported). "track vs alone": median track rms of a plus-mrac deck divided by its alone deck, below 1 = MRAC better.

Files: https://github.com/YoussefChouj/px4-mrac-sim/tree/results/results/D-p16-sihwind-41780473246
