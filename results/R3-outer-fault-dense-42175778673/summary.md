arms run https://github.com/YoussefChouj/px4-mrac-sim/actions/runs/42175778673 wave **R3-outer-fault-dense** on `claude/collect-landed` finished: **plan success, build success, fly success**, 168/180 flights pass, 6 decks.

| deck | n | pass | track rms m | hold max m | tilt max deg | att rms deg | track vs alone |
|---|---|---|---|---|---|---|---|
| dn2-alone | 30 | 30 | - | 1.001 | 28.774 | 1.981 |  |
| dn2-l1bd | 30 | 30 | - | 0.754 | 29.437 | 2.107 |  |
| dn2-l1obd | 30 | 30 | - | 0.728 | 29.672 | 2.162 |  |
| hff3-alone | 30 | 27 | 0.868 | 1.556 | 38.697 | 1.860 |  |
| hff3-l1bd | 30 | 23 | 0.747 | 0.886 | 41.663 | 2.106 |  |
| hff3-l1obd | 30 | 28 | 0.747 | 1.030 | 37.766 | 2.116 |  |

Medians over runs (n = flights that reported). "track vs alone": median track rms of a plus-mrac deck divided by its alone deck, below 1 = MRAC better.

Files: https://github.com/YoussefChouj/px4-mrac-sim/tree/results/results/R3-outer-fault-dense-42175778673
