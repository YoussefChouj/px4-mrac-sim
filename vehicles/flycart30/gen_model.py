#!/usr/bin/env python3
"""Generate the FlyCart 30 Gazebo model (coaxial octo) from the x500_base sensors.

Every number comes from research/HEAVY-LIFT-REFERENCE.md ([S] sourced, [D] derived,
[A] assumed). Usage: gen_model.py X500_BASE_SDF OUT_DIR
"""
import math
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

MTOW = 95.0                    # [S] kg, max takeoff mass
PAYLOAD = 30.0                 # [S] kg, max payload (dual battery)
IXX, IZZ = 15.4, 29.0          # [D] kg m^2 at 65 kg (batteries, no payload)
CARGO = (0.6, 0.6, 0.22)       # [A] m, cargo box; flat so it fits under the body
CARGO_Z = -0.39                # [A] m, box centre below base_link, 2 cm under the body
ARM = 1.1 * math.sin(math.pi / 4)  # [D] 0.778 m, X layout, wheelbase 2200 mm [S]
COAX = 0.10                    # [A] m, rotor height above/below the arm plane
ROTOR_MASS = 0.5               # [A] kg per 54-inch prop + bell
PROP_D = 54 * 0.0254           # [S] m
K_T = 7.55e-3                  # [D] N/(rad/s)^2
MOMENT = 0.060                 # [D] m, k_Q / k_T
W_MAX = 176.0                  # [D] rad/s, thrust-to-weight 2.0 [A]
TAU = 0.1                      # [A] s, motor + prop spin-up time constant
BODY_Z = 0.55                  # [A] m, base_link height above ground at spawn

# PX4 CA order of airframe 12001_octo_cox: (front?, right?, upper?, ccw?), FRD signs.
ROTORS = [(1, 1, 1, 1), (1, -1, 1, 0), (-1, -1, 1, 1), (-1, 1, 1, 0),
          (1, -1, 0, 1), (1, 1, 0, 0), (-1, 1, 0, 1), (-1, -1, 0, 0)]


def sub(parent, tag, text=None, **attrib):
    e = ET.SubElement(parent, tag, attrib)
    if text is not None:
        e.text = str(text)
    return e


def inertial(link, mass, ixx, iyy, izz):
    i = sub(link, 'inertial')
    sub(i, 'mass', mass)
    m = sub(i, 'inertia')
    for k, v in (('ixx', ixx), ('ixy', 0), ('ixz', 0), ('iyy', iyy), ('iyz', 0), ('izz', izz)):
        sub(m, k, v)


def box(link, kind, name, pose, size, color=None):
    e = sub(link, kind, name=name)
    sub(e, 'pose', pose)
    sub(sub(e, 'geometry'), 'box').append(ET.fromstring(f'<size>{size}</size>'))
    if color:
        mat = sub(e, 'material')
        sub(mat, 'ambient', color)
        sub(mat, 'diffuse', color)
    return e


def main(base_sdf, out_dir):
    sensors = ET.parse(base_sdf).getroot().find('model/link[@name="base_link"]').findall('sensor')
    sdf = ET.Element('sdf', version='1.9')
    model = sub(sdf, 'model', name='flycart30')
    sub(model, 'pose', f'0 0 {BODY_Z} 0 0 0')
    base = sub(model, 'link', name='base_link')
    # Rotors are separate links, so the base carries the rest of the mass and inertia.
    rm = 8 * ROTOR_MASS
    rixx = 8 * ROTOR_MASS * (ARM ** 2 + COAX ** 2)
    rizz = 8 * ROTOR_MASS * 2 * ARM ** 2
    inertial(base, MTOW - PAYLOAD - rm, IXX - rixx, IXX - rixx, IZZ - rizz)
    box(base, 'visual', 'body', '0 0 0 0 0 0', '0.8 0.8 0.5', '0.8 0.8 0.8 1')
    box(base, 'collision', 'body_collision', '0 0 0 0 0 0', '0.8 0.8 0.5')
    for k, yaw in enumerate((math.pi / 4, -math.pi / 4)):
        box(base, 'visual', f'arm_{k}', f'0 0 0 0 0 {yaw}', f'{2 * 1.1} 0.06 0.06', '0.2 0.2 0.2 1')
    for k, (x, y) in enumerate(((0.5, 0.5), (0.5, -0.5), (-0.5, 0.5), (-0.5, -0.5))):
        box(base, 'collision', f'foot_{k}', f'{x} {y} {0.05 - BODY_Z} 0 0 0', '0.1 0.1 0.1')
        box(base, 'visual', f'leg_{k}', f'{x} {y} {(0.05 - BODY_Z) / 2} 0 0 0',
            f'0.04 0.04 {BODY_Z - 0.05}', '0.2 0.2 0.2 1')
    for s in sensors:
        base.append(s)

    izz_r = ROTOR_MASS * PROP_D ** 2 / 12  # [D] rod about its centre
    for n, (fx, ry, up, ccw) in enumerate(ROTORS):
        # PX4 FRD (x fwd, y right, z down) to Gazebo FLU (x fwd, y left, z up).
        x, y, z = fx * ARM, -ry * ARM, COAX if up else -COAX
        link = sub(model, 'link', name=f'rotor_{n}')
        sub(link, 'pose', f'{x:.4f} {y:.4f} {z} 0 0 0')
        inertial(link, ROTOR_MASS, 1e-3, izz_r, izz_r)
        box(link, 'visual', f'rotor_{n}_visual', '0 0 0 0 0 0', f'{PROP_D:.3f} 0.08 0.01',
            '0.1 0.1 0.1 1' if ccw else '0.6 0.1 0.1 1')
        joint = sub(model, 'joint', name=f'rotor_{n}_joint', type='revolute')
        sub(joint, 'parent', 'base_link')
        sub(joint, 'child', f'rotor_{n}')
        axis = sub(joint, 'axis')
        sub(axis, 'xyz', '0 0 1')
        lim = sub(axis, 'limit')
        sub(lim, 'lower', '-1e+16')
        sub(lim, 'upper', '1e+16')

    # The payload is its own model held by a detachable joint, so a flight can drop it:
    # gz topic -t /model/<name>/detachable_joint/detach -m gz.msgs.Empty -p ' '
    cargo = sub(model, 'model', name='payload')
    sub(cargo, 'pose', f'0 0 {CARGO_Z} 0 0 0')
    link = sub(cargo, 'link', name='box')
    a, b, c = CARGO
    inertial(link, PAYLOAD, PAYLOAD * (b * b + c * c) / 12, PAYLOAD * (a * a + c * c) / 12,
             PAYLOAD * (a * a + b * b) / 12)
    box(link, 'visual', 'box_visual', '0 0 0 0 0 0', f'{a} {b} {c}', '0.9 0.6 0.1 1')
    box(link, 'collision', 'box_collision', '0 0 0 0 0 0', f'{a} {b} {c}')
    p = sub(model, 'plugin', filename='gz-sim-detachable-joint-system',
            name='gz::sim::systems::DetachableJoint')
    sub(p, 'parent_link', 'base_link')
    sub(p, 'child_model', 'payload')
    sub(p, 'child_link', 'box')

    for n, (_, _, _, ccw) in enumerate(ROTORS):
        p = sub(model, 'plugin', filename='gz-sim-multicopter-motor-model-system',
                name='gz::sim::systems::MulticopterMotorModel')
        for k, v in (('jointName', f'rotor_{n}_joint'), ('linkName', f'rotor_{n}'),
                     ('turningDirection', 'ccw' if ccw else 'cw'),
                     ('timeConstantUp', TAU), ('timeConstantDown', TAU),
                     ('maxRotVelocity', W_MAX), ('motorConstant', K_T),
                     ('momentConstant', MOMENT), ('commandSubTopic', 'command/motor_speed'),
                     ('motorNumber', n),
                     # x500 values, not scaled (HEAVY-LIFT-REFERENCE.md, not modelled).
                     ('rotorDragCoefficient', 8.06428e-05),
                     ('rollingMomentCoefficient', 1e-06),
                     ('rotorVelocitySlowdownSim', 10), ('motorType', 'velocity')):
            sub(p, k, v)

    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    ET.indent(sdf)
    ET.ElementTree(sdf).write(out / 'model.sdf', encoding='UTF-8', xml_declaration=True)
    (out / 'model.config').write_text(
        '<?xml version="1.0"?>\n<model>\n  <name>flycart30</name>\n  <version>1.0</version>\n'
        '  <sdf version="1.9">model.sdf</sdf>\n  <description>Coaxial octo to the published '
        'DJI FlyCart 30 numbers; see HEAVY-LIFT-REFERENCE.md</description>\n</model>\n')


if __name__ == '__main__':
    main(*sys.argv[1:3])
