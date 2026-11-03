"""Patch mc_rate_control (in ~/PX4-mrac only): publish torque to vehicle_torque_setpoint_base when MRL_EN_RATE >= 1."""
import pathlib
import sys

d = pathlib.Path(sys.argv[1])
hpp = d / "MulticopterRateControl.hpp"
cpp = d / "MulticopterRateControl.cpp"
h = hpp.read_text()
c = cpp.read_text()

if "_torque_base_pub" not in h:
    anchor = "\tuORB::Publication<vehicle_torque_setpoint_s>\t_vehicle_torque_setpoint_pub;\n"
    assert anchor in h, "hpp anchor"
    h = h.replace(anchor, anchor + "\tuORB::Publication<vehicle_torque_setpoint_s>\t_torque_base_pub{ORB_ID(vehicle_torque_setpoint_base)};\n"
                  "\tint32_t _mrl_en_rate{0};\t// MRL_EN_RATE (mrac_layers): >= 1 routes torque through the MRAC layer\n")
    hpp.write_text(h)

if "_mrl_en_rate" not in c:
    a1 = "MulticopterRateControl::parameters_updated()\n{\n"
    assert a1 in c, "cpp anchor 1"
    c = c.replace(a1, a1 + "\tparam_t mrl = param_find(\"MRL_EN_RATE\");\n\n"
                  "\tif (mrl != PARAM_INVALID) { param_get(mrl, &_mrl_en_rate); }\n\n")
    a2 = "\t\t\t_vehicle_torque_setpoint_pub.publish(vehicle_torque_setpoint);\n"
    assert a2 in c, "cpp anchor 2"
    c = c.replace(a2, "\t\t\tif (_mrl_en_rate >= 1) {\n\t\t\t\t_torque_base_pub.publish(vehicle_torque_setpoint);\n\n"
                  "\t\t\t} else {\n\t\t\t\t_vehicle_torque_setpoint_pub.publish(vehicle_torque_setpoint);\n\t\t\t}\n")
    cpp.write_text(c)
print("mc_rate_control patched")
