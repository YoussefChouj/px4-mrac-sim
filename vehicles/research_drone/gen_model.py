#!/usr/bin/env python3
"""Generate the research drone Gazebo model (JX_FLY, 4-motor X, 0.2 m motor-to-motor) from x500_base.

Every number comes from research/research_drone_params.yaml ([D] logs/twin, [A] assumed, [S] derived).
The x500 frame is shrunk to the research drone's arm (meshes and sensor poses scaled); base_link gets the
research drone mass and effective inertia; four MulticopterMotorModel plugins get its rotor constants.
Usage: gen_model.py X500_BASE_SDF OUT_DIR   (writes OUT_DIR/research_drone/{model.sdf,model.config})
"""
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

MASS = 0.9885                        # [A] kg, firmware MASS_KG (not weighed)
IXX, IYY, IZZ = 0.01389, 0.01539, 0.01133  # [D] kg m^2, effective (replay fit), scaled to MASS
ARM = 0.1                            # [D] m, x/y offset of each rotor (0.2 m motor-to-motor diagonal / 2 * sqrt2)
K_T = 6.80e-6                        # [D] N/(rad/s)^2, m g / sum omega^2 at hover
K_M = 0.016                          # [A] m, x500 value. Twin fit 0.109 made gz hover 11 % low (P8 M2 2026-11-03)
W_MAX = 969.0                        # [S] rad/s, sqrt(T_MAX / K_T)
TAU = 0.0505                         # [D] s, motor lag up = down
GYRO_STD = 0.022                     # [S] rad/s, real gyro white-noise std flying (REALISM.md)
ACC_STD = 0.1                        # [S] m/s^2, real accel white-noise std flying (REALISM.md)
X500_ARM = 0.174
S = ARM / X500_ARM                   # geometric shrink of the x500 frame
# x500 rotor order and spin: (x sign, y sign, direction) in Gazebo FLU
ROTORS = [(1, -1, 'ccw'), (-1, 1, 'ccw'), (1, 1, 'cw'), (-1, -1, 'cw')]


def sub(parent, tag, text):
    e = ET.SubElement(parent, tag)
    e.text = str(text)
    return e


def scale_pose(el, k):
    v = el.text.split()
    el.text = ' '.join([f'{float(x) * k:.5g}' for x in v[:3]] + v[3:])


def main(base_sdf, out_dir):
    tree = ET.parse(base_sdf)
    model = tree.getroot().find('model')
    model.set('name', 'research_drone')
    base = model.find("link[@name='base_link']")
    inert = base.find('inertial')
    inert.find('mass').text = str(MASS)
    for k, v in (('ixx', IXX), ('iyy', IYY), ('izz', IZZ)):
        inert.find(f'inertia/{k}').text = str(v)
    for el in base.iter():  # frame visuals/collisions/sensors move in with the arms
        if el.tag == 'pose':
            scale_pose(el, S)
        elif el.tag == 'scale':
            el.text = ' '.join(f'{float(x) * S:.5g}' for x in el.text.split())
        elif el.tag == 'size':
            el.text = ' '.join(f'{float(x) * S:.5g}' for x in el.text.split())
    for i, (sx, sy, _) in enumerate(ROTORS):
        rotor = model.find(f"link[@name='rotor_{i}']")
        rotor.find('pose').text = f'{sx * ARM:.4f} {sy * ARM:.4f} 0.05 0 0 0'
        for el in rotor.iter():  # 5-inch props instead of 13-inch: shrink prop visuals
            if el.tag == 'scale':
                el.text = ' '.join(f'{float(x) * 0.0635 / 0.1651:.5g}' for x in el.text.split())
    for imu in base.iter('imu'):  # REALISM.md: x500 IMU is ~20x quieter than the real flying drone
        for n in imu.findall('angular_velocity/*/noise/stddev'):
            n.text = str(GYRO_STD)
        for n in imu.findall('linear_acceleration/*/noise/stddev'):
            n.text = str(ACC_STD)
    for i, (_, _, d) in enumerate(ROTORS):
        p = ET.SubElement(model, 'plugin', {'filename': 'gz-sim-multicopter-motor-model-system',
                                             'name': 'gz::sim::systems::MulticopterMotorModel'})
        for tag, val in (('jointName', f'rotor_{i}_joint'), ('linkName', f'rotor_{i}'), ('turningDirection', d),
                         ('timeConstantUp', TAU), ('timeConstantDown', TAU), ('maxRotVelocity', W_MAX),
                         ('motorConstant', K_T), ('momentConstant', K_M), ('commandSubTopic', 'command/motor_speed'),
                         ('motorNumber', i), ('rotorDragCoefficient', 8.06428e-05),
                         ('rollingMomentCoefficient', 1e-06), ('rotorVelocitySlowdownSim', 10),
                         ('motorType', 'velocity')):
            sub(p, tag, val)
    ET.SubElement(model, 'plugin', {'filename': 'gz-sim-joint-state-publisher-system',
                                    'name': 'gz::sim::systems::JointStatePublisher'})  # rotor speeds for M2 checks
    out =Path(out_dir) / 'research_drone'
    out.mkdir(parents=True, exist_ok=True)
    ET.indent(tree)
    tree.write(out / 'model.sdf', xml_declaration=True, encoding='UTF-8')
    (out / 'model.config').write_text(
        '<?xml version="1.0"?>\n<model><name>research_drone</name><version>1.0</version>'
        '<sdf version="1.9">model.sdf</sdf><description>JX_FLY research drone, from '
        'research/research_drone_params.yaml</description></model>\n')
    print(out / 'model.sdf')


if __name__ == '__main__':
    main(*sys.argv[1:3])
