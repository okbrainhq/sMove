"""Manual copper placement from exact (x_mm, y_mm, layer) waypoints.

No pathfinding. Repeating a coordinate with a different outer layer requests one
through via. Every edge and via is clearance-checked before anything is inserted.
"""
import math
import pcbnew as p
from .router import Plan
from .geometry import clean

LAYERS={'F.Cu':p.F_Cu,'B.Cu':p.B_Cu}

def waypoint_plan(net, waypoints, width=.2):
    if len(waypoints)<2: raise ValueError('At least two waypoints required')
    if not math.isfinite(width) or width<=0: raise ValueError('Positive finite width required')
    points=[]
    for x,y,l in waypoints:
        if not all(math.isfinite(v) for v in (x,y)): raise ValueError('Finite coordinates required')
        l=LAYERS.get(l,l)
        if l not in LAYERS.values(): raise ValueError('Manual traces must use F.Cu or B.Cu')
        points.append((x,y,l))
    legs=[];vias=[];l=points[0][2];pts=[points[0][:2]]
    for x,y,L in points[1:]:
        q=(x,y)
        if L!=l:
            if math.dist(q,pts[-1])>1e-6: raise ValueError('Layer change must repeat the same x,y coordinate')
            legs.append((l,clean(pts)));vias.append(q);l=L;pts=[q]
        else: pts.append(q)
    legs.append((l,clean(pts)))
    return Plan(net,width,legs,vias,'manual coordinates; no pathfinding')

def place(router,net,waypoints,width=.2):
    plan=waypoint_plan(net,waypoints,width)
    return plan,router.apply(plan)
