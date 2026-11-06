#!/usr/bin/env bash
# CI (gz.yml): fly one Gazebo scenario once on a prebuilt gz runtime (ci/build_gz.sh); leaves the run in OUT
# (arms.json + run folder, with gazebo-CAM.mp4 for decks that set "video").
# Usage: ci/run_gz.sh BUILD.tar.zst SCENARIO.json RUN_INDEX OUT
set -euo pipefail
here=$(cd "$(dirname "$0")/.." && pwd)
P=$HOME/PX4-mrac
mkdir -p "$P"
tar -C "$P" -I zstd -xf "$1"
# Gazebo Harmonic runtime (OSRF apt) + its python bindings (agent/gz_wind.py), a virtual display and software GL for
# the camera sensors, ffmpeg for the recorder
sudo curl -fsSL https://packages.osrfoundation.org/gazebo.gpg -o /usr/share/keyrings/pkgs-osrf-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/pkgs-osrf-archive-keyring.gpg] http://packages.osrfoundation.org/gazebo/ubuntu-stable $(lsb_release -cs) main" \
  | sudo tee /etc/apt/sources.list.d/gazebo-stable.list >/dev/null
# apt must not hang on a stalled mirror (2026-11-06: see build_gz.sh): short timeouts, retries
printf 'Acquire::Retries "5";\nAcquire::http::Timeout "30";\nAcquire::https::Timeout "30";\n' \
  | sudo tee /etc/apt/apt.conf.d/80-ci-retries >/dev/null
sudo apt-get update -qq
sudo DEBIAN_FRONTEND=noninteractive timeout 20m apt-get install -y -qq gz-harmonic python3-gz-transport13 python3-gz-msgs10 \
  xvfb ffmpeg libgl1-mesa-dri libegl1 >/dev/null
python3 -m venv ~/.venvs/px4
source ~/.venvs/px4/bin/activate
pip install -q -r "$here/ci/requirements.txt"
ln -sfn "$here" ~/px4-tools
# vehicles outside the PX4 tree (px4ctl gz): models are generated here, never committed
M="$here/vehicles/models"
mkdir -p "$M"
python3 "$here/vehicles/research_drone/gen_model.py" "$P/Tools/simulation/gz/models/x500_base/model.sdf" "$M"
for v in x500_chase research_drone_chase; do rm -rf "${M:?}/$v"; cp -r "$here/vehicles/$v/model" "$M/$v"; done
name=$(basename "$2" .json)
export ARMS_OUT="$4/$name-r$3" ARMS_TIMEOUT=${ARMS_TIMEOUT:-1500} ARMS_RUN0=$(($3 - 1))
export LIBGL_ALWAYS_SOFTWARE=1
xvfb-run -a -s "-screen 0 1280x720x24" python "$here/agent/arms.py" 0 "$P" 1 "$2"
