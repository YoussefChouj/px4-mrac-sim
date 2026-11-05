
## O-montecarlo-42107461595: 198/240 flights passed (commit 3db9725, finished 2026-11-05T21:39:41Z, lost jobs 0)

| deck | pass | failing flights per broken limit (value range > limit) | failing runs |
|---|---|---|---|
| mc-alone | 29/30 | max_hold_err_m 1 (3.17..3.17 > 3.0) | 19 |
| mc-l1r6 | 27/30 | must_land 1 (never landed); max_tilt_deg 3 (45.7..45.9 > 45) | 2, 8, 28 |
| mc-l1r6t | 29/30 | must_land 1 (never landed) | 8 |
| mc-mrac | 11/30 | must_land 1 (never landed); max_tilt_deg 19 (45.6..178 > 45) | 19 runs |
| mcf-l1r6 | 28/30 | must_land 1 (never landed); max_tilt_deg 1 (45.6..45.6 > 45) | 8, 28 |
| mcf-l1r6t | 29/30 | must_land 1 (never landed) | 8 |
| mcf-mrac | 15/30 | must_land 1 (never landed); max_tilt_deg 15 (45.3..70.3 > 45) | 15 runs |

Every run passed in 1 of 8 decks.

| treatment - control | pass T, C | n | max_hold_err_m | rms_track_err_m | max_tilt_deg |
|---|---|---|---|---|---|
| mc-mrac - mc-alone | 11/30, 29/30 | 30 | -0.63 [-0.838, -0.44]* | -0.0451 [-0.121, +0.0471] | +20.3 [+11.8, +31.6]* |
| mcf-mrac - mcf-alone | 15/30, 30/30 | 30 | -0.725 [-0.964, -0.45]* | -0.0199 [-0.0786, +0.0374] | +8.82 [+6.54, +11.4]* |
| mc-l1r6 - mc-alone | 27/30, 29/30 | 30 | -0.575 [-0.732, -0.422]* | -0.124 [-0.161, -0.0886]* | +3.09 [+2.52, +3.65]* |
| mc-l1r6t - mc-alone | 29/30, 29/30 | 30 | -0.549 [-0.699, -0.395]* | -0.145 [-0.188, -0.106]* | +0.568 [-0.187, +1.31] |
| mc-l1r6t - mc-l1r6 | 29/30, 27/30 | 30 | +0.0258 [-0.0187, +0.0725] | -0.021 [-0.0557, +0.0135] | -2.52 [-3.14, -1.91]* |
| mcf-l1r6 - mcf-alone | 28/30, 30/30 | 30 | -0.586 [-0.704, -0.474]* | -0.105 [-0.157, -0.0572]* | +3.13 [+2.71, +3.57]* |
| mcf-l1r6t - mcf-alone | 29/30, 30/30 | 30 | -0.58 [-0.707, -0.46]* | -0.0778 [-0.125, -0.0308]* | +0.866 [+0.205, +1.52]* |
| mcf-l1r6t - mcf-l1r6 | 29/30, 28/30 | 30 | +0.00589 [-0.0741, +0.0979] | +0.0273 [-0.00288, +0.0604] | -2.26 [-2.85, -1.72]* |
