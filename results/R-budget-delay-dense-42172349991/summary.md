arms run https://github.com/YoussefChouj/px4-mrac-sim/actions/runs/42172349991 wave **R-budget-delay-dense** on `claude/collect-landed` finished: **plan success, build success, fly success**, 203/240 flights pass, 8 decks.

| deck | n | pass | track rms m | hold max m | tilt max deg | att rms deg | track vs alone |
|---|---|---|---|---|---|---|---|
| dn-alone | 30 | 30 | - | 1.077 | 28.712 | 1.985 |  |
| dn-l1b | 30 | 28 | - | 0.741 | 29.769 | 2.116 |  |
| dn-l1bd | 30 | 30 | - | 0.758 | 30.057 | 2.094 |  |
| dn-l1r6t | 30 | 28 | - | 0.765 | 29.417 | 2.085 |  |
| hf2-alone | 30 | 26 | 0.877 | 1.597 | 40.071 | 2.009 |  |
| hf2-l1b | 30 | 20 | 0.731 | 1.035 | 42.880 | 2.212 |  |
| hf2-l1bd | 30 | 21 | 0.758 | 0.914 | 43.235 | 2.177 |  |
| hf2-l1r6t | 30 | 20 | 0.737 | 0.995 | 42.628 | 2.146 |  |

Medians over runs (n = flights that reported). "track vs alone": median track rms of a plus-mrac deck divided by its alone deck, below 1 = MRAC better.

Files: https://github.com/YoussefChouj/px4-mrac-sim/tree/results/results/R-budget-delay-dense-42172349991
