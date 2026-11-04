"""P14 known-map path planner: A* on a 2-D grid over worlds/obstacles.json (the same table the world is built from and
scenario.py checks clearance against), each obstacle inflated by drone radius + margin, then line-of-sight shortcutting
so the path is a few straight legs. Deterministic and controller-agnostic: the deck flies the legs with goto.

  python planner.py OBST.json N0 E0 N1 E1 [margin]       prints the waypoints

Why not PX4 Collision Prevention or PX4-Avoidance: research/notes/planners.md (P14).
"""
import heapq
import json
import math
import sys


def clearance(tab, n, e):
    """Distance from (n, e) to the nearest obstacle surface (negative inside), metres."""
    best = math.inf
    for o in tab['obstacles']:
        if o['kind'] == 'pole':
            d = math.hypot(n - o['n'], e - o['e']) - o['r']
        else:
            dn = abs(n - o['n']) - o['dn'] / 2
            de = abs(e - o['e']) - o['de'] / 2
            d = math.hypot(max(dn, 0), max(de, 0)) + min(max(dn, de), 0)
        best = min(best, d)
    return best


def free_segment(tab, a, b, need, step=0.05):
    k = max(1, int(math.hypot(b[0] - a[0], b[1] - a[1]) / step))
    return all(clearance(tab, a[0] + (b[0] - a[0]) * i / k, a[1] + (b[1] - a[1]) * i / k) >= need for i in range(k + 1))


def plan(tab, start, goal, margin=0.6, res=0.1, pad=3.0):
    """Waypoints [(n, e), ...] from start to goal (start excluded, goal included) keeping clearance >= drone radius +
    margin from every obstacle. Raises ValueError when no path exists inside the bounding box of obstacles + pad."""
    need = tab.get('drone_radius_m', 0.0) + margin
    pts = [(o['n'], o['e']) for o in tab['obstacles']] + [start, goal]
    n_lo, n_hi = min(p[0] for p in pts) - pad, max(p[0] for p in pts) + pad
    e_lo, e_hi = min(p[1] for p in pts) - pad, max(p[1] for p in pts) + pad
    nn, ne = int((n_hi - n_lo) / res) + 1, int((e_hi - e_lo) / res) + 1
    cell = lambda p: (round((p[0] - n_lo) / res), round((p[1] - e_lo) / res))
    xy = lambda c: (n_lo + c[0] * res, e_lo + c[1] * res)
    ok = {}

    def free(c):
        if c not in ok:
            ok[c] = 0 <= c[0] < nn and 0 <= c[1] < ne and clearance(tab, *xy(c)) >= need
        return ok[c]

    s, g = cell(start), cell(goal)
    if clearance(tab, *goal) < need:
        raise ValueError(f'goal {goal} is within {need:.2f} m of an obstacle')
    # the start may sit inside the inflated zone (e.g. after drifting); let A* leave it
    ok[s] = True
    moves = [(1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)]
    h = lambda c: math.hypot(c[0] - g[0], c[1] - g[1])
    openq, came, cost = [(h(s), s)], {s: None}, {s: 0.0}
    while openq:
        _, c = heapq.heappop(openq)
        if c == g:
            break
        for dn, de in moves:
            q = (c[0] + dn, c[1] + de)
            if not free(q):
                continue
            nc = cost[c] + math.hypot(dn, de)
            if nc < cost.get(q, math.inf):
                cost[q], came[q] = nc, c
                heapq.heappush(openq, (nc + h(q), q))
    if g not in came:
        raise ValueError(f'no path from {start} to {goal} with clearance {need:.2f} m')
    path, c = [], g
    while c is not None:
        path.append(xy(c))
        c = came[c]
    path = [tuple(start)] + path[::-1][1:-1] + [tuple(goal)]
    # shortcut: from each kept point jump to the farthest point still in line of sight
    out, i = [path[0]], 0
    while i < len(path) - 1:
        j = len(path) - 1
        while j > i + 1 and not free_segment(tab, path[i], path[j], need):
            j -= 1
        out.append(path[j])
        i = j
    return [(round(a, 2), round(b, 2)) for a, b in out[1:]]


if __name__ == '__main__':
    tab = json.load(open(sys.argv[1]))
    a = (float(sys.argv[2]), float(sys.argv[3]))
    b = (float(sys.argv[4]), float(sys.argv[5]))
    m = float(sys.argv[6]) if len(sys.argv) > 6 else 0.6
    wps = plan(tab, a, b, m)
    legs = [a] + wps
    print(json.dumps({'waypoints': wps, 'length_m': round(sum(math.dist(p, q) for p, q in zip(legs, legs[1:])), 2),
                      'min_clearance_m': round(min(clearance(tab, *p) for p in wps), 2)}))
