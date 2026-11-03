"""Add SIM_GPS_NSCL to the simulated GPS (sensor_gps_sim): one factor scaling its position/velocity noise and the
accuracy it reports (eph/epv/s_variance), so a sim can match a position sensor better than GPS (the lab drone is
positioned by a camera). Default 1.0 = stock PX4 behaviour. Idempotent."""
import sys
from pathlib import Path

d = Path(sys.argv[1]) / 'src/modules/simulation/sensor_gps_sim'
par, hpp, cpp = d / 'parameters.c', d / 'SensorGpsSim.hpp', d / 'SensorGpsSim.cpp'
t = par.read_text()
if 'SIM_GPS_NSCL' not in t:
    par.write_text(t + '''
/**
 * Simulated GPS noise scale
 *
 * Scales the simulated GPS position and velocity noise and the reported accuracy. 1 = stock.
 *
 * @min 0.01
 * @max 10
 * @group Simulator
 */
PARAM_DEFINE_FLOAT(SIM_GPS_NSCL, 1.0f);
''')
t = hpp.read_text()
if 'SIM_GPS_NSCL' not in t:
    t = t.replace('(ParamInt<px4::params::SIM_GPS_USED>) _sim_gps_used',
                  '(ParamInt<px4::params::SIM_GPS_USED>) _sim_gps_used,\n\t\t(ParamFloat<px4::params::SIM_GPS_NSCL>) _sim_gps_nscl')
    hpp.write_text(t)
t = cpp.read_text()
if '_sim_gps_nscl' not in t:
    for a, b in (('generate_wgn() * 0.2 /', 'generate_wgn() * 0.2 * (double)_sim_gps_nscl.get() /'),
                 ('(generate_wgn() * 0.5f)', '(generate_wgn() * 0.5f * _sim_gps_nscl.get())'),
                 ('noiseGauss3f(0.06f, 0.077f, 0.158f)', 'noiseGauss3f(0.06f, 0.077f, 0.158f) * _sim_gps_nscl.get()'),
                 ('sensor_gps.s_variance_m_s = 0.4f;', 'sensor_gps.s_variance_m_s = 0.4f * _sim_gps_nscl.get();'),
                 ('sensor_gps.eph = 0.9f;', 'sensor_gps.eph = 0.9f * _sim_gps_nscl.get();'),
                 ('sensor_gps.epv = 1.78f;', 'sensor_gps.epv = 1.78f * _sim_gps_nscl.get();')):
        n = t.count(a)
        if n < 1:
            sys.exit(f'patch_gps_noise: pattern not found: {a}')
        t = t.replace(a, b)
    cpp.write_text(t)
print('patch_gps_noise ok')
