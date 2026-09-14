#!/usr/bin/python3
"""Resume the user's saved U8 revision, not the rejected USB seed.
All work is in a distinct candidate project. This script never publishes to PCB/main.
"""
from pathlib import Path
import sys,json,math,collections
import pcbnew as p
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'scripts'))
from pcb_tools.router import Router,Rules,xy,uid,Obstacles,Plan
from pcb_tools.io import clone_project,save,drc,counts

SOURCE=ROOT/'PCB/main/smove-r2-main.kicad_pcb'
WORK=ROOT/'.cache/main-routing/completion'

def main():
    output=WORK/SOURCE.name
    if not output.exists(): clone_project(SOURCE,WORK)
    b=p.LoadBoard(str(output)); log=[]
    # Exactly the two D+ vias already identified by native DRC as unused.
    initial=drc(output)
    dangling={a['uuid'] for v in initial['violations'] if v['type']=='via_dangling' for a in v['items']}
    for t in list(b.GetTracks()):
        if uid(t) in dangling and t.GetNetname()=='/USB_DP': b.Remove(t)
    save(b,output)
    # Prioritize the incomplete USB MCU connection, then local pin escapes, then long trunks.
    for iteration in range(100):
        report=drc(output)
        if not report['unconnected_items']: break
        items={uid(t):t for t in b.GetTracks()}
        items.update({uid(a):a for f in b.GetFootprints() for a in f.Pads()})
        pairs=[]
        for entry in report['unconnected_items']:
            a,z=[items.get(x['uuid']) for x in entry['items']]
            if a is None or z is None: continue
            net=a.GetNetname()
            priority=0 if net=='/Compute/USB_DM_MCU' else 1 if net in ('/VBUS','/Power/PACK_P') else 2
            pairs.append((priority,math.dist(xy(a.GetPosition()),xy(z.GetPosition())),net,a,z))
        progressed=False
        for _,dist,net,a,z in sorted(pairs,key=lambda q:q[:3]):
            def candidates(item):
                if isinstance(item,p.PCB_VIA): return [(*xy(item.GetPosition()),l) for l in (p.F_Cu,p.B_Cu)]
                if isinstance(item,p.PCB_TRACK): return [(*xy(q),item.GetLayer()) for q in (item.GetStart(),item.GetEnd())]
                return [(*xy(item.GetPosition()),l) for l in (p.F_Cu,p.B_Cu) if item.IsOnLayer(l)]
            # Fine-pitch IMU tracks use 0.15mm; other logic 0.2mm. Power branches
            # below are provisional, with the main trunks handled explicitly later.
            width=.15 if net.startswith('/IMU/') else .2
            if net in ('/VBUS','/Power/PACK_P'): width=.25
            def island_points(item):
                b.BuildConnectivity();conn=b.GetConnectivity();queue=[item];seen=set();pts=set()
                while queue and len(seen)<250:
                    it=queue.pop();key=uid(it)
                    if key in seen: continue
                    seen.add(key);pts.update(candidates(it))
                    queue.extend(t for t in conn.GetConnectedTracks(it) if uid(t) not in seen)
                    queue.extend(t for t in conn.GetConnectedPads(it) if uid(t) not in seen)
                return pts
            starts,ends=island_points(a),island_points(z)
            tried=[]
            choices=sorted(((s,e) for s in starts for e in ends),key=lambda q:math.dist(q[0][:2],q[1][:2])+(0 if q[0][2]==q[1][2] else 2))
            # Existing via endpoints are valid launch points: do not duplicate a via.
            choices=sorted(choices[:80],key=lambda q:(q[0][2]!=p.B_Cu or q[1][2]!=p.B_Cu, math.dist(q[0][:2],q[1][:2])))[:16]
            for st,en in choices:
                layers=(p.F_Cu,) if net=='/Compute/USB_DM_MCU' else (p.F_Cu,p.B_Cu)
                try:
                    router=Router(b,Rules(grid=.1,max_nodes=120000))
                    plan=router.plan(net,st,en,width,layers)
                    made=router.apply(plan);save(b,output)
                    checked=drc(output)
                    new_errors=[v for v in checked['violations'] if v['severity']=='error']
                    def net_opens(j):
                        return sum(any('['+net+']' in item['description'] for item in v['items']) for v in j['unconnected_items'])
                    if new_errors or net_opens(checked)>=net_opens(report):
                        for t in made: b.Remove(t)
                        save(b,output);tried.append(('DRC rollback',new_errors));continue
                    log.append(plan.summary());print('ROUTED',iteration,net,plan.summary()['segments'],plan.summary()['vias'],'remaining',len(checked['unconnected_items']),flush=True)
                    progressed=True;break
                except (RuntimeError,ValueError) as e:
                    tried.append(str(e))
            if progressed: break
            print('DEFER',net,str(tried)[:350],flush=True)
        if not progressed: print('No progress',counts(report),flush=True);break
    (WORK/'route-log.json').write_text(json.dumps(log,indent=2)+'\n')
    print('FINAL',counts(drc(output,parity=True)),flush=True)

if __name__=='__main__': main()
