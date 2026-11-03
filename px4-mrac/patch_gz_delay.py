"""Patch the gz bridge ESC output (in ~/PX4-mrac only) with a pure actuator delay.

gz MulticopterMotorModel models only the rotor spin-up lag (timeConstantUp/Down), no transport delay, and PX4 has no
sim delay parameter, so this is a small custom piece. The delay is the PX4 param SIM_GZ_ACT_DLY (ms, 0 = stock
behaviour, re-read every second), so it is recorded in every ULog. Each published rotor command is the newest one
at least that old, from a ring buffer stamped with hrt (lockstep sim) time.
Usage: patch_gz_delay.py PX4_TREE [PRISTINE_TREE]. Idempotent; an older env-var version is replaced from PRISTINE_TREE.
"""
import sys
from pathlib import Path

rel = 'src/modules/simulation/gz_bridge/GZMixingInterfaceESC.cpp'
f = Path(sys.argv[1]) / rel
s = f.read_text()
if 'SIM_GZ_ACT_DLY' in s:
    print('gz actuator delay already patched')
    sys.exit(0)
if 'PX4_GZ_ACT_DLY_MS' in s:    # first version (env var): start again from the stock file
    s = (Path(sys.argv[2] if len(sys.argv) > 2 else '/home/acer/PX4-Autopilot') / rel).read_text()
anchor = '\tif (active_output_count > 0) {\n'
assert anchor in s and 'rotor_velocity_message.set_velocity(i, outputs[i]);' in s, 'gz bridge source changed'
ring = '''\tif (active_output_count > 0) {
\t\t// pure actuator delay, param SIM_GZ_ACT_DLY [ms] (0 = off), re-read every second
\t\tstatic const param_t dly_h = param_find("SIM_GZ_ACT_DLY");
\t\tstatic int32_t dly_ms = 0;
\t\tstatic hrt_abstime dly_chk = 0;
\t\tstatic constexpr unsigned N = 256;
\t\tstatic uint16_t hist[N][MAX_ACTUATORS] {};
\t\tstatic hrt_abstime hist_t[N] {};
\t\tstatic unsigned head = 0;
\t\tconst hrt_abstime now = hrt_absolute_time();

\t\tif (dly_h != PARAM_INVALID && now - dly_chk > 1000000) { param_get(dly_h, &dly_ms); dly_chk = now; }

\t\thead = (head + 1) % N;
\t\tmemcpy(hist[head], outputs, sizeof(hist[head]));
\t\thist_t[head] = now;
\t\tconst uint16_t *out = outputs;

\t\tif (dly_ms > 0) {
\t\t\tout = hist[(head + 1) % N]; // oldest kept sample if none is old enough yet

\t\t\tfor (unsigned k = 0; k < N; k++) {
\t\t\t\tconst unsigned j = (head + N - k) % N;

\t\t\t\tif (hist_t[j] != 0 && now - hist_t[j] >= (hrt_abstime)dly_ms * 1000) { out = hist[j]; break; }
\t\t\t}
\t\t}

'''
s = s.replace(anchor, ring, 1)
s = s.replace('rotor_velocity_message.set_velocity(i, outputs[i]);', 'rotor_velocity_message.set_velocity(i, out[i]);')
s = '#include <cstring>\n#include <parameters/param.h>\n' + s
f.write_text(s)
print('gz actuator delay patched')
