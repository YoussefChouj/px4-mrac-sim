arms run https://github.com/YoussefChouj/px4-mrac-sim/actions/runs/42175778654 wave **S-gz-validation+S-gz-video-dense** on `claude/collect-landed` finished: **plan success, build success, fly failure**, 49/52 flights pass, 8 decks.

| deck | n | pass | track rms m | hold max m | tilt max deg | att rms deg | track vs alone |
|---|---|---|---|---|---|---|---|
| gz-rw-alone | 7 | 7 | 0.712 | 0.540 | 41.113 | 2.537 |  |
| gz-rw-l1bd | 8 | 7 | 0.561 | 0.305 | 43.482 | 2.810 |  |
| gz-rw-l1obd | 8 | 8 | 0.575 | 0.337 | 40.036 | 2.595 |  |
| gzd-alone | 10 | 9 | - | 0.851 | 26.307 | 1.905 |  |
| gzd-l1bd | 8 | 7 | - | 0.556 | 32.230 | 2.376 |  |
| gzd-l1obd | 9 | 9 | - | 0.612 | 30.183 | 2.076 |  |
| gzvd-alone | 1 | 1 | - | 0.769 | 27.058 | 1.864 |  |
| gzvd-l1obd | 1 | 1 | - | 0.435 | 29.875 | 2.005 |  |

Medians over runs (n = flights that reported). "track vs alone": median track rms of a plus-mrac deck divided by its alone deck, below 1 = MRAC better.

10 job(s) reported nothing (infra, not a gate fail): gz-rw-alone-4, gz-rw-alone-6, gz-rw-alone-10, gz-rw-l1bd-9, gz-rw-l1bd-10, gz-rw-l1obd-4, gz-rw-l1obd-8, gzd-l1bd-3, gzd-l1bd-6, gzd-l1obd-5

Files: https://github.com/YoussefChouj/px4-mrac-sim/tree/results/results/S-gz-validation+S-gz-video-dense-42175778654
