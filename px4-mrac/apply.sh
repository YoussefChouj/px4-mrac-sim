#!/usr/bin/env bash
# Copy the mrac_layers sources into ~/PX4-mrac and apply the small baseline patches. Idempotent.
set -euo pipefail
SRC="$(cd "$(dirname "$0")" && pwd)"
P=${PX4_MRAC:-$HOME/PX4-mrac}
cp -r "$SRC/src/modules/mrac_layers" "$P/src/modules/"
cp "$SRC/msg/MracRateStatus.msg" "$P/msg/"
cat > "$P/src/modules/mrac_layers/CMakeLists.txt" <<'EOF'
px4_add_module(
	MODULE modules__mrac_layers
	MAIN mrac_layers
	SRCS
		MracLayers.cpp
		MracLayers.hpp
		OuterLayers.cpp
		XyCtrl.cpp
	DEPENDS
		mathlib
		px4_work_queue
	)
EOF
cat > "$P/src/modules/mrac_layers/Kconfig" <<'EOF'
menuconfig MODULES_MRAC_LAYERS
	bool "mrac_layers"
	default n
	---help---
		MRAC augmentation layers at the uORB handoffs
EOF
cd "$P"
grep -q 'MracRateStatus.msg' msg/CMakeLists.txt || sed -i 's/^\tVehicleTorqueSetpoint.msg$/\tVehicleTorqueSetpoint.msg\n\tMracRateStatus.msg/' msg/CMakeLists.txt
grep -q 'vehicle_torque_setpoint_base' msg/VehicleTorqueSetpoint.msg || sed -i 's/^# TOPICS vehicle_torque_setpoint$/# TOPICS vehicle_torque_setpoint vehicle_torque_setpoint_base/' msg/VehicleTorqueSetpoint.msg
grep -q 'MODULES_MRAC_LAYERS' boards/px4/sitl/default.px4board || sed -i 's/^CONFIG_MODULES_MC_RATE_CONTROL=y$/CONFIG_MODULES_MC_RATE_CONTROL=y\nCONFIG_MODULES_MRAC_LAYERS=y/' boards/px4/sitl/default.px4board
# status topics go in the default set (add_debug_topics only logs with the SDLOG_PROFILE debug bit)
sed -i '/add_topic("mrac_\(rate\|att\|pos\)_status"/d' src/modules/logger/logged_topics.cpp
sed -i 's/^\tadd_topic("vehicle_rates_setpoint", 20);$/&\n\tadd_topic("mrac_rate_status", 10);\n\tadd_topic("mrac_att_status", 20);\n\tadd_topic("mrac_pos_status", 20);/' src/modules/logger/logged_topics.cpp
grep -q 'mrac_layers start' ROMFS/px4fmu_common/init.d/rc.mc_apps || sed -i 's/^land_detector start multicopter$/land_detector start multicopter\n\nmrac_layers start/' ROMFS/px4fmu_common/init.d/rc.mc_apps
python3 "$SRC/patch_rate_control.py" src/modules/mc_rate_control
python3 "$SRC/patch_outer_control.py" src/modules
python3 "$SRC/patch_pos_xyc.py" src/modules
python3 "$SRC/patch_gz_delay.py" .
# xy baseline gains come from xyc_design.py (fitted from a flown ULog); refuse to build without them
test -f "$SRC/xyc_gains.h" || { echo "missing $SRC/xyc_gains.h: run xyc_design.py first" >&2; exit 1; }
cp "$SRC/xyc_gains.h" src/modules/mrac_layers/
grep -q 'trajectory_setpoint_xyc' msg/versioned/TrajectorySetpoint.msg || printf '\n# TOPICS trajectory_setpoint trajectory_setpoint_xyc\n' >> msg/versioned/TrajectorySetpoint.msg
grep -q 'vehicle_rates_setpoint_base' msg/versioned/VehicleRatesSetpoint.msg || printf '\n# TOPICS vehicle_rates_setpoint vehicle_rates_setpoint_base\n' >> msg/versioned/VehicleRatesSetpoint.msg
grep -q 'vehicle_attitude_setpoint_base' msg/versioned/VehicleAttitudeSetpoint.msg || sed -i 's/^# TOPICS vehicle_attitude_setpoint mc_virtual_attitude_setpoint fw_virtual_attitude_setpoint$/& vehicle_attitude_setpoint_base/' msg/versioned/VehicleAttitudeSetpoint.msg
grep -q 'mrac_att_status' msg/MracRateStatus.msg || printf '
# TOPICS mrac_rate_status mrac_att_status mrac_pos_status
' >> msg/MracRateStatus.msg
grep -n 'mrac\|_base' msg/VehicleTorqueSetpoint.msg msg/CMakeLists.txt boards/px4/sitl/default.px4board src/modules/logger/logged_topics.cpp ROMFS/px4fmu_common/init.d/rc.mc_apps src/modules/mc_rate_control/*.?pp
