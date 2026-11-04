# Wave digest A-G

Made 2026-11-04 by `tools/wave_digest.py` from the results-branch folders of waves A-G (arms runs
41780319812-41780622654, main 88c63e0): `python3 tools/wave_digest.py <results>/A-* ... <results>/G-*`.
Paired rows: treatment - control matched by run (seed), mean [95 % bootstrap interval], `*` = the interval
excludes 0. Findings in `research/PROGRESS.md` ("Wave digest A-G").

## A-p11-core-41780319812: 70/70 flights passed (commit 88c63e0, finished 2026-11-04T05:48:39Z, lost jobs 0)

| deck | pass | failing flights per broken limit (value range > limit) | failing runs |
|---|---|---|---|

Every run passed in 7 of 7 decks.

| treatment - control | pass T, C | n | max_hold_err_m | rms_track_err_m | max_tilt_deg | att_track_rms_deg | rate_rms_rp | motor_sat_frac | xy_err_rms_m |
|---|---|---|---|---|---|---|---|---|---|
| p11-adrc-plus-mrac - p11-adrc-alone | 10/10, 10/10 | 10 | +0.0108 [+0.0018, +0.0206]* | -0.000178 [-0.00165, +0.00119] | +1.25 [+0.385, +2.31]* | +0.286 [+0.175, +0.406]* | +0.0225 [+0.013, +0.0329]* | +0.0557 [+0.0458, +0.0609]* | +0.00137 [+3.11e-05, +0.00317]* |
| p11-lqr-plus-mrac - p11-lqr-alone | 10/10, 10/10 | 10 | +0.0103 [-0.0117, +0.0314] | -0.00721 [-0.0127, -0.00113]* | +0.558 [+0.116, +1.13]* | +0.152 [+0.0773, +0.25]* | +0.00751 [+0.00349, +0.0132]* | +0.0475 [+0.0343, +0.0596]* | +0.00345 [-0.000981, +0.00731] |
| p11-mpc-plus-mrac - p11-mpc-alone | 10/10, 10/10 | 10 | +0.007 [-0.0119, +0.0238] | -0.00346 [-0.0115, +0.00525] | +0.0288 [-0.119, +0.17] | +0.0609 [+0.0434, +0.0809]* | +0.00289 [+0.00186, +0.00402]* | +0.0471 [+0.0339, +0.0579]* | +0.00347 [-0.000378, +0.00738] |

Not paired: p11-pid-alone

## B-p11-extras-41780372380: 210/210 flights passed (commit 88c63e0, finished 2026-11-04T05:48:54Z, lost jobs 0)

| deck | pass | failing flights per broken limit (value range > limit) | failing runs |
|---|---|---|---|

Every run passed in 21 of 21 decks.

| treatment - control | pass T, C | n | max_hold_err_m | rms_track_err_m | max_tilt_deg | att_track_rms_deg | rate_rms_rp | motor_sat_frac | xy_err_rms_m |
|---|---|---|---|---|---|---|---|---|---|
| p11-x-aggr-lqr-plus-mrac - p11-x-aggr-lqr-alone | 10/10, 10/10 | 10 | -0.00535 [-0.0321, +0.0221] | -0.00523 [-0.0177, +0.00619] | +0.206 [+0.0275, +0.373]* | +0.129 [+0.111, +0.147]* | +0.00447 [+0.00309, +0.00598]* | +0.0675 [+0.0524, +0.0799]* | +0.00755 [+0.0014, +0.0138]* |
| p11-x-dist-lqr-plus-mrac - p11-x-dist-lqr-alone | 10/10, 10/10 | 10 | -0.0273 [-0.0612, +0.00401] | -0.021 [-0.0356, -0.00433]* | +0.913 [+0.583, +1.21]* | +0.134 [+0.0922, +0.186]* | +0.00993 [+0.00807, +0.0127]* | +0.047 [+0.0413, +0.0521]* | -0.0107 [-0.0164, -0.00509]* |
| p11-x-dly13-attonly-lqr - p11-x-dly13-lqr-alone | 10/10, 10/10 | 10 | +0.00173 [-0.0158, +0.0191] | +0.00188 [-0.00992, +0.0132] | -0.0035 [-0.243, +0.232] | -0.00552 [-0.00906, -0.00152]* | -6.68e-06 [-0.000326, +0.00035] | +0 [+0, +0] | -4.17e-05 [-0.00501, +0.00488] |
| p11-x-dly13-lqr-plus-mrac - p11-x-dly13-lqr-alone | 10/10, 10/10 | 10 | -0.00592 [-0.0313, +0.0196] | +0.0122 [+0.00295, +0.0217]* | +0.561 [+0.168, +0.97]* | +0.178 [+0.0801, +0.271]* | +0.0113 [+0.00686, +0.0157]* | +0.0458 [+0.0311, +0.0565]* | +0.00901 [+0.00547, +0.0118]* |
| p11-x-dly13-posonly-lqr - p11-x-dly13-lqr-alone | 10/10, 10/10 | 10 | +0.0136 [-0.00288, +0.0307] | +0.00457 [-0.00535, +0.0151] | +0.231 [-0.0753, +0.63] | +0.0986 [+0.0573, +0.142]* | +0.00383 [+0.00202, +0.00573]* | +0.0474 [+0.0352, +0.058]* | +0.00477 [+0.00225, +0.00712]* |
| p11-x-dly40-lqr-plus-mrac - p11-x-dly40-lqr-alone | 10/10, 10/10 | 10 | +0.144 [+0.104, +0.18]* | +0.0241 [+0.00805, +0.0418]* | +12.3 [+11.4, +13.1]* | +5.34 [+5.08, +5.55]* | +1.83 [+1.77, +1.87]* | +0.756 [+0.736, +0.78]* | +0.0238 [+0.0123, +0.0372]* |
| p11-x-mass-lqr-plus-mrac - p11-x-mass-lqr-alone | 10/10, 10/10 | 10 | +0.00675 [-0.0253, +0.0394] | -0.00904 [-0.0312, +0.0122] | +0.257 [-0.242, +0.723] | +0.0985 [+0.0555, +0.137]* | +0.00588 [+0.00386, +0.00782]* | +0.0377 [+0.0307, +0.0442]* | -0.00554 [-0.0148, +0.00329] |
| p11-x-mot1-lqr-plus-mrac - p11-x-mot1-lqr-alone | 10/10, 10/10 | 10 | -0.134 [-0.164, -0.103]* | -0.00243 [-0.0198, +0.0171] | -1.07 [-1.35, -0.767]* | -0.325 [-0.355, -0.29]* | -0.0131 [-0.0144, -0.0114]* | +0.0401 [+0.0288, +0.0498]* | -0.0114 [-0.0175, -0.00574]* |
| p11-x-slow-lqr-plus-mrac - p11-x-slow-lqr-alone | 10/10, 10/10 | 10 | -0.019 [-0.066, +0.0285] | +0.00451 [-0.00766, +0.0182] | +0.688 [+0.0873, +1.34]* | +0.141 [+0.0743, +0.217]* | +0.0118 [+0.00818, +0.0164]* | +0.0381 [+0.0318, +0.045]* | +0.000256 [-0.00694, +0.00909] |
| p11-x-tmax-lqr-plus-mrac - p11-x-tmax-lqr-alone | 10/10, 10/10 | 10 | -0.00554 [-0.0501, +0.0365] | -0.00493 [-0.0267, +0.0164] | +0.458 [+0.106, +0.777]* | +0.137 [+0.05, +0.229]* | +0.00847 [+0.00388, +0.0137]* | +0.0309 [+0.0227, +0.039]* | -0.00166 [-0.01, +0.00608] |

Not paired: p11-x-attonly-lqr, p11-x-posonly-lqr, p11-x-rateonly-lqr

## C-v5-v6-v7-41780422738: 124/190 flights passed (commit 88c63e0, finished 2026-11-04T05:57:02Z, lost jobs 0)

| deck | pass | failing flights per broken limit (value range > limit) | failing runs |
|---|---|---|---|
| v5-dly30-g05 | 4/10 | not in record 6 (must_land, error) | 6 runs |
| v5-dly30-g2 | 0/10 | max_hold_err_m 1 (0.509..0.509 > 0.5); not in record 9 (must_land, error) | 10 runs |
| v5-dly45-alone | 0/10 | not in record 10 (must_land, error) | 10 runs |
| v5-dly45-g05 | 0/10 | max_hold_err_m 1 (0.528..0.528 > 0.5); not in record 9 (must_land, error) | 10 runs |
| v5-dly45-g2 | 0/10 | not in record 10 (must_land, error) | 10 runs |
| v7-dly78-alone | 0/10 | max_hold_err_m 10 (0.929..2.18 > 0.5); max_tilt_deg 10 (66.4..72.5 > 35) | 10 runs |
| v7-dly78-g01-tau02 | 0/10 | max_hold_err_m 8 (0.64..2.12 > 0.5); max_tilt_deg 10 (41.2..47.9 > 35) | 10 runs |

Every run passed in 12 of 19 decks.

| treatment - control | pass T, C | n | max_hold_err_m | rms_track_err_m | max_tilt_deg | att_track_rms_deg | rate_rms_rp | motor_sat_frac | xy_err_rms_m |
|---|---|---|---|---|---|---|---|---|---|
| v5-dly20-g05 - v5-dly20-alone | 10/10, 10/10 | 10 | -0.0119 [-0.0254, +0.00361] | -0.000571 [-0.0117, +0.0103] | -0.707 [-0.995, -0.456]* | -0.271 [-0.284, -0.259]* | -0.0114 [-0.0119, -0.0109]* | +0 [+0, +0] | -0.0167 [-0.023, -0.0108]* |
| v5-dly20-g2 - v5-dly20-alone | 10/10, 10/10 | 10 | -0.0034 [-0.0291, +0.0223] | +0.00312 [-0.00601, +0.0155] | -1.3 [-1.69, -0.916]* | -0.447 [-0.456, -0.437]* | -0.0119 [-0.0129, -0.0108]* | +0 [+0, +0] | -0.0197 [-0.0282, -0.0109]* |
| v5-dly30-g05 - v5-dly30-alone | 4/10, 10/10 | 10 | +0.018 [-0.00936, +0.0462] | -0.00301 [-0.0138, +0.00802] | -0.165 [-0.559, +0.379] | +0.178 [-0.0321, +0.387] | +0.263 [+0.132, +0.394]* | +0.402 [+0.201, +0.602]* | -0.00619 [-0.0215, +0.0101] |
| v5-dly30-g2 - v5-dly30-alone | 0/10, 10/10 | 10 | +0.214 [+0.162, +0.272]* | +0.0417 [+0.0253, +0.0603]* | +5.19 [+3.93, +7.36]* | +0.826 [+0.814, +0.842]* | +0.568 [+0.566, +0.571]* | +0.726 [+0.725, +0.726]* | +0.105 [+0.0736, +0.134]* |
| v5-dly45-g05 - v5-dly45-alone | 0/10, 0/10 | 10 | +0.0644 [-0.0107, +0.155] | -0.00391 [-0.0221, +0.0125] | +3.86 [+2.84, +4.68]* | +0.828 [+0.814, +0.842]* | +0.204 [+0.199, +0.209]* | +0.144 [+0.138, +0.149]* | -0.0814 [-0.138, -0.0367]* |
| v5-dly45-g2 - v5-dly45-alone | 0/10, 0/10 | 10 | +0.0104 [-0.0318, +0.0534] | -0.00911 [-0.0258, +0.00257] | +4.68 [+2.77, +6.92]* | +0.878 [+0.866, +0.89]* | +0.218 [+0.214, +0.221]* | +0.143 [+0.138, +0.149]* | -0.21 [-0.264, -0.169]* |
| v7-dly78-g01-tau02 - v7-dly78-alone | 0/10, 0/10 | 10 | -0.515 [-0.972, -0.0237]* | -0.695 [-0.76, -0.635]* | -25.7 [-27.1, -24.4]* | -1.85 [-1.93, -1.77]* | -0.176 [-0.191, -0.162]* | +0.072 [+0.0707, +0.0733]* | +0.11 [+0.0104, +0.211]* |

Not paired: v6-circmass-lqr-set0, v6-circmass-lqr-set4, v6-circmass-pid-default, v6-circmass-pid-tuned, v6-wind-lqr-set0, v6-wind-lqr-set4, v6-wind-pid-default, v6-wind-pid-tuned

## D-p16-sihwind-41780473246: 129/130 flights passed (commit 88c63e0, finished 2026-11-04T05:56:38Z, lost jobs 0)

| deck | pass | failing flights per broken limit (value range > limit) | failing runs |
|---|---|---|---|
| p16-sihwind-lqr-set1 | 9/10 | not in record 1 (max_hold_err_m, max_tilt_deg, must_land, error) | 6 |

Every run passed in 12 of 13 decks.

| treatment - control | pass T, C | n | max_hold_err_m | rms_track_err_m | max_tilt_deg | att_track_rms_deg | rate_rms_rp | motor_sat_frac | xy_err_rms_m |
|---|---|---|---|---|---|---|---|---|---|
| p16-sihwind-lqr-plus-mrac - p16-sihwind-lqr-alone | 10/10, 10/10 | 10 | +0.0219 [-0.00333, +0.0475] | - | +0.109 [-0.0732, +0.313] | +0.0552 [+0.0335, +0.0758]* | +0.00495 [+0.00329, +0.00665]* | +0.033 [+0.0328, +0.0333]* | -0.00127 [-0.00551, +0.00338] |

Not paired: p16-sihwind-calm, p16-sihwind-lqr-intwide, p16-sihwind-lqr-set1, p16-sihwind-lqr-set2, p16-sihwind-lqr-set3, p16-sihwind-lqr-set4, p16-sihwind-mrac-set4, p16-sihwind-mrac-umax40, p16-sihwind-mrac-umax40-intwide, p16-sihwind-pid-alone, p16-sihwind-pid-tuned

## E-tau-grid-41780523682: 50/50 flights passed (commit 88c63e0, finished 2026-11-04T05:56:27Z, lost jobs 0)

| deck | pass | failing flights per broken limit (value range > limit) | failing runs |
|---|---|---|---|

Every run passed in 10 of 10 decks.

Not paired: tau-a015-p050, tau-a015-p100, tau-a015-p100-b1, tau-a015-p200, tau-a030-p050, tau-a030-p100, tau-a030-p200, tau-a060-p050, tau-a060-p100, tau-a060-p200

## F-nominal-41780573202: 105/115 flights passed (commit 88c63e0, finished 2026-11-04T05:56:35Z, lost jobs 0)

| deck | pass | failing flights per broken limit (value range > limit) | failing runs |
|---|---|---|---|
| adrc-wc-08 | 0/5 | max_hold_err_m 5 (1.62..1.84 > 1.5) | 5 runs |
| adrc-wc-12 | 0/5 | max_hold_err_m 5 (1.92..1.94 > 1.5) | 5 runs |

Every run passed in 21 of 23 decks.

Not paired: adrc-wc-08, adrc-wc-12, adrc-wc-15, adrc-wc-20, adrc-wc-25, adrc-wc-30, lqrfig-set0, lqrfig-set4, pg-def, pg-vi12, pg-vp25, pg-vp35, pg-xp15, pg-xp15vp35, pg-xp15vp35vi12, xyc-adrc, xyc-adrc-a7, xyc-adrc-tuned, xyc-lqr, xyc-lqr-a7, xyc-mpc, xyc-mpc-a7, xyc-pid

## G-p11n-mrac-unit-41780622654: 95/105 flights passed (commit 88c63e0, finished 2026-11-04T05:59:23Z, lost jobs 0)

| deck | pass | failing flights per broken limit (value range > limit) | failing runs |
|---|---|---|---|
| heavy-hover-step | 0/5 | max_tilt_deg 5 (51.7..53.9 > 35) | 5 runs |
| motor-out | 0/5 | max_tilt_deg 5 (180..180 > 90) | 5 runs |

Every run passed in 19 of 21 decks.

| treatment - control | pass T, C | n | max_hold_err_m | rms_track_err_m | max_tilt_deg | att_track_rms_deg | rate_rms_rp | motor_sat_frac | xy_err_rms_m |
|---|---|---|---|---|---|---|---|---|---|
| p11-gps-lqr-plus-mrac - p11-gps-lqr-alone | 5/5, 5/5 | 5 | -0.00711 [-0.107, +0.103] | +0.00869 [-0.0254, +0.0477] | +0.00565 [-0.563, +0.513] | +0.103 [+0.0426, +0.163]* | +0.00697 [+0.00274, +0.0112]* | +0.0343 [+0.0151, +0.0534]* | +0.00768 [-0.0135, +0.0279] |
| p11n-lqr-plus-mrac - p11n-lqr-alone | 5/5, 5/5 | 5 | +0.00156 [-0.0221, +0.023] | +0.00478 [-0.00448, +0.014] | +0.0971 [-0.304, +0.395] | +0.123 [+0.0808, +0.174]* | +0.00614 [+0.00436, +0.0085]* | +0.0467 [+0.0302, +0.0606]* | -0.00014 [-0.00494, +0.00466] |
| p11n-x-dly13-lqr-plus-mrac - p11n-x-dly13-lqr-alone | 5/5, 5/5 | 5 | -0.016 [-0.0534, +0.0132] | -0.00533 [-0.0125, +0.00312] | +0.555 [-0.154, +1.54] | +0.178 [+0.0423, +0.339]* | +0.0113 [+0.00485, +0.0196]* | +0.0457 [+0.0268, +0.0605]* | -0.000949 [-0.00487, +0.0021] |
| p11n-x-dly13-rateonly-lqr - p11n-x-dly13-lqr-alone | 5/5, 5/5 | 5 | +0.000175 [-0.017, +0.0209] | +0.00395 [-0.00153, +0.00884] | +0.211 [-0.256, +0.593] | +0.0048 [-0.0127, +0.0258] | +0.00277 [+0.0022, +0.00334]* | +0 [+0, +0] | -0.000135 [-0.00485, +0.00529] |
| p11n-x-mot1-lqr-plus-mrac - p11n-x-mot1-lqr-alone | 5/5, 5/5 | 5 | -0.0993 [-0.138, -0.0581]* | -0.0149 [-0.0297, +0.00288] | -0.985 [-1.11, -0.856]* | -0.334 [-0.353, -0.315]* | -0.0139 [-0.0143, -0.0136]* | +0.053 [+0.0525, +0.0535]* | -0.015 [-0.0229, -0.00842]* |

Not paired: heavy-hover-step, hover-step, motor-out, mrac-att-adapt, mrac-att-adapt-g10, mrac-att-adapt-g5, mrac-att-slow-adapt, mrac-dist-adapt, mrac-off, mrac-pos-adapt, mrac-pos-adapt-u25, p11-x-dly13-rateonly-lqr
