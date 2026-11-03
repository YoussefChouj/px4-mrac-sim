# px4-mrac-sim

Multi-time-scale MRAC layers (rate, attitude, position) for PX4 v1.17.0, plus the tools that fly scenario
experiments in SIH or Gazebo and score them from the ULog.

| folder | what |
|---|---|
| `px4-mrac/` | the `mrac_layers` module, `MracRateStatus` msg and `apply.sh`, which patches a PX4 v1.17.0 tree (`$PX4_MRAC`, default `~/PX4-mrac`) |
| `agent/` | `scenario.py` (fly one scenario, PASS/FAIL), `arms.py` (N arms x runs, ULog metrics), report and viewer helpers |
| `scenarios/` | scenario specs (JSON) |
| `vehicles/`, `airframes/`, `worlds/` | Gazebo research-drone model, SIH airframe params, worlds |
| `px4ctl` | local PX4 control script (build, run, gz, param, scenario) |
| `ci/` | GitHub Actions helpers: `build.sh`, `run.sh`, `collect.py` |

## Run a sweep in the cloud

Actions -> **arms** -> Run workflow, with a list of scenario names and runs per scenario. One job builds PX4
(cached by the hash of `px4-mrac/`), one runner flies each (scenario, run), and the last job writes a
mean [min..max] table to the run summary and `all.json`.

## Run locally (Ubuntu 24.04 or WSL)

```bash
bash ci/build.sh ~/px4-sih.tar.zst   # clone + patch + build PX4 v1.17.0 into ~/PX4-mrac
python agent/arms.py 0 ~/PX4-mrac 3 scenarios/mrac-off.json scenarios/mrac-dist-adapt.json
```
