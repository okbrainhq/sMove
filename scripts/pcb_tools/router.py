"""Bounded two-point router. Plans first, inserts only after all geometry passes.

Not a shove router or impedance solver. KiCad DRC with the original project/rules
is mandatory: this conservative obstacle model does not evaluate custom rule DSL.
Only the two outer layers are routed. Inner copper is reserved for planes.
"""
import math
import heapq
from functools import lru_cache
from dataclasses import dataclass
import pcbnew as p
from .geometry import clean, patterns, best_pattern, simplify, length

V = lambda q: p.VECTOR2I(round(q[0]*1e6), round(q[1]*1e6))
xy = lambda q: (q.x/1e6, q.y/1e6)
uid = lambda item: item.m_Uuid.AsString()

@dataclass(frozen=True)
class Rules:
    clearance: float = .16
    edge: float = .26
    hole: float = .26
    via_diameter: float = .45
    via_drill: float = .20
    bend_cost: float = .45
    via_cost: float = 3.
    grid: float = .1
    max_nodes: int = 180000

class Obstacles:
    def __init__(self, board, net, rules=Rules()):
        self.board, self.net, self.rules = board, net, rules
        self.layers = list(board.GetEnabledLayers().CuStack())
        self.obs = {l: [] for l in self.layers}
        self.holes, self.paste = [], []
        self.outline = p.SHAPE_POLY_SET()
        if not board.GetBoardPolygonOutlines(self.outline):
            raise ValueError('A valid closed Edge.Cuts outline is required')
        self.edges = []
        for i in range(self.outline.OutlineCount()):
            for line in [self.outline.COutline(i)]+[self.outline.CHole(i,j) for j in range(self.outline.HoleCount(i))]:
                pts = [line.CPoint(j) for j in range(line.PointCount())]
                for a, b in zip(pts, pts[1:]+pts[:1]):
                    self.edges.append(p.SHAPE_SEGMENT(a, b, 0))
        def add(layer, shape, gap):
            bb=shape.BBox()
            self.obs[layer].append((bb.GetX()/1e6-gap,bb.GetY()/1e6-gap,
                                   bb.GetRight()/1e6+gap,bb.GetBottom()/1e6+gap,shape,gap))
        for f in board.GetFootprints():
            for a in f.Pads():
                if max(a.GetDrillSize().x,a.GetDrillSize().y):
                    self.holes.append((xy(a.GetPosition()), max(a.GetDrillSize().x,a.GetDrillSize().y)/2e6))
                if a.GetAttribute()==p.PAD_ATTRIB_SMD:
                    for l, paste in ((p.F_Cu,p.F_Paste),(p.B_Cu,p.B_Paste)):
                        if a.GetLayerSet().Contains(paste): self.paste.append(a.GetEffectiveShape(l))
                if a.GetNetname()==net: continue
                for l in self.layers:
                    if a.IsOnLayer(l): add(l,a.GetEffectiveShape(l),rules.hole if a.GetAttribute()==p.PAD_ATTRIB_NPTH else rules.clearance)
        for t in board.GetTracks():
            if isinstance(t,p.PCB_VIA): self.holes.append((xy(t.GetPosition()),t.GetDrill()/2e6))
            if t.GetNetname()==net: continue
            for l in self.layers:
                if t.IsOnLayer(l): add(l,t.GetEffectiveShape(),rules.clearance)
        # Keepouts are conservatively obstacles, even those only disallowing zones.
        for z in list(board.Zones())+[z for f in board.GetFootprints() for z in f.Zones()]:
            if z.GetIsRuleArea():
                for l in self.layers:
                    if z.IsOnLayer(l): add(l,z.Outline(),.01)
        # Copper graphics are not necessarily nets; fail closed for clearance.
        for g in list(board.GetDrawings())+[g for f in board.GetFootprints() for g in f.GraphicalItems()]:
            if g.GetLayer() in self.layers and hasattr(g,'GetEffectiveShape'):
                add(g.GetLayer(),g.GetEffectiveShape(),rules.clearance)

    def segment(self,a,b,width,layer):
        if layer not in self.obs: return False
        if not self.outline.Contains(V(a)) or not self.outline.Contains(V(b)): return False
        shape=p.SHAPE_SEGMENT(V(a),V(b),p.FromMM(width))
        if any(p.SHAPE.Collide(shape,e,p.FromMM(self.rules.edge)) for e in self.edges): return False
        bb=shape.BBox(); x,y,X,Y=bb.GetX()/1e6,bb.GetY()/1e6,bb.GetRight()/1e6,bb.GetBottom()/1e6
        return not any(X>=u and U>=x and Y>=v and W>=y and p.SHAPE.Collide(shape,s,p.FromMM(gap))
                       for u,v,U,W,s,gap in self.obs[layer])

    def via(self,q):
        r=self.rules
        if not all(self.segment(q,q,r.via_diameter,l) for l in self.layers): return False
        if any(math.dist(q,c)<h+r.via_drill/2+r.hole for c,h in self.holes): return False
        shape=p.SHAPE_CIRCLE(V(q),p.FromMM(r.via_diameter/2+.075))
        return not any(p.SHAPE.Collide(shape,s) for s in self.paste)

@dataclass
class Plan:
    net: str
    width: float
    legs: list  # (layer, points)
    vias: list
    method: str

    def summary(self):
        return dict(net=self.net,width=self.width,method=self.method,
                    length_mm=round(sum(length(pts) for _,pts in self.legs),4),
                    segments=sum(len(pts)-1 for _,pts in self.legs),vias=len(self.vias),
                    legs=self.legs,via_positions=self.vias)

class Router:
    def __init__(self, board, rules=Rules()): self.board,self.rules=board,rules

    def plan(self, net, start, end, width=.2, layers=(p.F_Cu,p.B_Cu)):
        if not math.isfinite(width) or width<=0: raise ValueError('Positive finite width required')
        if not layers or any(l not in (p.F_Cu,p.B_Cu) for l in layers): raise ValueError('Outer routing layers only')
        if start[2] not in layers or end[2] not in layers: raise ValueError('Endpoint layer not enabled')
        if not self.board.FindNet(net) or net.startswith('unconnected-'): raise ValueError('Invalid signal net')
        ob=Obstacles(self.board,net,self.rules)
        if start[2]==end[2]:
            q=best_pattern(start[:2],end[:2],lambda a,b:ob.segment(a,b,width,start[2]))
            if q is not None: return Plan(net,width,[(start[2],q)],[],'pattern')
            # Try open parallel corridors before using a maze search.
            candidates=[]
            for axis in (0,1):
                for origin in (start[axis],end[axis]):
                    for offset in (.4,-.4,.8,-.8,1.2,-1.2,2.,-2.):
                        c=origin+offset
                        a=(c,start[1]) if axis==0 else (start[0],c)
                        b=(c,end[1]) if axis==0 else (end[0],c)
                        pts=clean([start[:2],a,b,end[:2]])
                        if all(ob.segment(u,v,width,start[2]) for u,v in zip(pts,pts[1:])): candidates.append(pts)
            if candidates:
                pts=min(candidates,key=lambda q:length(q)+self.rules.bend_cost*(len(q)-2))
                if length(pts)<1.7*math.dist(start[:2],end[:2])+1:
                    return Plan(net,width,[(start[2],pts)],[],'corridor')
        # Endpoint fanouts + a straight bottom trunk avoid large labyrinth searches.
        # Unlike dropping a via at every grid cell, this favors short, deliberate escapes.
        if len(layers)>1:
            bridge=self._bridge(ob,net,start,end,width)
            if bridge is not None: return bridge
        return self._search(ob,net,start,end,width,layers)

    def _bridge(self,ob,net,start,end,width):
        def escapes(q,target):
            if q[2]==p.B_Cu: return [(0.,q[:2],[q[:2]],False)]
            possibilities=[]
            for dx in range(-16,17):
                for dy in range(-16,17):
                    v=(round((q[0]+dx*.1)*10)/10,round((q[1]+dy*.1)*10)/10)
                    dist=math.dist(v,q[:2])
                    if dist<.3 or dist>1.6: continue
                    possibilities.append((dist+.06*math.dist(v,target[:2]),v))
            result=[]
            for score,v in sorted(possibilities):
                if not ob.via(v): continue
                pts=best_pattern(q[:2],v,lambda a,b:ob.segment(a,b,width,p.F_Cu))
                if pts and length(pts)<1.8:
                    result.append((score,v,pts,True))
                    if len(result)>=16: break
            return result
        starts,ends=escapes(start,end),escapes(end,start)
        options=[]
        for _,a,pa,va in starts:
            for _,z,pz,vz in ends:
                if va and vz and math.dist(a,z)<self.rules.via_drill+self.rules.hole: continue
                mid=best_pattern(a,z,lambda u,v:ob.segment(u,v,width,p.B_Cu))
                if not mid: continue
                legs=[]
                if va: legs.append((p.F_Cu,pa))
                legs.append((p.B_Cu,mid))
                if vz: legs.append((p.F_Cu,list(reversed(pz))))
                plan=Plan(net,width,legs,([a] if va else [])+([z] if vz else []),'short fanouts + bottom trunk')
                score=sum(length(pts)+self.rules.bend_cost*max(0,len(pts)-2) for _,pts in legs)
                options.append((score,plan))
        return min(options,key=lambda q:q[0])[1] if options else None

    def _search(self,ob,net,start,end,width,layers):
        r=self.rules; S=r.grid
        dirs=((1,0),(1,1),(0,1),(-1,1),(-1,0),(-1,-1),(0,-1),(1,-1))
        @lru_cache(None)
        def edge(x,y,X,Y,l): return ob.segment((x*S,y*S),(X*S,Y*S),width,l)
        @lru_cache(None)
        def via(x,y): return ob.via((x*S,y*S))
        def ends(q):
            result={}
            for x in range(round(q[0]/S)-2,round(q[0]/S)+3):
                for y in range(round(q[1]/S)-2,round(q[1]/S)+3):
                    pts=best_pattern(q[:2],(x*S,y*S),lambda a,b:ob.segment(a,b,width,q[2]))
                    if pts: result[(x,y,q[2])]=pts
            return result
        starts,ends_=ends(start),ends(end)
        if not starts or not ends_: raise RuntimeError(('blocked endpoint',net,start,end))
        # Weighted A*: bounded runtime is preferred to a claim of global optimality.
        def h(n): return 2.0*math.hypot(n[0]*S-end[0],n[1]*S-end[1])+(r.via_cost if n[2]!=end[2] else 0)
        pq=[];cost={};prev={}
        for n,pts in starts.items():
            state=(*n,8); cost[state]=length(pts);prev[state]=None
            heapq.heappush(pq,(cost[state]+h(state),cost[state],state))
        count=0
        while pq:
            _,g,u=heapq.heappop(pq)
            if g!=cost[u]: continue
            count+=1
            if u[:3] in ends_: break
            if count>r.max_nodes: raise RuntimeError(('node limit',net,count))
            x,y,l,d=u; moves=[]
            for k,(dx,dy) in enumerate(dirs):
                if d<8 and min((k-d)%8,(d-k)%8)>2: continue
                if edge(x,y,x+dx,y+dy,l):
                    moves.append(((x+dx,y+dy,l,k),S*math.hypot(dx,dy)+(r.bend_cost if d<8 and k!=d else 0)))
            if len(layers)>1 and via(x,y):
                moves.extend(((x,y,L,8),r.via_cost) for L in layers if L!=l)
            for v,c in moves:
                ng=g+c
                if ng<cost.get(v,float('inf')):
                    cost[v]=ng; prev[v]=u;heapq.heappush(pq,(ng+h(v),ng,v))
        else: raise RuntimeError(('no path',net,count))
        path=[u]
        while prev[path[-1]] is not None: path.append(prev[path[-1]])
        path.reverse()
        legs=[]; vias=[]; l=path[0][2]; pts=list(starts[path[0][:3]])
        for x,y,L,_ in path[1:]:
            q=(x*S,y*S)
            if L!=l:
                legs.append((l,simplify(clean(pts),lambda a,b:ob.segment(a,b,width,l))))
                vias.append(q);pts=[q];l=L
            else: pts.append(q)
        pts+=list(reversed(ends_[path[-1][:3]]))[1:]
        legs.append((l,simplify(clean(pts),lambda a,b:ob.segment(a,b,width,l))))
        return Plan(net,width,legs,vias,'bend-aware A* + visibility simplification')

    def apply(self,plan):
        # Recheck against the CURRENT board, so a stale plan cannot silently short it.
        if not self.board.FindNet(plan.net) or plan.net.startswith('unconnected-'): raise ValueError('Invalid signal net')
        if not math.isfinite(plan.width) or plan.width<=0: raise ValueError('Positive finite width required')
        if any(l not in (p.F_Cu,p.B_Cu) for l,_ in plan.legs): raise ValueError('Outer routing layers only')
        ob=Obstacles(self.board,plan.net,self.rules)
        bad=[(self.board.GetLayerName(l),a,b) for l,pts in plan.legs for a,b in zip(pts,pts[1:]) if not ob.segment(a,b,plan.width,l)]
        if bad:
            from .inspect import conflicts
            details=[(layer,a,b,conflicts(self.board,plan.net,a,b,plan.width,self.board.GetLayerID(layer),self.rules.clearance)) for layer,a,b in bad]
            raise RuntimeError(('Blocked manual/planned edges',details))
        bad=[q for q in plan.vias if not ob.via(q)]
        if bad: raise RuntimeError(('Via clearance/paste failure',bad))
        if any(math.dist(a,b)<self.rules.via_drill+self.rules.hole for i,a in enumerate(plan.vias) for b in plan.vias[i+1:]):
            raise RuntimeError('New vias too close')
        made=[]
        for l,pts in plan.legs:
            for a,b in zip(pts,pts[1:]):
                if math.dist(a,b)<1e-6: continue
                t=p.PCB_TRACK(self.board);t.SetStart(V(a));t.SetEnd(V(b));t.SetWidth(p.FromMM(plan.width));t.SetLayer(l);t.SetNet(self.board.FindNet(plan.net));self.board.Add(t);made.append(t)
        for q in plan.vias:
            v=p.PCB_VIA(self.board);v.SetPosition(V(q));v.SetWidth(p.FromMM(self.rules.via_diameter));v.SetDrill(p.FromMM(self.rules.via_drill));v.SetLayerPair(p.F_Cu,p.B_Cu);v.SetNet(self.board.FindNet(plan.net));self.board.Add(v);made.append(v)
        return made

    def connect(self,*args,**kwargs):
        plan=self.plan(*args,**kwargs);self.apply(plan);return plan
