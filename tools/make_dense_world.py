#!/usr/bin/env python3
"""worlds/gusty_dense.sdf: worlds/gusty_video.sdf (same physics as gusty.sdf) with the floor grid moved over the dense
path area and the path itself painted on the floor (visual only), for chase-camera videos of the 'dense' step.
The path is agent/scenario.py dense_path() with its defaults, drawn from the takeoff point (local origin = spawn).
gz world frame is ENU: x = east, y = north."""
import math
import re
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'agent'))
src = (ROOT / 'agent' / 'scenario.py').read_text()
ns = {'np': np, 'math': math}
exec(compile(src[src.index('def dense_path'):src.index('def seg_dist')], 'dense_path', 'exec'), ns)
wp, total = ns['dense_path'](0.05)


def box(name, x, y, sx, sy, yaw, rgb):
    c = ' '.join(f'{v:g}' for v in rgb)
    return (f'<visual name="{name}"><pose>{x:.3f} {y:.3f} 0.001 0 0 {yaw:.4f}</pose><geometry><box><size>{sx:.3f} {sy:.3f} '
            f'0.002</size></box></geometry><material><ambient>{c} 1</ambient><diffuse>{c} 1</diffuse></material>'
            f'<cast_shadows>false</cast_shadows></visual>')


E0, E1, N0, N1 = -6, 12, -14, 14                      # grid extent [m]
vis = []
for e in range(E0, E1 + 1):
    vis.append(box(f'ge{e - E0}', e, (N0 + N1) / 2, 0.06 if e % 5 == 0 else 0.025, N1 - N0, 0,
                   (0.25,) * 3 if e % 5 == 0 else (0.5,) * 3))
for n in range(N0, N1 + 1):
    vis.append(box(f'gn{n - N0}', n * 0 + (E0 + E1) / 2, n, E1 - E0, 0.06 if n % 5 == 0 else 0.025, 0,
                   (0.25,) * 3 if n % 5 == 0 else (0.5,) * 3))
# path: one segment per 5 waypoints (25 cm), orange
P = np.vstack([wp[::5, :2], wp[:1, :2]])
for i in range(len(P) - 1):
    (n0, e0), (n1, e1) = P[i], P[i + 1]
    L = math.hypot(n1 - n0, e1 - e0)
    vis.append(box(f'p{i}', (e0 + e1) / 2, (n0 + n1) / 2, L + 0.01, 0.05, math.atan2(n1 - n0, e1 - e0), (0.92, 0.41, 0.2)))
w = (ROOT / 'worlds' / 'gusty_video.sdf').read_text()
a, b = w.index('      <!-- Visual-only floor grid'), w.index('    </link></model>') + len('    </link></model>')
model = ('      <!-- Visual-only floor grid (1 m lines, 5 m darker, -6..12 m east, -14..14 m north) and the dense test path '
         f'(orange, {total:.1f} m loop from the takeoff point; tools/make_dense_world.py). No collision, no mass. Physics '
         'is identical to worlds/gusty.sdf. -->\n    <model name="floor_grid"><static>true</static><link name="link">\n        '
         + '\n        '.join(vis) + '\n    </link></model>')
out = w[:a] + model + w[b:]
out = re.sub(r'<world name="[^"]+"', '<world name="gusty_dense"', out, count=1)
(ROOT / 'worlds' / 'gusty_dense.sdf').write_text(out)
print(f'{len(vis)} visuals -> worlds/gusty_dense.sdf')
