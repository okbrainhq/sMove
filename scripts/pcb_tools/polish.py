"""Remove staircase paths without weakening rules or discarding connectivity.
Run: python -m pcb_tools.polish INPUT.kicad_pcb OUTPUT_DIRECTORY
USB data nets are protected by default. Every accepted chain passes native DRC.
"""
from collections import defaultdict
import json,sys
import pcbnew as p
from .router import uid,xy,Router,Obstacles,Plan
from .geometry import simplify,length
from .edit import CopperTransaction
from .io import clone_project,save,drc,counts


def chains(board):
    groups=defaultdict(list)
    for t in board.GetTracks():
        if isinstance(t,p.PCB_VIA) or isinstance(t,p.PCB_ARC) or t.IsLocked() or 'USB_D' in t.GetNetname(): continue
        groups[(t.GetNetname(),t.GetLayer(),t.GetWidth()/1e6)].append(t)
    for (net,l,w),tracks in groups.items():
        adjacent=defaultdict(list);by_id={uid(t):t for t in tracks}
        for t in tracks:
            adjacent[xy(t.GetStart())].append(uid(t));adjacent[xy(t.GetEnd())].append(uid(t))
        # Pad and via endpoints are graph anchors, not disposable intermediate vertices.
        def anchor(q):
            return len(adjacent[q])!=2 or any(a.HitTest(p.VECTOR2I(round(q[0]*1e6),round(q[1]*1e6))) for f in board.GetFootprints() for a in f.Pads() if a.GetNetname()==net and a.IsOnLayer(l)) or any(isinstance(v,p.PCB_VIA) and xy(v.GetPosition())==q for v in board.GetTracks())
        anchors={q for q in adjacent if anchor(q)};seen=set()
        for start in sorted(anchors):
            for tid in adjacent[start]:
                if tid in seen: continue
                current=start; ids=[];points=[start]
                while tid not in seen:
                    seen.add(tid);ids.append(tid);t=by_id[tid]
                    current=xy(t.GetEnd()) if xy(t.GetStart())==current else xy(t.GetStart())
                    points.append(current)
                    if current in anchors: break
                    tid=next(i for i in adjacent[current] if i!=tid)
                if len(ids)>=3: yield net,l,w,ids,points


def main():
    out=clone_project(sys.argv[1],sys.argv[2]);b=p.LoadBoard(str(out));baseline=counts(drc(out));changes=[]
    for net,l,w,ids,points in list(chains(b)):
        tracks={uid(t):t for t in b.GetTracks()}
        if any(i not in tracks for i in ids): continue
        with CopperTransaction(b) as tx:
            tx.remove([tracks[i] for i in ids]);ob=Obstacles(b,net)
            try: pts=simplify(points,lambda a,z:ob.segment(a,z,w,l))
            except ValueError: continue
            if len(pts)>=len(points) or length(pts)>length(points)+.01: continue
            try: Router(b).apply(Plan(net,w,[(l,pts)],[],'visibility polish'))
            except RuntimeError: continue
            save(b,out);check=counts(drc(out))
            if check['errors']>baseline['errors'] or check['unconnected']>baseline['unconnected'] or check['warnings']>baseline['warnings']: continue
            tx.commit();changes.append(dict(net=net,before=len(ids),after=len(pts)-1,saved_mm=round(length(points)-length(pts),4)))
            print(changes[-1],flush=True)
    save(b,out);final=counts(drc(out,parity=True))
    (out.parent/'polish.json').write_text(json.dumps({'changes':changes,'drc':final},indent=2)+'\n')
    print('FINAL',final,flush=True)

if __name__=='__main__': main()
