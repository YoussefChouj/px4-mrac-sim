#!/usr/bin/env bash
# CI: fly one scenario once on a prebuilt SIH runtime and leave the run in OUT (arms.json + run folder).
# Usage: ci/run.sh BUILD.tar.zst SCENARIO.json RUN_INDEX OUT
set -euo pipefail
here=$(cd "$(dirname "$0")/.." && pwd)
P=$HOME/PX4-mrac
mkdir -p "$P"
tar -C "$P" -I zstd -xf "$1"
python3 -m venv ~/.venvs/px4
source ~/.venvs/px4/bin/activate
pip install -q -r "$here/ci/requirements.txt"
# px4ctl reads the tools from its own folder and the tree from PX4_SOURCE
ln -sfn "$here" ~/px4-tools
name=$(basename "$2" .json)
export ARMS_OUT="$4/$name-r$3" ARMS_TIMEOUT=${ARMS_TIMEOUT:-600}
python "$here/agent/arms.py" 0 "$P" 1 "$2"
