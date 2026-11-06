arms run https://github.com/YoussefChouj/px4-mrac-sim/actions/runs/42138795657 wave **Q-gz-crosscheck+Q-gz-video** on `claude/collect-landed` finished: **plan success, build success, fly failure**, 6/10 flights pass, 4 decks.

| deck | n | pass | track rms m | hold max m | tilt max deg | att rms deg | track vs alone |
|---|---|---|---|---|---|---|---|
| gz-rw-alone | 3 | 3 | 0.707 | 0.450 | 41.263 | 2.546 |  |
| gz-rw-l1r6t | 3 | 2 | 0.552 | 0.309 | 43.653 | 2.965 |  |
| gz-rw-mrac | 3 | 0 | 10.018 | 10.433 | 180.000 | 117.358 |  |
| gzv-rw-alone | 1 | 1 | 0.730 | 0.573 | 40.806 | 2.538 |  |

Medians over runs (n = flights that reported). "track vs alone": median track rms of a plus-mrac deck divided by its alone deck, below 1 = MRAC better.

1 job(s) reported nothing (infra, not a gate fail): gzv-rw-l1r6t-1

Files: https://github.com/YoussefChouj/px4-mrac-sim/tree/results/results/Q-gz-crosscheck+Q-gz-video-42138795657
