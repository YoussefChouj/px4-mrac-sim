
## Q-gz-crosscheck+Q-gz-video-42138795657: 6/10 flights passed (commit 86694c8, finished 2026-11-06T01:13:42Z, lost jobs 1)

| deck | pass | failing flights per broken limit (value range > limit) | failing runs |
|---|---|---|---|
| gz-rw-l1r6t | 2/3 | max_tilt_deg 1 (49.1..49.1 > 45) | 1 |
| gz-rw-mrac | 0/3 | max_hold_err_m 3 (5.96..11.3 > 3.0); max_tilt_deg 3 (180..180 > 45) | 1, 2, 3 |

Every run passed in 2 of 4 decks.

| treatment - control | pass T, C | n | max_hold_err_m | rms_track_err_m | max_tilt_deg |
|---|---|---|---|---|---|
| gz-rw-mrac - gz-rw-alone | 0/3, 3/3 | 3 | +8.74 [+5.56, +10.8]* | +9.35 [+8.73, +9.96]* | +139 [+138, +140]* |
| gz-rw-l1r6t - gz-rw-alone | 2/3, 3/3 | 3 | -0.212 [-0.302, -0.094]* | -0.137 [-0.162, -0.0951]* | +4.24 [+1.79, +7.8]* |

Not paired: gzv-rw-alone
