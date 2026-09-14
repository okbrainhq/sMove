"""Run with PYTHONPATH=scripts /usr/bin/python3 -m pcb_tools --help."""
import argparse
import json
from pathlib import Path
import pcbnew as p
from .router import Router, xy, uid
from .io import clone_project, save, drc, counts
from .geometry import length, patterns


def endpoint(board, spec):
    ref, number=spec.split(':',1)
    items=[a for f in board.GetFootprints() if f.GetReference()==ref for a in f.Pads() if a.GetNumber()==number]
    if len(items)!=1: raise ValueError(f'{spec}: expected exactly one pad, found {len(items)}')
    return items[0]

def main():
    ap=argparse.ArgumentParser(description='Safe candidate-only PCB routing/placement tools. Native input is never overwritten.')
    sub=ap.add_subparsers(dest='command',required=True)
    route=sub.add_parser('route',help='Plan a two-pad connection; optional candidate project output')
    route.add_argument('board');route.add_argument('start');route.add_argument('end')
    route.add_argument('--width',type=float,default=.2);route.add_argument('--layers',choices=['top','bottom','both'],default='both')
    route.add_argument('--output-dir')
    rotate=sub.add_parser('rotate',help='Compare rotation/position candidates; never rotate a connected part silently')
    rotate.add_argument('board');rotate.add_argument('reference');rotate.add_argument('--angles',type=float,nargs='+',default=[0,90,180,270])
    rotate.add_argument('--positions',nargs='+',help='Absolute x,y positions in mm; default is current origin')
    rotate.add_argument('--ripup-connected-nets',action='store_true',help='Explicitly remove all attached-net tracks in preview copies only')
    rotate.add_argument('--output-dir',required=True)
    manual=sub.add_parser('waypoints',help='Place exact coordinates with explicit vias; NO pathfinding')
    manual.add_argument('board');manual.add_argument('--net',required=True)
    manual.add_argument('--points',required=True,help='JSON [[x,y,"F.Cu"], ...]; repeat x,y on B.Cu to request a via')
    manual.add_argument('--width',type=float,default=.2);manual.add_argument('--output-dir',required=True)
    manual.add_argument('--ripup-id',action='append',default=[],help='Explicit copper UUID to remove in the candidate only')
    manual.add_argument('--ripup-net',action='append',default=[],help='Explicit entire net to reroute in the candidate only')
    args=ap.parse_args(); source=Path(args.board); b=p.LoadBoard(str(source.resolve()))
    if args.command=='waypoints':
        from .manual import waypoint_plan
        plan=waypoint_plan(args.net,json.loads(args.points),args.width)
        output=clone_project(source,args.output_dir)
        from .edit import CopperTransaction
        with CopperTransaction(b) as tx:
            tracks={uid(t):t for t in b.GetTracks()}
            if any(i not in tracks for i in args.ripup_id): raise ValueError('Unknown rip-up UUID')
            tx.remove([t for i,t in tracks.items() if i in args.ripup_id or t.GetNetname() in args.ripup_net])
            Router(b).apply(plan);save(b,output)
            result=plan.summary();result['drc']=counts(drc(output,parity=True))
            result['removed_uuids']=[uid(t) for t in tx.removed]
            tx.commit()
        (output.parent/'manual-route.json').write_text(json.dumps(result,indent=2)+'\n')
        print(json.dumps(result,indent=2));return
    if args.command=='route':
        a,z=endpoint(b,args.start),endpoint(b,args.end)
        if not a.GetNetname() or a.GetNetname()!=z.GetNetname(): raise ValueError('Endpoints must share a nonempty net')
        layers={'top':(p.F_Cu,),'bottom':(p.B_Cu,),'both':(p.F_Cu,p.B_Cu)}[args.layers]
        # SMD pads cannot originate on the opposite layer. PTH pads can.
        start_layer=next((l for l in layers if a.IsOnLayer(l)),None)
        end_layer=next((l for l in layers if z.IsOnLayer(l)),None)
        if start_layer is None or end_layer is None: raise ValueError('Pad is not on selected routing layer')
        router=Router(b); plan=router.plan(a.GetNetname(),(*xy(a.GetPosition()),start_layer),(*xy(z.GetPosition()),end_layer),args.width,layers)
        result=plan.summary()
        if args.output_dir:
            output=clone_project(source,args.output_dir); router.apply(plan);save(b,output)
            result['drc']=counts(drc(output,parity=True));result['output']=str(output)
            (output.parent/'route.json').write_text(json.dumps(result,indent=2)+'\n')
        print(json.dumps(result,indent=2));return
    original=next(f for f in b.GetFootprints() if f.GetReference()==args.reference)
    if original.IsLocked(): raise ValueError('Footprint is locked')
    nets={a.GetNetname() for a in original.Pads() if a.GetNetname() and not a.GetNetname().startswith('unconnected-')}
    attached=[t for t in b.GetTracks() if t.GetNetname() in nets]
    if attached and not args.ripup_connected_nets:
        raise ValueError('Connected copper exists. Refusing to leave stale tracks; use explicit preview-only ripup flag.')
    positions=[tuple(map(float,s.split(','))) for s in args.positions] if args.positions else [xy(original.GetPosition())]
    results=[]
    for i,pos in enumerate(positions):
        if len(pos)!=2: raise ValueError('Position must be x,y')
        for angle in args.angles:
            out=clone_project(source,Path(args.output_dir)/f'position-{i}-angle-{angle:g}')
            import subprocess,sys
            subprocess.run([sys.executable,'-m','pcb_tools.rotation_worker',str(out),args.reference,str(angle),str(pos[0]),str(pos[1])],check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
            results.append(json.loads((out.parent/'rotation.json').read_text()))
    results.sort(key=lambda q:(q['drc']['errors'],q['approx_connection_length_mm']))
    Path(args.output_dir,'comparison.json').write_text(json.dumps(results,indent=2)+'\n')
    print(json.dumps(results,indent=2))

if __name__=='__main__': main()
