arms run https://github.com/YoussefChouj/px4-mrac-sim/actions/runs/41780319812 wave **A-p11-core** on `main` finished: **plan success, build success, fly success**, 70/70 flights pass, 7 decks.

| deck | n | pass | track rms m | hold max m | tilt max deg | att rms deg | track vs alone |
|---|---|---|---|---|---|---|---|
| p11-adrc-alone | 10 | 10 | 0.020 | 0.045 | 3.028 | 0.633 |  |
| p11-adrc-plus-mrac | 10 | 10 | 0.020 | 0.052 | 3.898 | 0.900 | 1.00x |
| p11-lqr-alone | 10 | 10 | 0.074 | 0.111 | 1.539 | 0.150 |  |
| p11-lqr-plus-mrac | 10 | 10 | 0.067 | 0.115 | 1.929 | 0.286 | 0.90x |
| p11-mpc-alone | 10 | 10 | 0.067 | 0.111 | 1.681 | 0.159 |  |
| p11-mpc-plus-mrac | 10 | 10 | 0.065 | 0.126 | 1.708 | 0.199 | 0.97x |
| p11-pid-alone | 10 | 10 | 0.080 | 0.126 | 1.599 | 0.165 |  |

Medians over runs (n = flights that reported). "track vs alone": median track rms of a plus-mrac deck divided by its alone deck, below 1 = MRAC better.

Files: https://github.com/YoussefChouj/px4-mrac-sim/tree/results/results/A-p11-core-41780319812
