arms run https://github.com/YoussefChouj/px4-mrac-sim/actions/runs/41780372380 wave **B-p11-extras** on `main` finished: **plan success, build success, fly success**, 210/210 flights pass, 21 decks.

| deck | n | pass | track rms m | hold max m | tilt max deg | att rms deg | track vs alone |
|---|---|---|---|---|---|---|---|
| p11-x-aggr-lqr-alone | 10 | 10 | 0.776 | 0.205 | 13.672 | 2.226 |  |
| p11-x-aggr-lqr-plus-mrac | 10 | 10 | 0.765 | 0.212 | 13.841 | 2.348 | 0.99x |
| p11-x-attonly-lqr | 10 | 10 | 0.066 | 0.140 | 1.960 | 0.162 |  |
| p11-x-dist-lqr-alone | 10 | 10 | 0.133 | 0.144 | 2.573 | 0.185 |  |
| p11-x-dist-lqr-plus-mrac | 10 | 10 | 0.113 | 0.160 | 3.529 | 0.299 | 0.85x |
| p11-x-dly13-attonly-lqr | 10 | 10 | 0.067 | 0.121 | 1.551 | 0.160 |  |
| p11-x-dly13-lqr-alone | 10 | 10 | 0.068 | 0.124 | 1.678 | 0.166 |  |
| p11-x-dly13-lqr-plus-mrac | 10 | 10 | 0.075 | 0.120 | 1.961 | 0.354 | 1.10x |
| p11-x-dly13-posonly-lqr | 10 | 10 | 0.066 | 0.139 | 1.719 | 0.239 |  |
| p11-x-dly40-lqr-alone | 10 | 10 | 0.073 | 0.107 | 1.858 | 0.190 |  |
| p11-x-dly40-lqr-plus-mrac | 10 | 10 | 0.088 | 0.258 | 13.976 | 5.649 | 1.21x |
| p11-x-mass-lqr-alone | 10 | 10 | 0.116 | 0.147 | 1.986 | 0.180 |  |
| p11-x-mass-lqr-plus-mrac | 10 | 10 | 0.106 | 0.161 | 2.468 | 0.294 | 0.91x |
| p11-x-mot1-lqr-alone | 10 | 10 | 0.113 | 0.276 | 3.479 | 0.630 |  |
| p11-x-mot1-lqr-plus-mrac | 10 | 10 | 0.098 | 0.150 | 2.537 | 0.291 | 0.86x |
| p11-x-posonly-lqr | 10 | 10 | 0.064 | 0.137 | 2.097 | 0.337 |  |
| p11-x-rateonly-lqr | 10 | 10 | 0.067 | 0.120 | 1.744 | 0.166 |  |
| p11-x-slow-lqr-alone | 10 | 10 | 0.116 | 0.139 | 2.270 | 0.171 |  |
| p11-x-slow-lqr-plus-mrac | 10 | 10 | 0.123 | 0.144 | 2.619 | 0.292 | 1.07x |
| p11-x-tmax-lqr-alone | 10 | 10 | 0.131 | 0.157 | 2.205 | 0.185 |  |
| p11-x-tmax-lqr-plus-mrac | 10 | 10 | 0.104 | 0.172 | 2.634 | 0.262 | 0.79x |

Medians over runs (n = flights that reported). "track vs alone": median track rms of a plus-mrac deck divided by its alone deck, below 1 = MRAC better.

Files: https://github.com/YoussefChouj/px4-mrac-sim/tree/results/results/B-p11-extras-41780372380
