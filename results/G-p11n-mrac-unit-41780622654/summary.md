arms run https://github.com/YoussefChouj/px4-mrac-sim/actions/runs/41780622654 wave **G-p11n-mrac-unit** on `main` finished: **plan success, build success, fly success**, 95/105 flights pass, 21 decks.

| deck | n | pass | track rms m | hold max m | tilt max deg | att rms deg | track vs alone |
|---|---|---|---|---|---|---|---|
| heavy-hover-step | 5 | 0 | - | 0.773 | 52.948 | 14.936 |  |
| hover-step | 5 | 5 | - | 0.621 | 35.682 | 1.907 |  |
| motor-out | 5 | 0 | - | 2.083 | 179.996 | 74.218 |  |
| mrac-att-adapt | 5 | 5 | 2.959 | 0.851 | 34.847 | 2.877 |  |
| mrac-att-adapt-g10 | 5 | 5 | 2.944 | 0.683 | 34.407 | 2.351 |  |
| mrac-att-adapt-g5 | 5 | 5 | 2.946 | 0.598 | 34.888 | 2.604 |  |
| mrac-att-slow-adapt | 5 | 5 | 3.505 | 0.413 | 42.177 | 4.448 |  |
| mrac-dist-adapt | 5 | 5 | 3.052 | 0.659 | 34.798 | 2.887 |  |
| mrac-off | 5 | 5 | 3.040 | 0.996 | 35.058 | 2.817 |  |
| mrac-pos-adapt | 5 | 5 | - | 0.671 | 4.996 | 0.694 |  |
| mrac-pos-adapt-u25 | 5 | 5 | - | 0.655 | 6.463 | 0.847 |  |
| p11-gps-lqr-alone | 5 | 5 | 0.115 | 0.213 | 2.715 | 0.275 |  |
| p11-gps-lqr-plus-mrac | 5 | 5 | 0.111 | 0.231 | 2.453 | 0.408 | 0.97x |
| p11-x-dly13-rateonly-lqr | 5 | 5 | 0.068 | 0.119 | 2.091 | 0.169 |  |
| p11n-lqr-alone | 5 | 5 | 0.072 | 0.107 | 2.000 | 0.159 |  |
| p11n-lqr-plus-mrac | 5 | 5 | 0.077 | 0.126 | 1.798 | 0.272 | 1.07x |
| p11n-x-dly13-lqr-alone | 5 | 5 | 0.076 | 0.147 | 1.742 | 0.182 |  |
| p11n-x-dly13-lqr-plus-mrac | 5 | 5 | 0.064 | 0.144 | 1.970 | 0.342 | 0.84x |
| p11n-x-dly13-rateonly-lqr | 5 | 5 | 0.077 | 0.153 | 2.147 | 0.173 |  |
| p11n-x-mot1-lqr-alone | 5 | 5 | 0.100 | 0.320 | 3.448 | 0.624 |  |
| p11n-x-mot1-lqr-plus-mrac | 5 | 5 | 0.095 | 0.188 | 2.581 | 0.297 | 0.95x |

Medians over runs (n = flights that reported). "track vs alone": median track rms of a plus-mrac deck divided by its alone deck, below 1 = MRAC better.

Files: https://github.com/YoussefChouj/px4-mrac-sim/tree/results/results/G-p11n-mrac-unit-41780622654
