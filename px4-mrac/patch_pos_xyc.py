"""Patch mc_pos_control (in ~/PX4-mrac only) to follow trajectory_setpoint_xyc instead of trajectory_setpoint when
XYC_MODE >= 1 (mrac_layers XyCtrlLayer), read in parameters_update so the switch works in flight. Idempotent."""
import pathlib
import sys

pos = pathlib.Path(sys.argv[1]) / 'mc_pos_control'
hpp, cpp = pos / 'MulticopterPositionControl.hpp', pos / 'MulticopterPositionControl.cpp'
h, c = hpp.read_text(), cpp.read_text()
anchor = '\tuORB::Subscription _trajectory_setpoint_sub{ORB_ID(trajectory_setpoint)};\n'
if '_xyc_mode' not in h:
    assert anchor in h, 'hpp anchor'
    h = h.replace(anchor, anchor + '\tuORB::Subscription _xyc_setpoint_sub{ORB_ID(trajectory_setpoint_xyc)};\n'
                  '\tint32_t _xyc_mode{0};\t// XYC_MODE (mrac_layers): >= 1 follows the xy baseline output\n'
                  '\tuORB::Subscription &traj_sub() { return _xyc_mode >= 1 ? _xyc_setpoint_sub : _trajectory_setpoint_sub; }\n')
    hpp.write_text(h)
if '_xyc_mode' not in c:
    upd = 'MulticopterPositionControl::parameters_update(bool force)\n{\n'
    assert upd in c, 'cpp anchor'
    c = c.replace(upd, upd + '\tparam_t xyc = param_find("XYC_MODE");\n\n'
                  '\tif (xyc != PARAM_INVALID) { param_get(xyc, &_xyc_mode); }\n\n', 1)
    n = c.count('_trajectory_setpoint_sub.')
    assert n == 2, f'expected 2 uses, found {n}'
    c = c.replace('_trajectory_setpoint_sub.', 'traj_sub().')
    cpp.write_text(c)
print('mc_pos_control xyc switch patched')
