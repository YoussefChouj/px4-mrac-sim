arms run https://github.com/YoussefChouj/px4-mrac-sim/actions/runs/41795932701 wave **I-b-pair-seeds** on `main` finished: **plan success, build success, fly success**, 80/80 flights pass, 8 decks.

| deck | n | pass | track rms m | hold max m | tilt max deg | att rms deg | track vs alone |
|---|---|---|---|---|---|---|---|
| p11-x-dist-lqr-alone | 10 | 10 | 0.114 | 0.132 | 2.158 | 0.162 |  |
| p11-x-dist-lqr-plus-mrac | 10 | 10 | 0.115 | 0.142 | 3.427 | 0.294 | 1.01x |
| p11-x-mass-lqr-alone | 10 | 10 | 0.116 | 0.160 | 2.426 | 0.188 |  |
| p11-x-mass-lqr-plus-mrac | 10 | 10 | 0.103 | 0.148 | 2.148 | 0.242 | 0.89x |
| p11-x-slow-lqr-alone | 10 | 10 | 0.136 | 0.159 | 2.592 | 0.195 |  |
| p11-x-slow-lqr-plus-mrac | 10 | 10 | 0.104 | 0.154 | 2.433 | 0.234 | 0.77x |
| p11-x-tmax-lqr-alone | 10 | 10 | 0.128 | 0.125 | 2.298 | 0.188 |  |
| p11-x-tmax-lqr-plus-mrac | 10 | 10 | 0.117 | 0.160 | 2.037 | 0.214 | 0.91x |

Medians over runs (n = flights that reported). "track vs alone": median track rms of a plus-mrac deck divided by its alone deck, below 1 = MRAC better.

Files: https://github.com/YoussefChouj/px4-mrac-sim/tree/results/results/I-b-pair-seeds-41795932701
