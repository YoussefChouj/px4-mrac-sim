arms run https://github.com/YoussefChouj/px4-mrac-sim/actions/runs/42013772172 wave **M-l1-realworld** on `claude/collect-landed` finished: **plan success, build success, fly success**, 41/252 flights pass, 28 decks.

| deck | n | pass | track rms m | hold max m | tilt max deg | att rms deg | track vs alone |
|---|---|---|---|---|---|---|---|
| rw-alone | 9 | 3 | 0.809 | 1.025 | 35.447 | 1.914 |  |
| rw-l1att | 9 | 3 | 0.826 | 0.934 | 35.662 | 1.916 |  |
| rw-l1r0 | 9 | 0 | 0.826 | 0.625 | 47.161 | 3.255 |  |
| rw-l1r1 | 9 | 0 | 0.730 | 0.933 | 47.462 | 2.854 |  |
| rw-l1r2 | 9 | 0 | 0.771 | 0.625 | 37.569 | 2.097 |  |
| rw-l1r3 | 9 | 0 | 0.814 | 0.851 | 40.119 | 2.077 |  |
| rw-l1r4 | 9 | 0 | 0.775 | 0.656 | 40.250 | 2.094 |  |
| rw-l1r5 | 9 | 0 | 0.739 | 0.696 | 40.800 | 2.127 |  |
| rw-l1r6 | 9 | 0 | 0.762 | 0.562 | 38.437 | 2.052 |  |
| rw-l1r7 | 9 | 0 | 0.752 | 0.758 | 38.931 | 2.058 |  |
| rw-l1rate | 9 | 0 | 0.846 | 0.959 | 37.911 | 1.855 |  |
| rw-l1vz | 9 | 5 | 0.821 | 1.072 | 34.617 | 1.908 |  |
| rw-l1xy | 9 | 1 | 0.742 | 0.830 | 36.231 | 2.112 |  |
| rw-mrac | 9 | 1 | 0.827 | 0.571 | 43.195 | 8.654 |  |
| rwf-alone | 9 | 8 | 0.895 | 0.908 | 34.108 | 1.958 |  |
| rwf-l1att | 9 | 6 | 0.810 | 1.029 | 34.321 | 1.884 |  |
| rwf-l1r0 | 9 | 0 | 0.782 | 0.639 | 44.607 | 3.716 |  |
| rwf-l1r1 | 9 | 0 | 0.749 | 0.911 | 45.268 | 5.616 |  |
| rwf-l1r2 | 9 | 0 | 0.796 | 0.659 | 37.652 | 2.083 |  |
| rwf-l1r3 | 9 | 0 | 0.779 | 0.818 | 37.886 | 2.119 |  |
| rwf-l1r4 | 9 | 0 | 0.755 | 0.620 | 38.865 | 2.101 |  |
| rwf-l1r5 | 9 | 0 | 0.715 | 0.761 | 38.968 | 2.143 |  |
| rwf-l1r6 | 9 | 1 | 0.752 | 0.577 | 37.378 | 1.999 |  |
| rwf-l1r7 | 9 | 1 | 0.737 | 0.937 | 36.842 | 2.063 |  |
| rwf-l1rate | 9 | 3 | 0.930 | 0.982 | 35.749 | 1.813 |  |
| rwf-l1vz | 9 | 6 | 0.837 | 1.069 | 34.429 | 1.917 |  |
| rwf-l1xy | 9 | 3 | 0.757 | 0.861 | 35.383 | 2.107 |  |
| rwf-mrac | 9 | 0 | 0.804 | 0.831 | 46.163 | 9.155 |  |

Medians over runs (n = flights that reported). "track vs alone": median track rms of a plus-mrac deck divided by its alone deck, below 1 = MRAC better.

Files: https://github.com/YoussefChouj/px4-mrac-sim/tree/results/results/M-l1-realworld-42013772172
