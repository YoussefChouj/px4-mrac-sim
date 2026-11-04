# px4-mrac-sim

Multi-time-scale MRAC layers (rate, attitude, vz, xy) for PX4 v1.17.0, plus the tools that fly scenario
experiments in SIH or Gazebo and score them from the ULog.

| folder | what |
|---|---|
| `px4-mrac/` | the `mrac_layers` module, `MracRateStatus` msg and `apply.sh`, which patches a PX4 v1.17.0 tree (`$PX4_MRAC`, default `~/PX4-mrac`) |
| `agent/` | `scenario.py` (fly one scenario, PASS/FAIL), `arms.py` (N arms x runs, ULog metrics), report and viewer helpers |
| `scenarios/` | scenario specs (JSON) |
| `vehicles/`, `airframes/`, `worlds/` | Gazebo research-drone model, SIH airframe params, worlds |
| `px4ctl` | local PX4 control script (build, run, gz, param, scenario) |
| `ci/` | GitHub Actions helpers: `build.sh`, `run.sh`, `collect.py` |

## Layers and what each one adapts

| Layer | Switch | Adapts | Code |
|---|---|---|---|
| rate | MRL_EN_RATE | body-rate setpoint -> torque, 3 axes | MracLayers.cpp |
| attitude | MRL_EN_ATT | attitude error -> rate setpoint, roll/pitch | MracLayers.cpp |
| vz | MRL_EN_POS | vertical velocity -> collective thrust only (the code calls it the pos layer) | OuterLayers.cpp |
| xy | MRL_EN_XY | horizontal acceleration setpoint of XyCtrl, x and y | OuterLayers.cpp |

Each switch: 0 off, 1 adapt, 2 status only (u_ad = 0). Per-loop regressor masks MRL_{R,A,P,X}_FEAT (default 7 = the
original x, r, bias law) select extra terms; see MracAxis.hpp.


## Run a sweep in the cloud

Actions -> **arms** -> Run workflow, with a list of scenario names and runs per scenario. One job builds PX4
(cached by the hash of `px4-mrac/`), one runner flies each (scenario, run), and the last job writes a
mean [min..max] table to the run summary and `all.json`.

## Run locally (Ubuntu 24.04 or WSL)

```bash
bash ci/build.sh ~/px4-sih.tar.zst   # clone + patch + build PX4 v1.17.0 into ~/PX4-mrac
python agent/arms.py 0 ~/PX4-mrac 3 scenarios/mrac-off.json scenarios/mrac-dist-adapt.json
```
