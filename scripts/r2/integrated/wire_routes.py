#!/usr/bin/python3
"""Small bounded, clearance-aware route completion for the compact wire-pad ECO nets.
Native final ERC/DRC is the authority. Does not route on In1 reference plane.
"""
import pcbnew as p, heapq, math, functools, json
from route import R,H,B,D,refill
from sexp import *
b=p.LoadBoard(str(B));L=[p.F_Cu,p.In2_Cu,p.B_Cu];S=.05
V=lambda x,y:p.VECTOR2I(round(x*1e6),round(y*1e6))
def connect(net,start,end):
 obstacles={l:[] for l in [p.F_Cu,p.In1_Cu,p.In2_Cu,p.B_Cu]}
 def add(l,shape):
  bb=shape.BBox();obstacles[l].append((bb.GetX()/1e6,bb.GetY()/1e6,bb.GetRight()/1e6,bb.GetBottom()/1e6,shape))
 for f in b.GetFootprints():
  for pad in f.Pads():
   if pad.GetNetname()==net:continue
   for l in obstacles:
    if pad.IsOnLayer(l):
     add(l,pad.GetEffectiveShape(l))
     if pad.GetAttribute()==p.PAD_ATTRIB_NPTH:add(l,p.SHAPE_CIRCLE(pad.GetPosition(),max(pad.GetDrillSize().x,pad.GetDrillSize().y)//2+p.FromMM(.11)))
 for t in b.GetTracks():
  if t.GetNetname()==net:continue
  for l in obstacles:
   if t.IsOnLayer(l):add(l,t.GetEffectiveShape())
 for z in list(b.Zones())+[z for f in b.GetFootprints() for z in f.Zones()]:
  if z.GetIsRuleArea():
   for l in obstacles:
    if z.IsOnLayer(l):add(l,z.Outline())
 @functools.lru_cache(None)
 def safe(x,y,layer,via=False):
  xx=x*S;yy=y*S;rr=.395 if via else .245
  if not(100.25+rr<xx<124.75-rr and 100.25+rr<yy<135.25-rr):return False
  if xx+rr>124.2 and 111.2-rr<yy<122.4+rr:return False
  sh=p.SHAPE_CIRCLE(V(xx,yy),round(rr*1e6))
  for l in (list(obstacles) if via else [layer]):
   for x0,y0,x1,y1,o in obstacles[l]:
    if x0-rr<=xx<=x1+rr and y0-rr<=yy<=y1+rr and p.SHAPE.Collide(sh,o):return False
  return True
 st=(round(start[0]/S),round(start[1]/S),start[2]);en=(round(end[0]/S),round(end[1]/S),end[2])
 def h(a):return math.hypot(a[0]-en[0],a[1]-en[1])+(0 if a[2]==en[2] else 10)
 pq=[(h(st),0,st)];dist={st:0};prev={};count=0
 while pq:
  _,g,u=heapq.heappop(pq)
  if g!=dist[u]:continue
  count+=1
  if u==en:break
  x,y,l=u
  nei=[((x+dx,y+dy,l),math.hypot(dx,dy)) for dx,dy in [(1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)] if safe(x+dx,y+dy,l)]
  if safe(x,y,l,True):nei += [((x,y,ll),22) for ll in L if ll!=l]
  for v,c in nei:
   if g+c<dist.get(v,1e30):dist[v]=g+c;prev[v]=u;heapq.heappush(pq,(g+c+h(v),g+c,v))
  if count>150000:raise RuntimeError('route node limit')
 else:raise RuntimeError((net,'no path',st,en,safe(*st),safe(*en),count,max(x for x,y,l in dist),min(x for x,y,l in dist)))
 path=[en]
 while path[-1]!=st:path.append(prev[path[-1]])
 path.reverse();nn=b.FindNet(net)
 # Coalesce collinear grid segments; no gratuitous long high-speed signal stub.
 verts=[path[0]]
 for i,v in enumerate(path[1:-1],1):
  bef=path[i-1];aft=path[i+1]
  if (v[0]-bef[0],v[1]-bef[1],v[2]-bef[2])!=(aft[0]-v[0],aft[1]-v[1],aft[2]-v[2]):verts.append(v)
 verts.append(path[-1])
 for u,v in zip(verts,verts[1:]):
  if u[2]!=v[2]:
   via=p.PCB_VIA(b);via.SetPosition(V(u[0]*S,u[1]*S));via.SetWidth(p.FromMM(.45));via.SetDrill(p.FromMM(.2));via.SetLayerPair(p.F_Cu,p.B_Cu);via.SetNet(nn);b.Add(via)
  else:
   t=p.PCB_TRACK(b);t.SetStart(V(u[0]*S,u[1]*S));t.SetEnd(V(v[0]*S,v[1]*S));t.SetLayer(u[2]);t.SetWidth(p.FromMM(.15));t.SetNet(nn);b.Add(t)
 print(net,'nodes',count,'segments',len(verts)-1,flush=True)
 return [[round(x*S,3),round(y*S,3),l] for x,y,l in verts]
if __name__=='__main__':
 raise SystemExit('Import connect() for a deliberate current-net ECO; historical endpoints disabled.')
