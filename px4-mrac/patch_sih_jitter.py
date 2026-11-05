"""Patch the SIH actuator delay (patch_sih_delay.py, run first) with a random per-sample jitter, as real loops have.

Real loop delay is a fixed pipeline part (filters, ESC protocol, motor electronics) plus scheduling jitter of a few
ms that changes every sample. SIH_ACT_DLY stays the fixed part; SIH_ACT_DJIT [ms] adds a uniform random extra delay
in [0, SIH_ACT_DJIT] drawn for every new actuator sample. The motor never sees an older sample than it saw last
(a real pipeline does not reorder), so the jitter shows as held samples, not as time going backwards. The draw is
seeded by SIH_WIND_SEED (re-read every second), so run i of every arm gets the same jitter sequence (paired A/B).
Usage: patch_sih_jitter.py PX4_TREE. Idempotent.
"""
import sys
from pathlib import Path

d = Path(sys.argv[1]) / 'src/modules/simulation/simulator_sih'
f, fp = d / 'sih.cpp', d / 'sih_params.c'
s, p = f.read_text(), fp.read_text()
if 'SIH_ACT_DJIT' in s:
    print('SIH actuator jitter present')
    sys.exit(0)
old_chk = '		if (dly_h != PARAM_INVALID && now - dly_chk > 1000000) { param_get(dly_h, &dly_ms); dly_chk = now; }\n'
old_sel = '''		if (dly_ms > 0) {
			actuators_out = hist[(head + 1) % N]; // oldest kept sample if none is old enough yet

			for (unsigned k = 0; k < N; k++) {
				const unsigned j = (head + N - k) % N;

				if (hist[j].timestamp != 0 && now - hist[j].timestamp >= (hrt_abstime)dly_ms * 1000) { actuators_out = hist[j]; break; }
			}
		}
'''
assert old_chk in s and old_sel in s, 'SIH delay patch changed (run patch_sih_delay.py first)'
s = s.replace(old_chk, '''		// per-sample jitter, param SIH_ACT_DJIT [ms] (0 = off), seeded by SIH_WIND_SEED (patch_sih_jitter.py)
		static const param_t djit_h = param_find("SIH_ACT_DJIT");
		static const param_t jseed_h = param_find("SIH_WIND_SEED");
		static float djit_ms = 0.f;
		static int32_t jseed = -1;
		static uint32_t jrng = 1;
		static actuator_outputs_s held {};

		if (dly_h != PARAM_INVALID && now - dly_chk > 1000000) {
			param_get(dly_h, &dly_ms);
			dly_chk = now;

			if (djit_h != PARAM_INVALID) { param_get(djit_h, &djit_ms); }

			int32_t sd = 1;

			if (jseed_h != PARAM_INVALID) { param_get(jseed_h, &sd); }

			if (sd != jseed) { jseed = sd; jrng = 2654435761u * (uint32_t)(sd + 1) + 1u; }
		}

		jrng = 1664525u * jrng + 1013904223u;
		const hrt_abstime dly_us = (hrt_abstime)dly_ms * 1000 + (hrt_abstime)(djit_ms > 0.f ? djit_ms * 1000.f *
					   (float)(jrng >> 8) / 16777216.f : 0.f);
''', 1)
s = s.replace(old_sel, '''		if (dly_us > 0) {
			actuators_out = hist[(head + 1) % N]; // oldest kept sample if none is old enough yet

			for (unsigned k = 0; k < N; k++) {
				const unsigned j = (head + N - k) % N;

				if (hist[j].timestamp != 0 && now - hist[j].timestamp >= dly_us) { actuators_out = hist[j]; break; }
			}

			if (actuators_out.timestamp < held.timestamp) { actuators_out = held; } // no reordering

			held = actuators_out;
		}
''', 1)
f.write_text(s)
fp.write_text(p + '''
/**
 * Random per-sample actuator delay jitter on top of SIH_ACT_DLY (research patch)
 *
 * Uniform in [0, SIH_ACT_DJIT], drawn for every actuator sample, seeded by SIH_WIND_SEED. 0 = off.
 *
 * @unit ms
 * @min 0
 * @max 50
 * @group Simulation In Hardware
 */
PARAM_DEFINE_FLOAT(SIH_ACT_DJIT, 0.0f);
''')
print('SIH actuator jitter patched')
