"""Patch mc_att_control and mc_pos_control (in ~/PX4-mrac only) to publish to the *_base topics when MRL_EN_ATT /
MRL_EN_POS >= 1, read in parameters_updated so the switch works in flight. Idempotent."""
import pathlib
import sys

root = pathlib.Path(sys.argv[1])


def patch(hpp, cpp, pub_anchor, pub_type, base_topic, flag, param, upd_anchor, call_old, call_new):
    h, c = hpp.read_text(), cpp.read_text()
    if flag not in h:
        assert pub_anchor in h, f'{hpp.name} anchor'
        h = h.replace(pub_anchor, pub_anchor + f'\tuORB::Publication<{pub_type}> _mrl_base_pub{{ORB_ID({base_topic})}};\n'
                      f'\tint32_t {flag}{{0}};\t// {param} (mrac_layers): >= 1 routes the output through the MRAC layer\n')
        hpp.write_text(h)
    if flag not in c:
        assert upd_anchor in c, f'{cpp.name} anchor 1'
        c = c.replace(upd_anchor, upd_anchor + f'\tparam_t mrl = param_find("{param}");\n\n'
                      f'\tif (mrl != PARAM_INVALID) {{ param_get(mrl, &{flag}); }}\n\n', 1)
        assert call_old in c, f'{cpp.name} anchor 2'
        c = c.replace(call_old, call_new, 1)
        cpp.write_text(c)


att = root / 'mc_att_control'
patch(att / 'mc_att_control.hpp', att / 'mc_att_control_main.cpp',
      '\tuORB::Publication<vehicle_rates_setpoint_s>     _vehicle_rates_setpoint_pub{ORB_ID(vehicle_rates_setpoint)};    /**< rate setpoint publication */\n',
      'vehicle_rates_setpoint_s', 'vehicle_rates_setpoint_base', '_mrl_en_att', 'MRL_EN_ATT',
      'MulticopterAttitudeControl::parameters_updated()\n{\n',
      '\t\t\t_vehicle_rates_setpoint_pub.publish(rates_setpoint);\n',
      '\t\t\tif (_mrl_en_att >= 1) {\n\t\t\t\t_mrl_base_pub.publish(rates_setpoint);\n\n'
      '\t\t\t} else {\n\t\t\t\t_vehicle_rates_setpoint_pub.publish(rates_setpoint);\n\t\t\t}\n')
pos = root / 'mc_pos_control'
patch(pos / 'MulticopterPositionControl.hpp', pos / 'MulticopterPositionControl.cpp',
      '\tuORB::Publication<vehicle_attitude_setpoint_s>\t     _vehicle_attitude_setpoint_pub{ORB_ID(vehicle_attitude_setpoint)};\n',
      'vehicle_attitude_setpoint_s', 'vehicle_attitude_setpoint_base', '_mrl_en_pos', 'MRL_EN_POS',
      'MulticopterPositionControl::parameters_update(bool force)\n{\n',
      '\t\t\t_vehicle_attitude_setpoint_pub.publish(attitude_setpoint);\n',
      '\t\t\tif (_mrl_en_pos >= 1) {\n\t\t\t\t_mrl_base_pub.publish(attitude_setpoint);\n\n'
      '\t\t\t} else {\n\t\t\t\t_vehicle_attitude_setpoint_pub.publish(attitude_setpoint);\n\t\t\t}\n')
print('mc_att_control + mc_pos_control patched')
