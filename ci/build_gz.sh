#!/usr/bin/env bash
# CI (gz.yml): build PX4 v1.17.0 with the mrac_layers patches AND Gazebo Harmonic support into ~/PX4-mrac and pack the
# gz runtime (binaries, etc, gz plugins, gz_env.sh, PX4's gz models and worlds). Same patches as ci/build.sh.
# Usage: ci/build_gz.sh OUT.tar.zst
set -euo pipefail
here=$(cd "$(dirname "$0")/.." && pwd)
P=${PX4_MRAC:-$HOME/PX4-mrac}
tag=${PX4_TAG:-v1.17.0}
if [[ ! -d $P/.git ]]; then
  git clone --depth 1 --branch "$tag" --recurse-submodules --shallow-submodules \
    https://github.com/PX4/PX4-Autopilot.git "$P"
fi
# apt must not hang on a stalled mirror (2026-11-06: a gz build sat 110 min mid-download): short timeouts, retries
printf 'Acquire::Retries "5";\nAcquire::http::Timeout "30";\nAcquire::https::Timeout "30";\n' \
  | sudo tee /etc/apt/apt.conf.d/80-ci-retries >/dev/null
sudo apt-get update -qq
# PX4's own dependency script WITH the sim tools: installs Gazebo Harmonic and its dev packages
# (hard limit and one retry: a stalled download must fail fast, not hold the job)
timeout 30m bash "$P/Tools/setup/ubuntu.sh" --no-nuttx || timeout 30m bash "$P/Tools/setup/ubuntu.sh" --no-nuttx
python3 -m venv ~/.venvs/px4
source ~/.venvs/px4/bin/activate
pip install -q -r "$P/Tools/setup/requirements.txt" -r "$here/ci/requirements.txt"
PX4_MRAC=$P bash "$here/px4-mrac/apply.sh"
export GZ_DISTRO=harmonic
make -C "$P" px4_sitl_default -j"$(nproc)"
# the default target leaves out the Gazebo plugins (px4ctl build does the same)
cmake --build "$P/build/px4_sitl_default" --target px4_gz_plugins -j"$(nproc)"
test -f "$P/build/px4_sitl_default/rootfs/gz_env.sh"
# the runtime only: no object files or static libraries (gz_env.sh points into this tree, so keep its layout)
tar -C "$P" -I 'zstd -T0 -3' --exclude='*.o' --exclude='*.a' --exclude='.ninja_*' \
  --exclude='CMakeFiles' -cf "$1" build/px4_sitl_default Tools/simulation/gz
# the runtime must carry the startup scripts (an exclude pattern once dropped etc/init.d and PX4 could not boot)
# (list to a file first: grep -q stops reading early, tar then fails on SIGPIPE and pipefail reports it)
tar -I zstd -tf "$1" > "$1.list"
grep -q 'etc/init.d/rc.mc_defaults' "$1.list" || { echo 'packed runtime lacks etc/init.d' >&2; exit 1; }
grep -q 'etc/init.d-posix/rcS' "$1.list" || { echo 'packed runtime lacks etc/init.d-posix' >&2; exit 1; }
rm -f "$1.list"
ls -l "$1"
