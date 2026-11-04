arms run https://github.com/YoussefChouj/px4-mrac-sim/actions/runs/41780573202 wave **F-nominal** on `main` finished: **plan success, build success, fly success**, 105/115 flights pass, 23 decks.

| deck | n | pass | track rms m | hold max m | tilt max deg | att rms deg | track vs alone |
|---|---|---|---|---|---|---|---|
| adrc-wc-08 | 5 | 0 | 5.529 | 1.787 | 35.624 | 2.916 |  |
| adrc-wc-12 | 5 | 0 | 3.705 | 1.930 | 35.248 | 3.907 |  |
| adrc-wc-15 | 5 | 5 | 3.001 | 1.090 | 35.363 | 4.457 |  |
| adrc-wc-20 | 5 | 5 | 2.193 | 0.557 | 35.456 | 5.166 |  |
| adrc-wc-25 | 5 | 5 | 1.054 | 0.393 | 35.532 | 5.641 |  |
| adrc-wc-30 | 5 | 5 | 0.740 | 0.622 | 36.986 | 11.470 |  |
| lqrfig-set0 | 5 | 5 | 0.757 | 0.162 | 13.899 | 2.208 |  |
| lqrfig-set4 | 5 | 5 | 0.483 | 0.158 | 20.611 | 3.368 |  |
| pg-def | 5 | 5 | 0.724 | 0.219 | 12.019 | 1.940 |  |
| pg-vi12 | 5 | 5 | 0.802 | 0.249 | 14.584 | 2.411 |  |
| pg-vp25 | 5 | 5 | 0.577 | 0.109 | 14.624 | 2.309 |  |
| pg-vp35 | 5 | 5 | 0.447 | 0.118 | 16.056 | 2.607 |  |
| pg-xp15 | 5 | 5 | 0.741 | 0.173 | 15.572 | 2.528 |  |
| pg-xp15vp35 | 5 | 5 | 0.433 | 0.128 | 18.720 | 3.028 |  |
| pg-xp15vp35vi12 | 5 | 5 | 0.455 | 0.158 | 20.753 | 3.340 |  |
| xyc-adrc | 5 | 5 | 3.659 | 1.138 | 23.219 | 3.829 |  |
| xyc-adrc-a7 | 5 | 5 | 2.996 | 1.070 | 35.303 | 4.426 |  |
| xyc-adrc-tuned | 5 | 5 | 1.057 | 0.407 | 35.506 | 5.528 |  |
| xyc-lqr | 5 | 5 | 3.481 | 1.039 | 22.352 | 3.111 |  |
| xyc-lqr-a7 | 5 | 5 | 2.523 | 0.751 | 34.951 | 3.043 |  |
| xyc-mpc | 5 | 5 | 3.510 | 1.051 | 22.362 | 3.085 |  |
| xyc-mpc-a7 | 5 | 5 | 2.521 | 0.646 | 34.759 | 3.009 |  |
| xyc-pid | 5 | 5 | 2.987 | 0.637 | 35.162 | 3.032 |  |

Medians over runs (n = flights that reported). "track vs alone": median track rms of a plus-mrac deck divided by its alone deck, below 1 = MRAC better.

Files: https://github.com/YoussefChouj/px4-mrac-sim/tree/results/results/F-nominal-41780573202
