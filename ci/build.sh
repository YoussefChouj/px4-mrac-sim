#!/usr/bin/env bash
# CI: build PX4 v1.17.0 with the mrac_layers patches into ~/PX4-mrac and pack the SIH runtime (bin + etc).
# Usage: ci/build.sh OUT.tar.zst
set -euo pipefail
here=$(cd "$(dirname "$0")/.." && pwd)
P=${PX4_MRAC:-$HOME/PX4-mrac}
tag=${PX4_TAG:-v1.17.0}
if [[ ! -d $P/.git ]]; then
  git clone --depth 1 --branch "$tag" --recurse-submodules --shallow-submodules \
    https://github.com/PX4/PX4-Autopilot.git "$P"
fi
# PX4's own dependency script, without NuttX and Gazebo (SIH needs neither)
sudo apt-get update -qq
bash "$P/Tools/setup/ubuntu.sh" --no-nuttx --no-sim-tools
python3 -m venv ~/.venvs/px4
source ~/.venvs/px4/bin/activate
pip install -q -r "$P/Tools/setup/requirements.txt" -r "$here/ci/requirements.txt"
PX4_MRAC=$P bash "$here/px4-mrac/apply.sh"
make -C "$P" px4_sitl_default -j"$(nproc)"
tar -C "$P" -I zstd -cf "$1" build/px4_sitl_default/bin build/px4_sitl_default/etc
