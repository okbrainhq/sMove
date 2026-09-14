"""Deterministic, grid-independent orthogonal/45-degree path primitives (millimetres)."""
import math

EPS = 2e-6

def length(points):
    return sum(math.dist(a, b) for a, b in zip(points, points[1:]))

def clean(points):
    out = []
    for point in points:
        q = tuple(round(x, 6) for x in point)
        if out and math.dist(q, out[-1]) < EPS:
            continue
        while len(out) > 1:
            a, b = out[-2:]
            u, v = (b[0]-a[0], b[1]-a[1]), (q[0]-b[0], q[1]-b[1])
            if abs(u[0]*v[1]-u[1]*v[0]) < 1e-8 and u[0]*v[0]+u[1]*v[1] > 0:
                out.pop()
            else:
                break
        out.append(q)
    return out

def octilinear(a, b):
    dx, dy = abs(a[0]-b[0]), abs(a[1]-b[1])
    return min(dx, dy, abs(dx-dy)) < EPS

def patterns(a, b):
    """At most two bends; exact endpoints, no off-grid stubs or stair steps."""
    x, y = a; X, Y = b
    dx, dy = X-x, Y-y
    sx, sy = (1 if dx >= 0 else -1), (1 if dy >= 0 else -1)
    d = min(abs(dx), abs(dy))
    routes = [[a, b]] if octilinear(a, b) else []
    routes += [[a, (x+sx*d, y+sy*d), b], [a, (X-sx*d, Y-sy*d), b],
               [a, (X, y), b], [a, (x, Y), b]]
    # Symmetric 45-degree entry/exit with a central straight trunk.
    d /= 2
    routes += [[a, (x+sx*d, y+sy*d), (X-sx*d, Y-sy*d), b]]
    seen = set()
    for pts in routes:
        pts = clean(pts); key = tuple(pts)
        if key not in seen:
            seen.add(key); yield pts

def best_pattern(a, b, clear, bend_cost=.45):
    valid = [q for q in patterns(a, b) if all(clear(u, v) for u, v in zip(q, q[1:]))]
    return min(valid, key=lambda q: (length(q)+bend_cost*max(0,len(q)-2), len(q), q)) if valid else None

def simplify(points, clear, bend_cost=.45):
    """Visibility shortcuts with rechecked full-width edges, not unchecked RDP."""
    points = clean(points)
    # Dynamic programming chooses simple replacement legs over the original vertices.
    costs = [0.] + [float('inf')]*(len(points)-1)
    paths = [[points[0]]] + [None]*(len(points)-1)
    for j in range(1, len(points)):
        for i in range(j):
            q = best_pattern(points[i], points[j], clear, bend_cost)
            if q is None: continue
            merged = clean(paths[i]+q[1:]) if paths[i] else None
            if merged is None: continue
            score = length(merged)+bend_cost*max(0,len(merged)-2)
            if score < costs[j]-EPS:
                costs[j], paths[j] = score, merged
    if not paths[-1]: raise ValueError('Original path is not clear')
    return paths[-1]
